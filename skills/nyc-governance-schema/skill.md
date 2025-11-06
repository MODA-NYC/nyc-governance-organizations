# NYC Governance Schema Skill

This skill provides specialized guidance for working with the NYC Governance Organizations schema, particularly the Phase II expanded schema with new fields for enhanced organizational relationship tracking.

## Purpose

The NYC Governance Schema skill ensures consistent data validation, field definitions, and quality standards for the NYC Governance Organizations dataset. It guides LLMs in:

- **Schema Field Validation**: Proper use and population of all schema fields
- **Phase II Field Implementation**: Correct implementation of new fields (reports_to redefinition, org_chart_oversight, authorizing_authority, authorizing_url, appointments_summary)
- **Data Quality Standards**: Consistency checks and validation rules
- **Entity Classification**: Proper categorization of NYC governance entities
- **Relationship Mapping**: Understanding and documenting organizational relationships

## Phase II Schema Expansion

### New Field Definitions

#### 1. reports_to (Redefined)
- **Type**: Short text field
- **NEW Definition**: Legal/managerial reporting relationships ONLY
- **Previous Issue**: Conflated political oversight with legal reporting
- **NEW Values**:
  - Legal reporting entity name (when applicable)
  - `NULL` or `"Independent"` when no legal reporting exists
  - Examples: "NYC Department of Education", "NYC Health + Hospitals", "Independent"
- **Purpose**: Capture actual statutory/legal management structure
- **Validation Rules**:
  - Must be NULL for truly independent entities (e.g., independent boards/commissions)
  - Must reference actual legal reporting entity, not political oversight
  - Should align with statutory/charter requirements

#### 2. org_chart_oversight (New)
- **Type**: Short text field
- **Definition**: Who the Mayor's org chart shows as the liaison/overseer
- **Purpose**: Purely descriptive, captures administrative oversight as shown on official org charts
- **Values**: Mayor's office entity or official responsible for coordination/liaison
- **Examples**: "Mayor's Office", "Deputy Mayor for Operations", "First Deputy Mayor"
- **Validation Rules**:
  - Should reflect current Mayor's organizational structure
  - Separate from legal reporting relationships
  - Can change with new administrations

#### 3. authorizing_authority (New)
- **Type**: Short text field
- **Definition**: Legal entity or statute that created/authorizes the organization
- **Purpose**: Capture the source of organizational authority
- **Examples**:
  - "NYC Charter § 2801" (specific charter section)
  - "New York State Education Law"
  - "Executive Order 2019-1"
  - "Administrative Code § 21-101"
- **Validation Rules**:
  - Must reference specific legal authority
  - Should include section numbers when available
  - Must be researchable/verifiable

#### 4. authorizing_url (New)
- **Type**: URL field
- **Definition**: Link to the legal document, statute, or charter provision that establishes the organization
- **Purpose**: Provide direct access to authorizing documentation
- **Examples**:
  - `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2524`
  - `https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/2019/eo-1.pdf`
  - `https://www.nysenate.gov/legislation/laws/EDN`
- **Validation Rules**:
  - Must be valid URL format
  - Should point to official government sources
  - Must correspond to authorizing_authority field

#### 5. appointments_summary (New)
- **Type**: Text field
- **Definition**: Summary of how key positions are appointed (board members, leadership, etc.)
- **Purpose**: Capture appointment mechanisms for Mayor's Office of Appointments tracking
- **Examples**:
  - "Mayor appoints 5 of 7 board members; 2 appointed by City Council"
  - "Mayor appoints Executive Director with City Council confirmation"
  - "Self-governing board; internal selection of leadership"
  - "Board members appointed by various agencies; Mayor appoints chair"
- **Validation Rules**:
  - Must describe key appointment mechanisms
  - Should specify numbers when relevant
  - Must be factually accurate and verifiable

### Existing Field Validation

#### entity_name
- **Standards**: Official entity name as used in legal documents
- **Consistency**: Standardized across all related records
- **Format**: Proper capitalization and official naming conventions

#### entity_type
- **Categories**: Board, Commission, Authority, Department, Office, etc.
- **Consistency**: Standardized categorization across similar entities
- **Validation**: Must align with official entity classification

#### description
- **Content**: Clear, factual description of entity purpose and function
- **Length**: Concise but comprehensive (typically 1-3 sentences)
- **Source**: Based on official documentation and legal establishment

## Data Quality Guidelines

### Field Population Standards

#### Required Fields
All entities must have:
- `entity_name` (primary identifier)
- `entity_type` (classification)
- `description` (functional description)
- `authorizing_authority` (NEW - Phase II requirement)

#### Conditional Requirements
- `reports_to`: Required only if legal reporting relationship exists
- `org_chart_oversight`: Required for entities appearing on Mayor's org chart
- `authorizing_url`: Required when public documentation is available (target: 90%+)
- `appointments_summary`: Required for entities where Mayor has appointment authority

### Validation Rules

#### reports_to vs org_chart_oversight Distinction
```
CORRECT:
reports_to: "NYC Department of Education"
org_chart_oversight: "Deputy Mayor for Strategic Policy Initiatives"

INCORRECT (old conflated approach):
reports_to: "Deputy Mayor for Strategic Policy Initiatives"
```

#### Authorizing Authority Specificity
```
PREFERRED:
authorizing_authority: "NYC Charter § 2801"
authorizing_url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2524"

ACCEPTABLE:
authorizing_authority: "NYC Charter"
authorizing_url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/"

INADEQUATE:
authorizing_authority: "City government"
```

#### Appointments Summary Detail Level
```
EXCELLENT:
"Mayor appoints 5 of 9 members to 3-year terms; Public Advocate appoints 1; Borough Presidents each appoint 1; all subject to City Council confirmation"

GOOD:
"Mayor appoints 5 of 9 board members; other officials appoint remaining 4"

MINIMAL (acceptable):
"Mayor appoints majority of board members"

INADEQUATE:
"Mayor involved in appointments"
```

## Entity Classification Standards

### Entity Type Categories

#### Boards
- **Definition**: Multi-member governing or advisory bodies
- **Examples**: Board of Education, Landmarks Preservation Commission Board
- **Characteristics**: Multiple appointed members, regular meetings, formal votes

#### Commissions
- **Definition**: Regulatory or oversight bodies with specific mandates
- **Examples**: Human Rights Commission, Conflicts of Interest Board
- **Characteristics**: Regulatory authority, quasi-judicial functions

#### Authorities
- **Definition**: Semi-independent entities with specific operational mandates
- **Examples**: Economic Development Corporation, Housing Authority
- **Characteristics**: Operational independence, often revenue-generating

#### Departments
- **Definition**: Core city agencies under direct mayoral control
- **Examples**: Department of Education, Department of Health and Mental Hygiene
- **Characteristics**: Direct reporting to Mayor, operational city functions

#### Offices
- **Definition**: Administrative units within Mayor's office or departments
- **Examples**: Mayor's Office of Criminal Justice, Office of Emergency Management
- **Characteristics**: Staff-level support, specialized functions

### Relationship Mapping Standards

#### Legal Reporting Relationships
- Based on statutory or charter requirements
- Formal accountability structures
- Budget and operational oversight authority

#### Administrative Oversight
- Day-to-day coordination relationships
- Policy alignment responsibilities
- Political/strategic guidance

#### Appointment Authority Relationships
- Who has power to appoint key positions
- Confirmation requirements
- Term lengths and removal authority

## Research and Validation Protocols

### Source Verification Requirements

#### Primary Sources (Required)
1. **NYC Charter**: For charter-mandated entities
2. **Administrative Code**: For code-established entities
3. **Executive Orders**: For Mayor-created entities
4. **State Statutes**: For state-mandated local entities

#### Secondary Sources (Supportive)
1. **Mayor's Office org charts**: For administrative relationships
2. **Agency websites**: For current operational information
3. **Budget documents**: For financial relationships
4. **News reports**: For recent changes (must verify against primary sources)

### Data Quality Assurance

#### Entity Verification Checklist
- [ ] Official entity name confirmed from legal source
- [ ] Entity type classification verified against similar entities
- [ ] Authorizing authority identified and cited
- [ ] Legal documentation accessible via URL
- [ ] Appointment mechanisms researched and documented
- [ ] Reporting relationships distinguished (legal vs administrative)

#### Cross-Reference Validation
- [ ] Entity appears in Mayor's Office of Appointments scope (if applicable)
- [ ] Entity cross-referenced with NYC.gov appointments page
- [ ] Budget codes identified and validated (where applicable)
- [ ] Historical changes documented and accounted for

## Phase II Implementation Guidelines

### Migration Strategy for Existing Data

#### Step 1: reports_to Field Redefinition
1. Review all existing `reports_to` values
2. Identify entries that conflate political oversight with legal reporting
3. Research actual legal reporting relationships
4. Update `reports_to` to legal-only relationships
5. Capture political oversight in new `org_chart_oversight` field

#### Step 2: New Field Population
1. Research authorizing authority for all entities
2. Locate and verify authorizing URLs
3. Document appointment mechanisms
4. Populate org chart oversight relationships
5. Validate all new field values

#### Step 3: Quality Assurance
1. Cross-check new data against primary sources
2. Validate field consistency across similar entities
3. Ensure Mayor's Office of Appointments coverage is complete
4. Test data integrity with pipeline validation

### Common Implementation Patterns

#### Independent Boards/Commissions
```yaml
reports_to: null  # or "Independent"
org_chart_oversight: "Mayor's Office"
authorizing_authority: "NYC Charter § XXXX"
appointments_summary: "Mayor appoints X of Y members"
```

#### Mayoral Agencies
```yaml
reports_to: null  # (direct to Mayor)
org_chart_oversight: "Mayor"
authorizing_authority: "NYC Charter § XXXX"
appointments_summary: "Mayor appoints agency head"
```

#### Subsidiary Entities
```yaml
reports_to: "Parent Agency Name"
org_chart_oversight: "Deputy Mayor for [Area]"
authorizing_authority: "Administrative Code § XXX"
appointments_summary: "Agency head appoints; Mayor confirms"
```

This skill ensures that the NYC Governance Organizations dataset maintains the highest standards of accuracy, consistency, and comprehensiveness as it expands to capture the full complexity of NYC's governance structure in Phase II.
