# NYC Governance Organizations Pipeline Refactor

This document captures the agreed roadmap for reorganizing the publication pipeline, file layout, and supporting tooling. It supersedes ad-hoc notes in this chat and should be kept in sync during implementation.

---

## Phase 0 · Baseline & Conventions

- **Run artifact contents**: every pipeline execution must bundle the following under `data/audit/runs/<run_id>/`:
  - Inputs (`inputs/`):
    - Golden dataset snapshot used for the run
    - Previous published dataset snapshot
    - “Edits to make” CSV that drove the run
  - Outputs (`outputs/`):
    - Generated golden dataset (pre-release suffix)
    - Generated published dataset (pre-release suffix)
    - Run changelog CSV
    - Run summary JSON (with record counts, key field rollups, etc.)
  - Review aids (`review/`):
    - Comparison/QA reports (source checks, summary stats)

- **Naming conventions**:
  - Run folders: `YYYYMMDD-HHMM_<descriptor>` (include UTC or timezone indicator).
  - Pre-release outputs: `*_pre-release.csv` / `.json`.
  - Final outputs (once published): `*_final.csv` placed in `data/published/` and `data/published/latest/`.

- **Versioning**:
  - Transition to semantic versions beginning at **v1.0** for the next release.
  - Maintain a manifest or annotation tying run ids to dataset versions.

- **Documentation**: merge `CHANGELOG.md` narrative into `README.md`; retain specs in `/docs/` with updated references.

---

## Phase 1 · Source Package Restructure

1. Create `src/nycgo_pipeline/` package and move core modules:
   - `global_rules.py`, `qa_edits.py`, `export.py`, `schema.py`, `crosswalk.py`, `directory_changelog.py`, and utilities.
2. Update imports, tests, and tooling to reference the new package namespace.
3. Add a high-level `pipeline.py` module that exposes an orchestration function (global rules → apply edits → export → changelog prep).

---

## Phase 2 · Pipeline & Publish CLI

### 2.1 Pipeline CLI
- Implement `scripts/pipeline/run_pipeline.py` that:
  1. Generates a run id (fallback to `nogit` if git SHA unavailable).
  2. Copies required inputs into `runs/<run_id>/inputs/`.
  3. Calls orchestrator modules to run global rules, apply edits, and export datasets, writing artifacts to `outputs/` with `*pre-release*` suffixes.
  4. Generates run changelog and run summary (`run_summary.json`).
  5. Produces review aids (`review/`), including source comparisons and summary stats.

> Note: the previous `proposed_changes.csv` / `reviewed_changes.csv` flow is retired; the per-run changelog supersedes them.

### 2.2 Publish CLI
- Implement `scripts/pipeline/publish_run.py` that:
  1. Validates the run folder contents.
  2. Moves any existing files from `data/published/latest/` into `data/published/archive/` with version-stamped names.
  3. Copies final golden/published datasets (renaming to `*_final.csv`) into `data/published/` and `data/published/latest/`.
  4. Appends the run changelog to `data/changelog.csv`.
  5. Archives the entire run folder into `dist/nycgo-run-<run_id>.zip`.
  6. Tags/releases the version (prepare for `gh release` integration; initially, emit instructions if CLI unavailable).

---

## Phase 3 · Utilities Reorganization

- Move analyst utilities under `tools/` with thin wrappers that call into `nycgo_pipeline.source_checks`:
  - `tools/source_checks/compare_to_source.py`
  - `tools/source_checks/compare_field_values.py`
  - Core logic lives in `src/nycgo_pipeline/source_checks/`
  - `tools/changelog/` → helper scripts reused by the publish CLI (if still needed).
  - Retire or archive `compare_datasets.py` if no longer part of standard workflow (e.g., `archive/one-off/compare_datasets.py`).
- Ensure utilities produce outputs directly within the run folder when invoked by the pipeline.

---

## Phase 4 · Data Layout Cleanup

- Deprecate `data/output/`; update code/tests to avoid writing there.
- Establish run folder subdirectories (`inputs/`, `outputs/`, `review/`).
- Add `data/published/archive/` to hold prior `latest/` snapshots.
- Standardize file names for traceability (include version + run id in filenames where appropriate).

---

## Phase 5 · Documentation & Tests

- Update `README.md` with:
  - Repo structure map
  - Pipeline run instructions
  - Publish workflow & versioning policy
  - Data directory overview & naming conventions
- Relocate or rename supporting docs (`CHANGELOG_SPEC.md` stays in `/docs/` or is merged into README).
- Refresh tests to match new modules and to cover run-folder generation logic.
- Add lightweight documentation in `/docs/` for utilities (`tools/` usage, review aids).

---

## Phase 6 · Optional Enhancements (Deferred)

- GitHub Actions for release automation (triggered on publish or manual dispatch).
- Automated validation of run folders (schema checks, linting).
- Additional review dashboards (e.g., HTML summary from run data).

---

## Implementation Notes

- Plan to implement in a fresh chat to avoid context drift; reference this document at the outset.
- Capture decisions and adjustments in this file as the work progresses (e.g., if naming conventions change).
- After Phase 5, cut release **v1.0** using the new publish process.
