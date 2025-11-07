from datetime import datetime, timezone
from scripts.fetch_data import fetch_and_clean
from scripts.merge_diff import merge_and_save

DB_PATH = "data/percona_events.json"

def main():
    start_time = datetime.now(timezone.utc)
    print(f"Run started at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Step 1 — Fetch & Clean (only open CFPs)
    open_cfps = fetch_and_clean()

    # Step 2/3 — Compare with DB & Save
    result = merge_and_save(open_cfps, DB_PATH)

    print(f"Updated {DB_PATH}: total={result['count']} | added={len(result['added'])} | updated={len(result['updated'])} | closed={len(result['closed'])}")

    end_time = datetime.now(timezone.utc)
    print(f"Run finished at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Duration: {(end_time - start_time).seconds} seconds")

if __name__ == "__main__":
    main()
