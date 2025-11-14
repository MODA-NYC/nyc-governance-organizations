# Phase II Schema Documentation (v2.0.0)

## Overview

Phase II introduces **4 new fields** and **redefines 1 existing field** to better capture organizational relationships, legal authority structures, and appointment mechanisms for NYC government entities.

## Version: v2.0.0 (Breaking Change)

This is a **BREAKING CHANGE** because the `ReportsTo` field's semantics have changed significantly. Organizations relying on v1.0.0 must review their use of this field.

---

## New Fields

### 1. `org_chart_oversight` (NEW)
**Type:** String
**Required:** No
**Default:** Empty string

**Definition:**
The organization shown as the parent/supervisor on the official Mayor's office organizational charts for administrative oversight purposes, even if there is no formal legal reporting relationship.

**Purpose:**
Distinguishes political/administrative oversight from legal reporting relationships. Many entities appear under specific offices in org charts for coordination purposes without formal legal subordination.

**Examples:**
- Department of City Planning → appears under Deputy Mayor for Strategic Initiatives
- NYC Health + Hospitals → appears under First Deputy Mayor
- Independent Budget Office → appears in chart but reports to Mayor and Council

**Validation Rules:**
- Must match a valid RecordID from the dataset if populated
- May differ from `ReportsTo` field
- Should align with current Mayor's org chart

**Research Sources:**
- Official NYC Mayor's Office organizational charts
- City of New York Organization Charts (published documents)
- Mayor's Office website

---

### 2. `authorizing_authority` (NEW)
**Type:** String
**Required:** **YES** (100% population target)
**Default:** Empty string

**Definition:**
The legal authority (statute, charter provision, executive order, or local law) that established or authorizes the organization to exist and operate.

**Purpose:**
Documents the legal foundation for each entity's existence and authority. Critical for understanding jurisdictional boundaries, statutory mandates, and legal basis for operations.

**Format:**
- NYC Charter § [section number]
- NYC Administrative Code § [section]
- Executive Order [number] ([year])
- Local Law [number] of [year]
- NYS [statute citation]
- Multiple sources separated by semicolons

**Examples:**
- "NYC Charter § 1301" (Department of City Planning)
- "NYC Charter § 2203; Health and Hospitals Corporation Act of 1969" (NYC Health + Hospitals)
- "NYC Charter § 259; Local Law 128 of 2013" (Independent Budget Office)
- "Executive Order 16 (2014)" (Office of Immigrant Affairs)

**Validation Rules:**
- Required for ALL entities (100% population)
- Must use standard citation format
- Multiple authorities separated by semicolons
- Cross-reference with `authorizing_url` when available

**Research Sources:**
- NYC Charter (nyc.gov/charter)
- NYC Administrative Code
- NYC Local Laws database
- Executive Orders archive
- NYS Consolidated Laws

---

### 3. `authorizing_url` (NEW)
**Type:** String (URL)
**Required:** No (90%+ population target)
**Default:** Empty string

**Definition:**
Direct URL link to the official legal document, statute, or charter provision that establishes the organization's legal authority.

**Purpose:**
Provides immediate access to source documents for verification and research. Enhances transparency and auditability of the dataset.

**Format:**
- Must be valid HTTP/HTTPS URL
- Prefer official NYC.gov, State of NY, or government sources
- Use permalinks when available
- Pipe-separated (|) for multiple sources

**Examples:**
- "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-1301"
- "https://www.nyc.gov/site/doh/about/about-hh.page"
- "https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/2014/eo_16.pdf"

**Validation Rules:**
- Must be valid URL format (https?://...)
- Should return 200 OK status when checked
- Prefer stable/permalink URLs over dynamic pages
- 90%+ population target

**Quality Standards:**
- ✅ GOOD: Direct link to statute/charter/EO text
- ⚠️ ACCEPTABLE: Agency "About" page citing authority
- ❌ AVOID: Wikipedia, non-official sources

**Research Sources:**
- NYC Charter online (codelibrary.amlegal.com)
- NYC.gov agency pages
- NYC Laws & Rules portal
- Executive Orders archive
- NYS Legislature website

---

### 4. `appointments_summary` (NEW)
**Type:** String (Free text)
**Required:** No
**Default:** Empty string

**Definition:**
Brief description of how the organization's leadership and key positions are appointed, including appointing authority, term lengths, and confirmation requirements.

**Purpose:**
Documents appointment mechanisms to understand political accountability, tenure security, and governance structure. Critical for analyzing mayoral control vs. independence.

**Format:**
Free-text summary, typically 1-3 sentences. Use semicolons to separate multiple appointment types.

**Examples:**
- "Commissioner appointed by Mayor; Deputy Commissioners appointed by Commissioner"
- "15-member board: 5 appointed by Mayor, 5 by Public Advocate, 5 by Borough Presidents; 6-year staggered terms"
- "Director appointed by Mayor with City Council approval; 5-year term; may be removed for cause"
- "President appointed by Board of Directors; Board members appointed by Mayor"

**Key Information to Include:**
- Appointing authority (Mayor, Governor, Board, etc.)
- Term length if applicable
- Confirmation/approval requirements
- Removal conditions
- Board composition if applicable

**Validation Rules:**
- Required for entities with mayoral appointments
- Should align with Mayor's Office of Appointments data
- Cross-reference with NYC Charter/enabling legislation

**Research Sources:**
- Mayor's Office of Appointments (nyc.gov/appointments)
- NYC Charter provisions
- Agency enabling legislation
- Board bylaws and governance documents

---

## Redefined Field

### `ReportsTo` (REDEFINED - BREAKING CHANGE)

**Original Definition (v1.0.0):**
Conflated legal reporting relationships with political oversight and organizational chart placement.

**New Definition (v2.0.0):**
**STRICTLY** the legal or managerial direct reporting relationship as defined by statute, charter, or formal organizational structure. Does NOT include political oversight or org chart placement.

**What Changed:**
In v1.0.0, this field included:
- ✅ Legal reporting (Charter-defined)
- ✅ Org chart placement
- ✅ Political oversight

In v2.0.0, this field includes ONLY:
- ✅ Legal/Charter-defined reporting
- ✅ Direct managerial reporting
- ❌ Org chart placement → **NOW in `org_chart_oversight`**
- ❌ Political oversight → **NOW in `org_chart_oversight`**

**Examples of Changes:**
| Entity | v1.0.0 ReportsTo | v2.0.0 ReportsTo | v2.0.0 org_chart_oversight |
|--------|------------------|------------------|----------------------------|
| Dept of City Planning | Deputy Mayor for Strategic Initiatives | Mayor | Deputy Mayor for Strategic Initiatives |
| NYC Health + Hospitals | First Deputy Mayor | Independent (Board-governed) | First Deputy Mayor |
| Independent Budget Office | Mayor | Mayor and City Council | Mayor |

**Validation Rules:**
- Must match a valid RecordID from dataset
- Should be verifiable in NYC Charter or enabling legislation
- Should align with `authorizing_authority` documentation
- May be "Independent" or "Board-governed" for autonomous entities

**Migration Impact:**
- Existing `ReportsTo` values will be reviewed and potentially changed
- Previous values that reflected org chart placement only will be moved to `org_chart_oversight`
- This is why v2.0.0 is a breaking change

---

## Implementation Status

### Schema Modification
- ✅ 4 new columns added to dataset
- ✅ Schema expanded from 38 to 42 fields
- ✅ All 433 entities preserved
- ✅ Default empty values set for new fields

### Data Population Status
| Field | Population Target | Current Status |
|-------|-------------------|----------------|
| `org_chart_oversight` | 80%+ | 0% (to be researched) |
| `authorizing_authority` | 100% | 0% (to be researched) |
| `authorizing_url` | 90%+ | 0% (to be researched) |
| `appointments_summary` | Entities with mayoral appointments | 0% (to be researched) |
| `ReportsTo` (redefined) | 100% | 100% (needs audit & correction) |

### Next Steps
1. **Phase II.2**: Research and populate `authorizing_authority` for all 433 entities
2. **Phase II.2**: Find and validate `authorizing_url` for 90%+ entities
3. **Phase II.2**: Scrape Mayor's Office of Appointments page for `appointments_summary`
4. **Phase II.2**: Extract `org_chart_oversight` from official org charts
5. **Phase II.4**: Audit and correct `ReportsTo` values to match new definition

---

## Data Quality Standards

### authorizing_authority
- **Required:** YES
- **Quality Check:** Cross-reference with NYC Charter and Administrative Code
- **Validation:** Must cite specific statute/charter section or EO number

### authorizing_url
- **Required:** No, but 90%+ target
- **Quality Check:** URL must be accessible (200 OK)
- **Validation:** Must be from official government source

### appointments_summary
- **Required:** For entities with mayoral appointments
- **Quality Check:** Must align with Charter provisions and MOA data
- **Validation:** Verify against official appointment records

### org_chart_oversight
- **Required:** No
- **Quality Check:** Must match current published org chart
- **Validation:** RecordID must exist in dataset

### ReportsTo (redefined)
- **Required:** YES
- **Quality Check:** Must be verifiable in legal documents
- **Validation:** Must match new strict definition (legal reporting only)

---

## Breaking Changes Summary (v1.0.0 → v2.0.0)

### Field Semantics Changed
- **ReportsTo**: Narrowed from "org chart + political oversight" to "legal reporting only"

### New Fields Added
- **org_chart_oversight**: Administrative oversight from org charts
- **authorizing_authority**: Legal basis for entity's existence
- **authorizing_url**: Link to authorizing legal documents
- **appointments_summary**: How leadership is appointed

### Schema Impact
- Column count: 38 → 42 (+4 fields)
- Record count: 433 (unchanged)
- Data semantics: Changed (breaking)

### Migration Guidance
Users of v1.0.0 should:
1. Review all uses of `ReportsTo` field
2. Update queries to use `org_chart_oversight` for org chart relationships
3. Verify legal reporting relationships using `authorizing_authority`
4. Update any assumptions about political oversight chains

---

## Version History

- **v1.0.0** (October 7, 2024): Initial stable release with 38 fields, 433 entities
- **v2.0.0-dev** (November 14, 2024): Phase II schema expansion
  - Added 4 new fields
  - Redefined ReportsTo (breaking change)
  - Schema modification complete
  - Data population: In progress

---

## References

- **Phase II Plan**: `/docs/PHASE_II_PLAN.md`
- **Skills**: `/skills/nyc-governance-schema/skill.md`
- **NYC Charter**: https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter
- **Mayor's Office of Appointments**: https://www.nyc.gov/content/appointments/pages/boards-commissions

---

**Last Updated:** November 14, 2024
**Status:** Schema modification complete; data population in progress
**Target Release:** v2.0.0
