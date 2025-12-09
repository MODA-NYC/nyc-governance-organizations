# Sprint 6: Schema Alignment & Directory Logic Refactoring

## Overview

This sprint addresses structural issues identified during Sprint 5 testing: the mismatch between golden and published dataset schemas, the confusing directory field logic, and the need for schema change tracking.

**Context**:
- Golden dataset has 38 fields, published has 16 - different schemas cause confusion
- `NYC.gov Agency Directory` field can diverge between golden and published datasets
- `InOrgChart` vs `Jan 2025 Org Chart` fields are confusing
- Exception lists are hardcoded in Python code, hard to maintain
- No tracking of schema changes between releases

**Inputs**:
- Validated pipeline from Sprint 5
- Understanding of current field logic issues

**Outputs**:
- Clear schema documentation
- Refactored directory logic
- Externalized exception lists
- Schema change tracking system

---

## Issues to Address

### Issue 1: Golden/Published Schema Mismatch

**Golden dataset** (38 fields): Internal working dataset with all fields including:
- Crosswalk mappings (Name - NYC.gov Agency List, Name - Ops, etc.)
- Source flags (Jan 2025 Org Chart)
- Internal notes

**Published dataset** (16 fields): Public-facing export with subset of fields:
- Core identity and status fields
- Principal officer info
- `in_org_chart` and `listed_in_nyc_gov_agency_directory`

**Problem**: The `NYC.gov Agency Directory` field in golden can have a different value than `listed_in_nyc_gov_agency_directory` in published because:
1. The published value is calculated during export
2. The golden value may be stale or set independently
3. Records not in published export still have values in golden

### Issue 2: Confusing Org Chart Fields

Current fields:
- `InOrgChart` - Boolean, used in export logic
- `Jan 2025 Org Chart` - Boolean, appears to be a point-in-time snapshot

**Questions to resolve**:
- What's the difference between these fields?
- Which one is authoritative?
- Should `Jan 2025 Org Chart` be renamed or deprecated?

### Issue 3: Hardcoded Exception Lists

Currently in `export_dataset.py`:
- `published_export_exceptions` (line 563-566, duplicated at 760-763)
- `nonprofit_exemptions` (line 166-173)
- `advisory_exemptions` (line 175-179)
- `manual_override_true_record_ids` (line 182-185)
- `manual_override_false_record_ids` (line 187-190)

**Problems**:
- Requires code changes to update
- Easy to miss duplicate lists
- No audit trail for when/why exemptions were added
- Not visible to non-developers

### Issue 4: No Schema Change Tracking

Currently no systematic way to track:
- When fields are added/removed/renamed
- Which version introduced schema changes
- Breaking vs non-breaking changes

---

## Phase 1: Document Current Schema

### 1.1 Create Schema Documentation

Create `nyc-governance-organizations/docs/SCHEMA.md`:

```markdown
# NYCGO Dataset Schema

## Golden Dataset (Internal)
38 fields - used for data management and pipeline processing

| Field | Type | Description | Added | Notes |
|-------|------|-------------|-------|-------|
| RecordID | string | Unique identifier | v1.0.0 | Format: NYC_GOID_XXXXXX |
| ... | ... | ... | ... | ... |

## Published Dataset (Public)
16 fields - exported to NYC Open Data portal

| Field | Type | Description | Derived From |
|-------|------|-------------|--------------|
| record_id | string | Unique identifier | RecordID |
| ... | ... | ... | ... |

## Field Mapping
| Golden (PascalCase) | Published (snake_case) | Notes |
|---------------------|------------------------|-------|
| RecordID | record_id | |
| ... | ... | |
```

### 1.2 Document Field Relationships

Clarify:
- [ ] `InOrgChart` vs `Jan 2025 Org Chart` - document purpose of each
- [ ] `NYC.gov Agency Directory` (golden) vs `listed_in_nyc_gov_agency_directory` (published)
- [ ] Which fields are source-of-truth vs derived

### Acceptance Criteria
- [ ] Complete schema documentation exists
- [ ] Field relationships documented
- [ ] Confusing fields clarified with decision on future handling

---

## Phase 2: Align Golden/Published Directory Field

### 2.1 Define Authoritative Source

**Proposed rule**: The published dataset is authoritative for `listed_in_nyc_gov_agency_directory`. The golden dataset's `NYC.gov Agency Directory` field should:
- Match the published value for records that are in the published dataset
- Be `False` (or empty) for records not in the published dataset

### 2.2 Implementation Options

**Option A: Post-export sync**
After generating published dataset, update golden dataset to match:
```python
# After export, update golden with calculated directory values
for record_id in golden_df['RecordID']:
    if record_id in published_df['record_id'].values:
        golden_value = published_df[published_df['record_id'] == record_id]['listed_in_nyc_gov_agency_directory'].iloc[0]
    else:
        golden_value = False
    golden_df.loc[golden_df['RecordID'] == record_id, 'NYC.gov Agency Directory'] = golden_value
```

**Option B: Single calculation point**
Calculate directory status once, use for both golden and published:
```python
# Calculate directory eligibility for all records
df['_directory_eligible'] = calculate_directory_eligibility(df)

# Apply to golden
golden_df['NYC.gov Agency Directory'] = df['_directory_eligible']

# Filter for published, apply same value
published_df = df[export_filter].copy()
published_df['listed_in_nyc_gov_agency_directory'] = published_df['_directory_eligible']
```

**Recommendation**: Option B - single source of truth for the calculation

### 2.3 Update Export Logic

Modify `export_dataset.py` to:
1. Calculate directory eligibility for ALL records first
2. Store in golden dataset
3. Filter for published export
4. Use same calculated values

### Acceptance Criteria
- [ ] Directory field calculated once, used consistently
- [ ] Golden and published values always match for shared records
- [ ] Records not in published have `False` in golden

---

## Phase 3: Externalize Exception Lists

### 3.1 Create Configuration File

Create `nyc-governance-organizations/config/export_rules.yaml`:

```yaml
# Export Rules Configuration
# Last updated: 2024-12-09
#
# Changes to this file should be committed with justification

# Records always included in published export regardless of InOrgChart/Name-Ops
published_export_exceptions:
  - record_id: NYC_GOID_000354
    name: Office of Collective Bargaining
    reason: "Added Sprint 5 - active org with public presence"
    added_date: 2024-12-09
  - record_id: NYC_GOID_000476
    name: MTA (Metropolitan Transportation Authority)
    reason: "State agency with significant NYC operations"
    added_date: 2024-01-01
  - record_id: NYC_GOID_100030
    name: Office of Digital Assets and Blockchain
    reason: "New mayoral office, not yet in org chart"
    added_date: 2024-11-21

# NYC.gov Agency Directory exemptions by organization type
directory_exemptions:
  nonprofit:
    - Brooklyn Public Library
    - New York City Tourism + Conventions
    - New York Public Library
    - Queens Public Library
    - Gracie Mansion Conservancy
    - Mayor's Fund to Advance New York City

  advisory:
    - Board of Elections
    - Campaign Finance Board
    - Rent Guidelines Board

# Manual overrides for directory field
directory_overrides:
  force_true: []
  force_false: []
```

### 3.2 Update Pipeline to Read Config

Modify `export_dataset.py`:
```python
import yaml

def load_export_rules():
    config_path = Path(__file__).parent.parent.parent / 'config' / 'export_rules.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)

rules = load_export_rules()
published_export_exceptions = [r['record_id'] for r in rules['published_export_exceptions']]
# ... etc
```

### 3.3 Add Config Validation

Create validation to ensure config file is valid:
- All record_ids exist in golden dataset
- No duplicate entries
- Required fields present

### Acceptance Criteria
- [ ] Exception lists moved to YAML config
- [ ] Pipeline reads from config file
- [ ] Config includes reason and date for each entry
- [ ] Validation prevents invalid config

---

## Phase 4: Schema Change Tracking

### 4.1 Create Schema Changelog

Create `nyc-governance-organizations/docs/SCHEMA_CHANGELOG.md`:

```markdown
# Schema Changelog

All schema changes to the NYCGO dataset are documented here.

## [v1.2.0] - TBD
### Added
- `Name - MOA` - Mayor's Office of Appointments crosswalk
- `AuthorizingAuthority` - Legal authority citation
- `AuthorizingAuthorityType` - Type of authority
- `AuthorizingURL` - URL to authorizing document
- `AppointmentsSummary` - Appointment process summary
- `GovernanceStructure` - Governance description
- `ParentOrganizationRecordID` - Parent org reference
- `ParentOrganizationName` - Parent org name

## [v1.1.0] - 2024-11-21
### Added
- Record NYC_GOID_100030 (Office of Digital Assets and Blockchain)

### Changed
- (none)

## [v1.0.0] - 2024-XX-XX
### Initial Release
- 38-field schema established
- 434 records
```

### 4.2 Automate Schema Diff

Create `scripts/check_schema_changes.py`:
```python
"""
Compare schema between two dataset versions.
Outputs added/removed/renamed fields.
Can be run as part of publish workflow.
"""
```

### 4.3 Integrate with Publish Workflow

Add step to `publish-release.yml`:
```yaml
- name: Check for schema changes
  run: |
    python scripts/check_schema_changes.py \
      --previous data/published/latest/NYCGO_golden_dataset_latest.csv \
      --current data/audit/runs/$RUN_ID/outputs/golden_pre-release.csv \
      --output schema_diff.md

    if [ -s schema_diff.md ]; then
      echo "::warning::Schema changes detected - review schema_diff.md"
      cat schema_diff.md
    fi
```

### Acceptance Criteria
- [ ] Schema changelog exists with historical entries
- [ ] Schema diff script works
- [ ] Publish workflow warns on schema changes
- [ ] Process documented for updating schema changelog

---

## Phase 5: Clarify Org Chart Fields

### 5.1 Document Field Purposes

| Field | Purpose | Authoritative? |
|-------|---------|----------------|
| `InOrgChart` | Record should appear in org chart exports | Yes - editable |
| `Jan 2025 Org Chart` | Snapshot: was in Jan 2025 org chart | No - historical reference |

### 5.2 Decision Needed

Options:
1. **Keep both** - `InOrgChart` is current state, `Jan 2025 Org Chart` is point-in-time snapshot
2. **Rename** - Change `Jan 2025 Org Chart` to something clearer like `InOrgChart_Jan2025_Snapshot`
3. **Deprecate** - Remove `Jan 2025 Org Chart` if no longer needed

### 5.3 Update Logic if Needed

If we keep both, ensure:
- Export logic uses `InOrgChart` (current)
- Directory logic uses `InOrgChart` (current)
- `Jan 2025 Org Chart` is informational only

### Acceptance Criteria
- [ ] Decision made on org chart fields
- [ ] Documentation updated
- [ ] Export/directory logic uses correct field

---

## Phase 6: Edit UI Directory Logic Transparency

### 6.1 Problem

Users editing records don't understand why a record is or isn't in the NYC.gov Agency Directory. The logic is hidden in Python code and not visible in the UI.

### 6.2 Solution

Show directory eligibility reasoning in the Edit UI for each record.

### 6.3 UI Display

When viewing/editing a record, show:

```
NYC.gov Agency Directory: ✅ True

Why this record qualifies:
├─ OperationalStatus: Active ✓
├─ OrganizationType: Mayoral Agency
├─ Has contact info: ✓ (URL exists)
└─ Not in exclusion list ✓

📖 View directory logic rules
```

Or for a record that doesn't qualify:

```
NYC.gov Agency Directory: ❌ False

Why this record doesn't qualify:
├─ OperationalStatus: Active ✓
├─ OrganizationType: Advisory or Regulatory Organization
├─ InOrgChart: ❌ (empty)
├─ Has nyc.gov URL: ❌ (uses ocb-nyc.org)
└─ In advisory exemptions: ❌

📖 View directory logic rules
```

### 6.4 Implementation Options

**Option A: Client-side logic**
- Replicate the Python logic in JavaScript
- Pros: Fast, no API needed
- Cons: Logic duplication, can drift from Python

**Option B: Pre-computed field**
- Add `directory_eligibility_reason` field to golden dataset
- Pipeline computes and stores the reasoning
- UI just displays it
- Pros: Single source of truth
- Cons: Adds field to dataset

**Option C: API endpoint**
- Create a simple endpoint that evaluates a record
- Pros: Logic stays in Python
- Cons: Requires backend infrastructure

**Recommendation**: Option B - add a `directory_eligibility_reason` field computed during export.

### 6.5 Link to Logic Documentation

Add a "View directory logic rules" link that points to:
- `docs/DIRECTORY_LOGIC.md` (to be created)
- Or directly to the relevant section of `export_dataset.py`

### 6.6 Files to Modify

- `nycgo-admin-ui/js/app.js` - Display eligibility reasoning
- `nycgo-admin-ui/index.html` - Add reasoning display section
- `nyc-governance-organizations/scripts/process/export_dataset.py` - Generate reasoning field
- `nyc-governance-organizations/docs/DIRECTORY_LOGIC.md` - Document the rules

### Acceptance Criteria
- [ ] Each record shows directory eligibility reasoning in Edit UI
- [ ] Reasoning matches actual export logic
- [ ] Link to documentation provided
- [ ] Users can understand why a record is/isn't in the directory

---

## Definition of Done

- [ ] Schema documentation complete (`docs/SCHEMA.md`)
- [ ] Golden/published directory field alignment implemented
- [ ] Exception lists externalized to YAML config
- [ ] Schema changelog created with historical entries
- [ ] Schema diff automation in place
- [ ] Org chart field confusion resolved
- [ ] Edit UI shows directory eligibility reasoning (Phase 6)
- [ ] All changes tested with pipeline run

---

## Future Considerations

### Potential Sprint 7 Items
- Revise published export filter to use `NYC.gov Agency Directory` instead of `InOrgChart | has_ops_name`
- Add more sophisticated directory eligibility rules
- Create admin interface for managing exception lists
- Automate schema changelog updates

### Technical Debt Identified
- Duplicate exception lists in `export_dataset.py` (main and main_with_dataframe)
- Directory logic is complex and spread across multiple functions
- No integration tests for export logic
