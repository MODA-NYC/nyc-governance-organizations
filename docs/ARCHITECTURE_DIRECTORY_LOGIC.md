# Directory Logic Architecture

This document explains how NYC.gov Agency Directory eligibility is determined
and how the logic is kept in sync across documentation, code, and data.

## Single Source of Truth

All directory eligibility rules are defined in:

```
src/nycgo_pipeline/directory_rules.py
```

This single file is used for:
1. **Evaluation** - Determining if a record is eligible (True/False)
2. **Reasoning** - Generating human-readable explanation of why
3. **Documentation** - Auto-generating `docs/DIRECTORY_LOGIC.md`
4. **Changelog** - Tracking changes via `data/directory_logic_changelog.csv`

## Architecture Diagram

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
    │  (script)    │ │  (runtime)  │ │ (pipeline)  │
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

## Making Changes

To change directory eligibility rules:

1. **Edit rules** in `src/nycgo_pipeline/directory_rules.py`
   - Add/modify/remove rules in `GATEKEEPER_RULES` or `TYPE_SPECIFIC_RULES`
   - Update exemption lists (`NONPROFIT_EXEMPTIONS`, `ADVISORY_EXEMPTIONS`, etc.)

2. **Run regression test** to ensure no unintended changes:
   ```bash
   python scripts/test_directory_regression.py --verbose
   ```

3. **Regenerate documentation** (this also updates the changelog):
   ```bash
   python scripts/generate_directory_docs.py --changed-by "your_username"
   ```

4. **Commit all changes**:
   - `src/nycgo_pipeline/directory_rules.py` (your edits)
   - `docs/DIRECTORY_LOGIC.md` (regenerated)
   - `data/directory_logic_changelog.csv` (auto-appended)
   - `data/directory_rules_snapshot.json` (auto-updated)

## Files

| File | Purpose | Editable? |
|------|---------|-----------|
| `src/nycgo_pipeline/directory_rules.py` | Rule definitions | **YES - edit here** |
| `docs/DIRECTORY_LOGIC.md` | Human-readable documentation | NO - auto-generated |
| `data/directory_logic_changelog.csv` | Audit trail of changes | NO - auto-appended |
| `data/directory_rules_snapshot.json` | For change detection | NO - auto-updated |
| `scripts/generate_directory_docs.py` | Documentation generator | Rarely |
| `scripts/test_directory_regression.py` | Regression test | Rarely |

## Rule Categories

### 1. Gatekeeper Rules
ALL must pass for a record to be considered. These are fundamental requirements:
- Must be Active
- URL cannot be state .ny.gov
- Must have some contact information

### 2. Type-Specific Rules
At least ONE must pass (after gatekeepers pass). These determine eligibility based on organization type:
- Some types always included (Mayoral Agency, Elected Office, etc.)
- Some types conditional (Division: only if in Org Chart)
- Some types have exemption lists (Nonprofit, Advisory)

### 3. Manual Overrides
Force True/False for specific records when rules don't capture edge cases.

## How It Stays In Sync

| Change Scenario | What Happens |
|-----------------|--------------|
| Add new rule | Add to `DIRECTORY_RULES` → automatically in docs, evaluation, and reasoning |
| Change rule description | Change in `Rule.description` → updates everywhere on regeneration |
| Change rule logic | Change in `Rule.check` → evaluation changes, run regression test |
| Add exemption | Add to exemption list → reasoning shows specific match |
| Remove rule | Remove from list → gone from docs, evaluation, reasoning |

## Changelog

Every time rules change and documentation is regenerated, an entry is appended to
`data/directory_logic_changelog.csv` with:
- Timestamp
- Who made the change
- What type of change (rule_added, rule_modified, exemption_added, etc.)
- Old and new values
- Git commit SHA

This provides a complete audit trail of all directory logic changes.

## Related Documentation

- [DIRECTORY_LOGIC.md](DIRECTORY_LOGIC.md) - Auto-generated rule documentation
- [Sprint 6A](sprints/SPRINT_6A.md) - Implementation details
