#!/usr/bin/env python3
"""
apply_edits.py - Applies QA feedback and supplemental edits to a dataset.

This is the second processing stage. It takes a dataset (presumably one that
has already had global rules applied) and applies targeted changes based on an
input edits file (in the QA feedback format).
"""
import argparse
import pathlib
import re
import sys
import typing
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import pandas as pd

# Global list to store changelog entries
changelog_entries = []
changelog_id_counter = 0


class QAAction(Enum):
    DIRECT_SET = "direct_set"
    CHAR_FIX = "char_fix"
    BLANK_VALUE = "blank_value"
    DEDUP_SEMICOLON = "dedup_semicolon"
    POLICY_QUERY = "policy_query"
    REMOVE_ACTING_PREFIX = "remove_acting_prefix"
    DELETE_RECORD = "delete_record"
    APPEND_FROM_CSV = "append_from_csv"
    # These actions are handled by run_global_rules.py but are kept here for
    # rule matching
    NAME_SPLIT_SUCCESS = "name_split_success"
    NAME_SPLIT_REVIEW_NEEDED = "name_split_review_needed"
    NAME_PARSE_SUCCESS = "name_parse_success"
    NAME_PARSE_REVIEW_NEEDED = "name_parse_review_needed"
    _RECORD_FILTERED_OUT = "_record_filtered_out"
    DATA_ENRICH = "data_enrich"
    NOT_FOUND = "not_found"


@dataclass
class QAEditRule:
    pattern: re.Pattern
    action: QAAction
    value_parser: typing.Callable | None


CHANGELOG_COLUMNS = [
    "ChangeID",
    "timestamp",
    "record_id",
    "column_changed",
    "old_value",
    "new_value",
    "feedback_source",
    "notes",
    "changed_by",
    "RuleAction",
]

RULES = {
    r"Delete RecordID (?P<record_id_to_delete>\S+)": QAAction.DELETE_RECORD,
    r"^\s*Append records from CSV\s+(?P<csv_path_to_add>[\w./-]+\.csv)\s*$": (
        QAAction.APPEND_FROM_CSV
    ),
    r"Set (?P<column>\w+) to (?P<value>.+)": QAAction.DIRECT_SET,
    # Handles cases where column is in its own field
    r"Set to (?P<value>.+)": QAAction.DIRECT_SET,
    r"Fix \"(?P<value>.*?)\"": QAAction.DIRECT_SET,
    r"Fix '(?P<value>.*?)'": QAAction.DIRECT_SET,
    r".*(?:makes it look|appears|seems)\s+(?:inactive|active).*": (
        QAAction.POLICY_QUERY
    ),
    r"^(?P<value>[A-Z0-9+-.]{1,10})$": QAAction.DIRECT_SET,
    r"^(?P<value>[A-Z0-9+-. /]+?) rather than [A-Z0-9+-. /]+?$": QAAction.DIRECT_SET,
    r"^(?:.*is now|.*is currently)\s+(?P<value>.+)$": QAAction.DIRECT_SET,
    r"Fix special characters(?: in (?P<column>\w+))?": QAAction.POLICY_QUERY,
    r"Remove value of .*": QAAction.BLANK_VALUE,
    r"^(?:.*(?:has left|is no longer with|is no longer at))(?:\s+\w+)*$": (
        QAAction.POLICY_QUERY
    ),
    r"(?:Confirmed, ?so )?no longer Acting": QAAction.REMOVE_ACTING_PREFIX,
    r".*\?": QAAction.POLICY_QUERY,
}


def log_change(
    record_id: str,
    column_changed: str,
    old_value: typing.Any,
    new_value: typing.Any,
    feedback_source: str,
    notes: str | None,
    changed_by: str,
    rule_action: str | None,
):
    """Logs a change to the changelog_entries list."""
    global changelog_entries, changelog_id_counter
    changelog_id_counter += 1
    entry = {
        "ChangeID": changelog_id_counter,
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "column_changed": column_changed,
        "old_value": old_value,
        "new_value": new_value,
        "feedback_source": feedback_source,
        "notes": notes,
        "changed_by": changed_by,
        "RuleAction": rule_action if rule_action else "unknown",
    }
    changelog_entries.append(entry)


def detect_rule(feedback: str) -> tuple[QAAction, re.Match | None]:
    for pattern_str, action in RULES.items():
        match = re.search(pattern_str, feedback, re.IGNORECASE)
        if match:
            return action, match
    return QAAction.POLICY_QUERY, None


# --- Handler Functions ---
# Note: All handler functions from process_golden_dataset.py are copied here.


def handle_direct_set(
    row_series: pd.Series,
    column_to_edit: str,
    new_value: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    old_value = row_series.get(column_to_edit)
    log_change(
        record_id,
        column_to_edit,
        old_value,
        new_value,
        feedback_source,
        notes,
        changed_by,
        QAAction.DIRECT_SET.value,
    )
    row_series[column_to_edit] = new_value
    return row_series


def handle_blank_value(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    old_value = row_series.get(column_to_edit)
    log_change(
        record_id,
        column_to_edit,
        old_value,
        "",
        feedback_source,
        notes,
        changed_by,
        QAAction.BLANK_VALUE.value,
    )
    row_series[column_to_edit] = ""
    return row_series


def handle_remove_acting_prefix(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    old_value = row_series.get(column_to_edit)
    if isinstance(old_value, str) and old_value.lower().strip().startswith("acting"):
        new_value = re.sub(r"acting\s*", "", old_value, flags=re.IGNORECASE).strip()
        log_change(
            record_id,
            column_to_edit,
            old_value,
            new_value,
            feedback_source,
            notes,
            changed_by,
            QAAction.REMOVE_ACTING_PREFIX.value,
        )
        row_series[column_to_edit] = new_value
    return row_series


def handle_policy_query(
    row_series: pd.Series,
    column_to_edit: str | None,
    original_feedback: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
):
    log_change(
        record_id,
        column_to_edit or "Policy Question",
        "N/A",
        "N/A",
        feedback_source,
        original_feedback,
        changed_by,
        QAAction.POLICY_QUERY.value,
    )
    return row_series


def handle_delete_record(
    current_df: pd.DataFrame,
    record_id_to_delete: str,
    feedback_source: str,
    changed_by: str,
    notes_from_feedback: str,
) -> pd.DataFrame:
    if record_id_to_delete in current_df["RecordID"].values:
        old_value = (
            current_df[current_df["RecordID"] == record_id_to_delete]
            .iloc[0]
            .get("Name", "Entire Row")
        )
        log_change(
            record_id_to_delete,
            "_ROW_DELETED",
            old_value,
            "N/A",
            feedback_source,
            notes_from_feedback,
            changed_by,
            QAAction.DELETE_RECORD.value,
        )
        return current_df[current_df["RecordID"] != record_id_to_delete].copy()
    else:
        log_change(
            record_id_to_delete,
            "_ROW_DELETE_FAILED",
            "Record Not Found",
            "N/A",
            feedback_source,
            f"Deletion failed: {notes_from_feedback}",
            changed_by,
            QAAction.DELETE_RECORD.value,
        )
        return current_df


def handle_append_from_csv(
    current_df: pd.DataFrame,
    csv_path_str: str,
    base_input_dir: pathlib.Path,
    feedback_source: str,
    changed_by: str,
    notes_from_feedback: str,
) -> pd.DataFrame:
    csv_path_obj = pathlib.Path(csv_path_str)

    # Handle both project-root relative paths and paths relative to the QA file
    if csv_path_str.startswith("data/"):
        # Assume it's a path from the project root
        resolved_csv_path = csv_path_obj
    else:
        # Assume it's relative to the input file's directory
        resolved_csv_path = base_input_dir / csv_path_obj

    try:
        df_new_records = pd.read_csv(resolved_csv_path, dtype=str).fillna("")
        if df_new_records.empty:
            print(
                f"⚠️ Warning: CSV file '{resolved_csv_path}' is empty. "
                "No records appended."
            )
            return current_df

        print(f"Appending {len(df_new_records)} records from '{resolved_csv_path}'...")
        for _, new_row in df_new_records.iterrows():
            log_change(
                new_row.get("RecordID", "N/A"),
                "_ROW_ADDED",
                "N/A",
                new_row.get("Name"),
                feedback_source,
                notes_from_feedback,
                changed_by,
                QAAction.APPEND_FROM_CSV.value,
            )
        return pd.concat([current_df, df_new_records], ignore_index=True)
    except FileNotFoundError:
        # This is a critical error, print it loudly to the console.
        print(
            f"❌ CRITICAL ERROR: File not found at resolved path "
            f"'{resolved_csv_path}'. Cannot append records.",
            file=sys.stderr,
        )
        log_change(
            "_APPEND_ERROR",
            "_APPEND_FROM_CSV_FAILED",
            "File Not Found",
            str(resolved_csv_path),
            feedback_source,
            notes_from_feedback,
            changed_by,
            QAAction.APPEND_FROM_CSV.value,
        )
        return current_df
    except Exception as e:
        print(
            f"❌ CRITICAL ERROR: Failed to load or process CSV "
            f"'{resolved_csv_path}': {e}",
            file=sys.stderr,
        )
        log_change(
            "_APPEND_ERROR",
            "_APPEND_FROM_CSV_FAILED",
            str(e),
            str(resolved_csv_path),
            feedback_source,
            notes_from_feedback,
            changed_by,
            QAAction.APPEND_FROM_CSV.value,
        )
        return current_df


# Simplified handlers for actions not fully implemented in this script
def handle_char_fix(row, **kwargs):
    return row


def handle_dedup_semicolon(row, **kwargs):
    return row


ACTION_HANDLERS = {
    QAAction.DIRECT_SET: handle_direct_set,
    QAAction.BLANK_VALUE: handle_blank_value,
    QAAction.REMOVE_ACTING_PREFIX: handle_remove_acting_prefix,
    QAAction.POLICY_QUERY: handle_policy_query,
    QAAction.DELETE_RECORD: handle_delete_record,
    QAAction.APPEND_FROM_CSV: handle_append_from_csv,
    # Placeholders for handlers whose logic now lives in run_global_rules.py
    QAAction.CHAR_FIX: handle_char_fix,
    QAAction.DEDUP_SEMICOLON: handle_dedup_semicolon,
}


def _handle_direct_set(
    row_series,
    match,
    qa_row,
    record_id,
    feedback_source_name,
    changed_by,
    feedback,
    df_modified,
    index,
):
    col = (
        match.group("column") if "column" in match.groupdict() else qa_row.get("Column")
    )
    parsed_value = match.group("value")

    if col and parsed_value is not None:
        # Strip leading/trailing whitespace and quotes
        clean_value = parsed_value.strip()
        if (
            len(clean_value) > 1
            and clean_value.startswith('"')
            and clean_value.endswith('"')
        ):
            clean_value = clean_value[1:-1]
        elif (
            len(clean_value) > 1
            and clean_value.startswith("'")
            and clean_value.endswith("'")
        ):
            clean_value = clean_value[1:-1]

        # Call the handler with the cleaned value
        modified_row = handle_direct_set(
            row_series,
            col,
            clean_value,
            record_id,
            feedback_source_name,
            changed_by,
            feedback,
        )
        df_modified.loc[index] = modified_row


def _process_row(
    row_series,
    qa_row,
    action,
    match,
    feedback_source_name,
    changed_by,
    feedback,
    df_modified,
):
    record_id = qa_row.get("Row(s)")
    if pd.isna(record_id) or record_id not in df_modified["RecordID"].values:
        return

    target_indices = df_modified[df_modified["RecordID"] == record_id].index
    for index in target_indices:
        row_series = df_modified.loc[index].copy()
        handler = ACTION_HANDLERS.get(action)

        if not handler:
            continue

        # This is the corrected block for DIRECT_SET
        if action == QAAction.DIRECT_SET and match:
            _handle_direct_set(
                row_series,
                match,
                qa_row,
                record_id,
                feedback_source_name,
                changed_by,
                feedback,
                df_modified,
                index,
            )

        # This is the existing logic for other row-level actions
        elif action in [
            QAAction.BLANK_VALUE,
            QAAction.REMOVE_ACTING_PREFIX,
        ]:
            col = qa_row.get("Column")
            if col:
                modified_row = handler(
                    row_series=row_series,
                    column_to_edit=col,
                    record_id=record_id,
                    feedback_source=feedback_source_name,
                    changed_by=changed_by,
                    notes=feedback,
                )
                df_modified.loc[index] = modified_row

        elif action == QAAction.POLICY_QUERY:
            handle_policy_query(
                row_series=row_series,
                column_to_edit=qa_row.get("Column"),
                original_feedback=feedback,
                record_id=record_id,
                feedback_source=feedback_source_name,
                changed_by=changed_by,
                notes=feedback,
            )


def apply_qa_edits(
    df_golden: pd.DataFrame,
    df_qa: pd.DataFrame,
    changed_by: str,
    qa_filename: str,
) -> pd.DataFrame:
    df_modified = df_golden.copy()
    feedback_source_name = pathlib.Path(qa_filename).name
    base_input_dir = pathlib.Path(qa_filename).parent

    for _, qa_row in df_qa.iterrows():
        feedback = qa_row.get("feedback")
        if pd.isna(feedback):
            continue

        action, match = detect_rule(feedback)
        print(
            f"DEBUG: Feedback='{feedback}', "
            f"Detected Action='{action.name if action else 'None'}'"
        )

        # Handle DataFrame-level actions
        if action == QAAction.DELETE_RECORD and match:
            record_id = match.group("record_id_to_delete")
            df_modified = handle_delete_record(
                df_modified,
                record_id,
                feedback_source_name,
                changed_by,
                feedback,
            )
            continue
        elif action == QAAction.APPEND_FROM_CSV and match:
            csv_path = match.group("csv_path_to_add")
            print(f"DEBUG: Calling handle_append_from_csv with path='{csv_path}'")
            df_modified = handle_append_from_csv(
                df_modified,
                csv_path,
                base_input_dir,
                feedback_source_name,
                changed_by,
                feedback,
            )
            continue

        # Handle row-level actions
        record_id = qa_row.get("Row(s)")
        if pd.notna(record_id) and record_id in df_modified["RecordID"].values:
            # Pass the full qa_row series to the processing function
            _process_row(
                df_modified[df_modified["RecordID"] == record_id].iloc[0],
                qa_row,
                action,
                match,
                feedback_source_name,
                changed_by,
                feedback,
                df_modified,
            )

    return df_modified


def main():
    parser = argparse.ArgumentParser(description="Apply a QA/edits file to a dataset.")
    parser.add_argument(
        "--input_csv",
        type=pathlib.Path,
        required=True,
        help="Path to the input dataset CSV.",
    )
    parser.add_argument(
        "--qa_csv",
        type=pathlib.Path,
        required=True,
        help="Path to the QA/edits CSV file.",
    )
    parser.add_argument(
        "--output_csv",
        type=pathlib.Path,
        required=True,
        help="Path to save the processed dataset CSV.",
    )
    parser.add_argument(
        "--changelog",
        type=pathlib.Path,
        required=True,
        help="Path to save the changelog for this run.",
    )
    parser.add_argument(
        "--changed_by",
        type=str,
        required=True,
        help="Identifier for who is running the script.",
    )
    args = parser.parse_args()

    try:
        df_input = pd.read_csv(args.input_csv, dtype=str).fillna("")
        df_qa = pd.read_csv(args.qa_csv, dtype=str).fillna("")
    except FileNotFoundError as e:
        print(f"Error: A file was not found - {e}", file=sys.stderr)
        sys.exit(1)

    print("Applying QA edits...")
    df_processed = apply_qa_edits(df_input, df_qa, args.changed_by, str(args.qa_csv))
    print("Edits applied successfully.")

    df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"Processed dataset saved to: {args.output_csv}")

    df_changelog = pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS)
    df_changelog.to_csv(args.changelog, index=False, encoding="utf-8-sig")
    print(f"Changelog for edits saved to: {args.changelog}")

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
