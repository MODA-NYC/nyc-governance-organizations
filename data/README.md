# Data Directory

`data/` contains the inputs, outputs, and published artifacts for the NYC Governance Organizations pipeline.

- See [`docs/run_artifacts.md`](../docs/run_artifacts.md) for required per-run folder layout and artifact expectations.
- The append-only changelog (`data/changelog.csv`) remains protected; append via `scripts/maint/append_changelog.py`. Additional details live in [`docs/CHANGELOG_SPEC.md`](../docs/CHANGELOG_SPEC.md).
- `data/published/latest/` holds the most recent published datasets and is tracked in git. Earlier releases are archived by the publish CLI.
- The legacy `data/output/` location is deprecated; new runs emit artifacts exclusively under `data/audit/runs/<run_id>/`. If you need ad-hoc scratch space, prefer a gitignored subfolder under `_local_archives/`.
