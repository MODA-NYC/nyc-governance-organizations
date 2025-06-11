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
        help=(
            "Path to save the full, versioned golden dataset "
            "(e.g., data/output/golden_dataset_v3.csv)."
        ),
    )
    parser.add_argument(
        "--output_published",
        required=True,
        type=pathlib.Path,
        help=(
            "Path to save the final, transformed, public-facing dataset "
            "(e.g., data/published/NYCOrgs_v3.csv)."
        ),
    )

    args = parser.parse_args()

    # Load Input CSV
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'")
        sys.exit(1)

    # --- Step 1: Save the full, versioned Golden Dataset ---
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

    # Create a copy for transformation to avoid changing the original DataFrame
    df_public = df.copy()

    # Rename columns
    rename_map = {
        "PrincipalOfficerGivenName": "PrincipalOfficerFirstName",
        "PrincipalOfficerFamilyName": "PrincipalOfficerLastName",
    }
    df_public.rename(columns=rename_map, inplace=True)

    # Filter by InOrgChart column
    if "InOrgChart" in df_public.columns:
        df_public["InOrgChart"] = (
            df_public["InOrgChart"]
            .astype(str)
            .str.lower()
            .map({"true": True})
            .fillna(False)
        )
        df_public = df_public[df_public["InOrgChart"]].copy()

    # Define and select final columns for public output
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

    # Convert headers to snake case
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
