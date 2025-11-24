import os
import requests
from datetime import datetime, timezone
import re
from urllib.parse import urlsplit

# Single source (developers.events). Allow optional env override; no mirror fallback.
EVENTS_URL = os.getenv("ALL_EVENTS_URL") or "https://developers.events/all-events.json"
CFPS_URL   = os.getenv("ALL_CFPS_URL")  or "https://developers.events/all-cfps.json"

def _normalize_component(value):
    """
    Normalize a component for external_id:
    - Lowercase
    - Trim whitespace
    - Collapse spaces and non-alphanumerics to single hyphens
    - Return empty string if falsy
    """
    if not value:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text

def _normalize_url(url: str) -> str:
    """
    Normalize URLs for ID stability:
    - lowercase scheme/host
    - drop query/fragment (including utm params)
    - remove trailing slash from path
    """
    if not url:
        return ""
    try:
        parts = urlsplit(str(url).strip())
        scheme = (parts.scheme or "https").lower()
        netloc = (parts.netloc or "").lower()
        path = (parts.path or "").rstrip("/")
        return f"{scheme}://{netloc}{path}"
    except Exception:
        text = str(url).strip().lower()
        text = text.split("?", 1)[0].split("#", 1)[0]
        return text.rstrip("/")

def build_external_id(source: str, hyperlink: str, event_start):
    """
    Build a stable external_id:
    Format: {source}::{normalized_hyperlink}::{event_start}
    - Prefer stable hyperlink over name/city
    - event_start is included to disambiguate rare cases of reused URLs
    """
    normalized_url = _normalize_url(hyperlink)
    parts = [
        _normalize_component(source),
        _normalize_component(normalized_url),
        str(event_start or "")
    ]
    return "::".join(parts)

def fetch_and_clean():
    """
    Fetch public JSON feeds and return a list of 'open CFP' items with the fields we care about,
    including source_tags from all-events.json.
    """
    events_resp = requests.get(EVENTS_URL, timeout=30); events_resp.raise_for_status()
    cfps_resp   = requests.get(CFPS_URL,   timeout=30); cfps_resp.raise_for_status()
    events_raw = events_resp.json()
    cfps_raw   = cfps_resp.json()

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    open_cfps = [c for c in cfps_raw if c.get("untilDate") and c["untilDate"] > now_ms]

    # Build lookup from all-events.json to enrich fields (incl. source_tags)
    by_link_or_name = {}
    for e in events_raw:
        key = (e.get("hyperlink") or e.get("name") or "").strip()
        if key:
            by_link_or_name[key] = {
                "event": e,
                "source_tags": e.get("tags") or []   # <— take original tags from source
            }

    def normalize_date_range(value):
        """Return (start, end) from a possibly missing/short 'date' field."""
        if isinstance(value, (list, tuple)):
            start = value[0] if len(value) >= 1 else None
            end = value[1] if len(value) >= 2 else None
            return start, end
        return None, None

    cleaned = []
    for c in open_cfps:
        conf = c.get("conf", {}) or {}
        key = (conf.get("hyperlink") or conf.get("name") or "").strip()

        ev_match     = by_link_or_name.get(key, {})
        ev           = ev_match.get("event", {}) or {}
        source_tags  = ev_match.get("source_tags", [])

        conf_start, conf_end = normalize_date_range(conf.get("date"))
        ev_start, ev_end     = normalize_date_range(ev.get("date"))

        item_name      = conf.get("name") or ev.get("name")
        item_hyperlink = conf.get("hyperlink") or ev.get("hyperlink")
        item_city      = ev.get("city") or ""
        item_source    = "developers.events"
        item_start     = conf_start or ev_start

        cleaned_item = {
            "name":        item_name,
            "hyperlink":   item_hyperlink,
            "cfp_url":     c.get("link"),
            "cfp_close":   c.get("untilDate"),  # epoch ms
            "event_start": item_start,
            "event_end":   conf_end or ev_end,
            "location":    conf.get("location") or ev.get("location"),
            "city":        item_city,
            "country":     ev.get("country"),
            "source":      item_source,
            "source_tags": source_tags,         # <— keep source-provided tags intact
        }
        cleaned_item["external_id"] = build_external_id(
            cleaned_item["source"], cleaned_item["hyperlink"], cleaned_item["event_start"]
        )

        cleaned.append(cleaned_item)

    return cleaned
