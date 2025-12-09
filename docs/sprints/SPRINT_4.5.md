# Sprint 4.5: Release Notes & Smart Versioning

**Status: ⚠️ PARTIAL** (Phase 1, 1.5, 1.6 complete; Phase 2 and 3 pending)

## Overview

Improve release notes to include all artifacts and implement smart semantic versioning based on the type of change.

## Issues to Address

### Issue 1: Missing Golden Datasets in Release Notes

Current release notes template lists:
- `nycgo-run-{run_id}.zip`
- `NYCGovernanceOrganizations_{version}.csv`
- `NYCGovernanceOrganizations_latest.csv`
- `run_changelog.csv`

Missing:
- `NYCGO_golden_dataset_{version}.csv`
- `NYCGO_golden_dataset_latest.csv`

### Issue 2: Published By Shows Generic Name

Currently shows "NYCGO Admin UI" instead of the actual GitHub user who made the edit.

### Issue 3: No Smart Version Bumping

Currently defaults to whatever is specified (usually patch). Should automatically determine version bump based on change type.

---

## Phase 1: Fix Release Notes Template (✅ COMPLETED)

### 1.1 Update publish.py

File: `src/nycgo_pipeline/publish.py`

Update the release notes template (around line 293):

```python
"## Attached Assets",
"",
f"- `nycgo-run-{run_id}.zip` - Full run artifacts bundle",
f"- `NYCGO_golden_dataset_{version}.csv` - Golden dataset (internal)",
f"- `NYCGO_golden_dataset_latest.csv` - Latest golden dataset (copy)",
f"- `NYCGovernanceOrganizations_{version}.csv` - Published dataset (public)",
f"- `NYCGovernanceOrganizations_latest.csv` - Latest published dataset (copy)",
"- `run_changelog.csv` - Run-specific changelog",
```

### Acceptance Criteria
- [x] Release notes list all 6 asset files
- [x] Golden datasets listed before published datasets

---

## Phase 1.5: Add Detailed Changes Table to Release Notes (✅ COMPLETED)

### 1.5.1 Requirements

When there are 5 or fewer QA edits, show a detailed table in the release notes:

| Record | Field | Old Value | New Value | Reason |
|--------|-------|-----------|-----------|--------|
| NYC_GOID_000002 | Notes | (test data) | (empty) | Removing test data |

When there are more than 5 changes, show summary only with note:
```
See `run_changelog.csv` for full details.
```

### 1.5.2 Implementation

Update `generate_release_notes()` in `publish.py`:

```python
# After the Changes summary section
qa_changes = counts.get('qa_changes', 0)
if 0 < qa_changes <= 5 and run_changelog.exists():
    changelog_df = pd.read_csv(run_changelog, dtype=str)
    # Filter to only QA edits (not global rules)
    qa_edits = changelog_df[~changelog_df['feedback_source'].str.contains('System_', na=False)]

    notes_lines.extend([
        "",
        "### Changes Detail",
        "",
        "| Record | Field | Old Value | New Value | Reason |",
        "|--------|-------|-----------|-----------|--------|",
    ])

    for _, row in qa_edits.iterrows():
        old_val = row.get('old_value', '') or '(empty)'
        new_val = row.get('new_value', '') or '(empty)'
        # Truncate long values
        old_val = old_val[:30] + '...' if len(old_val) > 30 else old_val
        new_val = new_val[:30] + '...' if len(new_val) > 30 else new_val
        notes_lines.append(
            f"| {row.get('record_id', '')} | {row.get('column_changed', '')} | {old_val} | {new_val} | {row.get('reason', '')[:40]} |"
        )
elif qa_changes > 5:
    notes_lines.extend([
        "",
        f"*{qa_changes} changes made. See `run_changelog.csv` for full details.*",
    ])
```

### Acceptance Criteria
- [x] Changes ≤5: Show detailed table with old/new values
- [x] Changes >5: Show "See run_changelog.csv" message
- [x] Table includes: Record ID, Field, Old Value, New Value, Reason
- [x] Long values truncated to prevent table overflow

---

## Phase 1.6: Add Full Changelog Link (✅ COMPLETED)

### 1.6.1 Requirements

After the Changes Detail section (or summary), add a link to the full running changelog:

```markdown
## Changes

- **Total changes:** 2
- **QA edits:** 2
- **Global rules:** 0
- **Directory field changes:** 0

### Changes Detail
| Record | Field | Old Value | New Value | Reason |
...

📋 [View full changelog](https://github.com/MODA-NYC/nyc-governance-organizations/blob/main/data/changelog.csv)
```

### 1.6.2 Implementation

Update `generate_release_notes()` in `publish.py` to add a link after the changes section:

```python
# After the changes table or summary
notes_lines.extend([
    "",
    "📋 [View full changelog](https://github.com/MODA-NYC/nyc-governance-organizations/blob/main/data/changelog.csv)",
])
```

### Acceptance Criteria
- [x] Release notes include link to full changelog
- [x] Link appears after the Changes section

---

## Phase 2: Pass GitHub Actor to Release Notes (📋 PENDING)

### 2.1 Update process-edit.yml

In `nycgo-admin-ui/.github/workflows/process-edit.yml`, pass the GitHub actor when running the pipeline:

```yaml
- name: Run pipeline
  env:
    GITHUB_ACTOR: ${{ github.actor }}
  run: |
    # ... existing code ...
    # Pass actor to pipeline
```

### 2.2 Update Pipeline to Accept Actor

Modify the pipeline to accept and store the GitHub username in the run summary:

```python
# In run_summary.json
{
  "changed_by": "npstorey",  # GitHub username
  "changed_by_display": "NYCGO Admin UI",  # System name
  ...
}
```

### 2.3 Update Release Notes

Change "Published by" to show both:
```markdown
**Published by:** @npstorey via NYCGO Admin UI
```

### Acceptance Criteria
- [ ] GitHub username captured from workflow
- [ ] Release notes show actual GitHub username
- [ ] Links to GitHub profile (@username format)

---

## Phase 3: Smart Semantic Versioning (📋 PENDING)

### 3.1 Version Bump Rules

| Change Type | Version Bump | Examples |
|-------------|--------------|----------|
| Schema change (add/remove fields) | **Major** (v2.0.0) | Adding new columns, removing columns |
| New organization added | **Minor** (v1.2.0) | `generate_recordid` action |
| OperationalStatus change | **Minor** (v1.2.0) | Active → Inactive, etc. |
| Field correction/update | **Patch** (v1.1.4) | Fix typo, update URL, add alternate name |

### 3.2 Implementation

#### Option A: Determine at Pipeline Runtime

Analyze the changelog to determine bump type:

```python
def determine_version_bump(changelog_df: pd.DataFrame) -> str:
    """Determine version bump based on changes."""

    # Check for schema changes (would need to compare field lists)
    # This is complex - may need separate detection

    # Check for new organizations
    if "generate_recordid" in changelog_df["action"].values:
        return "minor"

    # Check for OperationalStatus changes
    if "OperationalStatus" in changelog_df["field_name"].values:
        return "minor"

    # Default to patch
    return "patch"
```

#### Option B: Determine in Workflow

Check the edit CSV before running pipeline:

```yaml
- name: Determine version bump
  id: version-bump
  run: |
    EDIT_FILE=$(ls pending-edits/*.csv | head -1)

    # Check for new org (generate_recordid)
    if grep -q "generate_recordid" "$EDIT_FILE"; then
      echo "bump=minor" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check for OperationalStatus change
    if grep -q "OperationalStatus" "$EDIT_FILE"; then
      echo "bump=minor" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Default to patch
    echo "bump=patch" >> $GITHUB_OUTPUT
```

Then pass to publish:
```yaml
gh workflow run publish-release.yml \
  -f run_id=$RUN_ID \
  -f version_bump=${{ steps.version-bump.outputs.bump }}
```

**Recommendation**: Option B (workflow) - simpler, doesn't require pipeline changes.

### 3.3 Schema Change Detection

For major version bumps (schema changes), this is harder to automate because:
- Schema changes happen during Phase II releases
- They're planned, not ad-hoc edits

**Recommendation**: Keep major bumps manual. When doing a schema change:
1. Manually trigger publish workflow
2. Select "major" for version_bump
3. Or add a workflow input flag `is_schema_change: true`

### 3.4 Documentation

Create `docs/VERSIONING.md`:

```markdown
# Versioning Policy

This project uses Semantic Versioning (semver): `vMAJOR.MINOR.PATCH`

## Version Bump Rules

| Change Type | Bump | Example |
|-------------|------|---------|
| Schema change | Major | v1.x.x → v2.0.0 |
| New organization | Minor | v1.1.x → v1.2.0 |
| OperationalStatus change | Minor | v1.1.x → v1.2.0 |
| Field correction | Patch | v1.1.3 → v1.1.4 |

## Automatic Detection

The pipeline automatically determines version bump based on:
- `generate_recordid` action → Minor
- `OperationalStatus` field change → Minor
- All other changes → Patch

Major version bumps require manual trigger.
```

### Acceptance Criteria
- [ ] Pipeline detects new org → minor bump
- [ ] Pipeline detects OperationalStatus change → minor bump
- [ ] Other edits → patch bump
- [ ] Major bumps remain manual
- [ ] VERSIONING.md documents the policy

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/nycgo_pipeline/publish.py` | Add golden datasets to release notes |
| `nycgo-admin-ui/.github/workflows/process-edit.yml` | Pass GitHub actor, detect version bump |
| `nyc-governance-organizations/.github/workflows/publish-release.yml` | Accept version bump from trigger |
| `docs/VERSIONING.md` | New file documenting policy |

---

## Definition of Done

- [x] Release notes include all 6 asset files
- [x] Release notes show detailed changes table (≤5 edits) or summary (>5)
- [x] Release notes include link to full changelog
- [ ] Release notes show GitHub username of editor
- [ ] Version bump automatically determined based on change type
- [ ] Major bumps remain manual (for schema changes)
- [ ] VERSIONING.md documents the policy
- [ ] Tested with: patch edit, new org (minor), status change (minor)
