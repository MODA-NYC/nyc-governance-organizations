#!/usr/bin/env python3
"""
Generate DIRECTORY_LOGIC.md from directory_rules.py

This script reads the rule definitions and generates human-readable
documentation. It also maintains a changelog of rule changes.

Outputs:
- docs/DIRECTORY_LOGIC.md (auto-generated documentation)
- data/directory_rules_snapshot.json (for change detection)
- data/directory_logic_changelog.csv (audit trail)

Usage:
    python scripts/generate_directory_docs.py
    python scripts/generate_directory_docs.py --changed-by "username"
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nycgo_pipeline.directory_rules import (
    ADVISORY_EXEMPTIONS,
    GATEKEEPER_RULES,
    MANUAL_OVERRIDE_FALSE,
    MANUAL_OVERRIDE_TRUE,
    NONPROFIT_EXEMPTIONS,
    PUBLISHED_EXPORT_EXCEPTIONS,
    STATE_GOVERNMENT_EXEMPTIONS,
    TYPE_SPECIFIC_RULES,
)

# Paths
DOCS_PATH = Path(__file__).parent.parent / "docs" / "DIRECTORY_LOGIC.md"
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
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent,
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
        "nonprofit_exemptions": sorted(NONPROFIT_EXEMPTIONS),
        "advisory_exemptions": sorted(ADVISORY_EXEMPTIONS),
        "state_government_exemptions": sorted(STATE_GOVERNMENT_EXEMPTIONS),
        "published_export_exceptions": [
            {"record_id": r[0], "name": r[1]} for r in PUBLISHED_EXPORT_EXCEPTIONS
        ],
        "manual_override_true": sorted(MANUAL_OVERRIDE_TRUE),
        "manual_override_false": sorted(MANUAL_OVERRIDE_FALSE),
    }


def load_snapshot() -> dict:
    """Load previous snapshot, or return empty dict if not exists."""
    if SNAPSHOT_PATH.exists():
        return json.loads(SNAPSHOT_PATH.read_text())
    return {}


def save_snapshot(snapshot: dict) -> None:
    """Save current rules snapshot."""
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, sort_keys=True))


def detect_changes(old: dict, new: dict) -> list[dict]:  # noqa: C901
    """Detect changes between old and new snapshots."""
    changes = []

    # Compare rules
    for rule_type in ["gatekeeper_rules", "type_specific_rules"]:
        old_rules = {r["name"]: r for r in old.get(rule_type, [])}
        new_rules = {r["name"]: r for r in new.get(rule_type, [])}

        # Added rules
        for name in set(new_rules) - set(old_rules):
            changes.append(
                {
                    "change_type": "rule_added",
                    "rule_name": name,
                    "category": new_rules[name]["category"],
                    "old_value": "",
                    "new_value": new_rules[name]["description"],
                }
            )

        # Removed rules
        for name in set(old_rules) - set(new_rules):
            changes.append(
                {
                    "change_type": "rule_removed",
                    "rule_name": name,
                    "category": old_rules[name]["category"],
                    "old_value": old_rules[name]["description"],
                    "new_value": "",
                }
            )

        # Modified rules
        for name in set(old_rules) & set(new_rules):
            if old_rules[name]["description"] != new_rules[name]["description"]:
                changes.append(
                    {
                        "change_type": "rule_modified",
                        "rule_name": name,
                        "category": new_rules[name]["category"],
                        "old_value": old_rules[name]["description"],
                        "new_value": new_rules[name]["description"],
                    }
                )

    # Compare exemption lists
    exemption_lists = [
        ("nonprofit_exemptions", "exemption"),
        ("advisory_exemptions", "exemption"),
        ("state_government_exemptions", "exemption"),
        ("manual_override_true", "override"),
        ("manual_override_false", "override"),
    ]

    for list_name, category in exemption_lists:
        old_items = set(old.get(list_name, []))
        new_items = set(new.get(list_name, []))

        for item in new_items - old_items:
            changes.append(
                {
                    "change_type": "exemption_added",
                    "rule_name": list_name,
                    "category": category,
                    "old_value": "",
                    "new_value": item,
                }
            )

        for item in old_items - new_items:
            changes.append(
                {
                    "change_type": "exemption_removed",
                    "rule_name": list_name,
                    "category": category,
                    "old_value": item,
                    "new_value": "",
                }
            )

    # Compare published export exceptions
    old_exceptions = {
        e["record_id"]: e for e in old.get("published_export_exceptions", [])
    }
    new_exceptions = {
        e["record_id"]: e for e in new.get("published_export_exceptions", [])
    }

    for record_id in set(new_exceptions) - set(old_exceptions):
        changes.append(
            {
                "change_type": "exemption_added",
                "rule_name": "published_export_exceptions",
                "category": "exemption",
                "old_value": "",
                "new_value": f"{record_id}: {new_exceptions[record_id]['name']}",
            }
        )

    for record_id in set(old_exceptions) - set(new_exceptions):
        changes.append(
            {
                "change_type": "exemption_removed",
                "rule_name": "published_export_exceptions",
                "category": "exemption",
                "old_value": f"{record_id}: {old_exceptions[record_id]['name']}",
                "new_value": "",
            }
        )

    return changes


def append_changelog(changes: list[dict], changed_by: str) -> None:
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
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "changed_by": changed_by,
                    "change_type": change["change_type"],
                    "rule_name": change["rule_name"],
                    "category": change["category"],
                    "old_value": change["old_value"],
                    "new_value": change["new_value"],
                    "commit_sha": commit_sha,
                    "notes": "",
                }
            )

    print(f"Appended {len(changes)} changes to {CHANGELOG_PATH}")


def get_recent_changes(limit: int = 5) -> list[dict]:
    """Get recent changelog entries for docs summary."""
    if not CHANGELOG_PATH.exists():
        return []

    with CHANGELOG_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        entries = list(reader)

    return entries[-limit:][::-1]  # Most recent first


def generate_docs() -> str:  # noqa: C901
    """Generate documentation including recent changes summary."""
    lines = [
        "# NYC.gov Agency Directory Logic",
        "",
        "<!-- DO NOT EDIT THIS FILE DIRECTLY -->",
        "<!-- Auto-generated from src/nycgo_pipeline/directory_rules.py -->",
        "<!-- To update: edit directory_rules.py, then run: -->",
        "<!-- python scripts/generate_directory_docs.py --changed-by 'username' -->",
        "",
    ]

    # Add recent changes summary
    recent = get_recent_changes(5)
    if recent:
        lines.extend(
            [
                "## Recent Changes",
                "",
                "| Date | Change | Rule | Details |",
                "|------|--------|------|---------|",
            ]
        )
        for entry in recent:
            date = entry["timestamp"][:10]
            change_type = entry["change_type"].replace("_", " ").title()
            rule = entry["rule_name"]
            new_val = entry.get("new_value", "")
            details = (new_val[:50] + "...") if len(new_val) > 50 else new_val
            lines.append(f"| {date} | {change_type} | {rule} | {details} |")

        lines.extend(
            [
                "",
                "*See `data/directory_logic_changelog.csv` for full history.*",
                "",
                "---",
                "",
            ]
        )

    # Overview
    lines.extend(
        [
            "## Overview",
            "",
            "This document describes the rules that determine whether an organization",
            "appears in the NYC.gov Agency Directory. These rules are defined in",
            "`src/nycgo_pipeline/directory_rules.py`.",
            "",
            "---",
            "",
        ]
    )

    # Gatekeeper rules
    lines.extend(
        [
            "## Gatekeeper Rules",
            "",
            "**ALL** of these must pass for a record to be considered:",
            "",
        ]
    )
    for rule in GATEKEEPER_RULES:
        lines.append(f"- **{rule.name}**: {rule.description}")

    lines.extend(["", "---", ""])

    # Type-specific rules
    lines.extend(
        [
            "## Type-Specific Rules",
            "",
            "After passing gatekeeper rules, "
            "**at least one** type-specific rule must pass:",
            "",
        ]
    )
    for rule in TYPE_SPECIFIC_RULES:
        lines.append(f"- **{rule.name}**: {rule.description}")

    lines.extend(["", "---", ""])

    # Exemption lists
    lines.extend(
        [
            "## Exemption Lists",
            "",
            "### Nonprofit Exemptions",
            "",
            "These nonprofits are included even if not in Org Chart:",
            "",
        ]
    )
    for name in sorted(NONPROFIT_EXEMPTIONS):
        lines.append(f"- {name}")

    lines.extend(
        [
            "",
            "### Advisory Exemptions",
            "",
            "These advisory organizations are included even if not in Org Chart:",
            "",
        ]
    )
    for name in sorted(ADVISORY_EXEMPTIONS):
        lines.append(f"- {name}")

    lines.extend(
        [
            "",
            "### State Government Exemptions",
            "",
            "These NYC-affiliated state agencies are included in the directory:",
            "",
        ]
    )
    for name in sorted(STATE_GOVERNMENT_EXEMPTIONS):
        lines.append(f"- {name}")

    lines.extend(
        [
            "",
            "### Published Export Exceptions",
            "",
            "These records are always included in the published export:",
            "",
        ]
    )
    for record_id, name in PUBLISHED_EXPORT_EXCEPTIONS:
        lines.append(f"- `{record_id}`: {name}")

    # Manual overrides
    if MANUAL_OVERRIDE_TRUE or MANUAL_OVERRIDE_FALSE:
        lines.extend(["", "---", "", "## Manual Overrides", ""])

        if MANUAL_OVERRIDE_TRUE:
            lines.extend(["", "### Force TRUE", ""])
            for record_id in MANUAL_OVERRIDE_TRUE:
                lines.append(f"- `{record_id}`")

        if MANUAL_OVERRIDE_FALSE:
            lines.extend(["", "### Force FALSE", ""])
            for record_id in MANUAL_OVERRIDE_FALSE:
                lines.append(f"- `{record_id}`")

    lines.extend(
        [
            "",
            "---",
            "",
            "*Auto-generated from `src/nycgo_pipeline/directory_rules.py`*",
            "",
            "*See [ARCHITECTURE_DIRECTORY_LOGIC.md]"
            "(ARCHITECTURE_DIRECTORY_LOGIC.md) for how this system works.*",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate directory logic documentation from rules"
    )
    parser.add_argument(
        "--changed-by",
        default="unknown",
        help="Who made the changes (for changelog)",
    )
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
            print("No changes detected in rules")
    else:
        print("No previous snapshot found - creating initial snapshot")
        print("(First run won't log changes to changelog)")

    # Save current snapshot
    save_snapshot(current)
    print(f"Updated snapshot at {SNAPSHOT_PATH}")

    # Generate docs
    content = generate_docs()
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text(content)
    print(f"Generated documentation at {DOCS_PATH}")


if __name__ == "__main__":
    main()
