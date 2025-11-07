import os, json

DEFAULT_STATUS = "pending_approval"  # approved | ignored | pending_approval | closed

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

def merge_and_save(open_cfps, db_path):
    """
    - Add new events (status=pending_approval, notified=false, tags/comments empty)
    - Update source fields for existing events (incl. source_tags)
    - Mark missing ones as closed
    """
    db = load_db(db_path)

    def make_key(e):
        return f"{e.get('name','').strip()}|{e.get('hyperlink','').strip()}"

    existing = {make_key(e): e for e in db}
    current  = {make_key(e): e for e in open_cfps}

    added, updated, closed = [], [], []

    # 1) Mark as closed if the event disappeared from the current open CFP list
    for ev in db:
        if make_key(ev) not in current and ev.get("status") != "closed":
            ev["status"] = "closed"
            closed.append(ev.get("name"))

    # 2) Add or update events that are currently open
    for item in open_cfps:
        k = make_key(item)
        if k in existing:
            ev = existing[k]
            # Update only source-driven fields (do NOT overwrite team-managed fields)
            for field in [
                "cfp_url", "cfp_close", "event_start", "event_end",
                "location", "city", "country", "source", "source_tags"
            ]:
                if item.get(field) is not None:
                    ev[field] = item[field]
            # If it was previously closed and reappears, put back to pending_approval
            if ev.get("status") == "closed":
                ev["status"] = DEFAULT_STATUS
            updated.append(item.get("name"))
        else:
            # New event: initialize team-managed fields
            item.setdefault("source_tags", [])
            item["status"]   = DEFAULT_STATUS
            item["notified"] = False
            item["tags"]     = []         # team tags (manual)
            item["category"] = None       # team category (manual)
            item["comments"] = ""         # team notes (manual)
            db.append(item)
            added.append(item.get("name"))

    save_db(db_path, db)
    return {"added": added, "updated": updated, "closed": closed, "count": len(db)}
