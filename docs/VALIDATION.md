# Pilot delivery evidence — 2026-11-10

## Checks performed

- `.venv/bin/ruff check .` — passed.
- `TESSDATA_PREFIX=/workspace/tiktok-tessdata .venv/bin/python -m pytest -q`
  — 25 passed (8.78s). The Thai/English Tesseract models for this cloud machine
  were copied from the built image to avoid a host system installation.
- `XDG_CACHE_HOME=/workspace/cache .venv/bin/pip-audit -r requirements.lock`
  — no known vulnerabilities found at audit time.
- `.venv/bin/python -m pip check` — no broken requirements.
- `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt
  --target test -t collector-test .` — passed; **24 tests passed inside Docker**
  (10.34s); final review regression adds a 25th test. Runs as non-root `pilot`; real local Chromium and Tesseract execution.
- `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt
  -t collector-pilot .` — runtime image built successfully.
- Runtime container health and login verified separately with a disposable random
  password passed through process environment, never written into repository.

The e2e test launches Streamlit, signs in using a generated test password, uploads
synthetic UTF-8 CSV through the real browser, clicks Import & process, downloads
the CSV, and asserts Thai/emoji captions, +07:00 timestamp, missing counts, rounded
raw labels, exact zero, and deterministic file prefix. It also verifies signout.
Its screenshot is an ignored local artifact, not private owner analytics.

The separate synthetic channel fixture exercises typing, scrolling, clicking,
reading visible metrics, normalization and CSV bytes. It is not TikTok.

Initial failures were fixed rather than suppressed: test download role mismatch,
Streamlit test path resolution after dependency upgrade, and missing libatomic1
needed by the upgraded Playwright bundled Node runtime in Debian slim. The final
suite above is passing. Initial vulnerable dependency pins were upgraded and the
runtime dependency closure was pinned in requirements.lock.

## Acceptance gates

| Phase | Evidence and remaining gates |
| --- | --- |
| 0 | Empty origin audited; PRD read; plan committed. No Version 2 ZIP supplied. |
| 1 | CSV/XLSX, mapping, precision, dates, merge, exports tested. Ten owner October reference rows not supplied: reference-data gate pending. |
| 2 | Local OCR and editable manual path implemented. Synthetic image extraction tested; owner/redacted sample reconciliation gate pending. OCR needs human review. |
| 3 | Browser fixture tests passed inside Docker. Live TikTok NOT TESTED / NOT VERIFIED; production browser UI blocked pending documentary permission. |
| 4 | Docker and deploy configuration ready. No connected Render account: hosted deployment blocked by credentials/connection. No hosted URL verified. |
| 5 | Not implemented; no production multi-user claim. |

All record fields exercised by tests came from synthetic files/HTML or manual
synthetic corrections, not live account analytics. Rounded views have no exact
numeric export, missing shares/saves remain blank. No coverage of @masterart_th
has been established. A source-marked `verified` test row means fixture evidence,
not independent verification against TikTok.

GitHub native push/read works. The GitHub API is denied by this environment's
network policy, preventing API-based Actions-run inspection. The Actions web page is accessible
and is used to monitor runs. Local Docker tests and
remote CI status are separate: remote CI must not be called green without a result.

## Required next action

Connect the repository to Render using its Blueprint flow and enter a fresh
PILOT_PASSWORD privately, following DEPLOYMENT.md. Review Starter billing before
creation. Then supply the resulting URL for an actual hosted health/UI/download
check. No laptop tooling is required. Do not paste the password in chat.
