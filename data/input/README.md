# Data Input Directory

This directory contains QA edit files for the NYCGO pipeline.

## Structure

```
data/input/
├── pending/          # Active edits waiting to be processed
├── processed/        # Archive of processed edit files
│   ├── YYYY-MM/      # Organized by month
│   └── phase-ii-deferred/  # Phase II edits (on hold)
├── research/         # Reference materials (saved webpages, etc.)
├── templates/        # Edit file templates and references
├── empty_qa.csv      # Utility file for no-edit runs
└── README.md         # This file
```

## Workflow

### 1. Create New Edits

Place new edit files in `pending/`:
```bash
# Example
data/input/pending/my_edits.csv
```

### 2. Run Pipeline

Pass the edit file path to the pipeline:
```bash
python scripts/pipeline/run_pipeline.py \
  --golden data/published/latest/NYCGO_golden_dataset_latest.csv \
  --qa data/input/pending/my_edits.csv \
  --changed-by "your-name"
```

### 3. Archive Processed Edits

After a successful pipeline run, move processed files to `processed/YYYY-MM/`:
```bash
mv data/input/pending/my_edits.csv data/input/processed/2026-01/
```

## Edit File Format

Edit files use CSV format with these columns:
```
record_id,record_name,field_name,action,justification,evidence_url
```

**Actions:**
- `direct_set` - Set field to specific value
- `append_to_list` - Append to semicolon-separated list
- `remove_from_list` - Remove from list
- `generate_recordid` - Auto-generate new RecordID (for new orgs)

See `templates/` for examples and field references.

## Notes

- **Only `pending/` should contain active work** - one glance tells you what's next
- **`processed/` is historical** - kept for audit trail but out of the way
- **`research/` holds reference materials** - not edit files
- **The pipeline is path-agnostic** - you always pass explicit paths via CLI arguments
