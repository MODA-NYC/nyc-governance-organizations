# Sprint 1: Admin UI Infrastructure

**Status: ✅ COMPLETED**
**Completed: December 2024**

## Overview

This sprint established the foundational infrastructure for a reliable, maintainable data workflow:

1. ✅ **Admin UI data source**: Point to latest release via static `_latest.csv` file
2. ✅ **Batch edit review interface**: Allow review of `edits_to_make` CSVs before processing
3. ✅ **Data source simplification**: Eliminate `data/working/` directory; use `data/published/latest/` as single source of truth

---

## Data Flow (Implemented)

```
Admin UI loads from:
  main branch → data/published/latest/NYCGO_golden_dataset_latest.csv

Pipeline workflow (process-edit.yml):
  Finds latest golden in data/published/latest/

Publish workflow (publish-release.yml):
  Outputs to data/published/latest/ and updates _latest.csv
```

---

## Key Commits

- `a0e9e2d` Add NYCGO_golden_dataset_latest.csv for Admin UI data source (pipeline)
- `5c0ff3e` Update data source to use published _latest.csv (admin-ui)
- `9958ee4` Add batch edit review interface (admin-ui)
- `e06078e` Update process-edit.yml to use data/published/latest/ (admin-ui)
- `b35997a` Remove data/working/ directory (Sprint 1 Phase 3) (pipeline)

---

## Phase 1: Update Admin UI Data Source ✅

**Goal**: Admin UI automatically loads the latest released golden dataset using a static `_latest.csv` file.

### Approach: Static `_latest.csv` File

Follow the existing pattern used for `NYCGovernanceOrganizations_latest.csv` - maintain a copy of the current versioned golden dataset with a predictable `_latest` name.

**Why this approach over GitHub API:**
- **Simpler**: One static URL, no client-side logic needed
- **Faster**: Direct file fetch, no API call before data fetch
- **Reliable**: No rate limiting (GitHub API: 60 req/hr unauthenticated)
- **Consistent**: Matches existing pattern for published data

### Files Modified

#### 1. Publish Workflow: `nyc-governance-organizations/.github/workflows/publish-release.yml`
Added step to create `_latest.csv` copy after publish.

#### 2. Admin UI Config: `nycgo-admin-ui/js/config.js`
Updated data source URL:
```javascript
dataUrls: {
    published: 'https://data.cityofnewyork.us/api/views/t3jq-9nkf/rows.csv?accessType=DOWNLOAD',
    github: 'https://raw.githubusercontent.com/MODA-NYC/nyc-governance-organizations/main/data/published/latest/NYCGO_golden_dataset_latest.csv'
}
```

### Acceptance Criteria
- [x] `NYCGO_golden_dataset_latest.csv` exists in `data/published/latest/`
- [x] Admin UI loads from main branch (not v1.2.0 from dev)
- [x] `publish-release.yml` creates/updates `_latest.csv` on new release

---

## Phase 2: Add Batch Edit Review Interface ✅

**Goal**: Allow users to upload and review CSV files in `edits_to_make` format before they're processed.

### Files Created
- `nycgo-admin-ui/review-edits.html` - Batch edit review page
- `nycgo-admin-ui/js/review.js` - Review page logic

### Edit Format Reference

The `edits_to_make` CSV format:
```csv
record_id,record_name,field_name,action,justification,evidence_url
```

Where:
- `record_id` - Target record ID (or empty for new records)
- `record_name` - Human-readable name (for verification)
- `field_name` - Column to modify (PascalCase, e.g., `OperationalStatus`)
- `action` - One of: `direct_set:<value>`, `append_to_list:<value>`, `remove_from_list:<value>`, `generate_recordid`
- `justification` - Reason for change
- `evidence_url` - URL to supporting documentation

### Review Interface Features Implemented

- File upload with drag-and-drop CSV upload
- File format validation
- Preview table showing current vs. new values
- Validation of required columns, field names, actions
- Commit flow via GitHub redirect

### Acceptance Criteria
- [x] CSV upload works with valid files
- [x] Validation catches: missing columns, invalid actions, unknown record IDs
- [x] Preview shows current vs. new values correctly
- [x] GitHub redirect pre-fills correct content

---

## Phase 3: Eliminate data/working/ Directory ✅

**Goal**: Simplify data flow by using `data/published/latest/` as the single source of truth.

### Files Modified

#### 1. Pipeline Workflow: `nycgo-admin-ui/.github/workflows/process-edit.yml`

Updated to find golden dataset from `data/published/latest/`:
```yaml
- name: Find latest golden dataset
  run: |
    cd pipeline
    # Use data/published/latest/ as source of truth (Sprint 1 Phase 3)
    if [ -f "data/published/latest/NYCGO_golden_dataset_latest.csv" ]; then
      golden="data/published/latest/NYCGO_golden_dataset_latest.csv"
    else
      golden=$(ls -t data/published/latest/NYCGO_golden_dataset_v*.csv 2>/dev/null | head -1)
    fi
```

#### 2. Removed data/working/ Directory

The `data/working/` directory has been removed from the pipeline repo. Backup available at `backup/pre-working-removal-20251205`.

### Acceptance Criteria
- [x] process-edit.yml finds golden from data/published/latest/
- [x] New edits process correctly
- [x] publish-release.yml still works
- [x] No broken references to data/working/

---

## Additional Features Implemented (Beyond Original Plan)

- **Scheduled edits feature** (`ad65eba`) - ability to schedule future-dated edits
- **About panel** (`671f089`) - expandable panel explaining tool and data relationships
- **Auth status display** (`b632c57`) - shows authentication status in UI

---

## Rollback Plan (Archived)

### If Phase 1 fails
Revert config.js to hardcode versioned URL.

### If Phase 2 fails
Review interface is isolated; main Admin UI unaffected.

### If Phase 3 fails
Restore data/working/ from backup branch:
```bash
git checkout backup/pre-working-removal-20251205 -- data/working/
```

---

## Open Questions (Resolved or Deferred)

1. **Review permissions**: Currently accessible to all users (no authentication required)
2. **Batch size limits**: No limit implemented
3. **Conflict detection**: Not yet implemented - potential future enhancement

---

## Future Enhancements

- **Edit history viewer**: Show changelog for each record
- **Diff view**: Visual diff between current and proposed changes
- **Multi-reviewer approval**: Require multiple approvals for batch edits
- **Edit templates**: Pre-built CSV templates for common edit types
- **Integration tests**: Automated testing of the full edit flow
- **Conflict detection**: Handle simultaneous conflicting edits
