# Logic for `listed_in_nyc_gov_agency_directory` Field

## Overview

The `listed_in_nyc_gov_agency_directory` field determines which organizations appear in the public-facing NYC.gov Agency Directory. This field is computed automatically during the export process using business logic defined in `scripts/process/export_dataset.py::add_nycgov_directory_column()`.

**Current Logic Version:** `directory_logic_v2`

## Decision Flow

A record is marked `TRUE` for `listed_in_nyc_gov_agency_directory` if it passes **ALL** of the following:

### Step 1: Blanket Gatekeeper Rules (ALL must pass)

1. **Operational Status = Active**
   - `operational_status` must be exactly "Active" (case-insensitive)

2. **URL does NOT contain state "ny.gov"**
   - URL must NOT contain `.ny.gov` (state government URLs)
   - City URLs like `.nyc.gov` are OK
   - Records with no URL can still pass if they have other contact info

3. **Has at least ONE contact field**
   - Must have at least one of:
     - `url` (non-empty)
     - `principal_officer_full_name` (non-empty)
     - `principal_officer_contact_url` (non-empty)

### Step 2: Organization Type Specific Rules

After passing blanket rules, inclusion depends on `organization_type`:

| Organization Type | Inclusion Rule |
|------------------|----------------|
| **Mayoral Agency** | ✅ All included (if passes blanket rules) |
| **Mayoral Office** | ✅ All included (if passes blanket rules) |
| **Division** | ✅ Only if `in_org_chart = True` |
| **Elected Office** | ✅ All included (if passes blanket rules) |
| **Nonprofit Organization** | ✅ Only if `in_org_chart = True` **OR** in exemption list |
| **Pension Fund** | ✅ All included (if passes blanket rules) |
| **State Government Agency** | ✅ All included (if passes blanket rules) |
| **Public Benefit or Development Organization** | ✅ Only if `in_org_chart = True` |
| **Advisory or Regulatory Organization** | ✅ If `in_org_chart = True` **OR** has main `nyc.gov/index.page` URL **OR** in exemption list |

### Step 3: Manual Overrides (applied last)

Manual overrides can force TRUE or FALSE for specific record IDs, regardless of the above rules.

- **Manual TRUE overrides:** Force inclusion even if rules don't apply
- **Manual FALSE overrides:** Force exclusion even if rules would include

## Exemption Lists

### Nonprofit Organization Exemptions
These nonprofits are included even if `in_org_chart = False`:
- Brooklyn Public Library
- New York City Tourism + Conventions
- New York Public Library
- Queens Public Library
- Gracie Mansion Conservancy
- Mayor's Fund to Advance New York City

### Advisory or Regulatory Organization Exemptions
These advisory/regulatory orgs are included even if they don't meet other criteria:
- Board of Elections
- Campaign Finance Board
- Rent Guidelines Board

## Examples

### Example 1: Mayoral Office (Included)
- ✅ `operational_status = "Active"`
- ✅ `url = "https://www.nyc.gov/content/oti/pages/"` (city URL, not state)
- ✅ `principal_officer_full_name = "Matthew Fraser"` (has contact info)
- ✅ `organization_type = "Mayoral Office"` (all included)
- **Result:** `listed_in_nyc_gov_agency_directory = True`

### Example 2: Division (Conditional)
- ✅ `operational_status = "Active"`
- ✅ `url = "https://portal.311.nyc.gov/"` (city URL)
- ✅ `principal_officer_full_name = "Joseph Morrisroe"` (has contact info)
- ✅ `organization_type = "Division"`
- ✅ `in_org_chart = True` (required for Divisions)
- **Result:** `listed_in_nyc_gov_agency_directory = True`

### Example 3: Division (Excluded)
- ✅ `operational_status = "Active"`
- ✅ `url = "https://example.nyc.gov/"` (city URL)
- ✅ `principal_officer_full_name = "John Doe"` (has contact info)
- ✅ `organization_type = "Division"`
- ❌ `in_org_chart = False` (Divisions must be in org chart)
- **Result:** `listed_in_nyc_gov_agency_directory = False`

### Example 4: State Agency (Excluded by Blanket Rule)
- ✅ `operational_status = "Active"`
- ❌ `url = "https://example.ny.gov/"` (state URL - violates blanket rule)
- ✅ `principal_officer_full_name = "Jane Smith"` (has contact info)
- ✅ `organization_type = "State Government Agency"`
- **Result:** `listed_in_nyc_gov_agency_directory = False` (fails blanket rule #2)

### Example 5: Nonprofit with Exemption (Included)
- ✅ `operational_status = "Active"`
- ✅ `url = "https://www.nypl.org/"` (not state URL)
- ✅ `principal_officer_full_name = "Anthony Marx"` (has contact info)
- ✅ `organization_type = "Nonprofit Organization"`
- ❌ `in_org_chart = False`
- ✅ `name = "New York Public Library"` (in exemption list)
- **Result:** `listed_in_nyc_gov_agency_directory = True` (exemption applies)

## Implementation Details

- **Location:** `scripts/process/export_dataset.py::add_nycgov_directory_column()`
- **Applied:** During export process, after snake_case conversion
- **Change Tracking:** Changes are tracked in the changelog when `run_id` is provided
- **Version:** Current logic is `directory_logic_v2`

## Debug Output

When the pipeline runs, it prints debug information showing:
- How many records pass each blanket rule
- How many records of each organization type are included
- First 5 records marked as TRUE
- Any warnings (e.g., state URLs that slipped through)

Example output:
```
Debug - Blanket gatekeeper rules:
  - Records with operational_status = 'active': 304
  - Records with state 'ny.gov' URLs (excluded): 4
  - Records with at least one contact field: 296
  - Records passing ALL blanket rules: 292

Debug - Organization type specific rules:
  - Mayoral Agency: 32 total
  - Mayoral Office: 72 total
  - Division (in Org Chart): 17 included
  ...
```

## Notes

- The field is computed dynamically during export, not stored in the golden dataset
- Manual overrides are currently empty (all logic is type-based)
- The logic version is tracked in changelog entries (`directory_logic_v2`)
- Changes to this logic should be documented in `docs/DIRECTORY_FIELD_CHANGELOG.md`
