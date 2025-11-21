# Phase II Schema Proposal: Governance Structure Modeling

## Summary of Proposed Changes

**Retire:** `reports_to` field (removed from schema)

**Add - Governance & Oversight:**
- `governance_structure` (free text) - Describes WHAT type of governance exists (e.g., "NYC Health + Hospitals is governed by a Board of Directors", "Division reports directly to the leadership of Office of Technology and Innovation")
- `org_chart_oversight_record_id` (RecordID format) - Links to overseeing entity via RecordID (e.g., `NYC_GOID_000123`). **Replaces** `reports_to` field for org chart/political oversight relationships
- `org_chart_oversight_name` (text) - Name of the overseeing entity (derived from `org_chart_oversight_record_id`)
- `parent_organization_record_id` (RecordID format) - Links to parent entity via RecordID (e.g., `NYC_GOID_000318`). Used for specialized boards → parent, divisions → parent department, subdivisions → parent
- `parent_organization_name` (text) - Name of the parent entity (derived from `parent_organization_record_id`)

**Add - Legal Authority:**
- `authorizing_authority` (free text) - Legal authority that establishes the organization (e.g., "NYC Charter § 2203", "New York State Public Authorities Law § 1260")
- `authorizing_authority_type` (controlled vocabulary) - Categorizes authority type for queryability (e.g., "NYC Charter", "Mayoral Executive Order", "New York State Law")
- `authorizing_url` (URL) - Link to the legal document or statute (e.g., "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2203")

**Add - Appointments:**
- `appointments_summary` (free text) - Describes HOW appointments/selection works (e.g., "Board of Directors consists of 17 members: 11 appointed by Mayor, 3 by Borough Presidents, 3 by Comptroller. Chief Executive selected by Board.")

## Board Modeling Approach

**Primary Governing Boards** (Board of Directors/Trustees):
- Captured in `governance_structure` and `appointments_summary` fields
- **NOT** separate entity records

**Specialized Boards** (with independent legal authority):
- Get their own entity records
- Linked to parent via `parent_organization_record_id` (RecordID, e.g., `NYC_GOID_000318`)
- Relationship optionally mentioned in parent's `governance_structure`
- **Note:** `parent_organization_record_id` is separate from `org_chart_oversight_record_id` (which is for org chart relationships only)

---

## Edge Cases: Examples by Entity Type

### 1. Entity with Board of Directors (MTA)

| Field | Value |
|------|-------|
| `name` | Metropolitan Transportation Authority |
| `organization_type` | Public Benefit or Development Organization |
| `governance_structure` | Metropolitan Transportation Authority is governed by a Board of Directors. |
| `appointments_summary` | Board of Directors consists of members appointed by Governor, Mayor, and other officials. Chair and CEO appointed by Governor. |
| `org_chart_oversight_record_id` | *(empty - not in Mayor's org chart)* |
| `org_chart_oversight_name` | *(empty)* |
| `authorizing_authority` | New York State Public Authorities Law § 1260 |
| `authorizing_authority_type` | New York State Law |

**Note:** Board of Directors is described in narrative fields, not a separate entity.

---

### 2. Division (NYC311)

| Field | Value |
|------|-------|
| `name` | NYC311 |
| `organization_type` | Division |
| `governance_structure` | Division reports directly to the leadership of Office of Technology and Innovation. |
| `appointments_summary` | Deputy Commissioner appointed by Commissioner of Office of Technology and Innovation. |
| `parent_organization_record_id` | NYC_GOID_000382 |
| `parent_organization_name` | Office of Technology and Innovation |
| `org_chart_oversight_record_id` | NYC_GOID_000382 |
| `org_chart_oversight_name` | Office of Technology and Innovation |
| `authorizing_authority` | NYC Charter § 1301 |
| `authorizing_authority_type` | NYC Charter |

**Note:** Divisions describe their reporting relationship in `governance_structure` and link to parent via `parent_organization`.

---

### 3. Non-profit Organization (Brooklyn Public Library)

| Field | Value |
|------|-------|
| `name` | Brooklyn Public Library |
| `organization_type` | Nonprofit Organization |
| `governance_structure` | Brooklyn Public Library is governed by a Board of Trustees. |
| `appointments_summary` | Board of Trustees consists of members appointed by Mayor and Brooklyn Borough President. President and CEO selected by Board. |
| `org_chart_oversight_record_id` | *(empty - not in Mayor's org chart)* |
| `org_chart_oversight_name` | *(empty)* |
| `authorizing_authority` | New York State Education Law § 260 |
| `authorizing_authority_type` | New York State Law |

**Note:** Board of Trustees described in narrative, not a separate entity.

---

### 4. Entity with Board of Directors + Separate Associated Board (NYC Health + Hospitals)

#### Parent Entity: NYC Health + Hospitals

| Field | Value |
|------|-------|
| `name` | NYC Health + Hospitals |
| `organization_type` | Public Benefit or Development Organization |
| `governance_structure` | NYC Health + Hospitals is governed by a Board of Directors. Also has a Personnel Review Board (see NYC_GOID_000212) for personnel matters. |
| `appointments_summary` | Board of Directors consists of 17 members: 11 appointed by Mayor, 3 by Borough Presidents, 3 by Comptroller. Chief Executive selected by Board. |
| `org_chart_oversight_record_id` | *(RecordID of overseeing entity from org chart)* |
| `org_chart_oversight_name` | *(name derived from RecordID)* |
| `authorizing_authority` | NYC Charter § 2203; Health and Hospitals Corporation Act of 1969 |
| `authorizing_authority_type` | NYC Charter |

#### Specialized Board: Personnel Review Board

| Field | Value |
|------|-------|
| `name` | Health and Hospitals Corporation Personnel Review Board |
| `organization_type` | Advisory or Regulatory Organization |
| `governance_structure` | Personnel Review Board for NYC Health + Hospitals; reviews personnel matters for H+H system. |
| `appointments_summary` | Personnel Review Board members appointed by Board of Directors of NYC Health + Hospitals. |
| `parent_organization_record_id` | NYC_GOID_000318 |
| `parent_organization_name` | NYC Health + Hospitals |
| `org_chart_oversight_record_id` | *(empty - not in Mayor's org chart)* |
| `org_chart_oversight_name` | *(empty)* |
| `authorizing_authority` | NYC Charter § 2203 |
| `authorizing_authority_type` | NYC Charter |

**Note:**
- Primary Board of Directors → described in parent's `governance_structure` and `appointments_summary`
- Specialized Personnel Review Board → separate entity record linked via `parent_organization_record_id` (RecordID)

---

## Key Benefits

1. **Clear separation:** Governance structure (WHAT) vs. appointment process (HOW)
2. **No schema bloat:** Primary boards don't create separate records
3. **Queryable relationships:** Can filter for specialized boards, divisions, and subdivisions via `parent_organization_record_id`
4. **Usability:** Both RecordID and name fields provided for `org_chart_oversight` and `parent_organization` (name derived from RecordID)
5. **Referential integrity:** Both `org_chart_oversight_record_id` and `parent_organization_record_id` use RecordID format
6. **Distinct purposes:** `org_chart_oversight_record_id` (org chart placement) vs. `parent_organization_record_id` (governance relationship)
7. **Flexible:** Can iteratively enhance parent entities to mention specialized boards

---

## Field Definitions

**`governance_structure`** (free text)
- Describes WHAT type of governance mechanism exists
- Examples: "Entity is governed by a Board of Directors", "Division reports directly to Department leadership"

**`appointments_summary`** (free text)
- Describes HOW appointments/selection works
- Examples: "Board consists of 17 members: 11 appointed by Mayor...", "Chief Executive selected by Board"

**`org_chart_oversight_record_id`** (RecordID)
- Links to overseeing entity using RecordID format (e.g., `NYC_GOID_000123`)
- Used for: org chart/political oversight relationships only (what appears in Mayor's org chart)

**`org_chart_oversight_name`** (text)
- Name of the overseeing entity (derived from `org_chart_oversight_record_id`)
- Automatically populated from RecordID lookup

**`parent_organization_record_id`** (RecordID)
- Links to parent entity using RecordID format (e.g., `NYC_GOID_000318`)
- Used for: specialized boards → parent, divisions → parent department, subdivisions → parent
- Separate from `org_chart_oversight_record_id` (governance relationship vs. org chart placement)

**`parent_organization_name`** (text)
- Name of the parent entity (derived from `parent_organization_record_id`)
- Automatically populated from RecordID lookup

**`authorizing_authority`** (free text)
- Legal authority that establishes the organization (statute, charter provision, executive order, or local law)
- Examples: "NYC Charter § 2203", "New York State Public Authorities Law § 1260", "Mayoral Executive Order 18 of 2025"

**`authorizing_authority_type`** (controlled vocabulary)
- Categorizes authority type for queryability
- Values: "NYC Charter", "Mayoral Executive Order", "NYC Local Law", "New York State Law", etc.

**`authorizing_url`** (URL)
- Link to the legal document or statute that authorizes the organization
- Examples: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2203"
- Must be official government sources (NYC.gov, State Legislature, etc.)
