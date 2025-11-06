# NYC Legal Citation Skill

This skill provides specialized guidance for proper citation and formatting of NYC legal documents, statutes, and government sources, ensuring consistency and accuracy in legal references throughout the NYC Governance Organizations project.

## Purpose

The NYC Legal Citation skill ensures consistent, accurate, and professional citation of NYC legal sources, supporting Phase II requirements for:

- **Authorizing Authority Documentation**: Proper citation of legal foundations
- **Source URL Standardization**: Consistent linking to official documents
- **Legal Research Validation**: Verification of citation accuracy
- **Professional Documentation**: Adherence to legal citation standards
- **Cross-Reference Integrity**: Consistent citations across all project materials

## NYC Legal Source Hierarchy

### Primary Legal Sources (Authoritative)

#### 1. NYC Charter
- **Authority Level**: Highest for NYC-specific entities
- **Citation Format**: `NYC Charter § [section number]`
- **URL Format**: `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-[section]`
- **Examples**:
  - `NYC Charter § 2801` (Board of Education)
  - `NYC Charter § 31` (Mayor's powers)
  - `NYC Charter § 2602` (Landmarks Preservation Commission)

**Citation Standards**:
```yaml
Full Citation:
  format: "New York City Charter § [section] ([year if not current])"
  example: "New York City Charter § 2801"

Short Citation (after first use):
  format: "Charter § [section]"
  example: "Charter § 2801"

URL Citation:
  format: "NYC Charter § [section], https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-[section]"
  example: "NYC Charter § 2801, https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801"
```

#### 2. NYC Administrative Code
- **Authority Level**: High for regulatory and operational entities
- **Citation Format**: `NYC Admin. Code § [title]-[section]`
- **URL Format**: `https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-[section]`
- **Examples**:
  - `NYC Admin. Code § 21-101` (Human Rights Commission)
  - `NYC Admin. Code § 15-106` (Buildings enforcement)
  - `NYC Admin. Code § 24-101` (Environmental control)

**Citation Standards**:
```yaml
Full Citation:
  format: "New York City Administrative Code § [title]-[section] ([year if not current])"
  example: "New York City Administrative Code § 21-101"

Short Citation:
  format: "Admin. Code § [title]-[section]"
  example: "Admin. Code § 21-101"

URL Citation:
  format: "NYC Admin. Code § [title]-[section], https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-[section]"
```

#### 3. NYC Local Laws
- **Authority Level**: High for recently enacted or modified entities
- **Citation Format**: `NYC Local Law [number] of [year]`
- **URL Format**: `https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=[ID]&GUID=[GUID]`
- **Examples**:
  - `NYC Local Law 97 of 2019` (Climate mobilization)
  - `NYC Local Law 1 of 2021` (Police accountability)

**Citation Standards**:
```yaml
Full Citation:
  format: "New York City Local Law [number] of [year]"
  example: "New York City Local Law 97 of 2019"

Short Citation:
  format: "Local Law [number] of [year]"
  example: "Local Law 97 of 2019"

URL Citation:
  format: "NYC Local Law [number] of [year], [Legistar URL]"
```

#### 4. Executive Orders
- **Authority Level**: Moderate for Mayor-created entities
- **Citation Format**: `NYC Executive Order [number] ([year])`
- **URL Format**: `https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/[year]/eo-[number].pdf`
- **Examples**:
  - `NYC Executive Order 1 (2019)` (ThriveNYC)
  - `NYC Executive Order 14 (2021)` (Racial equity)

**Citation Standards**:
```yaml
Full Citation:
  format: "New York City Executive Order [number] ([year])"
  example: "New York City Executive Order 1 (2019)"

Short Citation:
  format: "Exec. Order [number] ([year])"
  example: "Exec. Order 1 (2019)"

URL Citation:
  format: "NYC Executive Order [number] ([year]), https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/[year]/eo-[number].pdf"
```

### Secondary Legal Sources

#### 5. New York State Laws (when applicable)
- **Authority Level**: High for state-mandated local entities
- **Citation Format**: `NY [Law Code] § [section]`
- **URL Format**: `https://www.nysenate.gov/legislation/laws/[CODE]/[section]`
- **Examples**:
  - `NY Educ. Law § 2590-h` (Community education councils)
  - `NY Pub. Health Law § 1352` (Local health boards)

**Citation Standards**:
```yaml
Full Citation:
  format: "New York [Law Name] Law § [section]"
  example: "New York Education Law § 2590-h"

Common Abbreviations:
  - Education Law: "Educ. Law"
  - Public Health Law: "Pub. Health Law"
  - Mental Hygiene Law: "Mental Hyg. Law"
  - Environmental Conservation Law: "Envtl. Conserv. Law"
```

#### 6. NYC Rules (RCNY)
- **Authority Level**: Moderate for implementation details
- **Citation Format**: `[Title] RCNY § [section]-[subsection]`
- **URL Format**: `https://rules.cityofnewyork.us/`
- **Examples**:
  - `1 RCNY § 1-01` (Mayor's office organization)
  - `38 RCNY § 1-01` (Landmarks procedures)

### Tertiary Sources (Supporting)

#### 7. Agency Websites and Documents
- **Authority Level**: Low to moderate for operational information
- **Citation Format**: `[Agency Name], [Document Title] ([Date])`
- **URL Format**: Direct agency URL
- **Use Cases**: Current operational information, recent changes

#### 8. Budget Documents
- **Authority Level**: Moderate for financial relationships
- **Citation Format**: `NYC Office of Management and Budget, [Document Title] ([Fiscal Year])`
- **URL Format**: `https://www1.nyc.gov/site/omb/publications/[document].page`

## Citation Formatting Guidelines

### Basic Formatting Rules

#### Section and Subsection References
```yaml
Single Section: "§ 2801"
Multiple Sections: "§§ 2801, 2802"
Section with Subsection: "§ 2801(a)"
Section Range: "§§ 2801-2810"
```

#### Year and Date Conventions
```yaml
Current Law: No year needed
Historical Version: Include year in parentheses
  - "NYC Charter § 2801 (1989)" # for historical reference
  - "NYC Charter § 2801" # for current version

Amendment References:
  - "NYC Charter § 2801, as amended by Local Law 123 of 2020"
```

#### URL Standards and Validation

**URL Requirements**:
- Must link to official government sources
- Should point to specific section when possible
- Must be current and accessible
- Should use HTTPS when available

**Preferred URL Sources (in order)**:
1. **NYC Law Library (codelibrary.amlegal.com)**: For Charter and Administrative Code
2. **NYC.gov official pages**: For Executive Orders and current documents
3. **NYC Council Legistar**: For Local Laws and legislation
4. **NY State Senate website**: For state laws
5. **Agency official websites**: For operational documents

**URL Validation Requirements**:
- Test all URLs for accessibility
- Use permalink or stable URLs when available
- Include access date for time-sensitive documents
- Provide alternative URL if primary is unstable

### Field-Specific Citation Guidelines

#### For authorizing_authority Field
**Format**: Brief, authoritative citation
**Examples**:
```yaml
Charter Entity: "NYC Charter § 2801"
Admin Code Entity: "NYC Admin. Code § 21-101"
Executive Order Entity: "NYC Executive Order 1 (2019)"
State Mandated: "NY Educ. Law § 2590-h"
```

#### For authorizing_url Field
**Format**: Direct link to authorizing document
**Examples**:
```yaml
Charter URL: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801"
Admin Code URL: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-21101"
Executive Order URL: "https://www1.nyc.gov/assets/home/downloads/pdf/executive-orders/2019/eo-1.pdf"
```

#### For Research Documentation
**Format**: Complete citation with access information
**Examples**:
```yaml
Research Note: "Authority confirmed via NYC Charter § 2801, https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801 (accessed Nov. 4, 2025)"
```

## Common NYC Entity Legal Foundations

### Charter-Mandated Entities

#### Major Boards and Commissions
```yaml
Board of Education:
  citation: "NYC Charter § 2801"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801"

Landmarks Preservation Commission:
  citation: "NYC Charter § 2602"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2602"

Planning Commission:
  citation: "NYC Charter § 191"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-191"

Board of Standards and Appeals:
  citation: "NYC Charter § 659"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-659"
```

#### Mayoral Agencies
```yaml
Department of Education:
  citation: "NYC Charter Ch. 52"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801"

Fire Department:
  citation: "NYC Charter Ch. 15"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-487"

Police Department:
  citation: "NYC Charter Ch. 18"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-434"
```

### Administrative Code Entities

#### Regulatory Commissions
```yaml
Human Rights Commission:
  citation: "NYC Admin. Code § 8-101"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-8101"

Conflicts of Interest Board:
  citation: "NYC Admin. Code Ch. 68"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-25681"

Campaign Finance Board:
  citation: "NYC Admin. Code Ch. 7"
  url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-3701"
```

### Executive Order Entities

#### Recent Mayoral Initiatives
```yaml
ThriveNYC:
  citation: "NYC Executive Order 1 (2019)"
  url: "https://www1.nyc.gov/assets/home/downloads/pdf/executive-orders/2019/eo-1.pdf"

Office of Neighborhood Safety:
  citation: "NYC Executive Order 14 (2021)"
  url: "https://www1.nyc.gov/assets/home/downloads/pdf/executive-orders/2021/eo-14.pdf"
```

## Research and Validation Procedures

### Citation Verification Protocol

#### Step 1: Source Identification
1. Identify the authorizing legal document
2. Verify document authenticity and currency
3. Locate specific section or provision
4. Confirm entity establishment or authority

#### Step 2: URL Validation
1. Test URL accessibility and stability
2. Verify URL points to correct document section
3. Check for more recent amendments or changes
4. Document alternative URLs if primary is unstable

#### Step 3: Citation Accuracy
1. Verify section numbers and legal references
2. Check spelling and formatting consistency
3. Confirm citation follows established standards
4. Cross-reference with multiple sources when possible

### Common Citation Errors and Corrections

#### Incorrect Section References
```yaml
INCORRECT: "NYC Charter Section 2801"
CORRECT: "NYC Charter § 2801"

INCORRECT: "NYC Charter 2801"
CORRECT: "NYC Charter § 2801"

INCORRECT: "Charter Article 2801"
CORRECT: "NYC Charter § 2801"
```

#### URL Format Issues
```yaml
INCORRECT: HTTP instead of HTTPS
CORRECT: Use HTTPS when available

INCORRECT: Generic page instead of specific section
CORRECT: Link to specific section when possible

INCORRECT: Outdated or broken links
CORRECT: Verify URL accessibility before inclusion
```

#### Abbreviation Inconsistencies
```yaml
Standardized Abbreviations:
  - NYC Charter (not "City Charter" or "Charter")
  - NYC Admin. Code (not "Administrative Code")
  - Local Law (not "LL" or "Loc. Law")
  - Executive Order (not "EO" or "Exec. Ord.")
```

## Integration with Phase II Implementation

### Schema Field Support

This citation skill directly supports Phase II fields:

#### authorizing_authority Field
- Provides standardized citation format
- Ensures consistent legal reference style
- Validates section number accuracy
- Maintains professional documentation standards

#### authorizing_url Field
- Establishes URL format standards
- Validates link accessibility and stability
- Ensures official source prioritization
- Maintains consistent linking patterns

### Quality Assurance Integration

**Pre-Population Validation**:
- Verify legal authority exists and is current
- Confirm URL accessibility and accuracy
- Validate citation format consistency
- Cross-check with multiple sources

**Post-Population Review**:
- Spot-check citation accuracy across entities
- Validate URL stability and accessibility
- Ensure format consistency throughout dataset
- Identify and correct any citation errors

### Research Integration

**Legal Research Support**:
- Guides systematic legal source research
- Provides standard citation format for documentation
- Ensures professional-quality legal references
- Supports source verification procedures

**Documentation Standards**:
- Maintains consistent citation style across project
- Supports reproducible research methodology
- Enables efficient source verification
- Facilitates professional presentation of findings

This citation skill ensures that all legal references in the NYC Governance Organizations project meet professional standards and provide reliable, verifiable links to authoritative sources.
