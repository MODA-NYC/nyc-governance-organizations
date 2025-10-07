# Append-only changelog: spec and workflow

This repo maintains a single, append-only changelog at `data/changelog.csv` that tracks approved changes across runs. Per-run artifacts are written under `data/audit/runs/<run_id>/` and are ignored by Git. See [`docs/run_artifacts.md`](run_artifacts.md) for the baseline structure of each run folder and the required subdirectories.

## Why append-only
- Provenance: every approved change has a stable `event_id` and `run_id`.
- Idempotence: appending skips rows that already exist by `event_id`.
- Reviewability: proposed changes are reviewed locally before appending.

## Files
- `data/changelog.csv` (tracked): append-only CSV of approved changes.
- `data/audit/runs/<run_id>/outputs/run_changelog.csv` (ignored): per-run change log emitted by the pipeline.
- `data/audit/runs/<run_id>/outputs/run_summary.json` (ignored): metadata about the run and publish steps.

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
1. Run `scripts/pipeline/run_pipeline.py ...` to generate pre-release artifacts and `outputs/run_changelog.csv`.
2. Review `run_changelog.csv` and supporting review artifacts.
3. Run `scripts/pipeline/publish_run.py --run-dir ... --version ... --append-changelog` to promote artifacts, archive previous `latest/`, zip the run folder, and append rows to `data/changelog.csv`.

## Computing event_id
`sha256(lower(nfc(trim(record_id))) + '|' + lower(nfc(trim(field))) + '|' + lower(nfc(trim(old_value))) + '|' + lower(nfc(trim(new_value))))`

## Derived triggers (future)
When these fields change, also emit derived entries automatically:
- `name`
- `url`
- `listed_in_nyc_gov_agency_directory`
- `in_org_chart`

Derived events or synthetic rows should be appended to `outputs/run_changelog.csv` prior to invoking the publish step. The publish CLI expects that file to match the schema described below.

## Commit message template

Chore: append {N} reviewed changes to data/changelog.csv

- run: {RUN_ID}
- appended rows: {N}
- operator: {USER}

Include a short summary of high-level reasons (e.g., `rename`, `po_update`).
