# Scripts index

`scripts/` contains runnable CLI entry points that shell users invoke directly. Reusable logic lives in the `src/nycgo_pipeline/` package; the CLIs below are thin wrappers around those modules.

## Process (ETL/exports)
- `scripts/process/manage_schema.py` — Add/modify columns in CSVs
  `python scripts/process/manage_schema.py --help`
- `scripts/process/export_dataset.py` — Export cleaned golden & public datasets; tracks `listed_in_nyc_gov_agency_directory` changes
  `python scripts/process/export_dataset.py --help`
  Optional changelog tracking: `--run-dir <path> --run-id <id> --operator <name> --previous-export <path>`
- `scripts/process/create_crosswalk.py` — Generate crosswalks between source systems
  `python scripts/process/create_crosswalk.py --help`

## Maintenance / Ops
- `scripts/maint/compare_datasets.py` — Compare original vs processed; report adds/drops
  `python scripts/maint/compare_datasets.py --help`
- `scripts/maint/compare_to_source.py` — Compare dataset to a source-of-truth extract
  `python scripts/maint/compare_to_source.py --help`
- `scripts/maint/compare_field_values.py` — Compare configured fields against a source extract
  `python scripts/maint/compare_field_values.py --help`
- `scripts/legacy/` — Historical review/publish tooling retained for archival reference (e.g., `append_changelog.py`, `review_changes.py`, `run_global_rules.py`). New runs should rely on the pipeline + publish CLIs.
# Core pipeline entry points

- `scripts/pipeline/run_pipeline.py`
  - Orchestrates a full pipeline run (generates run id, stages inputs, applies rules/QA edits, exports pre-release datasets, writes run changelog and summary)
- `scripts/pipeline/publish_run.py`
  - Validates a run folder, promotes pre-release artifacts to `_final`, archives previous `latest/`, appends `run_changelog.csv` into `data/changelog.csv`, and zips the run folder
- `scripts/maint/ingest_audit_folder.py` — Ingest legacy audit and per-run folders into append-only changelog
  `python scripts/maint/ingest_audit_folder.py --help`

## Library
- `nycgo_pipeline` (package) — Core pipeline modules (crosswalk, directory changelog, publish, etc.)
- Legacy helpers such as `utility_case_converter.py` now live under `scripts/legacy/` for reference.
