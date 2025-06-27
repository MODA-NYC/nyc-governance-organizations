#!/usr/bin/env python3
"""
export_dataset.py - Prepares and exports datasets for different destinations.

This script takes a final, processed "golden" dataset and produces two outputs:
1.  A versioned copy of the full golden dataset, saved to data/output/.
2.  A cleaned, filtered, and transformed public-facing version, saved to
    data/published/.
"""
import argparse
import pathlib
import re
import sys

import pandas as pd


def to_snake_case(name: str) -> str:
    """Converts a PascalCase or CamelCase string to snake_case."""
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s2 = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s1)
    return s2.lower()


def main():
    """Main function to process the dataset for export."""
    parser = argparse.ArgumentParser(
        description=(
            "Processes a dataset CSV for final export, creating a versioned golden "
            "copy and a public-facing, transformed version."
        )
    )
    parser.add_argument(
        "--input_csv",
        required=True,
        type=pathlib.Path,
        help="Path to the final processed dataset to be exported.",
    )
    parser.add_argument(
        "--output_golden",
        required=True,
        type=pathlib.Path,
        help="Path to save the full, versioned golden dataset.",
    )
    parser.add_argument(
        "--output_published",
        required=True,
        type=pathlib.Path,
        help="Path to save the final, transformed, public-facing dataset.",
    )
    args = parser.parse_args()

    # Load Input CSV
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    # --- Step 1: Save the full, versioned Golden Dataset ---
    # This happens first, before any public-facing transformations.
    print(f"Saving full golden dataset to {args.output_golden}...")
    try:
        args.output_golden.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output_golden, index=False, encoding="utf-8-sig")
        print("✅ Golden dataset saved successfully.")
    except Exception as e:
        print(f"Error saving golden dataset: {e}")
        sys.exit(1)

    # --- Step 2: Process and save the Published Dataset ---
    print("\nProcessing data for public export...")

    df_public = df.copy()

    # Rename columns for clarity (e.g., GivenName -> FirstName)
    rename_map = {
        "PrincipalOfficerGivenName": "PrincipalOfficerFirstName",
        "PrincipalOfficerFamilyName": "PrincipalOfficerLastName",
    }
    df_public.rename(columns=rename_map, inplace=True)

    # --- Filter for records to include in public output ---
    print("Applying filters for public export...")
    rows_before_filter = len(df_public)

    # Define conditions
    in_org_chart = (
        df_public.get("InOrgChart", pd.Series([False] * len(df_public)))
        .astype(str)
        .str.lower()
        .map({"true": True})
        .fillna(False)
    )
    has_ops_name = df_public.get(
        "Name - Ops", pd.Series([False] * len(df_public))
    ).notna() & (
        df_public.get("Name - Ops", pd.Series([""] * len(df_public))).str.strip() != ""
    )
    is_mta_exception = (
        df_public.get("RecordID", pd.Series([""] * len(df_public))) == "NYC_GOID_000476"
    )

    # Apply combined filter
    df_public = df_public[in_org_chart | has_ops_name | is_mta_exception].copy()

    print(
        f"Kept {len(df_public)} rows out of {rows_before_filter} after applying combined filter."
    )

    # --- Select and order columns for final output ---
    required_output_columns = [
        "RecordID",
        "Name",
        "NameAlphabetized",
        "OperationalStatus",
        "OrganizationType",
        "Description",
        "URL",
        "AlternateOrFormerNames",
        "Acronym",
        "AlternateOrFormerAcronyms",
        "BudgetCode",
        "OpenDatasetsURL",
        "FoundingYear",
        "PrincipalOfficerFullName",
        "PrincipalOfficerFirstName",
        "PrincipalOfficerLastName",
        "PrincipalOfficerTitle",
        "PrincipalOfficerContactURL",
        "InOrgChart",
        "ReportsTo",
    ]

    missing_cols = [
        col for col in required_output_columns if col not in df_public.columns
    ]
    if missing_cols:
        print(f"Error: Expected columns missing for public export: {missing_cols}")
        sys.exit(1)

    df_selected = df_public[required_output_columns]

    # --- Convert headers to snake_case (This is the FINAL transformation) ---
    df_selected.columns = [to_snake_case(col) for col in df_selected.columns]
    print("Converted public column headers to snake_case.")

    # Save final published file
    try:
        args.output_published.parent.mkdir(parents=True, exist_ok=True)
        df_selected.to_csv(args.output_published, index=False, encoding="utf-8-sig")
        print(f"✅ Published dataset saved successfully to: {args.output_published}")
    except Exception as e:
        print(f"Error saving published dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
