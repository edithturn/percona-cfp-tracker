import os, json, re
from datetime import datetime, timezone
from urllib.parse import urlsplit

def load_db(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_db(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_component(value):
    if not value:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text

def _normalize_url(url: str) -> str:
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

def _compute_external_id(ev):
    src   = _normalize_component(ev.get("source"))
    norm_url = _normalize_component(_normalize_url(ev.get("hyperlink")))
    start = str(ev.get("event_start") or "")
    return "::".join([src, norm_url, start])

def _to_date_str(value):
    """
    Convert epoch ms (int/float) or ISO-like string to YYYY-MM-DD for readability.
    Returns None for unknown/invalid.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    if isinstance(value, str):
        # Try common formats; otherwise take first 10 chars if looks like a date
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
        return value[:10] if len(value) >= 10 else value
    return None

def merge_and_save(open_cfps, db_path):
    """
    - Add new events
    - Update source fields for existing events (incl. source_tags)
    - Maintain created_at / updated_at timestamps
    """
    db = load_db(db_path)

    def make_key(e):
        return f"{e.get('name','').strip()}|{e.get('hyperlink','').strip()}"

    existing = {make_key(e): e for e in db}
    current  = {make_key(e): e for e in open_cfps}

    added, updated, closed = [], [], []

    # Add or update events that are currently open
    for item in open_cfps:
        k = make_key(item)
        if k in existing:
            ev = existing[k]
            # Update only source-driven fields (do NOT overwrite team-managed fields)
            # Update source-driven fields
            if item.get("cfp_url") is not None:
                ev["cfp_url"] = item["cfp_url"]
            if item.get("location") is not None:
                ev["location"] = item["location"]
            if item.get("city") is not None:
                ev["city"] = item["city"]
            if item.get("country") is not None:
                ev["country"] = item["country"]
            if item.get("source") is not None:
                ev["source"] = item["source"]
            if item.get("source_tags") is not None:
                ev["source_tags"] = item["source_tags"]
            if item.get("external_id") is not None:
                ev["external_id"] = item["external_id"]
            # Dates: keep epoch ms, add readable mirror fields
            if item.get("cfp_close") is not None:
                ev["cfp_close"] = item["cfp_close"]
                ev["cfp_close_date"] = _to_date_str(item["cfp_close"])
            if item.get("event_start") is not None:
                ev["event_start"] = item["event_start"]
                ev["event_start_date"] = _to_date_str(item["event_start"])
            if item.get("event_end") is not None:
                ev["event_end"] = item["event_end"]
                ev["event_end_date"] = _to_date_str(item["event_end"])
            # Ensure we backfill external_id if missing
            if not ev.get("external_id"):
                ev["external_id"] = _compute_external_id(ev)
            # Touch updated_at timestamp
            ev["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated.append(item.get("name"))
        else:
            # New event
            item.setdefault("source_tags", [])
            # Ensure external_id exists for new items even if upstream missed it
            if not item.get("external_id"):
                item["external_id"] = _compute_external_id(item)
            # Initialize timestamps; do NOT add team-managed fields
            now_iso = datetime.now(timezone.utc).isoformat()
            item["created_at"] = now_iso
            item["updated_at"] = now_iso
            # Dates: keep epoch ms, add readable mirror fields
            if item.get("cfp_close") is not None:
                item["cfp_close_date"] = _to_date_str(item.get("cfp_close"))
            if item.get("event_start") is not None:
                item["event_start_date"] = _to_date_str(item.get("event_start"))
            if item.get("event_end") is not None:
                item["event_end_date"] = _to_date_str(item.get("event_end"))
            db.append(item)
            added.append(item.get("name"))

    # Global backfill: ensure every record has an external_id before saving
    for ev in db:
        if not ev.get("external_id"):
            ev["external_id"] = _compute_external_id(ev)
        # Ensure timestamps exist
        if not ev.get("created_at"):
            ev["created_at"] = datetime.now(timezone.utc).isoformat()
        if not ev.get("updated_at"):
            ev["updated_at"] = ev["created_at"]
        # Ensure mirror date fields exist
        if ev.get("cfp_close") is not None:
            ev["cfp_close_date"] = _to_date_str(ev.get("cfp_close"))
        if ev.get("event_start") is not None:
            ev["event_start_date"] = _to_date_str(ev.get("event_start"))
        if ev.get("event_end") is not None:
            ev["event_end_date"] = _to_date_str(ev.get("event_end"))

    save_db(db_path, db)
    return {"added": added, "updated": updated, "closed": closed, "count": len(db)}
