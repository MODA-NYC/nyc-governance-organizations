#!/usr/bin/env python3
"""A utility to parse PrincipalOfficerName into its constituent parts.

This script is intended for targeted use on datasets where officer names need to be
split into first, last, middle, suffix, etc. It has been separated from the main
pipeline to avoid errors with complex or non-standard name formats.
"""
import argparse
import pathlib
import sys

import pandas as pd
from nameparser import HumanName


def populate_officer_name_parts(df_input: pd.DataFrame) -> pd.DataFrame:
    """Populates detailed name parts from PrincipalOfficerName."""
    print("Parsing officer names...")
    df_processed = df_input.copy()

    # Ensure all required columns exist
    name_cols = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]
    for col in name_cols:
        if col not in df_processed.columns:
            print(f"Adding missing column: {col}")
            df_processed[col] = ""

    for i, row in df_processed.iterrows():
        name_str = row.get("PrincipalOfficerName")
        if isinstance(name_str, str) and name_str.strip():
            try:
                parsed = HumanName(name_str)
                updates = {
                    "PrincipalOfficerFullName": name_str,
                    "PrincipalOfficerGivenName": parsed.first,
                    "PrincipalOfficerMiddleNameOrInitial": parsed.middle,
                    "PrincipalOfficerFamilyName": parsed.last,
                    "PrincipalOfficerSuffix": parsed.suffix,
                }
                for col, new_val in updates.items():
                    if new_val:  # Only update if the parsed value is not empty
                        df_processed.loc[i, col] = new_val
            except Exception as e:
                print(
                    f"Warning: Could not parse name '{name_str}' for "
                    f"RecordID {row.get('RecordID')}. Error: {e}",
                    file=sys.stderr,
                )

    return df_processed


def main():
    """Main function to run the name parsing utility."""
    parser = argparse.ArgumentParser(description="Parse officer names in a dataset.")
    parser.add_argument(
        "--input_csv",
        type=pathlib.Path,
        required=True,
        help="Path to the input dataset CSV.",
    )
    parser.add_argument(
        "--output_csv",
        type=pathlib.Path,
        required=True,
        help="Path to save the processed dataset CSV with parsed names.",
    )
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    df_processed = populate_officer_name_parts(df)

    try:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
        print(f"Successfully parsed names and saved output to: {args.output_csv}")
    except Exception as e:
        print(f"Error saving output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
