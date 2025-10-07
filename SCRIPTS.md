# Scripts index

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
- `scripts/maint/process_decisions.py` — Process decision logs / QA outputs
  `python scripts/maint/process_decisions.py --help`
# Core pipeline entry points

- `scripts/pipeline/run_pipeline.py`
  - Orchestrates a full pipeline run (generates run id, stages inputs, applies rules/QA edits, exports pre-release datasets, writes run changelog and summary)
- `scripts/pipeline/publish_run.py`
  - Validates a run folder, promotes pre-release artifacts to `_final`, archives previous `latest/`, appends `run_changelog.csv` into `data/changelog.csv`, and zips the run folder
- `scripts/maint/ingest_audit_folder.py` — Ingest legacy audit and per-run folders into append-only changelog
  `python scripts/maint/ingest_audit_folder.py --help`

## Library
- `src/utility_case_converter.py` — Case conversion helpers
