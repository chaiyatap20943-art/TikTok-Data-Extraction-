# How to use this package

1. Create a GitHub repository (suggested: `tiktok-content-collector`). Keep it PRIVATE for the first pilot.
2. Upload `PROJECT_BRIEF.md` and `CODEX_START_PROMPT.md` into the repository root. You may optionally also upload the extracted contents of your prior `TikTok_Browser_Collector_v2_Experimental.zip` (do not upload the ZIP alone) so Codex can reuse tested modules. Do not upload private account credentials, cookies or sensitive screenshots.
3. Open Codex on the repository and paste the text from `CODEX_START_PROMPT.md`.
4. Let Codex implement and verify Phase 1–4 against `PROJECT_BRIEF.md` and report exact deployment blockers.
5. For a persistent shareable website, connect a suitable Docker hosting provider (e.g. Render) to the repository when prompted. GitHub alone is for source and CI; Codespaces provides temporary previews, not production hosting.

Note: TikTok live browser collection is NOT guaranteed or currently proven. The project must provide a working import-and-CSV path without prohibited scraping.
