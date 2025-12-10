#!/usr/bin/env python3
"""
Standardize field names to snake_case across the golden dataset.

This is a one-time migration script to convert PascalCase column headers
to snake_case, matching the published export format.

Usage:
    python scripts/maint/standardize_field_names.py --check   # Preview changes
    python scripts/maint/standardize_field_names.py --apply   # Apply changes
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

# Field name mapping: PascalCase → snake_case
# Fields with special characters need explicit mapping
COLUMN_MAP = {
    # Standard PascalCase fields
    "RecordID": "record_id",
    "Name": "name",
    "NameAlphabetized": "name_alphabetized",
    "OperationalStatus": "operational_status",
    "OrganizationType": "organization_type",
    "Description": "description",
    "URL": "url",
    "AlternateOrFormerNames": "alternate_or_former_names",
    "Acronym": "acronym",
    "AlternateOrFormerAcronyms": "alternate_or_former_acronyms",
    "BudgetCode": "budget_code",
    "OpenDatasetsURL": "open_datasets_url",
    "FoundingYear": "founding_year",
    "PrincipalOfficerName": "principal_officer_name",
    "PrincipalOfficerTitle": "principal_officer_title",
    "PrincipalOfficerContactURL": "principal_officer_contact_url",
    "Notes": "notes",
    "InstanceOf": "instance_of",
    "PrincipalOfficerFullName": "principal_officer_full_name",
    "PrincipalOfficerGivenName": "principal_officer_given_name",
    "PrincipalOfficerMiddleNameOrInitial": "principal_officer_middle_name_or_initial",
    "PrincipalOfficerFamilyName": "principal_officer_family_name",
    "PrincipalOfficerSuffix": "principal_officer_suffix",
    "InOrgChart": "in_org_chart",
    "ReportsTo": "reports_to",
    "ReportingNotes": "reporting_notes",
    # Fields with special characters (explicit mapping)
    "Name - NYC.gov Agency List": "name_nycgov_agency_list",
    "Name - NYC.gov Mayor's Office": "name_nycgov_mayors_office",
    "Name - NYC Open Data Portal": "name_nyc_open_data_portal",
    "Name - ODA": "name_oda",
    "Name - CPO": "name_cpo",
    "Name - WeGov": "name_wegov",
    "Name - Greenbook": "name_greenbook",
    "Name - Checkbook": "name_checkbook",
    "Name - HOO": "name_hoo",
    "Name - Ops": "name_ops",
    "NYC.gov Agency Directory": "listed_in_nyc_gov_agency_directory",
    "Jan 2025 Org Chart": "jan_2025_org_chart",
    # Phase II fields (if present)
    "GovernanceStructure": "governance_structure",
    "OrgChartOversightRecordID": "org_chart_oversight_record_id",
    "OrgChartOversightName": "org_chart_oversight_name",
    "ParentOrganizationRecordID": "parent_organization_record_id",
    "ParentOrganizationName": "parent_organization_name",
    "AuthorizingAuthority": "authorizing_authority",
    "AuthorizingAuthorityType": "authorizing_authority_type",
    "AuthorizingURL": "authorizing_url",
    "AppointmentsSummary": "appointments_summary",
    "NameMOA": "name_moa",
}

# Reverse mapping for reference
REVERSE_MAP = {v: k for k, v in COLUMN_MAP.items()}

GOLDEN_PATH = (
    Path(__file__).parent.parent.parent
    / "data"
    / "published"
    / "latest"
    / "NYCGO_golden_dataset_latest.csv"
)


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    # First check explicit mapping
    if name in COLUMN_MAP:
        return COLUMN_MAP[name]
    # Otherwise apply algorithmic conversion
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s2 = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s1)
    return s2.lower()


def check_columns(csv_path: Path) -> None:
    """Preview column name changes without applying."""
    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, nrows=0)  # Just headers

    print(f"\nFound {len(df.columns)} columns:")
    print("-" * 60)
    print(f"{'Current Name':<40} → {'New Name':<40}")
    print("-" * 60)

    changes_needed = 0
    unmapped = []

    for col in df.columns:
        # Strip BOM if present
        clean_col = col.lstrip("\ufeff")
        new_name = to_snake_case(clean_col)

        if clean_col != new_name or col != clean_col:
            print(f"{col:<40} → {new_name:<40}")
            changes_needed += 1
        else:
            print(f"{col:<40}   (no change)")

        if clean_col not in COLUMN_MAP:
            unmapped.append(clean_col)

    print("-" * 60)
    print(f"\nChanges needed: {changes_needed}")

    if unmapped:
        print(
            f"\nWarning: {len(unmapped)} columns not in explicit map "
            "(using algorithmic conversion):"
        )
        for col in unmapped:
            print(f"  - {col}")


def apply_changes(csv_path: Path) -> None:
    """Apply column name changes to the CSV file."""
    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)

    # Build rename map for this file
    rename_map = {}
    for col in df.columns:
        clean_col = col.lstrip("\ufeff")
        new_name = to_snake_case(clean_col)
        if col != new_name:
            rename_map[col] = new_name

    if not rename_map:
        print("No changes needed - all columns already in snake_case")
        return

    print(f"\nRenaming {len(rename_map)} columns...")
    df.rename(columns=rename_map, inplace=True)

    # Backup original
    backup_path = csv_path.with_suffix(".csv.bak")
    print(f"Creating backup: {backup_path}")
    import shutil

    shutil.copy(csv_path, backup_path)

    # Write updated file
    print(f"Writing: {csv_path}")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("\nDone! Column names standardized to snake_case.")
    print(f"Backup saved to: {backup_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Standardize field names to snake_case"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check", action="store_true", help="Preview changes without applying"
    )
    group.add_argument(
        "--apply", action="store_true", help="Apply changes to golden dataset"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Specific file to process (default: latest golden dataset)",
    )
    args = parser.parse_args()

    csv_path = args.file or GOLDEN_PATH

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        return 1

    if args.check:
        check_columns(csv_path)
    elif args.apply:
        apply_changes(csv_path)

    return 0


if __name__ == "__main__":
    exit(main())
