# Scripts index

## Process (ETL/exports)
- `scripts/process/manage_schema.py` — Add/modify columns in CSVs
  `python scripts/process/manage_schema.py --help`
- `scripts/process/export_dataset.py` — Export cleaned golden & public datasets
  `python scripts/process/export_dataset.py --help`
- `scripts/process/create_crosswalk.py` — Generate crosswalks between source systems
  `python scripts/process/create_crosswalk.py --help`

## Maintenance / Ops
- `scripts/maint/compare_datasets.py` — Compare original vs processed; report adds/drops
  `python scripts/maint/compare_datasets.py --help`
- `scripts/maint/compare_to_source.py` — Compare dataset to a source-of-truth extract
  `python scripts/maint/compare_to_source.py --help`
- `scripts/maint/compare_field_values.py` — Field-level comparisons across versions
  `python scripts/maint/compare_field_values.py --help`
- `scripts/maint/process_decisions.py` — Process decision logs / QA outputs
  `python scripts/maint/process_decisions.py --help`
- `scripts/maint/prepare_run_proposed_changes.py` — Build `<run_dir>/proposed_changes.csv` from step1/step2
  `python scripts/maint/prepare_run_proposed_changes.py --help`
- `scripts/maint/publish_changelog_run.py` — Review → append to `data/changelog.csv`; optional commit/tag/release
  `python scripts/maint/publish_changelog_run.py --help`
- `scripts/maint/ingest_audit_folder.py` — Ingest legacy audit and per-run folders into append-only changelog
  `python scripts/maint/ingest_audit_folder.py --help`

## Library
- `src/utility_case_converter.py` — Case conversion helpers
- `src/utility_name_parser.py` — Name parsing helpers
(Import as `from src.utility_name_parser import ...`)
