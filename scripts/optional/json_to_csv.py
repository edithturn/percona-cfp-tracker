#!/usr/bin/env python3
"""
Generate/refresh a Markdown table of current (non-closed) CFP events inside README.md,
and export the same rows to data/open_cfps.csv for easy import into Notion.
Content is inserted between:
  <!-- events:start --> and <!-- events:end -->
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, List, Dict, Tuple

REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(REPO_ROOT, "data", "percona_events.json")
README_PATH = os.path.join(REPO_ROOT, "README.md")
CSV_PATH    = os.path.join(REPO_ROOT, "data", "open_cfps.csv")

START_MARK = "<!-- events:start -->"
END_MARK   = "<!-- events:end -->"


def load_events(db_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def to_date_str(ts: Any) -> str:
    """Convert epoch ms (int) or ISO-like string to YYYY-MM-DD; return '' if unknown."""
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


def date_range_str(start: Any, end: Any) -> str:
    start_s = to_date_str(start)
    end_s   = to_date_str(end)
    if start_s and end_s and start_s != end_s:
        return f"{start_s} → {end_s}"
    return start_s or end_s or ""


def _tags_to_string(value: Any) -> str:
    """Normalize tags (list[str] or list[dict]) to a comma-separated string."""
    if not value:
        return ""
    def tag_to_str(tag: Any) -> str:
        if isinstance(tag, str):
            return tag
        if isinstance(tag, dict):
            return (
                tag.get("name")
                or tag.get("label")
                or tag.get("title")
                or tag.get("tag")
                or tag.get("value")
                or str(tag)
            )
        return str(tag)
    if isinstance(value, (list, tuple)):
        names = [tag_to_str(t) for t in value]
        names = [n for n in names if n]
        return ", ".join(names)
    return tag_to_str(value)


def _sort_key(e: Dict[str, Any]) -> Tuple[int, str]:
    close = e.get("cfp_close")
    close_int = 2**63 - 1
    try:
        if isinstance(close, (int, float)):
            close_int = int(close)
    except Exception:
        pass
    name = (e.get("name") or "").lower()
    return (close_int, name)


# ---------- NEW: build rows once, reuse for Markdown + CSV ----------
def build_rows(events: List[Dict[str, Any]], limit: int | None = None) -> List[Dict[str, str]]:
    """Return normalized rows for active (non-closed) events, sorted by CFP close."""
    active = [e for e in events if e.get("status") != "closed"]
    active.sort(key=_sort_key)
    if limit is not None:
        active = active[:limit]

    rows: List[Dict[str, str]] = []
    for ev in active:
        rows.append({
            "Name":        ev.get("name") or "",
            "CFP closes":  to_date_str(ev.get("cfp_close")),
            "Event dates": date_range_str(ev.get("event_start"), ev.get("event_end")),
            "Location":    ev.get("location") or ev.get("city") or ev.get("country") or "",
            "Status":      ev.get("status") or "",
            "Source tags": _tags_to_string(ev.get("source_tags")),
            "Team tags":   _tags_to_string(ev.get("tags")),
            "Link":        ev.get("cfp_url") or ev.get("hyperlink") or "",
        })
    return rows


def generate_markdown_table(rows: List[Dict[str, str]]) -> str:
    """Build GitHub-flavored Markdown table from normalized rows."""
    if not rows:
        return "_No events found._"
    header = ["Name", "CFP closes", "Event dates", "Location", "Status", "Source tags", "Team tags", "Link"]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    def esc(s: str) -> str:
        return str(s).replace("|", "\\|")
    for r in rows:
        link_md = f"[link]({r['Link']})" if r.get("Link") else ""
        lines.append(
            "| " + " | ".join([
                esc(r["Name"]), esc(r["CFP closes"]), esc(r["Event dates"]),
                esc(r["Location"]), esc(r["Status"]),
                esc(r["Source tags"]), esc(r["Team tags"]), link_md
            ]) + " |"
        )
    return "\n".join(lines)


# ---------- NEW: CSV writer ----------
def write_csv(rows: List[Dict[str, str]], csv_path: str) -> None:
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not rows:
        # still write headers for a clean empty file
        headers = ["Name","CFP closes","Event dates","Location","Status","Source tags","Team tags","Link"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    headers = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def upsert_readme_section(readme_path: str, content: str) -> None:
    header  = "## Current Open CFPs"
    section = f"{header}\n\n{START_MARK}\n{content}\n{END_MARK}\n"

    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(section)
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    if START_MARK in readme and END_MARK in readme:
        pre, _sep1, rest = readme.partition(START_MARK)
        _mid, _sep2, post = rest.partition(END_MARK)
        new_readme = f"{pre}{START_MARK}\n{content}\n{END_MARK}{post}"
    else:
        if not readme.endswith("\n"):
            readme += "\n"
        new_readme = readme + "\n" + section

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme)


def main() -> None:
    events = load_events(DB_PATH)

    # Build once → reuse
    rows   = build_rows(events)
    table  = generate_markdown_table(rows)

    # Update README section
    upsert_readme_section(README_PATH, table)

    # Also export the exact same rows to CSV (for Notion import)
    write_csv(rows, CSV_PATH)

    print(f"README updated and CSV written: {len(rows)} open CFPs → {CSV_PATH}")


if __name__ == "__main__":
    main()


