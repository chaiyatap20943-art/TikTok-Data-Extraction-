# TikTok Content Collector — private owner pilot

Browser UI for authorized CSV/XLSX imports, screenshot OCR/manual review,
Bangkok publication-date filtering, reconciliation, quality reports and safe Thai
CSV exports. **Live TikTok collection: NOT TESTED / NOT VERIFIED.**

End users need only a browser. Hosted deployment is pending a connected Render
account; this repository does not itself host the dynamic application.

## Current capabilities

- Default pilot: `@masterart_th`, October 1–31, 2026, Asia/Bangkok.
- Multi-file CSV/XLSX previews, configurable English/Thai column mapping.
- Missing counts remain null; K/M labels retained as rounded evidence, not exact
  counts. Missing publication time is never inferred from video IDs.
- Source labels, field quality, provisional URLs excluded from verified URL field,
  original normalized observations retained for session review.
- Deduplication only by explicitly verified video ID/link, complete snapshots
  ranked by exact metrics then observation time; conflicting snapshots flagged.
- OCR English/Thai text extraction plus mandatory manual transcription/review.
- Editable correction table, status filter, CSV and coverage JSON downloads.
- Shared owner password, session deletion/signout, no durable data storage.
- Real Playwright scroll/click/type/read against **synthetic local fixtures**.
  Production browser action is disabled pending documentary method approval.

## Development (cloud machine only)

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
# Linux runtime: chromium, tesseract-ocr-eng, tesseract-ocr-tha, Thai fonts
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```

For development set `PILOT_PASSWORD` securely in your process environment (16+
random characters), then `.venv/bin/streamlit run app.py`. Never commit the value.

```sh
docker build --target test -t collector-test .
docker build -t collector-pilot .
docker run --rm -p 8501:8501 --env PILOT_PASSWORD collector-pilot
```

Managed cloud builds may require the session CA as a BuildKit secret:
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt`. TLS verification stays enabled.
The test stage executes real browser and OCR checks as the non-root pilot user.

See [deployment](docs/DEPLOYMENT.md), [operations](docs/OPERATION.md),
[schema](docs/SCHEMA.md), [compliance](docs/COMPLIANCE.md),
[phase audit](docs/IMPLEMENTATION_PLAN.md) and [PRD](PROJECT_BRIEF.md).

## Known acceptance limits

No experimental ZIP or ten owner reference records were supplied. Synthetic test
rows are not that reference dataset. No TikTok login, scraping completion,
permission, exact hidden counts or live coverage is asserted. Phase 5 multi-user
release is not implemented. Jobs and data are ephemeral; one owner pilot only.
