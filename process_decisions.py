#!/usr/bin/env python3
"""
process_decisions.py - Processes a reviewed discrepancies file.

This script automates the analyst workflow by taking a reviewed discrepancies
CSV as input. It expects 'Decision' and 'DecisionNotes' columns to have been
added and populated by the analyst.

The script performs two main actions:
1. Appends the decision records to a master `decision_log.csv`.
2. Generates a `supplemental_edits.csv` file formatted for ingestion by the
   main `process_golden_dataset.py` script.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Define the expected columns in the decision log
DECISION_LOG_COLUMNS = [
    "Timestamp",
    "Decision",
    "DecisionNotes",
    "OriginalRecordID",
    "OriginalColumn",
    "OriginalFeedback",
]

# Define the columns for the supplemental edits file
SUPPLEMENTAL_EDITS_COLUMNS = ["Row(s)", "Column", "feedback"]


def load_and_validate_input(input_path: Path) -> pd.DataFrame | None:
    """Loads and validates the input reviewed CSV file."""
    print(f"Loading reviewed discrepancies file from: {input_path}")
    try:
        df = pd.read_csv(input_path, dtype=str).fillna("")
    except FileNotFoundError:
        print(f"❌ Error: Input file not found at '{input_path}'", file=sys.stderr)
        return None

    required_cols = ["Decision", "DecisionNotes", "RecordID", "Column", "Feedback"]
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
    log_data.rename(
        columns={
            "RecordID": "OriginalRecordID",
            "Column": "OriginalColumn",
            "Feedback": "OriginalFeedback",
        },
        inplace=True,
    )

    final_log_df = log_data[DECISION_LOG_COLUMNS]

    print(f"Appending {len(final_log_df)} records to decision log: {log_path}")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Append with header if file doesn't exist, otherwise without
        header = not log_path.exists()
        final_log_df.to_csv(
            log_path, mode="a", header=header, index=False, encoding="utf-8-sig"
        )
        print("✅ Successfully updated decision log.")
    except Exception as e:
        print(f"❌ Error updating decision log: {e}", file=sys.stderr)


def generate_supplemental_edits(df_decisions: pd.DataFrame, edits_path: Path):
    """Generates the supplemental_edits.csv file from decisions."""
    edits = []
    for _, row in df_decisions.iterrows():
        decision = str(row["Decision"]).strip().upper()
        if not decision:
            continue

        if decision == "SUGGEST_ADD":
            # The feedback already contains the suggested action, just pass it through.
            edits.append(
                {
                    "Row(s)": row["RecordID"],
                    "Column": row["Column"],
                    "feedback": row["Feedback"],
                }
            )
        elif decision == "SUGGEST_REVIEW_DELETE":
            # Create a specific "Delete RecordID" command
            edits.append(
                {
                    "Row(s)": row["RecordID"],
                    "Column": "_SYSTEM_ACTION",
                    "feedback": f"Delete RecordID {row['RecordID']}",
                }
            )
        # Other decisions like "IGNORE" or "INVESTIGATE" do not generate edits.

    if not edits:
        print("ℹ️ No decisions found that require supplemental edits.")
        return

    df_edits = pd.DataFrame(edits, columns=SUPPLEMENTAL_EDITS_COLUMNS)

    print(f"Generating {len(df_edits)} supplemental edits to: {edits_path}")
    try:
        edits_path.parent.mkdir(parents=True, exist_ok=True)
        df_edits.to_csv(edits_path, index=False, encoding="utf-8-sig")
        print("✅ Successfully generated supplemental edits file.")
    except Exception as e:
        print(f"❌ Error generating supplemental edits file: {e}", file=sys.stderr)


def main():
    """Main function to orchestrate the processing of decisions."""
    parser = argparse.ArgumentParser(
        description=(
            "Process a reviewed discrepancies file to log decisions and "
            "generate edits."
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
        "--supplemental_edits",
        type=Path,
        required=True,
        help="Path to save the generated supplemental edits CSV file.",
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
    generate_supplemental_edits(df_processed, args.supplemental_edits)

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
