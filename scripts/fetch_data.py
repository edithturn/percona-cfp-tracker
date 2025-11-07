import requests
from datetime import datetime, timezone

ALL_EVENTS_URL = "https://developers.events/all-events.json"
ALL_CFPS_URL   = "https://developers.events/all-cfps.json"

def fetch_and_clean():
    """
    Fetch public JSON feeds and return a list of 'open CFP' items with the fields we care about,
    including source_tags from all-events.json.
    """
    events_resp = requests.get(ALL_EVENTS_URL, timeout=30); events_resp.raise_for_status()
    cfps_resp   = requests.get(ALL_CFPS_URL,   timeout=30); cfps_resp.raise_for_status()

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

        cleaned.append({
            "name":        conf.get("name") or ev.get("name"),
            "hyperlink":   conf.get("hyperlink") or ev.get("hyperlink"),
            "cfp_url":     c.get("link"),
            "cfp_close":   c.get("untilDate"),  # epoch ms
            "event_start": conf_start or ev_start,
            "event_end":   conf_end or ev_end,
            "location":    conf.get("location") or ev.get("location"),
            "city":        ev.get("city"),
            "country":     ev.get("country"),
            "source":      "developers.events",
            "source_tags": source_tags,         # <— keep source-provided tags intact
        })

    return cleaned
