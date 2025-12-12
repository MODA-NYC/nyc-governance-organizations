# Schema Changelog

This file documents all schema changes to the NYC Governance Organizations datasets.

## Schema Files

- **`nycgo_golden_dataset.tableschema.json`** - Golden dataset schema (internal, 38 fields)
- **`nycgo_published_dataset.tableschema.json`** - Published dataset schema (Open Data, 17 fields)

---

## Published Dataset Schema Changes

### v1.7.0 (2024-12-12)

**Added:**
- `reports_to` - Restored field that was accidentally omitted from PUBLISHED_COLUMN_ORDER

**Context:**
The `reports_to` field was present in the Open Data portal but missing from our published CSV exports due to an omission in the `PUBLISHED_COLUMN_ORDER` list in `scripts/process/export_dataset.py`. This release restores schema parity with the Open Data portal.

**Fields (17):**
1. record_id
2. name
3. name_alphabetized
4. operational_status
5. organization_type
6. url
7. alternate_or_former_names
8. acronym
9. alternate_or_former_acronyms
10. principal_officer_full_name
11. principal_officer_first_name
12. principal_officer_last_name
13. principal_officer_title
14. principal_officer_contact_url
15. reports_to
16. in_org_chart
17. listed_in_nyc_gov_agency_directory

---

### v1.6.0 (2024-12-10)

**Changed:**
- Converted all column names from PascalCase to snake_case
- Standardized column ordering

**Fields (16):**
1. record_id
2. name
3. name_alphabetized
4. operational_status
5. organization_type
6. url
7. alternate_or_former_names
8. acronym
9. alternate_or_former_acronyms
10. principal_officer_full_name
11. principal_officer_first_name
12. principal_officer_last_name
13. principal_officer_title
14. principal_officer_contact_url
15. in_org_chart
16. listed_in_nyc_gov_agency_directory

**Note:** `reports_to` was missing from this version (unintentional).

---

## Golden Dataset Schema Changes

### v1.6.0 (2024-12-10)

**Changed:**
- Converted all column names from PascalCase to snake_case
- 38 fields total (internal metadata fields included)

---

## Schema Change Process

When making schema changes:

1. **Update the schema file** (`nycgo_published_dataset.tableschema.json` or `nycgo_golden_dataset.tableschema.json`)
2. **Update the version number** in the schema file
3. **Update this changelog** with:
   - Version number and date
   - Summary of changes (Added/Removed/Changed)
   - Context explaining why the change was made
   - Complete field list for the new version
4. **Update `PUBLISHED_COLUMN_ORDER`** in `scripts/process/export_dataset.py` if changing published schema
5. **Run pipeline validation** to ensure outputs match the new schema
6. **Use minor or major version bump** (not patch) for schema changes
