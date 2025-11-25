# Percona CFP Tracker

Track open CFPs, keep a clean JSON database, and sync to a Notion database.

## Data source
- We fetch open CFP data daily from the open‑source project [developers.events](https://developers.events/), created by Aurélie Vache and maintained by the community.
- We consume the public JSON feeds provided by developers.events. 
  - ALL_EVENTS_URL → https://developers.events/all-events.json
  - ALL_CFPS_URL → https://developers.events/all-cfps.json


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

## Automated daily run (what happens every day)

Runs daily at 06:00 UTC:
- File: `.github/workflows/daily-update.yml`
- Command: `python -m scripts.main`
- Schedule: `0 4 * * *` 

This project runs automatically every day at 06:00 UTC (GitHub Actions). The job performs two steps in order:

1) Build/update the local JSON database (only open CFPs)
   - Command: `python -m scripts.main`
2) Sync to Notion and reconcile missing pages
   - Command: `python -m scripts.sync_notion --reconcile-missing`

 
## What the Notion sync updates
- On create:
  - Sets core fields from JSON: Name, Technology, URL, CFP URL, CFP Dates, Date, Event Location
  - If present in your database schema:
    - `[CFP] Status` → Open
    - `[CFP] Source` → developers.events
- On update (idempotent upsert by URL):
  - Only updates these source-controlled fields:
    - `CFP Dates` (single date from cfp_close)
    - `CFP URL`
    - `Technology` (Multi-select): merges incoming tags with existing values (does not overwrite manual tags)
  - All other properties (e.g., Name, Date, Event Location, `[CFP] Status`, `[CFP] Source`, category, notified, manual flags) are left untouched
- Reconcile (`--reconcile-missing`):
  - Scans only pages with `[CFP] Source = developers.events`
  - Marks them Closed (or archives with `--archive-missing`) when their URL is no longer present in the current JSON

## Run locally (manual testing)
```bash
# Prepare environment
cd path/to/percona-cfp-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt


# Upsert to Notion (preview first)
export NOTION_API_TOKEN='secret_...'
export NOTION_DATABASE_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

# Refresh local JSON (optionally limit for quick tests)
python -m scripts.main --limit 10 # limit for testing
python -m scripts.main # no limit

# Apply and reconcile a small batch
python -m scripts.sync_notion  --reconcile-missing --limit 10 # limit for testing
python -m scripts.sync_notion --reconcile-missing # no limit

# Note
You can apply the flag  --dry-run to see what would be done without actually doing it.
```
### Expected Notion properties
- Name (Title)
- CFP Dates (Date)
- CFP URL (URL)
- Date (Date; start/end supported)
- Event Location (Rich text)
- URL (URL)
- Technology (Multi-select)
- [CFP] Status (Status: Open, Active, Sent to Slack, Closed, Archived, Needs Review)
- [CPF] Source (Source: developers.events)

