# NYCGO Dataset Schema Reference

This document describes the field schema for the NYC Governance Organizations dataset.

## Overview

The dataset exists in two forms:

1. **Golden Dataset** (38 fields) - Internal master dataset with all metadata
2. **Published Dataset** (17 fields) - Public export for NYC.gov Agency Directory

For detailed descriptions of the 17 published fields, see the [Data Dictionary](NYC_Agencies_and_Governance_Organizations_Data_Dictionary.xlsx).

## Field Naming History

> **Note:** Prior to v1.8.0, the fields `principal_officer_first_name` and `principal_officer_last_name` were named `principal_officer_given_name` and `principal_officer_family_name` respectively. The rename aligns the golden dataset with the published export naming convention.

## All Fields (Golden Dataset)

| # | Field Name | Description | In Published |
|---|------------|-------------|--------------|
| 1 | `record_id` | Stable internal identifier (format: `NYC_GOID_XXXXXX`) | Yes |
| 2 | `name` | Official/preferred name of the organization | Yes |
| 3 | `name_alphabetized` | Name normalized for alphabetical sorting | Yes |
| 4 | `operational_status` | Current status (Active, Inactive, Dissolved, etc.) | Yes |
| 5 | `organization_type` | Category classification | Yes |
| 6 | `description` | Detailed description of purpose and function | No |
| 7 | `url` | Official website URL | Yes |
| 8 | `alternate_or_former_names` | Other names (semicolon-separated) | Yes |
| 9 | `acronym` | Official acronym | Yes |
| 10 | `alternate_or_former_acronyms` | Other acronyms | Yes |
| 11 | `budget_code` | NYC budget code identifier | No |
| 12 | `open_datasets_url` | Link to NYC Open Data datasets | No |
| 13 | `founding_year` | Year established | No |
| 14 | `principal_officer_full_name` | Full name of principal officer | Yes |
| 15 | `principal_officer_first_name` | First name of principal officer | Yes |
| 16 | `principal_officer_middle_name_or_initial` | Middle name or initial | No |
| 17 | `principal_officer_last_name` | Last name of principal officer | Yes |
| 18 | `principal_officer_suffix` | Name suffix (Jr., Sr., III, etc.) | No |
| 19 | `principal_officer_name` | Full name (legacy field) | No |
| 20 | `principal_officer_title` | Title of principal officer | Yes |
| 21 | `principal_officer_contact_url` | Profile/contact page URL | Yes |
| 22 | `notes` | Additional notes and context | No |
| 23 | `instance_of` | Type classification | No |
| 24 | `name_nycgov_agency_list` | Name on NYC.gov Agency List | No |
| 25 | `name_nycgov_mayors_office` | Name on Mayor's Office website | No |
| 26 | `name_nyc_open_data_portal` | Name on NYC Open Data Portal | No |
| 27 | `name_oda` | Name in ODA system | No |
| 28 | `name_cpo` | Name in CPO system | No |
| 29 | `name_wegov` | Name in WeGov system | No |
| 30 | `name_greenbook` | Name in Greenbook | No |
| 31 | `name_checkbook` | Name in Checkbook system | No |
| 32 | `name_hoo` | Name in HOO system | No |
| 33 | `name_ops` | Name in Ops system | No |
| 34 | `in_org_chart` | Appears in current citywide org chart | Yes |
| 35 | `reports_to` | Reporting/oversight relationship | Yes |
| 36 | `reporting_notes` | Notes about reporting relationships | No |
| 37 | `jan_2025_org_chart` | Appeared in January 2025 org chart | No |
| 38 | `listed_in_nyc_gov_agency_directory` | Computed directory eligibility flag | Yes |

## Golden-Only Fields (21)

These fields are maintained in the golden dataset but not included in the published export:

- `description` - Full description text
- `budget_code` - Internal budget identifier
- `open_datasets_url` - Link to Open Data portal
- `founding_year` - Year established
- `principal_officer_middle_name_or_initial` - Middle name/initial
- `principal_officer_suffix` - Name suffix
- `principal_officer_name` - Legacy full name field
- `notes` - Internal notes
- `instance_of` - Type classification
- `name_*` (10 fields) - Name variants from different source systems
- `reporting_notes` - Internal reporting notes
- `jan_2025_org_chart` - Historical org chart snapshot

## Org Chart Fields Explained

The dataset contains two org chart-related fields that serve different purposes:

### `in_org_chart` (Published)
- **Purpose**: Current truth about whether an organization appears in the citywide org chart
- **Values**: `TRUE`, `FALSE`, or empty
- **Usage**: Used in directory eligibility calculations for certain organization types
- **Updates**: Maintained as current state; should reflect latest org chart

### `jan_2025_org_chart` (Golden-only)
- **Purpose**: Historical snapshot of org chart status as of January 2025
- **Values**: `TRUE`, `FALSE`, or empty
- **Usage**: Reference for tracking changes over time; useful for auditing
- **Updates**: Immutable snapshot; not updated after initial recording

The distinction allows:
1. Tracking current eligibility status (`in_org_chart`)
2. Auditing changes since a baseline date (`jan_2025_org_chart`)

## Enumerated Values

### `operational_status`
- Active
- Inactive
- Dissolved
- Reorganized
- Verification Pending
- Excluded

### `organization_type`
- Mayoral Agency
- Mayoral Office
- Division
- Elected Office
- Advisory or Regulatory Organization
- Nonprofit Organization
- Public Benefit or Development Organization
- State Government Agency
- Pension Fund

## Primary Key

The `record_id` field is the immutable primary key. Format: `NYC_GOID_XXXXXX` (6-digit zero-padded number).

## Machine-Readable Schema

See `schemas/nycgo_golden_dataset.tableschema.json` for the complete Table Schema specification.
