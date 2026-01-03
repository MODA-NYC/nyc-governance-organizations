# NYCGO Project - Claude Code Guide

This workspace contains two related repositories for managing NYC Governance Organizations data.

> **Multi-repo setup**: If you're working with both `nyc-governance-organizations` and `nycgo-admin-ui`, create a parent folder containing both repos and copy this CLAUDE.md there. This gives Claude Code context across both repositories.
> ```
> mkdir nycgo && cd nycgo
> git clone <nyc-governance-organizations-url>
> git clone <nycgo-admin-ui-url>
> cp nyc-governance-organizations/CLAUDE.md .
> ```

## Sprint Planning

Sprint documentation lives in `nyc-governance-organizations/docs/sprints/`:

**Completed** (in `completed/` subfolder):
- `SPRINT_1.md` - Admin UI Infrastructure
- `SPRINT_2.md` - Pipeline Testing & Validation
- `SPRINT_3.md` - v1.1.2 Release Fix & Production Pipeline Test
- `SPRINT_4.md` - Edit Submission Rate Limiting
- `SPRINT_4.5.md` - Release Notes & Smart Versioning
- `SPRINT_5.md` - Data Quality & Standardization
- `SPRINT_6.md` - Directory Logic Transparency & QA (Dec 2024, released v1.6.0)

**Active/Planned** (in root folder):
- `SPRINT_7.md` - Cleanup & Technical Debt (schema docs, externalize configs, etc.)
- `PHASE_II.md` - Phase II Data Release (46-field schema, 9 new orgs - deferred indefinitely)

---

## Repository Structure

```
/nycgo/
├── nyc-governance-organizations/  # Data pipeline & golden dataset
└── nycgo-admin-ui/                # Web-based admin interface
```

Both are symlinks to the actual repos.

---

## Repository Overview

### nyc-governance-organizations (Pipeline Repo)

**Purpose**: Data pipeline for processing, validating, and publishing the NYC Governance Organizations dataset.

**Key Directories**:
- `data/input/` - Source QA edit files
- `data/published/latest/` - Single source of truth for golden datasets
- `data/audit/runs/` - Run artifacts with inputs/outputs/review
- `data/changelog.csv` - Master append-only changelog
- `src/nycgo_pipeline/` - Python pipeline package
- `scripts/pipeline/` - CLI entrypoints (run_pipeline.py, publish_run.py)
- `.github/workflows/publish-release.yml` - Automated release workflow

**Current Versions**:
- v1.6.0 - Latest published (434 records, 38 fields, snake_case column names)
- v1.2.0 - Development (443 records, 46 fields, Phase II schema - deferred)

**Pipeline Commands**:
```bash
# Run pipeline
make run-pipeline GOLDEN=... QA=... DESCRIPTOR=...

# Publish a run
make publish-run RUN_ID=... VERSION=...

# Run tests
make test
```

### nycgo-admin-ui (Admin UI Repo)

**Purpose**: Web-based interface for submitting individual organization edits.

**Key Files**:
- `js/config.js` - Configuration (data sources, editable fields, GitHub settings)
- `js/app.js` - Main application logic
- `js/data.js` - Data loading and parsing
- `pending-edits/` - Edits waiting to be processed
- `processed-edits/` - Archive of processed edits
- `scheduled-edits/` - Future-dated edits
- `.github/workflows/process-edit.yml` - Workflow to process edits

**Current Configuration** (config.js):
- Data source: GitHub raw file from `data/published/latest/NYCGO_golden_dataset_latest.csv`
- Batch review interface: `review-edits.html` for reviewing CSV uploads before commit
- Workflow mode: Check repo variables (TEST_MODE / PRODUCTION_MODE)

**⚠️ IMPORTANT: Cache-Busting for JS Changes**

When modifying any JavaScript files in `nycgo-admin-ui/js/`, you MUST update the cache-busting version in BOTH HTML files to ensure users get the new code:

1. Edit `index.html` - update all `?v=YYYYMMDD` params to today's date
2. Edit `review-edits.html` - update all `?v=YYYYMMDD` params to today's date

Example: Change `js/app.js?v=20260101` to `js/app.js?v=20260108`

Without this step, users may continue loading old cached JavaScript.

---

## Data Flow

```
User submits edit in Admin UI
        ↓
CSV file committed to nycgo-admin-ui/pending-edits/
        ↓
process-edit.yml workflow runs
        ↓
Pipeline processes edit using nyc-governance-organizations
        ↓
Output committed to target branch (admin-ui-test/test/main)
        ↓
publish-release.yml creates GitHub release (if test/prod mode)
        ↓
Artifacts available in data/published/latest/
```

---

## Edit Format

Edits use a CSV format with these columns:
```
record_id,record_name,field_name,action,justification,evidence_url
```

**Actions**:
- `direct_set` - Set field to specific value
- `append_to_list` - Append to semicolon-separated list
- `remove_from_list` - Remove from list
- `generate_recordid` - Auto-generate new RecordID

---

## Workflow Modes

The process-edit.yml workflow has three modes (controlled by repo variables):

| Mode | Variable | Target Branch | Release |
|------|----------|---------------|---------|
| Default | (neither set) | admin-ui-test | None |
| Test | TEST_MODE=true | test | Draft |
| Production | PRODUCTION_MODE=true | main | Real |

---

## Sprint 6 Completed (Dec 2024)

Sprint 6 focused on Directory Logic Transparency, field standardization, and QA:

1. **Directory rules module**: `src/nycgo_pipeline/directory_rules.py` - single source of truth
2. **Regression tests**: 70 test cases covering all organization types and edge cases
3. **snake_case standardization**: All column names converted from PascalCase to snake_case
4. **Column ordering**: Golden dataset columns aligned with published export order
5. **Edit UI enhancement**: Shows directory eligibility status with reasoning
6. **Admin UI fixes**: BOM handling in CSV parser, snake_case column support
7. **Workflow fix**: Automatic release run detection uses name-based sorting (not mtime)
8. **QA fixes**: URL corrections, release attribution, UI polish

**Released**: v1.6.0 with snake_case columns

## Sprint 1 Completed (Dec 2024)

1. **Admin UI data source**: Now uses `NYCGO_golden_dataset_latest.csv` from `data/published/latest/`
2. **Batch edit review**: New `review-edits.html` interface for reviewing CSV uploads before commit
3. **Single source of truth**: `data/published/latest/` is now the only golden dataset location
4. **data/working/ removed**: Eliminated to prevent divergence; backup at `backup/pre-working-removal-*`

---

## Common Tasks

### Check current data source
```bash
cat nycgo-admin-ui/js/config.js | grep github:
```

### Find latest golden dataset
```bash
ls -la nyc-governance-organizations/data/published/latest/NYCGO_golden_dataset_*.csv
```

### View pending edits
```bash
ls -la nycgo-admin-ui/pending-edits/
```

### Test the admin UI locally
```bash
cd nycgo-admin-ui && python3 -m http.server 8000
```

---

## Safety Protocols for Schema/Breaking Changes

When making changes to the golden dataset schema, field names, or other breaking changes:

### 1. Commit Before Breaking Changes
```bash
cd nyc-governance-organizations
git add -A && git commit -m "chore: Complete work before [change description]"
```

### 2. Create Baseline Tag
```bash
git tag v1.X.Y-pre-[change-name] -m "Stable baseline before [change description]"
```
This enables easy rollback if something goes wrong.

### 3. Make Changes
Update all affected files:
- `data/published/latest/NYCGO_golden_dataset_latest.csv` - Data file
- `schemas/nycgo_golden_dataset.tableschema.json` - Schema definition
- `scripts/process/export_dataset.py` - Export logic
- `src/nycgo_pipeline/*.py` - Pipeline code
- `tests/` - Test fixtures and assertions

### 4. Run Tests
```bash
make test
```
Verify no new failures (pre-existing failures are documented in SPRINT_7.md).

### 5. Pipeline Smoke Test
```bash
echo "record_id,record_name,field_name,action,justification,evidence_url" > /tmp/empty_qa.csv
make run-pipeline GOLDEN=data/published/latest/NYCGO_golden_dataset_latest.csv \
                  QA=/tmp/empty_qa.csv \
                  DESCRIPTOR="post-change-test"
```
Verify: Golden=38 fields, Published=17 fields (or expected counts).

### 6. Clean Up Test Artifacts
```bash
rm -rf data/audit/runs/*post-change-test*
```

### 7. Commit Changes
Include the baseline tag reference in the commit message for traceability.

---

## Schema Reference

**Current (v1.8.x)**: 38 fields, snake_case column names, `record_id` format `NYC_GOID_XXXXXX`
**Phase II**: 46 fields (deferred indefinitely)

See `nyc-governance-organizations/docs/SCHEMA.md` for complete field documentation.

Key fields:
- `record_id`, `name`, `name_alphabetized`
- `operational_status`, `organization_type`, `url`
- `in_org_chart`, `listed_in_nyc_gov_agency_directory`
- `principal_officer_full_name`, `principal_officer_first_name`, `principal_officer_last_name`, `principal_officer_title`

---

## Release Assets & Artifacts

**GitHub Release Assets** (attached to each release):
- `NYCGO_golden_dataset_v{X.Y.Z}.csv` - Versioned golden dataset
- `NYCGO_golden_dataset_latest.csv` - Same file, stable name
- `NYCGovernanceOrganizations_v{X.Y.Z}.csv` - Public export (directory-eligible only)
- `NYCGovernanceOrganizations_latest.csv` - Same file, stable name

**Pipeline Run Artifacts** (`data/audit/runs/<run_id>/`):
```
<run_id>/
├── inputs/           # Copies of input files used
├── outputs/          # Generated files
│   ├── golden_pre-release.csv
│   ├── public_export.csv
│   └── run_summary.json
└── review/           # Diff and changelog files
```

**Data Dictionary**: `docs/NYC_Agencies_and_Governance_Organizations_Data_Dictionary.xlsx`

**Primary Key**: `record_id` (format: `NYC_GOID_XXXXXX`, unique per record)

---

## Related Documentation

- `nyc-governance-organizations/README.md` - Main pipeline docs
- `nyc-governance-organizations/docs/` - Detailed documentation
- `docs/PHASE_I_SCHEMA.md` - Field definitions and types
- `nycgo-admin-ui/README.md` - Admin UI docs
