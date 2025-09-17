#!/usr/bin/env python3
"""
compare_field_values.py - Compares specific field values for matched records.

This script uses a crosswalk file to identify matching records between the golden
dataset and a source file. It then compares the values in a configurable list
of fields and generates a report of any discrepancies, which can be reviewed
by an analyst.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

# --- CONFIGURATION ---
# To add a new source, add a new entry to this dictionary.
# 'source_name_col': The column in the source CSV that contains the entity name.
# 'field_mappings': A dictionary mapping the Golden Dataset field name to the
#                   corresponding field name in the Source CSV.
SOURCE_CONFIG = {
    "Ops": {
        "source_name_col": "Agency Name",
        "field_mappings": {
            "Name": "Agency Name",
            "PrincipalOfficerGivenName": "Agency Head First Name",
            "PrincipalOfficerFamilyName": "Agency Head Last Name",
            "Description": "BC Description",
            "URL": "Agency/Board Website",
            # Add other fields to compare here, e.g., "URL": "Website"
        },
    },
    # "CPO": {
    #     "source_name_col": "CPO_Agency_Name",
    #     "field_mappings": { ... },
    # },
}


def compare_fields(
    df_golden: pd.DataFrame,
    df_crosswalk: pd.DataFrame,
    df_source: pd.DataFrame,
    source_name: str,
) -> pd.DataFrame:
    """
    Compares configured fields for a given source and returns a list of discrepancies.
    """
    if source_name not in SOURCE_CONFIG:
        print(
            f"❌ Error: Source '{source_name}' not found in SOURCE_CONFIG.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = SOURCE_CONFIG[source_name]
    source_name_col = config["source_name_col"]
    field_mappings = config["field_mappings"]

    print(
        f"Comparing {len(field_mappings)} configured fields for source "
        f"'{source_name}'..."
    )

    # --- Data Merging ---
    # 1. Filter crosswalk for the relevant source
    df_crosswalk_filtered = df_crosswalk[
        df_crosswalk["SourceSystem"] == source_name
    ].copy()

    # 2. Merge golden with crosswalk to link RecordID to SourceName
    df_merged = pd.merge(df_golden, df_crosswalk_filtered, on="RecordID", how="inner")

    # 3. Merge the result with the source data on the source name
    df_final_comparison = pd.merge(
        df_merged,
        df_source,
        left_on="SourceName",
        right_on=source_name_col,
        how="inner",
        suffixes=("_golden", "_source"),
    )

    discrepancies = []

    # --- Field Comparison ---
    for golden_field, source_field in field_mappings.items():
        if (
            golden_field not in df_final_comparison
            or source_field not in df_final_comparison
        ):
            print(
                f"⚠️ Warning: Skipping comparison for '{golden_field}'/"
                f"'{source_field}' as one or both columns are missing.",
                file=sys.stderr,
            )
            continue

        # Compare each row for the current pair of fields
        for _, row in df_final_comparison.iterrows():
            golden_value = str(row[golden_field]).strip()
            source_value = str(row[source_field]).strip()

            if golden_value != source_value:
                discrepancies.append(
                    {
                        "RecordID": row["RecordID"],
                        "Column": golden_field,
                        "GoldenValue": golden_value,
                        "SourceValue": source_value,
                    }
                )

    print(f"Found {len(discrepancies)} potential discrepancies.")
    return pd.DataFrame(discrepancies)


def main():
    """Main function to handle command-line arguments and orchestrate the comparison."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare specific field values between the golden data and a source file."
        ),
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
        help="Path to the new/updated source file.",
    )
    parser.add_argument(
        "--source_name",
        type=str,
        required=True,
        choices=SOURCE_CONFIG.keys(),
        help="Name of the source system to compare.",
    )
    parser.add_argument(
        "--output_csv",
        type=Path,
        required=True,
        help="Path to save the generated change candidates report.",
    )
    args = parser.parse_args()

    # --- Data Loading ---
    try:
        df_golden = pd.read_csv(args.golden, dtype=str).fillna("")
        df_crosswalk = pd.read_csv(args.crosswalk, dtype=str).fillna("")
        df_source = pd.read_csv(args.source_file, dtype=str).fillna("")
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)

    # --- Comparison and Output ---
    df_discrepancies = compare_fields(
        df_golden, df_crosswalk, df_source, args.source_name
    )

    if not df_discrepancies.empty:
        try:
            args.output_csv.parent.mkdir(parents=True, exist_ok=True)
            df_discrepancies.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
            print(
                "✅ Successfully saved change candidates report to: "
                f"{args.output_csv}"
            )
        except Exception as e:
            print(
                f"❌ Error saving output file to '{args.output_csv}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        print("✅ No discrepancies found between the specified fields.")


if __name__ == "__main__":
    main()
