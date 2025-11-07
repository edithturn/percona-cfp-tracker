#!/usr/bin/env python3
"""
Generate/refresh a Markdown table of current (non-closed) CFP events inside README.md.
Inserts content between the markers:
  <!-- events:start --> and <!-- events:end -->
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "data", "percona_events.json")
README_PATH = os.path.join(REPO_ROOT, "README.md")

START_MARK = "<!-- events:start -->"
END_MARK = "<!-- events:end -->"


def load_events(db_path: str) -> list[dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def to_date_str(ts: Any) -> str:
    """Convert epoch ms (int) or ISO-like string to YYYY-MM-DD; return "" if unknown."""
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
    end_s = to_date_str(end)
    if start_s and end_s and start_s != end_s:
        return f"{start_s} → {end_s}"
    return start_s or end_s or ""


def generate_markdown_table(events: list[dict[str, Any]], limit: int | None = None) -> str:
    """
    Build a GitHub-flavored Markdown table for non-closed events,
    sorted by CFP close date, including source_tags and team tags.
    """
    active_events = [e for e in events if e.get("status") != "closed"]

    def sort_key(e: dict[str, Any]) -> tuple[int, str]:
        close = e.get("cfp_close")
        close_int = 2**63 - 1
        try:
            if isinstance(close, (int, float)):
                close_int = int(close)
        except Exception:
            pass
        name = (e.get("name") or "").lower()
        return (close_int, name)

    active_events.sort(key=sort_key)
    if limit is not None:
        active_events = active_events[:limit]

    lines: list[str] = []
    lines.append("| Name | CFP closes | Event dates | Location | Status | Source tags | Team tags | Link |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

    def format_tags_cell(value: Any) -> str:
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

    for ev in active_events:
        name = ev.get("name") or ""
        cfp_close = to_date_str(ev.get("cfp_close"))
        ev_dates = date_range_str(ev.get("event_start"), ev.get("event_end"))
        location = ev.get("location") or ev.get("city") or ev.get("country") or ""
        status = ev.get("status") or ""
        source_tags = format_tags_cell(ev.get("source_tags"))
        team_tags = format_tags_cell(ev.get("tags"))
        link = ev.get("cfp_url") or ev.get("hyperlink") or ""
        link_md = f"[link]({link})" if link else ""

        def esc(s: str) -> str:
            return str(s).replace("|", "\\|")

        lines.append(
            f"| {esc(name)} | {esc(cfp_close)} | {esc(ev_dates)} | "
            f"{esc(location)} | {esc(status)} | {esc(source_tags)} | {esc(team_tags)} | {link_md} |"
        )

    return "\n".join(lines) if lines else "_No events found._"


def upsert_readme_section(readme_path: str, content: str) -> None:
    header = "## Current Open CFPs"
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
    table_md = generate_markdown_table(events)
    upsert_readme_section(README_PATH, table_md)
    print(
        f"README updated with {len([e for e in events if e.get('status') != 'closed'])} active events."
    )


if __name__ == "__main__":
    main()

