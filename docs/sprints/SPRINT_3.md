# Sprint 3: v1.1.2 Release Fix & Production Pipeline Test

## Overview

This sprint fixes the incomplete v1.1.2 release and validates the production pipeline with a real edit to Office of Collective Bargaining.

**Context**:
- v1.1.2 release is missing `_latest` artifacts needed for Open Data portal automation
- Office of Collective Bargaining exists in golden dataset but not in published dataset (due to export filter)
- Need to switch from demo mode to production mode for pipeline testing

**Inputs**:
- Current v1.1.2 release (incomplete)
- Office of Collective Bargaining record (NYC_GOID_000354)

**Outputs**:
- Fixed v1.1.2 release with `_latest` artifacts
- Office of Collective Bargaining in published dataset
- Validated production pipeline workflow
- v1.1.3 release

---

## Issues Identified

### Issue 1: v1.1.2 Missing `_latest` Artifacts

The v1.1.2 GitHub release is missing:
- `NYCGO_golden_dataset_latest.csv`
- `NYCGovernanceOrganizations_latest.csv`

These are needed for the Open Data portal automation integration.

### Issue 2: Office of Collective Bargaining Not in Published Dataset

**Record**: NYC_GOID_000354

**Current state in golden dataset**:
- `OperationalStatus: Active`
- `InOrgChart: (empty)`
- `Name - Ops: (empty)`
- `NYC.gov Agency Directory: True` (incorrect - see below)

**Root cause**: The published dataset export filter requires:
```python
(in_org_chart | has_ops_name | is_export_exception) & active_only
```

Office of Collective Bargaining fails because:
- `InOrgChart` is empty (not True)
- `Name - Ops` is empty
- Not in the hardcoded exception list

### Issue 3: Golden/Published Divergence for NYC.gov Agency Directory

The golden dataset shows `NYC.gov Agency Directory = True` for Office of Collective Bargaining, but:
1. The record isn't even in the published dataset
2. Even if it were, it would get `False` because:
   - OrganizationType: Advisory or Regulatory Organization
   - Rule: `in_org_chart OR has_main_nyc_gov_url OR in_advisory_exemptions`
   - Fails all three (InOrgChart empty, URL is ocb-nyc.org not nyc.gov, not in advisory exemptions)

This is a symptom of the larger issue addressed in Sprint 6.

---

## Phase 1: Fix v1.1.2 Release

### 1.1 Verify Current Release State

```bash
gh release view v1.1.2 --repo MODA-NYC/nyc-governance-organizations
```

### 1.2 Add Missing Artifacts

Upload missing files to existing release:
```bash
gh release upload v1.1.2 \
  data/published/latest/NYCGO_golden_dataset_latest.csv \
  data/published/latest/NYCGovernanceOrganizations_latest.csv \
  --repo MODA-NYC/nyc-governance-organizations
```

If upload fails (file already exists), may need to use `--clobber` flag.

### 1.3 Verify Fix

- [ ] `_latest` files present in release
- [ ] Files are identical to versioned files (v1.1.2)
- [ ] Open Data portal automation can access files

---

## Phase 2: Add Office of Collective Bargaining to Exception List

### 2.1 Locate Exception List

File: `nyc-governance-organizations/scripts/process/export_dataset.py`

Current exception list (lines 563-566):
```python
published_export_exceptions = [
    "NYC_GOID_000476",  # MTA (Metropolitan Transportation Authority)
    "NYC_GOID_100030",  # Office of Digital Assets and Blockchain
]
```

### 2.2 Add Record

Add Office of Collective Bargaining:
```python
published_export_exceptions = [
    "NYC_GOID_000354",  # Office of Collective Bargaining
    "NYC_GOID_000476",  # MTA (Metropolitan Transportation Authority)
    "NYC_GOID_100030",  # Office of Digital Assets and Blockchain
]
```

Note: There's a duplicate list at line 760 in `main_with_dataframe()` that also needs updating.

### 2.3 Commit Change

- [ ] Both exception lists updated
- [ ] Commit with clear message explaining why
- [ ] Push to main branch

---

## Phase 3: Switch to Production Mode

### 3.1 Current Mode Status

Check nycgo-admin-ui repository variables:
- `DEMO_MODE` = true (currently)
- `PRODUCTION_MODE` = false (currently)

### 3.2 Update Mode

In GitHub repo settings for nycgo-admin-ui (Settings → Secrets and variables → Actions → Variables):
1. Set `DEMO_MODE` = false (or delete)
2. Set `PRODUCTION_MODE` = true

### 3.3 Verify Mode Understanding

| Mode | Target Branch | Release Type |
|------|---------------|--------------|
| Test (default) | admin-ui-test | None |
| Demo | demo | Draft release |
| Production | main | Real release |

- [ ] `DEMO_MODE` disabled
- [ ] `PRODUCTION_MODE` enabled
- [ ] Understand that workflow will target `main` branch and create real releases

---

## Phase 4: Test Production Pipeline

### 4.1 Prepare Edit

Create edit file for Office of Collective Bargaining:
```csv
record_id,record_name,field_name,action,new_value,justification,evidence_url
NYC_GOID_000354,Office of Collective Bargaining,InOrgChart,direct_set,False,Setting InOrgChart to False - org is not in the city org chart,
```

### 4.2 Submit Edit

Option A: Use Admin UI
1. Navigate to Office of Collective Bargaining
2. Edit InOrgChart field to False
3. Submit with justification

Option B: Manual commit
1. Create edit CSV file
2. Commit to `nycgo-admin-ui/pending-edits/`

### 4.3 Monitor Pipeline

- [ ] `process-edit.yml` workflow triggers
- [ ] Pipeline processes successfully
- [ ] Audit artifacts created in `nyc-governance-organizations/data/audit/runs/<run_id>/`
- [ ] Changes committed to `main` branch

### 4.4 Verify Results

After pipeline completes:
- [ ] Office of Collective Bargaining appears in published dataset
- [ ] `InOrgChart = False` set correctly
- [ ] `NYC.gov Agency Directory` calculated correctly (should be `False` based on current logic)
- [ ] New release (v1.1.3) created
- [ ] `_latest` files included in release

---

## Phase 5: Verify Golden/Published Alignment

### 5.1 Check Field Values

After the run, verify `NYC.gov Agency Directory` values:

**Published dataset**: Should be `False` (Advisory/Regulatory without in_org_chart, nyc.gov URL, or advisory exemption)

**Golden dataset**: Should also be `False` (matching published)

### 5.2 Document Discrepancies

If values don't match, this confirms the issue to be addressed in Sprint 6.

---

## Definition of Done

- [ ] v1.1.2 release has `_latest` artifacts uploaded
- [ ] Office of Collective Bargaining added to published export exception list (both locations in code)
- [ ] Production mode enabled in nycgo-admin-ui
- [ ] Test edit (InOrgChart=False) submitted and processed successfully
- [ ] Office of Collective Bargaining appears in published dataset
- [ ] v1.1.3 release created with all artifacts including `_latest` files
- [ ] Golden and published datasets have consistent `NYC.gov Agency Directory` values for this record

---

## Notes

- This sprint intentionally defers larger refactoring to Sprint 6
- The `NYC.gov Agency Directory` value for Office of Collective Bargaining will be `False` under current logic
- If we want it to be `True`, we'd need to either:
  - Add it to the `advisory_exemptions` list, OR
  - Set `InOrgChart = True`, OR
  - Wait for Sprint 6 to revise the directory logic
