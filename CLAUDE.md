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

Sprint documentation lives in `docs/sprints/`:
- `SPRINT_1.md` - Admin UI Infrastructure ✅ COMPLETED
- `SPRINT_2.md` - Pipeline Testing & Validation ✅ COMPLETED
- `SPRINT_3.md` - v1.1.2 Release Fix & Production Pipeline Test ✅ COMPLETED
- `SPRINT_4.md` - Edit Submission Rate Limiting ✅ COMPLETED
- `SPRINT_4.5.md` - Release Notes & Smart Versioning ✅ COMPLETED
- `SPRINT_5.md` - Data Quality & Standardization ✅ COMPLETED
- `SPRINT_6.md` - Schema Alignment & Directory Logic Refactoring 📋 PLANNED (deferred)
- `SPRINT_6A.md` - Directory Logic Transparency 📋 PLANNED (extracted from Sprint 6 Phase 6)
- `FUTURE.md` - Phase II Data Release 🔮 DEFERRED

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
- v1.1.2 - Latest published (435 records, 38 fields, Phase I schema)
- v1.2.0 - Development (443 records, 46 fields, Phase II schema)

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
Output committed to target branch (test/demo/main)
        ↓
publish-release.yml creates GitHub release (if prod/demo mode)
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

## Schema Reference

**Phase I (v1.1.x)**: 38 fields, RecordID format `NYC_GOID_XXXXXX`
**Phase II (v1.2.x)**: 46 fields, RecordID format `XXXXXX` (6-digit numeric)

New Phase II fields:
- name_moa, org_chart_oversight_record_id/name
- parent_organization_record_id/name
- authorizing_authority, authorizing_authority_type, authorizing_url
- appointments_summary, governance_structure

---

## Related Documentation

- `nyc-governance-organizations/README.md` - Main pipeline docs
- `nyc-governance-organizations/docs/` - Detailed documentation
- `nycgo-admin-ui/README.md` - Admin UI docs
