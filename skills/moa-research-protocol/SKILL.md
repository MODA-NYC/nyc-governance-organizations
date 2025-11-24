# Mayor's Office of Appointments Research Protocol Skill

This skill provides specialized methodology for researching and validating entities within the Mayor's Office of Appointments universe, ensuring comprehensive coverage and accurate appointment authority documentation.

## Purpose

The MOA Research Protocol skill guides systematic research into NYC governance entities where the Mayor has appointment authority, supporting Phase II objectives of:

- **Complete MOA Universe Coverage**: Ensuring no entities are missed from Mayor's appointment scope
- **Appointment Authority Validation**: Accurate documentation of appointment mechanisms
- **Source Verification**: Systematic validation against official NYC sources
- **Data Quality Assurance**: Comprehensive quality checks for MOA-related data
- **Cross-Reference Integration**: Coordination between multiple data sources

## Core Research Methodology

### Phase 1: Universe Definition and Scope

#### Primary Sources for MOA Universe
1. **NYC.gov Appointments Page**: https://www.nyc.gov/content/appointments/pages/boards-commissions
   - Official listing of boards and commissions with mayoral appointments
   - Primary source for current appointment opportunities
   - Updated regularly by Mayor's Office

2. **Mayor's Office of Appointments Internal Records**
   - Direct communication with MOA staff when possible
   - Official appointment lists and tracking documents
   - Historical appointment records

3. **NYC Charter Provisions**
   - Charter-mandated boards and commissions
   - Statutory appointment requirements
   - Constitutional appointment authorities

4. **Administrative Code References**
   - Code-established entities with mayoral appointments
   - Regulatory bodies with appointment provisions
   - Operational entities under mayoral authority

#### Secondary Validation Sources
1. **Executive Orders**: Mayor-created entities and appointment modifications
2. **Local Laws**: Council-created entities with mayoral appointment roles
3. **Agency Websites**: Current board/commission membership listings
4. **Budget Documents**: Entities receiving city funding with mayoral oversight

### Phase 2: Data Collection Protocol

#### NYC.gov Appointments Page Scraping

**Target URL**: https://www.nyc.gov/content/appointments/pages/boards-commissions

**Data Collection Standards**:
```yaml
Required Fields:
  - entity_name: Official name as listed
  - description: Function description from page
  - url: Direct link to entity page (when available)
  - appointment_details: Specific appointment information provided

Optional Fields:
  - application_deadline: If specified
  - term_length: If specified
  - meeting_frequency: If specified
  - compensation: If specified

Quality Standards:
  - Exact text capture (no paraphrasing)
  - Preserve official formatting and terminology
  - Note any inconsistencies or unclear information
  - Document scraping date and page version
```

**Scraping Best Practices**:
- Respect rate limits (2-second delays between requests)
- Handle dynamic content loading appropriately
- Verify page structure hasn't changed before scraping
- Capture full page content for later verification
- Document any access limitations or restrictions

#### Cross-Reference Validation Protocol

**Step 1: Entity Matching**
1. Match scraped entities against existing NYCGO dataset
2. Identify exact matches, partial matches, and new entities
3. Create crosswalk mapping between sources
4. Flag entities for manual review when matching is uncertain

**Step 2: Appointment Authority Verification**
1. Research specific appointment mechanisms for each entity
2. Verify Mayor's role (direct appointment, confirmation, etc.)
3. Document any shared appointment authority with other officials
4. Validate against authoritative legal sources

**Step 3: Gap Analysis**
1. Identify entities in NYCGO dataset not on appointments page
2. Research whether entities should be included in MOA scope
3. Identify entities on appointments page not in NYCGO dataset
4. Prioritize new entity additions based on significance

### Phase 3: Entity Verification and Validation

#### Appointment Mechanism Research

**Research Questions for Each Entity**:
1. **Who appoints?** (Mayor alone, Mayor with confirmation, shared authority)
2. **How many positions?** (Total board size, mayoral appointments)
3. **What terms?** (Length, staggered, renewable)
4. **What qualifications?** (Required background, geographic requirements)
5. **What process?** (Application, nomination, confirmation requirements)

**Documentation Standards**:
```yaml
Appointment Summary Format:
  mayor_appointments: Number of positions Mayor appoints
  total_positions: Total board/commission size
  appointment_type: "Direct" | "With Confirmation" | "Shared Authority"
  confirming_body: Entity that confirms (if applicable)
  term_length: Duration of appointments
  term_limits: Maximum terms/tenure limits
  qualifications: Required qualifications or restrictions
  selection_process: Application/nomination process description

Example:
  mayor_appointments: 5
  total_positions: 7
  appointment_type: "With Confirmation"
  confirming_body: "City Council"
  term_length: "3 years"
  term_limits: "2 consecutive terms"
  qualifications: "NYC resident, relevant professional experience"
  selection_process: "Open application with public interview"
```

#### Source Documentation Requirements

**Primary Source Hierarchy**:
1. **NYC Charter**: Definitive for charter-mandated entities
2. **Administrative Code**: Authoritative for code-established entities
3. **Local Laws**: Current legal requirements
4. **Executive Orders**: Recent modifications or creations
5. **Agency Rules**: Operational appointment procedures

**Documentation Standards**:
- Always cite specific section numbers
- Include direct quotes for appointment language
- Note effective dates for any recent changes
- Document conflicting information between sources
- Maintain source URL or legal citation for verification

### Phase 4: Quality Assurance Framework

#### Coverage Validation Checklist

**MOA Universe Completeness**:
- [ ] All entities from NYC.gov appointments page researched
- [ ] All charter-mandated appointment authorities identified
- [ ] All code-established entities with mayoral appointments included
- [ ] Recent executive orders reviewed for new entities
- [ ] Historical entities evaluated for current status

**Data Quality Validation**:
- [ ] Appointment mechanisms verified against primary sources
- [ ] Cross-references validated between sources
- [ ] Entity names standardized against official usage
- [ ] Descriptions verified against authoritative sources
- [ ] URLs tested and verified as accessible

**Relationship Accuracy**:
- [ ] Legal reporting relationships distinguished from appointment authority
- [ ] Administrative oversight documented separately
- [ ] Shared appointment authorities properly attributed
- [ ] Confirmation requirements accurately documented

#### Error Detection and Resolution

**Common Data Quality Issues**:

1. **Name Variations**:
   - Problem: Same entity listed with different names across sources
   - Solution: Establish official name hierarchy, document variants
   - Example: "Landmarks Preservation Commission" vs "LPC" vs "Landmarks Commission"

2. **Outdated Information**:
   - Problem: Sources showing different current status
   - Solution: Prioritize most recent official sources, document changes
   - Example: Entity dissolved by recent executive order but still on website

3. **Appointment Authority Conflicts**:
   - Problem: Different sources showing different appointment mechanisms
   - Solution: Research legal hierarchy, cite most authoritative source
   - Example: Charter vs Administrative Code vs Executive Order precedence

4. **Scope Boundary Issues**:
   - Problem: Uncertainty about MOA scope inclusion
   - Solution: Apply consistent criteria, document edge cases
   - Example: Entities with advisory vs operational roles

### Phase 5: Integration and Crosswalk Development

#### MOA-NYCGO Dataset Integration

**Integration Workflow**:
1. **Entity Matching**: Link MOA entities to existing NYCGO records
2. **New Entity Addition**: Add previously unidentified MOA entities
3. **Data Enhancement**: Populate appointment-specific fields
4. **Quality Validation**: Cross-check enhanced data
5. **Crosswalk Creation**: Maintain mapping between sources

**Crosswalk Schema**:
```yaml
Crosswalk Fields:
  nycgo_entity_id: Internal NYCGO identifier
  moa_listing_name: Name as appears on appointments page
  moa_page_url: Direct URL to entity on appointments page
  official_name: Authoritative entity name
  match_confidence: "Exact" | "High" | "Medium" | "Manual Review"
  appointment_authority_verified: Boolean
  last_verification_date: Date of last validation
  notes: Any special considerations or issues
```

#### Data Validation Rules

**Mandatory Validations**:
- Every MOA entity must have appointment mechanism documented
- Every appointment mechanism must cite authoritative source
- Every entity must be classified by type and function
- Every new entity must be verified against multiple sources

**Quality Metrics**:
- **Coverage Rate**: % of known MOA entities included in dataset
- **Verification Rate**: % of entities with primary source validation
- **Currency Rate**: % of entities with recent validation (within 6 months)
- **Accuracy Rate**: % of spot-checked entities with correct information

## Research Tools and Techniques

### Web Research Strategies

#### NYC.gov Navigation
- Use site search with appointment-related terms
- Navigate agency pages for board/commission listings
- Check "About" sections for governance structure
- Review meeting calendars for board activity

#### Legal Research Approaches
- Search Charter and Administrative Code for appointment terms
- Review recent Local Laws for entity modifications
- Check Executive Order database for new entities
- Search agency rules for appointment procedures

#### Cross-Validation Techniques
- Compare multiple official sources for consistency
- Check news reports for recent changes
- Review budget documents for funding validation
- Contact agency public information officers when needed

### Data Management Standards

#### Research Documentation
- Maintain research notes for each entity
- Document source consultation date and findings
- Note any unresolved questions or conflicts
- Track decision rationale for edge cases

#### Version Control
- Date-stamp all research findings
- Maintain audit trail for data changes
- Document source precedence decisions
- Track validation and verification dates

#### Quality Control
- Implement spot-checking procedures
- Cross-validate samples with multiple researchers
- Maintain feedback loop for methodology improvements
- Document and learn from research errors

## Integration with Phase II Implementation

### Schema Population Support

This research protocol directly supports Phase II schema expansion by:

1. **Authorizing Authority Research**: Systematic identification of legal foundations
2. **Appointment Summary Documentation**: Detailed appointment mechanism capture
3. **Authority URL Collection**: Direct links to authorizing documents
4. **Cross-Reference Validation**: Multi-source verification procedures

### Pipeline Integration

**Data Collection Phase**:
- MOA research feeds into entity verification
- Appointment mechanisms populate appointments_summary field
- Legal research supports authorizing_authority and authorizing_url fields

**Quality Assurance Phase**:
- MOA coverage validation ensures comprehensive scope
- Cross-reference checks validate entity accuracy
- Source verification supports data reliability

**Maintenance Phase**:
- Regular MOA page monitoring for changes
- Periodic re-validation of appointment mechanisms
- Update procedures for entity status changes

This research protocol ensures that Phase II achieves comprehensive and accurate coverage of the Mayor's Office of Appointments universe while maintaining the highest standards of data quality and source verification.
