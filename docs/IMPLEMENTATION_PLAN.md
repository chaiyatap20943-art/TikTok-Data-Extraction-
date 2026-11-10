# Phase 0 audit and milestones

The checkout and GitHub origin were empty (unborn `work` branch). No existing
code, tests, experimental ZIP, ten-row owner reference CSV, or hosting binding
was available. PROJECT_BRIEF.md supplied during development is the master PRD.

1. Define schema v1; implement CSV/XLSX header mapping, Thai/Bangkok normalization,
   precision and provenance, merge/conflict handling, safe deterministic exports.
2. OCR only visible text; manual editable transcription and confirmation, private
   session retention and deletion. Never silently convert OCR text to verified facts.
3. Bounded Playwright adapter with explicit operator authorization. Local fixture
   demonstrates scroll, click, read, filtering, export. TikTok stays disabled.
4. Unit, UI, fixture and Docker checks; CI and Docker deployment to Render.
   Deployment needs a connected Render account and pilot access secret.
5. Public multi-user release is out of this pilot's scope and remains blocked
   on proper identity, durable tenant storage/jobs, monitoring and abuse controls.

Adapters return canonical records plus row issues and coverage. Missing metrics
are null; rounded displays retained separately. Raw uploads remain in the current
session only and are never committed. All fixture rows are synthetic.

Acceptance limitations: owner ten-row dataset and redacted sample not provided;
no live TikTok method permission supplied; no cloud hosting credentials supplied.
These gates must not be marked passed by synthetic checks.
