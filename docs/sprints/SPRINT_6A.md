# Sprint 6A: Directory Logic Transparency

**Status: ✅ COMPLETED**
**Extracted from: Sprint 6, Phase 6**
**Completed: December 2024**

## Overview

Make the NYC.gov Agency Directory eligibility logic transparent and maintainable by:
1. Restructuring rules as data (single source of truth)
2. Auto-generating documentation from rule definitions
3. Pre-computing eligibility reasoning for display in Edit UI
4. Creating regression tests to ensure refactoring doesn't change results

**Key Principle**: Rules are defined once → used for evaluation, documentation, and UI display.

## Completion Summary

### Implemented Features:
- **directory_rules.py**: Single source of truth for eligibility logic with Rule dataclass
- **Documentation generator**: Auto-generates DIRECTORY_LOGIC.md from rules
- **Regression tests**: 70 test cases covering all organization types and edge cases
- **Pipeline integration**: export_dataset.py imports exemption lists from directory_rules
- **Edit UI enhancement**: Shows directory eligibility status with reasoning
- **Field name standardization**: Converted all column names from PascalCase to snake_case

### Additional Work (Phase 4.5):
- Standardized all field names to snake_case matching published export format
- Updated golden dataset, pipeline code, admin UI, and tests
- Created standardize_field_names.py migration script

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

### How It Stays In Sync

| Change Scenario | What Happens |
|-----------------|--------------|
| Add new rule | Add to `DIRECTORY_RULES` → automatically in docs, evaluation, and reasoning |
| Change rule description | Change in `Rule.description` → updates everywhere |
| Change rule logic | Change in `Rule.check` → evaluation changes |
| Add exemption | Add to exemption list → reasoning shows specific match |

---

## Phase 1: Rename Demo Mode to Test Mode

### 1.1 Files to Modify

**nycgo-admin-ui:**
- `.github/workflows/process-edit.yml` - Change `DEMO_MODE` to `TEST_MODE`
- `README.md` - Update documentation references

**nyc-governance-organizations:**
- `.github/workflows/publish-release.yml` - Update if referenced
- `docs/sprints/*.md` - Update any references

### 1.2 Implementation

Replace all occurrences:
- `DEMO_MODE` → `TEST_MODE`
- `demo` branch references → `test` (if applicable)
- Documentation references

### Acceptance Criteria
- [ ] All `DEMO_MODE` references renamed to `TEST_MODE`
- [ ] Workflows function correctly with new variable name
- [ ] Documentation updated

---

## Phase 2: Create Directory Rules Module

### 2.1 Create `src/nycgo_pipeline/directory_rules.py`

```python
"""
NYC.gov Agency Directory Eligibility Rules

This module is the SINGLE SOURCE OF TRUTH for directory eligibility logic.
Rules defined here are used for:
1. Evaluating record eligibility (True/False)
2. Generating reasoning strings (for golden dataset and UI)
3. Generating documentation (docs/DIRECTORY_LOGIC.md)

IMPORTANT: After changing rules, regenerate documentation:
    python scripts/generate_directory_docs.py

See docs/ARCHITECTURE_DIRECTORY_LOGIC.md for full architecture explanation.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional
import re

@dataclass
class Rule:
    """A single eligibility rule."""
    name: str
    description: str  # Human-readable, shown in UI and docs
    check: Callable[[dict], bool]
    category: str  # "gatekeeper", "type_specific", "exemption", "override"
    details_on_match: Optional[Callable[[dict], str]] = None  # For specific match info


# =============================================================================
# EXEMPTION LISTS
# =============================================================================

NONPROFIT_EXEMPTIONS = [
    "Brooklyn Public Library",
    "New York City Tourism + Conventions",
    "New York Public Library",
    "Queens Public Library",
    "Gracie Mansion Conservancy",
    "Mayor's Fund to Advance New York City",
]

ADVISORY_EXEMPTIONS = [
    "Board of Elections",
    "Campaign Finance Board",
    "Rent Guidelines Board",
]

PUBLISHED_EXPORT_EXCEPTIONS = [
    ("NYC_GOID_000354", "Office of Collective Bargaining"),
    ("NYC_GOID_000476", "MTA (Metropolitan Transportation Authority)"),
    ("NYC_GOID_100030", "Office of Digital Assets and Blockchain"),
]

# Manual overrides (empty by default)
MANUAL_OVERRIDE_TRUE = []
MANUAL_OVERRIDE_FALSE = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_state_nygov_url(url: str) -> bool:
    """Check if URL is state .ny.gov (not city .nyc.gov)."""
    if not url:
        return False
    has_ny_gov = bool(re.search(r'\.ny\.gov', url, re.IGNORECASE))
    has_nyc_gov = bool(re.search(r'\.nyc\.gov', url, re.IGNORECASE))
    return has_ny_gov and not has_nyc_gov

def has_main_nyc_gov_url(url: str) -> bool:
    """Check if URL is a main nyc.gov page (contains index.page)."""
    if not url:
        return False
    return bool(re.search(r'nyc\.gov', url, re.IGNORECASE) and
                re.search(r'index\.page', url, re.IGNORECASE))


# =============================================================================
# GATEKEEPER RULES (all must pass)
# =============================================================================

GATEKEEPER_RULES = [
    Rule(
        name="active_status",
        description="OperationalStatus must be 'Active'",
        check=lambda r: str(r.get('operational_status', '')).strip().lower() == 'active',
        category="gatekeeper",
    ),
    Rule(
        name="no_state_nygov_url",
        description="URL must not be state .ny.gov (city .nyc.gov is OK)",
        check=lambda r: not is_state_nygov_url(str(r.get('url', ''))),
        category="gatekeeper",
    ),
    Rule(
        name="has_contact_info",
        description="Must have at least one: URL, principal officer name, or officer contact URL",
        check=lambda r: bool(
            str(r.get('url', '')).strip() or
            str(r.get('principal_officer_full_name', '')).strip() or
            str(r.get('principal_officer_contact_url', '')).strip()
        ),
        category="gatekeeper",
    ),
]


# =============================================================================
# TYPE-SPECIFIC RULES (at least one must pass, after gatekeepers)
# =============================================================================

TYPE_SPECIFIC_RULES = [
    Rule(
        name="mayoral_agency",
        description="Mayoral Agency: always included",
        check=lambda r: r.get('organization_type') == 'Mayoral Agency',
        category="type_specific",
    ),
    Rule(
        name="mayoral_office",
        description="Mayoral Office: always included",
        check=lambda r: r.get('organization_type') == 'Mayoral Office',
        category="type_specific",
    ),
    Rule(
        name="elected_office",
        description="Elected Office: always included",
        check=lambda r: r.get('organization_type') == 'Elected Office',
        category="type_specific",
    ),
    Rule(
        name="pension_fund",
        description="Pension Fund: always included",
        check=lambda r: r.get('organization_type') == 'Pension Fund',
        category="type_specific",
    ),
    Rule(
        name="state_government_agency",
        description="State Government Agency: always included",
        check=lambda r: r.get('organization_type') == 'State Government Agency',
        category="type_specific",
    ),
    Rule(
        name="division_in_org_chart",
        description="Division: included if in Org Chart",
        check=lambda r: (
            r.get('organization_type') == 'Division' and
            str(r.get('in_org_chart', '')).strip().lower() in ('true', '1', 't', 'yes')
        ),
        category="type_specific",
    ),
    Rule(
        name="public_benefit_in_org_chart",
        description="Public Benefit or Development Organization: included if in Org Chart",
        check=lambda r: (
            r.get('organization_type') == 'Public Benefit or Development Organization' and
            str(r.get('in_org_chart', '')).strip().lower() in ('true', '1', 't', 'yes')
        ),
        category="type_specific",
    ),
    Rule(
        name="nonprofit_in_org_chart_or_exemption",
        description="Nonprofit Organization: included if in Org Chart OR in exemption list",
        check=lambda r: (
            r.get('organization_type') == 'Nonprofit Organization' and
            (str(r.get('in_org_chart', '')).strip().lower() in ('true', '1', 't', 'yes') or
             r.get('name') in NONPROFIT_EXEMPTIONS)
        ),
        category="type_specific",
        details_on_match=lambda r: (
            f"Exemption: {r.get('name')}" if r.get('name') in NONPROFIT_EXEMPTIONS
            else "In Org Chart"
        ),
    ),
    Rule(
        name="advisory_in_org_chart_or_url_or_exemption",
        description="Advisory or Regulatory Organization: included if in Org Chart, has main nyc.gov URL, OR in exemption list",
        check=lambda r: (
            r.get('organization_type') == 'Advisory or Regulatory Organization' and
            (str(r.get('in_org_chart', '')).strip().lower() in ('true', '1', 't', 'yes') or
             has_main_nyc_gov_url(str(r.get('url', ''))) or
             r.get('name') in ADVISORY_EXEMPTIONS)
        ),
        category="type_specific",
        details_on_match=lambda r: (
            f"Exemption: {r.get('name')}" if r.get('name') in ADVISORY_EXEMPTIONS
            else "Has main nyc.gov URL" if has_main_nyc_gov_url(str(r.get('url', '')))
            else "In Org Chart"
        ),
    ),
]


# =============================================================================
# EVALUATION ENGINE
# =============================================================================

@dataclass
class RuleResult:
    """Result of evaluating a single rule."""
    rule_name: str
    description: str
    passed: bool
    category: str
    details: Optional[str] = None


@dataclass
class EligibilityResult:
    """Complete eligibility evaluation result."""
    eligible: bool
    reasoning: str  # Human-readable summary
    reasoning_detailed: str  # Full details for debugging/audit
    rule_results: List[RuleResult]


def evaluate_eligibility(record: dict) -> EligibilityResult:
    """
    Evaluate a record's eligibility for NYC.gov Agency Directory.

    Returns eligibility status AND detailed reasoning.
    """
    results = []

    # Check manual overrides first
    record_id = record.get('record_id', '')
    if record_id in MANUAL_OVERRIDE_TRUE:
        return EligibilityResult(
            eligible=True,
            reasoning="Manual override: forced TRUE",
            reasoning_detailed="Manual override: forced TRUE",
            rule_results=[],
        )
    if record_id in MANUAL_OVERRIDE_FALSE:
        return EligibilityResult(
            eligible=False,
            reasoning="Manual override: forced FALSE",
            reasoning_detailed="Manual override: forced FALSE",
            rule_results=[],
        )

    # Evaluate gatekeeper rules
    for rule in GATEKEEPER_RULES:
        passed = rule.check(record)
        details = None
        if passed and rule.details_on_match:
            details = rule.details_on_match(record)
        results.append(RuleResult(
            rule_name=rule.name,
            description=rule.description,
            passed=passed,
            category=rule.category,
            details=details,
        ))

    # Check if all gatekeepers passed
    gatekeeper_results = [r for r in results if r.category == "gatekeeper"]
    all_gatekeepers_passed = all(r.passed for r in gatekeeper_results)

    if not all_gatekeepers_passed:
        # Failed gatekeepers - not eligible
        reasoning = format_reasoning(results, eligible=False)
        reasoning_detailed = format_reasoning_detailed(results)
        return EligibilityResult(
            eligible=False,
            reasoning=reasoning,
            reasoning_detailed=reasoning_detailed,
            rule_results=results,
        )

    # Evaluate type-specific rules
    for rule in TYPE_SPECIFIC_RULES:
        passed = rule.check(record)
        details = None
        if passed and rule.details_on_match:
            details = rule.details_on_match(record)
        results.append(RuleResult(
            rule_name=rule.name,
            description=rule.description,
            passed=passed,
            category=rule.category,
            details=details,
        ))

    # Check if any type-specific rule passed
    type_results = [r for r in results if r.category == "type_specific"]
    any_type_passed = any(r.passed for r in type_results)

    eligible = all_gatekeepers_passed and any_type_passed
    reasoning = format_reasoning(results, eligible=eligible)
    reasoning_detailed = format_reasoning_detailed(results)

    return EligibilityResult(
        eligible=eligible,
        reasoning=reasoning,
        reasoning_detailed=reasoning_detailed,
        rule_results=results,
    )


def format_reasoning(results: List[RuleResult], eligible: bool) -> str:
    """Format a concise reasoning string for display."""
    parts = []

    for r in results:
        if r.category == "gatekeeper":
            symbol = "✓" if r.passed else "✗"
            # Shorten description for display
            short_desc = r.description.split(":")[0] if ":" in r.description else r.description
            parts.append(f"{short_desc}: {symbol}")
        elif r.category == "type_specific" and r.passed:
            detail = f" ({r.details})" if r.details else ""
            parts.append(f"{r.description.split(':')[0]}{detail}: ✓")

    return " | ".join(parts)


def format_reasoning_detailed(results: List[RuleResult]) -> str:
    """Format detailed reasoning for audit/debugging."""
    lines = []

    lines.append("GATEKEEPER RULES (all must pass):")
    for r in results:
        if r.category == "gatekeeper":
            symbol = "✓" if r.passed else "✗"
            lines.append(f"  {symbol} {r.description}")

    lines.append("")
    lines.append("TYPE-SPECIFIC RULES (at least one must pass):")
    for r in results:
        if r.category == "type_specific":
            symbol = "✓" if r.passed else "✗"
            detail = f" [{r.details}]" if r.details else ""
            lines.append(f"  {symbol} {r.description}{detail}")

    return "\n".join(lines)
```

### 2.2 Architecture Documentation

Create `docs/ARCHITECTURE_DIRECTORY_LOGIC.md`:

```markdown
# Directory Logic Architecture

This document explains how NYC.gov Agency Directory eligibility is determined
and how the logic is kept in sync across documentation, code, and data.

## Single Source of Truth

All directory eligibility rules are defined in:
`src/nycgo_pipeline/directory_rules.py`

This single file is used for:
1. **Evaluation** - Determining if a record is eligible (True/False)
2. **Reasoning** - Generating human-readable explanation of why
3. **Documentation** - Auto-generating `docs/DIRECTORY_LOGIC.md`

## Making Changes

To change directory eligibility rules:

1. Edit rules in `src/nycgo_pipeline/directory_rules.py`
2. Run regression test: `python scripts/test_directory_regression.py`
3. Regenerate documentation: `python scripts/generate_directory_docs.py`
4. Commit all three: rules, test results (if changed), documentation

## Files

| File | Purpose | Editable? |
|------|---------|-----------|
| `src/nycgo_pipeline/directory_rules.py` | Rule definitions | YES - edit here |
| `docs/DIRECTORY_LOGIC.md` | Human-readable documentation | NO - auto-generated |
| `scripts/generate_directory_docs.py` | Documentation generator | Rarely |
| `scripts/test_directory_regression.py` | Regression test | Rarely |

## Rule Categories

1. **Gatekeeper Rules** - ALL must pass
   - Active status
   - No state .ny.gov URL
   - Has contact info

2. **Type-Specific Rules** - At least ONE must pass (after gatekeepers)
   - Organization type determines which rules apply
   - Some types always included (Mayoral Agency)
   - Some types conditional (Division: only if in Org Chart)
   - Some types have exemption lists (Nonprofit, Advisory)

3. **Manual Overrides** - Force True/False for specific records
```

### Acceptance Criteria
- [ ] `directory_rules.py` created with all current rules
- [ ] Architecture documentation created
- [ ] Rules match current `export_dataset.py` logic exactly

---

## Phase 3: Create Documentation Generator

### 3.1 Create `scripts/generate_directory_docs.py`

```python
#!/usr/bin/env python3
"""
Generate DIRECTORY_LOGIC.md from directory_rules.py

This script reads the rule definitions and generates human-readable
documentation. Run this after changing rules:

    python scripts/generate_directory_docs.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nycgo_pipeline.directory_rules import (
    GATEKEEPER_RULES,
    TYPE_SPECIFIC_RULES,
    NONPROFIT_EXEMPTIONS,
    ADVISORY_EXEMPTIONS,
    PUBLISHED_EXPORT_EXCEPTIONS,
)

def generate_docs() -> str:
    lines = [
        "# NYC.gov Agency Directory Logic",
        "",
        "<!-- DO NOT EDIT THIS FILE DIRECTLY -->",
        "<!-- This file is auto-generated from src/nycgo_pipeline/directory_rules.py -->",
        "<!-- To update, edit directory_rules.py and run: python scripts/generate_directory_docs.py -->",
        "",
        "## Overview",
        "",
        "This document describes the rules that determine whether an organization",
        "appears in the NYC.gov Agency Directory.",
        "",
        "## Gatekeeper Rules",
        "",
        "**ALL** of these must pass for a record to be considered:",
        "",
    ]

    for rule in GATEKEEPER_RULES:
        lines.append(f"- **{rule.name}**: {rule.description}")

    lines.extend([
        "",
        "## Type-Specific Rules",
        "",
        "After passing gatekeeper rules, **at least one** type-specific rule must pass:",
        "",
    ])

    for rule in TYPE_SPECIFIC_RULES:
        lines.append(f"- **{rule.name}**: {rule.description}")

    lines.extend([
        "",
        "## Exemption Lists",
        "",
        "### Nonprofit Exemptions",
        "",
        "These nonprofits are included even if not in Org Chart:",
        "",
    ])

    for name in NONPROFIT_EXEMPTIONS:
        lines.append(f"- {name}")

    lines.extend([
        "",
        "### Advisory Exemptions",
        "",
        "These advisory organizations are included even if not in Org Chart:",
        "",
    ])

    for name in ADVISORY_EXEMPTIONS:
        lines.append(f"- {name}")

    lines.extend([
        "",
        "### Published Export Exceptions",
        "",
        "These records are always included in the published export:",
        "",
    ])

    for record_id, name in PUBLISHED_EXPORT_EXCEPTIONS:
        lines.append(f"- `{record_id}`: {name}")

    lines.extend([
        "",
        "---",
        "",
        "*Auto-generated from `src/nycgo_pipeline/directory_rules.py`*",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    docs_path = Path(__file__).parent.parent / "docs" / "DIRECTORY_LOGIC.md"
    content = generate_docs()
    docs_path.write_text(content)
    print(f"Generated {docs_path}")
```

### Acceptance Criteria
- [ ] Script generates valid Markdown
- [ ] Generated docs match rule definitions
- [ ] "DO NOT EDIT" header included

---

## Phase 3.5: Directory Logic Changelog

### 3.5.1 Overview

Create an append-only changelog that tracks all changes to directory eligibility rules. This provides an audit trail for when rules are added, modified, or removed.

### 3.5.2 Files to Create

| File | Purpose |
|------|---------|
| `data/directory_logic_changelog.csv` | Append-only changelog of rule changes |
| `data/directory_rules_snapshot.json` | Snapshot of current rules (for diff detection) |

### 3.5.3 Changelog Schema

`data/directory_logic_changelog.csv`:

```csv
timestamp,changed_by,change_type,rule_name,category,old_value,new_value,commit_sha,notes
2024-12-09T15:30:00Z,npstorey,rule_added,new_rule_name,type_specific,,"New rule description",abc123,Initial addition
2024-12-10T10:00:00Z,npstorey,rule_modified,active_status,gatekeeper,"Old description","New description",def456,Clarified wording
2024-12-11T09:00:00Z,npstorey,exemption_added,nonprofit_exemptions,exemption,,"New Library Name",ghi789,Added per request
```

**Change Types:**
- `rule_added` - New rule added
- `rule_modified` - Existing rule description/logic changed
- `rule_removed` - Rule deleted
- `exemption_added` - New item added to exemption list
- `exemption_removed` - Item removed from exemption list

### 3.5.4 Update `generate_directory_docs.py`

Modify the script to:
1. Load current rules from `directory_rules.py`
2. Load previous snapshot from `directory_rules_snapshot.json` (if exists)
3. Compare and detect changes
4. If changes found:
   - Append entries to `data/directory_logic_changelog.csv`
   - Update `directory_rules_snapshot.json`
5. Generate `DIRECTORY_LOGIC.md` with recent changes summary at top

```python
#!/usr/bin/env python3
"""
Generate DIRECTORY_LOGIC.md from directory_rules.py

Also maintains:
- data/directory_rules_snapshot.json (for change detection)
- data/directory_logic_changelog.csv (audit trail)

Usage:
    python scripts/generate_directory_docs.py
    python scripts/generate_directory_docs.py --changed-by "username"
"""

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ... imports ...

CHANGELOG_PATH = Path(__file__).parent.parent / "data" / "directory_logic_changelog.csv"
SNAPSHOT_PATH = Path(__file__).parent.parent / "data" / "directory_rules_snapshot.json"

CHANGELOG_FIELDS = [
    "timestamp",
    "changed_by",
    "change_type",
    "rule_name",
    "category",
    "old_value",
    "new_value",
    "commit_sha",
    "notes",
]


def get_current_commit_sha() -> str:
    """Get current git commit SHA, or empty string if not in git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()[:7]
    except Exception:
        return ""


def rules_to_dict() -> dict:
    """Convert current rules to a dict for snapshot/comparison."""
    return {
        "gatekeeper_rules": [
            {"name": r.name, "description": r.description, "category": r.category}
            for r in GATEKEEPER_RULES
        ],
        "type_specific_rules": [
            {"name": r.name, "description": r.description, "category": r.category}
            for r in TYPE_SPECIFIC_RULES
        ],
        "nonprofit_exemptions": NONPROFIT_EXEMPTIONS,
        "advisory_exemptions": ADVISORY_EXEMPTIONS,
        "published_export_exceptions": [
            {"record_id": r[0], "name": r[1]} for r in PUBLISHED_EXPORT_EXCEPTIONS
        ],
    }


def load_snapshot() -> dict:
    """Load previous snapshot, or return empty dict if not exists."""
    if SNAPSHOT_PATH.exists():
        return json.loads(SNAPSHOT_PATH.read_text())
    return {}


def save_snapshot(snapshot: dict):
    """Save current rules snapshot."""
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2))


def detect_changes(old: dict, new: dict) -> list[dict]:
    """Detect changes between old and new snapshots."""
    changes = []

    # Compare rules
    for rule_type in ["gatekeeper_rules", "type_specific_rules"]:
        old_rules = {r["name"]: r for r in old.get(rule_type, [])}
        new_rules = {r["name"]: r for r in new.get(rule_type, [])}

        # Added rules
        for name in set(new_rules) - set(old_rules):
            changes.append({
                "change_type": "rule_added",
                "rule_name": name,
                "category": new_rules[name]["category"],
                "old_value": "",
                "new_value": new_rules[name]["description"],
            })

        # Removed rules
        for name in set(old_rules) - set(new_rules):
            changes.append({
                "change_type": "rule_removed",
                "rule_name": name,
                "category": old_rules[name]["category"],
                "old_value": old_rules[name]["description"],
                "new_value": "",
            })

        # Modified rules
        for name in set(old_rules) & set(new_rules):
            if old_rules[name]["description"] != new_rules[name]["description"]:
                changes.append({
                    "change_type": "rule_modified",
                    "rule_name": name,
                    "category": new_rules[name]["category"],
                    "old_value": old_rules[name]["description"],
                    "new_value": new_rules[name]["description"],
                })

    # Compare exemption lists
    for list_name in ["nonprofit_exemptions", "advisory_exemptions"]:
        old_items = set(old.get(list_name, []))
        new_items = set(new.get(list_name, []))

        for item in new_items - old_items:
            changes.append({
                "change_type": "exemption_added",
                "rule_name": list_name,
                "category": "exemption",
                "old_value": "",
                "new_value": item,
            })

        for item in old_items - new_items:
            changes.append({
                "change_type": "exemption_removed",
                "rule_name": list_name,
                "category": "exemption",
                "old_value": item,
                "new_value": "",
            })

    return changes


def append_changelog(changes: list[dict], changed_by: str):
    """Append changes to changelog CSV."""
    CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_exists = CHANGELOG_PATH.exists() and CHANGELOG_PATH.stat().st_size > 0
    timestamp = datetime.now(timezone.utc).isoformat()
    commit_sha = get_current_commit_sha()

    with CHANGELOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANGELOG_FIELDS)
        if not file_exists:
            writer.writeheader()

        for change in changes:
            writer.writerow({
                "timestamp": timestamp,
                "changed_by": changed_by,
                "change_type": change["change_type"],
                "rule_name": change["rule_name"],
                "category": change["category"],
                "old_value": change["old_value"],
                "new_value": change["new_value"],
                "commit_sha": commit_sha,
                "notes": "",
            })

    print(f"Appended {len(changes)} changes to {CHANGELOG_PATH}")


def get_recent_changes(limit: int = 5) -> list[dict]:
    """Get recent changelog entries for docs summary."""
    if not CHANGELOG_PATH.exists():
        return []

    with CHANGELOG_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        entries = list(reader)

    return entries[-limit:][::-1]  # Most recent first


def generate_docs_with_changelog() -> str:
    """Generate docs including recent changes summary."""
    lines = [
        "# NYC.gov Agency Directory Logic",
        "",
        "<!-- DO NOT EDIT THIS FILE DIRECTLY -->",
        "<!-- Auto-generated from src/nycgo_pipeline/directory_rules.py -->",
        "<!-- To update: edit directory_rules.py, then run: python scripts/generate_directory_docs.py -->",
        "",
    ]

    # Add recent changes summary
    recent = get_recent_changes(5)
    if recent:
        lines.extend([
            "## Recent Changes",
            "",
            "| Date | Change | Rule | Details |",
            "|------|--------|------|---------|",
        ])
        for entry in recent:
            date = entry["timestamp"][:10]
            change_type = entry["change_type"].replace("_", " ").title()
            rule = entry["rule_name"]
            details = entry["new_value"][:50] + "..." if len(entry.get("new_value", "")) > 50 else entry.get("new_value", "")
            lines.append(f"| {date} | {change_type} | {rule} | {details} |")

        lines.extend([
            "",
            f"*See `data/directory_logic_changelog.csv` for full history.*",
            "",
            "---",
            "",
        ])

    # ... rest of generate_docs() ...

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-by", default="unknown", help="Who made the changes")
    args = parser.parse_args()

    # Get current rules as dict
    current = rules_to_dict()
    previous = load_snapshot()

    # Detect and log changes
    if previous:
        changes = detect_changes(previous, current)
        if changes:
            print(f"Detected {len(changes)} changes:")
            for c in changes:
                print(f"  - {c['change_type']}: {c['rule_name']}")
            append_changelog(changes, args.changed_by)
        else:
            print("No changes detected")
    else:
        print("No previous snapshot - creating initial snapshot")

    # Save current snapshot
    save_snapshot(current)

    # Generate docs
    docs_path = Path(__file__).parent.parent / "docs" / "DIRECTORY_LOGIC.md"
    content = generate_docs_with_changelog()
    docs_path.write_text(content)
    print(f"Generated {docs_path}")
```

### 3.5.5 Example Output in DIRECTORY_LOGIC.md

```markdown
# NYC.gov Agency Directory Logic

<!-- DO NOT EDIT THIS FILE DIRECTLY -->

## Recent Changes

| Date | Change | Rule | Details |
|------|--------|------|---------|
| 2024-12-10 | Rule Modified | active_status | OperationalStatus must be 'Active' |
| 2024-12-09 | Exemption Added | nonprofit_exemptions | New Library Name |
| 2024-12-08 | Rule Added | new_advisory_rule | Advisory orgs with special criteria |

*See `data/directory_logic_changelog.csv` for full history.*

---

## Overview
...
```

### Acceptance Criteria
- [ ] `directory_logic_changelog.csv` created with proper schema
- [ ] `directory_rules_snapshot.json` stores current rule state
- [ ] Script detects added/modified/removed rules
- [ ] Script detects exemption list changes
- [ ] Changes appended to changelog with timestamp, author, commit SHA
- [ ] Generated docs include "Recent Changes" summary section
- [ ] Changelog location consistent with existing `data/changelog.csv`

---

## Phase 4: Create Regression Test Script

### 4.1 Create `scripts/test_directory_regression.py`

```python
#!/usr/bin/env python3
"""
Regression test for directory eligibility logic.

Compares the new rules-based evaluation against the current published dataset
to ensure refactoring doesn't change any values.

Usage:
    # Create baseline (run once before refactoring)
    python scripts/test_directory_regression.py --create-baseline

    # Run regression test
    python scripts/test_directory_regression.py

    # Run with verbose diff output
    python scripts/test_directory_regression.py --verbose
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

BASELINE_PATH = Path(__file__).parent.parent / "tests" / "directory_baseline.csv"
PUBLISHED_PATH = Path(__file__).parent.parent / "data" / "published" / "latest" / "NYCGovernanceOrganizations_latest.csv"


def create_baseline():
    """Create baseline snapshot from current published dataset."""
    print(f"Reading published dataset from {PUBLISHED_PATH}")
    df = pd.read_csv(PUBLISHED_PATH, dtype=str).fillna("")

    baseline = df[["record_id", "listed_in_nyc_gov_agency_directory"]].copy()

    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(BASELINE_PATH, index=False)
    print(f"Created baseline with {len(baseline)} records at {BASELINE_PATH}")


def run_regression_test(verbose: bool = False):
    """Compare new evaluation against baseline."""
    from nycgo_pipeline.directory_rules import evaluate_eligibility

    if not BASELINE_PATH.exists():
        print(f"ERROR: Baseline not found at {BASELINE_PATH}")
        print("Run with --create-baseline first")
        sys.exit(1)

    print(f"Loading baseline from {BASELINE_PATH}")
    baseline = pd.read_csv(BASELINE_PATH, dtype=str).fillna("")

    print(f"Loading published dataset from {PUBLISHED_PATH}")
    published = pd.read_csv(PUBLISHED_PATH, dtype=str).fillna("")

    print(f"Evaluating {len(published)} records with new rules...")

    differences = []

    for _, row in published.iterrows():
        record = row.to_dict()
        result = evaluate_eligibility(record)

        new_value = "True" if result.eligible else "False"
        old_value = baseline[baseline["record_id"] == record["record_id"]]["listed_in_nyc_gov_agency_directory"].iloc[0]

        # Normalize for comparison
        old_normalized = "True" if old_value.lower() in ("true", "1") else "False"

        if new_value != old_normalized:
            differences.append({
                "record_id": record["record_id"],
                "name": record.get("name", ""),
                "old_value": old_value,
                "new_value": new_value,
                "reasoning": result.reasoning,
            })

    if differences:
        print(f"\nDIFFERENCES FOUND: {len(differences)} records")
        print("=" * 60)

        for diff in differences:
            print(f"\n{diff['record_id']}: {diff['name']}")
            print(f"  Old: {diff['old_value']}")
            print(f"  New: {diff['new_value']}")
            if verbose:
                print(f"  Reasoning: {diff['reasoning']}")

        print("\n" + "=" * 60)
        print("REGRESSION TEST FAILED")
        print("Review differences above. If intentional, update baseline with --create-baseline")
        sys.exit(1)
    else:
        print("\nSUCCESS: No differences found")
        print("Regression test passed - new rules produce identical results")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Directory eligibility regression test")
    parser.add_argument("--create-baseline", action="store_true", help="Create baseline snapshot")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed reasoning for differences")
    args = parser.parse_args()

    if args.create_baseline:
        create_baseline()
    else:
        run_regression_test(verbose=args.verbose)
```

### 4.2 Create tests directory

```bash
mkdir -p tests/
echo "# Test artifacts" > tests/.gitkeep
```

### Acceptance Criteria
- [ ] Baseline can be created from current published data
- [ ] Regression test compares new evaluation to baseline
- [ ] Differences are clearly reported with record details
- [ ] Script returns non-zero exit code on failure (for CI)

---

## Phase 5: Integrate with Pipeline

### 5.1 Update `export_dataset.py`

Replace the current `add_nycgov_directory_column` function to use the new rules module:

```python
from nycgo_pipeline.directory_rules import evaluate_eligibility

def add_nycgov_directory_column(df, ...):
    """
    Applies directory eligibility rules using the centralized rules module.

    See src/nycgo_pipeline/directory_rules.py for rule definitions.
    See docs/DIRECTORY_LOGIC.md for documentation.
    """
    df_processed = df.copy()

    for idx, row in df_processed.iterrows():
        record = row.to_dict()
        result = evaluate_eligibility(record)

        df_processed.loc[idx, "listed_in_nyc_gov_agency_directory"] = result.eligible
        df_processed.loc[idx, "directory_eligibility_reason"] = result.reasoning

    return df_processed
```

### 5.2 Add Reasoning Field to Golden Dataset

The `directory_eligibility_reason` field will be added to the golden dataset during export.

### Acceptance Criteria
- [ ] `export_dataset.py` uses new rules module
- [ ] `directory_eligibility_reason` field populated
- [ ] Regression test passes after integration

---

## Phase 6: Update Edit UI

### 6.1 Display Reasoning in Edit Modal

Update `nycgo-admin-ui/js/app.js` to display the reasoning field when viewing a record.

### 6.2 UI Design

When viewing a record in the Edit modal:

```
NYC.gov Agency Directory: ✅ True

Why: OperationalStatus: ✓ | No state URL: ✓ | Has contact: ✓ | Mayoral Agency: ✓

📖 View directory logic documentation
```

Or for ineligible:

```
NYC.gov Agency Directory: ❌ False

Why: OperationalStatus: ✓ | No state URL: ✓ | Has contact: ✓ | Division (not in Org Chart): ✗

📖 View directory logic documentation
```

### 6.3 Link to Documentation

Add link to `docs/DIRECTORY_LOGIC.md` (or hosted version) for users who want full details.

### Acceptance Criteria
- [ ] Reasoning displayed in Edit modal
- [ ] Link to documentation provided
- [ ] Works for both eligible and ineligible records

---

## Phase 7: Update FUTURE.md

Add CI check option for future consideration:

```markdown
### Future: CI Check for Directory Docs

Add CI step to verify docs are regenerated when rules change:

\`\`\`yaml
- name: Check directory docs up to date
  run: |
    python scripts/generate_directory_docs.py
    if ! git diff --exit-code docs/DIRECTORY_LOGIC.md; then
      echo "ERROR: Directory rules changed but docs not regenerated"
      exit 1
    fi
\`\`\`
```

### Acceptance Criteria
- [ ] FUTURE.md updated with CI check option

---

## Testing Plan

### Regression Testing Workflow

1. **Before any code changes:**
   ```bash
   python scripts/test_directory_regression.py --create-baseline
   ```

2. **After implementing new rules module:**
   ```bash
   python scripts/test_directory_regression.py --verbose
   ```

3. **If differences found:**
   - Investigate each difference
   - Determine if old or new is correct
   - Fix code or update baseline as appropriate

4. **After all tests pass:**
   - Run full pipeline in test mode
   - Verify outputs match expected

### Integration Testing

1. Switch to test mode (TEST_MODE=true)
2. Submit a test edit through Admin UI
3. Verify pipeline runs successfully
4. Check that `directory_eligibility_reason` field is populated
5. Verify Edit UI displays reasoning correctly

---

## Files Summary

### New Files

| File | Purpose |
|------|---------|
| `src/nycgo_pipeline/directory_rules.py` | Rule definitions (SINGLE SOURCE OF TRUTH) |
| `scripts/generate_directory_docs.py` | Documentation generator + changelog maintainer |
| `scripts/test_directory_regression.py` | Regression test |
| `docs/DIRECTORY_LOGIC.md` | Auto-generated documentation (with recent changes) |
| `docs/ARCHITECTURE_DIRECTORY_LOGIC.md` | Architecture explanation |
| `data/directory_logic_changelog.csv` | Append-only changelog of rule changes |
| `data/directory_rules_snapshot.json` | Snapshot for change detection |
| `tests/directory_baseline.csv` | Regression test baseline |

### Modified Files

| File | Changes |
|------|---------|
| `scripts/process/export_dataset.py` | Use new rules module |
| `nycgo-admin-ui/js/app.js` | Display reasoning in Edit modal |
| `nycgo-admin-ui/index.html` | Add reasoning display section |
| `.github/workflows/process-edit.yml` | Rename DEMO_MODE to TEST_MODE |
| `docs/sprints/FUTURE.md` | Add CI check option |

---

## Definition of Done

- [ ] DEMO_MODE renamed to TEST_MODE everywhere
- [ ] `directory_rules.py` created with all current rules
- [ ] `generate_directory_docs.py` creates valid documentation
- [ ] `directory_logic_changelog.csv` tracks rule changes
- [ ] `directory_rules_snapshot.json` stores current state for diffing
- [ ] Generated docs include "Recent Changes" summary
- [ ] `test_directory_regression.py` works and passes
- [ ] `export_dataset.py` uses new rules module
- [ ] Regression test confirms no value changes
- [ ] `directory_eligibility_reason` field added to golden dataset
- [ ] Edit UI displays reasoning for each record
- [ ] Link to documentation in Edit UI
- [ ] Architecture documentation complete
- [ ] FUTURE.md updated with CI check option
- [ ] All changes tested with full pipeline run in test mode
