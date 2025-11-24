# NYC Governance Schema Skill

This skill provides specialized guidance for working with the NYC Governance Organizations schema, particularly the Phase II expanded schema with new fields for enhanced organizational relationship tracking.

## Purpose

The NYC Governance Schema skill ensures consistent data validation, field definitions, and quality standards for the NYC Governance Organizations dataset. It guides LLMs in:

- **Schema Field Validation**: Proper use and population of all schema fields
- **Phase II Field Implementation**: Correct implementation of new fields (reports_to redefinition, org_chart_oversight, authorizing_authority, authorizing_url, appointments_summary)
- **Data Quality Standards**: Consistency checks and validation rules
- **Entity Classification**: Proper categorization of NYC governance entities
- **Relationship Mapping**: Understanding and documenting organizational relationships

## CRITICAL: Published Schema Fields Only

**IMPORTANT**: When creating edits or populating data, **ONLY fill in fields that are part of the published schema**. The golden dataset contains additional internal fields that are NOT published and should NOT be populated during Phase II data entry.

### Published Phase II Schema Fields (26 fields)

**Core Identity:**
- `record_id`, `name`, `name_alphabetized`, `operational_status`, `organization_type`

**Descriptive:**
- `url`, `alternate_or_former_names`, `acronym`, `alternate_or_former_acronyms`

**Principal Officer:**
- `principal_officer_title`, `principal_officer_full_name`, `principal_officer_first_name`, `principal_officer_last_name`, `principal_officer_contact_url`

**Organizational Relationships:**
- `in_org_chart`, `org_chart_oversight`, `org_chart_oversight_record_id`, `org_chart_oversight_name`, `parent_organization_record_id`, `parent_organization_name`

**Phase II New Fields:**
- `authorizing_authority`, `authorizing_authority_type`, `authorizing_url`, `appointments_summary`, `governance_structure`

**Computed:**
- `listed_in_nyc_gov_agency_directory` (computed field, not manually populated)

### ⚠️ CRITICAL: RecordID Format Standards

**New Format (Current):**
- **Format**: 6-digit number starting with "1" (e.g., `100436`, `100318`, `110026`)
- **Rules**:
  - Always 6 digits
  - NEVER starts with "0"
  - All numeric (no prefixes like `NYC_GOID_`)

**Conversion from Old Format:**
```python
# Reference: tests/test_recordid_generation.py
# For old IDs < 100000 (e.g., NYC_GOID_000436):
old_id = 436  # numeric part of NYC_GOID_000436
new_id = 100436  # add 100000 → result: 100436

# For old IDs ≥ 100000 (e.g., NYC_GOID_100026):
old_id = 100026  # numeric part of NYC_GOID_100026
new_id = 110026  # add 10000 → result: 110026
```

**Examples:**
- `NYC_GOID_000436` → `100436` ✓
- `NYC_GOID_000318` → `100318` ✓
- `NYC_GOID_100026` → `110026` ✓
- `NYC_GOID_000119` → `100119` ✓

**❌ Common Errors:**
- Using 3-digit IDs: `436` (WRONG - must be 6 digits)
- Starting with "0": `000436` (WRONG - must start with "1")
- Keeping old prefix: `NYC_GOID_100436` (WRONG - no prefix in new format)
- Just stripping prefix: `000436` from `NYC_GOID_000436` (WRONG - must apply formula)

**For NEW entities in edits files:**
- Use `NEW` as placeholder record_id
- Pipeline will auto-generate next available ID in sequence

### Fields NOT in Published Schema (DO NOT FILL IN)

**❌ DO NOT populate these fields in edits files:**
- `founding_year` (FoundingYear) - Internal field only
- `notes` (Notes) - Internal field only
- `description` (Description) - Internal field only
- `budget_code` (BudgetCode) - Internal field only
- `open_datasets_url` (OpenDatasetsURL) - Internal field only
- Other internal tracking fields (source tracking, instance tracking, etc.)

**Rationale:**
- Focus on fields that will be published and used by external consumers
- Avoid populating fields that are internal-only or not yet part of the published schema
- Maintain consistency with published schema expectations
- Reduce data entry burden by focusing on relevant fields

**When in doubt:** Check the published schema documentation (`docs/PHASE_II_SCHEMA.md`) or the README to confirm if a field is part of the published schema before including it in edits.

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
- **Multiple Authorities**: Use semicolon (`;`) to separate multiple authorities when an entity has truly multiple authorizing sources
- **Examples**:
  - "NYC Charter § 2801" (specific charter section - preferred)
  - "NYC Admin. Code § 21-101" (administrative code)
  - "NYC Charter § 738; NYS L.1969, c.1016 (\"Health and Hospitals Corporation Act\")" (multiple authorities)
  - "Executive Order 2019-1" (only if no codified citation)
  - "Local Law 38 of 2012" (only if no codified citation exists)
- **Local Law Citation Guidance**:
  - **Generally**: Prefer codified citations (Charter/Admin Code) over Local Law numbers
  - **Include Local Law**: Only when no codified citation exists, or entity is defined by Local Law itself (temporary task forces)
  - **Avoid**: Including Local Law citations when Charter/Admin Code citation already exists (e.g., avoid "NYC Charter § 1301; Local Law 38 of 2012")
- **Validation Rules**:
  - Must reference specific legal authority
  - Prefer Charter or Administrative Code citations when available
  - Multiple authorities separated by semicolon (`;`) if truly multiple sources
  - Should include section numbers when available
  - Must be researchable/verifiable

#### 4. authorizing_authority_type (New)
- **Type**: Controlled Vocabulary (String)
- **Definition**: Categorizes the type of legal authority that establishes the organization
- **Purpose**: Provides standardized classification for filtering and querying by authority source
- **CRITICAL RULE**: **Controlled Vocabulary - EXACT VALUES ONLY**
- **Controlled Vocabulary (Valid Values)**:
  1. **"NYC Charter"** - Entity established by NYC Charter provision
  2. **"NYC Administrative Code"** - Entity established by NYC Administrative Code section
  3. **"City Council Local Law"** - Entity established by City Council Local Law (use only when no codified citation exists)
  4. **"Mayoral Executive Order"** - Entity established by Mayoral Executive Order (use only when no codified citation exists)
  5. **"New York State Law"** - Entity established by New York State statute
  6. **"Federal Law"** - Entity established by federal statute
  7. **"Other"** - Other legal authority not covered above (use sparingly)
- **CRITICAL RULES**:
  - **Single value only** - Do NOT use semicolon-separated values (e.g., "NYC Local Law; NYC Charter" is INVALID)
  - **Prefer codified citations** - If entity is codified into Charter/Admin Code, use that type even if originally established by Local Law
  - **Must match `authorizing_authority` field** - The type should correspond to the primary authority cited in `authorizing_authority`
- **Selection Priority**:
  1. If entity is codified in Charter → use "NYC Charter"
  2. If entity is codified in Admin Code → use "NYC Administrative Code"
  3. If entity is only in Local Law (not codified) → use "City Council Local Law"
  4. If entity is only in Executive Order (not codified) → use "Mayoral Executive Order"
  5. If entity is established by State law → use "New York State Law"
  6. If entity is established by Federal law → use "Federal Law"
- **Examples (CORRECT)**:
  - `authorizing_authority`: "NYC Charter § 1524-a" → `authorizing_authority_type`: "NYC Charter"
  - `authorizing_authority`: "NYC Admin. Code § 21-101" → `authorizing_authority_type`: "NYC Administrative Code"
  - `authorizing_authority`: "Local Law 38 of 2012" (not codified) → `authorizing_authority_type`: "City Council Local Law"
  - `authorizing_authority`: "Executive Order 16 (2014)" (not codified) → `authorizing_authority_type`: "Mayoral Executive Order"
  - `authorizing_authority`: "NYC Charter § 738; NYS L.1969, c.1016" → `authorizing_authority_type`: "NYC Charter" (prefer Charter)
- **Examples (INCORRECT)**:
  - ❌ "NYC Local Law; NYC Charter" (multiple values - use single value, prefer Charter)
  - ❌ "Local Law" (not in controlled vocabulary - use "City Council Local Law")
  - ❌ "NYC Local Law" (not in controlled vocabulary - use "City Council Local Law")
  - ❌ "Executive Order" (not in controlled vocabulary - use "Mayoral Executive Order")
- **Validation Rules**:
  - Must be one of the controlled vocabulary values listed above
  - Must align with `authorizing_authority` field
  - Should prefer codified citations (Charter/Admin Code) over Local Law/Executive Order when codified
  - Single value only (no semicolon-separated multiple values)

#### 5. authorizing_url (New)
- **Type**: URL field
- **Definition**: Link to the legal document, statute, or charter provision that establishes the organization
- **Purpose**: Provide direct access to authorizing documentation
- **CRITICAL RULE**: Exactly ONE URL per row (the canonical link)
- **URL Selection Priority**:
  1. Charter or Administrative Code section (if available) - preferred as most stable
  2. State law URL (if authority is state law only, no Charter/Admin Code)
  3. Local Law URL (only if no codified citation exists)
  4. Executive Order URL (only if no codified citation exists)
- **Examples**:
  - `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2524` (Charter - preferred)
  - `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-21101` (Admin Code)
  - `https://www.nysenate.gov/legislation/laws/PBH/A1260` (State law - only if no Charter/Admin Code)
  - `https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/2019/eo-1.pdf` (EO - only if no codified citation)
- **Multiple Authorities Handling**:
  - If `authorizing_authority` contains multiple citations (semicolon-separated), use only the canonical URL (prefer Charter/Admin Code)
  - Do NOT use pipe-separated URLs (`|`) - keep to single URL
  - If you need to expose multiple URLs later, consider a separate `nycgo_authorities` table rather than overloading this field
- **Validation Rules**:
  - Must be valid URL format
  - Should point to official government sources
  - Must correspond to authorizing_authority field
  - Exactly one URL per row (no pipe-separated multiple URLs)

#### 6. appointments_summary (New)
- **Type**: Text field
- **Definition**: Summary of how key positions are appointed (board members, leadership, etc.)
- **Purpose**: Capture appointment mechanisms for Mayor's Office of Appointments tracking
- **Critical Distinction**: This field describes the **appointment mechanism/rules** as defined in the Charter or enabling legislation, NOT specific appointment events. It should capture the ongoing rules for how appointments work, not who was appointed on a particular date.
- **Examples (CORRECT - describing mechanisms):**
  - "Mayor appoints 5 of 7 board members; 2 appointed by City Council"
  - "Mayor appoints Executive Director with City Council confirmation"
  - "Self-governing board; internal selection of leadership"
  - "Board members appointed by various agencies; Mayor appoints chair"
  - "Members appointed by Mayor, including at minimum representatives from environmental, environmental justice, urban planning, architecture, engineering, coastal protection, construction, critical infrastructure, labor, business, energy, and academic sectors. Also includes Speaker of City Council or designee and Chairperson of Council Committee on Environmental Protection or designee."
- **Examples (INCORRECT - describing specific events):**
  - ❌ "Mayor Adams appointed 26 members in Dec 2022" (specific appointment event)
  - ❌ "26 members appointed by Mayor" (current composition, not mechanism)
  - ✅ "Members appointed by Mayor, including at minimum representatives from [sectors]" (mechanism/rules)
- **Validation Rules**:
  - Must describe key appointment mechanisms (rules from Charter/legislation)
  - Should specify numbers when relevant (e.g., "5 of 7 members")
  - Must be factually accurate and verifiable
  - Should NOT describe specific appointment events or current composition

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

#### alternate_or_former_names
- **Purpose**: Capture actual alternate names or former names used in official sources
- **Critical Requirements**:
  - **DO NOT include acronyms** - Acronyms belong in the `acronym` or `alternate_or_former_acronyms` fields
  - **DO NOT guess or assume** - Only include names with evidence from official sources
  - **Must have evidence** - Each alternate/former name must be justified with evidence (URL, document citation, etc.)
  - **Distinguish from primary name** - Only include names that are actually used as distinct alternate names, not just variations in how the primary name is written
- **What to Include**:
  - ✅ Former official names (e.g., entity was renamed)
  - ✅ Alternate names used in specific official contexts (e.g., legal documents, specific agencies)
  - ✅ Names used for specific purposes with evidence
- **What NOT to Include**:
  - ❌ Acronyms (use `acronym` field instead)
  - ❌ Common variations of the primary name without evidence
  - ❌ Guessed or assumed names
  - ❌ Names found only in unofficial sources
- **Examples**:
  - ✅ CORRECT: "Department of Health and Mental Hygiene" (if entity was formerly "Department of Health" and renamed)
  - ✅ CORRECT: "NYC Health + Hospitals" (if used as alternate name in official sources with evidence)
  - ❌ INCORRECT: "TDC; NYC TDC" (these are acronyms, not alternate names)
  - ❌ INCORRECT: "NYC Technology Development Corporation" (if no evidence it was used as distinct alternate name)
- **Validation**: Each name must be traceable to an official source with evidence documented in reason field

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
EXCELLENT (describes mechanism/rules):
"Mayor appoints 5 of 9 members to 3-year terms; Public Advocate appoints 1; Borough Presidents each appoint 1; all subject to City Council confirmation"

GOOD (describes mechanism):
"Mayor appoints 5 of 9 board members; other officials appoint remaining 4"

MINIMAL (acceptable - describes mechanism):
"Mayor appoints majority of board members"

INADEQUATE (too vague):
"Mayor involved in appointments"

INCORRECT (describes specific event, not mechanism):
❌ "Mayor Adams appointed 26 members in Dec 2022"
❌ "26 members appointed by Mayor"
```

## Entity Classification Standards

### organization_type Field - Controlled Vocabulary

**CRITICAL**: The `organization_type` field uses a **controlled vocabulary**. Only the following exact values are valid:

1. **"Elected Office"** - Elected positions and their supporting offices
2. **"Mayoral Agency"** - Agencies under direct mayoral control
3. **"Non-Mayoral Agency"** - Agencies not under direct mayoral control (e.g., independent authorities, elected official offices)
4. **"Division"** - Divisions within larger agencies
5. **"Mayoral Office"** - Offices within the Mayor's executive structure
6. **"Advisory or Regulatory Organization"** - Advisory boards, commissions, regulatory bodies
7. **"Public Benefit or Development Organization"** - Public benefit corporations, economic development entities
8. **"Nonprofit Organization"** - 501(c)(3) and other nonprofit entities affiliated with city governance
9. **"State Government Agency"** - State agencies with NYC representation or impact

**Selection Guidelines:**
- Use exact spelling and capitalization as listed above
- Choose the most specific category that fits the entity
- For entities that could fit multiple categories, prioritize by governance structure over function
- Document rationale in justification field when categorization is non-obvious

### Entity Type Categories (Historical Reference)

**Note**: The following categories are descriptive guidance. Always use the controlled vocabulary above for the `organization_type` field.

#### Boards
- **Definition**: Multi-member governing or advisory bodies
- **Examples**: Board of Education, Landmarks Preservation Commission Board
- **Characteristics**: Multiple appointed members, regular meetings, formal votes
- **Typical organization_type**: "Advisory or Regulatory Organization"

#### Commissions
- **Definition**: Regulatory or oversight bodies with specific mandates
- **Examples**: Human Rights Commission, Conflicts of Interest Board
- **Characteristics**: Regulatory authority, quasi-judicial functions
- **Typical organization_type**: "Advisory or Regulatory Organization"

#### Authorities
- **Definition**: Semi-independent entities with specific operational mandates
- **Examples**: Economic Development Corporation, Housing Authority
- **Characteristics**: Operational independence, often revenue-generating
- **Typical organization_type**: "Public Benefit or Development Organization" or "Non-Mayoral Agency"

#### Departments
- **Definition**: Core city agencies under direct mayoral control
- **Examples**: Department of Education, Department of Health and Mental Hygiene
- **Characteristics**: Direct reporting to Mayor, operational city functions
- **Typical organization_type**: "Mayoral Agency"

#### Offices
- **Definition**: Administrative units within Mayor's office or departments
- **Examples**: Mayor's Office of Criminal Justice, Office of Emergency Management
- **Characteristics**: Staff-level support, specialized functions
- **Typical organization_type**: "Mayoral Office" or "Division"

### Statutory Subcommittees and Sub-Bodies

#### When to Create Separate Entities vs. Document in governance_structure

**General Rule**: Subcommittees or sub-bodies that exist only to support a parent organization should be documented in the parent's `governance_structure` field, NOT as separate top-level NYCGO entities.

**Create Separate Top-Level Entity When:**
- Entity has its own legal powers and authorities independent of parent
- Entity has its own statutory mandate distinct from parent organization
- Entity is widely treated as standalone body with its own public role
- Entity can take official actions or promulgate regulations independently
- Examples: Civil Service Commission (separate from its Screening Committee), Tax Appeals Tribunal (within OATA but has independent judicial authority)

**Document in governance_structure Field When:**
- Subcommittee/sub-body exists only to advise or support parent organization
- Subcommittee's existence and membership flow entirely from parent body
- Subcommittee's remit is solely to advise parent, even if mandated by statute
- Subcommittee has no independent powers or authorities
- Examples: Community Services Board subcommittees (Mental Health, Developmental Disabilities, Substance Use Disorder)

#### Statutory Subcommittees Example: Community Services Board

The Community Services Board is required by NYS Mental Hygiene Law §41.11 and NYC Charter §568 to have three subcommittees:
1. Mental Health Subcommittee
2. Developmental Disabilities Subcommittee
3. Substance Use Disorder Subcommittee

**Why These Are NOT Separate Entities:**
- They exist only "as subcommittees of the Community Services Board"
- They advise the CSB and Director of Community Services, not independent authorities
- They have no statutory powers to contract, promulgate rules, or take official actions
- Chair selection is internal to DOHMH staff, not independent appointments

**How to Document:**
```yaml
Entity: Community Services Board (record_id 119)
governance_structure: "Advisory board to NYC Commissioner of Health and Mental Hygiene per NYC Charter §568 and NYS Mental Hygiene Law §§41.05(b), 41.11(b). Board consists of 15 members appointed by Mayor. Statutorily required to have three subcommittees per MHL §41.11 and Charter §568: Mental Health Subcommittee, Developmental Disabilities Subcommittee, and Substance Use Disorder Subcommittee. Each subcommittee (maximum 9-11 members) appointed by Mayor; at least three subcommittee members must also be CSB members..."
```

#### Decision Tree for Subcommittees

```
Is the sub-body created by statute/charter?
├─ YES → Does it have independent powers/authorities?
│   ├─ YES → Create separate top-level entity
│   │   Example: Tax Appeals Tribunal (within OATA but has judicial authority)
│   └─ NO → Is it widely treated as standalone with own public role?
│       ├─ YES → Consider separate entity (edge case, consult with team)
│       └─ NO → Document in parent's governance_structure field
│           Example: Community Services Board subcommittees
└─ NO (internal committee) → Document in parent's governance_structure field
    Example: Agency internal advisory committees
```

#### Implementation Standards for Statutory Subcommittees

**In governance_structure Field, Include:**
1. **Statutory Requirement**: Cite the law requiring subcommittees
2. **Subcommittee Names**: List all required subcommittees
3. **Composition Rules**: Size limits, overlap requirements with parent board
4. **Appointment Authority**: Who appoints subcommittee members
5. **Function**: What subcommittees advise on, their relationship to parent

**Example Format:**
```
"Statutorily required to have [number] subcommittees per [law citation]:
[Subcommittee 1 Name], [Subcommittee 2 Name], [Subcommittee 3 Name].
Each subcommittee ([composition details]) appointed by [authority];
[overlap requirements]. Subcommittees meet separately and advise
[parent body] on their respective subject areas."
```

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
