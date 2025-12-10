# Sprint 6B: QA & Polish

**Status: ✅ COMPLETED**
**Started: December 2024**
**Completed: December 10, 2024**
**Branch: sprint-6b-qa**

## Overview

QA sprint to address issues discovered after Sprint 6A, focusing on UI polish, release notes formatting, and fixing incorrect URLs/attribution.

---

## Issues

### Issue 1: Edit UI - Directory Status Position ✅
**Priority: Medium**
**Location: nycgo-admin-ui**
**Status: FIXED**

The NYC.gov Agency Directory status in the edit modal appears above the principal officer name fields. It should be moved to appear above the "Schedule For Later" button, consistent with the Add New Organization modal.

**Fix:** Moved directory status section from line 198 to line 294 in `index.html`, now positioned above the schedule-group.

**Files modified:**
- `index.html` - Edit modal HTML structure

---

### Issue 2: Incorrect GitHub Organization Name in URLs ✅
**Priority: High**
**Location: nycgo-admin-ui**
**Status: FIXED**

The "View full rules" links use incorrect GitHub organization `nyc-cto` instead of `MODA-NYC`.

**Fix:** Changed all 3 occurrences from `nyc-cto` to `MODA-NYC`.

**Files modified:**
- `index.html` (line 455)
- `js/app.js` (lines 1241, 1284)

---

### Issue 3: Release Notes Formatting ✅
**Priority: Medium**
**Location: nyc-governance-organizations**
**Status: FIXED**

Improved release notes structure and clarity:

1. Renamed "Changes" section to "Release Summary"
2. Removed "Bundle Contents" header (was redundant with "Attached Assets")
3. Improved "Attached Assets" descriptions:
   - Note about GitHub auto-generated source archives
   - Clear descriptions for pipeline outputs vs data files

**Files modified:**
- `src/nycgo_pipeline/publish.py` - `generate_release_notes()` function

---

### Issue 4: Release Attribution Shows "Claude" ✅
**Priority: High**
**Location: nyc-governance-organizations**
**Status: FIXED**

The v1.6.0 release shows "Published by: Claude" instead of the user's GitHub handle.

**Root Cause:** The `--changed-by` parameter was required, and Claude Code set it to "Claude".

**Fix:** Changed `--changed-by` from required to defaulting to `$USER` environment variable.

**Files modified:**
- `scripts/pipeline/run_pipeline.py` - Default value for `--changed-by` now uses `os.environ.get("USER", "unknown")`

---

### Issue 5: State Government Agency Rule Contradiction ✅
**Priority: Low**
**Location: nyc-governance-organizations**
**Status: FIXED**

The `no_state_nygov_url` gatekeeper rule and `state_government_agency` type-specific rule were logically contradictory - State Government Agencies could be blocked by the .ny.gov URL gatekeeper while simultaneously being included by the type-specific rule.

**Root Cause:** The `state_government_agency` rule checked `organization_type == "State Government Agency"` instead of using an explicit exemption list like other organization types.

**Fix:** Created `STATE_GOVERNMENT_EXEMPTIONS` list with the 6 NYC-affiliated state agencies and modified the rule to check the exemption list. This follows the same pattern as `NONPROFIT_EXEMPTIONS` and `ADVISORY_EXEMPTIONS`.

**State Government Exemptions:**
- Bronx County Public Administrator
- City University of New York
- Kings County Public Administrator
- New York County Public Administrator
- Public Administrator of Queens County
- Richmond County Public Administrator

**Impact:** No records affected (all 6 State Government Agencies remain eligible)

**Files modified:**
- `src/nycgo_pipeline/directory_rules.py` - Added `STATE_GOVERNMENT_EXEMPTIONS` list, modified rule
- `scripts/generate_directory_docs.py` - Added tracking for new exemption list
- `docs/DIRECTORY_LOGIC.md` - Auto-regenerated
- `data/directory_logic_changelog.csv` - First changelog entry created
- `data/directory_rules_snapshot.json` - Updated snapshot

---

## Implementation Plan

### Phase 1: Fix Critical URL Issues
1. Fix GitHub org name in admin-ui (nyc-cto → MODA-NYC)
2. Search both repos for any other incorrect org references

### Phase 2: Edit UI Directory Status Position
1. Review current HTML structure in edit modal
2. Move directory status section below principal officer fields
3. Position above "Schedule For Later" button
4. Test on localhost

### Phase 3: Release Notes Improvements
1. Rename "Changes" → "Release Summary"
2. Improve "Attached Assets" descriptions
3. Review/remove "Bundle Contents" section if redundant
4. Test by running publish script locally

### Phase 4: Attribution Fix
1. Update default `--changed-by` to use `$USER` env var
2. Update workflow to pass `${{ github.actor }}`
3. Update documentation

---

## Acceptance Criteria

- [x] All "View full rules" links point to MODA-NYC organization
- [x] No other nyc-cto references in codebase
- [x] Directory status in edit modal positioned consistently with Add New modal
- [x] Release notes use clearer section names and descriptions
- [x] Future releases show correct GitHub username attribution
- [x] State Government Agency rule uses explicit exemption list
- [x] Directory logic changelog tracking functional
- [ ] Changes tested locally before merging

---

## Testing

1. Open Admin UI at localhost:8000
2. Click on a record to edit - verify directory status position
3. Verify "View full rules" link works correctly
4. Run pipeline with `--changed-by` test value
5. Verify run_summary.json has correct attribution

---

## Notes

- Sprint 6A completion released as v1.6.0 with snake_case columns
- This sprint focuses on polish items that don't affect data integrity
- All changes should be backward compatible
