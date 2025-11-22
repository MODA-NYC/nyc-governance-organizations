# Phase I Pipeline Documentation

## Overview

This document describes the Phase I pipeline workflow for the NYC Governance Organizations dataset. Phase I represents the initial stable release with v1.0.0 as the baseline (released October 7, 2024) and v1.1.1 as the latest release (released November 21, 2024).

**Version Context:**
- **Baseline**: v1.0.0 (October 7, 2024)
- **Latest Release**: v1.1.1 (November 21, 2024)
- **Schema**: 38 golden dataset fields, 16 public export fields
- **RecordID Format**: `NYC_GOID_XXXXXX` (e.g., `NYC_GOID_000318`)
- **Entity Count**: 433

## Phase I Schema

### Golden Dataset Fields (38 total)

The golden dataset contains all internal fields used for data management, including source tracking fields and operational metadata.

**Core Identity Fields:**
- `RecordID` - Stable internal identifier (format: `NYC_GOID_XXXXXX`)
- `Name` - Official/preferred name
- `NameAlphabetized` - Name normalized for sorting
- `OperationalStatus` - Current status (Active, Inactive, Dissolved, etc.)
- `OrganizationType` - Category classification

**Descriptive Fields:**
- `Description` - Detailed description
- `URL` - Official website URL
- `AlternateOrFormerNames` - Other names seen in sources
- `Acronym` - Official acronym
- `AlternateOrFormerAcronyms` - Other acronyms
- `Notes` - Additional context

**Budget and Data Fields:**
- `BudgetCode` - Budget code identifier
- `OpenDatasetsURL` - Link to NYC Open Data datasets
- `FoundingYear` - Year organization was founded

**Principal Officer Fields:**
- `PrincipalOfficerName` - Full name (legacy)
- `PrincipalOfficerFullName` - Full name
- `PrincipalOfficerGivenName` - Given (first) name
- `PrincipalOfficerMiddleNameOrInitial` - Middle name or initial
- `PrincipalOfficerFamilyName` - Family (last) name
- `PrincipalOfficerSuffix` - Name suffix (Jr., Sr., III, etc.)
- `PrincipalOfficerTitle` - Title
- `PrincipalOfficerContactURL` - Profile/contact page URL

**Organizational Relationships:**
- `ReportsTo` - Reporting/administrative/oversight relationship
- `InOrgChart` - Flag for citywide org chart inclusion
- `ReportingNotes` - Notes about reporting relationships

**Source Tracking Fields (10 fields):**
- `InstanceOf`
- `Name - NYC.gov Agency List`
- `Name - NYC.gov Mayor's Office`
- `Name - NYC Open Data Portal`
- `Name - ODA`
- `Name - CPO`
- `Name - WeGov`
- `Name - Greenbook`
- `Name - Checkbook`
- `Name - HOO`
- `Name - Ops`
- `NYC.gov Agency Directory`
- `Jan 2025 Org Chart`

### Public Export Fields (16 fields, snake_case)

The public export includes a curated subset of fields, converted to snake_case:

1. `record_id`
2. `name`
3. `name_alphabetized`
4. `operational_status`
5. `organization_type`
6. `url`
7. `alternate_or_former_names`
8. `acronym`
9. `alternate_or_former_acronyms`
10. `principal_officer_full_name`
11. `principal_officer_first_name`
12. `principal_officer_last_name`
13. `principal_officer_title`
14. `principal_officer_contact_url`
15. `reports_to`
16. `in_org_chart`

**Additional Computed Field:**
- `listed_in_nyc_gov_agency_directory` - Computed based on organization type and other criteria

## Pipeline Workflow

### Overview

The Phase I pipeline processes a golden dataset CSV, applies global rules and QA edits, and produces two outputs:
1. **Golden Dataset** - Full versioned copy with all 38 fields
2. **Published Dataset** - Public-facing export with 16 fields (plus computed field)

### Entry Points

#### 1. Main Pipeline Orchestrator

**Script**: `scripts/pipeline/run_pipeline.py`

**Purpose**: End-to-end pipeline execution

**Usage**:
```bash
python scripts/pipeline/run_pipeline.py \
  --golden data/input/golden_dataset.csv \
  --qa data/input/qa_edits.csv \
  --changed-by "operator-name" \
  [--run-dir data/audit/runs/<run_id>] \
  [--previous-export data/published/latest/NYCGovernanceOrganizations_latest.csv]
```

**Key Arguments**:
- `--golden` - Path to golden dataset CSV (required)
- `--qa` - Path to QA edits CSV (can be specified multiple times)
- `--changed-by` - User or system applying changes (required)
- `--operator` - Operator for changelog attribution (optional)
- `--run-dir` - Explicit run directory (optional, defaults to `data/audit/runs/<run_id>`)
- `--previous-export` - Previous published dataset for changelog comparison (optional)
- `--run-id` - Explicit run identifier (optional, auto-generated if omitted)
- `--descriptor` - Descriptor appended to run ID (optional)

**Outputs**:
- `run_dir/outputs/golden_pre-release.csv` - Full golden dataset
- `run_dir/outputs/published_pre-release.csv` - Public export
- `run_dir/outputs/run_changelog.csv` - Per-run changelog
- `run_dir/outputs/run_summary.json` - Summary metadata

#### 2. Export Script (Legacy/Standalone)

**Script**: `scripts/process/export_dataset.py`

**Purpose**: Process and export datasets (can be used standalone)

**Usage**:
```bash
python scripts/process/export_dataset.py \
  --input_csv data/working/dataset.csv \
  --output_golden data/published/golden_v1.0.0.csv \
  --output_published data/published/public_v1.0.0.csv \
  [--run-dir data/audit/runs/<run_id>] \
  [--run-id <run_id>] \
  [--operator <name>] \
  [--previous-export data/published/previous.csv]
```

## Pipeline Steps

### 1. Load Golden Dataset
- Read CSV with all 38 fields
- Preserve all source tracking fields
- Maintain RecordID format: `NYC_GOID_XXXXXX`

### 2. Apply Global Rules
- **File**: `src/nycgo_pipeline/global_rules.py`
- Applies data quality rules and transformations
- Validates field formats and relationships
- Ensures data consistency

### 3. Apply QA Edits
- Loads QA edit CSV files
- Applies edits to specific records/fields
- Tracks changes in changelog

### 4. Generate Public Export
- Filters records (Active status, in org chart or Ops list)
- Selects 16 public export fields
- Converts field names to snake_case
- Computes `listed_in_nyc_gov_agency_directory` field
- Applies directory inclusion logic

### 5. Generate Changelog
- Compares with previous export (if provided)
- Tracks field changes
- Documents directory field changes
- Records run metadata

## RecordID Format

**Phase I Format**: `NYC_GOID_XXXXXX`

- Prefix: `NYC_GOID_`
- Format: 6-digit zero-padded number
- Examples:
  - `NYC_GOID_000022`
  - `NYC_GOID_000318`
  - `NYC_GOID_100026`

**Characteristics**:
- Stable and immutable identifier
- Primary key for all records
- Used in crosswalks and relationships
- Referenced in `ReportsTo` field

## ReportsTo Field

**Purpose**: Captures reporting/administrative/oversight relationships

**Usage in Phase I**:
- Contains entity names (not RecordIDs)
- Can represent:
  - Org chart/political oversight relationships
  - Parent-child governance relationships
  - Legal reporting relationships

**Examples**:
- "Mayor's Office"
- "Department of Finance"
- "NYC Health + Hospitals"

**Note**: In Phase II, this field is retired and replaced by more specific relationship fields (`org_chart_oversight_record_id`, `parent_organization_record_id`).

## Directory Inclusion Logic

The `listed_in_nyc_gov_agency_directory` field is computed based on:

1. **Blanket Gatekeeper Rules** (must pass ALL):
   - Must be Active (`operational_status = "Active"`)
   - URL must NOT contain state "ny.gov" (city "nyc.gov" is OK)
   - Must have at least one contact field (URL, officer name, or officer contact URL)

2. **Organization Type Specific Rules**:
   - **Mayoral Agency**: All included
   - **Mayoral Office**: All included
   - **Division**: Only if `in_org_chart = True`
   - **Elected Office**: All included
   - **Advisory or Regulatory Organization**: Included if has nyc.gov URL with index.page
   - **Nonprofit Organization**: Included if in exemption list
   - **Public Benefit or Development Organization**: Included if `in_org_chart = True` or has ops name
   - Other types: Case-by-case evaluation

3. **Manual Overrides**: Can force TRUE or FALSE for specific RecordIDs

## How to Generate Phase I Outputs from Snapshot

### Using Git Snapshot

1. **Checkout the snapshot branch**:
   ```bash
   git checkout phase-i-pipeline-snapshot
   ```

2. **Or checkout the tagged version**:
   ```bash
   git checkout phase-i-pipeline-v1.1.1-final
   ```

3. **Run the pipeline**:
   ```bash
   python scripts/pipeline/run_pipeline.py \
     --golden data/input/golden_dataset.csv \
     --qa data/input/qa_edits.csv \
     --changed-by "operator-name"
   ```

4. **Return to development branch**:
   ```bash
   git checkout dev
   ```

### Using Phase I Export Bridge Tool

During Phase II development, use the bridge tool to generate Phase I-compatible exports:

```bash
python scripts/pipeline/export_phase_i.py \
  --input data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
  --output data/published/phase_i_compatible.csv \
  --crosswalk data/crosswalk/recordid_migration.csv
```

## Example Commands

### Full Pipeline Run
```bash
# Generate run ID automatically
python scripts/pipeline/run_pipeline.py \
  --golden data/input/NYCGO_golden_dataset_v1.1.0.csv \
  --qa data/input/NYCGO_edits_to_make_20251121.csv \
  --changed-by "nathanstorey" \
  --previous-export data/published/latest/NYCGovernanceOrganizations_latest.csv
```

### With Explicit Run ID
```bash
python scripts/pipeline/run_pipeline.py \
  --golden data/input/golden_dataset.csv \
  --qa data/input/qa_edits.csv \
  --changed-by "operator" \
  --run-id "20251122-1200_qa-pass" \
  --descriptor "qa-pass"
```

### Standalone Export
```bash
python scripts/process/export_dataset.py \
  --input_csv data/working/dataset.csv \
  --output_golden data/published/golden_v1.0.0.csv \
  --output_published data/published/public_v1.0.0.csv
```

## Key Files

### Pipeline Code
- `src/nycgo_pipeline/pipeline.py` - Main orchestration logic
- `src/nycgo_pipeline/global_rules.py` - Global validation rules
- `src/nycgo_pipeline/export.py` - Export utilities
- `src/nycgo_pipeline/qa_edits.py` - QA edit processing
- `scripts/pipeline/run_pipeline.py` - CLI entry point
- `scripts/process/export_dataset.py` - Export script

### Documentation
- `docs/PHASE_I_SCHEMA.md` - Full schema documentation
- `docs/PHASE_I_SCHEMA_FIELDS.txt` - Field list reference
- `docs/run_artifacts.md` - Run artifacts specification

### Data Files
- `data/published/latest/NYCGO_golden_dataset_v1.1.1.csv` - Latest golden dataset
- `data/published/latest/NYCGovernanceOrganizations_v1.1.1.csv` - Latest public export
- `data/changelog.csv` - Append-only changelog

## Release Artifacts

### v1.0.0 (Baseline - October 7, 2024)
- Initial stable release
- 38 golden fields, 16 public export fields
- 433 entities

### v1.1.1 (Latest - November 21, 2024)
- Patch release with name fixes
- Same schema as v1.0.0
- Run ID: `20251122-0058_v1.1.1-name-fix`

## Migration to Phase II

When migrating to Phase II:
- RecordID format changes: `NYC_GOID_XXXXXX` → `100318` (6-digit numeric)
- `ReportsTo` field is retired
- 9 new fields added (governance, legal authority, appointments)
- See `PHASE_II_PLAN.md` and `SCHEMA_PROPOSAL_SUMMARY.md` for details

## References

- **Phase I Schema**: [`docs/PHASE_I_SCHEMA.md`](PHASE_I_SCHEMA.md)
- **Phase I Fields**: [`docs/PHASE_I_SCHEMA_FIELDS.txt`](PHASE_I_SCHEMA_FIELDS.txt)
- **Phase II Plan**: [`../PHASE_II_PLAN.md`](../PHASE_II_PLAN.md)
- **Schema Comparison**: [`docs/SCHEMA_VERSION_COMPARISON.md`](SCHEMA_VERSION_COMPARISON.md)
- **Run Artifacts Spec**: [`docs/run_artifacts.md`](run_artifacts.md)

---

**Last Updated**: November 2024
**Status**: Phase I pipeline preserved in git snapshot `phase-i-pipeline-v1.1.1-final`
