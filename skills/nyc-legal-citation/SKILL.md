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

#### 7. DORIS Government Publications Portal
- **Authority Level**: Moderate for official agency reports and mandated publications
- **URL**: [https://a860-gpp.nyc.gov](https://a860-gpp.nyc.gov/collections/zw12z528p?locale=en)
- **Citation Format**: `[Agency Name], [Report Title], Government Publications Portal ([Date])`
- **Use Cases**: 
  - Agency reports that cite legal authorities
  - Mandated reports required by Charter §1133
  - Official publications documenting entity establishment
  - Full-text searchable repository of city government publications
- **Search Tips**: Use full-text search with entity name and terms like "authority", "charter", "local law", or "established by"

#### 8. Agency Websites and Documents
- **Authority Level**: Low to moderate for operational information
- **Citation Format**: `[Agency Name], [Document Title] ([Date])`
- **URL Format**: Direct agency URL
- **Use Cases**: Current operational information, recent changes

#### 9. Budget Documents
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
4. **DORIS Government Publications Portal (a860-gpp.nyc.gov)**: For agency reports, mandated reports, and official publications that may cite legal authorities
5. **NY State Senate website**: For state laws
6. **Agency official websites**: For operational documents

**URL Validation Requirements**:
- Test all URLs for accessibility before including in dataset
- Use permalink or stable URLs when available
- Include access date for time-sensitive documents
- Provide alternative URL if primary is unstable
- **HTTP Status Code Checks**:
  - ✅ **200 OK**: URL is accessible and valid
  - ⚠️ **301/302 Redirect**: Follow redirect to verify final destination is correct; may indicate outdated URL
  - ❌ **404 Not Found**: URL is broken; do not use without finding alternative
  - ❌ **403 Forbidden**: URL may require authentication; prefer public alternatives
  - ❌ **500+ Server Error**: Temporary issue; verify before using
- **Redirect Handling**: If URL returns 301/302, verify redirect destination is correct and update URL if redirect points to different content
- **Evidence URL Validation**: For URLs cited in reason/evidence fields, verify they are accessible and point to correct content

### Field-Specific Citation Guidelines

#### For authorizing_authority Field
**Format**: Brief, authoritative citation
**Multiple Authorities**: Use semicolon (`;`) to separate multiple authorities when an entity has truly multiple authorizing sources

**Standard Examples:**
```yaml
Charter Entity: "NYC Charter § 2801"
Admin Code Entity: "NYC Admin. Code § 21-101"
Executive Order Entity: "NYC Executive Order 1 (2019)"
State Mandated: "NY Educ. Law § 2590-h"
Multiple Authorities: "NYC Charter § 738; NYS L.1969, c.1016 (\"Health and Hospitals Corporation Act\")"
```

**Local Law Citation Guidance:**

**General Rule: Prefer Codified Citations Over Local Law Numbers**

For v1 of NYCGO, **do not systematically include Local Law citations** if you already have a clean Charter/Admin Code reference.

**❌ AVOID:**
```yaml
authorizing_authority: "NYC Charter § 1301; Local Law 38 of 2012"
# Unnecessary - Charter citation is sufficient
```

**✅ PREFER:**
```yaml
authorizing_authority: "NYC Charter § 1301"
# Clean, codified citation is sufficient
```

**When to Include Local Law in authorizing_authority:**

1. **No codified citation exists** - Entity is only referenced in Local Law, not yet codified:
   ```yaml
   authorizing_authority: "Local Law 38 of 2012"
   ```

2. **Entity defined by Local Law itself** - Temporary task force or time-limited entity created by specific Local Law:
   ```yaml
   authorizing_authority: "Local Law 12 of 2023"
   # OR if amended:
   authorizing_authority: "Local Law 12 of 2023 (as amended by Local Law 45 of 2024)"
   ```

**Why Keep It Simple:**
- Most users just need the codified hook (Charter/Admin Code)
- Consistency is hard if you go all-in on Local Laws (gaps, multiple LLs amending same thing)
- You can always add `authorizing_local_law` and `authorizing_local_law_url` fields later without breaking current semantics
- Avoids mix of records with rich legislative history and others with nothing (feels incomplete)

**Summary Rules:**
- **Usually**: Only current codified authority (Charter or Admin Code), e.g., `"NYC Charter § 1301"`
- **Rare multi-authority cases**: Semicolon-separated, e.g., `"NYC Charter § 738; NYS L.1969, c.1016 (\"Health and Hospitals Corporation Act\")"`
- **Use Local Law citations**: Only when there is no stable codified cite

#### For authorizing_url Field
**Format**: Direct link to authorizing document
**CRITICAL RULE: Exactly ONE URL per row**

The `authorizing_url` field should contain **exactly one canonical URL** per row, representing the primary legal authority. This keeps the field simple and maintainable.

**URL Selection Priority:**
1. **Charter or Administrative Code section** (if available) - preferred as most stable
2. **State law URL** (if authority is state law only, no Charter/Admin Code)
3. **Local Law URL** (only if no codified citation exists)
4. **Executive Order URL** (only if no codified citation exists)

**Convention for Multiple Authorities:**

**Rule 1: Multiple Authorities in Text Field Only**
When an entity has multiple authorizing authorities, represent the multiplicity in `authorizing_authority` (the text field) using semicolon separation, but keep `authorizing_url` to a single canonical URL.

**Example - Multiple Authorities (H+H-style case):**
```yaml
authorizing_authority: "NYC Health and Hospitals Corporation Act (L.1969, c.1016); NYC Charter ch. 40"
# OR alternative format:
authorizing_authority: "NYC Charter § 738; NYS L.1969, c.1016 (\"Health and Hospitals Corporation Act\")"
authorizing_url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-738"
# Note: Only Charter URL included (canonical source), even though State law also applies
```

**Rule 2: Historical Codification (Local Law → Charter)**
When a Local Law codified into Charter/Admin Code, include only the Charter/Admin Code URL (the current, active legal authority). The historical Local Law is documented in `authorizing_authority` text field but does not need its own URL.

**Example - Historical Codification:**
```yaml
authorizing_authority: "NYC Charter § 1524-a"
# Note: Even if originally established by Local Law 38 of 2012, only Charter URL is used
authorizing_url: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-6586"
```

**Standard Examples:**
```yaml
Charter Entity: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-2801"
Admin Code Entity: "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-21101"
Executive Order Entity: "https://www1.nyc.gov/assets/home/downloads/pdf/executive-orders/2019/eo-1.pdf"
State Law Only: "https://www.nysenate.gov/legislation/laws/PBH/A1260"
```

**Decision Tree:**
- **Multiple authorities** → Represent in `authorizing_authority` text (semicolon-separated), but use single canonical URL in `authorizing_url` (prefer Charter/Admin Code)
- **Historical codification** (Local Law → Charter) → Use Charter URL only
- **Single authority** → Use single URL
- **Future expansion**: If you need to expose multiple URLs later, consider a separate `nycgo_authorities` table rather than overloading `authorizing_url`

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

## Web Research Protocol for Authorizing Authority Discovery

### Search Query Templates

#### For Charter-Mandated Entities
```yaml
Query Pattern: "[Entity Name] NYC Charter section"
Example: "Banking Commission NYC Charter section"
Alternative: "[Entity Name] established by NYC Charter"
Expected Results: 
  - Charter section numbers
  - Official NYC.gov pages citing charter authority
  - Legal research sites with charter references
```

#### For Local Law Entities
```yaml
Query Pattern: "[Entity Name] Local Law [year]"
Example: "Community Investment Advisory Board Local Law 2012"
Alternative: "[Entity Name] established Local Law"
Expected Results:
  - Legistar legislation pages
  - NYC Council documents
  - Local Law database entries
```

#### For Executive Order Entities
```yaml
Query Pattern: "[Entity Name] Executive Order [Mayor Name]"
Example: "Office of Immigrant Affairs Executive Order de Blasio"
Alternative: "[Entity Name] created by Executive Order"
Expected Results:
  - NYC.gov Executive Orders archive
  - Mayor's office press releases
  - Agency "About" pages citing EO
```

#### For Administrative Code Entities
```yaml
Query Pattern: "[Entity Name] Administrative Code"
Example: "Human Rights Commission Administrative Code"
Alternative: "[Entity Name] NYC Admin Code section"
Expected Results:
  - Administrative Code citations
  - Agency enabling legislation
  - Legal code library references
```

### Search Result Evaluation Criteria

#### High Confidence Sources (Use Directly)
1. **Official NYC.gov pages** - Agency "About" pages, official descriptions
2. **NYC Charter/Code Library** - codelibrary.amlegal.com with specific sections
3. **Legistar** - NYC Council legislation database
4. **Executive Orders Archive** - nyc.gov official EO repository
5. **DORIS Government Publications Portal** - [https://a860-gpp.nyc.gov](https://a860-gpp.nyc.gov/collections/zw12z528p?locale=en) - Official agency reports and mandated publications that cite legal authorities

#### Medium Confidence Sources (Verify Against Primary)
1. **News articles** - Recent reporting on entity creation/changes
2. **Academic papers** - Legal or policy research citing authorities
3. **Wikipedia** - Good starting point, but always verify primary source

#### Low Confidence Sources (Use Only as Leads)
1. **Blog posts** - May contain errors
2. **Third-party legal sites** - May be outdated
3. **Social media** - Use only to find official sources

### Citation Extraction Workflow

#### Step 1: Initial Search
1. Run primary search query using templates above
2. Review first 5-10 results for relevant information
3. Look for specific section numbers, law citations, EO numbers

#### Step 2: Citation Identification
```yaml
What to Extract:
  - Charter section numbers: "§ 1524", "Section 2801"
  - Local Law citations: "Local Law 38 of 2012", "LL 2012/038"
  - Executive Order references: "Executive Order 16 (2014)", "EO 2014-16"
  - Administrative Code: "Admin Code § 21-101", "§ 8-101"
  
Red Flags:
  - Vague references: "established by Charter" (need section number)
  - Outdated citations: Check if entity still exists under same authority
  - Conflicting information: Multiple sources cite different authorities
```

#### Step 3: URL Discovery
```yaml
For Charter Citations:
  - Format: https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-[section]
  - ⚠️ CRITICAL: Charter section numbers (e.g., § 1524) do NOT directly map to URL numbers (e.g., 0-0-0-6715)
  - The URL number is an internal reference number, not the section number
  - You MUST verify the URL content matches the section number cited
  
  Verification Steps:
  1. Find the Charter section number (e.g., "§ 1524")
  2. Search codelibrary.amlegal.com for that specific section number
  3. Click through to find the correct URL
  4. Verify the URL content actually shows the section number you're citing
  5. Check that the entity name appears in or near that section
  
  Example:
  - Citation: "NYC Charter § 1524" (Banking Commission)
  - Search: Navigate to Charter and find section 1524
  - Verify: URL should show section 1524 and mention "Banking Commission"
  - Correct URL: https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-6715
  - ❌ WRONG: Using URL from a different section (e.g., 0-0-0-6584) even if it mentions banking
  
For Local Laws:
  - Search Legistar: https://legistar.council.nyc.gov
  - Or: https://intro.nyc/local-laws/[year]-[number]
  
For Executive Orders:
  - Format: https://www.nyc.gov/assets/home/downloads/pdf/executive-orders/[year]/eo-[number].pdf
  - Verify year and number match citation
  
For DORIS Government Publications:
  - Search portal: https://a860-gpp.nyc.gov/collections/zw12z528p?locale=en
  - Use full-text search with entity name and "authority" or "charter" or "local law"
  - Agency reports often cite legal foundations
```

#### Step 4: Validation Checklist
Before adding to dataset, verify:
- [ ] Citation format matches standards (see Citation Formatting Guidelines)
- [ ] URL is accessible and points to correct document
- [ ] **For Charter citations: URL content shows the exact section number cited (e.g., if citing § 1524, verify the URL page displays "§ 1524" or "Section 1524")**
- [ ] **For Charter citations: Entity name appears in or near the cited section on the URL page**
- [ ] Section number matches entity description
- [ ] Multiple sources confirm same authority (when possible)
- [ ] No conflicting authorities found
- [ ] Citation is current (not superseded by newer law)
- [ ] **Cross-check: If multiple Charter sections mention similar topics, verify you're using the correct one for this specific entity**

### Common Research Patterns

#### Pattern 1: Entity Name + "established by"
```yaml
Search: "[Entity Name] established by"
Use Case: General discovery when authority type unknown
Example: "Sustainability Advisory Board established by"
Expected: Multiple results showing charter sections, local laws, or EOs
```

#### Pattern 2: Entity Name + "legal authority"
```yaml
Search: "[Entity Name] legal authority"
Use Case: Finding enabling legislation
Example: "Technology Development Corporation legal authority"
Expected: Legal documents, agency pages, research papers
```

#### Pattern 3: Entity Name + site:nyc.gov
```yaml
Search: "[Entity Name] site:nyc.gov"
Use Case: Limiting to official NYC sources
Example: "Community Investment Advisory Board site:nyc.gov"
Expected: Official agency pages, charter references, EO archives
```

#### Pattern 4: Entity Name + "charter section" OR "local law"
```yaml
Search: "[Entity Name] (charter section OR local law)"
Use Case: Finding specific legal citations
Example: "Banking Commission (charter section OR local law)"
Expected: Specific section numbers and law citations
```

#### Pattern 5: Entity Name + site:a860-gpp.nyc.gov
```yaml
Search: "[Entity Name] site:a860-gpp.nyc.gov"
Use Case: Finding agency reports that cite legal authority
Example: "Community Investment Advisory Board site:a860-gpp.nyc.gov"
Expected: Official agency reports, mandated reports, publications citing legal foundations
```

### Research Documentation Template

When documenting research findings, use this format:

```yaml
Entity: [Name]
RecordID: [if exists]

Research Date: [YYYY-MM-DD]
Search Queries Used:
  - "[query 1]"
  - "[query 2]"

Findings:
  authorizing_authority: "[citation]"
  authorizing_url: "[url]"
  authorizing_authority_type: "[type]"
  
Sources Consulted:
  - [Source 1]: [URL] - [What it said]
  - [Source 2]: [URL] - [What it said]
  
Confidence Level: High | Medium | Low
Validation Notes: [Any concerns or follow-up needed]
```

### Integration with Manual Validation

**Before Adding to Edits File:**
1. Extract citation from search results
2. Format according to citation standards
3. **Verify URL accessibility** (see URL Validation Requirements below)
4. **For Charter citations: CRITICALLY verify URL content matches section number** - Open the URL and confirm:
   - The page displays the exact section number cited (e.g., if citing § 1524, page must show "§ 1524" or "Section 1524")
   - The entity name appears in that section or nearby
   - You're not using a URL from a different section that happens to mention similar topics
5. **Check evidence URLs** cited in reason fields for accessibility
6. Cross-check with at least one additional source
7. Document research in reason field of edits CSV

**Evidence URL Validation Checklist:**
- [ ] Test each URL with HTTP request (check status code)
- [ ] Verify URL returns 200 OK or follow redirects to verify final destination
- [ ] If URL returns 301/302, verify redirect destination is correct content
- [ ] If URL returns 404/403/500+, find alternative source or remove URL
- [ ] Ensure URL points to correct document/content referenced in reason field
- [ ] Prefer stable/permanent URLs over dynamic or session-based URLs
- [ ] Document any URL issues in reason field if alternative not available
- [ ] **Prefer single URL** - Only use multiple URLs (pipe-separated `|`) when truly necessary

**Evidence URL: Single vs. Multiple URLs**

**General Rule: Prefer Single URL for Usability**

The `evidence_url` field supports multiple URLs separated by pipe (`|`), but **prefer single URLs** for better usability and clarity.

**✅ Use Single URL When:**
- One source provides sufficient evidence
- Entity is codified into Charter/Admin Code (use Charter URL only, not Local Law URL)
- One canonical source exists (prefer Charter/Admin Code over Local Law)

**Example (Single URL - Preferred):**
```csv
record_id,field_name,evidence_url
100430,authorizing_authority,https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-6574
```

**✅ Use Multiple URLs Only When:**
- Multiple **independent** sources provide different types of evidence
- Sources are not redundant (e.g., one doesn't codify into another)
- Each URL provides unique, non-overlapping evidence

**Example (Multiple URLs - When Appropriate):**
```csv
record_id,field_name,evidence_url
NEW,operational_status,https://charter-url.com | https://agency-report-url.com
# Only if Charter URL provides legal status AND agency report provides operational evidence
```

**❌ Avoid Multiple URLs When:**
- One source codifies into another (e.g., Local Law → Charter)
- URLs are redundant or overlapping
- Single canonical source exists

**Example (Avoid - Redundant URLs):**
```csv
# ❌ BAD: Local Law codified into Charter - use Charter URL only
NEW,name,https://charter-url.com | https://local-law-url.com

# ✅ GOOD: Use Charter URL only
NEW,name,https://charter-url.com
```

**Example Edits File Entry (with validated URLs):**
```csv
NEW,authorizing_authority,"Set to ""Local Law 38 of 2012; NYC Charter § 1524-a""","Research: Found via web search 'CIAB Local Law 2012'. Verified against Legistar (https://intro.nyc/local-laws/2012-38 - verified 200 OK) and Charter §1524-a (https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCcharter/0-0-0-6586 - verified 200 OK). Both sources confirm establishment."
```

**Example Edits File Entry (with problematic URL):**
```csv
NEW,name,"Set to ""Technology Development Corporation""","Add new entity. TDC was a Type C not-for-profit component unit created around 2012. Evidence: TDC 2016 Financial Statements: https://comptroller.nyc.gov/wp-content/uploads/2016/12/TDC-Financial-Statements-6-30-16.pdf (verified 200 OK) | Audit Committee docs: https://www.nycauditcommittee.org/meetings/2017/06/28/TDC-2017-Financial-Plan-and-Four-Year-Financial-Plan-Update (returns 301 redirect - URL may be outdated, verify redirect destination)"
```

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

#### Incorrect Charter Section URLs
```yaml
ERROR: Using wrong Charter section URL
  - Problem: Charter section numbers (e.g., § 1524) don't directly map to URL numbers (e.g., 0-0-0-6715)
  - Example Error: Citing "NYC Charter § 1524" but using URL for section 1524-a (0-0-0-6584) instead of section 1524 (0-0-0-6715)
  - Prevention: Always open the URL and verify it shows the exact section number cited
  - Verification: Check that the URL page displays the section number (e.g., "§ 1524") and mentions the entity name

CORRECT Workflow:
  1. Find Charter section number (e.g., "§ 1524")
  2. Navigate to codelibrary.amlegal.com Charter
  3. Search for or navigate to section 1524
  4. Copy the URL from that specific section page
  5. Verify: Open URL and confirm it shows "§ 1524" and mentions the entity
  6. Use that exact URL in evidence_url field

❌ WRONG: Using URL from a different section that happens to mention similar topics
✅ CORRECT: Using URL that displays the exact section number cited
```

#### URL Format Issues
```yaml
INCORRECT: HTTP instead of HTTPS
CORRECT: Use HTTPS when available

INCORRECT: Generic page instead of specific section
CORRECT: Link to specific section when possible

INCORRECT: Outdated or broken links (404, 500+)
CORRECT: Verify URL accessibility before inclusion; test with HTTP request

INCORRECT: URLs that redirect (301/302) without verifying destination
CORRECT: Follow redirects to verify final destination is correct content

INCORRECT: Including URLs in evidence without testing accessibility
CORRECT: Test all evidence URLs and document status (200 OK, redirect, etc.)

INCORRECT: Using session-based or dynamic URLs that expire
CORRECT: Use stable/permanent URLs (permalinks) when available
```

#### Evidence URL Validation Best Practices
```yaml
BEFORE including URL in reason/evidence field:
1. Test URL with curl or HTTP request tool
2. Check HTTP status code:
   - 200 OK: ✅ Safe to use
   - 301/302: ⚠️ Follow redirect, verify destination, update URL if needed
   - 404: ❌ Find alternative source or remove URL
   - 403: ❌ Find public alternative
   - 500+: ❌ Verify before using
3. Verify URL content matches what's referenced in reason field
4. Document URL status in reason field if issues found

Example reason field with URL validation:
"Evidence: Charter §1524 (https://codelibrary.amlegal.com/... - verified 200 OK) | 
DOF page (https://www.nyc.gov/... - verified 200 OK) | 
Old URL (https://example.com/old - returns 404, removed)"
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
