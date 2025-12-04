# Mayor's Office of Appointments Research Protocol Skill

Project-specific skill for systematic research and validation of entities within the Mayor's Office of Appointments universe.

## Purpose

This skill provides comprehensive methodology for researching NYC governance entities where the Mayor has appointment authority, ensuring complete coverage and accurate documentation for the Phase II expansion.

## Key Features

### Research Methodology
- **Systematic Data Collection**: Structured approach to MOA universe identification
- **Multi-Source Validation**: Cross-reference validation across official sources
- **Quality Assurance Framework**: Comprehensive validation and error detection
- **Documentation Standards**: Consistent source citation and evidence requirements

### Data Collection Targets
- **NYC.gov Appointments Page**: Primary source scraping and analysis
- **Legal Authority Research**: Charter, Administrative Code, and statutory validation
- **Cross-Reference Integration**: NYCGO dataset integration and gap analysis
- **Appointment Mechanism Documentation**: Detailed appointment process capture

### Quality Standards
- **Coverage Validation**: Ensuring complete MOA universe inclusion
- **Source Verification**: Primary source validation requirements
- **Data Accuracy**: Multi-source cross-validation procedures
- **Currency Maintenance**: Regular update and re-validation protocols

## Phase II Integration

### Schema Support
- Directly supports `appointments_summary` field population
- Validates `authorizing_authority` field accuracy
- Provides source URLs for `authorizing_url` field
- Ensures comprehensive entity coverage for dataset completeness

### Research Workflow
1. **Universe Definition**: Systematic identification of MOA scope
2. **Data Collection**: Structured scraping and research procedures
3. **Validation**: Multi-source verification and quality checks
4. **Integration**: NYCGO dataset enhancement and crosswalk development
5. **Maintenance**: Ongoing validation and update procedures

## Dependencies

- Works with NYC Governance Schema skill for field validation
- Integrates with Government Web Scraping skill for NYC.gov data collection
- Supports NYC Legal Citation skill for proper source documentation
- Leverages OpenGov MCP Server for NYC Open Data cross-validation
