#!/usr/bin/env python3
"""
process_decisions.py - Processes a reviewed discrepancies file.

This script automates the analyst workflow by taking a reviewed discrepancies
CSV as input. It expects 'Decision' and 'DecisionNotes' columns to have been
added and populated by the analyst.

The script performs two main actions:
1. Appends the decision records to a master `decision_log.csv`.
2. Generates a filtered "to-do list" for the analyst, containing only
   discrepancies that require further action.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Define the expected columns in the decision log
DECISION_LOG_COLUMNS = [
    "Timestamp",
    "SourceRecordID",
    "SourceColumn",
    "SourceColumnValue",
    "SourceFeedback",
    "Decision",
    "DecisionNotes",
]


def load_and_validate_input(input_path: Path) -> pd.DataFrame | None:
    """Loads and validates the input reviewed CSV file."""
    print(f"Loading reviewed discrepancies file from: {input_path}")
    try:
        df = pd.read_csv(input_path, dtype=str).fillna("")
    except FileNotFoundError:
        print(f"❌ Error: Input file not found at '{input_path}'", file=sys.stderr)
        return None

    required_cols = [
        "Decision",
        "DecisionNotes",
        "RecordID",
        "Column",
        "ColumnValue",
        "Feedback",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(
            "❌ Error: Input file is missing required "
            f"columns: {', '.join(missing_cols)}.",
            file=sys.stderr,
        )
        print(
            "Please ensure you have added and populated 'Decision' and "
            "'DecisionNotes'.",
            file=sys.stderr,
        )
        return None

    if df["Decision"].eq("").all():
        print(
            "⚠️ Warning: 'Decision' column is empty. " "No actions will be processed.",
            file=sys.stderr,
        )

    return df


def append_to_decision_log(df_decisions: pd.DataFrame, log_path: Path):
    """Appends processed decisions to the master decision log."""
    if df_decisions.empty:
        return

    log_data = df_decisions.copy()
    log_data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Explicitly rename columns to the 'Source' convention
    log_data.rename(
        columns={
            "RecordID": "SourceRecordID",
            "Column": "SourceColumn",
            "ColumnValue": "SourceColumnValue",
            "Feedback": "SourceFeedback",
        },
        inplace=True,
    )

    # Ensure all required columns are present before saving
    final_log_df = log_data[DECISION_LOG_COLUMNS]

    print(f"Appending {len(final_log_df)} records to decision log: {log_path}")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        header = not log_path.exists()
        final_log_df.to_csv(
            log_path, mode="a", header=header, index=False, encoding="utf-8-sig"
        )
        print("✅ Successfully updated decision log.")
    except Exception as e:
        print(f"❌ Error updating decision log: {e}", file=sys.stderr)


def generate_discrepancies_to_process(df_decisions: pd.DataFrame, output_path: Path):
    """Saves a file containing only the discrepancies that require action."""
    # Filter out rows where the decision is 'IGNORE' (case-insensitive)
    actionable_decisions = df_decisions[
        df_decisions["Decision"].str.strip().str.upper() != "IGNORE"
    ].copy()

    if actionable_decisions.empty:
        print("ℹ️ No actionable decisions found. The 'to-process' file will be empty.")
        pd.DataFrame(
            columns=[
                "Source",
                "RecordID",
                "SourceColumn",
                "SourceColumnValue",
                "SourceFeedback",
                "Decision",
                "DecisionNotes",
            ]
        ).to_csv(output_path, index=False, encoding="utf-8-sig")
        return

    # Rename columns to the new 'Source' convention for consistency
    actionable_decisions.rename(
        columns={
            "Column": "SourceColumn",
            "ColumnValue": "SourceColumnValue",
            "Feedback": "SourceFeedback",
        },
        inplace=True,
    )

    # Define the final, ordered list of columns for the output file
    output_columns = [
        "Source",
        "RecordID",
        "SourceColumn",
        "SourceColumnValue",
        "SourceFeedback",
        "Decision",
        "DecisionNotes",
    ]
    df_to_process = actionable_decisions[output_columns]

    print(f"Generating {len(df_to_process)} actionable discrepancies to: {output_path}")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_to_process.to_csv(output_path, index=False, encoding="utf-8-sig")
        print("✅ Successfully generated discrepancies-to-process file.")
    except Exception as e:
        print(
            f"❌ Error generating discrepancies-to-process file: {e}", file=sys.stderr
        )


def main():
    """Main function to orchestrate the processing of decisions."""
    parser = argparse.ArgumentParser(
        description=(
            "Process a reviewed discrepancies file to log decisions and generate a"
            " new to-do file."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--input_csv",
        type=Path,
        required=True,
        help="Path to the input CSV that has been reviewed by an analyst.",
    )
    parser.add_argument(
        "--decision_log",
        type=Path,
        required=True,
        help="Path to the master decision log CSV file to append to.",
    )
    parser.add_argument(
        "--discrepancies_to_process",
        type=Path,
        required=True,
        help="Path to save the output CSV with discrepancies that require action.",
    )
    args = parser.parse_args()

    df_reviewed = load_and_validate_input(args.input_csv)
    if df_reviewed is None:
        sys.exit(1)

    # Filter for rows where a decision has actually been made
    df_processed = df_reviewed[df_reviewed["Decision"].str.strip() != ""].copy()

    if df_processed.empty:
        print("No rows with decisions found to process. Exiting.")
        sys.exit(0)

    append_to_decision_log(df_processed, args.decision_log)
    generate_discrepancies_to_process(df_processed, args.discrepancies_to_process)

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
