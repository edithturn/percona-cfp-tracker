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

    # Prepare summary metrics for end-of-run print
    fetched_count = len(open_cfps)
    added_count = len(result["added"])
    updated_count = len(result["updated"])
    closed_count = len(result["closed"])
    # Compute CFP close date window from fetched data
    close_dates = [to_date_str(ev.get("cfp_close")) for ev in open_cfps if ev.get("cfp_close") is not None]
    close_dates = [d for d in close_dates if d]  # drop empty conversions
    window = f"{min(close_dates)} → {max(close_dates)}" if close_dates else ""

    # Preview first 10 rows from the DB as a friendly fixed-width table
    try:
        db = load_db(DB_PATH)
        preview = db[:10]
        # Column specs: (header, width)
        cols = [
            ("Name", 44),
            ("External ID", 36),
            ("CFP closes", 12),
            ("Link", 64),
        ]
        def ellipsize(s: str, width: int) -> str:
            s = "" if s is None else str(s)
            return s if len(s) <= width else (s[: max(0, width - 1)] + "…")
        header_line = " | ".join(h.ljust(w) for h, w in cols)
        separator = "-+-".join("-" * w for _, w in cols)
        print("\nFirst 10 events (table):")
        print(header_line)
        print(separator)
        for ev in preview:
            name = ev.get("name") or ""
            external_id = ev.get("external_id") or ""
            cfp_closes = to_date_str(ev.get("cfp_close"))
            link = ev.get("cfp_url") or ev.get("hyperlink") or ""
            # Keep fixed width for first three columns; print last column without right padding
            fixed_cells = [
                ellipsize(name, cols[0][1]).ljust(cols[0][1]),
                ellipsize(external_id, cols[1][1]).ljust(cols[1][1]),
                ellipsize(cfp_closes, cols[2][1]).ljust(cols[2][1]),
            ]
            last_col = ellipsize(link, cols[3][1])
            row = " | ".join(fixed_cells + [last_col])
            print(row.rstrip())
    except Exception as e:
        print(f"Could not load preview from {DB_PATH}: {e}")

    # End-of-run concise summary (rows)
    print("\nSummary:")
    print(f"| fetched: {fetched_count}")
    print(f"| added: {added_count}")
    print(f"| updated: {updated_count}")
    print(f"| closed: {closed_count}")
    if window:
        print(f"| cfp close window: {window}")
    if args.limit is not None:
        print(f"| limit: {args.limit}")

    end_time = datetime.now(timezone.utc)
    print(f"Run finished at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Duration: {(end_time - start_time).seconds} seconds")

if __name__ == "__main__":
    main()
