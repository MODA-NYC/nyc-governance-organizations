#!/usr/bin/env python3
"""
compare_to_source.py - Compares the golden dataset against an updated source.

This script uses the crosswalk file to check for differences between the golden
dataset's known source names and a newly provided source file. It generates a
CSV report of suggested edits for analyst review.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def _load_and_validate_data(
    golden_path: Path,
    crosswalk_path: Path,
    source_file_path: Path,
    source_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Loads all data files and validates them."""
    try:
        print(f"Loading golden dataset from: {golden_path}")
        pd.read_csv(golden_path, dtype=str)
        print(f"Loading crosswalk from: {crosswalk_path}")
        df_crosswalk = pd.read_csv(crosswalk_path, dtype=str)
        print(f"Loading new source data from: {source_file_path}")
        df_source = pd.read_csv(source_file_path, dtype=str)
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading files: {e}", file=sys.stderr)
        sys.exit(1)

    df_crosswalk_filtered = df_crosswalk[df_crosswalk["SourceSystem"] == source_name]
    if df_crosswalk_filtered.empty:
        print(
            f"⚠️ Warning: No entries found for SourceSystem '{source_name}' "
            "in the crosswalk file. Cannot perform comparison.",
            file=sys.stderr,
        )
        sys.exit(0)

    unique_source_columns = df_crosswalk_filtered["SourceColumn"].unique()
    if len(unique_source_columns) == 0:
        print(
            f"❌ Error: No 'SourceColumn' found for source '{source_name}' "
            "in crosswalk.",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(unique_source_columns) > 1:
        print(
            f"❌ Error: Found multiple differing source columns for '{source_name}' "
            f"in crosswalk: {list(unique_source_columns)}. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    source_name_col = unique_source_columns[0]
    print(f"ℹ️ Determined source column from crosswalk: '{source_name_col}'")

    if source_name_col not in df_source.columns:
        print(
            f"❌ Error: Column '{source_name_col}' (from crosswalk) not found "
            f"in source file '{source_file_path}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    return df_crosswalk_filtered, df_source, source_name_col


def _generate_suggestions(
    new_names: list, missing_names: list, source_name: str, name_to_id_map: dict
) -> list[dict]:
    """Generates a list of suggestion dictionaries."""
    suggestions = []
    for name in new_names:
        suggestions.append(
            {
                "RecordID": "N/A",
                "Column": "Name",
                "Feedback": f"SUGGEST_ADD: New record found in '{source_name}' "
                f"with name: '{name}'",
            }
        )

    for name in missing_names:
        record_id = name_to_id_map.get(name, "UNKNOWN_ID")
        suggestions.append(
            {
                "RecordID": record_id,
                "Column": "_SYSTEM",
                "Feedback": f"SUGGEST_REVIEW_DELETE: Record with source name '{name}' "
                f"was not found in the new '{source_name}' source file.",
            }
        )
    return suggestions


def compare_and_suggest(
    golden_path: Path,
    crosswalk_path: Path,
    source_file_path: Path,
    source_name: str,
    output_path: Path,
):
    """
    Compares data and generates a suggested edits report.
    """
    df_crosswalk_filtered, df_source, source_name_col = _load_and_validate_data(
        golden_path, crosswalk_path, source_file_path, source_name
    )

    # --- 1. Prepare Data Sets ---
    known_source_names: set[str] = set(df_crosswalk_filtered["SourceName"])
    current_source_names: set[str] = set(df_source[source_name_col].dropna())

    # --- 2. Perform Comparisons ---
    print(
        f"Comparing {len(known_source_names)} known records for '{source_name}' "
        f"against {len(current_source_names)} records in the new source file."
    )

    new_names = sorted(list(current_source_names - known_source_names))
    missing_names = sorted(list(known_source_names - current_source_names))

    if not new_names and not missing_names:
        print("✅ No new or missing records found. No suggestions generated.")
        return

    # --- 3. Generate and Save Suggestions ---
    name_to_id_map = df_crosswalk_filtered.set_index("SourceName")["RecordID"].to_dict()
    suggestions = _generate_suggestions(
        new_names, missing_names, source_name, name_to_id_map
    )

    df_suggestions = pd.DataFrame(
        suggestions, columns=["RecordID", "Column", "Feedback"]
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_suggestions.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Generated report with {len(suggestions)} suggestions.")
        print(f"✅ Successfully saved suggestions report to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving output file to '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Compare golden data with a new source file and suggest edits.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--golden",
        type=Path,
        required=True,
        help="Path to the input golden dataset CSV.",
    )
    parser.add_argument(
        "--crosswalk",
        type=Path,
        required=True,
        help="Path to the source name crosswalk CSV.",
    )
    parser.add_argument(
        "--source_file",
        type=Path,
        required=True,
        help="Path to the new/updated source file to compare against.",
    )
    parser.add_argument(
        "--source_name",
        type=str,
        required=True,
        help="Name of the source system being compared (e.g., 'CPO').",
    )
    parser.add_argument(
        "--output_csv",
        type=Path,
        required=True,
        help="Path to save the generated suggested edits report.",
    )
    args = parser.parse_args()

    compare_and_suggest(
        args.golden,
        args.crosswalk,
        args.source_file,
        args.source_name,
        args.output_csv,
    )


if __name__ == "__main__":
    main()
