# Pilot operation and recovery

- Run one Docker service, one owner, serial bounded operations. No job queue,
  durable history or public multi-user release. Import limit: 10 files, 5 MB each,
  10,000 rows each. Screenshots: 10 MB, 20 MP, OCR timeout 30 seconds.
- Docker installs system Chromium and local Thai/English Tesseract models. No
  API keys, TikTok credentials, cookie uploads or hidden requests are required.
- Health: GET /_stcore/health; additionally test sign-in, import and download.
  A healthy port does not establish acquisition success.
- Logs: Render service Logs. Avoid logging uploads, captions, passwords or session
  objects. No private screenshot is committed or included in test artifacts.
- Restart: Render Manual Deploy / Restart. Active sessions and datasets will be
  lost. Original evidence must remain with the owner outside this ephemeral app.
- Delete: use **Delete session data and sign out**. This clears application session
  references; it is not a cryptographic memory wipe. Restart to remove process state.
  Upload widgets/Streamlit memory may persist until session expiration or process exit.
- Rotate shared pilot password in Render, then restart the service to invalidate
  existing authenticated sessions. Session cooldown is not a global brute-force
  defense. Apply host/gateway rate limits before exposure beyond the owner.
- OCR missing language pack: manual transcription works without any external key.
  The container supplies Thai and English data; verify visible strings manually.
- CSV errors: inspect per-row issues, check timestamp/headers and column mapping;
  review provisional links and K/M counts, then revalidate corrections.
- TikTok challenge or login requirement: stop. Do not retry access restrictions,
  solve challenges or import authentication cookies. Use permitted uploads.
- Browser UI stays disabled. The separate evidence adapter requires both
  ENABLE_PERMITTED_BROWSER=true and BROWSER_AUTHORIZATION_REFERENCE plus user
  authorization. These controls are not proof of valid platform approval. Review
  applicable jurisdiction/method terms before deployment; keep disabled meanwhile.
- Playwright normally disables Chromium sandbox by default; non-root UID is an
  additional boundary, not a replacement. Before permitting external browsing,
  deploy with an appropriate seccomp/sandbox policy and an outbound network filter.
  Runtime host restrictions alone are not a complete private-IP DNS defense.
