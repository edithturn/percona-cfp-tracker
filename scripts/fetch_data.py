import requests
from datetime import datetime, timezone

ALL_EVENTS_URL = "https://developers.events/all-events.json"
ALL_CFPS_URL   = "https://developers.events/all-cfps.json"

def fetch_and_clean():
    """
    Fetch public JSON feeds and return a list of 'open CFP' items with the fields we care about.
    """
    events_raw = requests.get(ALL_EVENTS_URL, timeout=30)
    events_raw.raise_for_status()
    events_raw = events_raw.json()

    cfps_raw = requests.get(ALL_CFPS_URL, timeout=30)
    cfps_raw.raise_for_status()
    cfps_raw = cfps_raw.json()

    # Keep only CFPs still open today
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    open_cfps = [c for c in cfps_raw if c.get("untilDate") and c["untilDate"] > now_ms]

    # Build a quick lookup by hyperlink (or name) from all-events.json, to enrich fields
    by_link_or_name = {}
    for e in events_raw:
        key = (e.get("hyperlink") or e.get("name") or "").strip()
        if key:
            by_link_or_name[key] = e

    def get_date_range(value):
        """
        Normalize a 'date' field that may be a list, tuple, or None.
        Returns (start, end) where either may be None.
        """
        if isinstance(value, (list, tuple)):
            start = value[0] if len(value) >= 1 else None
            end = value[1] if len(value) >= 2 else None
            return start, end
        return None, None

    cleaned = []
    for c in open_cfps:
        conf = c.get("conf", {}) or {}
        key = (conf.get("hyperlink") or conf.get("name") or "").strip()
        ev  = by_link_or_name.get(key, {})
        conf_start, conf_end = get_date_range(conf.get("date"))
        ev_start, ev_end = get_date_range(ev.get("date"))
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
        })

    return cleaned
