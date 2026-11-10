# TikTok Content Collector — Project Brief / Product Requirements (PRD)

**Status:** Development specification, not proof of live TikTok collection  
**Last updated:** 2026-11-10  
**First pilot profile:** https://www.tiktok.com/@masterart_th  
**Owner's working environment:** GitHub repository + OpenAI Codex. End users must need only a web browser; do not require Python/Docker installation on their laptops.

## 1. Mission and product promise

Build and deploy a shareable, browser-based application that lets a user enter a TikTok profile URL, select an inclusive publication-date range, acquire video information from **sources the product is authorized to access**, review the results, and download standardized UTF-8 CSV files.

The product **must not** pretend that placing a URL guarantees comprehensive TikTok data. It must report data availability, authorization status, collection coverage, failures, and source quality. It must not invent share counts, favorite/save counts, exact numbers hidden behind rounded labels, full captions, or timestamps.

**Intended ideal flow:**
1. Paste `https://www.tiktok.com/@masterart_th` or another permitted profile URL.
2. Choose publication start and end dates, interpreted in `Asia/Bangkok` unless changed.
3. Choose collection method: **Own account import**, **authorized browser collection**, or **manual evidence/screenshot import**.
4. Click **Start collection**. For browser collection, only enable if documented authorization to use automated extraction is established; otherwise show a precise explanation and alternatives.
5. See progress, video counts, missing-data flags, and record-by-record quality.
6. Review/edit questionable rows; export CSV (plus an optional coverage report).

## 2. Background and existing artifacts

The user owns/manages `@masterart_th`. TikTok Studio cannot conveniently export all requested video-level metrics in one operation; some measures are not visible in the listing.

An earlier experimental source ZIP named `TikTok_Browser_Collector_v2_Experimental.zip` has these files:
- `app.py` — Streamlit prototype with URL, date selection, browser/CSV source selection, and CSV download.
- `browser_worker.py` — Playwright-based best-effort public webpage inspection. It was NOT tested successfully on a live authenticated TikTok session. It has no TikTok Studio login or secure multi-user session support.
- `collector.py` — CSV mapping, normalization, date filtering, deduplication, CSV export.
- `tests/`, `Dockerfile`, `requirements.txt`, `README.md`.
- `masterart_oct2026_reference.csv` — 10 October 2026 rows transcribed/reconciled from owner-provided TikTok Studio screenshot and an unverified public index. These are test/reference records, NOT validated results of the new browser worker. Some URLs are provisional; `K` counts are rounded; shares and saves are mostly blank.

**Codex instruction:** Inspect these files when available, reuse useful working components, identify technical and security gaps, and do not claim prior tests verify real TikTok operation. If the ZIP is not in the repository, implement from this specification without blocking.

## 3. Target users and account modes

### A. Owned account mode (pilot priority)
- The owner controls `@masterart_th` and may supply authorized TikTok Studio analytics downloads, screenshots, or individual post information.
- Build robust import and reconciliation of these sources immediately.
- Add automated TikTok Studio navigation only when an approved method of automated access is available and the account user can authenticate securely. Owning an account alone is not permission to circumvent platform controls or terms.

### B. External research mode (later, permission-gated)
- Allow a user to enter other public TikTok profile URLs.
- The app may process data that users lawfully provide or obtain from approved sources.
- Automated browsing/extraction must remain disabled unless the applicable automated collection method has explicit authorization; availability of publicly visible content is not by itself authorization to scrape it.
- No scraping private or restricted profiles, other users' accounts, or private metrics.

## 4. Core data requirements

Each video should yield one canonical record and optionally multiple metrics snapshots over time. Required export columns:

| Column | Type / rule |
|---|---|
| `account_handle` | String, e.g. `@masterart_th` |
| `video_id` | String; preserve all digits; blank if unknown |
| `video_url` | Canonical HTTPS URL when verified; blank if not verified |
| `posted_at_utc` | ISO 8601 UTC timestamp if verified |
| `posted_at_bangkok` | ISO 8601 with `+07:00` offset |
| `posted_date_bangkok` | `YYYY-MM-DD` |
| `posted_time_bangkok` | `HH:MM:SS` |
| `caption` | Full UTF-8 text if actually observed; preserve Thai, emojis, hashtags |
| `views` | Nullable integer; never fabricate exact count from rounded display |
| `likes` | Nullable integer |
| `comments` | Nullable integer |
| `shares` | Nullable integer |
| `saves` | Nullable integer; distinguish favorites/saves from likes |
| `collected_at_utc` | ISO 8601 timestamp of observation/import |
| `source_type` | `owner_export`, `owner_screenshot`, `authorized_browser`, `approved_provider`, `manual`, `fixture` |
| `source_reference` | Filename, approved source reference, or page reference (do not include credentials) |
| `publication_time_quality` | `exact`, `estimated_video_id`, `date_only`, `unknown` |
| `metrics_precision` | E.g. structured per-field quality flags or serialized JSON; see below |
| `caption_quality` | `full`, `truncated`, `unknown` |
| `video_url_quality` | `verified`, `provisional`, `missing` |
| `record_status` | `verified`, `partial`, `needs_review`, `blocked` |
| `notes` | Human-readable evidence/reconciliation notes |

Also retain **raw displayed values** such as `104K` or `11K`, stored separately from approximate numeric estimates. Recommended metric-specific fields for each of `views,likes,comments,shares,saves`: `*_displayed`, `*_quality` (`exact`, `rounded`, `estimated`, `missing`). If a numeric estimate is derived from rounded text, clearly flag it as an estimate. Never treat blank, N/A, blocked, or not-visible as `0`.

Do not silently substitute the TikTok video ID-derived approximate timestamp for the official publication time. Use it as an estimate only and flag it. Apply inclusive date filtering in the user's selected timezone: `2026-10-01 00:00:00` through **before** `2026-11-01 00:00:00` Asia/Bangkok for October 2026. Prefer half-open ranges internally to avoid subsecond boundary issues.

CSV requirements:
- Default UTF-8 with BOM (`utf-8-sig`) to open Thai text correctly in common Excel installations; offer standard UTF-8 as an optional setting.
- RFC-compliant quoting of commas, newlines and embedded quotes in captions.
- CSV formula-injection protection for attacker-controlled text fields without silently destroying source text (safe exported view plus preserved raw source in restricted storage).
- Stable sorted order by publication time; tie-break by video ID.
- Deterministic file name: `tiktok_<handle>_<start>_<end>_<snapshot_date>.csv`.
- Exact schema documented and covered by tests.
- Optional second report: coverage summary with `found`, `included`, `outside_range`, `missing_fields`, `blocked`, `unverified`, plus a warning that discovered count might be incomplete.

## 5. User interface specification

Preserve a simple, friendly interface resembling the previously approved mockup:

### Main screen
- Header: **TikTok Content Collector**.
- Input: profile URL (default `https://www.tiktok.com/@masterart_th`).
- Two date pickers: **Published from** and **Published until**; timezone default `Asia/Bangkok`.
- Method selector: `My Account / authorized import`, `Authorized browser collection`, `Screenshot / manual upload`.
- Selected output fields: date/time, caption, views, likes, comments, shares, saves, video URL.
- Start button: `Start collection` or `Import & process`, depending on method. Explicitly disable the browser action if permissions are unverified.
- Progress display: `Queued`, `Running`, `Partial`, `Blocked`, `Completed`, `Failed`, with actual pages/records processed; support cancellation and bounded retries where appropriate.
- Results: table with filters, data-source badges, missing-value indicators, and a review/edit flow.
- Download buttons: `Download CSV` and `Download Coverage Report`.
- Clear text explaining no data versus blocked/not collected versus zero matching published posts, and account-specific limits.

### Multi-user safety
- Start with a private owner pilot. Before public release, add secure user authentication, separate datasets/jobs per user, prevent cross-user result access, and apply per-user rate and concurrency limits.
- Uploaded screenshots may show account/private analytics; treat them as private, not public demo content.
- Support data deletion and retention controls.

## 6. Acquisition approaches, priority and constraints

Implement as interchangeable adapters behind one ingestion interface. Each adapter returns records with evidence/provenance and a coverage result.

**A. CSV/XLSX owner export importer (must work first)**
- Upload one or multiple files; preview headers, map varying column names, validate values, combine rows across uploads.
- Support English/Thai field names and `K/M` formatting with precision flags.
- Deduplicate by verified video ID; avoid overwriting newer exact observations with older rounded values.
- Show import errors per row rather than crash.

**B. Screenshot-to-table import (high priority)**
- Upload creator-owned TikTok Studio listing screenshots and, optionally, individual post detail screenshots.
- Extract only visible text with an appropriate vision/OCR pipeline; include confidence or review status per extracted field. No fabricated values.
- Provide an editable confirmation table before committing records.
- Merge screenshots with prior CSV/verified links by video ID when available; use date + caption as an unverified candidate match, requiring review.
- Distinguish screenshots from the example October 2026 fixture; never present fixture data as live.
- If a vision service requires an API key, make it optional via server-side secrets and provide a no-key manual-review fallback.

**C. Authorized computer/browser worker (desired innovation, gated)**
- Use Playwright in Chromium to navigate permitted web UI pages, scroll, click video tiles, inspect visible engagement information, and populate records. A screenshot/vision fallback may interpret the rendered screen if necessary.
- Build a **local fixture website** and e2e tests demonstrating real mouse/keyboard/scroll browser interaction, collection, and CSV download. Passing a fixture test does not prove TikTok access.
- Keep collection adapter isolated from frontend; apply timeouts, cancellation, bounded navigation, per-job limit and backoff on ordinary failures.
- Never defeat CAPTCHA, challenge pages, sign-in restrictions, paywalls or anti-bot protections. No stealth plugins, fingerprint evasion, proxy rotation, account-cookie theft, guessed private endpoints, or hidden API reverse engineering.
- If the site blocks access, mark `blocked`, stop, and explain what permission or user-supplied source is needed. A checkbox asserting ownership is not enough if applicable platform terms require written permission.
- Session authentication (if explicitly authorized) must happen through a secure isolated session, with user-controlled sign-in; do not ask for passwords or cookies in plaintext, commit sessions to GitHub, or share sessions across users.
- Validate TikTok profile/video hostnames and paths to avoid SSRF and redirects to arbitrary hosts. Deny localhost/private-network destinations. Disable arbitrary URLs, file URLs, and unexpected downloads.
- Accept that external-profile metrics, full captions, shares and saves may be inaccessible. Leave unavailable fields blank with provenance.

**D. Approved developer/provider source (optional future enhancement)**
- Where the owner actually has required approved access, a provider adapter may obtain authorized metrics. Do not depend on an API for the MVP, and never invent approval.

## 7. Architecture and engineering constraints

**Preferred MVP stack:** Python 3.12+, Streamlit, Playwright (Python), pandas or standard `csv`, Pydantic validation, pytest; Docker for consistent cloud runtime. Reuse the existing Streamlit and collector modules where practical.

**Separation of concerns:**
- `ui/`: Streamlit screens and form state.
- `core/schema.py`: canonical field definitions and data-quality flags.
- `core/normalize.py`: parsing, Thai/English text, date conversion, numeric precision.
- `core/reconcile.py`: merge/dedup conflict rules, provenance.
- `sources/csv_import.py`, `sources/screenshot_import.py`, `sources/browser_authorized.py`.
- `jobs/`: bounded tasks, progress, cancel, structured errors.
- `storage/`: per-user records; avoid persisting secret material.
- `export/csv_export.py`: exact schema and safe output.
- `tests/fixtures/`: synthetic HTML, screenshots (non-private or redacted), CSV.

A single-user pilot may run jobs serially with careful timeouts. **Do not call it production multi-user ready.** Before sharing broadly, add a proper background queue, durable datastore, user isolation, and concurrency controls. Do not rely on per-process Streamlit session state to manage shared jobs. Avoid storing persistent data only on an ephemeral host disk.

Security checklist: non-root browser process where feasible; sandboxing, URL allowlist, request egress controls, no secrets in source, `.env.example` only, safe file upload size limits/type checks, privacy-aware logs, secure temp-file deletion, dependency pinning, minimal containers, no public arbitrary browsing endpoint. Follow current official Playwright container hardening guidance.

## 8. GitHub and deployment specification

**GitHub role:** source of truth, issues/PR, code review, CI tests, security checks, release tags. **GitHub alone does not provide a persistent production web server for this dynamic Playwright app.** GitHub Codespaces port-forwarding may provide a temporary/private pilot, but is not a durable public deployment.

**Recommended first cloud host:** Render Docker Web Service or another Playwright-compatible container host, connected to the GitHub repository. Check current pricing, memory, container support, idle spin-down, worker runtime and storage constraints. Render Free can spin down after inactivity and has an ephemeral filesystem; do not assume it is suitable for multi-user background jobs. Do not imply a fee-free production SLA.

Required deliverables in repo:
- `Dockerfile`, `.dockerignore`, `.gitignore`, pinned dependency manifest, `README.md`, `PROJECT_BRIEF.md`.
- `.env.example` with non-secret placeholder names.
- `render.yaml` or verified step-by-step provider config, if compatible with selected deployment.
- `.github/workflows/ci.yml`: lint, unit tests, fixture browser integration tests, secure build check.
- `docs/DEPLOYMENT.md`: exact GitHub and host setup, including manual credential and permission steps.
- `docs/OPERATION.md`: run, restart, review logs, troubleshoot blocked TikTok access, retention.
- `docs/COMPLIANCE.md`: what is approved/blocked, permitted sources, no circumvention policy.
- Versioned data schema and example fixture CSV.
- Executable tests; use real assertions rather than empty smoke tests.

If user credentials, TikTok approvals, a cloud-host connection, billing approval, or provider permissions are missing, **stop at the exact externally blocked step** and report the one-time user action. Codex must never paste secrets into commits or falsely claim deployment. Once user completes actions, resume, deploy, and verify health and CSV download from the actual public/private deployment URL.

## 9. Development phases and acceptance gates

### Phase 0 — Audit and plan
- Inspect existing repository and experimental ZIP, read tests and source.
- Record defects/gaps. Define API/schema between sources and CSV output.
- Decide on cost-sensitive pilot deployment and show prerequisites.
- Commit a minimal technical plan and checklist.

### Phase 1 — Reliable ingestion/CSV baseline
- Implement URL/date validation, Thai timezone inclusive filtering, normalization, deterministic CSV.
- CSV/XLSX imports, quality/provenance flags, upload preview, merge/dedup.
- Unit tests for null vs zero, rounded K/M, Thai emoji captions, timezone boundaries, duplicate IDs, CSV injection, errors.
- **Gate:** Reference dataset loads; 10 owner-provided October 2026 records appear as source-labeled evidence, never live browser results.

### Phase 2 — Screenshot import and review
- Add screenshot upload, extraction path with required review, field-level quality, merge into canonical records.
- If vision API not configured, do not fake extraction; provide manual transcription table.
- **Gate:** A provided non-private/redacted sample can be transcribed/reviewed and exported with evidence labels.

### Phase 3 — Permitted browser automation
- Build Playwright worker with strict allowlist, timeouts and blocked-state handling.
- Demo fixture simulates scrolling/pagination, clicking videos, reading metrics, and filtering by publication timestamp.
- Production site collection must remain permission gated.
- **Gate:** Fixture browser tests pass inside Docker; live TikTok coverage only claimed after a permitted real-world test with documentary evidence, otherwise show `NOT VERIFIED`.

### Phase 4 — Deploy and validate private pilot
- Connect GitHub repo to chosen Docker host; configure approved secrets privately.
- Run CI + container build + deployment; test health endpoint/UI using the deployed URL.
- From the deployed app, import sample CSV, filter October, download output, confirm Thai characters and counts.
- **Gate:** Real hosted URL works and CSV download passes; provide URL, commit SHA, screenshots/logs, and known limitations. If external cloud permissions prevent completion, give the exact manual steps and do not report success.

### Phase 5 — Shareable multi-user release (only after pilot)
- Add authentication, isolation, durable job queue/storage, retention and privacy controls, abuse protections, monitoring.
- Load-test concurrent browser jobs within host limits and measure failures.
- **Gate:** Demonstrated no cross-user data leakage, resumable jobs, operational monitoring, and accurate availability messages. Public release only when security and collection authorization issues are resolved.

## 10. Success criteria — two separate layers

**Software delivery success:**
- GitHub repository includes complete documented code and tests; CI green.
- The cloud app is reachable without client installation, login/security appropriate to pilot.
- URL and date fields work; authorized import/screenshots work; CSV exports and provenance are accurate.
- Playwright controls a test browser on a fixture site and produces the correct CSV.

**TikTok live collection success (CONDITIONAL, must not be asserted from synthetic tests):**
- Documented permission applies to the actual collection method and account.
- The deployed worker can access the permitted TikTok page(s) without bypassing restrictions.
- Actual records match manual reference checks for publication time, caption and available metrics.
- A coverage report clearly lists blocked/unavailable fields and any partial pages.

If this second layer cannot be achieved, the app should still deploy as a functional importer/reconciliation/CSV tool and transparently show that live profile collection is unavailable.

## 11. Non-goals and prohibited behavior

- No assurance that entering *any* TikTok URL exposes all engagement metrics.
- No downloading videos or bulk archiving content unless separately approved.
- No comments harvesting, private-user info, DMs or personal data unrelated to requested video-level analytics.
- No CAPTCHA bypass, stealth evasion, proxy rotations, credential collection, reverse engineering of private TikTok endpoints, or interference with restrictions.
- No invented data. No `0` for missing or inaccessible counts.
- No public unauthenticated remote browser-control endpoint.
- No deployment 'success' claim based solely on a local simulation.

## 12. Reporting requirements for Codex at every milestone

Return:
1. What changed and which files were created/modified.
2. What tests were run with their exact commands and pass/fail results.
3. Whether TikTok live collection was tested; if not, say **NOT TESTED**.
4. Which requested fields were truly obtained and their source/precision.
5. Git branch/commit/PR links when available.
6. Deployment state: `Not started`, `Blocked by credentials`, `In progress`, `Deployed and verified`, or `Failed`.
7. Actual application URL only after it exists and a live check succeeds.
8. Exactly one concise next user action if something blocks progress.

## 13. Developer reference links

- TikTok current applicable terms: https://t.tiktok.com/legal/page/us/terms-of-service/en (US terms are jurisdiction-specific; verify applicability and authorization).
- TikTok official Research API fields (requires approved access): https://developers.tiktok.com/docs/en/research-api-specs-query-videos
- Playwright Python Docker recommendations: https://playwright.dev/python/docs/docker
- Render Docker Web Services: https://render.com/docs/web-services
- Render free-tier limitations: https://render.com/docs/free
- GitHub Codespaces port forwarding: https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace
