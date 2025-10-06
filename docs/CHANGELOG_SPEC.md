# Append-only changelog: spec and workflow

This repo maintains a single, append-only changelog at `data/changelog.csv` that tracks approved changes across runs. Per-run artifacts are written under `data/audit/runs/<run_id>/` and are ignored by Git.

## Why append-only
- Provenance: every approved change has a stable `event_id` and `run_id`.
- Idempotence: appending skips rows that already exist by `event_id`.
- Reviewability: proposed changes are reviewed locally before appending.

## Files
- `data/changelog.csv` (tracked): append-only CSV of approved changes.
- `data/audit/runs/<run_id>/proposed_changes.csv` (ignored): per-run proposed rows.
- `data/audit/runs/<run_id>/reviewed_changes.csv` (ignored): adds `event_id`, `review_status`.
- `data/audit/runs/<run_id>/run_summary.json` (ignored): counts and metadata.

## Schemas

Tracked append-only changelog (minimal columns):
- `event_id`
- `timestamp_utc`
- `run_id`
- `record_id`
- `record_name`
- `field`
- `old_value`
- `new_value`
- `reason`
- `evidence_url`
- `source_ref`
- `operator`
- `notes`

## Evidence vs. source (legacy vs. new)
Legacy migrations often cite non-URL provenance; store these in source_ref (free text). For new changes, prefer an evidence_url pointing to an official source (nyc.gov page, Executive Order, press release, Charter section). When no URL exists, leave evidence_url blank and use source_ref.

Notes:
- The tracked file is append-only and contains only the columns above.
- Extra review-time fields like `change_kind`, `reason_code`, or `review_status` are not written to the tracked file.

Per-run proposed/review files (ignored):
- Proposed input may include any useful columns for QA.
- `review_changes.py` computes `event_id`, deduplicates, and may add `review_status` for QA.
- `review_status` is not appended to the tracked file.

Run summary JSON (ignored):
- `run_id`, `started_at`, `finished_at`, `git_sha`, and `counts` {`proposed`, `approved`, `rejected`, `appended`}

## Flow
1. Produce `proposed_changes.csv` under `data/audit/runs/<run_id>/`.
2. Review and normalize: `scripts/maint/review_changes.py --run-dir ...`
   - Validates URLs (simple http/https check)
   - Normalizes whitespace/Unicode NFC
   - Computes `event_id` and deduplicates within the run
   - Approves everything by default; optional overrides with `--approvals-csv`
3. Append idempotently: `scripts/maint/append_changelog.py --run-dir ... --changelog data/changelog.csv --operator $USER`
   - Accepts `reviewed_changes.csv` with extra columns and writes only the minimal schema.
   - `reason` is taken from `reason` if present, otherwise `reason_code`, else blank.
   - `evidence_url` must match `^https?://` to be included; otherwise left blank.
   - `source_ref` is populated from non-URL `source_ref` or `feedback_source` when present.
   - Skips rows whose `event_id` already exists in `data/changelog.csv`.
   - Updates `run_summary.json` with `appended` count.

## Computing event_id
`sha256(lower(nfc(trim(record_id))) + '|' + lower(nfc(trim(field))) + '|' + lower(nfc(trim(old_value))) + '|' + lower(nfc(trim(new_value))))`

## Derived triggers (future)
When these fields change, also emit derived entries automatically:
- `name`
- `url`
- `listed_in_nyc_gov_agency_directory`
- `in_org_chart`

Placeholders should be added in the processing scripts where `proposed_changes.csv` is generated, so derived events can be appended alongside direct changes. TODO markers are acceptable until implemented.

## Commit message template

Chore: append {N} reviewed changes to data/changelog.csv

- run: {RUN_ID}
- appended rows: {N}
- operator: {USER}

Include a short summary of high-level reasons (e.g., `rename`, `po_update`).
