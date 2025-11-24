# Testing Recommendations Before Phase II.2

## Overview
Before proceeding to Phase II.2 (data population and research), we should verify that all Phase II.1 migrations and code changes work correctly.

## Critical Tests

### 1. RecordID Migration Verification
**Purpose**: Ensure all RecordIDs were correctly converted and no data was lost.

**Test Steps**:
```bash
# Verify crosswalk completeness
python3 -c "
import pandas as pd
df = pd.read_csv('data/published/NYCGO_golden_dataset_v1.1.1_final.csv', dtype=str)
crosswalk = pd.read_csv('data/crosswalk/recordid_migration.csv', dtype=str)
print(f'Source records: {len(df)}')
print(f'Crosswalk mappings: {len(crosswalk)}')
print(f'Match: {len(df) == len(crosswalk)}')
"

# Verify dataset migration
python3 -c "
import pandas as pd
df = pd.read_csv('data/working/NYCGO_golden_dataset_v2.0.0-dev.csv', dtype=str)
old_format = df['RecordID'].str.startswith('NYC_GOID_').sum()
new_format = (~df['RecordID'].str.startswith('NYC_GOID_')).sum()
print(f'Old format IDs: {old_format}')
print(f'New format IDs: {new_format}')
print(f'All migrated: {old_format == 0}')
"
```

**Expected Results**:
- Crosswalk has 434 mappings (matches v1.1.1 final)
- All RecordIDs in v2.0.0-dev are in new 6-digit format
- No old format IDs remain

### 2. Reports_to Migration Verification
**Purpose**: Ensure all 137 ReportsTo values were correctly migrated to new relationship fields.

**Test Steps**:
```bash
# Verify migration completeness
python3 -c "
import pandas as pd
migration = pd.read_csv('data/crosswalk/reports_to_migration.csv', dtype=str)
df = pd.read_csv('data/working/NYCGO_golden_dataset_v2.0.0-dev.csv', dtype=str)
print(f'Migration records: {len(migration)}')
print(f'Expected: 137')
print(f'Match: {len(migration) == 137}')

# Check relationship fields populated
org_chart = df['org_chart_oversight_record_id'].notna().sum()
parent = df['parent_organization_record_id'].notna().sum()
print(f'\\nPopulated fields:')
print(f'  org_chart_oversight_record_id: {org_chart}')
print(f'  parent_organization_record_id: {parent}')
print(f'  Total relationships: {org_chart + parent}')
"
```

**Expected Results**:
- Migration mapping has 137 records
- Relationship fields are populated correctly
- No ReportsTo field remains in dataset

### 3. RecordID Generation Uniqueness Test
**Purpose**: Verify that new RecordID generation ensures uniqueness.

**Test Steps**:
```bash
# Run the test suite
make test
# Or specifically:
python3 -m pytest tests/test_recordid_generation.py -v
```

**Expected Results**:
- All tests pass
- Generated IDs are unique
- Handles edge cases (gaps, duplicates, mixed formats)

### 4. Export Pipeline Test
**Purpose**: Verify Phase II fields are included in exports and ReportsTo is excluded.

**Test Steps**:
```bash
# Test export with Phase II dataset
python3 scripts/process/export_dataset.py \
  --input_csv data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
  --output_golden data/test/golden_test.csv \
  --output_published data/test/published_test.csv

# Verify exported fields
python3 -c "
import pandas as pd
df = pd.read_csv('data/test/published_test.csv', dtype=str)
print('Phase II fields in export:')
phase_ii_fields = [
    'governance_structure', 'org_chart_oversight_record_id',
    'org_chart_oversight_name', 'parent_organization_record_id',
    'parent_organization_name', 'authorizing_authority',
    'authorizing_authority_type', 'authorizing_url', 'appointments_summary'
]
for field in phase_ii_fields:
    status = '✓' if field in df.columns else '✗'
    print(f'  {status} {field}')

# Check ReportsTo is removed
has_reports_to = 'reports_to' in df.columns or 'ReportsTo' in df.columns
print(f'\\nReportsTo removed: {not has_reports_to}')
"
```

**Expected Results**:
- All Phase II fields present in export
- ReportsTo field absent
- RecordIDs in new format

### 5. Validation Rules Test
**Purpose**: Verify Phase II validation rules work correctly.

**Test Steps**:
```bash
# Create test dataset with validation issues
python3 << 'EOF'
import pandas as pd
from src.nycgo_pipeline.global_rules import validate_phase_ii_fields, reset_changelog

# Create test dataset with various validation issues
test_data = {
    'RecordID': ['100000', 'INVALID', '100002', '100003'],
    'Name': ['Valid Entity', 'Invalid ID Entity', 'Self Ref', 'Bad URL'],
    'org_chart_oversight_record_id': ['100001', '', '100003', '100004'],  # Self-ref in row 2
    'authorizing_url': ['https://example.com', '', 'not-a-url', 'https://valid.com'],
    'authorizing_authority_type': ['NYC Charter', 'Invalid Type', 'Mayoral Executive Order', '']
}
df = pd.DataFrame(test_data)

reset_changelog()
df_validated = validate_phase_ii_fields(df, 'test_user', 'test')

# Check changelog for validation warnings
from src.nycgo_pipeline.global_rules import changelog_entries
print(f'Validation warnings generated: {len(changelog_entries)}')
for entry in changelog_entries[:5]:
    print(f"  - {entry['column_changed']}: {entry['notes']}")
EOF
```

**Expected Results**:
- Invalid RecordID format detected
- Self-reference detected
- Invalid URL format detected
- Invalid controlled vocabulary detected

### 6. Phase I Export Bridge Test
**Purpose**: Verify the Phase I export bridge tool works for urgent updates.

**Test Steps**:
```bash
# Test Phase I export from Phase II dataset
python3 scripts/pipeline/export_phase_i.py \
  --input data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
  --output data/test/phase_i_compatible_test.csv \
  --crosswalk data/crosswalk/recordid_migration.csv

# Verify output format
python3 -c "
import pandas as pd
df = pd.read_csv('data/test/phase_i_compatible_test.csv', dtype=str)
print(f'Records exported: {len(df)}')

# Check Phase I fields present
phase_i_fields = [
    'record_id', 'name', 'reports_to', 'in_org_chart'
]
for field in phase_i_fields:
    status = '✓' if field in df.columns else '✗'
    print(f'  {status} {field}')

# Check RecordIDs converted back
old_format = df['record_id'].str.startswith('NYC_GOID_').sum()
print(f'\\nRecordIDs in old format: {old_format}')
"
```

**Expected Results**:
- Phase I fields present
- RecordIDs converted back to old format
- ReportsTo field reconstructed

## Integration Test

### Full Pipeline Test
**Purpose**: Run a complete pipeline cycle to ensure everything works together.

**Test Steps**:
```bash
# 1. Run pipeline with Phase II dataset
make run-pipeline \
  GOLDEN=data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
  QA=data/input/NYCGO_phase2_edits_to_make_20251118.csv \
  DESCRIPTOR=phase-ii-test

# 2. Verify outputs
# Check run artifacts created
# Check changelog generated
# Check exports created

# 3. Test export
# Verify Phase II fields included
# Verify ReportsTo excluded
# Verify RecordIDs in new format
```

## Recommended Test Order

1. ✅ **RecordID Migration Verification** (Quick, critical)
2. ✅ **Reports_to Migration Verification** (Quick, critical)
3. ✅ **RecordID Generation Uniqueness** (Automated tests)
4. ✅ **Export Pipeline Test** (Medium complexity)
5. ✅ **Validation Rules Test** (Medium complexity)
6. ✅ **Phase I Export Bridge Test** (Low priority, but useful)
7. ✅ **Full Pipeline Integration Test** (Most comprehensive)

## Success Criteria

Before proceeding to Phase II.2, all tests should:
- ✅ Pass without errors
- ✅ Verify data integrity (no data loss)
- ✅ Confirm migrations completed correctly
- ✅ Validate new code works as expected

## Notes

- Tests can be run incrementally
- Focus on critical tests first (1-3)
- Integration test (7) is most comprehensive but takes longest
- If any test fails, fix issues before proceeding

