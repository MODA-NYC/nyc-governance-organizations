# Phase II Data Release

**Status: PAUSED - Resuming after Sprint 7**
**Last Updated: January 2026**

This document tracks the Phase II schema expansion and data population work for the NYC Governance Organizations dataset. Phase II adds governance and legal authority fields to better capture organizational relationships.

> **Archived Documentation**: Detailed technical specs from the original planning phase are archived in `docs/sprints/phase-ii-archive/`:
> - `PHASE_II_SCHEMA.md` - Original schema documentation
> - `PHASE_II_PROGRESS.md` - November 2024 progress tracking
> - `SCHEMA_VERSION_COMPARISON.md` - Phase I vs Phase II field comparison

---

## Overview

**Current Production**: v1.7.x (38 golden fields, 16 public export fields, 436 records)
**Target Release**: v2.0.0 (42 golden fields, 20 public export fields)

### Schema Changes (v1.7.x → v2.0.0)

**New Fields (4 additions + 1 type field = 5 total)**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `org_chart_oversight` | String | No | Administrative oversight from Mayor's org charts |
| `authorizing_authority` | String | **Yes (100%)** | Legal authority citation (Charter, Local Law, EO, etc.) |
| `authorizing_authority_type` | Enum | Recommended | Type of legal authority (controlled vocabulary) |
| `authorizing_url` | URL | 90%+ target | Link to authorizing legal document |
| `appointments_summary` | Text | For MOA entities | How leadership is appointed |

**Breaking Change**: `ReportsTo` field semantics narrowed from "org chart + political oversight" to "legal/Charter-defined reporting only". Org chart relationships move to `org_chart_oversight`.

---

## Completed Work

### Phase II.0: Infrastructure Setup (100% Complete)

Completed November 2024. MCP servers and research skills configured.

- civic-ai-tools integration (opengov-mcp-server, playwright-civic)
- Research skills for MOA protocol and legal citations
- Development environment ready for data collection

### Phase II.1: Schema Expansion (100% Complete)

Completed November 2024. Schema modified in development dataset.

- Development file: `data/working/NYCGO_golden_dataset_v2.0.0-dev.csv` (42 fields, 433 records)
- Validation rules added to `src/nycgo_pipeline/global_rules.py`
- Export functionality updated in `scripts/process/export_dataset.py`

**Schema Status**: Dev file ready, but data population work never started.

---

## Remaining Work

### Phase II.2: Data Population (NOT STARTED)

This is the main work remaining. Research and populate the 5 new fields for all ~436 entities.

#### Tasks:

1. **Research `authorizing_authority` (100% population required)**
   - Review NYC Charter, Admin Code, Local Laws, Executive Orders
   - Document legal basis using standard citation format
   - Example: "NYC Charter § 1301" (Department of City Planning)

2. **Find `authorizing_url` (90%+ target)**
   - Locate official source documents
   - Prefer stable NYC.gov/codelibrary.amlegal.com URLs
   - Verify links are accessible

3. **Populate `authorizing_authority_type`**
   - Categorize using controlled vocabulary (see below)
   - Must align with `authorizing_authority` field

4. **Extract `org_chart_oversight`**
   - Review current Mayor's organizational charts
   - Map administrative oversight relationships
   - Use RecordIDs from dataset

5. **Document `appointments_summary`**
   - Scrape Mayor's Office of Appointments page
   - Research Charter provisions for appointment mechanisms
   - Focus on entities with mayoral appointments

### Phase II.3: ReportsTo Audit (NOT STARTED)

Audit and correct `ReportsTo` values to match new strict definition.

- Review all 436 values
- Move org chart relationships to `org_chart_oversight`
- Verify against NYC Charter/enabling legislation
- May result in many records changing

### Phase II.4: QA & Validation (NOT STARTED)

- Full dataset validation against Phase II rules
- Cross-check new fields for accuracy
- Verify all URLs accessible
- Test pipeline with expanded schema

### Phase II.5: Release (NOT STARTED)

- Generate v2.0.0 release files
- Update documentation
- Publish to NYC Open Data
- Create migration guide for v1.x users

---

## Field Definitions

### `org_chart_oversight`

**Type:** String (RecordID reference)
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

---

### `authorizing_authority`

**Type:** String
**Required:** **YES (100% population target)**
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

**Citation Guidance:**
- Prefer codified citations (Charter/Admin Code) over Local Law numbers
- Include Local Law only when no codified citation exists
- Multiple authorities: separate with semicolons

---

### `authorizing_authority_type`

**Type:** String (Controlled Vocabulary)
**Required:** Recommended when `authorizing_authority` is populated
**Default:** Empty string

**Definition:**
Categorizes the type of legal authority that establishes the organization.

**Controlled Vocabulary (EXACT VALUES ONLY):**

| Value | Use When |
|-------|----------|
| `NYC Charter` | Entity established by NYC Charter provision |
| `NYC Administrative Code` | Entity established by NYC Admin Code section |
| `City Council Local Law` | Entity established by Local Law (not codified) |
| `Mayoral Executive Order` | Entity established by EO (not codified) |
| `New York State Law` | Entity established by NYS statute |
| `Federal Law` | Entity established by federal statute |
| `Other` | Other legal authority (use sparingly) |

**Critical Rules:**
- Single value only (no semicolons)
- Prefer codified citations (Charter/Admin Code over Local Law/EO when codified)
- Must match `authorizing_authority` field

**Selection Priority:**
1. If codified in Charter → use "NYC Charter"
2. If codified in Admin Code → use "NYC Administrative Code"
3. If only in Local Law (not codified) → use "City Council Local Law"
4. If only in Executive Order (not codified) → use "Mayoral Executive Order"

---

### `authorizing_url`

**Type:** String (URL)
**Required:** No (90%+ population target)
**Default:** Empty string

**Definition:**
Direct URL link to the official legal document, statute, or charter provision that establishes the organization's legal authority.

**Critical Rule: Exactly ONE URL per row**

Use only the canonical URL representing the primary legal authority.

**URL Selection Priority:**
1. Charter or Administrative Code section (preferred - most stable)
2. State law URL (if authority is state law only)
3. Local Law URL (only if no codified citation)
4. Executive Order URL (only if no codified citation)

**Examples:**
- `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-1301`
- `https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/2014/eo_16.pdf`

**Quality Standards:**
- Must be valid URL format (https://...)
- Should return 200 OK when checked
- Prefer stable/permalink URLs
- Must be from official government source

---

### `appointments_summary`

**Type:** String (Free text)
**Required:** For entities with mayoral appointments
**Default:** Empty string

**Definition:**
Brief description of how the organization's leadership and key positions are appointed, including appointing authority, term lengths, and confirmation requirements.

**Important:** Describes the **appointment mechanism/rules** as defined in Charter or enabling legislation, NOT specific appointment events.

**Format:**
Free-text summary, typically 1-3 sentences. Use semicolons to separate multiple appointment types.

**Examples (CORRECT - describing mechanisms):**
- "Commissioner appointed by Mayor; Deputy Commissioners appointed by Commissioner"
- "15-member board: 5 appointed by Mayor, 5 by Public Advocate, 5 by Borough Presidents; 6-year staggered terms"
- "Director appointed by Mayor with City Council approval; 5-year term; may be removed for cause"

**Examples (INCORRECT - describing specific events):**
- "Mayor Adams appointed 26 members in Dec 2022" (specific event)
- "26 members appointed by Mayor" (current composition, not mechanism)

**Key Information to Include:**
- Appointing authority (Mayor, Governor, Board, etc.)
- Term length if applicable
- Confirmation/approval requirements
- Removal conditions
- Board composition if applicable

---

## Research Sources

| Field | Primary Sources |
|-------|----------------|
| `authorizing_authority` | NYC Charter (codelibrary.amlegal.com), NYC Admin Code, Local Laws, Executive Orders archive |
| `authorizing_url` | Same as above, prefer permalinks |
| `authorizing_authority_type` | Derived from `authorizing_authority` |
| `appointments_summary` | Mayor's Office of Appointments (nyc.gov/appointments), NYC Charter |
| `org_chart_oversight` | Mayor's Office organizational charts, City Hall documentation |

---

## Breaking Changes Summary (v1.x → v2.0.0)

### ReportsTo Semantics Changed

**v1.x Definition:** Conflated org chart placement, political oversight, AND legal reporting
**v2.0.0 Definition:** STRICTLY legal/Charter-defined reporting only

| What | v1.x | v2.0.0 |
|------|------|--------|
| Legal/Charter reporting | In `ReportsTo` | In `ReportsTo` |
| Org chart placement | In `ReportsTo` | In `org_chart_oversight` |
| Political oversight | In `ReportsTo` | In `org_chart_oversight` |

**Migration Impact:**
- Many `ReportsTo` values will change
- Previous org chart values move to `org_chart_oversight`
- Users must update queries relying on old `ReportsTo` semantics

### New Fields Added (5 total)
- `org_chart_oversight` - Administrative oversight
- `authorizing_authority` - Legal basis (required)
- `authorizing_authority_type` - Authority classification
- `authorizing_url` - Source document link
- `appointments_summary` - Appointment mechanisms

### Schema Impact
- Golden dataset: 38 → 42 fields (+4, +1 type field already existed)
- Public export: 16 → 20 fields (+4)
- Record count: ~436 (may increase if new orgs discovered)

---

## Data Population Targets

| Field | Target | Notes |
|-------|--------|-------|
| `authorizing_authority` | 100% | Required for all entities |
| `authorizing_url` | 90%+ | Some older EOs may lack URLs |
| `authorizing_authority_type` | 100% | Derived from authority field |
| `org_chart_oversight` | 80%+ | Only entities in org charts |
| `appointments_summary` | MOA entities | ~50-100 entities with mayoral appointments |
| `ReportsTo` (audit) | 100% | Correct to new definition |

---

## Definition of Done

- [ ] Phase II.2: All new fields populated to target levels
- [ ] Phase II.3: ReportsTo audit complete, values corrected
- [ ] Phase II.4: Full validation passing, all URLs verified
- [ ] Phase II.5: v2.0.0 published with migration guide
- [ ] Documentation updated (README, data dictionary)
- [ ] NYC Open Data portal updated

---

## Timeline

Phase II work resumes after Sprint 7 cleanup items are complete. No specific dates set - prioritize based on:
1. User/stakeholder demand for governance fields
2. Available research time
3. Other project priorities

---

## Version History

- **November 2024**: Phase II.0 & II.1 completed (infrastructure + schema expansion)
- **December 2024**: Phase II deferred, focus shifted to Sprint 5-7
- **January 2026**: Documentation consolidated, ready to resume after Sprint 7
