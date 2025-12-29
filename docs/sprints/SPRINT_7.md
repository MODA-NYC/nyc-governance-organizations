# Sprint 7: Cleanup & Technical Debt

**Status: PLANNED**

## Overview

This sprint consolidates remaining cleanup work and technical debt items that were deferred from earlier sprints. These are "nice to have" improvements that don't block production use.

**Note**: Phase II data release (46-field schema, 9 new organizations) is tracked separately in [PHASE_II.md](PHASE_II.md).

---

## Items

### 1. Schema Documentation

Create comprehensive schema documentation.

**Files to create**:
- `docs/SCHEMA.md` - Field definitions for golden and published datasets
- `docs/SCHEMA_CHANGELOG.md` - Historical record of schema changes

**Tasks**:
- [ ] Document all 38 golden dataset fields
- [ ] Document all 16 published dataset fields
- [ ] Create field mapping table (golden → published)
- [ ] Document `InOrgChart` vs `Jan 2025 Org Chart` distinction

---

### 2. Externalize Exception Lists to YAML

Move hardcoded exception lists from Python to a YAML config file.

**Current state**: Lists are in `src/nycgo_pipeline/directory_rules.py` (Python)
**Target state**: Lists in `config/export_rules.yaml` (YAML)

**Benefits**:
- Non-developers can review/edit
- Changes don't require code deployment
- Includes justification and dates for each entry

**Tasks**:
- [ ] Create `config/export_rules.yaml` with all exception lists
- [ ] Update pipeline to read from YAML
- [ ] Add validation to ensure config is valid
- [ ] Migrate existing lists with justifications

---

### 3. Schema Change Tracking Automation

Automate detection of schema changes between releases.

**Tasks**:
- [ ] Create `scripts/check_schema_changes.py`
- [ ] Add warning step to publish-release.yml
- [ ] Document process for updating schema changelog

---

### 4. Golden/Published Directory Field Alignment

Ensure the directory eligibility field is calculated consistently.

**Problem**: Golden dataset `NYC.gov Agency Directory` can diverge from published `listed_in_nyc_gov_agency_directory` because they're calculated at different times.

**Solution**: Calculate once, use everywhere (Option B from original Sprint 6).

**Tasks**:
- [ ] Refactor export to calculate directory eligibility once
- [ ] Apply same value to both golden and published datasets
- [ ] Records not in published export get `False` in golden

---

### 5. UV Package Manager Migration

Modernize package management from `venv + pip` to UV.

**Rationale**:
- Faster dependency installation
- Better lockfile support
- Modern tooling (from Astral, makers of ruff)

**Tasks**:
- [ ] Install UV
- [ ] Update Makefile
- [ ] Create `uv.lock`
- [ ] Update documentation
- [ ] Test all functionality

---

### 6. ~~Rename DEMO_MODE to TEST_MODE~~ ✅ DONE

Fixed December 2024. `DEMO_MODE` deleted, `TEST_MODE` created.

---

### 7. Test Workflow Rate Limiting

Verify Sprint 4's rate limiting feature works correctly.

**Test procedure**:
1. Set `TEST_MODE=true`
2. Submit an edit via Admin UI
3. While workflow is running, try to submit another edit
4. Should see: "Edit currently in progress. Check back in a couple minutes."

**Tasks**:
- [ ] Test the above procedure
- [ ] Document results
- [ ] Fix if not working

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
| Failing test: changelog schema | `test_changelog_schema.py` | Fields `founding_year`, `jan_2025_org_chart` not in allowed list |
| Failing test: regression snapshot | `test_directory_rules.py` | MTA regression test expects True, gets False |

---

## Definition of Done

- [ ] Schema documentation complete
- [ ] Exception lists in YAML config
- [ ] Schema change detection automated
- [ ] Directory field alignment implemented
- [ ] UV migration complete (optional)
- [x] ~~DEMO_MODE renamed to TEST_MODE~~ (Done Dec 2024)
- [ ] Rate limiting tested
- [ ] Enhanced release notes with export changes
- [ ] Failing tests fixed (MTA eligibility, changelog schema)
- [ ] Branch audit complete, unnecessary branches removed

---

## Priority

These items are **not blocking** production use. Prioritize based on:
1. Pain points encountered during normal operations
2. Preparation needed for Phase II
3. Available time between other work
