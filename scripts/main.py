from datetime import datetime, timezone
import argparse
from scripts.fetch_data import fetch_and_clean
from scripts.merge_diff import merge_and_save, load_db

DB_PATH = "data/percona_events.json"

def to_date_str(ts):
    """Convert epoch ms (int) or ISO-like string to YYYY-MM-DD for preview output."""
    if ts is None:
        return ""
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    if isinstance(ts, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(ts, fmt)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
        return ts[:10]
    return ""

def main():
    parser = argparse.ArgumentParser(description="Fetch open CFPs and update local DB.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N events (testing)")
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    print(f"Run started at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Step 1 — Fetch & Clean (only open CFPs)
    open_cfps = fetch_and_clean()
    if args.limit is not None:
        open_cfps = open_cfps[: args.limit]

    # Step 2/3 — Compare with DB & Save
    result = merge_and_save(open_cfps, DB_PATH)

    print(f"Updated {DB_PATH}: total={result['count']} | added={len(result['added'])} | updated={len(result['updated'])} | closed={len(result['closed'])}")

    # Preview first 10 rows from the DB as a friendly table (with External ID)
    try:
        db = load_db(DB_PATH)
        preview = db[:10]
        headers = ["Name", "External ID", "CFP closes", "Link"]
        print("\nFirst 10 events (table):")
        print("| " + " | ".join(headers) + " |")
        print("| " + " | ".join(["---"] * len(headers)) + " |")
        def esc(s: str) -> str:
            return str(s).replace("|", "\\|")
        for ev in preview:
            name = ev.get("name") or ""
            external_id = ev.get("external_id") or ""
            cfp_closes = to_date_str(ev.get("cfp_close"))
            link = ev.get("cfp_url") or ev.get("hyperlink") or ""
            link_md = f"[link]({link})" if link else ""
            print("| " + " | ".join([esc(name), esc(external_id), esc(cfp_closes), link_md]) + " |")
    except Exception as e:
        print(f"Could not load preview from {DB_PATH}: {e}")

    end_time = datetime.now(timezone.utc)
    print(f"Run finished at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Duration: {(end_time - start_time).seconds} seconds")

if __name__ == "__main__":
    main()
