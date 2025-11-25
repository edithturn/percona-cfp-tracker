#!/usr/bin/env python3
from __future__ import annotations

import os
import time
import argparse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import requests

from scripts.merge_diff import load_db

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


def require_env() -> None:
    missing = []
    if not NOTION_API_TOKEN:
        missing.append("NOTION_API_TOKEN")
    if not NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def notion_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def to_iso_date(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        # Support epoch ms
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        # Support already formatted strings like YYYY-MM-DD or ISO8601
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    continue
            # Fallback: pass through if looks like date
            return value[:10] if len(value) >= 10 else value
    except Exception:
        return None


def normalize_tag_names(value: Any) -> List[str]:
    """
    Convert a heterogeneous tags value (list[str] | list[dict] | dict | str | None)
    into a flat list of tag names suitable for Notion multi_select [{'name': name}, ...].
    """
    def tag_to_str(tag: Any) -> str:
        if isinstance(tag, str):
            return tag
        if isinstance(tag, dict):
            # Try common keys; fall back to any truthy string representation.
            for k in ("name", "label", "title", "tag", "value"):
                v = tag.get(k)
                if isinstance(v, str) and v:
                    return v
            # last resort: stringify
            return str(tag)
        return str(tag)

    if not value:
        return []
    if isinstance(value, (list, tuple)):
        names = [tag_to_str(t) for t in value]
    else:
        names = [tag_to_str(value)]
    # Deduplicate and drop empties while preserving order
    seen = set()
    out: List[str] = []
    for n in names:
        n = (n or "").strip()
        if not n:
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _normalize_url(url: str) -> str:
    """Lowercase scheme/host, strip query/fragment, trim trailing slash."""
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

def find_page_by_url(event_url: str) -> Optional[dict]:
    """Return the first page (full object) where Event URL equals the normalized URL."""
    norm = _normalize_url(event_url)
    payload = {
        "filter": {
            "property": "URL",
            "url": {"equals": norm}
        },
        "page_size": 1,
    }
    r = requests.post(
        f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
        headers=notion_headers(),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

def find_pages_by_name_and_start(name: str, start_iso: Optional[str]) -> List[dict]:
    """
    Fallback search: find pages by Name + Date start.
    Useful when the event URL changed and we want to locate/close prior rows.
    """
    if not name or not start_iso:
        return []
    payload = {
        "filter": {
            "and": [
                {"property": "Name", "title": {"equals": name}},
                {"property": "Date", "date": {"equals": start_iso}},
            ]
        },
        "page_size": 25,
    }
    r = requests.post(
        f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
        headers=notion_headers(),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("results", [])

def list_all_pages_with_url() -> List[Dict[str, str]]:
    """
    Return a list of dicts: { 'page_id': str, 'url_key': str }
    """
    pages: List[Dict[str, str]] = []
    payload: Dict[str, Any] = {"page_size": 100}
    while True:
        r = requests.post(
            f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
            headers=notion_headers(),
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        for p in data.get("results", []):
            props = p.get("properties", {})
            url_val = ""
            try:
                url_val = props.get("URL", {}).get("url") or ""
            except Exception:
                url_val = ""
            pages.append({"page_id": p["id"], "url_key": _normalize_url(url_val)})
        if data.get("has_more") and data.get("next_cursor"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break
    return pages

def get_database() -> Dict[str, Any]:
    r = requests.get(
        f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}",
        headers=notion_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def ensure_schema(verbose: bool = True) -> None:
    """
    Ensure required properties exist:
      - External ID (rich_text) is already expected
      - Source CFP Status (select) with 'Closed'
      - Active (checkbox)
    """
    db = get_database()
    props = db.get("properties", {}) or {}
    wanted: Dict[str, Any] = {}
    if "Source CFP Status" not in props:
        wanted["Source CFP Status"] = {"select": {"options": [{"name": "Closed", "color": "red"}]}}
    if "Active" not in props:
        wanted["Active"] = {"checkbox": {}}
    if not wanted:
        if verbose:
            print("Schema OK: properties exist (Source CFP Status, Active).")
        return
    if verbose:
        print(f"Adding missing properties to database: {', '.join(wanted.keys())}")
    r = requests.patch(
        f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}",
        headers=notion_headers(),
        json={"properties": wanted},
        timeout=30,
    )
    r.raise_for_status()
    if verbose:
        print("Schema update complete.")


def build_properties(ev: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map JSON fields to your Notion property names (only source-driven properties).
    Leaves manual fields (Source CFP Status, Active, Category, Notified) untouched.
    """
    name = ev.get("name") or ""
    source_tags = normalize_tag_names(ev.get("source_tags"))
    properties: Dict[str, Any] = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Technology": {"multi_select": [{"name": t} for t in source_tags]},
        "URL": {"url": _normalize_url(ev.get("hyperlink") or "") or None},
        "CFP URL": {"url": ev.get("cfp_url") or None},
        "CFP Dates": {"date": {"start": to_iso_date(ev.get("cfp_close"))}},
        "Date": {
            "date": {
                "start": to_iso_date(ev.get("event_start")),
                "end": to_iso_date(ev.get("event_end")),
            }
        },
        "Event Location": {"rich_text": [{"text": {"content": ev.get("location", "")}}]},
        # Intentionally NOT setting: legacy status fields or manual workflow fields.
    }
    return properties


def create_page(ev: Dict[str, Any], dry_run: bool = False) -> None:
    body = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": build_properties(ev),
    }
    # Default workflow status for new pages
    body["properties"]["[CFP] Status"] = {"status": {"name": "Open"}}
    if dry_run:
        print(f"[DRY-RUN] CREATE: {ev.get('name')} ({_normalize_url(ev.get('hyperlink') or '')})")
        return
    r = requests.post(
        f"{NOTION_BASE_URL}/pages",
        headers=notion_headers(),
        json=body,
        timeout=30,
    )
    r.raise_for_status()


def _merge_multi_select(existing: List[Dict[str, Any]], incoming_names: List[str]) -> List[Dict[str, str]]:
    """
    Merge existing multi-select values with incoming names (case-insensitive union).
    We keep all already selected options and add any new names from JSON.
    """
    seen: Dict[str, str] = {}
    for opt in (existing or []):
        name = (opt.get("name") or "").strip()
        if name:
            seen[name.lower()] = name
    for n in (incoming_names or []):
        nn = (n or "").strip()
        if not nn:
            continue
        key = nn.lower()
        if key not in seen:
            seen[key] = nn
    return [{"name": v} for v in seen.values()]

def update_page(page_id: str, ev: Dict[str, Any], dry_run: bool = False, existing_page: Optional[dict] = None) -> None:
    """
    Update only the allowed fields:
      - CFP Dates (single date from ev['cfp_close'])
      - CFP URL (url)
      - Technology (multi-select) → merge (preserve existing + add new)
    Do not touch other properties to preserve manual edits.
    """
    props: Dict[str, Any] = {}
    # CFP Dates
    props["CFP Dates"] = {"date": {"start": to_iso_date(ev.get("cfp_close"))}}
    # CFP URL
    props["CFP URL"] = {"url": ev.get("ccp_url") or ev.get("cfp_url") or None}
    # Technology merge
    incoming = normalize_tag_names(ev.get("source_tags"))
    existing = []
    if isinstance(existing_page, dict):
        existing = (existing_page.get("properties") or {}).get("Technology", {}).get("multi_select", [])
    props["Technology"] = {"multi_select": _merge_multi_select(existing, incoming)}

    body = {"properties": props}
    if dry_run:
        print(f"[DRY-RUN] UPDATE: {ev.get('name')} ({_normalize_url(ev.get('hyperlink') or '')})")
        return
    r = requests.patch(f"{NOTION_BASE_URL}/pages/{page_id}", headers=notion_headers(), json=body, timeout=30)
    r.raise_for_status()

def mark_page_closed(page_id: str, dry_run: bool = False) -> None:
    """
    Mark page as Closed in the CFP Status select.
    """
    body = {"properties": {"[CFP] Status": {"status": {"name": "Closed"}}}}
    if dry_run:
        print(f"[DRY-RUN] MARK CLOSED: {page_id}")
        return
    r = requests.patch(
        f"{NOTION_BASE_URL}/pages/{page_id}",
        headers=notion_headers(),
        json=body,
        timeout=30,
    )
    r.raise_for_status()

def archive_page(page_id: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[DRY-RUN] ARCHIVE MISSING: {page_id}")
        return
    r = requests.patch(
        f"{NOTION_BASE_URL}/pages/{page_id}",
        headers=notion_headers(),
        json={"archived": True},
        timeout=30,
    )
    r.raise_for_status()


def upsert_events(events: List[Dict[str, Any]], limit: Optional[int], dry_run: bool, rps: float) -> Dict[str, int]:
    rate_delay = 1.0 / max(rps, 0.1)
    created = 0
    updated = 0
    processed = 0

    for ev in events:
        if limit is not None and processed >= limit:
            break
        processed += 1
        url_key = _normalize_url(ev.get("hyperlink") or "")
        if not url_key:
            print(f"Skipping event without Event URL: {ev.get('name')}")
            continue
        page = find_page_by_url(url_key)
        # Fallback: if no page found by URL, try to locate by Name + Date.start (URL might have changed)
        if not page:
            start_iso = to_iso_date(ev.get("event_start"))
            candidates = find_pages_by_name_and_start(ev.get("name") or "", start_iso)
            # If any candidate already has the same normalized URL, treat it as the match
            for cand in candidates:
                cand_url = ""
                try:
                    cand_url = cand.get("properties", {}).get("URL", {}).get("url") or ""
                except Exception:
                    cand_url = ""
                if _normalize_url(cand_url) == url_key:
                    page = cand
                    break
            # If still not found, close duplicates that match name+date but have different URL
            if not page and candidates:
                for cand in candidates:
                    cand_url = ""
                    try:
                        cand_url = cand.get("properties", {}).get("URL", {}).get("url") or ""
                    except Exception:
                        cand_url = ""
                    if _normalize_url(cand_url) != url_key:
                        if dry_run:
                            print(f"[DRY-RUN] CLOSE DUPLICATE (URL changed): {ev.get('name')} "
                                  f"{_normalize_url(cand_url)} -> {url_key}")
                            time.sleep(rate_delay)
                        else:
                            mark_page_closed(cand["id"], dry_run=False)
                            time.sleep(rate_delay)
        if page:
            update_page(page["id"], ev, dry_run=dry_run, existing_page=page)
            updated += 1
        else:
            create_page(ev, dry_run=dry_run)
            created += 1
        time.sleep(rate_delay)

    return {"created": created, "updated": updated, "processed": processed}

def reconcile_missing(current_url_keys: set[str], dry_run: bool, rps: float, archive: bool) -> Dict[str, int]:
    """
    Find pages in the DB whose External ID is not in current_external_ids and mark them closed
    or archive them.
    """
    rate_delay = 1.0 / max(rps, 0.1)
    total = 0
    actions = 0
    pages = list_all_pages_with_url()
    for p in pages:
        total += 1
        key = p.get("url_key") or ""
        if not key:
            continue
        if key not in current_url_keys:
            if archive:
                archive_page(p["page_id"], dry_run=dry_run)
            else:
                mark_page_closed(p["page_id"], dry_run=dry_run)
            actions += 1
            time.sleep(rate_delay)
    return {"scanned": total, "affected": actions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync JSON events to Notion database (upsert by External ID).")
    parser.add_argument("--db", default="data/percona_events.json", help="Path to JSON DB file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of events to process")
    parser.add_argument("--dry-run", action="store_true", help="Print intended actions without calling Notion API")
    parser.add_argument("--rps", type=float, default=2.5, help="Requests per second throttle (<= 3 recommended)")
    parser.add_argument("--reconcile-missing", action="store_true", help="Mark or archive pages not present in the JSON")
    parser.add_argument("--archive-missing", action="store_true", help="When reconciling, archive missing pages instead of marking closed")
    parser.add_argument("--skip-upsert", action="store_true", help="Skip create/update phase; only run reconcile if requested")
    parser.add_argument("--ensure-schema", action="store_true", help="Ensure required Notion properties exist before syncing")
    args = parser.parse_args()

    require_env()
    if args.ensure_schema:
        try:
            ensure_schema(verbose=not args.dry_run)
        except requests.HTTPError as e:
            print(f"Schema check/update failed: {getattr(e.response, 'status_code', '?')} {getattr(e.response, 'text', '')}")
            raise
    events = load_db(args.db)
    if not isinstance(events, list):
        raise SystemExit(f"Invalid DB content (expected list): {args.db}")

    start = datetime.now(timezone.utc)
    print(f"Notion sync started at {start.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        result = upsert_events(events, limit=args.limit, dry_run=args.dry_run, rps=args.rps)
        print(f"Upsert complete: processed={result['processed']} created={result['created']} updated={result['updated']}")
        if args.reconcile_missing:
            # Respect --limit for reconcile: only consider the first N events when provided
            subset = events[: args.limit] if args.limit is not None else events
            current_keys = {_normalize_url(e.get("hyperlink") or "") for e in subset if e.get("hyperlink")}
            rec = reconcile_missing(current_keys, dry_run=args.dry_run, rps=args.rps, archive=args.archive_missing)
            mode = "archived" if args.archive_missing else "marked closed"
            print(f"Reconcile complete: scanned={rec['scanned']} {mode}={rec['affected']}")
    except requests.HTTPError as e:
        print(f"HTTP error: {getattr(e.response, 'status_code', '?')} {getattr(e.response, 'text', '')}")
        raise

    end = datetime.now(timezone.utc)
    print(f"Notion sync finished at {end.strftime('%Y-%m-%d %H:%M:%S %Z')} (duration: {(end - start).seconds}s)")


if __name__ == "__main__":
    main()
