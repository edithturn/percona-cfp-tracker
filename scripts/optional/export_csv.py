#!/usr/bin/env python3
from __future__ import annotations

import os
import argparse
from typing import Any, Dict, List

from scripts.optional.json_to_csv import build_rows, write_csv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(REPO_ROOT, "data", "percona_events.json")
DEFAULT_CSV_PATH = os.path.join(REPO_ROOT, "data", "open_cfps.csv")


def load_events(db_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    try:
        import json
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CSV from local percona_events.json.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to percona_events.json")
    parser.add_argument("--out", default=DEFAULT_CSV_PATH, help="Path to write open_cfps.csv")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for rows")
    args = parser.parse_args()

    events = load_events(args.db)
    rows = build_rows(events, limit=args.limit)
    write_csv(rows, args.out)
    print(f"Wrote CSV with {len(rows)} rows → {args.out}")


if __name__ == "__main__":
    main()


