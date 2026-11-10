# Hosting options

For a **free pilot**, follow [Streamlit Community Cloud](STREAMLIT_CLOUD.md).
The instructions below are an optional **paid** Render alternative.

## Render private pilot deployment

Status: externally blocked until the repository is connected to a Render account.
No real hosted application URL has been created or verified by this implementation.

1. In Render, choose **New → Blueprint**, connect GitHub and grant access only to
   `chaiyatap20943-art/TikTok-Data-Extraction-`. Select `main` and `render.yaml`.
2. Review the current **Starter** price, available RAM, Docker support and billing
   in Render before accepting the paid service. The YAML intentionally avoids
   Free idle spin-down. Do not assume a free SLA or durable disk.
3. Enter a unique randomly generated `PILOT_PASSWORD` (at least 16 characters)
   through Render's secret environment-variable UI. Never send it in chat/Git.
   Keep `ENABLE_PERMITTED_BROWSER=false`. Do not upload TikTok passwords/cookies.
4. Apply the Blueprint. Docker builds the runtime as UID 10001, listens on Render's
   supplied `PORT`, and uses `/_stcore/health`. CI must pass before automatic deploy.
5. After the first deployment, open the actual Render HTTPS service URL. Confirm
   unauthenticated users see only login; sign in, import the synthetic CSV from
   `tests/fixtures/synthetic.csv`, choose October 2026 and download CSV/coverage.
   Verify Thai text, rounded blank views, exact zero likes, missing shares/saves,
   source labels and Bangkok boundaries. Sign out and verify results disappear.
6. Provide only the service URL to Codex for an independent live check. If browser
   sign-in is needed, sign in through a secure shared browser; do not paste secrets.

Render's endpoint is network reachable; the application password protects the
owner UI. For stronger private access, put an identity-aware access gateway in
front before inviting additional users. A shared password is not tenant identity.
This app is not production multi-user ready. Use TLS, never expose Streamlit
without its application password, and do not disable XSRF/CORS protections.

The container retains no uploads on persistent disk. Restart/deploy loses sessions.
No external vision API key is needed; Tesseract runs locally. Current OCR is text
extraction with review, not an automatic reliable screenshot-to-row detector.

## GitHub / CI

CI lints, audits dependencies, runs unit/UI/browser/OCR tests inside Docker and
builds the runtime. It does not deploy without your Render GitHub connection.
Do not claim CI is green until the GitHub run actually completes. A local passing
run and a remote CI result are different evidence.

No hosting connection tool or Render credential was available during development.
There is no deploy token embedded in files, and no fabricated deployment URL.
