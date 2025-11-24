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

**Multiple Authorities:**
When an entity has multiple authorizing authorities, separate them with semicolons (`;`). Example: `"NYC Charter § 738; NYS L.1969, c.1016 (\"Health and Hospitals Corporation Act\")"`

**Local Law Citation Guidance:**
- **Generally**: Prefer codified citations (Charter/Admin Code) over Local Law numbers
- **Include Local Law**: Only when no codified citation exists, or entity is defined by Local Law itself (temporary task forces)
- **Avoid**: Including Local Law citations when Charter/Admin Code citation already exists
- **Rationale**: Most users need the codified hook; Local Law inclusion creates consistency challenges; can add `authorizing_local_law` field later if needed

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

**CRITICAL RULE: Exactly ONE URL per row**

The `authorizing_url` field contains exactly one canonical URL representing the primary legal authority. This keeps the field simple and maintainable.

**URL Selection Priority:**
1. Charter or Administrative Code section (if available) - preferred as most stable
2. State law URL (if authority is state law only, no Charter/Admin Code)
3. Local Law URL (only if no codified citation exists)
4. Executive Order URL (only if no codified citation exists)

**Multiple Authorities Handling:**
- If `authorizing_authority` contains multiple citations (semicolon-separated), use only the canonical URL (prefer Charter/Admin Code)
- Do NOT use pipe-separated URLs (`|`) - keep to single URL
- If multiple URLs are needed later, consider a separate `nycgo_authorities` table rather than overloading this field

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

### 3.5. `authorizing_authority_type` (NEW)
**Type:** String (Controlled Vocabulary)
**Required:** No (recommended when `authorizing_authority` is populated)
**Default:** Empty string

**Definition:**
Categorizes the type of legal authority that establishes the organization, enabling filtering and querying by authority source.

**Purpose:**
Provides a standardized way to categorize and filter entities by their legal authority type. Complements the `authorizing_authority` field with a structured classification.

**Controlled Vocabulary (EXACT VALUES ONLY):**
The `authorizing_authority_type` field uses a controlled vocabulary. **Only the following values are allowed:**

1. **"NYC Charter"** - Entity established by NYC Charter provision
2. **"NYC Administrative Code"** - Entity established by NYC Administrative Code section
3. **"City Council Local Law"** - Entity established by City Council Local Law (use only when no codified citation exists)
4. **"Mayoral Executive Order"** - Entity established by Mayoral Executive Order (use only when no codified citation exists)
5. **"New York State Law"** - Entity established by New York State statute
6. **"Federal Law"** - Entity established by federal statute
7. **"Other"** - Other legal authority not covered above (use sparingly)

**CRITICAL RULES:**
- **Single value only** - Do NOT use semicolon-separated values (e.g., "NYC Local Law; NYC Charter" is INVALID)
- **Prefer codified citations** - If entity is codified into Charter/Admin Code, use that type even if originally established by Local Law
- **Must match `authorizing_authority` field** - The type should correspond to the primary authority cited in `authorizing_authority`

**Selection Priority:**
1. If entity is codified in Charter → use "NYC Charter"
2. If entity is codified in Admin Code → use "NYC Administrative Code"
3. If entity is only in Local Law (not codified) → use "City Council Local Law"
4. If entity is only in Executive Order (not codified) → use "Mayoral Executive Order"
5. If entity is established by State law → use "New York State Law"
6. If entity is established by Federal law → use "Federal Law"

**Examples:**
- `authorizing_authority`: "NYC Charter § 1524-a" → `authorizing_authority_type`: "NYC Charter"
- `authorizing_authority`: "NYC Admin. Code § 21-101" → `authorizing_authority_type`: "NYC Administrative Code"
- `authorizing_authority`: "Local Law 38 of 2012" (not codified) → `authorizing_authority_type`: "City Council Local Law"
- `authorizing_authority`: "Executive Order 16 (2014)" (not codified) → `authorizing_authority_type`: "Mayoral Executive Order"
- `authorizing_authority`: "NYC Charter § 738; NYS L.1969, c.1016" → `authorizing_authority_type`: "NYC Charter" (prefer Charter)

**❌ INVALID Examples:**
- "NYC Local Law; NYC Charter" (multiple values - use single value, prefer Charter)
- "Local Law" (not in controlled vocabulary - use "City Council Local Law")
- "NYC Local Law" (not in controlled vocabulary - use "City Council Local Law")
- "Executive Order" (not in controlled vocabulary - use "Mayoral Executive Order")

**Validation Rules:**
- Must be one of the controlled vocabulary values listed above
- Must align with `authorizing_authority` field
- Should prefer codified citations (Charter/Admin Code) over Local Law/Executive Order when codified

**Research Sources:**
- Same as `authorizing_authority` field
- Cross-reference with `authorizing_authority` to ensure consistency

---

### 4. `appointments_summary` (NEW)
**Type:** String (Free text)
**Required:** No
**Default:** Empty string

**Definition:**
Brief description of how the organization's leadership and key positions are appointed, including appointing authority, term lengths, and confirmation requirements.

**Purpose:**
Documents appointment mechanisms to understand political accountability, tenure security, and governance structure. Critical for analyzing mayoral control vs. independence.

**Important:** This field describes the **appointment mechanism/rules** as defined in the Charter or enabling legislation, NOT specific appointment events. It should capture the ongoing rules for how appointments work, not who was appointed on a particular date.

**Format:**
Free-text summary, typically 1-3 sentences. Use semicolons to separate multiple appointment types.

**Examples (CORRECT - describing mechanisms):**
- "Commissioner appointed by Mayor; Deputy Commissioners appointed by Commissioner"
- "15-member board: 5 appointed by Mayor, 5 by Public Advocate, 5 by Borough Presidents; 6-year staggered terms"
- "Director appointed by Mayor with City Council approval; 5-year term; may be removed for cause"
- "Members appointed by Mayor, including at minimum representatives from environmental, environmental justice, urban planning, architecture, engineering, coastal protection, construction, critical infrastructure, labor, business, energy, and academic sectors. Also includes Speaker of City Council or designee and Chairperson of Council Committee on Environmental Protection or designee."

**Examples (INCORRECT - describing specific events):**
- ❌ "Mayor Adams appointed 26 members in Dec 2022" (This is a specific appointment event)
- ❌ "26 members appointed by Mayor" (This describes a current composition, not the mechanism)
- ✅ "Members appointed by Mayor, including at minimum representatives from [sectors]" (This describes the mechanism/rules)

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
- **Skills**: `/skills/nyc-governance-schema/SKILL.md`
- **NYC Charter**: https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter
- **Mayor's Office of Appointments**: https://www.nyc.gov/content/appointments/pages/boards-commissions

---

**Last Updated:** November 14, 2024
**Status:** Schema modification complete; data population in progress
**Target Release:** v2.0.0
