# NYC Governance Organizations: MCP & Skills Setup
## Project-Specific Infrastructure for Phase II Implementation

This document outlines the NYC-specific setup of Model Context Protocol (MCP) servers and Claude Skills to support the Phase II schema expansion and Mayor's Office of Appointments work. This plan integrates with the general civic AI infrastructure established in the `civic-ai-tools` repository.

---

## Background & Context

**Objective**: Configure project-specific MCP servers and Claude Skills for the NYC Governance Organizations Phase II implementation, leveraging both community tools and custom NYC-specific capabilities.

**Dependencies**: This plan assumes the `civic-ai-tools` repository has been cloned to `/Users/nathanstorey/Code/civic-ai-tools/` and provides general-purpose civic AI infrastructure.

---

## Part I: Project Structure Integration

### Directory Organization

This setup integrates with the existing Code directory structure and leverages the community `civic-ai-tools` repository:

```
/Users/nathanstorey/Code/
├── civic-ai-tools/                       # 🌐 COMMUNITY INFRASTRUCTURE
│   ├── mcp-servers/                      # General-purpose MCP servers
│   ├── skills/                           # Reusable civic AI skills
│   ├── configs/                          # Template configurations
│   └── docs/                            # Community documentation
├── opengov-mcp-server/                   # ✅ YOUR EXISTING SOCRATA MCP
├── nyc-governance-organizations/         # 🏛️ THIS PROJECT
│   ├── .cursor/
│   │   └── mcp.json                     # Project MCP configuration
│   ├── skills/                          # 🆕 NYC-SPECIFIC SKILLS
│   │   ├── nyc-governance-schema/        # Schema validation & definitions
│   │   ├── moa-research-protocol/        # MOA-specific methodology
│   │   └── nyc-legal-citation/           # NYC legal document formats
│   ├── configs/                         # 🆕 PROJECT CONFIGURATIONS
│   │   ├── mcp-development.json         # Development MCP config
│   │   ├── mcp-production.json          # Production MCP config
│   │   └── security-settings.json       # Project security policies
│   └── [existing project files]
```

### Benefits of This Integrated Structure

1. **Community Leverage**: Reuse proven tools from civic-ai-tools
2. **Project Focus**: NYC-specific customizations stay in project repo
3. **Existing Investment**: Your opengov-mcp-server stays in place
4. **Version Control**: Independent evolution of general vs specific tools
5. **Contribution**: General improvements can flow back to community

---

## Part II: NYC-Specific MCP Configuration

### Phase 1: Project Setup (Week 1)

#### 1.1 Create Project Directories
- [ ] Create `skills/` directory in project root
- [ ] Create `configs/` directory for project-specific configurations
- [ ] Set up project-specific environment variables

#### 1.2 Verify Community Infrastructure
- [ ] Confirm `civic-ai-tools` is cloned to `/Users/nathanstorey/Code/civic-ai-tools/`
- [ ] Test community MCP servers are accessible
- [ ] Review community security guidelines

#### 1.3 Integrate Your Existing OpenGov MCP Server
- [ ] **Confirm location**: `/Users/nathanstorey/Code/opengov-mcp-server/`
- [ ] **Test functionality** with Socrata APIs for NYC Open Data
- [ ] **Document NYC-specific capabilities** and datasets
- [ ] **Update if needed** for Phase II requirements

### Phase 2: Community MCP Server Integration (Week 1)

#### 2.1 Data Commons MCP Server
- [ ] **Install from community setup**: Follow `civic-ai-tools/CIVIC_AI_TOOLS_SETUP.md`
- [ ] **Test NYC-relevant queries**: Demographics, budget data, census info
- [ ] **Document NYC use cases**: Borough comparisons, historical trends
- [ ] **Configure for Phase II**: Budget code research, demographic validation

#### 2.2 Playwright MCP Server
- [ ] **Install from community infrastructure**
- [ ] **Test on NYC.gov appointments page**: https://www.nyc.gov/content/appointments/pages/boards-commissions
- [ ] **Create NYC-specific scraping templates**
- [ ] **Configure for MOA data collection**

### Phase 3: NYC-Specific Skills Development (Week 2)

#### 3.1 NYC Governance Schema Skill
**Location**: `skills/nyc-governance-schema/`

**Contents**:
- Phase II schema field definitions (reports_to, org_chart_oversight, etc.)
- NYC-specific data validation rules
- Entity classification standards
- Data quality checks for NYC governance data

**Time Investment**: 3-4 hours

#### 3.2 MOA Research Protocol Skill
**Location**: `skills/moa-research-protocol/`

**Contents**:
- Mayor's Office of Appointments research methodology
- Entity verification procedures specific to NYC
- Source documentation standards for NYC government
- Quality assurance checklists for MOA data

**Time Investment**: 2-3 hours

#### 3.3 NYC Legal Citation Skill
**Location**: `skills/nyc-legal-citation/`

**Contents**:
- NYC Charter citation formatting (specific sections and amendments)
- Administrative Code reference standards
- Executive Order citation formats
- NYC-specific legal URL patterns and formatting

**Time Investment**: 1-2 hours

---

## Part III: Project Configuration

### NYC Governance Organizations MCP Configuration

The project's `.cursor/mcp.json` file integrates community tools with project-specific and existing infrastructure:

```json
{
  "servers": {
    "opengov-nyc": {
      "command": "node",
      "args": ["../opengov-mcp-server/dist/index.js"],
      "env": {
        "PORT": "10000",
        "DEFAULT_DOMAIN": "data.cityofnewyork.us"
      }
    },
    "data-commons": {
      "command": "python",
      "args": ["-m", "datacommons_mcp"],
      "env": {
        "DC_API_ROOT": "https://datacommons.org"
      }
    },
    "playwright-civic": {
      "command": "node",
      "args": ["../civic-ai-tools/mcp-servers/playwright-civic/dist/index.js"],
      "env": {
        "HEADLESS": "true",
        "TIMEOUT": "30000"
      }
    }
  },
  "skills": [
    "../civic-ai-tools/skills/opengov-mcp-companion",
    "./skills/nyc-governance-schema",
    "./skills/moa-research-protocol",
    "./skills/nyc-legal-citation",
    "../civic-ai-tools/skills/government-web-scraping",
    "../civic-ai-tools/skills/legal-document-formatting"
  ]
}
```

### Environment Configuration

Create `.env` file in project root:

```bash
# NYC-specific API keys and configuration
SOCRATA_APP_TOKEN=your_app_token_here
NYC_OPEN_DATA_DOMAIN=data.cityofnewyork.us

# Data Commons configuration
DATA_COMMONS_API_KEY=optional_for_higher_limits

# Playwright configuration for NYC sites
PLAYWRIGHT_TIMEOUT=30000
SCRAPING_DELAY=2000

# Security settings
MCP_LOG_LEVEL=info
ENABLE_AUDIT_LOGGING=true
```

---

## Part IV: NYC-Specific Implementation Timeline

### Week 1: Project Setup & Community Integration
- **Days 1-2**: Create project directories (`skills/`, `configs/`)
- **Days 3-4**: Configure integration with `civic-ai-tools` infrastructure
- **Days 5-7**: Test and document your existing OpenGov MCP server for Phase II needs

### Week 2: NYC Skills Development & MCP Testing
- **Days 1-3**: Develop NYC-specific skills (schema, MOA protocol, legal citation)
- **Days 4-5**: Set up and test Playwright MCP for NYC.gov appointments scraping
- **Days 6-7**: Integration testing of all MCP servers with NYC data sources

### Week 3: Phase II Integration & Validation
- **Days 1-3**: Configure full MCP setup for Phase II workflow
- **Days 4-5**: Test complete Phase II data collection and validation pipeline
- **Days 6-7**: Documentation and refinement for production use

---

## Part V: Success Criteria for NYC Project

### NYC-Specific Deliverables
- [ ] Project-specific skills for NYC governance data
- [ ] Integrated MCP configuration leveraging community tools
- [ ] Functional NYC.gov appointments page scraping
- [ ] Enhanced NYC Open Data access via your existing MCP server
- [ ] Demographics and budget data access via Data Commons MCP

### Phase II Integration Validation
- [ ] Schema validation working via NYC Governance Schema skill
- [ ] MOA research methodology enforced via custom skill
- [ ] Legal citation consistency via NYC Legal Citation skill
- [ ] Automated appointments data collection functional
- [ ] Budget code research capabilities operational

### Security & Documentation
- [ ] Project follows community security guidelines
- [ ] NYC-specific configurations documented
- [ ] Integration patterns documented for future projects
- [ ] All custom skills validated and tested

---

## Part VI: Phase II Benefits

Once this NYC-specific setup is complete, Phase II will benefit from:

### **Automated Data Collection**
- NYC Open Data queries via your enhanced OpenGov MCP server
- Government statistics and demographics via Data Commons MCP
- NYC.gov appointments page data via Playwright MCP

### **Consistent Methodology**
- Schema validation and data quality checks via NYC Governance Schema skill
- Research procedures standardized via MOA Research Protocol skill
- Legal citations formatted consistently via NYC Legal Citation skill

### **Enhanced Capabilities**
- Budget code research accelerated via Data Commons integration
- Cross-jurisdictional comparisons for validation
- Automated quality assurance and data verification

### **Future Scalability**
- Infrastructure can support additional NYC civic projects
- Skills can be refined and improved based on Phase II experience
- Community contributions can enhance general-purpose tools

---

## Part VII: Notes & Next Steps

### Integration Notes
- This setup leverages both community tools and project-specific customizations
- Your existing `opengov-mcp-server` remains in its current location and role
- Community tools from `civic-ai-tools` provide general civic AI capabilities
- NYC-specific skills ensure project requirements are met precisely

### Future Considerations
- Successful patterns can be contributed back to `civic-ai-tools` community
- Additional NYC projects can leverage this established infrastructure
- Skills can be continuously improved based on real-world usage in Phase II
- Security practices follow established community guidelines

### Dependencies
- Requires `civic-ai-tools` repository setup (see community documentation)
- Existing `opengov-mcp-server` must be functional and tested
- Phase II schema and requirements must be finalized
- Security and access policies must be established
