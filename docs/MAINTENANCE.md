# Maintenance Runbook

How to keep the edit-to-release pipeline running. For how the pipeline works, see the [README](../README.md) and the [pipeline diagram](nycgo-edit-publish-pipeline.mermaid.md).

## The moving parts

| Part | Where | What it does |
|------|-------|--------------|
| Admin UI | `MODA-NYC/nycgo-admin-ui` (GitHub Pages) | Editors submit edits; each edit is a CSV committed to `pending-edits/` |
| `process-edit.yml` | Admin UI repo | Runs on each commit to `pending-edits/` and hourly. Runs the pipeline, commits the run folder to this repo, starts `publish-release.yml`, archives the edit to `processed-edits/` |
| `publish-release.yml` | This repo | Promotes the run, validates, commits `data/published/latest/` and `data/changelog.csv`, creates the GitHub Release |
| `PIPELINE_REPO_TOKEN` | Admin UI repo → Settings → Secrets → Actions | Lets `process-edit.yml` push to this repo and start `publish-release.yml` |
| `WORKFLOW_MODE` | Admin UI repo → Settings → Variables → Actions | `production` creates real releases. `test` (or unset) creates draft releases tagged `-test` and does not append to `data/changelog.csv` |
| Open Data sync | Outside these repositories | A separate automated process monitors this repository's releases and updates NYC Open Data |

Edits are processed one at a time. A second edit submitted while one is running waits in a queue.

## Routine tasks

### Add or remove an editor
Give or remove **write** access on the Admin UI repository. Editors need no access to this repository.

### Rotate `PIPELINE_REPO_TOKEN`
The token is a fine-grained personal access token scoped to this repository with `contents: write` and `actions: write`. It expires.

1. Create a new fine-grained token with the same scope.
2. Replace the `PIPELINE_REPO_TOKEN` secret in the Admin UI repository.
3. Submit a small edit, or run **Process Edit** manually, and confirm a release appears.

Tracking issue for replacing the token with a credential that does not expire: [nycgo-admin-ui#1](https://github.com/MODA-NYC/nycgo-admin-ui/issues/1).

### Schedule an edit for later
Use "Schedule for later" in the Admin UI. The file lands in `scheduled-edits/` and is moved to `pending-edits/` by the hourly run once its time (UTC) has passed.

### Change Admin UI JavaScript
Update the `?v=YYYYMMDD` cache-busting values in both `index.html` and `review-edits.html`, or browsers keep serving the old code.

## When something fails

Nothing notifies editors or maintainers when a run fails. Check the Actions tab of each repository.

### An edit was submitted but no release appeared
1. Open [Admin UI Actions](https://github.com/MODA-NYC/nycgo-admin-ui/actions) and find the failed **Process Edit** run.
2. If the **Checkout pipeline repo** step failed with `could not read Username for 'https://github.com'`, the token has expired. Rotate it (above).
3. For other failures, read the step log. If the edit file is malformed, fix or delete it in `pending-edits/`.
4. The edit stays in `pending-edits/` until a run succeeds. The hourly run retries it automatically, or run **Process Edit** manually from the Actions tab.

### Process Edit succeeded but Publish Release failed
The edit is already archived, and the run folder is already committed to this repository under `data/audit/runs/<run_id>/`.

1. Open [pipeline Actions](https://github.com/MODA-NYC/nyc-governance-organizations/actions/workflows/publish-release.yml) and read the failed step. A validation failure means the output broke a schema rule; the validation report names the check.
2. If the data is wrong, submit a correcting edit through the Admin UI. New edits run against `data/published/latest/`. If the failed run's changes are not in that file, include them again.
3. If the failure was transient, run **Publish Release** manually with the same `run_id` and `version_bump: patch`.

### A bad value was published
Submit a correcting edit through the Admin UI. Every change is recorded in `data/changelog.csv`, so the previous value can be read from there. Do not edit files in `data/published/latest/` by hand.

## Known gaps

- **Token expiry** stops all edits until rotated. See [nycgo-admin-ui#1](https://github.com/MODA-NYC/nycgo-admin-ui/issues/1).
- **No failure alerts.** A failed run is visible only in the Actions tab.
- **Tests do not run automatically.** Run `make test` before merging code changes.
- **Version numbers.** `process-edit.yml` is written to use a minor version for new organizations and status changes, but its checks look for older field and action names, so every Admin UI edit is released as a patch.
- **GitHub Actions versions** need upgrading. See [nycgo-admin-ui#2](https://github.com/MODA-NYC/nycgo-admin-ui/issues/2).

_Last reviewed: 2026-11-09_
