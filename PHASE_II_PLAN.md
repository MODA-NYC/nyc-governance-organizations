# NYC Governance Organizations: Phase II Plan
## Schema Expansion & Mayor's Office of Appointments Coverage

This document outlines Phase II of the NYC Governance Organizations project, building on the v1.0.0 release completed in Phase I. Phase II focuses on expanding the data schema and ensuring comprehensive coverage of entities under the Mayor's Office of Appointments.

---

## Background & Context

**Phase I Achievement**: Successfully established the pipeline infrastructure, tooling, and published the first tagged release (v1.0.0) with a stable dataset covering NYC governance organizations.

**Phase II Objective**: Expand the schema to better capture organizational relationships and authority structures, while ensuring comprehensive coverage of all entities in the Mayor's Office of Appointments universe.

---

## Phase II.0 · Infrastructure Setup

**Prerequisites**: Before beginning Phase II implementation, establish MCP server and Claude Skills infrastructure to enhance efficiency and consistency throughout the project.

**References**:
- **Community Infrastructure**: [`../civic-ai-tools/CIVIC_AI_TOOLS_SETUP.md`](../civic-ai-tools/CIVIC_AI_TOOLS_SETUP.md)
- **NYC-Specific Setup**: [`MCP_SKILLS_SETUP_PLAN.md`](MCP_SKILLS_SETUP_PLAN.md)

### Infrastructure Components
- **Community Tools**: General-purpose MCP servers and skills from `civic-ai-tools` repository
- **Project-Specific Tools**: NYC Governance Schema, MOA Research Protocol, NYC Legal Citation skills
- **Existing Assets**: Your OpenGov MCP server for Socrata/NYC Open Data access
- **Integration Layer**: Cross-repository MCP configuration and security framework

### Timeline
**Duration**: 2-3 weeks (can be done in parallel with Phase II planning)
**Dependencies**: Must be completed before Phase II.4 implementation begins

### Benefits for Phase II
- **Automated data collection** from NYC Open Data (via existing OpenGov MCP) and government statistics (via Data Commons MCP)
- **Efficient web scraping** for NYC.gov appointments page (via Playwright MCP)
- **Consistent methodology** enforcement via NYC-specific skills
- **Community leverage** of proven civic AI tools and patterns
- **Future scalability** for additional NYC civic projects

---

## Phase II.1 · Schema Expansion

**Reference**: For detailed field definitions, examples, and edge cases, see [`SCHEMA_PROPOSAL_SUMMARY.md`](SCHEMA_PROPOSAL_SUMMARY.md)

### Current Issue: reports_to Field Ambiguity
The existing `reports_to` field conflates two distinct concepts:
- (a) Mayor's office oversight line on the citywide org chart (political/administrative)
- (b) True legal reporting/management relationships (statutory/legal)

### Schema Changes

#### 1. Retire reports_to Field
- **Action**: Remove `reports_to` field from schema
- **Rationale**: Field conflated multiple concepts and will be replaced by more specific fields

#### 2. Add Governance & Oversight Fields
- **`governance_structure`** (free text) - Describes WHAT type of governance exists
  - **Purpose**: Captures the governance mechanism (e.g., "NYC Health + Hospitals is governed by a Board of Directors", "Division reports directly to the leadership of Office of Technology and Innovation")
  - **Examples**: "Entity is governed by a Board of Directors", "Division reports directly to Department leadership"
  
- **`org_chart_oversight_record_id`** (RecordID format) - Links to overseeing entity via RecordID (e.g., `100123`)
  - **Purpose**: Replaces `reports_to` for org chart/political oversight relationships (what appears in Mayor's org chart)
  - **Usage**: Used for org chart/political oversight relationships only
  - **Note**: Distinct from `parent_organization_record_id` (org chart placement vs. governance relationship)
  
- **`org_chart_oversight_name`** (text) - Name of overseeing entity (derived from RecordID)
  - **Purpose**: Automatically populated from `org_chart_oversight_record_id` lookup
  - **Note**: Derived field for usability - provides both RecordID and name
  
- **`parent_organization_record_id`** (RecordID format) - Links to parent entity via RecordID (e.g., `100318`)
  - **Purpose**: Used for specialized boards → parent, divisions → parent department, subdivisions → parent
  - **Usage**: Governance relationships (specialized boards, divisions, subdivisions)
  - **Note**: Separate from `org_chart_oversight_record_id` (governance relationship vs. org chart placement)
  
- **`parent_organization_name`** (text) - Name of parent entity (derived from RecordID)
  - **Purpose**: Automatically populated from `parent_organization_record_id` lookup
  - **Note**: Derived field for usability - provides both RecordID and name

#### 3. Add Legal Authority Fields
- **`authorizing_authority`** (free text) - Legal authority that establishes the organization
  - **Purpose**: Documents the legal basis for the entity's existence
  - **Examples**: "NYC Charter § 2203", "New York State Public Authorities Law § 1260", "Mayoral Executive Order 18 of 2025"
  - **Format**: Statute, charter provision, executive order, or local law reference
  
- **`authorizing_authority_type`** (controlled vocabulary) - Categorizes authority type for queryability
  - **Purpose**: Enables filtering and querying by authority source
  - **Values**: "NYC Charter", "Mayoral Executive Order", "NYC Local Law", "New York State Law", etc.
  
- **`authorizing_url`** (URL) - Link to the legal document or statute
  - **Purpose**: Provides direct access to authoritative source documents
  - **Examples**: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2203"
  - **Requirement**: Must be official government sources (NYC.gov, State Legislature, etc.)

#### 4. Add Appointments Field
- **`appointments_summary`** (free text) - Describes HOW appointments/selection works
  - **Purpose**: Capture appointment mechanisms for Mayor's Office of Appointments tracking
  - **Examples**: 
    - "Board consists of 17 members: 11 appointed by Mayor, 3 by Borough Presidents, 3 by Comptroller. Chief Executive selected by Board."
    - "Board of Directors consists of members appointed by Governor, Mayor, and other officials. Chair and CEO appointed by Governor."
    - "Deputy Commissioner appointed by Commissioner of Office of Technology and Innovation."

#### 5. RecordID Format Change
- **Current format**: `NYC_GOID_000318` (uppercase, underscores, leading zeros)
- **New format**: `100318` (6-digit numeric, no prefix)
- **Rationale**: Avoids zip code conflicts (6 digits vs 5-digit zip codes), easier joins/queries, simpler format
- **Migration**: Crosswalk file will be provided mapping old IDs to new IDs
- **Examples**:
  - `NYC_GOID_000022` → `100022`
  - `NYC_GOID_000318` → `100318`
  - `NYC_GOID_100026` → `110026`
- **Timing**: RecordID format change happens during Phase II.4 implementation (see section 4.1)

#### 6. Board Modeling Approach

**Decision**: How to model boards and governance structures in the dataset.

**Primary Governing Boards** (Boards of Directors/Trustees):
- **Approach**: Captured in `governance_structure` and `appointments_summary` fields
- **NOT** separate entity records
- **Rationale**: These boards exist solely to govern their parent organization and do not have independent legal authority
- **Examples**: 
  - MTA Board of Directors → described in MTA entity's `governance_structure` and `appointments_summary`
  - Brooklyn Public Library Board of Trustees → described in Brooklyn Public Library entity's fields

**Specialized Boards** (with independent legal authority):
- **Approach**: Get their own entity records
- **Linking**: Linked to parent via `parent_organization_record_id` (RecordID, e.g., `100318`)
- **Documentation**: Relationship optionally mentioned in parent's `governance_structure`
- **Examples**: 
  - Health and Hospitals Corporation Personnel Review Board → separate entity record with `parent_organization_record_id` pointing to NYC Health + Hospitals
- **Note**: `parent_organization_record_id` is separate from `org_chart_oversight_record_id` (governance relationship vs. org chart placement)

**Key Benefits**:
- Clear separation between governance structure (WHAT) and appointment process (HOW)
- No schema bloat - primary boards don't create separate records
- Queryable relationships - can filter for specialized boards, divisions, and subdivisions via `parent_organization_record_id`
- Flexible - can iteratively enhance parent entities to mention specialized boards

---

## Phase II.2 · Mayor's Office of Appointments Universe Review

### Objective
Ensure the dataset comprehensively covers all entities where the Mayor has appointment authority, as tracked by the Mayor's Office of Appointments.

### Board Modeling Context
When reviewing crosswalk mappings and identifying entities to add, apply the **Board Modeling Approach** (see Phase II.1, section 6):
- **"Board of Directors/Trustees" entries** in MOA should match to parent organization, not create separate entities
  - These boards are captured in the parent entity's `governance_structure` and `appointments_summary` fields
- **Specialized boards** with independent legal authority should be separate entities
  - These get their own entity records, linked to parent via `parent_organization_record_id`
- **Crosswalk review** should distinguish between primary governing boards (narrative fields) and specialized boards (separate entities)

### Tasks

#### 1. NYC.gov Appointments Page Data Collection
- **Source**: https://www.nyc.gov/content/appointments/pages/boards-commissions
- **Scrape and create raw dataset** with available fields:
  - Entity name
  - Description
  - URL (when available)
- **Cross-reference with main NYCGO dataset** to identify coverage gaps
- **Create crosswalk mapping** between scraped data and existing entities

#### 2. Complete Entity Coverage Audit
- Review remaining entities from the ops list that haven't been confirmed yet
- Cross-reference with Mayor's Office of Appointments records
- Compare against NYC.gov appointments page data
- Identify any missing entities in current dataset

#### 3. Appointment Authority Validation
- Verify appointment mechanisms for all entities
- Populate new `appointments_summary` field
- Ensure accuracy of Mayor's appointment role for each entity

#### 4. Data Quality Review
- Validate new schema fields across all existing records
- Ensure consistency in field population
- Review and update any outdated information

---

## Phase II.3 · Crosswalk Data Expansion

### Objective
Expand the crosswalk dataset to include additional data sources and improve entity matching capabilities.

### Tasks

#### 1. Budget Code Integration
- **Research budget code sources** (OMB, Checkbook NYC, budget documents)
- **Map budget codes to NYCGO entities** where applicable
- **Add budget code fields** to crosswalk schema
- **Validate budget code accuracy** across fiscal years

#### 2. Additional Source Integration
- **Identify high-value crosswalk sources** beyond current coverage
- **Research NYC Open Data** for relevant organizational datasets
- **Explore state databases** for entities with state/local hybrid governance
- **Document new source integration methodology**

#### 3. Crosswalk Quality Enhancement
- **Standardize entity name matching** across sources
- **Add confidence scores** for crosswalk mappings
- **Create validation rules** for crosswalk data integrity
- **Implement automated crosswalk updates** where possible

---

## Phase II.4 · Implementation Plan

### 4.1 Schema Updates
1. **Update schema definition** in `src/nycgo_pipeline/schema.py`
2. **Modify export functions** to include new fields
3. **Update validation rules** for new field constraints
4. **Create migration strategy** for existing data
5. **Create RecordID format migration crosswalk file** mapping old IDs (`NYC_GOID_XXXXXX`) to new IDs (6-digit numeric)
6. **Update codebase to generate new RecordID format** for future entities
7. **Update all internal references and crosswalk files** to use new RecordID format

### 4.2 Web Scraping & Data Collection
1. **Develop scraper for NYC.gov appointments page**
2. **Create raw dataset from scraped appointments data**
3. **Research and collect budget code data sources**
4. **Document data collection methodology**

### 4.3 Data Population & Integration
1. **Research and populate authorizing_authority** for all existing entities
2. **Research and populate authorizing_url** where available
3. **Migrate existing `reports_to` field values** to new fields:
   - Map org chart/political oversight relationships → `org_chart_oversight_record_id` (requires translating entity names to RecordIDs)
   - Map parent-child governance relationships → `parent_organization_record_id` (requires translating entity names to RecordIDs)
   - Document migration decisions and any ambiguous cases
4. **Populate org_chart_oversight** from Mayor's office org chart
5. **Research and populate appointments_summary** for all entities
6. **Integrate budget codes** into crosswalk data
7. **Cross-reference scraped appointments data** with main dataset

### 4.4 Quality Assurance
1. **Review all Mayor's Office of Appointments entities** for completeness
2. **Validate new field accuracy** through source verification
3. **Cross-check appointment summaries** with official documentation
4. **Test pipeline with expanded schema**
5. **Validate crosswalk data integrity** and mappings

### 4.5 Documentation & Release
1. **Update field documentation** in schema specifications
2. **Document new data sources** and research methodology
3. **Update README** with Phase II changes
4. **Prepare release notes** for v1.1.0 or v2.0.0

---

## Phase II.5 · Data Sources & Research Strategy

### Primary Sources
- **NYC Charter**: For charter-mandated entities
- **Mayor's Office of Appointments**: Entity lists and appointment records
- **NYC.gov appointments page**: https://www.nyc.gov/content/appointments/pages/boards-commissions
- **NYC.gov org charts**: For administrative oversight relationships
- **Administrative Code**: For additional statutory entities
- **Executive Orders**: For Mayor-created entities
- **State statutes**: For state-mandated local entities
- **Budget documents**: OMB budget publications, Checkbook NYC
- **NYC Open Data**: For organizational and financial datasets

### Research Methodology
1. **Web scraping protocol** for NYC.gov appointments page
2. **Entity-by-entity verification** of authorizing documents
3. **Cross-reference multiple sources** for appointment mechanisms
4. **Budget code mapping** from financial data sources
5. **Document source URLs** for transparency and verification
6. **Maintain research notes** for future updates

---

## Success Criteria

### Deliverables
- [ ] Expanded schema with 9 new fields implemented (retiring 1 field: `reports_to`)
- [ ] All existing entities updated with new field values
- [ ] Complete coverage of Mayor's Office of Appointments universe
- [ ] Scraped dataset from NYC.gov appointments page
- [ ] Expanded crosswalk with budget codes and additional sources
- [ ] Updated documentation reflecting schema changes
- [ ] New dataset version published (v1.1.0 or v2.0.0)

### Quality Metrics
- **100% population** of authorizing_authority field
- **90%+ population** of authorizing_url field (where public documents exist)
- **Complete migration** of `reports_to` values to appropriate new fields (`org_chart_oversight_record_id` or `parent_organization_record_id`)
- **Comprehensive appointment summaries** for all entities with mayoral appointments
- **Zero missing entities** from Mayor's Office of Appointments scope
- **Complete crosswalk** between scraped appointments data and main dataset
- **Budget code coverage** for 80%+ of applicable entities

---

## Timeline Estimate

**Phase II.0 (Infrastructure Setup)**: 2-3 weeks *(can run parallel with planning)*
**Phase II.1 (Schema)**: 1-2 weeks
**Phase II.2 (MOA Universe Review)**: 2-3 weeks
**Phase II.3 (Crosswalk Expansion)**: 1-2 weeks
**Phase II.4 (Implementation)**: 2-3 weeks *(benefits from infrastructure)*
**Phase II.5 (QA & Release)**: 1 week

**Total**: 9-14 weeks *(or 7-11 weeks if infrastructure setup runs parallel)*

---

## Notes

- This phase builds directly on the stable v1.0.0 foundation from Phase I
- **Infrastructure setup** (Phase II.0) can begin immediately and run parallel with planning
- Schema changes will require careful migration of existing data
- Research phase may uncover additional entities not currently in scope
- **MCP servers and skills** will significantly accelerate implementation phases
- Consider whether schema changes warrant v1.1.0 (minor) or v2.0.0 (major) version
- Infrastructure investment will benefit future civic data projects beyond Phase II
- **Board modeling approach**: Primary boards are captured in narrative fields, specialized boards are separate entities. See Phase II.1, section 6 for details.
- **RecordID format migration**: Old format (`NYC_GOID_XXXXXX`) must be migrated to new format (6-digit numeric) during Phase II.4 implementation. Crosswalk file required for backward compatibility.
