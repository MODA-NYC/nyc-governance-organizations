# Phase I Fields Reference for Edits

This document lists all Phase I fields that can be used in `edits_to_make` CSV files. **Use only Phase I fields** when creating edits for Phase I schema compatibility.

## Field Names in Edits Files

**Important:** Edits files use **snake_case** field names (matching the public export format), not PascalCase.

## Core Fields

- `record_id` - Stable internal ID (use `NEW` for new records)
- `name` - Official/preferred name
- `name_alphabetized` - Name normalized for sorting
- `operational_status` - Current status (e.g., "Active", "Inactive", "Dissolved")
- `organization_type` - Category (e.g., "Mayoral Agency", "Advisory or Regulatory Organization")

## Descriptive Fields

- `url` - Official website URL
- `alternate_or_former_names` - Other names seen in official sources
- `acronym` - Official acronym (if any)
- `alternate_or_former_acronyms` - Other acronyms seen in official sources

## Principal Officer Fields

- `principal_officer_full_name` - Full name of principal officer
- `principal_officer_first_name` - Given (first) name
- `principal_officer_last_name` - Family (last) name
- `principal_officer_title` - Title of the principal officer
- `principal_officer_contact_url` - Profile/contact page URL

## Organizational Relationships

- `reports_to` - Reporting/administrative/oversight relationship
- `in_org_chart` - Boolean flag (use "True" or "False")

## Example Usage

```csv
Row(s),Column,feedback,reason
NEW,name,"Set to ""New Organization""","Add new entity"
NEW,operational_status,"Set to ""Active""","Add new entity - currently active"
NYC_GOID_000123,name,"Set to ""Updated Name""","Update existing entity - name change"
```

## Fields NOT Available in Phase I

Do **NOT** use these Phase II fields in Phase I edits:

- `org_chart_oversight` ❌
- `authorizing_authority` ❌
- `authorizing_url` ❌
- `appointments_summary` ❌
- `governance_structure` ❌
- `org_chart_oversight_record_id` ❌
- `org_chart_oversight_name` ❌
- `parent_organization_record_id` ❌
- `parent_organization_name` ❌
- `authorizing_authority_type` ❌

## Notes

- For new records, use `NEW` as the Row(s) value
- For existing records, use the RecordID (e.g., `NYC_GOID_000123`)
- Field values in feedback column should be wrapped in double quotes if they contain commas
- Use "True" or "False" (capitalized) for boolean fields like `in_org_chart`

## See Also

- `docs/PHASE_I_SCHEMA.md` - Full Phase I schema documentation
- `docs/PHASE_I_SCHEMA_FIELDS.txt` - Complete field list
- `data/input/templates/phase_i_edits_template.csv` - Template file with examples
