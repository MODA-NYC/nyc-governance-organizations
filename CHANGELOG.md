# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

This section is for upcoming changes.

### Added
- Append-only audit flow with tracked `data/changelog.csv` and spec in `docs/CHANGELOG_SPEC.md`.
- Maintenance scripts:
  - `scripts/maint/make_run_id.py`, `review_changes.py`, `append_changelog.py`
  - `scripts/maint/ingest_audit_folder.py`, `prepare_run_proposed_changes.py`, `publish_changelog_run.py`
- Schema guard test: `tests/test_changelog_schema.py` (validates minimal changelog schema).
- Script index: `SCRIPTS.md` documenting runnable entrypoints.

### Changed
- Repository structure (no behavior changes):
  - Runnable entrypoints moved under `scripts/{process,maint}/`
  - Importable utilities live under `src/`
- README updated with “Step 4: Publish changelog run” and review → append flow.
- `.gitignore` refined (allow-list for `data/published/latest/*.csv`, broader cache ignores).

### Deprecated
- (Nothing yet)

### Removed
- Legacy published CSVs from `data/published/` (now keep curated `data/published/latest/` only).
- Emptied local `data/input/`, `data/output/`, and `data/intermediary` (archived to `_local_archives/`).
- Legacy audit artifacts under `data/audit/legacy/*` (history consolidated in `data/changelog.csv`).

### Fixed
- (Nothing yet)

### Security
- (Nothing yet)

---

## [2.8.0] - 2025-06-10

This version represents the state of the project prior to the major refactoring initiative. It is considered the baseline for the current work.

### Added
- Initial project structure with modular scripts (`manage_schema.py`, `process_golden_dataset.py`, `export_dataset.py`, `compare_datasets.py`).
- Core processing logic within `process_golden_dataset.py` for applying global rules and QA edits.
- `nameparser` integration for splitting `PrincipalOfficerName` into components.
- `Makefile` for streamlined setup, testing, and formatting.
- `pytest` suite for core data transformation logic.
- `pre-commit` configuration with `black` and `ruff` for code quality.
