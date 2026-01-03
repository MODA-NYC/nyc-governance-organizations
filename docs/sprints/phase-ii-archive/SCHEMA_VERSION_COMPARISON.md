# Schema Version Comparison: Phase I vs Phase II

This document compares Phase I (v1.0.0) and Phase II (v2.0.0-dev and finalized proposal) schemas to help determine which fields to use when creating edits.

## Quick Reference

| Aspect | Phase I (v1.0.0) | Phase II (v2.0.0-dev) | Finalized Phase II (Proposed) |
|--------|------------------|------------------------|-------------------------------|
| **Release Date** | October 7, 2024 | November 14, 2024 | Not yet released |
| **Golden Dataset Fields** | 38 | 42 | 46 |
| **Public Export Fields** | 16 (+ 1 computed) | 20 (+ 1 computed) | 25 (+ 1 computed) |
| **RecordID Format** | `NYC_GOID_XXXXXX` | `NYC_GOID_XXXXXX` | `100318` (6-digit numeric) |
| **Breaking Changes** | None | `ReportsTo` semantics changed | `reports_to` retired |

---

## Field Comparison

### Phase I Fields (v1.0.0) - 38 Golden Dataset Fields

**Core Identity:**
- RecordID, Name, NameAlphabetized, OperationalStatus, OrganizationType

**Descriptive:**
- Description, URL, AlternateOrFormerNames, Acronym, AlternateOrFormerAcronyms, Notes

**Budget & Data:**
- BudgetCode, OpenDatasetsURL, FoundingYear

**Principal Officer:**
- PrincipalOfficerName (legacy), PrincipalOfficerFullName, PrincipalOfficerGivenName, PrincipalOfficerMiddleNameOrInitial, PrincipalOfficerFamilyName, PrincipalOfficerSuffix, PrincipalOfficerTitle, PrincipalOfficerContactURL

**Organizational Relationships:**
- ReportsTo, InOrgChart, ReportingNotes

**Source Tracking (10 fields):**
- InstanceOf, Name - NYC.gov Agency List, Name - NYC.gov Mayor's Office, Name - NYC Open Data Portal, Name - ODA, Name - CPO, Name - WeGov, Name - Greenbook, Name - Checkbook, Name - HOO, Name - Ops, NYC.gov Agency Directory, Jan 2025 Org Chart

### Phase II Fields Added (v2.0.0-dev) - 4 Fields

These fields were added to the dataset but are **NOT part of Phase I schema:**

1. `org_chart_oversight` (String)
   - Administrative oversight from Mayor's org charts
   - **DO NOT USE** in Phase I edits

2. `authorizing_authority` (String)
   - Legal authority that establishes the organization
   - **DO NOT USE** in Phase I edits

3. `authorizing_url` (URL)
   - Link to authorizing legal documents
   - **DO NOT USE** in Phase I edits

4. `appointments_summary` (Text)
   - How leadership is appointed
   - **DO NOT USE** in Phase I edits

### Finalized Phase II Fields (Proposed) - 9 New Fields

**Retired:**
- `reports_to` - Retired, replaced by more specific fields

**Added:**
1. `governance_structure` (free text)
2. `org_chart_oversight_record_id` (RecordID)
3. `org_chart_oversight_name` (text)
4. `parent_organization_record_id` (RecordID)
5. `parent_organization_name` (text)
6. `authorizing_authority` (free text)
7. `authorizing_authority_type` (controlled vocabulary)
8. `authorizing_url` (URL)
9. `appointments_summary` (free text)

---

## Public Export Field Comparison

### Phase I Public Export (16 fields + 1 computed)

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
17. listed_in_nyc_gov_agency_directory (computed)

### Phase II Public Export (v2.0.0-dev) - 20 fields + 1 computed

**Phase I fields (16) + Phase II fields (4):**
- org_chart_oversight
- authorizing_authority
- authorizing_url
- appointments_summary

### Finalized Phase II Public Export (Proposed) - 25 fields + 1 computed

**Phase I fields (15, excluding reports_to) + Phase II fields (9):**
- governance_structure
- org_chart_oversight_record_id
- org_chart_oversight_name
- parent_organization_record_id
- parent_organization_name
- authorizing_authority
- authorizing_authority_type
- authorizing_url
- appointments_summary

---

## Breaking Changes

### Phase I → Phase II (v2.0.0-dev)

**`ReportsTo` Field Semantics Changed:**
- **Phase I:** Captured both org chart oversight AND legal reporting relationships
- **Phase II:** Narrowed to legal reporting relationships only
- **Impact:** Breaking change - users must review all uses of `ReportsTo` field

### Phase II (v2.0.0-dev) → Finalized Phase II

**`reports_to` Field Retired:**
- **Action:** Field removed from schema
- **Replacement:**
  - `org_chart_oversight_record_id` + `org_chart_oversight_name` (for org chart relationships)
  - `parent_organization_record_id` + `parent_organization_name` (for parent-child relationships)
- **Impact:** Breaking change - field no longer exists

---

## Guidance for Creating Edits

### For Phase I Schema Compatibility

**✅ USE these Phase I fields:**
- All 16 Phase I public export fields (see `docs/PHASE_I_SCHEMA_FIELDS.txt`)
- Use snake_case field names (matching public export format)
- RecordID format: `NYC_GOID_XXXXXX`

**❌ DO NOT USE these Phase II fields:**
- `org_chart_oversight`
- `authorizing_authority`
- `authorizing_url`
- `appointments_summary`
- `governance_structure`
- `org_chart_oversight_record_id`
- `org_chart_oversight_name`
- `parent_organization_record_id`
- `parent_organization_name`
- `authorizing_authority_type`

### For Phase II Schema

**✅ USE Phase I fields + Phase II fields:**
- All Phase I fields (except `reports_to` if using finalized Phase II)
- Phase II fields as appropriate

---

## Field Mapping: Internal → Public Export

### Phase I

| Internal (PascalCase) | Public Export (snake_case) |
|----------------------|---------------------------|
| RecordID | record_id |
| Name | name |
| NameAlphabetized | name_alphabetized |
| OperationalStatus | operational_status |
| OrganizationType | organization_type |
| URL | url |
| AlternateOrFormerNames | alternate_or_former_names |
| Acronym | acronym |
| AlternateOrFormerAcronyms | alternate_or_former_acronyms |
| PrincipalOfficerFullName | principal_officer_full_name |
| PrincipalOfficerGivenName | principal_officer_first_name |
| PrincipalOfficerFamilyName | principal_officer_last_name |
| PrincipalOfficerTitle | principal_officer_title |
| PrincipalOfficerContactURL | principal_officer_contact_url |
| ReportsTo | reports_to |
| InOrgChart | in_org_chart |

**Note:** Public export uses snake_case conversion via `to_snake_case()` function in `export_dataset.py`.

---

## Migration Path

### Phase I → Phase II Migration

1. **Review `ReportsTo` usage:**
   - Identify uses for org chart oversight → map to `org_chart_oversight_record_id`
   - Identify uses for legal reporting → keep in `ReportsTo` (Phase II v2.0.0-dev) or remove (finalized Phase II)

2. **Add Phase II fields:**
   - Populate `authorizing_authority` for all entities
   - Add `authorizing_url` where available
   - Document appointment mechanisms in `appointments_summary`

3. **Update RecordID format (finalized Phase II):**
   - Migrate from `NYC_GOID_XXXXXX` to 6-digit numeric format
   - Use crosswalk file for mapping

---

## References

- **Phase I Schema:** `docs/PHASE_I_SCHEMA.md`
- **Phase II Schema:** `docs/PHASE_II_SCHEMA.md`
- **Phase I Fields List:** `docs/PHASE_I_SCHEMA_FIELDS.txt`
- **Phase I Edits Template:** `data/input/templates/phase_i_edits_template.csv`
- **Phase I Fields Reference:** `data/input/templates/PHASE_I_FIELDS_REFERENCE.md`
- **Schema Proposal:** `SCHEMA_PROPOSAL_SUMMARY.md`

---

**Last Updated:** November 21, 2024
**Status:** Reference document for schema version comparison
