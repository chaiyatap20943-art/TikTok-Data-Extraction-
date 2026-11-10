# Free owner pilot: Streamlit Community Cloud

Community Cloud is a free alternative to the optional paid Render Blueprint.
Official docs describe support for one private app per account. Current terms,
resource limits and signup eligibility are controlled by Streamlit. This is a
small owner pilot, not an always-on service with an SLA.

## Deploy using only your browser

1. Open https://share.streamlit.io/ and sign in. Connect your GitHub account.
2. Choose **Create app** (or **New app**) and deploy from an existing repository.
3. Select:
   - Repository: `chaiyatap20943-art/TikTok-Data-Extraction-`
   - Branch: `main`
   - Main file: `app.py`
4. In **Advanced settings**, select **Python 3.12** and enter this TOML in
   **Secrets**, replacing the placeholder privately with your own unique random
   password of at least 16 characters:

   ```toml
   PILOT_PASSWORD = "REPLACE_WITH_YOUR_OWN_RANDOM_PASSWORD"
   ENABLE_PERMITTED_BROWSER = "false"
   ```

   Do not put secrets into GitHub files, screenshots, or chat. The app supports
   both Streamlit Secrets and process environment variables. No TikTok or vision
   API credentials are required.
5. Deploy. Community Cloud reads `requirements.txt` and installs the system OCR
   packages in `packages.txt`; it does not use our Dockerfile or render.yaml.
6. In **Settings → Sharing**, choose **Only specific people can view this app**
   and keep the initial pilot restricted to yourself. A public GitHub repository
   makes the app public by default, so check this explicitly before uploading
   private analytics. Keep the application password as a second gate.
7. Open the actual `.streamlit.app` URL. Sign in, upload the synthetic CSV from
   `tests/fixtures/synthetic.csv`, choose October 2026, and download CSV/coverage.
   Check Thai text, rounded views, blank unavailable counts and exact zero likes.
8. Send only the resulting app URL back to Codex for a hosted check. Never send
   the pilot password. A private service may require you to complete sign-in in
   a secure browser before independent verification is possible.

## Capabilities and limitations

Imports, mapping, Bangkok filtering, manual screenshot review, local OCR and CSV
exports use the same application as the Docker pilot. The host may sleep or
restart, and all session data is ephemeral: download exports promptly. OCR can
run out of resources; the manual transcription fallback remains available.
Chromium is intentionally not installed by packages.txt. Production browser
collection is disabled; local/Docker fixture tests do not prove live TikTok access.

Only Python requirements and Debian packages are prepared here; no Community
Cloud deployment has yet been created or verified. A GitHub-connected Community
Cloud account and one-time secure secret entry remain necessary. There is no
verified hosted URL yet. Do not apply the paid Render Blueprint for this free path.

Community Cloud's documentation currently states apps are hosted in the United
States; consider this before uploading private analytics. Platform telemetry and
access logs are governed by its policy, separately from the app's session-only
retention. This pilot is not a production multi-user release.

## Official sources checked

The documentation website was denied by this development environment's network
policy. The same official documentation was read from `streamlit/docs` on GitHub
at commit `902ba7e401a96b5fcb3d96df85e8856ac4518390`:

- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/status
