# Governance Structure Modeling Experiment

## Overview

This workspace explores different approaches to modeling governance structures (particularly boards) in the NYC Governance Organizations dataset. The experiment focuses on entities with Board of Directors/Trustees and edge cases with multiple boards.

## Schema Format (v2.0.0 - Updated)

All example CSV files use the **published dataset schema** with snake_case field names:

**Core Fields:**
- `record_id`, `name`, `name_alphabetized`, `operational_status`, `organization_type`, `url`
- `alternate_or_former_names`, `acronym`, `alternate_or_former_acronyms`
- `principal_officer_full_name`, `principal_officer_first_name`, `principal_officer_last_name`, `principal_officer_title`, `principal_officer_contact_url`
- `in_org_chart` (boolean), `listed_in_nyc_gov_agency_directory`

**Phase II Fields:**
- `org_chart_oversight` (RecordID format, e.g., `NYC_GOID_000123`)
- `authorizing_authority` (free text)
- `authorizing_authority_type` (controlled vocabulary: "NYC Charter", "Mayoral Executive Order", "NYC Local Law", "New York State Law", etc.)
- `authorizing_url` (URL)
- `appointments_summary` (free text - describes HOW appointments work)
- `governance_structure` (free text - describes WHAT type of governance)

**Schema Changes:**
- ❌ `reports_to` field **retired** (removed from schema)
- ✅ `governance_structure` added (free text field describing governance structure)
- ✅ `org_chart_oversight` uses RecordID format instead of entity name
- ✅ `authorizing_authority_type` added for queryability

**Field Separation:**
- `governance_structure`: Structural description (e.g., "NYC Health + Hospitals is governed by a Board of Directors")
- `appointments_summary`: Process description (e.g., "Board consists of 17 members: 11 appointed by Mayor, 3 by Borough Presidents. Chief Executive selected by Board.")

## Board Modeling Solution

- **Primary governing boards** (BoD/Trustees): Captured in `governance_structure` field, NOT separate entities
- **Specialized boards**: Get their own entity records; relationship captured in `governance_structure` (optional mention in parent entity's `governance_structure` for iterative enhancement)

## Files

- `entity_list.csv` - List of 20-30 entities with board structures
- `examples/approach_a_narrative_only.csv` - Boards in `governance_structure`/`appointments_summary` only
- `examples/approach_b_separate_entities.csv` - Boards as separate entity records
- `examples/approach_c_mixed.csv` - Mixed approach (primary boards = narrative, specialized = separate)
- `edge_cases/` - Detailed examples for complex multi-board entities
- `analysis/comparison_notes.md` - Analysis of approaches
