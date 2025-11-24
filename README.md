# Percona CFP Tracker

Track open CFPs, keep a clean JSON database, and sync to a Notion database.

## Repo layout
- `data/` JSON database and CSV export
- `scripts/` pipeline and utilities
- `.github/workflows/` scheduled daily run (optional)

## External ID (stable key)
- Format: `source :: normalized-hyperlink :: event_start`
- URL normalization: lowercase scheme/host, strip query/fragment (utm, etc.), drop trailing slash.
- Rationale: avoids churn when names/cities change; IDs stay stable across minor edits.

## Requirements
- Python 3.11+
- Install deps:
  - `python -m pip install -r requirements.txt`

## Setup
```bash
# cd into your local clone of this repo
cd path/to/percona-cfp-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Note: Activate the venv each new shell: `source .venv/bin/activate`.

## Daily workflow (recommended)
1) Fetch and update the local DB (only open CFPs)
```bash
python -m scripts.main
```
2) Upsert current events into Notion (creates/updates)
```bash
export NOTION_API_TOKEN='secret_...'
export NOTION_DATABASE_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
python -m scripts.sync_notion
```
3) Close any pages missing from today’s JSON (or archive)
```bash
python -m scripts.sync_notion --reconcile-missing
# or: python -m scripts.sync_notion --reconcile-missing --archive-missing
```

Reconcile (mark pages not in JSON as Closed and Active=false):
```bash

# Safe preview first (no writes):
python -m scripts.sync_notion --reconcile-missing --dry-run

# Only consider the first N JSON rows for reconcile
python -m scripts.sync_notion --limit N --reconcile-missing --skip-upsert

# Ensure required columns exist (Source CFP Status: Select, Active: Checkbox)
python -m scripts.sync_notion --ensure-schema

```

## Optional Commands (run independently) on local machine
- Refresh README table from DB:
```bash
python -m scripts.optional.update_readme
```
- Export CSV from DB:
```bash
python -m scripts.optional.export_csv
```
- Pretty preview (console) of first 10 events:
```bash
python -m scripts.main    # already prints a Markdown table preview
```

```
Notes:
- Upsert writes source-driven fields (Name, External ID, Source, Source Tags, URLs, dates, location).
- Manual fields (Source CFP Status, Active, Category, Notified) are left intact except during reconcile.
- Use `--rps 2` if you hit Notion rate limits.

## Data source overrides (optional)
- `ALL_EVENTS_URL`
- `ALL_CFPS_URL`

## GitHub Actions (optional)
Runs daily at 06:00 UTC:
- File: `.github/workflows/daily-update.yml`
- Command: `python -m scripts.main`
- Schedule: `0 6 * * *`