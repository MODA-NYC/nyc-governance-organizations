# Sprint 3: Data Quality & Standardization

**Status: ⚠️ PARTIALLY COMPLETE**
**Last reviewed: December 2024**

## Overview

This sprint addresses formatting inconsistencies and technical debt identified during Sprint 2 testing. The goal is to establish clear standards for data formatting, field naming, and output consistency.

**Inputs**: Validated pipeline from Sprint 2, identified issues list
**Outputs**: Standardized formatting, documented conventions, clean pipeline output

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Boolean Standardization | ❌ NOT DONE | Mixed formats in data: `TRUE`/`False`, `True`/`False` |
| Phase 2: Numeric Standardization | ⚠️ PARTIAL | BudgetCode good (3-digit), FoundingYear still has `.0` suffix |
| Phase 3: Field Name Conventions | ⚠️ PARTIAL | Mapping exists in code but not formally documented |
| Phase 4: Column Order | 🔮 DEFERRED | To be done with Phase II release (FUTURE.md) |
| Phase 5: CSV Output Consistency | ✅ DONE | Pipeline uses UTF-8 with BOM, consistent settings |

**Remaining work**: Boolean normalization and FoundingYear cleanup should be addressed in a future sprint or as part of Sprint 6 schema work.

---

## Goals

1. **Standardize boolean formatting** - Consistent `TRUE`/`FALSE` vs `True`/`False`
2. **Standardize numeric formatting** - BudgetCode leading zeros, FoundingYear format
3. **Field name conventions** - Document and potentially standardize snake_case vs PascalCase
4. **Column order** - Logical grouping of fields in output
5. **Pipeline output consistency** - Ensure reproducible, well-formatted output

---

## Phase 1: Boolean Value Standardization

### Current State

| Field | Published v1.1.1 | Working Files |
|-------|------------------|---------------|
| InOrgChart | `TRUE`/`FALSE` | `True`/`False` |
| NYC.gov Agency Directory | `True`/`False` | `True`/`False` |
| Jan 2025 Org Chart | `True`/`False` | `True`/`False` |

### Decision Needed

**Option A**: Uppercase `TRUE`/`FALSE`
- Matches Excel/spreadsheet conventions
- More visually distinct
- Current published format

**Option B**: Title case `True`/`False`
- Matches Python boolean literals
- More common in data science contexts

**Recommendation**: Option A (`TRUE`/`FALSE`) - matches published format, minimizes downstream impact

### Implementation

#### 1. Pipeline Output Formatting

Update the pipeline's output formatting to standardize booleans:

```python
# In pipeline output code
def format_boolean(value):
    if pd.isna(value) or value == '':
        return ''
    if str(value).lower() in ('true', '1', 'yes'):
        return 'TRUE'
    if str(value).lower() in ('false', '0', 'no'):
        return 'FALSE'
    return value
```

#### 2. Apply to Existing Data

One-time cleanup of working files (if any remain after Sprint 1 Phase 3).

### Affected Fields
- `InOrgChart`
- `NYC.gov Agency Directory`
- `Jan 2025 Org Chart`
- Any other boolean fields

### Acceptance Criteria
- [ ] Standard chosen and documented
- [ ] Pipeline outputs consistent boolean format
- [ ] Existing data cleaned up
- [ ] No mixed formats in output

---

## Phase 2: Numeric Field Standardization

### BudgetCode

#### Current State
- Published: `068` (string with leading zero preserved)
- Working: `68.0` (float, leading zero lost)

#### Standard
BudgetCode should be stored as a **3-digit zero-padded string**: `068`, `001`, `126`

#### Implementation

```python
def format_budget_code(value):
    if pd.isna(value) or value == '':
        return ''
    # Handle float inputs (68.0 -> 68 -> '068')
    if isinstance(value, float):
        value = int(value)
    return str(value).zfill(3)
```

### FoundingYear

#### Current State
- Published: `1996.0` (float format)
- Expected: `1996` (integer or clean string)

#### Standard
FoundingYear should be stored as an **integer or 4-digit string**: `1996`, `2003`

#### Implementation

```python
def format_year(value):
    if pd.isna(value) or value == '':
        return ''
    if isinstance(value, float):
        return str(int(value))
    return str(value)
```

### Acceptance Criteria
- [ ] BudgetCode always 3-digit zero-padded
- [ ] FoundingYear always clean integer format
- [ ] No `.0` suffixes in numeric fields

---

## Phase 3: Field Name Conventions

### Current State

**Edit files** use snake_case:
```csv
record_id,record_name,field_name,action,justification,evidence_url
100001,Dept of Finance,operational_status,Set to "Active",...
```

**Golden dataset** uses PascalCase:
```csv
RecordID,Name,OperationalStatus,...
```

### Options

#### Option A: Standardize on PascalCase Everywhere
- Edit files use `OperationalStatus` instead of `operational_status`
- Simpler mapping (no transformation needed)
- Matches published schema directly

#### Option B: Standardize on snake_case Everywhere
- Change golden dataset to `record_id`, `operational_status`
- More developer-friendly
- **Breaking change** for downstream consumers

#### Option C: Keep Both with Explicit Mapping
- Edit files use snake_case (developer-friendly input)
- Pipeline maps to PascalCase (published output)
- Document the mapping clearly

**Recommendation**: Option C - maintain compatibility while keeping edit files readable

### Mapping Table

| Edit File (snake_case) | Golden Dataset (PascalCase) |
|------------------------|-----------------------------|
| record_id | RecordID |
| name | Name |
| name_alphabetized | NameAlphabetized |
| operational_status | OperationalStatus |
| organization_type | OrganizationType |
| description | Description |
| url | URL |
| alternate_or_former_names | AlternateOrFormerNames |
| acronym | Acronym |
| budget_code | BudgetCode |
| founding_year | FoundingYear |
| principal_officer_name | PrincipalOfficerName |
| ... | ... |

### Implementation

1. Document the mapping in a schema file
2. Ensure pipeline validates field names against mapping
3. Update review UI to show both formats where helpful

### Acceptance Criteria
- [ ] Decision documented
- [ ] Mapping table complete
- [ ] Pipeline validates field names
- [ ] Review UI handles mapping correctly

---

## Phase 4: Column Order Reorganization

### Current State (v1.1.x - 38 columns)

Columns are roughly grouped but could be more logical:
1. Identity (RecordID, Name, NameAlphabetized)
2. Status (OperationalStatus, OrganizationType)
3. Description (Description, URL)
4. Names/Aliases (AlternateOrFormerNames, Acronym, etc.)
5. Administrative (BudgetCode, OpenDatasetsURL, FoundingYear)
6. Officer Info (PrincipalOfficer*)
7. Internal (Notes, InstanceOf)
8. Crosswalk mappings (Name - NYC.gov Agency List, etc.)
9. Org Chart (NYC.gov Agency Directory, Jan 2025 Org Chart, InOrgChart, ReportsTo, etc.)

### Phase II Additions (columns 39-46)

Currently appended at end:
- Name - MOA
- AuthorizingAuthority
- AuthorizingAuthorityType
- AuthorizingURL
- AppointmentsSummary
- GovernanceStructure
- ParentOrganizationRecordID
- ParentOrganizationName

### Proposed Logical Grouping

```
IDENTITY
  RecordID, Name, NameAlphabetized, Acronym, AlternateOrFormerNames, AlternateOrFormerAcronyms

STATUS & TYPE
  OperationalStatus, OrganizationType, InstanceOf

DESCRIPTION
  Description, URL

GOVERNANCE (Phase II)
  AuthorizingAuthority, AuthorizingAuthorityType, AuthorizingURL
  GovernanceStructure, AppointmentsSummary

ORGANIZATIONAL STRUCTURE
  ParentOrganizationRecordID, ParentOrganizationName
  ReportsTo, ReportingNotes, InOrgChart

ADMINISTRATIVE
  BudgetCode, FoundingYear, OpenDatasetsURL

LEADERSHIP
  PrincipalOfficerName, PrincipalOfficerTitle, PrincipalOfficerContactURL
  PrincipalOfficerFullName, PrincipalOfficerGivenName, PrincipalOfficerMiddleNameOrInitial
  PrincipalOfficerFamilyName, PrincipalOfficerSuffix

CROSSWALK MAPPINGS
  Name - NYC.gov Agency List, Name - NYC.gov Mayor's Office, Name - NYC Open Data Portal
  Name - ODA, Name - CPO, Name - WeGov, Name - Greenbook, Name - Checkbook
  Name - HOO, Name - Ops, Name - MOA

SOURCE FLAGS
  NYC.gov Agency Directory, Jan 2025 Org Chart

INTERNAL
  Notes
```

### Decision Needed

**Option A**: Reorganize now (Sprint 3)
- Cleaner schema for Phase II release
- One-time migration effort
- May require downstream consumer updates

**Option B**: Defer to Phase II release (Sprint 4)
- Batch the breaking change with schema expansion
- Less churn

**Option C**: Don't reorganize
- Maintain backwards compatibility
- Accept less logical grouping

**Recommendation**: Option B - reorganize as part of Sprint 4 Phase II release

### Acceptance Criteria
- [ ] Decision made and documented
- [ ] If reorganizing: new column order defined
- [ ] If reorganizing: migration plan created

---

## Phase 5: Pipeline Output Consistency

### CSV Formatting Standards

#### Encoding
- UTF-8 with BOM (for Excel compatibility)
- Or UTF-8 without BOM (for maximum compatibility)
- **Decision needed**

#### Quoting
- Quote fields containing commas, quotes, or newlines
- Use double-quotes, escape internal quotes by doubling

#### Line Endings
- Unix-style LF (`\n`)
- Or Windows-style CRLF (`\r\n`)
- **Decision needed**: Recommend LF for git consistency

#### Empty Values
- Empty string `""` vs missing (no value between commas)
- **Standard**: Empty string for optional fields

### Implementation

Update pipeline output to use consistent settings:

```python
df.to_csv(
    output_path,
    index=False,
    encoding='utf-8-sig',  # UTF-8 with BOM
    quoting=csv.QUOTE_MINIMAL,
    lineterminator='\n'
)
```

### Acceptance Criteria
- [ ] CSV formatting standards documented
- [ ] Pipeline outputs match standards
- [ ] Output passes validation checks

---

## Testing

### Validation Script

Create `scripts/validate_data_quality.py`:

```python
"""
Validates golden dataset against quality standards:
- Boolean format (TRUE/FALSE)
- BudgetCode format (3-digit padded)
- FoundingYear format (integer)
- No unexpected NULL values
- Column order (if applicable)
"""
```

### Test Cases
- [ ] TC-1: Boolean fields contain only TRUE/FALSE/empty
- [ ] TC-2: BudgetCode is 3-digit zero-padded or empty
- [ ] TC-3: FoundingYear is integer or empty
- [ ] TC-4: No `.0` suffixes in any field
- [ ] TC-5: CSV encoding is correct
- [ ] TC-6: Line endings are consistent

---

## Documentation Updates

- [ ] Update schema documentation with formatting standards
- [ ] Document field name mapping (snake_case ↔ PascalCase)
- [ ] Add data quality standards to README or docs/
- [ ] Update CONTRIBUTING.md with formatting guidelines

---

## Definition of Done

- [ ] Boolean formatting standardized and implemented
- [ ] Numeric formatting standardized and implemented
- [ ] Field name convention documented
- [ ] Column order decision made
- [ ] CSV output settings standardized
- [ ] Validation script created and passing
- [ ] Documentation updated
- [ ] Ready for Sprint 4
