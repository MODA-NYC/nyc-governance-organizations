# Schema Decisions: Modeling Governance vs Authority

## Summary of Issue

Phase II.2 crosswalk review revealed tension between **legal authority** (what authorizes an entity to exist) and **governance structure** (what board/body runs it). The Phase II schema captures legal authority via `authorizing_authority` and `authorizing_url`, but doesn't explicitly capture governance mechanisms. Key question: **How should we model entities with multiple boards** (e.g., NYC Health + Hospitals has both a Board of Directors and a Personnel Review Board)?

## Decision Framework: When to Create Separate Entity Records

We need a consistent rule for when boards warrant separate entity records vs being described within the parent entity. **Proposed rule:** Create separate records for **specialized/functional boards with independent legal authority** (Personnel Review Boards, Audit Committees with statutory powers); capture **primary governing boards** (Boards of Directors/Trustees that exist solely to govern the parent) within the parent entity's existing fields (`Description`, `Notes`, `appointments_summary`). Link specialized boards to parents using `org_chart_oversight`. This approach **avoids schema bloat** while maintaining the critical distinction between an entity's legal basis (`authorizing_authority` = Charter/law that creates the entity) and its governance mechanism (described in narrative fields).

## Open Questions for Discussion

1. **Schema additions:** Should we add new fields to capture board structure (e.g., `primary_governing_board`, `governing_board_composition`) or rely on narrative in the existing `appointments_summary` field? The former would make board information more structured/queryable but increases the published schema from 21 fields (v2.0.0 with Phase II additions) to 23+ fields; the latter keeps the schema stable but makes board composition harder to extract programmatically.

2. **Consistency rule:** Do we apply the "specialized boards = separate records" rule retrospectively to existing entities (e.g., should MTA Board of Directors remain implicit or become explicit)? This affects ~20-30 entities with known board structures.

3. **MOA appointments page alignment:** MOA lists "Board of Directors" entities as separate appointment bodies. Should our model prioritize structural accuracy (boards as entity attributes) or appointment workflow (boards as separate entities for appointment tracking)? If we create separate board entity records to match MOA's appointment-tracking needs, we would need a way to indicate the board-to-parent relationship—either using the existing `InstanceOf` field or adding a new field like `FunctionalType` to distinguish governing boards from operating entities.
