import os, json

DEFAULT_STATUS = "pending_approval"  # approved | ignored | pending_approval | closed

def load_db(path):
    """Load local JSON database, return empty list if file doesn't exist or is broken."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_db(path, data):
    """Save updated database to disk (pretty formatted)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def merge_and_save(open_cfps, db_path):
    """
    Compare new CFPs with our local DB and update percona_events.json.
    - Add new events (status=pending_approval)
    - Update existing ones
    - Mark as closed if they disappear from open CFPs
    """
    db = load_db(db_path)

    # Simple key: use name + hyperlink to identify same event
    def make_key(e):
        return f"{e.get('name','').strip()}|{e.get('hyperlink','').strip()}"

    existing = {make_key(e): e for e in db}
    current = {make_key(e): e for e in open_cfps}

    added, updated, closed = [], [], []

    # Mark as closed if event disappeared
    for event in db:
        k = make_key(event)
        if k not in current and event.get("status") != "closed":
            event["status"] = "closed"
            closed.append(event["name"])

    # Add or update open events
    for item in open_cfps:
        k = make_key(item)
        if k in existing:
            ev = existing[k]
            # Update key details (if changed)
            for field in ["cfp_url", "cfp_close", "event_start", "event_end", "location", "city", "country"]:
                if item.get(field):
                    ev[field] = item[field]
            updated.append(item["name"])
        else:
            # New event → waiting for approval
            item["status"] = DEFAULT_STATUS
            item["notified"] = False
            item["tags"] = []
            item["comments"] = ""
            db.append(item)
            added.append(item["name"])

    #  Save results
    save_db(db_path, db)

    # Return a small summary for logging
    return {
        "added": added,
        "updated": updated,
        "closed": closed,
        "count": len(db)
    }

