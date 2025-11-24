# Percona CFP Tracker

Track open CFPs, keep a clean JSON database, and sync to a Notion database.

## Repo layout
- `data/` JSON database and CSV export
- `scripts/` pipeline and utilities
- `.github/workflows/` scheduled daily run (optional)

## Matching key (URL-based)
- We match items by normalized URL (lowercase host/scheme, strip query/fragment, drop trailing slash).
- If a source changes an event URL, a new page will be created and the old one will be marked Closed during reconcile.

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

Reconcile (mark pages not in JSON as “[CFP] Status = Closed”, or archive with the flag):
```bash

# Safe preview first (no writes):
python -m scripts.sync_notion --reconcile-missing --dry-run

# Only consider the first N JSON rows for reconcile
python -m scripts.sync_notion --limit N --reconcile-missing --skip-upsert

```

```
Notes:
- Upsert writes source-driven fields (Name, Technology, URL, CFP URL, CFP Dates, Date, Event Location).
- “[CFP] Status” (Status property in Notion) is set to Open on create and to Closed during reconcile; otherwise we don’t overwrite it.
- Use `--rps 2` if you hit Notion rate limits.

### Expected Notion properties
- Name (Title)
- URL (URL)
- CFP URL (URL)
- CFP Dates (Date)
- Date (Date; start/end supported)
- Event Location (Rich text)
- Technology (Multi-select)
- [CFP] Status (Status: Open, Active, Sent to Slack, Closed, Archived, Needs Review)

## Data source overrides (optional)
- `ALL_EVENTS_URL`
- `ALL_CFPS_URL`
Defaults (if not set) pull from developers.events:
- ALL_EVENTS_URL → https://developers.events/all-events.json
- ALL_CFPS_URL → https://developers.events/all-cfps.json

## GitHub Actions (optional)
Runs daily at 06:00 UTC:
- File: `.github/workflows/daily-update.yml`
- Command: `python -m scripts.main`
- Schedule: `0 6 * * *`