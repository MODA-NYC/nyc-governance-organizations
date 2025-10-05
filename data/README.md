# Data Directory

## Important: Changelog Protection

### `data/changelog.csv` is APPEND-ONLY ⚠️

**DO NOT:**
- ❌ Pass `data/changelog.csv` to `src/apply_edits.py --changelog`
- ❌ Pass `data/changelog.csv` to `src/run_global_rules.py --changelog`
- ❌ Edit `data/changelog.csv` directly
- ❌ Overwrite `data/changelog.csv`

**DO:**
- ✅ Use `scripts/maint/append_changelog.py` to add new entries
- ✅ Pass temporary changelog paths (e.g., `data/output/changelog_v0_XX_edits.csv`) to processing scripts
- ✅ Review changes before appending using `scripts/maint/review_changes.py`

### Correct Workflow

```bash
# Step 1: Generate temporary changelog with processing scripts
python src/apply_edits.py \
  --input_csv ... \
  --qa_csv ... \
  --output_csv data/output/processed_v0_19.csv \
  --changelog data/output/changelog_v0_19_edits.csv \  # ← TEMP FILE
  --changed_by nathanstorey

# Step 2: Review and append to main changelog
RUN_ID=$(python scripts/maint/make_run_id.py)
python scripts/maint/prepare_run_proposed_changes.py \
  --run-id $RUN_ID \
  --step1 data/output/changelog_v0_19_edits.csv

python scripts/maint/review_changes.py --run-dir data/audit/runs/$RUN_ID

python scripts/maint/append_changelog.py \
  --run-dir data/audit/runs/$RUN_ID \
  --changelog data/changelog.csv \  # ← SAFE: append_changelog.py uses append mode
  --operator nathanstorey
```

### Built-in Protection

Both `src/apply_edits.py` and `src/run_global_rules.py` now include runtime checks that **prevent** overwriting `data/changelog.csv`. If you accidentally try to use it, you'll see:

```
❌ ERROR: Cannot write directly to data/changelog.csv (append-only file).
   This script should write to a temporary changelog in data/output/.
   Use scripts/maint/append_changelog.py to append to the main changelog.
```

### Schema

The main changelog uses this minimal tracked schema:

```
event_id,timestamp_utc,run_id,record_id,field,old_value,new_value,reason,evidence_url,source_ref,operator,notes
```

All entries must have unique `event_id` values (SHA256 hashes). The `append_changelog.py` script automatically deduplicates based on `event_id`.

## Directory Structure

- `data/audit/` - Run-specific audit trails (gitignored)
- `data/changelog.csv` - **APPEND-ONLY** master changelog (tracked in git)
- `data/input/` - Input files for processing
- `data/output/` - Temporary output files (gitignored)
- `data/published/` - Final published datasets
- `data/published/latest/` - Latest published versions (tracked in git)
