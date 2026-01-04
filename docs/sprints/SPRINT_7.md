# Sprint 7: Cleanup & Technical Debt

**Status: IN PROGRESS**
**Started: January 2026**

## Overview

This sprint consolidates remaining cleanup work and technical debt items that were deferred from earlier sprints. These are "nice to have" improvements that don't block production use.

**Note**: Phase II data release (46-field schema, 9 new organizations) is tracked separately in [PHASE_II.md](PHASE_II.md).

---

## Items

### 0. Repository & Docs Cleanup ✅ COMPLETE

Consolidate and organize documentation that has accumulated over multiple sprints.

**Problem**: The `docs/` folder had redundant and potentially stale files:
- 4 different directory logic docs (`ARCHITECTURE_DIRECTORY_LOGIC.md`, `DIRECTORY_LOGIC.md`, `DIRECTORY_FIELD_CHANGELOG.md`, `LISTED_IN_NYC_GOV_AGENCY_DIRECTORY_LOGIC.md`)
- 4 pipeline diagram formats (`.html`, `.bpmn`, `.mermaid.md`, `-standalone.html`)
- Phase II docs that are deferred indefinitely
- Unclear what's current vs. historical

**Resolution**: Audited all files, deleted redundant docs, archived historical docs, consolidated diagram formats to 3 (each serves distinct purpose: Mermaid for GitHub, BPMN for tool interop, standalone HTML for interactive viewing).

**Completed (January 2026)**:
- [x] Audit all files in `docs/` - identified current, redundant, and stale
- [x] Deleted redundant `LISTED_IN_NYC_GOV_AGENCY_DIRECTORY_LOGIC.md` (admin UI uses auto-generated `DIRECTORY_LOGIC.md`)
- [x] Reorganized `data/input/` folder structure:
  - `pending/` - active edits waiting to be processed
  - `processed/` - archive organized by month
  - `research/` - reference materials
  - Created `README.md` explaining workflow
- [x] Moved `docs/drafts/mamdani_transition_draft.csv` to `data/input/pending/mamdani_transition.csv`
- [x] Updated `CLAUDE.md` with new folder structure and current version (v1.7.x)
- [x] Updated `README.md` pipeline examples to use new `pending/` paths

**Remaining Tasks**:
- [x] Archive Phase I docs (`PHASE_I_SCHEMA.md`, `PHASE_I_PIPELINE.md`, `PHASE_I_SCHEMA_FIELDS.txt`) to `docs/sprints/phase-i-archive/`
- [x] Archive Phase II docs (`PHASE_II_SCHEMA.md`, `PHASE_II_PROGRESS.md`, `SCHEMA_VERSION_COMPARISON.md`) to `docs/sprints/phase-ii-archive/`
- [x] Update `sprints/PHASE_II.md` to reflect "resuming after Sprint 7" status (consolidated with full field definitions, completed work status, 42-column schema target)
- [x] Review pipeline diagram formats - evaluated all formats, kept 3 (Mermaid, BPMN XML, standalone HTML), deleted redundant CDN-dependent HTML (`nycgo-edit-publish-pipeline.html`)

**Docs Audit Summary**:
| Category | Files | Status |
|----------|-------|--------|
| Current/Active | `DIRECTORY_LOGIC.md` (auto-gen), `ARCHITECTURE_DIRECTORY_LOGIC.md`, `BACKLOG.md`, `APPOINTMENTS_MONITOR.md`, `GITHUB_RELEASE_GUIDE.md`, `CHANGELOG_SPEC.md`, `run_artifacts.md`, `DIRECTORY_FIELD_CHANGELOG.md` | Keep |
| Archived (Phase II) | `PHASE_II_SCHEMA.md`, `PHASE_II_PROGRESS.md`, `SCHEMA_VERSION_COMPARISON.md` | Done (moved to `sprints/phase-ii-archive/`) |
| Archived (Phase I) | `PHASE_I_SCHEMA.md`, `PHASE_I_PIPELINE.md`, `PHASE_I_SCHEMA_FIELDS.txt` | Done (moved to `sprints/phase-i-archive/`) |
| Deleted | `LISTED_IN_NYC_GOV_AGENCY_DIRECTORY_LOGIC.md`, `nycgo-edit-publish-pipeline.html` (redundant CDN version) | Done |

---

### 1. Schema Documentation & Field Alignment ✅ COMPLETE

**Sprint 7.1 - Completed January 2026**

This sprint addressed schema documentation and aligned field names between golden and published datasets.

#### Field Rename (Golden Dataset)

Renamed fields to match published export naming:
- `principal_officer_given_name` → `principal_officer_first_name`
- `principal_officer_family_name` → `principal_officer_last_name`

**Files updated**:
- `data/published/latest/NYCGO_golden_dataset_latest.csv` - Column headers
- `schemas/nycgo_golden_dataset.tableschema.json` - Schema definition
- `scripts/process/export_dataset.py` - Removed mapping code, updated GOLDEN_COLUMN_ORDER
- `src/nycgo_pipeline/qa_edits.py` - Reversed synonym map for backward compatibility
- `scripts/maint/standardize_field_names.py` - Updated COLUMN_MAP
- `tests/fixtures/appointments/golden_sample.csv` - Test fixture headers
- `tests/test_changelog_schema.py` - Added legacy field names to ALLOWED_FIELDS

**Why this is safe**: The published export already used `first_name`/`last_name`. This change removes the mapping step and makes the golden dataset consistent with the published output.

#### Schema Documentation Created

Created `docs/SCHEMA.md` containing:
- [x] All 38 golden dataset fields with descriptions
- [x] Field mapping table (which 21 fields are golden-only)
- [x] Reference to Excel data dictionary for published field details
- [x] Historical note about field rename (v1.8.0)
- [x] Explanation of `in_org_chart` vs `jan_2025_org_chart`

**Baseline Tag**: `v1.7.21-pre-sprint7.1` (created before changes)

---

### 2. ~~Externalize Exception Lists to YAML~~ ✅ RECONSIDERED

**Status**: Intentionally declined (January 2026)

After analysis, we decided to **keep exception lists in Python** rather than externalize to YAML.

**Rationale**:
- The current `directory_rules.py` architecture is a **Single Source of Truth** that drives evaluation, documentation generation, and changelog tracking
- Rules include Python lambdas that cannot be expressed in YAML; externalizing only the lists would split the source of truth
- Change detection and audit trail already exist via `generate_directory_docs.py`
- The lists total ~18 entries and rarely change—YAML overhead isn't justified
- If justifications are needed, Python comments serve the same purpose

**Documentation**: See `docs/ARCHITECTURE_DIRECTORY_LOGIC.md` → "Design Decisions" section for full explanation.

---

### 3. Schema Change Tracking Automation ✅ COMPLETE

**Sprint 7.3 - Completed January 2026**

Automate detection of schema changes between releases.

**Implementation**:
- Created `scripts/check_schema_changes.py` - compares current schema against previous release
- Added "Check for schema changes" step to `publish-release.yml` (non-blocking)
- If schema changes detected, they're automatically appended to release notes
- Updated `schemas/SCHEMA_CHANGELOG.md` with documentation

**What Gets Detected**:
- Field additions/removals
- Type changes
- Constraint changes (required, enum, pattern)
- Format changes
- Schema version number changes

**Tasks**:
- [x] Create `scripts/check_schema_changes.py`
- [x] Add warning step to publish-release.yml
- [x] Document process for updating schema changelog

---

### 4. Golden/Published Directory Field Alignment ✅ COMPLETE

**Sprint 7.4 - Completed January 2026**

Ensure the directory eligibility field is calculated consistently.

**Problem**: Golden dataset `listed_in_nyc_gov_agency_directory` could diverge from the published export because:
- Golden preserved stale/empty values from input CSV
- Published export recalculated fresh using current rules
- This resulted in 86+ mismatches between the datasets

**Solution**: "Calculate once, use everywhere"

**Implementation**:
- Added `calculate_directory_eligibility_all()` function to `scripts/process/export_dataset.py`
- This function uses `evaluate_eligibility()` from `directory_rules.py` (single source of truth)
- Called BEFORE saving golden dataset, so all records get freshly calculated values
- Published export then uses these same values (consistency guaranteed)

**Files updated**:
- `scripts/process/export_dataset.py` - Added new function and calls in `main()` and `main_with_dataframe()`

**Tasks**:
- [x] Refactor export to calculate directory eligibility once
- [x] Apply same value to both golden and published datasets
- [x] Records not in published export get calculated `True`/`False` in golden

---

### 5. UV Package Manager Migration ✅ COMPLETE

**Sprint 7.5 - Completed January 2026**

Modernized package management from `venv + pip` to UV (from Astral, makers of ruff).

**Rationale**:
- Faster dependency installation
- Better lockfile support
- Modern tooling (from Astral, makers of ruff)

**Implementation**:
- Created `uv.lock` lockfile (42 packages resolved)
- Updated `Makefile` to use `uv sync` and `uv run` commands
- Updated `publish-release.yml` workflow to use UV via `astral-sh/setup-uv@v5` action
- Updated `README.md` prerequisites section with UV install instructions

**Files updated**:
- `Makefile` - Simplified to use UV commands
- `.github/workflows/publish-release.yml` - Uses UV for dependency installation
- `README.md` - Updated prerequisites & install section
- `uv.lock` - New lockfile (committed)

**Tasks**:
- [x] Install UV (already installed: v0.9.7)
- [x] Update Makefile
- [x] Create `uv.lock`
- [x] Update documentation
- [x] Update GitHub workflows
- [x] Test all functionality

---

### 6. ~~Rename DEMO_MODE to TEST_MODE~~ ✅ DONE

Fixed December 2024. `DEMO_MODE` deleted, `TEST_MODE` created.

---

### 6.5 Simplify Workflow Mode Variables ✅ COMPLETE

**Sprint 7.6 - Completed January 2026**

Consolidated confusing workflow mode variables into a single variable.

**Problem**: Two separate boolean variables (`TEST_MODE` and `PRODUCTION_MODE`) were error-prone:
- Had to flip both together correctly
- Three implicit modes (neither set, test, production) were confusing
- "Neither set" mode committed to admin-ui-test branch which wasn't needed

**Solution**: Single `WORKFLOW_MODE` variable with two values:
- `test` (default) - commits to main, creates draft release
- `production` - commits to main, creates real release

**Files updated**:
- `nycgo-admin-ui/.github/workflows/process-edit.yml` - Uses new variable
- `CLAUDE.md` - Updated Workflow Modes documentation

**Tasks**:
- [x] Update process-edit.yml to use single WORKFLOW_MODE variable
- [x] Remove admin-ui-test branch mode (not needed)
- [x] Update CLAUDE.md documentation
- [x] Update tech debt log

**Note**: After deploying, delete old repo variables (TEST_MODE, PRODUCTION_MODE) and create new WORKFLOW_MODE variable via GitHub UI or CLI:
```bash
# In nycgo-admin-ui repo
gh variable delete TEST_MODE
gh variable delete PRODUCTION_MODE
gh variable set WORKFLOW_MODE --body "test"
```

---

### 7. Test Workflow Rate Limiting ✅ COMPLETE

**Sprint 7.7 - Completed January 2026**

Verified Sprint 4's rate limiting feature works correctly.

**Test procedure**:
1. Set `WORKFLOW_MODE=test`
2. Submit an edit via Admin UI
3. While workflow is running, try to submit another edit
4. Should see: "Edit currently in progress. Check back in a couple minutes."

**Test Results (January 2026)**:

Rate limiting works at two levels:

1. **Workflow-level queueing** ✅ Working
   - Tested by pushing two edits ~9 seconds apart
   - First workflow: `in_progress`
   - Second workflow: `pending` (queued, not running simultaneously)
   - Both processed successfully, creating separate draft releases
   - `concurrency` setting in process-edit.yml correctly queues workflows

2. **UI-level blocking** ✅ Implemented
   - `isWorkflowRunning()` in app.js checks GitHub API before allowing submission
   - Shows overlay: "A pipeline is currently processing changes..."
   - Polls every 5 seconds until workflow completes

**Edge case discovered**: When two commits push in quick succession, the second push can cause a git conflict when the first workflow tries to archive its processed edit. This is a git timing issue, not a rate limiting bug.

**Tasks**:
- [x] Test the above procedure
- [x] Document results
- [x] Fix if not working (no fix needed - working as designed)

---

### 8. Enhanced Release Notes with Export Changes

Auto-generate release notes that summarize changes to the published dataset.

**Current state**: Release notes only show run ID and basic metadata
**Target state**: Release notes include summary of records added/removed and directory eligibility changes

**Desired output in release notes**:
```markdown
## Published Dataset Changes

**Records added to Open Data (3):**
- NYC_GOID_100031 - Mayor's Office of Rodent Mitigation
- NYC_GOID_000303 - Municipal Division of Transitional Services
- ...

**Records removed from Open Data (1):**
- NYC_GOID_000474 - Director of Rodent Mitigation

**Directory Eligibility Changes (1):**
- NYC_GOID_000474: TRUE → FALSE
```

**Implementation approach**:
1. Enhance pipeline to compare previous vs new published export
2. Store changes in `run_summary.json`:
   ```json
   {
     "published_export_changes": {
       "added": [{"id": "NYC_GOID_100031", "name": "..."}],
       "removed": [{"id": "NYC_GOID_000474", "name": "..."}],
       "directory_status_changes": [
         {"id": "NYC_GOID_000474", "name": "...", "from": "TRUE", "to": "FALSE"}
       ]
     }
   }
   ```
3. Update publish-release workflow to format this into release notes

**Tasks**:
- [ ] Add comparison logic to pipeline (compare golden snapshots)
- [ ] Update `run_summary.json` schema with export changes
- [ ] Update release notes generation in `publish-release.yml`
- [ ] Limit displayed orgs to first 5 with "and N more..." if needed

---

### 9. Branch Audit & Cleanup

Audit and clean up unnecessary branches in both repositories.

**Repositories**:
- `nyc-governance-organizations` (pipeline)
- `nycgo-admin-ui` (admin interface)

**Known branches to review**:
- `demo` - Deprecated after Option A implementation (test mode now commits to main)
- `admin-ui-test` - Used for test-without-release mode
- `dev` - Verify if still needed
- `test` - Verify if still needed

**Test commit cleanup**:
Test mode commits are tagged with `test-run-*` for easy identification and cleanup.

```bash
# List test tags
git tag -l "test-run-*"

# Delete test tags (after deleting draft releases)
git tag -l "test-run-*" | xargs -I {} git tag -d {}
git push origin --delete $(git tag -l "test-run-*")
```

**Tasks**:
- [ ] List all branches in both repos
- [ ] Identify which branches are still needed
- [ ] Delete `demo` branch (no longer used)
- [ ] Document which branches should exist and why

---

## Technical Debt Log

Items identified but not yet prioritized:

| Item | Location | Notes |
|------|----------|-------|
| Duplicate exception lists | `export_dataset.py` | Lines 563-566 duplicated at 760-763 |
| No integration tests | export logic | Only unit tests exist |
| Complex directory logic | multiple functions | Could be simplified |
| Failing test: MTA eligibility | `test_directory_rules.py` | State Government Agency rule for MTA returns False, expected True |
| ~~Failing test: changelog schema~~ | ~~`test_changelog_schema.py`~~ | ~~Fixed in Sprint 7.1 - added missing fields to ALLOWED_FIELDS~~ |
| Failing test: regression snapshot | `test_directory_rules.py` | MTA regression test expects True, gets False |
| ~~Confusing workflow mode variables~~ | ~~`nycgo-admin-ui` repo variables~~ | ~~Fixed Jan 2026 - consolidated to single WORKFLOW_MODE variable~~ |
| Auto-detect schema changes for version bump | `process-edit.yml` | Workflow should detect schema changes and auto-bump minor version instead of patch |

---

## Definition of Done

- [x] Schema documentation complete (Sprint 7.1 - Jan 2026)
- [x] ~~Exception lists in YAML config~~ Reconsidered - keeping Python (Sprint 7.2 - Jan 2026)
- [x] Schema change detection automated (Sprint 7.3 - Jan 2026)
- [x] Directory field alignment implemented (Sprint 7.4 - Jan 2026)
- [x] UV migration complete (Sprint 7.5 - Jan 2026)
- [x] ~~DEMO_MODE renamed to TEST_MODE~~ (Done Dec 2024)
- [x] Workflow mode variables simplified (Sprint 7.6 - Jan 2026)
- [x] Rate limiting tested (Sprint 7.7 - Jan 2026)
- [ ] Enhanced release notes with export changes
- [ ] Failing tests fixed (MTA eligibility) - changelog schema fixed in 7.1
- [ ] Branch audit complete, unnecessary branches removed

---

## Priority

These items are **not blocking** production use. Prioritize based on:
1. Pain points encountered during normal operations
2. Preparation needed for Phase II
3. Available time between other work
