#!/usr/bin/env python3
"""
create_crosswalk.py - A utility to generate a source name crosswalk file.

This script reads a "golden" dataset and creates a long-format CSV that maps
the internal RecordID to the names of the entity as they appear in various
source systems.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def generate_crosswalk(input_path: Path, output_path: Path):
    """
    Reads the golden dataset, extracts source names, and creates a crosswalk file.

    Args:
        input_path (Path): Path to the input golden dataset CSV.
        output_path (Path): Path to save the output crosswalk CSV.
    """
    print(f"Reading golden dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path, dtype=str)
    except FileNotFoundError:
        print(f"❌ Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    # Identify the RecordID column (case-insensitive)
    try:
        record_id_col = next(col for col in df.columns if col.lower() == "recordid")
    except StopIteration:
        print(
            "❌ Error: Could not find a 'RecordID' column in the input file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Identify all columns that represent source names
    name_source_cols = [col for col in df.columns if col.startswith("Name - ")]

    if not name_source_cols:
        print(
            "⚠️ Warning: No source name columns (e.g., 'Name - CPO') found.",
            file=sys.stderr,
        )
        return

    print(f"Found {len(name_source_cols)} source name columns to process.")

    # Use pandas.melt to transform from wide to long format
    df_long = df.melt(
        id_vars=[record_id_col],
        value_vars=name_source_cols,
        var_name="SourceSystem",
        value_name="SourceName",
    )

    # Clean up the SourceSystem column by removing the prefix
    df_long["SourceSystem"] = df_long["SourceSystem"].str.replace(
        "Name - ", "", regex=False
    )

    # Drop rows where the SourceName is missing, as they are not useful
    df_long.dropna(subset=["SourceName"], inplace=True)
    # Also drop rows where SourceName is an empty string
    df_long = df_long[df_long["SourceName"].str.strip() != ""]

    # Rename the record ID column to a consistent name
    df_long.rename(columns={record_id_col: "RecordID"}, inplace=True)

    print(f"Generated a crosswalk with {len(df_long)} entries.")

    # Save the output file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ Successfully saved crosswalk to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving output file to '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a long-format source name crosswalk from the golden dataset."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--input_csv",
        type=Path,
        required=True,
        help="Path to the input golden dataset CSV file.",
    )
    parser.add_argument(
        "--output_csv",
        type=Path,
        required=True,
        help="Path to save the output crosswalk CSV file.",
    )
    args = parser.parse_args()

    generate_crosswalk(args.input_csv, args.output_csv)


if __name__ == "__main__":
    main()
