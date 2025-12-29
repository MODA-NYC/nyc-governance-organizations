# Sprint 6: Directory Logic Transparency & QA

**Status: COMPLETED**
**Completed: December 2024**
**Released: v1.6.0**

## Overview

Made the NYC.gov Agency Directory eligibility logic transparent and maintainable by:
1. Restructuring rules as data (single source of truth)
2. Auto-generating documentation from rule definitions
3. Pre-computing eligibility reasoning for display in Edit UI
4. Creating regression tests to ensure refactoring doesn't change results
5. QA fixes for UI polish, URLs, and attribution

**Key Principle**: Rules are defined once → used for evaluation, documentation, and UI display.

---

## What Was Delivered

### Directory Rules Module
- **`src/nycgo_pipeline/directory_rules.py`**: Single source of truth for eligibility logic with Rule dataclass
- **Documentation generator**: Auto-generates `docs/DIRECTORY_LOGIC.md` from rules
- **Regression tests**: 70 test cases covering all organization types and edge cases
- **Pipeline integration**: `export_dataset.py` imports exemption lists from `directory_rules`

### Field Name Standardization
- Converted all column names from PascalCase to snake_case
- Updated golden dataset, pipeline code, admin UI, and tests
- Created `standardize_field_names.py` migration script
- Column ordering aligned with published export order

### Admin UI Enhancements
- Shows directory eligibility status with reasoning in Edit modal
- BOM handling in CSV parser for Excel-exported files
- snake_case column support with PascalCase fallbacks

### QA Fixes
- **URL fix**: Changed GitHub organization from `nyc-cto` to `MODA-NYC` in all links
- **UI polish**: Directory status positioned consistently above "Schedule For Later"
- **Release notes**: Improved formatting with clearer section names
- **Attribution**: Changed `--changed-by` default to `$USER` environment variable
- **Rule fix**: State Government Agencies now use explicit exemption list

### Workflow Improvements
- Fixed `ls -t` to `ls -1 | sort -r` in publish-release.yml for reliable run detection

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   DIRECTORY_RULES                        │
│   (Python data structure defining rules + descriptions)  │
│         src/nycgo_pipeline/directory_rules.py            │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Documentation│ │  Evaluation │ │ Pre-computed│
    │  Generator   │ │   Engine    │ │   Field     │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐
    │ DIRECTORY_  │ │ True/False  │ │ directory_reasoning │
    │ LOGIC.md    │ │  result     │ │ field in golden     │
    └─────────────┘ └─────────────┘ └─────────────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │  Edit UI    │
                                   │  Display    │
                                   └─────────────┘
```

### How It Stays In Sync

| Change Scenario | What Happens |
|-----------------|--------------|
| Add new rule | Add to `DIRECTORY_RULES` → automatically in docs, evaluation, and reasoning |
| Change rule description | Change in `Rule.description` → updates everywhere |
| Change rule logic | Change in `Rule.check` → evaluation changes |
| Add exemption | Add to exemption list → reasoning shows specific match |

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `src/nycgo_pipeline/directory_rules.py` | Rule definitions (SINGLE SOURCE OF TRUTH) |
| `scripts/generate_directory_docs.py` | Documentation generator + changelog |
| `docs/DIRECTORY_LOGIC.md` | Auto-generated documentation |
| `docs/ARCHITECTURE_DIRECTORY_LOGIC.md` | Architecture explanation |
| `data/directory_logic_changelog.csv` | Append-only changelog of rule changes |
| `data/directory_rules_snapshot.json` | Snapshot for change detection |

### Modified Files

| File | Changes |
|------|---------|
| `scripts/process/export_dataset.py` | Use new rules module |
| `nycgo-admin-ui/js/app.js` | Display reasoning in Edit modal |
| `nycgo-admin-ui/index.html` | Add reasoning display section, fix URLs |
| `nycgo-admin-ui/js/config.js` | snake_case column mappings |
| `scripts/pipeline/run_pipeline.py` | Default `--changed-by` to `$USER` |

---

## Exemption Lists

### Nonprofit Exemptions
- Brooklyn Public Library
- New York City Tourism + Conventions
- New York Public Library
- Queens Public Library
- Gracie Mansion Conservancy
- Mayor's Fund to Advance New York City

### Advisory Exemptions
- Board of Elections
- Campaign Finance Board
- Rent Guidelines Board

### State Government Exemptions
- Bronx County Public Administrator
- City University of New York
- Kings County Public Administrator
- New York County Public Administrator
- Public Administrator of Queens County
- Richmond County Public Administrator

---

## Release

**v1.6.0** - First release with snake_case column names
- 434 records
- 38 fields
- 201 directory-eligible organizations

---

## QA Backlog (for future sprints)

- [ ] Test workflow rate limiting (Sprint 4): Verify "Edit currently in progress" message
- [ ] Rename `DEMO_MODE` variable to `TEST_MODE` (variable exists but is unused)
