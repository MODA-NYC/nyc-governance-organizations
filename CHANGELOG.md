# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

This section is for upcoming changes.

### Added
- Created `CHANGELOG.md` to track project versions and notable changes to the codebase.

### Changed
- (Nothing yet)

### Deprecated
- (Nothing yet)

### Removed
- `src/data_exploration.py` (exploratory script, no longer needed).
- `notebooks/phase2_profile.md` (exploratory notebook, no longer needed).
- `test_pandas_read.py` (diagnostic script, no longer needed).
- `README_phase2.8.md` (obsolete documentation).

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
