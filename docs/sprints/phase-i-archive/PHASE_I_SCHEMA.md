# Phase I Schema Documentation (v1.0.0)

## Overview

Phase I (v1.0.0) represents the initial stable release of the NYC Governance Organizations dataset. This schema was released on October 7, 2024, with 38 fields in the golden dataset and 16 fields in the public export.

## Version: v1.0.0

**Release Date:** October 7, 2024
**Golden Dataset Fields:** 38
**Public Export Fields:** 16
**Entity Count:** 433

---

## Golden Dataset Schema (38 Fields)

The golden dataset contains all internal fields used for data management, including source tracking fields and operational metadata.

### Core Identity Fields

1. **RecordID** (String)
   - Stable internal identifier (immutable)
   - Format: `NYC_GOID_XXXXXX` (e.g., `NYC_GOID_000318`)
   - Primary key for all records

2. **Name** (String)
   - Official/preferred name of the organization

3. **NameAlphabetized** (String)
   - Name normalized for alphabetical sorting

4. **OperationalStatus** (String)
   - Current status of the organization
   - Values: "Active", "Inactive", "Dissolved", etc.

5. **OrganizationType** (String)
   - Category classification
   - Examples: "Mayoral Agency", "Advisory or Regulatory Organization", "Nonprofit Organization", etc.

### Descriptive Fields

6. **Description** (Text)
   - Detailed description of the organization's purpose and function

7. **URL** (String)
   - Official website URL

8. **AlternateOrFormerNames** (Text)
   - Other names seen in official sources

9. **Acronym** (String)
   - Official acronym (if any)

10. **AlternateOrFormerAcronyms** (Text)
    - Other acronyms seen in official sources

11. **Notes** (Text)
    - Additional notes and context

### Budget and Data Fields

12. **BudgetCode** (String)
    - Budget code identifier

13. **OpenDatasetsURL** (String)
    - Link to related NYC Open Data datasets

14. **FoundingYear** (String)
    - Year the organization was founded/established

### Principal Officer Fields

15. **PrincipalOfficerName** (String)
    - Full name of principal officer (legacy field)

16. **PrincipalOfficerFullName** (String)
    - Full name of principal officer

17. **PrincipalOfficerGivenName** (String)
    - Given (first) name

18. **PrincipalOfficerMiddleNameOrInitial** (String)
    - Middle name or initial

19. **PrincipalOfficerFamilyName** (String)
    - Family (last) name

20. **PrincipalOfficerSuffix** (String)
    - Name suffix (Jr., Sr., III, etc.)

21. **PrincipalOfficerTitle** (String)
    - Title of the principal officer

22. **PrincipalOfficerContactURL** (String)
    - Profile/contact page URL for principal officer

### Organizational Relationships

23. **ReportsTo** (String)
    - Reporting/administrative/oversight relationship
    - Note: In Phase II, this field's semantics changed significantly

24. **InOrgChart** (Boolean)
    - Flag indicating if entity appears in citywide org chart

25. **ReportingNotes** (Text)
    - Notes about reporting relationships

### Source Tracking Fields

26. **InstanceOf** (String)
    - Type classification

27. **Name - NYC.gov Agency List** (String)
    - Name as it appears on NYC.gov Agency List

28. **Name - NYC.gov Mayor's Office** (String)
    - Name as it appears on Mayor's Office website

29. **Name - NYC Open Data Portal** (String)
    - Name as it appears on NYC Open Data Portal

30. **Name - ODA** (String)
    - Name as it appears in ODA system

31. **Name - CPO** (String)
    - Name as it appears in CPO system

32. **Name - WeGov** (String)
    - Name as it appears in WeGov system

33. **Name - Greenbook** (String)
    - Name as it appears in Greenbook

34. **Name - Checkbook** (String)
    - Name as it appears in Checkbook system

35. **Name - HOO** (String)
    - Name as it appears in HOO system

36. **Name - Ops** (String)
    - Name as it appears in Ops system

37. **NYC.gov Agency Directory** (Boolean)
    - Flag indicating if entity appears in NYC.gov Agency Directory

38. **Jan 2025 Org Chart** (Boolean)
    - Flag indicating if entity appears in January 2025 org chart

---

## Public Export Schema (16 Fields)

The public export contains a subset of fields suitable for public release, with column names converted to snake_case.

### Exported Fields (snake_case in public export)

1. `record_id` - RecordID
2. `name` - Name
3. `name_alphabetized` - NameAlphabetized
4. `operational_status` - OperationalStatus
5. `organization_type` - OrganizationType
6. `url` - URL
7. `alternate_or_former_names` - AlternateOrFormerNames
8. `acronym` - Acronym
9. `alternate_or_former_acronyms` - AlternateOrFormerAcronyms
10. `principal_officer_full_name` - PrincipalOfficerFullName
11. `principal_officer_first_name` - PrincipalOfficerFirstName (derived from PrincipalOfficerGivenName)
12. `principal_officer_last_name` - PrincipalOfficerLastName (derived from PrincipalOfficerFamilyName)
13. `principal_officer_title` - PrincipalOfficerTitle
14. `principal_officer_contact_url` - PrincipalOfficerContactURL
15. `reports_to` - ReportsTo
16. `in_org_chart` - InOrgChart

### Additional Public Field (Computed)

17. `listed_in_nyc_gov_agency_directory` (Boolean)
    - Computed field added during export
    - Determined by directory logic v2

---

## Field Naming Conventions

- **Internal Schema (Golden Dataset):** PascalCase (e.g., `RecordID`, `PrincipalOfficerFullName`)
- **Public Export:** snake_case (e.g., `record_id`, `principal_officer_full_name`)
- **Conversion:** Performed automatically by `export_dataset.py` using `to_snake_case()` function

---

## Phase I vs Phase II Differences

### Phase I (v1.0.0)
- 38 fields in golden dataset
- 16 fields in public export (+ 1 computed field)
- `ReportsTo` field captures both org chart oversight and legal reporting relationships

### Phase II (v2.0.0-dev)
- 42 fields in golden dataset (38 Phase I + 4 Phase II fields initially)
- 20 fields in public export (16 Phase I + 4 Phase II)
- `ReportsTo` field semantics changed (breaking change)
- Added: `org_chart_oversight`, `authorizing_authority`, `authorizing_url`, `appointments_summary`

### Finalized Phase II (Proposed)
- 46 fields in golden dataset (38 Phase I - 1 retired + 9 new)
- Retires: `reports_to`
- Adds: `governance_structure`, `org_chart_oversight_record_id`, `org_chart_oversight_name`, `parent_organization_record_id`, `parent_organization_name`, `authorizing_authority`, `authorizing_authority_type`, `authorizing_url`, `appointments_summary`

---

## Usage Notes

- **For Phase I edits:** Use Phase I field names only (see `PHASE_I_SCHEMA_FIELDS.txt` for complete list)
- **Field names in edits_to_make files:** Use snake_case (matching public export format)
- **RecordID format:** Phase I uses `NYC_GOID_XXXXXX` format
- **Phase II fields:** Do NOT use Phase II fields (`org_chart_oversight`, `authorizing_authority`, `authorizing_url`, `appointments_summary`) when creating Phase I edits

---

## References

- **Phase II Schema:** `docs/PHASE_II_SCHEMA.md`
- **Schema Comparison:** `docs/SCHEMA_VERSION_COMPARISON.md`
- **Export Script:** `scripts/process/export_dataset.py`
- **v1.0.0 Release:** Git tag `v1.0.0` (commit `4a2cdd8`)

---

**Last Updated:** November 21, 2024
**Status:** Archived - Phase I schema preserved for reference
