# Percona CFP Tracker (skeleton)

This repository tracks conference events and CFPs and can sync with Notion.

Structure:
- `data/` main JSON database and backups
- `scripts/` pipeline scripts (stubs)
- `tests/` pytest stubs
- `.github/workflows/` scheduled daily run



```mermaid
flowchart TD
    %% =====================================================
    %%               DATA FLOW DIAGRAM - PERCONA CFP TRACKER
    %% =====================================================

    %% ==== External Sources ====
    A1[🌍 developers.events API<br>(all-events.json, all-cfps.json)]
    A2[🕒 GitHub Action<br>(Scheduled Daily Run)]

    %% ==== Processes ====
    P1[⚙️ Fetch & Normalize<br>• Fetch both JSONs<br>• Validate HTTP 200 / JSON<br>• Filter CFPs with untilDate > today<br>• Join by hyperlink field]
    P2[Merge & Diff Logic<br>• Compare new vs existing data<br>• Add new CFPs (pending_approval)<br>• Update existing CFPs<br>• Mark removed as closed<br>• Validate IDs, fields]
    P3[Local JSON DB<br>percona_events.json<br>• Full internal dataset<br>• Contains approvals, tags, notified flags]
    P4[Sync JSON → Notion<br>• Create/Update pages<br>• Only overwrite system fields<br>• Keep manager fields intact]
    P5[Sync Notion → JSON<br>• Pull status, tags, comments<br>• Validate values: approved/ignored/closed<br>• Update JSON accordingly]
    P6[Slack Notifier<br>• Send to channel via Webhook<br>• Only if approved & not notified<br>• Mark notified=True]
    P7[README Generator<br>• Filter approved events<br>• Generate Markdown Table<br>• Update README.md]
    P8[Commit & Push<br>• Stage updated JSON + README<br>• Commit if changed<br>• Push to repo main branch]

    %% ==== Data Stores ====
    D1[(percona_events.json<br>local database)]
    D2[(open_cfps (in-memory)<br>filtered feed)]
    D3[(Notion Database<br>• Manager approval<br>• Comments, Tags, Category)]
    D4[(Slack Channel)]
    D5[(README.md<br>auto-generated table)]

    %% ==== Relationships ====
    A2 -->|Trigger daily run| P1
    A1 -->|Download JSONs| P1
    P1 -->|Validated CFP feed| D2

    D2 -->|Compare| P2
    P2 -->|Merged data| D1
    D1 -->|Read existing DB| P2
    P2 -->|Updated dataset| D1

    P2 -->|Sync new events| P4
    P4 -->|Create/Update rows| D3
    D3 -->|Manager updates status/comments| P5
    P5 -->|Sync manager fields| D1

    D1 -->|Filter approved + not notified| P6
    P6 -->|Post messages| D4
    P6 -->|Update notified flag| D1
    D1 -->|Approved events| P7
    P7 -->|Markdown table| D5
    D1 -->|Commit changes| P8
    D5 -->|Commit changes| P8

    P8 -->|Push to GitHub| A2

    %% ==== Validations ====
    subgraph Validations
    V1[Data Validations<br>• HTTP 200<br>• JSON parse success<br>• untilDate > today<br>• Valid timestamp]
    V2[Merge Rules<br>• Unique IDs<br>• Required fields exist<br>• Keep tags/comments/status<br>• Auto-close missing CFPs]
    V3[Notion Sync Rules<br>• Valid Notion token<br>• Respect rate limits<br>• Keep manual fields intact]
    V4[Slack Control<br>• Avoid duplicates<br>• 3 retries on fail<br>• Log notification ID]
    V5[Save & Commit<br>• File < 2MB<br>• Schema verified<br>• Only changed files committed]
    end

    P1 --> V1
    P2 --> V2
    P4 --> V3
    P6 --> V4
    P8 --> V5

    %% ==== Notes ====
    note right of D3
    Manager Actions:
    • Approves / Ignores events
    • Adds categories or comments
    • Viewed in Table or Calendar (CFP Close)
    end

    note bottom of D4
    Slack Channel Message Example:
    🎤 CFP OPEN: KCD Porto 2025
    📅 2025-11-03 → 2025-11-04
    📍 Porto, Portugal
    ⏳ Closes: 2025-06-30
    🔗 https://cfp.kcdporto.com/
    end

    note bottom of D5
    README Table Auto-Generated:
    | Event | CFP Close | Status | Category |
    |--------|------------|----------|------------|
    | KCD Porto 2025 | 2025-06-30 | Approved | Kubernetes |
end

```