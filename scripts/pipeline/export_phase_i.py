#!/usr/bin/env python3
"""
Phase I Export Bridge Tool

Generates Phase I-compatible exports from Phase II datasets during Phase II development.
This is a temporary bridge tool for urgent Phase I-compatible updates,
not a long-term solution.

Usage:
    python scripts/pipeline/export_phase_i.py \
      --input data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
      --output data/published/phase_i_compatible.csv \
      --crosswalk data/crosswalk/recordid_migration.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Phase I public export fields (16 fields, snake_case)
PHASE_I_PUBLIC_FIELDS = [
    "record_id",
    "name",
    "name_alphabetized",
    "operational_status",
    "organization_type",
    "url",
    "alternate_or_former_names",
    "acronym",
    "alternate_or_former_acronyms",
    "principal_officer_full_name",
    "principal_officer_first_name",
    "principal_officer_last_name",
    "principal_officer_title",
    "principal_officer_contact_url",
    "reports_to",
    "in_org_chart",
]

# Additional computed field
COMPUTED_FIELD = "listed_in_nyc_gov_agency_directory"


def load_recordid_crosswalk(crosswalk_path: Path) -> dict[str, str]:
    """
    Load RecordID crosswalk mapping new format (6-digit) to old format
    (NYC_GOID_XXXXXX).

    Expected CSV format:
    - old_record_id: NYC_GOID_XXXXXX format
    - new_record_id: 6-digit numeric format
    - entity_name: (optional, for reference)

    Returns dict mapping new_record_id -> old_record_id
    """
    if not crosswalk_path.exists():
        print(f"Warning: Crosswalk file not found at {crosswalk_path}")
        print("RecordID conversion will be skipped. Output will use Phase II format.")
        return {}

    try:
        df_crosswalk = pd.read_csv(crosswalk_path, dtype=str)

        # Validate required columns
        if (
            "new_record_id" not in df_crosswalk.columns
            or "old_record_id" not in df_crosswalk.columns
        ):
            print(
                "Error: Crosswalk must have 'new_record_id' and 'old_record_id' columns"
            )
            sys.exit(1)

        # Create mapping: new_record_id -> old_record_id
        crosswalk_map = dict(
            zip(
                df_crosswalk["new_record_id"].astype(str).str.strip(),
                df_crosswalk["old_record_id"].astype(str).str.strip(),
            )
        )

        print(f"Loaded {len(crosswalk_map)} RecordID mappings from crosswalk")
        return crosswalk_map

    except Exception as e:
        print(f"Error loading crosswalk: {e}")
        sys.exit(1)


def convert_recordids(df: pd.DataFrame, crosswalk_map: dict[str, str]) -> pd.DataFrame:
    """
    Convert RecordIDs from Phase II format (6-digit) to Phase I format
    (NYC_GOID_XXXXXX).

    If crosswalk_map is empty, skips conversion and returns dataframe unchanged.
    """
    if not crosswalk_map:
        print("No crosswalk provided - RecordIDs will remain in Phase II format")
        return df

    if "record_id" not in df.columns:
        print("Warning: 'record_id' column not found in dataset")
        return df

    # Convert RecordIDs
    df_converted = df.copy()
    df_converted["record_id"] = df_converted["record_id"].astype(str).str.strip()

    # Map new format to old format
    converted_count = 0
    for idx, new_id in df_converted["record_id"].items():
        if new_id in crosswalk_map:
            df_converted.at[idx, "record_id"] = crosswalk_map[new_id]
            converted_count += 1

    print(f"Converted {converted_count} RecordIDs from Phase II to Phase I format")

    # Check for unmapped RecordIDs
    unmapped = df_converted[~df_converted["record_id"].isin(crosswalk_map.values())]
    if len(unmapped) > 0:
        print(
            f"Warning: {len(unmapped)} RecordIDs were not found in crosswalk "
            "and remain unchanged"
        )

    return df_converted


def filter_phase_i_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to Phase I public export fields only.

    Removes Phase II-only fields:
    - governance_structure
    - org_chart_oversight_record_id
    - org_chart_oversight_name
    - parent_organization_record_id
    - parent_organization_name
    - authorizing_authority
    - authorizing_authority_type
    - authorizing_url
    - appointments_summary
    """
    df_filtered = df.copy()

    # Phase II fields to remove
    phase_ii_fields = [
        "governance_structure",
        "org_chart_oversight_record_id",
        "org_chart_oversight_name",
        "parent_organization_record_id",
        "parent_organization_name",
        "authorizing_authority",
        "authorizing_authority_type",
        "authorizing_url",
        "appointments_summary",
    ]

    # Remove Phase II fields if present
    fields_removed = []
    for field in phase_ii_fields:
        if field in df_filtered.columns:
            df_filtered = df_filtered.drop(columns=[field])
            fields_removed.append(field)

    if fields_removed:
        print(f"Removed Phase II fields: {', '.join(fields_removed)}")

    # Select only Phase I fields (if they exist)
    available_fields = [f for f in PHASE_I_PUBLIC_FIELDS if f in df_filtered.columns]
    missing_fields = [f for f in PHASE_I_PUBLIC_FIELDS if f not in df_filtered.columns]

    if missing_fields:
        print(f"Warning: Missing Phase I fields: {', '.join(missing_fields)}")

    if not available_fields:
        print("Error: No Phase I fields found in dataset")
        sys.exit(1)

    # Select available Phase I fields
    df_filtered = df_filtered[available_fields]

    # Ensure computed field is included if it exists
    if COMPUTED_FIELD in df.columns and COMPUTED_FIELD not in df_filtered.columns:
        df_filtered[COMPUTED_FIELD] = df[COMPUTED_FIELD]

    print(f"Selected {len(available_fields)} Phase I fields for export")

    return df_filtered


def ensure_reports_to_field(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure reports_to field exists (required for Phase I).

    If missing, attempts to reconstruct from Phase II relationship fields.
    """
    if "reports_to" in df.columns:
        return df

    print(
        "Warning: 'reports_to' field not found. "
        "Attempting to reconstruct from Phase II fields..."
    )

    df_with_reports_to = df.copy()

    # Try to reconstruct from org_chart_oversight_name or parent_organization_name
    # (These fields may still exist in the dataset even after filtering)
    if "org_chart_oversight_name" in df.columns:
        df_with_reports_to["reports_to"] = df["org_chart_oversight_name"].fillna("")
    elif "parent_organization_name" in df.columns:
        df_with_reports_to["reports_to"] = df["parent_organization_name"].fillna("")
    else:
        # Create empty reports_to field
        df_with_reports_to["reports_to"] = ""
        print("Could not reconstruct 'reports_to' - field will be empty")

    return df_with_reports_to


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Phase I-compatible export from Phase II dataset. "
            "This is a temporary bridge tool for urgent updates "
            "during Phase II development."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to Phase II dataset CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to save Phase I-compatible export CSV",
    )
    parser.add_argument(
        "--crosswalk",
        type=Path,
        help=(
            "Path to RecordID migration crosswalk CSV "
            "(old_record_id, new_record_id, entity_name)"
        ),
    )

    args = parser.parse_args()

    # Load input dataset
    print(f"Loading Phase II dataset from {args.input}...")
    try:
        df = pd.read_csv(args.input, dtype=str)
        print(f"Loaded {len(df)} records with {len(df.columns)} fields")
    except Exception as e:
        print(f"Error loading input dataset: {e}")
        return 1

    # Convert PascalCase columns to snake_case for Phase I compatibility
    # Create mapping from PascalCase to snake_case
    column_mapping = {}
    for col in df.columns:
        # Convert PascalCase to snake_case
        if col == "RecordID":
            column_mapping[col] = "record_id"
        elif col == "Name":
            column_mapping[col] = "name"
        elif col == "NameAlphabetized":
            column_mapping[col] = "name_alphabetized"
        elif col == "OperationalStatus":
            column_mapping[col] = "operational_status"
        elif col == "OrganizationType":
            column_mapping[col] = "organization_type"
        elif col == "URL":
            column_mapping[col] = "url"
        elif col == "AlternateOrFormerNames":
            column_mapping[col] = "alternate_or_former_names"
        elif col == "Acronym":
            column_mapping[col] = "acronym"
        elif col == "AlternateOrFormerAcronyms":
            column_mapping[col] = "alternate_or_former_acronyms"
        elif col == "PrincipalOfficerFullName":
            column_mapping[col] = "principal_officer_full_name"
        elif col == "PrincipalOfficerFirstName":
            column_mapping[col] = "principal_officer_first_name"
        elif col == "PrincipalOfficerLastName":
            column_mapping[col] = "principal_officer_last_name"
        elif col == "PrincipalOfficerTitle":
            column_mapping[col] = "principal_officer_title"
        elif col == "PrincipalOfficerContactURL":
            column_mapping[col] = "principal_officer_contact_url"
        elif col == "InOrgChart":
            column_mapping[col] = "in_org_chart"
        elif col == "ReportsTo":
            column_mapping[col] = "reports_to"
    
    # Rename columns
    if column_mapping:
        df = df.rename(columns=column_mapping)
        print(f"Converted {len(column_mapping)} columns to snake_case")

    # Load crosswalk if provided
    crosswalk_map = {}
    if args.crosswalk:
        crosswalk_map = load_recordid_crosswalk(args.crosswalk)

    # Convert RecordIDs (if crosswalk provided)
    if crosswalk_map:
        df = convert_recordids(df, crosswalk_map)

    # Filter to Phase I fields
    df = filter_phase_i_fields(df)

    # Ensure reports_to field exists
    df = ensure_reports_to_field(df)

    # Save output
    print(f"\nSaving Phase I-compatible export to {args.output}...")
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print("✅ Export saved successfully")
        print(f"   Records: {len(df)}")
        print(f"   Fields: {len(df.columns)}")
        print(f"   File: {args.output}")
    except Exception as e:
        print(f"Error saving output: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
