# Canonical CSV schema v1

The exact ordered field definition is `collector.data.FIELDS` and covered by tests.
Every row contains:

`account_handle, video_id, video_url, posted_at_utc, posted_at_bangkok,
posted_date_bangkok, posted_time_bangkok, caption, views, likes, comments, shares,
saves, collected_at_utc, source_type, source_reference, publication_time_quality,
metrics_precision, caption_quality, video_url_quality, record_status, notes`,
then `<metric>_displayed,<metric>_quality` for views, likes, comments, shares, saves.

- Text video IDs preserve digits. No float conversion or inferred timestamp.
- Exact timezone-qualified timestamps convert to Bangkok and UTC. Naive times
  explicitly mean Bangkok. Date-only inputs preserve the date with blank times.
- Filter is inclusive Bangkok dates (equivalent to start midnight through before
  next-day end midnight). Rows missing dates go into issues, not guessed dates.
- Source types: owner_export, owner_screenshot, authorized_browser,
  approved_provider, manual, fixture. Filename is a reference, not proof of accuracy.
- Required input is publication date for dated output; other absent fields remain
  blank/unknown. CSV/XLSX maps English/Thai aliases with a visible mapping editor.
- Optional import columns `video_url_quality=verified`, `caption_quality=full`
  require human evidence. Canonical URL shape alone is not proof it exists.
- Metric quality: exact/rounded/estimated/missing/invalid. Numeric value is null
  for rounded/estimated/missing/invalid; raw label is retained. Zero is exact zero.
- Caption quality is unknown by default. No claim that a truncated caption is full.
- Reconciliation preserves one complete observation, never mixes metrics from
  different dates. Original normalized observations remain in private session.
  Unverified-ID/date-caption matches are not automatically merged.
- Status is verified only when explicit URL/caption evidence and exact time/all
  metrics are supplied; this is source-reported, not independent platform verification.
- Output is sorted by Bangkok publication date/time then ID; missing times sort
  before known times on the same date. Deterministic filename includes snapshot day.
- UTF-8 BOM default, optional plain UTF-8. Standard CSV quoting. Text beginning
  with =,+,-,@ after whitespace gets a leading apostrophe in the safe export.
  Original uploaded/raw text remains restricted to session memory; safe CSV is
  not a lossless archival source. A safe-export reimport preserves that apostrophe.

Coverage JSON reports found source rows, included reconciled rows, outside_range,
invalid_rows, per-metric missing counts, blocked and unverified. Imports do not
probe TikTok: blocked=0 means no blocked import attempt, not TikTok accessibility.
