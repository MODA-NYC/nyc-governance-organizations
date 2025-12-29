# Sprint 2: Pipeline Testing & Validation

**Status: ✅ COMPLETED**
**Completed: December 2024**

**Note**: v1.1.2 was released but with a minor issue (missing `_latest` artifacts in GitHub release). This is addressed in Sprint 5.

## Overview

This sprint validated the infrastructure built in Sprint 1 by running controlled test edits through the full pipeline.

**Inputs**: Working Admin UI with review interface, `data/published/latest/` as source of truth
**Outputs**: Validated pipeline, v1.1.2 release, documented issues/fixes

---

## Goals

1. **Create small test edits** - Identify 5-10 low-risk edits for v1.1.2
2. **End-to-end validation** - Run edits through the full pipeline (review UI → pending-edits → process-edit.yml → publish)
3. **Fix display issues** - Address any UI/UX problems discovered during testing
4. **Validate output** - Confirm pipeline produces correct, well-formatted output
5. **Document learnings** - Record any issues, fixes, or process improvements

---

## Phase 1: Identify Test Edits for v1.1.2

### Criteria for Good Test Edits
- Low risk (minor corrections, not structural changes)
- Verifiable (easy to confirm the change is correct)
- Cover different edit types (direct_set, append_to_list, etc.)
- Include at least one edit that touches common fields

### Candidate Edit Types

#### 1. Data Corrections
- Fix typos in descriptions or names
- Update outdated URLs
- Correct operational status for organizations with clear evidence

#### 2. Field Updates
- Add missing acronyms
- Update principal officer names (with evidence)
- Add missing crosswalk mappings (Name - NYC.gov Agency List, etc.)

#### 3. Edge Cases to Test
- Edit with special characters in value
- Edit with very long text value
- Edit to a list field (append/remove)

### Test Edit Template

Create file: `data/input/NYCGO_test_edits_v1.1.2.csv`

```csv
record_id,record_name,field_name,action,justification,evidence_url
```

### Tasks
- [ ] Review current v1.1.1 data for obvious corrections needed
- [ ] Identify 5-10 candidate edits
- [ ] Create test edit file
- [ ] Document expected outcomes for each edit

---

## Phase 2: End-to-End Pipeline Test

### Test Workflow

```
1. Upload test edits CSV to review interface
   ↓
2. Review and approve edits in UI
   ↓
3. Commit approved edits to pending-edits/
   ↓
4. process-edit.yml runs automatically
   ↓
5. Verify output in audit/runs/<run_id>/
   ↓
6. Trigger publish-release.yml
   ↓
7. Verify v1.1.2 in data/published/latest/
   ↓
8. Verify Admin UI loads v1.1.2
```

### Test Cases

#### TC-1: Single Edit Flow
- **Input**: One simple edit (e.g., fix a typo)
- **Expected**: Edit applies cleanly, changelog updated, output correct
- **Verify**: Field value changed, no other fields affected

#### TC-2: Multi-Edit Batch
- **Input**: 5+ edits in single file
- **Expected**: All edits apply, batch shows in changelog
- **Verify**: All changes correct, proper audit trail

#### TC-3: Validation Rejection
- **Input**: Edit with invalid field name
- **Expected**: Review UI rejects with clear error message
- **Verify**: Error displayed, edit not committed

#### TC-4: Edit to List Field
- **Input**: Append to `AlternateOrFormerNames`
- **Expected**: Value appended with semicolon separator
- **Verify**: Existing values preserved, new value added

#### TC-5: Special Characters
- **Input**: Edit containing quotes, commas, newlines
- **Expected**: Proper CSV escaping, value stored correctly
- **Verify**: Value displays correctly in output

### Acceptance Criteria
- [ ] All test cases pass
- [ ] No data corruption or unexpected changes
- [ ] Changelog correctly records all edits
- [ ] Audit trail complete and accurate

---

## Phase 3: Fix Display Issues

### Known/Suspected Issues to Investigate

#### Review Interface
- [ ] Field name mapping display (snake_case shown, PascalCase in dataset)
- [ ] Current value lookup working correctly
- [ ] Long text values display properly (truncation/scrolling)
- [ ] Evidence URL links work

#### Admin UI (Main)
- [ ] Data loads from correct source (`_latest.csv`)
- [ ] Version indicator shows correct version
- [ ] Edit form field names match schema

#### Pipeline Output
- [ ] Boolean values consistent (`TRUE` vs `True`)
- [ ] Numeric fields formatted correctly
- [ ] CSV encoding correct (UTF-8 with BOM if needed)

### Issue Tracking

Document issues in this format:

| ID | Component | Description | Severity | Status |
|----|-----------|-------------|----------|--------|
| D-1 | Review UI | Example issue | Medium | Open |

### Tasks
- [ ] Run through full workflow and note all display issues
- [ ] Prioritize by severity (blocking, high, medium, low)
- [ ] Fix blocking and high issues in this sprint
- [ ] Document medium/low issues for Sprint 3

---

## Phase 4: Validate Pipeline Output

### Output Validation Checklist

#### Golden Dataset Structure
- [ ] Correct number of columns (38 for v1.1.x schema)
- [ ] Column headers match expected names
- [ ] No empty rows or malformed records
- [ ] Record count matches expected (434 + any new records)

#### Data Integrity
- [ ] RecordID format consistent (`NYC_GOID_XXXXXX`)
- [ ] No duplicate RecordIDs
- [ ] Required fields populated
- [ ] List fields properly semicolon-separated

#### Changelog Validation
- [ ] All edits recorded with timestamps
- [ ] Edit descriptions accurate
- [ ] Run IDs link to audit artifacts

#### Audit Artifacts
- [ ] Input files preserved in `audit/runs/<run_id>/inputs/`
- [ ] Output files in `audit/runs/<run_id>/outputs/`
- [ ] Review files (if applicable) in `audit/runs/<run_id>/review/`

### Comparison Script

Create a simple validation script to compare pre/post datasets:

```python
# scripts/validate_edit_output.py
# Compare golden dataset before and after edits
# Verify only expected fields changed
# Check for unexpected side effects
```

---

## Phase 5: Release v1.1.2

### Pre-Release Checklist
- [ ] All test cases pass
- [ ] No blocking display issues
- [ ] Pipeline output validated
- [ ] Changelog updated

### Release Steps
1. Create PR with test edits
2. Merge to main branch
3. Run publish-release.yml workflow
4. Verify release artifacts
5. Confirm Admin UI shows v1.1.2

### Post-Release Verification
- [ ] GitHub release created with correct tag
- [ ] `data/published/latest/` contains v1.1.2 files
- [ ] `NYCGO_golden_dataset_latest.csv` updated
- [ ] Admin UI loads new data
- [ ] NYC Open Data portal update triggered (if applicable)

---

## Documentation

### Update These Documents
- [ ] README.md - Update version references
- [ ] CHANGELOG.md - Add v1.1.2 entry
- [ ] Any workflow documentation affected

### Create/Update
- [ ] Pipeline testing runbook (based on this sprint's learnings)
- [ ] Known issues list for Sprint 3

---

## Sprint Retrospective Items

After completing this sprint, document:

1. **What worked well**
   -

2. **What didn't work well**
   -

3. **Process improvements for future sprints**
   -

4. **Technical debt identified**
   -

5. **Blockers encountered**
   -

---

## Definition of Done

- [ ] Test edits file created and documented
- [ ] All 5 test cases executed successfully
- [ ] Display issues catalogued, blocking issues fixed
- [ ] Pipeline output validation complete
- [ ] v1.1.2 released and verified
- [ ] Documentation updated
- [ ] Retrospective completed
- [ ] Ready for Sprint 3
