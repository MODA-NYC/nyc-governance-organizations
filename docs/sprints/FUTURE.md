# FUTURE: Phase II Data Release

**Status: 🔮 DEFERRED**
**Originally: Sprint 4**

This was originally planned as Sprint 4 but has been deferred. When ready, this work will execute the Phase II data release.

## Overview

This work executes the Phase II data release by running the prepared edits file through the validated pipeline. This is the culmination of the infrastructure work from Sprints 1-3.

**Inputs**:
- Validated pipeline and review interface (Sprint 1-2)
- Standardized formatting (Sprint 3)
- `NYCGO_phase2_edits_to_make_20251118.csv` (233 edit rows)

**Outputs**:
- v1.2.0 release with 46-column schema
- 9 new organizations added
- ~90 MOA crosswalk mappings
- Phase II governance fields populated

---

## Phase II Scope

### Schema Changes (v1.1.x → v1.2.0)

**New columns (8 additions)**:
| Column | Description |
|--------|-------------|
| Name - MOA | Mayor's Office of Appointments crosswalk |
| AuthorizingAuthority | Legal authority citation (e.g., "NYC Charter § 1524") |
| AuthorizingAuthorityType | Type: NYC Charter, Local Law, Executive Order, etc. |
| AuthorizingURL | URL to authorizing document |
| AppointmentsSummary | Summary of appointment process |
| GovernanceStructure | Description of governance structure |
| ParentOrganizationRecordID | RecordID of parent organization |
| ParentOrganizationName | Name of parent organization |

### New Organizations (9 additions)

| Name | Type | Status |
|------|------|--------|
| Technology Development Corporation | Public Benefit or Development Organization | Dissolved |
| Community Investment Advisory Board | Advisory or Regulatory Organization | Inactive |
| Civil Service Commission - Screening Committee | Advisory or Regulatory Organization | Verification Pending |
| MTA Capital Program Review Board | Advisory or Regulatory Organization | Verification Pending |
| World Trade Center Captive Insurance Company | Public Benefit or Development Organization | Verification Pending |
| Quadrennial Advisory Commission for the Review of Compensation Levels of Elected Officials | Advisory or Regulatory Organization | Verification Pending |
| Veterans' Advisory Board | Advisory or Regulatory Organization | Verification Pending |
| New York City Global Partners | Nonprofit Organization | Verification Pending |
| SWMP Converted Marine Transfer Station Community Advisory Group - Gansevoort (Manhattan) | Advisory or Regulatory Organization | Inactive |

### Data Enhancements

- ~90 "Name - MOA" crosswalk mappings added
- Governance fields populated for select organizations (Banking Commission, Sustainability Advisory Board, etc.)
- Parent organization relationships established

---

## Pre-Sprint Checklist

Before starting Sprint 4, verify:

- [ ] Sprint 1 complete: Admin UI infrastructure working
- [ ] Sprint 2 complete: Pipeline validated with test edits
- [ ] Sprint 3 complete: Formatting standards implemented
- [ ] `NYCGO_phase2_edits_to_make_20251118.csv` preserved and accessible
- [ ] Current published version is v1.1.2 (or latest from Sprint 2)

---

## Phase 1: Review Edits File

### Prepare Edits File

1. Locate the edits file:
   ```
   nyc-governance-organizations/data/input/NYCGO_phase2_edits_to_make_20251118.csv
   ```

2. Verify file integrity:
   - [ ] 233 rows (excluding header)
   - [ ] All required columns present
   - [ ] No encoding issues

### Upload to Review Interface

1. Open review interface (review-edits.html)
2. Upload `NYCGO_phase2_edits_to_make_20251118.csv`
3. Review validation results

### Expected Validation Results

The review interface should flag:
- [ ] New record creation (records with `NEW` as record_id)
- [ ] New field names not in v1.1.x schema
- [ ] Any formatting issues

### Review Strategy

Given the large number of edits (233 rows), organize review by category:

#### Category 1: Name - MOA Crosswalk Mappings (~90 edits)
- Simple field additions
- Low risk, high volume
- Review sample, bulk approve if pattern consistent

#### Category 2: New Organizations (9 orgs × ~10 fields = ~90 edits)
- Higher scrutiny needed
- Verify each organization's:
  - Name and name_alphabetized
  - Operational status
  - Organization type
  - Authorizing authority and URL
  - Parent organization (if applicable)

#### Category 3: Governance Field Updates (~50 edits)
- Updates to existing records
- Verify authorizing authority citations
- Check URL validity

### Review Checklist

For each edit category:
- [ ] Sample edits reviewed for accuracy
- [ ] Field values match evidence URLs
- [ ] No obvious errors or typos
- [ ] Consistent with data standards (Sprint 3)

---

## Phase 2: Process Approved Edits

### Batch Processing

If review interface supports batching:
1. Approve Category 1 (MOA mappings) as batch
2. Review and approve Category 2 (new orgs) individually
3. Review and approve Category 3 (governance updates) individually

### Commit to Pending Edits

1. Generate approved edits CSV
2. Commit to `nycgo-admin-ui/pending-edits/`
3. Verify process-edit.yml workflow triggers

### Monitor Pipeline

- [ ] Workflow starts automatically
- [ ] Pipeline processes without errors
- [ ] Audit artifacts created in `audit/runs/<run_id>/`

### Review Pipeline Output

Before publishing:
- [ ] Record count: 434 + 9 = 443 records
- [ ] Column count: 38 + 8 = 46 columns
- [ ] New organizations present and correctly formatted
- [ ] MOA mappings populated
- [ ] Governance fields populated where expected
- [ ] No data corruption in existing records

---

## Phase 3: Validation

### Schema Validation

```bash
# Check column count
head -1 data/audit/runs/<run_id>/outputs/golden_pre-release.csv | tr ',' '\n' | wc -l
# Expected: 46

# Check record count
wc -l data/audit/runs/<run_id>/outputs/golden_pre-release.csv
# Expected: 444 (443 records + 1 header)
```

### New Organization Validation

For each new organization, verify:

| Organization | RecordID Generated | All Fields Populated | Status |
|--------------|-------------------|---------------------|--------|
| Technology Development Corporation | [ ] | [ ] | [ ] |
| Community Investment Advisory Board | [ ] | [ ] | [ ] |
| Civil Service Commission - Screening Committee | [ ] | [ ] | [ ] |
| MTA Capital Program Review Board | [ ] | [ ] | [ ] |
| World Trade Center Captive Insurance Company | [ ] | [ ] | [ ] |
| Quadrennial Advisory Commission... | [ ] | [ ] | [ ] |
| Veterans' Advisory Board | [ ] | [ ] | [ ] |
| New York City Global Partners | [ ] | [ ] | [ ] |
| SWMP CAG - Gansevoort | [ ] | [ ] | [ ] |

### MOA Crosswalk Validation

Spot-check 10 random MOA mappings:
- [ ] RecordID correct
- [ ] Name - MOA value matches MOA appointments page
- [ ] No typos

### Governance Field Validation

For organizations with governance updates:
- [ ] AuthorizingAuthority format consistent
- [ ] AuthorizingAuthorityType uses controlled vocabulary
- [ ] AuthorizingURL is valid and accessible
- [ ] Parent relationships correctly established

### Data Quality Checks (Sprint 3 standards)

- [ ] Boolean fields: TRUE/FALSE format
- [ ] BudgetCode: 3-digit zero-padded
- [ ] FoundingYear: integer format
- [ ] No .0 suffixes

---

## Phase 4: Publish v1.2.0

### Pre-Publish Checklist

- [ ] All validation checks pass
- [ ] Changelog entry prepared
- [ ] Release notes drafted

### Publish Steps

1. Trigger publish-release.yml with version `v1.2.0`
2. Monitor workflow execution
3. Verify release artifacts created

### Release Artifacts

Verify these files exist and are correct:
- [ ] `data/published/latest/NYCGO_golden_dataset_v1.2.0.csv`
- [ ] `data/published/latest/NYCGO_golden_dataset_latest.csv` (updated)
- [ ] `data/published/latest/NYCGovernanceOrganizations_v1.2.0.csv`
- [ ] `data/published/latest/NYCGovernanceOrganizations_latest.csv` (updated)
- [ ] GitHub release created with tag `v1.2.0`

### Post-Publish Verification

- [ ] Admin UI loads v1.2.0 data
- [ ] New columns visible (if UI updated to show them)
- [ ] New organizations searchable
- [ ] MOA crosswalk data accessible

---

## Phase 5: Documentation & Communication

### Update Documentation

- [ ] README.md - Update to reflect v1.2.0
- [ ] CHANGELOG.md - Add v1.2.0 entry with full details
- [ ] Schema documentation - Document new fields
- [ ] Data dictionary - Update field definitions

### Release Notes Template

```markdown
## v1.2.0 - Phase II Release

### New Features
- Added 8 new governance-related fields
- Added Name - MOA crosswalk column

### New Data
- 9 new organizations added
- ~90 MOA crosswalk mappings populated
- Governance fields populated for select organizations

### Schema Changes
- Total columns: 38 → 46
- Total records: 434 → 443
- RecordID format: NYC_GOID_XXXXXX (unchanged)

### New Fields
| Field | Description |
|-------|-------------|
| Name - MOA | Mayor's Office of Appointments crosswalk |
| AuthorizingAuthority | Legal authority citation |
| AuthorizingAuthorityType | Type of authorizing authority |
| AuthorizingURL | URL to authorizing document |
| AppointmentsSummary | Appointment process summary |
| GovernanceStructure | Governance structure description |
| ParentOrganizationRecordID | Parent organization RecordID |
| ParentOrganizationName | Parent organization name |

### New Organizations
1. Technology Development Corporation (Dissolved)
2. Community Investment Advisory Board (Inactive)
3. Civil Service Commission - Screening Committee
4. MTA Capital Program Review Board
5. World Trade Center Captive Insurance Company
6. Quadrennial Advisory Commission for the Review of Compensation Levels of Elected Officials
7. Veterans' Advisory Board
8. New York City Global Partners
9. SWMP Converted Marine Transfer Station Community Advisory Group - Gansevoort (Manhattan) (Inactive)
```

### Communication

- [ ] Update NYC Open Data portal (if applicable)
- [ ] Notify downstream data consumers
- [ ] Update any internal documentation

---

## Rollback Plan

If critical issues discovered post-publish:

### Immediate Rollback
```bash
# Revert to v1.1.2
cp data/published/archive/NYCGO_golden_dataset_v1.1.2.csv \
   data/published/latest/NYCGO_golden_dataset_latest.csv
git add data/published/latest/
git commit -m "Rollback to v1.1.2 due to [issue]"
git push
```

### Issue Documentation
Document any issues that required rollback for future reference.

---

## Definition of Done

- [ ] All 233 edits reviewed and approved
- [ ] Pipeline processed edits successfully
- [ ] Validation checks pass (schema, data quality, new orgs)
- [ ] v1.2.0 published to data/published/latest/
- [ ] GitHub release created
- [ ] Admin UI shows v1.2.0 data
- [ ] Documentation updated
- [ ] Release notes published
- [ ] Downstream consumers notified (if applicable)
