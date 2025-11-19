# Percona CFP Tracker (skeleton)

This repository tracks conference events and CFPs and can sync with Notion.

Structure:
- `data/` main JSON database and backups
- `scripts/` pipeline scripts (stubs)
- `.github/workflows/` scheduled daily run

## Requirements
- Python 3.11+
- Pip packages: installed via `requirements.txt` (currently `requests`)

## Setup (recommended with virtualenv)
```bash
cd /Users/edithpuclla/workspace/demos-super/percona-cfp-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Note: Activate the venv in each new shell with `source .venv/bin/activate`.

## Run locally
The pipeline fetches open CFPs, merges them into the local DB, and writes to `data/percona_events.json`.

```bash
python -m scripts.main
python -m scripts.update_readme  # refresh the table in README
```

Output:
- Logs start/end time and a summary of added/updated/closed events
- Writes/updates `data/percona_events.json`

## Environment variables (optional for future steps)
These are used by stub scripts and the GitHub workflow for future integrations:
- `NOTION_API_TOKEN`
- `NOTION_DATABASE_ID`
- `SLACK_WEBHOOK_URL`

Data source overrides (optional; defaults with fallback are built-in):
- `ALL_EVENTS_URL` (e.g., a mirror for all-events.json)
- `ALL_CFPS_URL` (e.g., a mirror for all-cfps.json)

## GitHub Actions
A daily workflow runs the pipeline at 06:00 UTC:
- File: `.github/workflows/daily-update.yml`
- Command: `python -m scripts.main`
- Schedule (cron): `0 6 * * *`

## Notes
- `scripts/` is a Python package; imports use `from scripts.fetch_data import fetch_and_clean`.
- The Notion/Slack scripts are stubs and can be implemented incrementally.

## Current Open CFPs

<!-- events:start -->
| Name | CFP closes | Event dates | Location | Status | Source tags | Team tags | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Microsoft Fabric Community Conference - FABCON 2026 - SESSIONS | 2025-11-20 | 2026-03-16 → 2026-03-20 | Atlanta, GA (USA) | pending_approval | microsoft, data, english |  | [link](https://sessionize.com/fabcon2026sessions) |
| DevConf.IN 2026 | 2025-11-21 | 2026-02-13 → 2026-02-14 | Pune (India) | pending_approval | open-source, red-hat, developer, community, community-building, free-software, technology, english |  | [link](https://pretalx.devconf.info/devconf-in-2026/cfp) |
| DevFest Addis 2025 | 2025-11-21 | 2025-12-13 | Addis Ababa (Ethiopia) | pending_approval | devops, ai, cloud, amharic |  | [link](https://app.advocu.com/events/68f26abc519905361385d98b) |
| DevFest Calabar 2025 | 2025-11-21 | 2025-12-13 | Calabar (Nigeria) | pending_approval | google, web-development, english |  | [link](https://sessionize.com/devfest-calabar-2025/) |
| DevFest'25 Kocaeli | 2025-11-22 | 2025-12-06 | Izmit (Turkey) | pending_approval | google-cloud, android, web-development, turkish |  | [link](https://app.advocu.com/events/68af150f04c92b1c261973a6) |
| T3chfest | 2025-11-23 | 2026-03-12 → 2026-03-13 | Madrid (Spain) | pending_approval | javascript, python, web-development, spanish, english |  | [link](https://t3chfest.es/2026/en/call-for-talks/) |
| Apres-Cyber Slopes Summit 2026 | 2025-11-28 | 2026-02-26 → 2026-02-27 | Park City, UT (USA) | pending_approval | cybersecurity, technology, security, english |  | [link](https://sessionize.com/apres-cyber-slopes-summit-2026/) |
| DevFest Armenia 2025 | 2025-11-29 | 2025-12-20 | Yerevan (Armenia) | pending_approval | devops, ai, cloud, armenian |  | [link](https://app.advocu.com/events/68eca6af7c50489f26c341f8) |
| Codemotion Madrid | 2025-11-30 | 2026-04-20 → 2026-04-21 | Madrid (Spain) | pending_approval | software-development, agile, spanish |  | [link](https://sessionize.com/codemotion-madrid-2026/) |
| Cybersec Asia x Thailand International Cyber Week 2026 (powered by NCSA) | 2025-11-30 | 2026-02-04 → 2026-02-05 | Bangkok (Thailand) | pending_approval | cybersecurity, technology, security, thai |  | [link](https://www.papercall.io/cybersecasia26) |
| DevFest Gwalior 2025 | 2025-11-30 | 2025-12-20 | Gwalior (India) | pending_approval | devops, ai, cloud, hindi |  | [link](https://app.advocu.com/events/68ed31dd7c50489f26c41038) |
| DevFest Kathmandu 2025 | 2025-11-30 | 2025-12-06 | Kathmandu (Nepal) | pending_approval | google, web-development, english |  | [link](https://sessionize.com/devfest-kathmandu-2025/) |
| Devfest Kigali 2025 | 2025-11-30 | 2025-12-19 → 2025-12-20 | Kigali (Rwanda) | pending_approval | android, web, google-cloud, firebase, kinyarwanda |  | [link](https://app.advocu.com/events/68d2d492be9820a862b5f0f4) |
| DevFest Makassar 2025 | 2025-11-30 | 2025-12-20 | Makassar (Indonesia) | pending_approval | devops, cloud, open-source, indonesian |  | [link](https://app.advocu.com/events/68f1cc1e51990536138511b2) |
| DevOpsCon & MLCon 2026 | 2025-11-30 | 2026-04-20 → 2026-04-24 | Amsterdam (Netherlands) | pending_approval | devops, ai, machine-learning, english |  | [link](https://sessionize.com/devopsconmlcon-2026) |
| KotlinConf 2026 | 2025-11-30 | 2026-05-20 → 2026-05-22 | Munich (Germany) | pending_approval | kotlin, english, german |  | [link](https://sessionize.com/kotlinconf-2026) |
| stackconf 2026 | 2025-11-30 | 2026-04-28 → 2026-04-29 | Munich (Germany) | pending_approval | various, cloud-computing, devops, german |  | [link](https://stackconf.eu/propose/) |
| DevCon #26 : sécurité / post-quantique / hacking | 2025-12-01 | 2026-01-22 | Paris (France) | pending_approval | security, development, english |  | [link](https://docs.google.com/forms/d/e/1FAIpQLScAkKRuLpmUYUyxBP7uVCpWLxShOUxvDD7rKbAiz_4njAyMRQ/viewform?usp=header) |
| IntelliC0N Austin 2026 | 2025-12-01 | 2026-02-06 | Austin, TX (USA) | pending_approval | security, english |  | [link](https://www.papercall.io/intellic0naustin2026) |
| RubyConf Austria 2026 | 2025-12-01 | 2026-05-29 → 2026-05-31 | Vienna (Austria) | pending_approval | ruby, web-development, english, german |  | [link](https://www.papercall.io/rubyconfaustria2026) |
| Visual Studio Live! @ Microsoft HQ 2026 | 2025-12-01 | 2026-07-27 → 2026-07-31 | Redmond, WA (USA) | pending_approval | dotnet, microsoft, english |  | [link](https://sessionize.com/vslive_Microsoft26) |
| Voxxed Days Zurich | 2025-12-01 | 2026-03-24 | Zurich (Switzerland) | pending_approval | voxxed, developer, technology, german |  | [link](https://vdz26.cfp.dev/) |
| Programmable 2026 - Melbourne | 2025-12-02 | 2026-03-17 | Melbourne (Australia) | pending_approval | web-development, english |  | [link](https://sessionize.com/programmable-2026-melbourne) |
| Programmable 2026 - Sydney | 2025-12-02 | 2026-03-19 | Sydney (Australia) | pending_approval | web-development, english |  | [link](https://sessionize.com/programmable-2026-sydney) |
| KCD New Delhi | 2025-12-04 | 2026-02-21 | New Delhi (India) | pending_approval |  |  | [link](https://sessionize.com/kcd-new-delhi) |
| NDC Sydney 2026 | 2025-12-06 | 2026-04-20 → 2026-04-24 | Sydney (Australia) | pending_approval | dotnet, software-development, english |  | [link](https://sessionize.com/ndc-sydney-2026) |
| PyTexas 2026 | 2025-12-07 | 2026-04-17 → 2026-04-19 | Austin, TX (USA) | pending_approval | python, english |  | [link](https://pretalx.com/pytexas-2026/cfp) |
| Green IO Paris | 2025-12-09 | 2025-12-09 → 2025-12-11 | Paris (France) | pending_approval | green-it, sustainability, english |  | [link](https://apidays.typeform.com/to/SMHd2wFE?=green-io-conference%3Dcall-for-speakers&typeform-source=greenio.tech) |
| DataGrillen 2026 | 2025-12-14 | 2026-05-21 → 2026-05-22 | Lingen (Germany) | pending_approval | data, data-management, german |  | [link](https://sessionize.com/datagrillen-2026/) |
| FOSSASIA Summit 2026 | 2025-12-15 | 2026-03-09 → 2026-03-10 | Bangkok (Thailand) | pending_approval | open-source, hardware, linux, web3, security, postgresql, english |  | [link](https://summit.fossasia.org/speaker-registration) |
| Future Tech 2026 | 2025-12-15 | 2026-03-11 | Utrecht (Netherlands) | pending_approval | web-development, dutch |  | [link](https://sessionize.com/future-tech-2026) |
| Java Day Istanbul 2026 | 2025-12-15 | 2026-05-09 | Istanbul (Turkey) | pending_approval | java, software-development, turkish |  | [link](https://www.papercall.io/javadayistanbul2026) |
| Perl Community Conference, Winter 2025 | 2025-12-15 | 2025-12-17 → 2025-12-18 | Austin, TX (USA) | pending_approval |  |  | [link](https://www.papercall.io/perlcommunityconferencew25) |
| SQLDay 2026 | 2025-12-15 | 2026-05-11 → 2026-05-13 | Wroclaw (Poland) | pending_approval | sql, data, english, polish |  | [link](https://sessionize.com/sqlday-2026/) |
| Appdevcon Conference 2026 | 2025-12-19 | 2026-03-10 → 2026-03-13 | Amsterdam (Netherlands) | pending_approval | app-development, software-engineering, technology, english |  | [link](https://sessionize.com/adc-dpc-wdc-2026) |
| Dutch PHP Conference 2026 | 2025-12-19 | 2026-03-10 → 2026-03-13 | Amsterdam (Netherlands) | pending_approval | php, web-development, programming, english |  | [link](https://sessionize.com/adc-dpc-wdc-2026) |
| Webdevcon Conference 2026 | 2025-12-19 | 2026-03-10 → 2026-03-13 | Amsterdam (Netherlands) | pending_approval | web-development, frontend, backend, english |  | [link](https://sessionize.com/adc-dpc-wdc-2026) |
| Voxxed Days Bucharest | 2025-12-21 | 2026-04-28 → 2026-04-29 | Bucharest (Romania) | pending_approval | java, kotlin, scala, romanian |  | [link](https://vdbuh2026.cfp.dev/#/login) |
| TestBash Brighton 2025 | 2025-12-22 | 2025-10-01 → 2025-10-02 | Brighton (UK) | pending_approval | testing, english |  | [link](https://www.ministryoftesting.com/contribute) |
| Security BSides Prague 2026 | 2025-12-24 | 2026-04-23 → 2026-04-24 | Prague (Czech Republic) | pending_approval | security, english, czech |  | [link](https://www.papercall.io/bsidesprg2026) |
| Baltic Ruby 2026 | 2025-12-31 | 2026-06-12 → 2026-06-13 | Hamburg (Germany) | pending_approval | ruby, programming, german |  | [link](https://www.papercall.io/balticruby2026) |
| MiXiT 2026 | 2026-01-04 | 2026-04-16 → 2026-04-17 | Lyon (France) | pending_approval | devops, agile, french |  | [link](https://sessionize.com/mixit-2026/) |
| Blastoff Rails | 2026-01-11 | 2026-06-11 → 2026-06-12 | Albuquerque, NM (USA) | pending_approval | rails, web-development, english |  | [link](https://www.papercall.io/blastoff) |
| CypherCon 9 (2026) | 2026-01-12 | 2026-04-01 → 2026-04-02 | Milwaukee, WI (USA) | pending_approval | cypher, database, technology, english |  | [link](https://sessionize.com/cyphercon-9-2026/) |
| wroclove.rb 2026 | 2026-01-13 | 2026-04-17 → 2026-04-19 | Wroclaw (Poland) | pending_approval | ruby, english, polish |  | [link](https://www.papercall.io/wrocloverb2026) |
| DataMeshLive | 2026-01-16 | 2026-06-11 → 2026-06-12 | Antwerp (Belgium) | pending_approval | data, data-management, data-science, architecture, software-architecture |  | [link](https://2026.datameshlive.com/cfp) |
| Domain-Driven Design Europe | 2026-01-16 | 2026-06-08 → 2026-06-12 | Antwerp (Belgium) | pending_approval | software, domain-driven-design, architecture, software-architecture, ai |  | [link](https://2026.dddeurope.com/cfp/) |
| WeAreDevelopers World Congress 2026 - Europe | 2026-01-16 | 2026-07-08 → 2026-07-10 | Berlin (Germany) | pending_approval | python, data, open-source, english |  | [link](https://sessionize.com/wearedevelopers-world-congress-2026-europe) |
| SREday London 2026 Q1 | 2026-01-30 | 2026-03-12 | London (UK) | pending_approval | devops, english |  | [link](https://www.papercall.io/sreday-2026-london-q1) |
| DevOpsDays Zurich 2026 | 2026-01-31 | 2026-05-06 → 2026-05-07 | Winterthur (Switzerland) | pending_approval | devops, english, german |  | [link](https://sessionize.com/devopsdays-zurich-2026) |
| HackConRD 2026 | 2026-01-31 | 2026-03-27 → 2026-03-28 | Santo Domingo (Dominican Republic) | pending_approval | security, spanish |  | [link](https://www.papercall.io/hackconrd-2026-cfp) |
| Securing AI in the Real World: Call for Practitioner Stories – AI Security Conference | 2026-01-31 | 2026-04-25 | Online | pending_approval | security, ai, english |  | [link](https://www.papercall.io/ai-security-msec) |
| Weblica 2026 | 2026-01-31 | 2026-05-08 | Strigova (Croatia) | pending_approval | web-development, english, croatian |  | [link](https://sessionize.com/weblica-2026) |
| DevopsDay Prague 2026 | 2026-02-01 | 2026-04-29 | Prague (Czech Republic) | pending_approval | devops, english, czech |  | [link](https://www.papercall.io/dodprague26) |
| Web Days Convention | 2026-02-02 | 2026-02-02 → 2026-02-06 | Aix-en-Provence (France) | pending_approval | web, technology, innovation, french |  | [link](https://conference-hall.io/web-days-convention) |
| DevOpsDays Geneva 2026 | 2026-02-06 | 2026-05-21 → 2026-05-22 | Geneva (Switzerland) | pending_approval | devops, automation, infrastructure, english |  | [link](https://devopsdays-geneva.ch/forms/InputFormSpkrsDodGe.php?who=pb0cb47956025e73c797e5e17f16fc38466e34f5ae) |
| XtremeAI 2026 | 2026-02-10 | 2026-06-02 | Online | pending_approval | ai, artificial-intelligence, english |  | [link](https://forms.gle/UoGXzvoNi8C2vHkRA) |
| XtremeJ 2026 | 2026-02-10 | 2026-05-12 | Online | pending_approval |  |  | [link](https://forms.gle/UoGXzvoNi8C2vHkRA) |
| XtremeJS 2026 | 2026-02-10 | 2026-05-19 | Online | pending_approval |  |  | [link](https://forms.gle/UoGXzvoNi8C2vHkRA) |
| XtremePython 2026 | 2026-02-10 | 2026-05-26 | Online | pending_approval |  |  | [link](https://forms.gle/UoGXzvoNi8C2vHkRA) |
| CfgMgmtCamp 2026 Ghent | 2026-02-15 | 2026-02-02 → 2026-02-04 | Ghent (Belgium) | pending_approval | configuration-management, automation, devops, english |  | [link](https://cfp.cfgmgmtcamp.org/ghent2026/cfp) |
| Container Days Hamburg 2026 | 2026-02-28 | 2026-09-02 → 2026-09-04 | Hamburg (Germany) | pending_approval | container-days, containers, open-source, english |  | [link](https://sessionize.com/containerdays-hamburg-2026) |
| Monkigras 2026 | 2026-02-28 | 2026-03-19 → 2026-03-20 | London (UK) | pending_approval | web-development, english |  | [link](https://www.papercall.io/monkigras26) |
| Cloud Native Days Italy | 2026-03-06 | 2026-05-18 → 2026-05-19 | Bologna (Italy) | pending_approval | kubernetes, ai, fintech, italian, english, sre, platform, platform-engineering, developer-experience |  | [link](https://sessionize.com/cloud-native-days-italy-2026) |
| CFCamp 2026 | 2026-03-09 | 2026-06-18 → 2026-06-19 | Munich (Germany) | pending_approval | coldfusion, english, german |  | [link](https://www.papercall.io/cfcamp2026) |
| DevLille 2026 | 2026-03-31 | 2026-07-11 → 2026-07-12 | Lille (France) | pending_approval |  |  | [link](https://conference-hall.io/devlille-2026) |
| WeAreDevelopers World Congress 2026 - North America | 2026-03-31 | 2026-09-23 → 2026-09-25 | San Jose, CA (USA) | pending_approval | python, data, open-source, english |  | [link](https://sessionize.com/wearedevelopers-world-congress-2026-us) |
| Green IO Singapore | 2026-04-14 | 2026-04-14 → 2026-04-15 | Singapore (Singapore) | pending_approval | green, sustainability, english |  | [link](https://apidays.typeform.com/to/SMHd2wFE?=green-io-conference%3Dcall-for-speakers&typeform-source=greenio.tech) |
| Cyber Security for Critical Assets Canada | 2026-05-03 | 2026-06-02 → 2026-06-03 | Calgary (Canada) | pending_approval | cybersecurity, english |  | [link](https://canada.cs4ca.com/submit-speaking-proposal/) |
<!-- events:end -->

## Troubleshooting
- ModuleNotFoundError: No module named 'requests'  
  Ensure the virtualenv is activated (`source .venv/bin/activate`) and run `python -m pip install -r requirements.txt`.

