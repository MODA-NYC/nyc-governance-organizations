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

from nycgo_pipeline.crosswalk import (
    DEFAULT_SOURCE_CONFIG,
    SourceConfig,
    build_crosswalk,
)


def generate_crosswalk(
    input_path: Path, output_path: Path, config: dict[str, SourceConfig] | None = None
):
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
        next(col for col in df.columns if col.lower() == "recordid")
    except StopIteration:
        print(
            "❌ Error: Could not find a 'RecordID' column in the input file.",
            file=sys.stderr,
        )
        sys.exit(1)

    crosswalk = build_crosswalk(
        df,
        sources=config,
    )

    if crosswalk.empty:
        print(
            "⚠️ Warning: No source data found based on configuration. "
            "No output generated."
        )
        return

    print(f"Generated a crosswalk with {len(crosswalk)} entries.")

    # Save the output file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        crosswalk.to_csv(output_path, index=False, encoding="utf-8-sig")
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

    generate_crosswalk(args.input_csv, args.output_csv, DEFAULT_SOURCE_CONFIG)


if __name__ == "__main__":
    main()
