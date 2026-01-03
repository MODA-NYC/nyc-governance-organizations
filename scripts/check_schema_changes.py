#!/usr/bin/env python3
"""
check_schema_changes.py - Detect schema changes between releases.

Compares the current Table Schema against the previous release's schema
and outputs a summary of changes. Used by the release workflow to include
schema change information in release notes.

Usage:
    python scripts/check_schema_changes.py [--output FILE] [--previous-tag TAG]

Output:
    - Prints summary to stdout
    - Optionally writes markdown to --output file for release notes
    - Exit code 0: no changes or changes detected successfully
    - Exit code 1: error (couldn't compare)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_previous_release_tag() -> str | None:
    """Get the most recent release tag (excluding test tags)."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = result.stdout.strip().split("\n")
        # Filter out test tags
        release_tags = [t for t in tags if t and "-test" not in t]
        return release_tags[0] if release_tags else None
    except subprocess.CalledProcessError:
        return None


def get_schema_from_tag(tag: str, schema_path: str) -> dict | None:
    """Retrieve schema JSON from a specific git tag."""
    try:
        result = subprocess.run(
            ["git", "show", f"{tag}:{schema_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def load_current_schema(schema_path: str) -> dict | None:
    """Load the current schema from disk."""
    try:
        with open(schema_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _compare_field(old_field: dict, new_field: dict) -> list:
    """Compare two field definitions and return list of changes."""
    field_changes = []

    # Check type change
    if old_field.get("type") != new_field.get("type"):
        field_changes.append(
            {
                "property": "type",
                "old": old_field.get("type"),
                "new": new_field.get("type"),
            }
        )

    # Check constraints change
    old_constraints = old_field.get("constraints", {})
    new_constraints = new_field.get("constraints", {})
    if old_constraints != new_constraints:
        all_keys = set(old_constraints.keys()) | set(new_constraints.keys())
        for key in all_keys:
            old_val = old_constraints.get(key)
            new_val = new_constraints.get(key)
            if old_val != new_val:
                field_changes.append(
                    {
                        "property": f"constraints.{key}",
                        "old": old_val,
                        "new": new_val,
                    }
                )

    # Check format change
    if old_field.get("format") != new_field.get("format"):
        field_changes.append(
            {
                "property": "format",
                "old": old_field.get("format"),
                "new": new_field.get("format"),
            }
        )

    return field_changes


def compare_schemas(old_schema: dict, new_schema: dict) -> dict:
    """
    Compare two schemas and return a dict of changes.

    Returns:
        {
            "has_changes": bool,
            "version_change": {"old": str, "new": str} | None,
            "fields_added": [{"name": str, "type": str, "description": str}],
            "fields_removed": [{"name": str, "type": str}],
            "fields_modified": [{"name": str, "changes": [...]}],
        }
    """
    changes = {
        "has_changes": False,
        "version_change": None,
        "fields_added": [],
        "fields_removed": [],
        "fields_modified": [],
    }

    # Compare versions
    old_version = old_schema.get("version", "unknown")
    new_version = new_schema.get("version", "unknown")
    if old_version != new_version:
        changes["version_change"] = {"old": old_version, "new": new_version}
        changes["has_changes"] = True

    # Build field lookups
    old_fields = {f["name"]: f for f in old_schema.get("fields", [])}
    new_fields = {f["name"]: f for f in new_schema.get("fields", [])}

    old_names = set(old_fields.keys())
    new_names = set(new_fields.keys())

    # Fields added
    for name in sorted(new_names - old_names):
        field = new_fields[name]
        changes["fields_added"].append(
            {
                "name": name,
                "type": field.get("type", "string"),
                "description": field.get("description", ""),
            }
        )
        changes["has_changes"] = True

    # Fields removed
    for name in sorted(old_names - new_names):
        field = old_fields[name]
        changes["fields_removed"].append(
            {
                "name": name,
                "type": field.get("type", "string"),
            }
        )
        changes["has_changes"] = True

    # Fields modified (same name, different definition)
    for name in sorted(old_names & new_names):
        field_changes = _compare_field(old_fields[name], new_fields[name])
        if field_changes:
            changes["fields_modified"].append({"name": name, "changes": field_changes})
            changes["has_changes"] = True

    return changes


def format_changes_markdown(changes: dict, schema_name: str, previous_tag: str) -> str:
    """Format schema changes as markdown for release notes."""
    if not changes["has_changes"]:
        return ""

    lines = [
        "## Schema Changes",
        "",
        f"Changes detected in `{schema_name}` since `{previous_tag}`:",
        "",
    ]

    if changes["version_change"]:
        old_v = changes["version_change"]["old"]
        new_v = changes["version_change"]["new"]
        lines.append(f"**Schema version:** {old_v} → {new_v}")
        lines.append("")

    if changes["fields_added"]:
        lines.append("**Fields added:**")
        for field in changes["fields_added"]:
            desc = f" - {field['description']}" if field["description"] else ""
            lines.append(f"- `{field['name']}` ({field['type']}){desc}")
        lines.append("")

    if changes["fields_removed"]:
        lines.append("**Fields removed:**")
        for field in changes["fields_removed"]:
            lines.append(f"- `{field['name']}` ({field['type']})")
        lines.append("")

    if changes["fields_modified"]:
        lines.append("**Fields modified:**")
        for field in changes["fields_modified"]:
            lines.append(f"- `{field['name']}`:")
            for change in field["changes"]:
                lines.append(
                    f"  - {change['property']}: `{change['old']}` → `{change['new']}`"
                )
        lines.append("")

    lines.append("_Please update `schemas/SCHEMA_CHANGELOG.md` with these changes._")
    lines.append("")

    return "\n".join(lines)


def format_changes_summary(changes: dict, previous_tag: str) -> str:
    """Format a brief summary for stdout."""
    if not changes["has_changes"]:
        return f"No schema changes since {previous_tag}"

    parts = []
    if changes["fields_added"]:
        parts.append(f"+{len(changes['fields_added'])} fields")
    if changes["fields_removed"]:
        parts.append(f"-{len(changes['fields_removed'])} fields")
    if changes["fields_modified"]:
        parts.append(f"~{len(changes['fields_modified'])} modified")
    if changes["version_change"]:
        old_v = changes["version_change"]["old"]
        new_v = changes["version_change"]["new"]
        parts.append(f"version {old_v}→{new_v}")

    return f"Schema changes since {previous_tag}: {', '.join(parts)}"


def main():
    parser = argparse.ArgumentParser(
        description="Detect schema changes between releases"
    )
    parser.add_argument(
        "--schema",
        default="schemas/nycgo_golden_dataset.tableschema.json",
        help="Path to current schema file",
    )
    parser.add_argument(
        "--previous-tag",
        help="Previous release tag to compare against (auto-detected if not provided)",
    )
    parser.add_argument(
        "--output",
        help="Write markdown summary to this file (for release notes)",
    )
    parser.add_argument(
        "--json",
        help="Write JSON changes to this file",
    )

    args = parser.parse_args()

    # Load current schema
    current_schema = load_current_schema(args.schema)
    if not current_schema:
        print(
            f"Error: Could not load current schema from {args.schema}", file=sys.stderr
        )
        sys.exit(1)

    # Get previous tag
    previous_tag = args.previous_tag or get_previous_release_tag()
    if not previous_tag:
        print(
            "No previous release tag found. Skipping schema comparison.",
            file=sys.stderr,
        )
        # Not an error - just no previous release to compare
        if args.output:
            Path(args.output).write_text("")
        sys.exit(0)

    # Load previous schema
    previous_schema = get_schema_from_tag(previous_tag, args.schema)
    if not previous_schema:
        msg = f"Warning: Could not load schema from {previous_tag}. "
        msg += "Schema file may not exist in that release."
        print(msg, file=sys.stderr)
        if args.output:
            Path(args.output).write_text("")
        sys.exit(0)

    # Compare schemas
    changes = compare_schemas(previous_schema, current_schema)

    # Output summary to stdout
    summary = format_changes_summary(changes, previous_tag)
    print(summary)

    # Write markdown to file if requested
    if args.output:
        schema_name = Path(args.schema).name
        markdown = format_changes_markdown(changes, schema_name, previous_tag)
        Path(args.output).write_text(markdown)
        if markdown:
            print(f"Schema changes written to {args.output}")

    # Write JSON if requested
    if args.json:
        changes["previous_tag"] = previous_tag
        changes["schema_file"] = args.schema
        Path(args.json).write_text(json.dumps(changes, indent=2))

    # Exit with 0 regardless - this is informational
    sys.exit(0)


if __name__ == "__main__":
    main()
