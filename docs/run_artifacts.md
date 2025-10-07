# Run Artifacts Baseline

Every pipeline execution must produce a predictable bundle of inputs, outputs, and review aids. This document codifies the baseline layout referenced in Phase 0 of the pipeline refactor.

## Run folder location & naming

- Root directory: `data/audit/runs/`
- Folder naming: `YYYYMMDD-HHMM_<descriptor>` (UTC recommended; include timezone indicator if non-UTC)
- Example: `20251006-1430Z_main-refresh`

## Directory structure

Each run directory must contain the following subdirectories:

```
<run_id>/
├── inputs/
├── outputs/
└── review/
```

### `inputs/`

Mandatory files:

- `golden_snapshot.csv` – immutable copy of the golden dataset used for this run
- `previous_published.csv` – the most recently published dataset before the run
- `edits_to_apply.csv` – QA or analyst change log that triggered the run (source-of-truth for edits)

Optional additions:

- Any supplemental lookup tables or reference data (name according to source)

### `outputs/`

All outputs remain in pre-release state until the publish CLI promotes them. Required files:

- `golden_pre-release.csv` – new golden dataset after applying rules and edits
- `published_pre-release.csv` – new public dataset image generated for release
- `run_changelog.csv` – per-run change log describing transformations performed
- `run_summary.json` – summary metadata (record counts, key field rollups, quality checks)

File naming should include `_pre-release` to signal unpublished status. When the run is published, the publish CLI will create `_final` copies in `data/published/`.

### `review/`

Stores QA aides generated during the run, such as:

- `source_comparison_report.csv` – diffs against upstream sources
- `summary_stats.csv` or `.json` – high-level metrics for reviewer sign-off
- Any additional artifacts that assist manual review (charts, notebooks, etc.)

### Example layout

```
data/audit/runs/20251006-1430Z_main-refresh/
├── inputs/
│   ├── golden_snapshot.csv
│   ├── previous_published.csv
│   └── edits_to_apply.csv
├── outputs/
│   ├── golden_pre-release.csv
│   ├── published_pre-release.csv
│   ├── run_changelog.csv
│   └── run_summary.json
└── review/
    ├── source_comparison_report.csv
    └── summary_stats.csv
```

## Metadata requirements

- `run_summary.json` must document:
  - `run_id`
  - timestamps: `started_at`, `finished_at`
  - `git_sha` (or `nogit` when unavailable)
  - `counts`: total records processed, and counts for key metrics (adds, updates, removals)
- `run_changelog.csv` should align with the minimal schema enforced by `tests/test_changelog_schema.py`

## Run manifest

Maintain a central manifest to link each dataset version to its originating run:

- File: `data/audit/run_manifest.csv`
- Columns: `run_id`, `created_at`, `golden_pre_release_path`, `published_pre_release_path`, `summary_path`, `notes`
- Update the manifest as part of the pipeline CLI so future publish steps can resolve the correct artifacts.

Keeping these conventions consistent enables automated publishing and long-term traceability of the NYC Governance Organizations dataset.
