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

# This config maps a SourceSystem to its column names in the golden and source files.
SOURCE_CONFIG = {
    "Ops": {"golden_col": "Name - Ops", "source_col": "Agency Name"},
    "CPO": {"golden_col": "Name - CPO", "source_col": "Name - CPO"},
    "Greenbook": {"golden_col": "Name - Greenbook", "source_col": "Name - Greenbook"},
    # If source_col is the same as golden_col, it's good practice to define it.
}


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

    all_source_dfs = []

    print("Processing sources based on SOURCE_CONFIG...")
    for source_system, config in SOURCE_CONFIG.items():
        golden_col = config["golden_col"]
        source_col = config["source_col"]

        if golden_col not in df.columns:
            print(
                f"⚠️ Warning: Golden column '{golden_col}' for source "
                f"'{source_system}' not found in input file. Skipping."
            )
            continue

        # Create a temporary DataFrame for the current source
        df_source = df[[record_id_col, golden_col]].copy()
        df_source.dropna(subset=[golden_col], inplace=True)
        df_source = df_source[df_source[golden_col].str.strip() != ""]

        if df_source.empty:
            continue

        df_source["SourceSystem"] = source_system
        df_source["SourceColumn"] = source_col
        df_source.rename(columns={golden_col: "SourceName"}, inplace=True)

        all_source_dfs.append(df_source)

    if not all_source_dfs:
        print(
            "⚠️ Warning: No source data found based on SOURCE_CONFIG. "
            "No output generated."
        )
        return

    # Concatenate all the individual source DataFrames into one
    df_long = pd.concat(all_source_dfs, ignore_index=True)

    # Rename the record ID column to a consistent name
    df_long.rename(columns={record_id_col: "RecordID"}, inplace=True)

    # Reorder columns for the final output
    df_long = df_long[["RecordID", "SourceSystem", "SourceColumn", "SourceName"]]

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
