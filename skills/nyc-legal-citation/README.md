# NYC Legal Citation Skill

Project-specific skill for proper citation and formatting of NYC legal documents, statutes, and government sources.

## Purpose

This skill ensures consistent, accurate, and professional citation of NYC legal sources, supporting Phase II requirements for proper documentation of authorizing authorities and legal foundations.

## Key Features

### Legal Source Hierarchy
- **Primary Sources**: NYC Charter, Administrative Code, Local Laws, Executive Orders
- **Secondary Sources**: NYS Laws, NYC Rules (RCNY)
- **Tertiary Sources**: Agency documents, budget materials
- **Citation Standards**: Professional legal citation formatting

### Citation Formatting
- **Standardized Formats**: Consistent citation style across all NYC legal sources
- **URL Standards**: Official government source linking with validation
- **Section References**: Proper legal section and subsection notation
- **Amendment Tracking**: Historical and current version citation

### Field Support
- **authorizing_authority Field**: Standardized citation format for legal foundations
- **authorizing_url Field**: Validated links to authoritative documents
- **Research Documentation**: Professional source citation for verification
- **Quality Assurance**: Citation accuracy validation and error correction

## Citation Standards

### Common NYC Legal Sources
```yaml
NYC Charter: "NYC Charter § [section]"
Administrative Code: "NYC Admin. Code § [title]-[section]"
Local Laws: "NYC Local Law [number] of [year]"
Executive Orders: "NYC Executive Order [number] ([year])"
State Laws: "NY [Law Code] § [section]"
```

### URL Validation
- Official government sources prioritized
- Specific section linking when available
- Accessibility and stability verification
- Alternative URL documentation when needed

## Phase II Integration

### Schema Support
- Populates `authorizing_authority` field with proper legal citations
- Provides verified URLs for `authorizing_url` field
- Ensures consistent citation style across all entities
- Validates legal source accuracy and accessibility

### Research Enhancement
- Guides systematic legal source identification
- Provides professional citation standards for documentation
- Supports source verification and validation procedures
- Enables reproducible research methodology

## Dependencies

- Integrates with NYC Governance Schema skill for field validation
- Supports MOA Research Protocol skill with proper source citation
- Leverages Legal Document Formatting skill from civic-ai-tools
- Works with Government Web Scraping skill for official document access
