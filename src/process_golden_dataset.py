import argparse
import pathlib
import re
import typing
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import ftfy
import pandas as pd

# Global list to store changelog entries (for demonstration/testing)
# In a real application, this would be a robust logging system
# (e.g., writing to CSV/DB).
changelog_entries = []
changelog_id_counter = 0  # Global counter for changelog IDs


class QAAction(Enum):
    DIRECT_SET = "direct_set"
    CHAR_FIX = "char_fix"
    BLANK_VALUE = "blank_value"
    DEDUP_SEMICOLON = "dedup_semicolon"
    POLICY_QUERY = "policy_query"
    DATA_ENRICH = "data_enrich"
    REMOVE_ACTING_PREFIX = "remove_acting_prefix"
    NOT_FOUND = "not_found"
    _RECORD_FILTERED_OUT = "_record_filtered_out"
    DELETE_RECORD = "delete_record"
    APPEND_FROM_CSV = "append_from_csv"
    NAME_SPLIT_SUCCESS = "name_split_success"
    NAME_SPLIT_REVIEW_NEEDED = "name_split_review_needed"
    NAME_PARSE_SUCCESS = "name_parse_success"
    NAME_PARSE_REVIEW_NEEDED = "name_parse_review_needed"


@dataclass
class QAEditRule:
    pattern: re.Pattern
    action: QAAction
    value_parser: typing.Callable | None


CHANGELOG_COLUMNS = [
    "ChangeID",  # New column for unique change ID
    "timestamp",
    "record_id",
    "column_changed",
    "old_value",
    "new_value",
    "feedback_source",
    "notes",
    "changed_by",
    "RuleAction",  # New column for the rule action that triggered the change
]

# Illustrative example rules
RULES = {
    # Rule for record deletion
    r"Delete RecordID (?P<record_id_to_delete>\S+)": QAAction.DELETE_RECORD,
    # Rule for appending from CSV
    (
        r"Append records from CSV " r"(?P<csv_path_to_add>[\w./-]+\.csv)"
    ): QAAction.APPEND_FROM_CSV,
    # Example: "Set Name to NYC311"
    r"Set (?P<column>\w+) to (?P<value>.+)": QAAction.DIRECT_SET,
    # Rule for "Fix "[value]"" (double quotes)
    r"Fix \"(?P<value>.*?)\"": QAAction.DIRECT_SET,
    # Rule for "Fix '[value]'" (single quotes)
    r"Fix '(?P<value>.*?)'": QAAction.DIRECT_SET,
    # New rule for operational status discussions
    r".*(?:makes it look|appears|seems)\s+(?:inactive|active).*": QAAction.POLICY_QUERY,
    # New rule for acronym-like direct values
    r"^(?P<value>[A-Z0-9+-.]{1,10})$": QAAction.DIRECT_SET,
    # New rule for "CorrectValue rather than IncorrectValue"
    r"^(?P<value>[A-Z0-9+-. /]+?) rather than [A-Z0-9+-. /]+?$": QAAction.DIRECT_SET,
    # New rule for "[Subject] is now/currently [New Value]"
    r"^(?:.*is now|.*is currently)\s+(?P<value>.+)$": QAAction.DIRECT_SET,
    # Example: "Fix special characters in Description"
    r"Fix special characters(?: in (?P<column>\w+))?": QAAction.POLICY_QUERY,
    # Example: "Remove value of PrincipalOfficerContactURL"
    r"Remove value of .*": QAAction.BLANK_VALUE,
    # Rule for departure feedback - now triggers policy query instead of blanking
    (
        r"^(?:.*(?:has left|is no longer with|is no longer at))" r"(?:\s+\w+)*$"
    ): QAAction.POLICY_QUERY,
    # New rule for "no longer Acting"
    r"(?:Confirmed, ?so )?no longer Acting": QAAction.REMOVE_ACTING_PREFIX,
    # Example: "What is the logic..." - More specific policy queries may catch first
    r"What is the logic.*": QAAction.POLICY_QUERY,
    # Example: "Repeated values error" - now a policy query since handled by global rule
    (
        r"(?:Repeated values?|Duplicated? values?|Values? repeated)"
        r"(?: error| issue| found)?"
    ): QAAction.POLICY_QUERY,
    # Example: "Consider elimination of Notes field..."
    r"Consider elimination of (?P<column>\w+) field.*": QAAction.POLICY_QUERY,
    # Enhanced General Policy Query Patterns
    r"(What is the logic|What's the process|Why is|Is this an error|"
    r"How should we handle|Is this correct|Can we find|"
    r"Should we be able)": QAAction.POLICY_QUERY,
    r"(Consider elimination|Consider merging|Should we delete|"
    r"Review for removal|Discuss|Mistakenly populated field|"
    r"appears to be an error|is not an acronym)": QAAction.POLICY_QUERY,
    # New patterns for research/verification tasks
    (
        r"(?:should|can|could)\s+(?:be able to )?find.*"
        r"(?:press release|announcement|news)"
    ): QAAction.POLICY_QUERY,
    (
        r"(?:I'?m certain|must have|should have|has to have).*"
        r"(?:founding year|date|established)"
    ): QAAction.POLICY_QUERY,
    # General rule for extracting double-quoted value for DIRECT_SET
    r".*?\"(?P<value>.*?)\".*": QAAction.DIRECT_SET,
    # General rule for extracting single-quoted value for DIRECT_SET
    r".*?'(?P<value>.*?)'.*": QAAction.DIRECT_SET,
    # Catch-all for questions if not matched above
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
    rule_action: str | None = None,  # New parameter for the rule action
):
    """Logs a change to the changelog_entries list.

    Args:
        record_id: The ID of the record being changed.
        column_changed: The name of the column being changed.
        old_value: The previous value.
        new_value: The new value.
        feedback_source: The source of the feedback (e.g., QA filename).
        notes: Additional notes about the change.
        changed_by: The user/process that made the change.
        rule_action: The QAAction that triggered this change (optional).
    """
    global changelog_entries, changelog_id_counter
    changelog_id_counter += 1  # Increment the counter for each new entry

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
    # print(f"Change logged: {entry}") # For debugging


def detect_rule(feedback: str) -> tuple[QAAction, re.Match | None]:
    """Detects which QA rule matches the feedback string.

    Args:
        feedback: The feedback string from the QA sheet.

    Returns:
        A tuple containing the QAAction and the regex match object if a rule is found,
        otherwise (QAAction.POLICY_QUERY, None) as a default fallback.
    """
    for pattern_str, action in RULES.items():
        match = re.search(pattern_str, feedback, re.IGNORECASE)
        if match:
            return action, match

    # If no specific rule matches, default to POLICY_QUERY
    print(
        f"Info: Feedback '{feedback}' not matched by specific rules, "
        f"defaulting to POLICY_QUERY."
    )
    return QAAction.POLICY_QUERY, None


# Stub handler functions
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


def handle_char_fix(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    old_value = row_series.get(column_to_edit)
    if isinstance(old_value, str):
        repaired_text = ftfy.fix_text(old_value)
        # Handle specific character sequences
        repaired_text = repaired_text.replace("¬†", " ")  # Fix ¬†
        repaired_text = repaired_text.replace("\u00a0", " ")  # Fix NBSP
        # Add new specific mojibake replacements
        repaired_text = repaired_text.replace("√É¬©", "é")  # Fix for é
        repaired_text = repaired_text.replace("√É¬°", "á")  # Fix for á
        new_value = repaired_text.strip()
        if new_value != old_value:
            log_change(
                record_id,
                column_to_edit,
                old_value,
                new_value,
                feedback_source,
                notes,
                changed_by,
                QAAction.CHAR_FIX.value,
            )
            row_series[column_to_edit] = new_value
    elif old_value is not None and not isinstance(old_value, str):
        print(
            f"Warning: RecordID {record_id}, Column {column_to_edit}: CHAR_FIX "
            f"applied to non-string type '{type(old_value)}'. Value: '{old_value}'. "
            "Skipping fix."
        )
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
    new_value = ""
    if old_value != new_value:
        log_change(
            record_id,
            column_to_edit,
            old_value,
            new_value,
            feedback_source,
            notes,
            changed_by,
            QAAction.BLANK_VALUE.value,
        )
        row_series[column_to_edit] = new_value
    return row_series


def handle_dedup_semicolon(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    old_value = row_series.get(column_to_edit)
    if isinstance(old_value, str) and old_value:
        items = old_value.split(";")
        stripped_items = [item.strip() for item in items]
        unique_items = list(dict.fromkeys([item for item in stripped_items if item]))
        new_value = ";".join(unique_items)

        if new_value != old_value:
            log_change(
                record_id,
                column_to_edit,
                old_value,
                new_value,
                feedback_source,
                notes,
                changed_by,
                QAAction.DEDUP_SEMICOLON.value,
            )
            row_series[column_to_edit] = new_value
    elif old_value is not None and not isinstance(old_value, str):
        print(
            f"Warning: RecordID {record_id}, Column {column_to_edit}: "
            f"DEDUP_SEMICOLON applied to non-string type '{type(old_value)}'. "
            f"Value: '{old_value}'. Skipping fix."
        )
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
        record_id=record_id,
        column_changed=column_to_edit if column_to_edit else "Policy Question",
        old_value="N/A",
        new_value="N/A",
        feedback_source=feedback_source,
        notes=original_feedback,
        changed_by=changed_by,
        rule_action=QAAction.POLICY_QUERY.value,
    )
    return row_series


def handle_data_enrich(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
):
    print(f"Called handle_data_enrich for column '{column_to_edit}'")
    return row_series


def handle_not_found(
    row_series: pd.Series,
    original_feedback: str,
    record_id: str | None,
    feedback_source: str | None,
    changed_by: str | None,
    notes: str | None = None,
):
    print(f"Called handle_not_found for feedback: {original_feedback}")
    return row_series


def handle_record_filtered_out(
    row_series: pd.Series,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,
) -> pd.Series:
    log_change(
        record_id=record_id,
        column_changed="_RECORD_FILTERED_OUT",
        old_value="N/A",
        new_value="N/A",
        feedback_source=feedback_source,
        notes=notes if notes else "Record filtered out by a rule",
        changed_by=changed_by,
        rule_action=QAAction._RECORD_FILTERED_OUT.value,
    )
    return row_series


def handle_remove_acting_prefix(
    row_series: pd.Series,
    column_to_edit: str,
    record_id: str,
    feedback_source: str,
    changed_by: str,
    notes: str | None = None,  # This is the original feedback string
) -> pd.Series:
    """Removes 'Acting ' prefix from a field if present (case-insensitive)."""
    old_value = row_series.get(column_to_edit)
    new_value = old_value  # Initialize

    # Define standardized log notes based on original feedback and old_value
    # These will be fully formed here for clarity if used.
    # The `notes` variable here is the original feedback.
    _log_note_no_prefix = (
        f"Rule '{notes}' triggered, but no 'Acting ' prefix found/changed "
        f"in '{old_value}'."
    )
    _log_note_non_string = (
        f"Rule '{notes}' triggered on non-string value '{old_value}'. "
        f"No action taken."
    )
    _log_note_none_value = f"Rule '{notes}' triggered on None value. No action taken."

    if isinstance(old_value, str):
        temp_old_value_lower = old_value.lower()
        # Check if it starts with "acting" possibly followed by spaces,
        # or is just "acting"
        if temp_old_value_lower.startswith("acting"):
            match = re.match(r"acting\s*", old_value, re.IGNORECASE)
            if match:
                prefix_len = len(match.group(0))
                # Only proceed if the prefix found is shorter than the whole string,
                # or if the whole string is just variations of "acting"
                # (e.g. "Acting  ")
                if (
                    prefix_len < len(old_value)
                    or temp_old_value_lower.strip() == "acting"
                ):
                    new_value = old_value[prefix_len:].strip()
                # If prefix_len == len(old_value) and
                # temp_old_value_lower.strip() != "acting",
                # it means something like old_value was "actingdirector" -
                # no space. We don't change this.
                # The temp_old_value_lower.strip() == "acting" handles
                # "Acting  " -> ""

        if new_value != old_value:
            # Standardized note for successful removal
            log_note_for_change = (
                f"Removed 'Acting' prefix from '{old_value}' to get '{new_value}'. "
                f"Original feedback: '{notes}'"
            )
            if old_value.lower().strip() == "acting" and new_value == "":
                log_note_for_change = (
                    f"Changed '{old_value}' to empty string based on "
                    f"'no longer Acting' feedback: '{notes}'"
                )

            log_change(
                record_id,
                column_to_edit,
                old_value,
                new_value,
                feedback_source,
                log_note_for_change,
                changed_by,
                QAAction.REMOVE_ACTING_PREFIX.value,
            )
            row_series[column_to_edit] = new_value
        else:  # No change was made to the string value (e.g., no prefix,
            # or not actionable)
            print(
                f"Info: RecordID {record_id}, Column {column_to_edit}: "
                f"Rule 'no longer Acting' triggered on non-string value "
                f"'{old_value}'. "
                f"Feedback: '{notes}'"
            )
            log_change(
                record_id,
                column_to_edit,
                old_value,
                old_value,  # No change
                feedback_source,
                _log_note_no_prefix,
                changed_by,
                QAAction.REMOVE_ACTING_PREFIX.value,
            )
    elif old_value is None:
        print(
            f"Info: RecordID {record_id}, Column {column_to_edit}: "
            f"Rule 'no longer Acting' triggered on None value. "
            f"Feedback: '{notes}'"
        )
        log_change(
            record_id,
            column_to_edit,
            old_value,  # Will be logged as None/NaN
            old_value,  # No change
            feedback_source,
            _log_note_none_value,
            changed_by,
            QAAction.REMOVE_ACTING_PREFIX.value,
        )
    else:  # Non-string, non-None value
        print(
            f"Info: RecordID {record_id}, Column {column_to_edit}: "
            f"Rule 'no longer Acting' triggered on non-string value '{old_value}'. "
            f"Feedback: '{notes}'"
        )
        log_change(
            record_id,
            column_to_edit,
            old_value,
            old_value,  # No change
            feedback_source,
            _log_note_non_string,
            changed_by,
            QAAction.REMOVE_ACTING_PREFIX.value,
        )

    return row_series


def handle_delete_record(
    current_df: pd.DataFrame,
    record_id_to_delete: str,
    feedback_source: str,
    changed_by: str,
    notes_from_feedback: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """Deletes a specific record by its RecordID from the DataFrame.

    Args:
        current_df: The current DataFrame to modify.
        record_id_to_delete: The RecordID to delete.
        feedback_source: Source of the feedback (e.g., QA filename).
        changed_by: User/process that made the change.
        notes_from_feedback: The original feedback string.
        log_change_func: Function to call for logging changes.
        qa_action_enum: The QAAction enum class for action types.

    Returns:
        Modified DataFrame with the record deleted (if found).
    """
    # Check if the record exists
    matching_rows = current_df[current_df["RecordID"] == record_id_to_delete]

    if matching_rows.empty:
        # Record not found
        print(
            f"Warning: RecordID '{record_id_to_delete}' not found for deletion. "
            f"Feedback: '{notes_from_feedback}'"
        )
        log_change_func(
            record_id=record_id_to_delete,
            column_changed="_ROW_DELETE_FAILED",
            old_value="Record Not Found",
            new_value="N/A",
            feedback_source=feedback_source,
            notes=f"Record not found for deletion. Feedback: {notes_from_feedback}",
            changed_by=changed_by,
            rule_action=qa_action_enum.DELETE_RECORD.value,
        )
        return current_df

    # Get the row data for logging (using Name if available, otherwise just note
    # it's the entire row)
    old_row_data = matching_rows.iloc[0].get("Name", "Entire Row Data")

    # Log the deletion
    log_change_func(
        record_id=record_id_to_delete,
        column_changed="_ROW_DELETED",
        old_value=old_row_data,
        new_value="N/A",
        feedback_source=feedback_source,
        notes=notes_from_feedback,
        changed_by=changed_by,
        rule_action=qa_action_enum.DELETE_RECORD.value,
    )

    # Delete the row
    modified_df = current_df[current_df["RecordID"] != record_id_to_delete].copy()

    print(f"Deleted RecordID '{record_id_to_delete}' from dataset.")

    return modified_df


def handle_append_from_csv(
    current_df: pd.DataFrame,
    csv_path_to_add_str: str,
    base_input_dir: pathlib.Path,
    feedback_source: str,
    changed_by: str,
    notes_from_feedback: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """Appends all records from a specified CSV file to the current DataFrame.

    Args:
        current_df: The current DataFrame to append to.
        csv_path_to_add_str: Path to the CSV file to append (relative or absolute).
        base_input_dir: Base directory for resolving relative paths.
        feedback_source: Source of the feedback (e.g., QA filename).
        changed_by: User/process that made the change.
        notes_from_feedback: The original feedback string.
        log_change_func: Function to call for logging changes.
        qa_action_enum: The QAAction enum class for action types.

    Returns:
        Modified DataFrame with new records appended.
    """
    # Resolve the CSV path
    csv_path_obj = pathlib.Path(csv_path_to_add_str)
    resolved_csv_path: pathlib.Path

    if csv_path_obj.is_absolute() or csv_path_to_add_str.startswith("data/"):
        # If absolute, or seems to be project-root relative starting with "data/"
        resolved_csv_path = csv_path_obj
    else:
        # Otherwise, assume it's relative to the QA file's directory (base_input_dir)
        resolved_csv_path = base_input_dir / csv_path_obj

    try:
        # Load the new records
        df_new_records = pd.read_csv(resolved_csv_path, dtype=str).fillna("")

        if df_new_records.empty:
            print(
                f"Warning: CSV file '{resolved_csv_path}' is empty. "
                "No records to append."
            )
            return current_df

        print(f"Loading {len(df_new_records)} records from '{resolved_csv_path}'")

        # Optional: Schema check (basic check for RecordID column)
        if "RecordID" not in df_new_records.columns:
            print(
                f"Warning: CSV file '{resolved_csv_path}' missing 'RecordID' column. "
                f"Attempting to append anyway."
            )

        # Check for significant schema differences
        current_cols = set(current_df.columns)
        new_cols = set(df_new_records.columns)
        missing_in_new = current_cols - new_cols
        extra_in_new = new_cols - current_cols

        if missing_in_new:
            print(
                f"Warning: New CSV missing columns present in main dataset: "
                f"{missing_in_new}"
            )
        if extra_in_new:
            print(
                f"Warning: New CSV has extra columns not in main dataset: "
                f"{extra_in_new}"
            )

        # Log each new row being added
        for idx, new_row in df_new_records.iterrows():
            new_record_id = new_row.get("RecordID", f"row_{idx}")
            new_record_name = new_row.get("Name", "Entire New Row Data")

            log_change_func(
                record_id=new_record_id,
                column_changed="_ROW_ADDED",
                old_value="N/A",
                new_value=new_record_name,
                feedback_source=feedback_source,
                notes=f"{notes_from_feedback} - Appended from {resolved_csv_path}",
                changed_by=changed_by,
                rule_action=qa_action_enum.APPEND_FROM_CSV.value,
            )

        # Append the new records
        modified_df = pd.concat([current_df, df_new_records], ignore_index=True)

        print(
            f"Successfully appended {len(df_new_records)} records from "
            f"'{resolved_csv_path}'"
        )

        return modified_df

    except FileNotFoundError:
        print(f"Error: CSV file not found: '{resolved_csv_path}'")
        log_change_func(
            record_id="_APPEND_ERROR",
            column_changed="_APPEND_FROM_CSV_FAILED",
            old_value="File Not Found",
            new_value=str(resolved_csv_path),
            feedback_source=feedback_source,
            notes=f"Failed to append from {resolved_csv_path}: File not found",
            changed_by=changed_by,
            rule_action=qa_action_enum.APPEND_FROM_CSV.value,
        )
        return current_df

    except Exception as e:
        print(f"Error loading CSV file '{resolved_csv_path}': {e}")
        log_change_func(
            record_id="_APPEND_ERROR",
            column_changed="_APPEND_FROM_CSV_FAILED",
            old_value="Load Error",
            new_value=str(e),
            feedback_source=feedback_source,
            notes=f"Failed to append from {resolved_csv_path}: {e}",
            changed_by=changed_by,
            rule_action=qa_action_enum.APPEND_FROM_CSV.value,
        )
        return current_df


ACTION_HANDLERS = {
    QAAction.DIRECT_SET: handle_direct_set,
    QAAction.CHAR_FIX: handle_char_fix,
    QAAction.BLANK_VALUE: handle_blank_value,
    QAAction.DEDUP_SEMICOLON: handle_dedup_semicolon,
    QAAction.POLICY_QUERY: handle_policy_query,
    QAAction.DATA_ENRICH: handle_data_enrich,
    QAAction.REMOVE_ACTING_PREFIX: handle_remove_acting_prefix,
    QAAction.NOT_FOUND: handle_not_found,
    QAAction._RECORD_FILTERED_OUT: handle_record_filtered_out,
    QAAction.DELETE_RECORD: handle_delete_record,
    QAAction.APPEND_FROM_CSV: handle_append_from_csv,
    QAAction.NAME_PARSE_SUCCESS: handle_policy_query,  # Placeholder handler
    QAAction.NAME_PARSE_REVIEW_NEEDED: handle_policy_query,  # Placeholder handler
}


# Helper functions for apply_qa_edits
def _get_qa_input_values(
    qa_row: pd.Series,
) -> tuple[str | None, str | None, str | None]:
    """
    Extracts and returns RecordID, Column, and Feedback from a QA row.

    Args:
        qa_row: A pandas Series representing a row from the QA edits DataFrame.
                Expected to contain 'Row(s)', 'Column', and 'feedback'.

    Returns:
        A tuple containing:
        - record_id_to_edit (str | None): The RecordID to edit, or None if missing/NaN.
        - column_to_edit (str | None): The column name to edit, or None if missing/NaN.
        - feedback (str | None): The feedback text, or None if missing/NaN.
    """
    record_id_val = qa_row.get("Row(s)")
    column_val = qa_row.get("Column")
    feedback_val = qa_row.get("feedback")

    record_id_to_edit: str | None = None
    column_to_edit: str | None = None
    feedback_text: str | None = None

    if pd.isna(record_id_val):
        feedback_str_for_log = str(feedback_val) if pd.notna(feedback_val) else "N/A"
        warning_msg = (
            f"Warning: QA row has missing RecordID (expected in 'Row(s)' column). "
            f"Feedback provided: '{feedback_str_for_log}'. Skipping record linkage."
        )
        print(warning_msg)
        if pd.notna(feedback_val):
            feedback_text = str(feedback_val)
        return None, None, feedback_text

    record_id_to_edit = str(record_id_val)

    if pd.notna(column_val):
        column_to_edit = str(column_val)

    if pd.notna(feedback_val):
        feedback_text = str(feedback_val)

    return record_id_to_edit, column_to_edit, feedback_text


def _find_target_indices(
    df_modified: pd.DataFrame, record_id_to_edit: str, feedback_for_log: str | None
) -> pd.Index | None:
    """
    Finds the indices of rows in df_modified that match the given RecordID.

    Args:
        df_modified: The DataFrame to search within (e.g., the golden dataset).
        record_id_to_edit: The RecordID to search for.
        feedback_for_log: The feedback string associated with this QA edit, for logging.

    Returns:
        A pandas Index of matching row indices, or None if no match is found
        or if record_id_to_edit is invalid.
    """
    if not record_id_to_edit:  # Should ideally be caught by _get_qa_input_values
        print(
            "Warning: _find_target_indices called with empty or invalid "
            "record_id_to_edit."
        )
        return None

    target_indices = df_modified[df_modified["RecordID"] == record_id_to_edit].index

    if target_indices.empty:
        feedback_info = (
            f" for feedback: '{feedback_for_log}'" if feedback_for_log else ""
        )
        warning_msg = (
            f"Warning: RecordID '{record_id_to_edit}' from QA sheet not found "
            f"in golden dataset{feedback_info}. Skipping."
        )
        print(warning_msg)
        return None

    return target_indices


def _prepare_base_handler_args(
    row_series: pd.Series,
    actual_record_id: str,
    feedback_source_name: str,
    changed_by_user: str,
    feedback_text: str,
) -> dict:
    """Prepare the base arguments dictionary for handlers."""
    return {
        "row_series": row_series,
        "record_id": actual_record_id,
        "feedback_source": feedback_source_name,
        "changed_by": changed_by_user,
        "notes": feedback_text,
    }


def _handle_direct_set_args(
    handler_args: dict,
    match: re.Match | None,
    column_to_edit_from_qa: str | None,
    feedback_text: str,
    actual_record_id: str,
    feedback_source_name: str,
    changed_by_user: str,
) -> tuple[str | None, bool]:
    """Handle argument preparation for DIRECT_SET action."""
    parsed_col_from_rule = (
        match.group("column") if match and "column" in match.groupdict() else None
    )
    parsed_value = (
        match.group("value") if match and "value" in match.groupdict() else None
    )

    if parsed_value is None:
        msg = (
            f"Warning: RecordID {actual_record_id}: DIRECT_SET failed to parse value "
            f"from feedback: '{feedback_text}'. Skipping."
        )
        print(msg)
        log_column_name = column_to_edit_from_qa or "DIRECT_SET_Value_Parse_Error"
        log_notes = f"Feedback: {feedback_text}"
        log_change(
            actual_record_id,
            log_column_name,
            "Parse Failed",
            "Skipped",
            feedback_source_name,
            log_notes,
            changed_by_user,
            QAAction.DIRECT_SET.value,
        )
        return None, False

    final_column_to_edit = column_to_edit_from_qa or parsed_col_from_rule

    if final_column_to_edit is None:
        msg = (
            f"Warning: RecordID {actual_record_id}: DIRECT_SET no column specified "
            f"for feedback: '{feedback_text}'. Skipping."
        )
        print(msg)
        log_notes = f"Feedback: {feedback_text}"
        log_change(
            actual_record_id,
            "DIRECT_SET_Column_Error",
            "No Column",
            "Skipped",
            feedback_source_name,
            log_notes,
            changed_by_user,
            QAAction.DIRECT_SET.value,
        )
        return None, False

    # Initial strip for whitespace
    processed_value = parsed_value.strip()

    # Remove surrounding double quotes if present
    if (
        len(processed_value) >= 2
        and processed_value.startswith('"')
        and processed_value.endswith('"')
    ):
        processed_value = processed_value[1:-1]

    # Remove surrounding single quotes if present (applied after double quote check)
    if (
        len(processed_value) >= 2
        and processed_value.startswith("'")
        and processed_value.endswith("'")
    ):
        processed_value = processed_value[1:-1]

    handler_args["column_to_edit"] = final_column_to_edit
    handler_args["new_value"] = processed_value
    return final_column_to_edit, True


def _handle_col_specific_action_args(
    handler_args: dict,
    match: re.Match | None,
    column_to_edit_from_qa: str | None,
    action: QAAction,
    feedback_text: str,
    actual_record_id: str,
    feedback_source_name: str,
    changed_by_user: str,
) -> tuple[str | None, bool]:
    """Handle argument preparation for column-specific actions."""
    parsed_col_from_rule = (
        match.group("column")
        if match and "column" in match.groupdict() and match.group("column")
        else None
    )
    final_column_to_edit = column_to_edit_from_qa or parsed_col_from_rule

    if final_column_to_edit is None:
        msg = (
            f"Warning: RecordID {actual_record_id}: Action {action.name} no column "
            f"specified for feedback: '{feedback_text}'. Skipping."
        )
        print(msg)
        log_column_name = f"{action.name}_Column_Error"
        log_notes = f"Feedback: {feedback_text}"
        log_change(
            actual_record_id,
            log_column_name,
            "No Column",
            "Skipped",
            feedback_source_name,
            log_notes,
            changed_by_user,
            action.value,
        )
        return None, False

    handler_args["column_to_edit"] = final_column_to_edit
    return final_column_to_edit, True


def _handle_policy_or_not_found_args(
    handler_args: dict,
    action: QAAction,
    column_to_edit_from_qa: str | None,
    feedback_text: str,
) -> tuple[str | None, bool]:
    """Handle argument preparation for POLICY_QUERY and NOT_FOUND actions."""
    if action == QAAction.POLICY_QUERY:
        handler_args["column_to_edit"] = column_to_edit_from_qa
        handler_args["original_feedback"] = feedback_text
        handler_args["notes"] = feedback_text
    elif action == QAAction.NOT_FOUND:
        handler_args["original_feedback"] = feedback_text

    return column_to_edit_from_qa, True


def _execute_handler_safely(
    handler: typing.Callable,
    handler_args: dict,
    action: QAAction,
    actual_record_id: str,
    feedback_text: str,
    final_column_to_edit: str | None,
    feedback_source_name: str,
    changed_by_user: str,
) -> pd.Series | None:
    """Execute the handler function safely with error handling."""
    try:
        actions_strictly_needing_column = {
            QAAction.DIRECT_SET,
            QAAction.CHAR_FIX,
            QAAction.BLANK_VALUE,
            QAAction.DEDUP_SEMICOLON,
            QAAction.DATA_ENRICH,
        }

        if (
            action in actions_strictly_needing_column
            and handler_args.get("column_to_edit") is None
        ):
            msg = (
                f"Error: RecordID {actual_record_id}: Column not set for handler "
                f"{action.name} with feedback '{feedback_text}'. Skipping."
            )
            print(msg)
            log_column_name = f"{action.name}_Internal_Column_Error"
            log_notes = f"Feedback: {feedback_text}"
            log_change(
                actual_record_id,
                log_column_name,
                "Missing Column Arg",
                "Skipped",
                feedback_source_name,
                log_notes,
                changed_by_user,
                action.value,
            )
            return None

        return handler(**handler_args)

    except Exception as e:
        msg = (
            f"Error processing RecordID {actual_record_id} with feedback "
            f"'{feedback_text}' using {action.name}: {e}"
        )
        print(msg)
        log_column_name = final_column_to_edit or str(action)
        log_notes = f"Feedback: {feedback_text}"
        log_change(
            actual_record_id,
            log_column_name,
            "Handler Error",
            str(e),
            feedback_source_name,
            log_notes,
            changed_by_user,
            action.value,
        )
        return None


def _apply_action_to_single_golden_row(
    original_row_series: pd.Series,
    feedback_text: str,
    column_to_edit_from_qa: str | None,
    feedback_source_name: str,
    changed_by_user: str,
    action_handlers: dict,
    rules_dict: dict,
    qa_action_enum: type[Enum],
) -> pd.Series:
    """
    Process a single row from the golden dataset against a single piece of QA feedback.
    """
    actual_record_id = str(original_row_series["RecordID"])
    action, match = detect_rule(feedback_text)
    handler = action_handlers.get(action)

    if not handler:
        msg = (
            f"Warning: No handler for action {action} "
            f"(feedback: '{feedback_text}'). Skipping."
        )
        print(msg)
        log_notes = f"Feedback: {feedback_text}"
        log_change(
            actual_record_id,
            "Rule Matching",
            "No Handler",
            str(action),
            feedback_source_name,
            log_notes,
            changed_by_user,
            action.value if action else "unknown",  # Pass the action value
        )
        return original_row_series

    handler_args = _prepare_base_handler_args(
        original_row_series,
        actual_record_id,
        feedback_source_name,
        changed_by_user,
        feedback_text,
    )

    final_column_to_edit = None
    continue_processing = True

    if action == QAAction.DIRECT_SET:
        final_column_to_edit, continue_processing = _handle_direct_set_args(
            handler_args,
            match,
            column_to_edit_from_qa,
            feedback_text,
            actual_record_id,
            feedback_source_name,
            changed_by_user,
        )
    elif action in {
        QAAction.CHAR_FIX,
        QAAction.BLANK_VALUE,
        QAAction.DEDUP_SEMICOLON,
        QAAction.DATA_ENRICH,
        QAAction.REMOVE_ACTING_PREFIX,
    }:
        final_column_to_edit, continue_processing = _handle_col_specific_action_args(
            handler_args,
            match,
            column_to_edit_from_qa,
            action,
            feedback_text,
            actual_record_id,
            feedback_source_name,
            changed_by_user,
        )
    else:  # POLICY_QUERY or NOT_FOUND
        final_column_to_edit, continue_processing = _handle_policy_or_not_found_args(
            handler_args,
            action,
            column_to_edit_from_qa,
            feedback_text,
        )

    if not continue_processing:
        return original_row_series

    modified_row_series = _execute_handler_safely(
        handler,
        handler_args,
        action,
        actual_record_id,
        feedback_text,
        final_column_to_edit,
        feedback_source_name,
        changed_by_user,
    )

    return (
        modified_row_series if modified_row_series is not None else original_row_series
    )


def _process_single_qa_row(
    qa_row: pd.Series,
    df_modified: pd.DataFrame,
    feedback_source_name: str,
    changed_by: str,
    action_handlers: dict,
    rules_dict: dict,
    qa_action_enum: type[Enum],
) -> None:
    """Process one row from the QA edits DataFrame."""
    (
        record_id_to_edit,
        column_to_edit_from_qa,
        feedback_text,
    ) = _get_qa_input_values(qa_row)

    if record_id_to_edit is None:
        return

    if feedback_text is None:
        msg = (
            f"Warning: RecordID '{record_id_to_edit}' has no feedback text provided "
            f"in QA sheet. Skipping this QA edit."
        )
        print(msg)
        log_change(
            record_id_to_edit,
            "QA Processing Error",
            "No Feedback Text",
            "Skipped",
            feedback_source_name,
            "Missing feedback text in QA sheet for given RecordID",
            changed_by,
            QAAction.POLICY_QUERY.value,
        )
        return

    target_row_indices = _find_target_indices(
        df_modified, record_id_to_edit, feedback_text
    )

    if target_row_indices is None or target_row_indices.empty:
        return

    for golden_row_index in target_row_indices:
        original_row_series = df_modified.loc[golden_row_index].copy()
        modified_row_series = _apply_action_to_single_golden_row(
            original_row_series,
            feedback_text,
            column_to_edit_from_qa,
            feedback_source_name,
            changed_by,
            action_handlers,
            rules_dict,
            qa_action_enum,
        )
        df_modified.loc[golden_row_index] = modified_row_series


def apply_qa_edits(  # noqa: C901
    df_golden: pd.DataFrame,
    df_qa: pd.DataFrame,
    changed_by: str,
    qa_filename: str,
) -> pd.DataFrame:
    """Apply QA edits from the QA DataFrame to the Golden DataFrame."""
    df_modified = df_golden.copy()
    feedback_source_name = pathlib.Path(qa_filename).name
    base_input_dir = pathlib.Path(qa_filename).parent

    # If df_qa is empty but has the correct columns (e.g. dummy file),
    # skip row processing
    if df_qa.empty and list(df_qa.columns) == ["Row(s)", "Column", "feedback"]:
        print(
            "QA DataFrame is empty (likely from dummy file), "
            "skipping QA row processing."
        )
        return df_modified

    # Only check columns if df_qa is not empty
    if not df_qa.empty:
        expected_qa_cols = ["Row(s)", "Column", "feedback"]
        for col in expected_qa_cols:
            if col not in df_qa.columns:
                raise ValueError(f"QA DataFrame is missing expected column: {col}")
    else:  # If df_qa is empty but didn't match the column check above,
        # it might be an issue.
        # This case should ideally be caught by the loading logic or be truly empty.
        # For safety, if it reached here as genuinely empty without columns,
        # skip processing rows.
        print("QA DataFrame is completely empty, skipping QA row processing.")
        return df_modified

    # Clean up encoding issues in the feedback column using ftfy
    df_qa["feedback"] = df_qa["feedback"].apply(
        lambda x: ftfy.fix_text(x) if pd.notna(x) else x
    )

    for _, qa_row in df_qa.iterrows():
        # Get feedback text first to determine action
        feedback_val = qa_row.get("feedback")
        if pd.isna(feedback_val):
            continue

        feedback_text = str(feedback_val)

        # Detect the rule/action
        action, match = detect_rule(feedback_text)

        # Handle DataFrame-level actions (DELETE_RECORD, APPEND_FROM_CSV)
        if action == QAAction.DELETE_RECORD:
            if match:
                record_id_to_delete = match.group("record_id_to_delete")
                df_modified = handle_delete_record(
                    df_modified,
                    record_id_to_delete,
                    feedback_source_name,
                    changed_by,
                    feedback_text,
                    log_change,
                    QAAction,
                )
                continue
            else:
                print(
                    f"Error: DELETE_RECORD action but no record ID found in "
                    f"feedback: '{feedback_text}'"
                )
                continue

        elif action == QAAction.APPEND_FROM_CSV:
            if match:
                csv_path_to_add = match.group("csv_path_to_add")
                df_modified = handle_append_from_csv(
                    df_modified,
                    csv_path_to_add,
                    base_input_dir,
                    feedback_source_name,
                    changed_by,
                    feedback_text,
                    log_change,
                    QAAction,
                )
                continue
            else:
                print(
                    f"Error: APPEND_FROM_CSV action but no CSV path found in "
                    f"feedback: '{feedback_text}'"
                )
                continue

        # For all other actions, use the existing row-specific processing
        _process_single_qa_row(
            qa_row,
            df_modified,
            feedback_source_name,
            changed_by,
            ACTION_HANDLERS,
            RULES,
            QAAction,
        )

    return df_modified


def apply_global_deduplication(
    df_input: pd.DataFrame,
    changed_by_user: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """Apply global deduplication to specified semicolon-separated columns.

    Args:
        df_input: Input DataFrame to process.
        changed_by_user: String identifying who/what made the changes.
        log_change_func: Function to call for logging changes.
        qa_action_enum: The QAAction enum class for action types.

    Returns:
        A processed copy of the input DataFrame with deduplication applied.
    """
    # Define columns that should always have semicolon deduplication applied
    semicolon_columns_to_dedup = [
        "AlternateOrFormerNames",
        "AlternateOrFormerAcronyms",
    ]

    df_processed = df_input.copy()

    for column_name_to_dedup in semicolon_columns_to_dedup:
        if column_name_to_dedup not in df_processed.columns:
            print(
                f"Warning: Column {column_name_to_dedup} not found in dataset. "
                f"Skipping global deduplication for this column."
            )
            continue

        for index, row_series in df_processed.iterrows():
            old_value = row_series.get(column_name_to_dedup)
            record_id = str(row_series["RecordID"])

            if isinstance(old_value, str) and old_value.strip():
                # Split by semicolon, strip items, filter empty ones
                items = old_value.split(";")
                stripped_items = [item.strip() for item in items]
                filtered_items = [item for item in stripped_items if item]

                # Remove duplicates while preserving order
                seen = set()
                unique_items = []
                for item in filtered_items:
                    if item not in seen:
                        seen.add(item)
                        unique_items.append(item)

                new_value = ";".join(unique_items)

                if new_value != old_value:
                    # Log the change
                    log_change_func(
                        record_id=record_id,
                        column_changed=column_name_to_dedup,
                        old_value=old_value,
                        new_value=new_value,
                        feedback_source="System_GlobalRule",
                        notes=(
                            f"Global deduplication applied to "
                            f"{column_name_to_dedup}"
                        ),
                        changed_by=changed_by_user,
                        rule_action=qa_action_enum.DEDUP_SEMICOLON.value,
                    )
                    # Update the DataFrame
                    df_processed.loc[index, column_name_to_dedup] = new_value

    return df_processed


def apply_global_character_fixing(
    df_input: pd.DataFrame,
    changed_by_user: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """Apply global character fixing to specified text columns.

    Args:
        df_input: Input DataFrame to process.
        changed_by_user: String identifying who/what made the changes.
        log_change_func: Function to call for logging changes.
        qa_action_enum: The QAAction enum class for action types.

    Returns:
        A processed copy of the input DataFrame with character fixing applied.
    """
    # Define columns that should have character fixing applied
    text_columns_to_fix = [
        "Name",
        "NameAlphabetized",
        "Description",
        "AlternateOrFormerNames",
        "AlternateOrFormerAcronyms",
        "PrincipalOfficerName",
        "PrincipalOfficerTitle",
        "Notes",
    ]

    df_processed = df_input.copy()

    for column_name_to_fix in text_columns_to_fix:
        if column_name_to_fix not in df_processed.columns:
            print(
                f"Warning: Column {column_name_to_fix} not found in dataset. "
                f"Skipping global character fixing for this column."
            )
            continue

        for index, row_series in df_processed.iterrows():
            old_value = row_series.get(column_name_to_fix)
            record_id = str(row_series["RecordID"])

            # Skip if value is not a string or is NaN
            if not isinstance(old_value, str):
                continue

            # Apply comprehensive text fixing
            new_value = ftfy.fix_text(old_value)
            new_value = unicodedata.normalize("NFKC", new_value)
            new_value = new_value.replace("¬†", " ").replace("\u00a0", " ")
            # Add the specific mojibake replacements from handle_char_fix
            new_value = new_value.replace("√É¬©", "é")  # Fix for é
            new_value = new_value.replace("√É¬°", "á")  # Fix for á
            new_value = new_value.strip()

            if new_value != old_value:
                # Log the change
                log_change_func(
                    record_id=record_id,
                    column_changed=column_name_to_fix,
                    old_value=old_value,
                    new_value=new_value,
                    feedback_source="System_GlobalCharFix",
                    notes=(
                        f"Global character/Unicode fixing applied to "
                        f"{column_name_to_fix}"
                    ),
                    changed_by=changed_by_user,
                    rule_action=qa_action_enum.CHAR_FIX.value,
                )
                # Update the DataFrame
                df_processed.loc[index, column_name_to_fix] = new_value

    return df_processed


def _log_name_split_issue(
    log_change_func: callable,
    record_id: str,
    original_full_name_raw: str | None,
    changed_by_user: str,
    qa_action_enum: type[Enum],
    reason: str,
):
    """Helper to log issues during name splitting."""
    log_notes = (
        f"PrincipalOfficerName ('{original_full_name_raw}') {reason}; "
        "requires manual review."
    )
    # Check for NA, non-string, or effectively empty string
    is_na = pd.isna(original_full_name_raw)
    is_not_str = not isinstance(original_full_name_raw, str)

    # Check for empty string only if it's a string, to avoid error on non-str types
    is_effectively_empty_str = False
    if not is_na and not is_not_str:  # i.e., it is a string
        is_effectively_empty_str = not original_full_name_raw.strip()

    if is_na or is_not_str or is_effectively_empty_str:
        log_notes = (
            f"PrincipalOfficerName ('{original_full_name_raw}') is effectively empty, "
            "None, or not a string after initial processing; requires manual review."
        )

    log_change_func(
        record_id=record_id,
        column_changed="PrincipalOfficerName_SplitReview",
        old_value=(
            original_full_name_raw if pd.notna(original_full_name_raw) else "N/A"
        ),
        new_value="N/A",
        feedback_source="System_NameSplitRule",
        notes=log_notes,
        changed_by=changed_by_user,
        rule_action=qa_action_enum.NAME_SPLIT_REVIEW_NEEDED.value,
    )


def populate_split_officer_names(
    df_input: pd.DataFrame,
    changed_by_user: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """
    Populates PrincipalOfficerGivenName and PrincipalOfficerFamilyName
    based on the existing PrincipalOfficerName field.
    """
    df_processed = df_input.copy()
    print("Populating split officer names...")

    required_name_cols = ["PrincipalOfficerGivenName", "PrincipalOfficerFamilyName"]
    for col in required_name_cols:
        if col not in df_processed.columns:
            print(
                f"Warning: Column '{col}' not found. Adding it with empty strings. "
                "This should ideally be handled by a schema management script."
            )
            df_processed[col] = ""

    num_successful_splits = 0
    num_review_needed = 0

    for index, row in df_processed.iterrows():
        record_id = str(row["RecordID"])
        original_full_name_raw = row.get("PrincipalOfficerName")
        old_given_name = row.get("PrincipalOfficerGivenName", "")
        old_family_name = row.get("PrincipalOfficerFamilyName", "")

        given_name_to_set = old_given_name
        family_name_to_set = old_family_name
        processed_successfully = False

        # Check for NA or non-string types first
        is_na_check = pd.isna(original_full_name_raw)
        is_not_str_check = not isinstance(original_full_name_raw, str)
        if is_na_check or is_not_str_check:
            name_to_process = None
        else:
            name_to_process = original_full_name_raw.strip()

        if name_to_process:
            parts = name_to_process.split()
            if len(parts) == 2:
                given_name_to_set = parts[0].strip()
                family_name_to_set = parts[1].strip()

                if given_name_to_set != old_given_name:
                    log_change_func(
                        record_id=record_id,
                        column_changed="PrincipalOfficerGivenName",
                        old_value=old_given_name,
                        new_value=given_name_to_set,
                        feedback_source="System_NameSplitRule",
                        notes=(
                            "Populated GivenName from PrincipalOfficerName: "
                            f"'{name_to_process}'"
                        ),
                        changed_by=changed_by_user,
                        rule_action=qa_action_enum.NAME_SPLIT_SUCCESS.value,
                    )
                    df_processed.loc[index, "PrincipalOfficerGivenName"] = (
                        given_name_to_set
                    )

                if family_name_to_set != old_family_name:
                    log_change_func(
                        record_id=record_id,
                        column_changed="PrincipalOfficerFamilyName",
                        old_value=old_family_name,
                        new_value=family_name_to_set,
                        feedback_source="System_NameSplitRule",
                        notes=(
                            "Populated FamilyName from PrincipalOfficerName: "
                            f"'{name_to_process}'"
                        ),
                        changed_by=changed_by_user,
                        rule_action=qa_action_enum.NAME_SPLIT_SUCCESS.value,
                    )
                    df_processed.loc[index, "PrincipalOfficerFamilyName"] = (
                        family_name_to_set
                    )
                processed_successfully = True
                num_successful_splits += 1
            else:
                # Name did not split into exactly two parts
                _log_name_split_issue(
                    log_change_func,
                    record_id,
                    original_full_name_raw,
                    changed_by_user,
                    qa_action_enum,
                    "did not split into two parts",
                )
                num_review_needed += 1
        else:
            # Name was None, NA, empty, or non-string initially
            _log_name_split_issue(
                log_change_func,
                record_id,
                original_full_name_raw,
                changed_by_user,
                qa_action_enum,
                "is effectively empty or invalid",
            )
            num_review_needed += 1

        # Ensure original values are retained if not processed successfully
        if not processed_successfully:
            df_processed.loc[index, "PrincipalOfficerGivenName"] = old_given_name
            df_processed.loc[index, "PrincipalOfficerFamilyName"] = old_family_name

    print(
        f"Name splitting complete. Successful splits: {num_successful_splits}, "
        f"Needs review: {num_review_needed}"
    )
    return df_processed


def populate_officer_name_parts(  # noqa: C901
    df_input: pd.DataFrame,
    changed_by_user: str,
    log_change_func: callable,
    qa_action_enum: type[Enum],
) -> pd.DataFrame:
    """
    Populates detailed name parts from PrincipalOfficerName.

    Populates:
    - PrincipalOfficerFullName (copy of original)
    - PrincipalOfficerGivenName
    - PrincipalOfficerMiddleNameOrInitial
    - PrincipalOfficerFamilyName
    - PrincipalOfficerSuffix

    Args:
        df_input: Input DataFrame to process
        changed_by_user: String identifying who made the changes
        log_change_func: Function to call for logging changes
        qa_action_enum: The QAAction enum class for action types

    Returns:
        Processed DataFrame with populated name fields
    """
    try:
        from nameparser import HumanName
    except ImportError:
        print(
            "Error: nameparser library not installed. "
            "Install with: pip install nameparser"
        )
        return df_input

    df_processed = df_input.copy()
    print("Populating officer name parts...")

    # Ensure all required columns exist
    required_name_cols = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]

    for col in required_name_cols:
        if col not in df_processed.columns:
            print(f"Warning: Column '{col}' not found. Adding it with empty strings.")
            df_processed[col] = ""

    num_successful_parses = 0
    num_review_needed = 0

    for index, row in df_processed.iterrows():
        record_id = str(row["RecordID"])
        original_full_name = row.get("PrincipalOfficerName")

        # Step 1: Always populate PrincipalOfficerFullName
        old_full_name_value = row.get("PrincipalOfficerFullName", "")

        # Check if original_full_name is a scalar value that pd.notna can handle
        is_scalar = not isinstance(original_full_name, list | dict | set | tuple)

        if is_scalar and pd.notna(original_full_name):
            df_processed.loc[index, "PrincipalOfficerFullName"] = original_full_name

            # Log the copy action
            if str(original_full_name) != str(old_full_name_value):
                log_change_func(
                    record_id=record_id,
                    column_changed="PrincipalOfficerFullName",
                    old_value=old_full_name_value,
                    new_value=original_full_name,
                    feedback_source="System_NameParseRule",
                    notes="Copied from PrincipalOfficerName",
                    changed_by=changed_by_user,
                    rule_action=qa_action_enum.NAME_PARSE_SUCCESS.value,
                )

        # Step 2: Attempt to parse the name
        if (
            is_scalar
            and pd.notna(original_full_name)
            and isinstance(original_full_name, str)
            and original_full_name.strip()
        ):
            try:
                # Parse the name using nameparser
                parsed_name = HumanName(original_full_name.strip())

                # Map parsed components to our fields
                name_parts = {
                    "PrincipalOfficerGivenName": parsed_name.first,
                    "PrincipalOfficerMiddleNameOrInitial": parsed_name.middle,
                    "PrincipalOfficerFamilyName": parsed_name.last,
                    "PrincipalOfficerSuffix": parsed_name.suffix,
                }

                # Check if we have meaningful parse results
                # (at least first and last name should be present)
                if parsed_name.first and parsed_name.last:
                    # Successfully parsed - update fields
                    for field_name, parsed_value in name_parts.items():
                        old_value = row.get(field_name, "")
                        new_value = parsed_value.strip() if parsed_value else ""

                        if new_value and new_value != old_value:
                            df_processed.loc[index, field_name] = new_value

                            # Log each field update
                            log_change_func(
                                record_id=record_id,
                                column_changed=field_name,
                                old_value=old_value,
                                new_value=new_value,
                                feedback_source="System_NameParseRule",
                                notes=f"Parsed from: '{original_full_name}'",
                                changed_by=changed_by_user,
                                rule_action=qa_action_enum.NAME_PARSE_SUCCESS.value,
                            )

                    num_successful_parses += 1

                else:
                    # Parse didn't yield usable results
                    log_change_func(
                        record_id=record_id,
                        column_changed="PrincipalOfficerName_ParseReview",
                        old_value=original_full_name,
                        new_value="N/A",
                        feedback_source="System_NameParseRule",
                        notes=(
                            f"PrincipalOfficerName '{original_full_name}' could not be "
                            "confidently parsed into Given/Middle/Family/Suffix parts. "
                            "Manual review required."
                        ),
                        changed_by=changed_by_user,
                        rule_action=qa_action_enum.NAME_PARSE_REVIEW_NEEDED.value,
                    )
                    num_review_needed += 1

            except Exception as e:
                # Error during parsing
                log_change_func(
                    record_id=record_id,
                    column_changed="PrincipalOfficerName_ParseReview",
                    old_value=original_full_name,
                    new_value="N/A",
                    feedback_source="System_NameParseRule",
                    notes=(
                        f"Error parsing name '{original_full_name}': {str(e)}. "
                        "Manual review needed."
                    ),
                    changed_by=changed_by_user,
                    rule_action=qa_action_enum.NAME_PARSE_REVIEW_NEEDED.value,
                )
                num_review_needed += 1

        else:
            # Name is empty, None, or not a string
            if not is_scalar:
                display_value = f"Invalid type: {type(original_full_name).__name__}"
            elif pd.notna(original_full_name):
                display_value = original_full_name
            else:
                display_value = "None/Empty"

            log_change_func(
                record_id=record_id,
                column_changed="PrincipalOfficerName_ParseReview",
                old_value=display_value,
                new_value="N/A",
                feedback_source="System_NameParseRule",
                notes=(
                    f"PrincipalOfficerName is empty or invalid ({display_value}). "
                    "Cannot parse into name parts."
                ),
                changed_by=changed_by_user,
                rule_action=qa_action_enum.NAME_PARSE_REVIEW_NEEDED.value,
            )
            num_review_needed += 1

    print(
        f"Name parsing complete. Successful parses: {num_successful_parses}, "
        f"Needs review: {num_review_needed}"
    )

    return df_processed


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process a golden dataset CSV with QA edits from another CSV."
    )
    parser.add_argument(
        "--golden", required=True, help="Path to the input golden dataset CSV."
    )
    parser.add_argument("--qa", required=True, help="Path to the input QA edits CSV.")
    parser.add_argument(
        "--out", required=True, help="Path to save the processed golden dataset CSV."
    )
    parser.add_argument(
        "--changelog", required=True, help="Path to save the changelog CSV."
    )
    parser.add_argument(
        "--changed-by",
        required=True,
        help="String to populate the 'changed_by' field in the changelog.",
    )
    arg_help_drop_filter = (  # Reformatted help string
        "If True, drop a hypothetical column named "
        "'_RECORD_FILTERED_OUT_FLAG' before saving."
    )
    parser.add_argument(
        "--drop-filter-col",
        action="store_true",
        help=arg_help_drop_filter,  # Use reformatted help string
    )
    return parser.parse_args()


def _load_dataframes(
    golden_path: str, qa_path: str
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Load golden and QA dataframes."""
    df_golden, df_qa = None, None
    try:
        print(
            "Attempting to load golden dataset with engine='python' "
            f"from {golden_path}..."
        )
        df_golden = pd.read_csv(golden_path, dtype=str, engine="python")
        print("Golden dataset loaded successfully.")
    except Exception as e:
        print(f"Error loading golden dataset ({golden_path}): {e}")
        return None, None

    try:
        print(f"Attempting to load QA dataset with engine='python' from {qa_path}...")
        # Try to read just the header to see if it's our dummy file
        header_df = pd.read_csv(qa_path, dtype=str, engine="python", nrows=0)
        # Read the full file to count rows
        row_count_df = pd.read_csv(qa_path, dtype=str, engine="python", header=None)

        if len(row_count_df) == 1 and list(header_df.columns) == [
            "Row(s)",
            "Column",
            "feedback",
        ]:
            # Dummy file: header only. Create empty DataFrame.
            print("QA file is header-only dummy. Creating empty DataFrame.")
            df_qa = pd.DataFrame(columns=["Row(s)", "Column", "feedback"]).astype(str)
        else:
            # Otherwise, load normally
            df_qa = pd.read_csv(qa_path, dtype=str, engine="python")

        print("QA dataset loaded successfully.")
    except Exception as e:
        print(f"Error loading QA dataset ({qa_path}): {e}")
        return df_golden, None
    return df_golden, df_qa


def _apply_transformations(
    df_golden: pd.DataFrame,
    df_qa: pd.DataFrame,
    changed_by: str,
    qa_filename: str,
) -> pd.DataFrame:
    """Apply global transformations and QA edits."""
    global changelog_entries
    changelog_entries = []  # Reset changelog for this processing run

    print("Applying global deduplication rules...")
    df_transformed = apply_global_deduplication(
        df_golden,
        changed_by,
        log_change,
        QAAction,
    )

    print("Applying global character fixing rules...")
    df_transformed = apply_global_character_fixing(
        df_transformed,
        changed_by,
        log_change,
        QAAction,
    )

    print("Populating detailed officer name parts...")
    df_transformed = populate_officer_name_parts(
        df_transformed, changed_by, log_change, QAAction
    )

    print(f"Applying QA edits from {qa_filename}...")
    df_transformed = apply_qa_edits(df_transformed, df_qa, changed_by, qa_filename)
    return df_transformed


def _handle_filter_column(df: pd.DataFrame, drop_flag: bool) -> pd.DataFrame:
    """Handle dropping the filter column if specified."""
    if drop_flag:
        hypothetical_main_filter_column = "_RECORD_FILTERED_OUT_FLAG"
        if hypothetical_main_filter_column in df.columns:
            print(f"Dropping filter column: {hypothetical_main_filter_column}")
            return df.drop(columns=[hypothetical_main_filter_column])
        else:
            msg = (
                f"Note: --drop-filter-col specified, but column "
                f"'{hypothetical_main_filter_column}' not found in the final DataFrame."
            )
            print(msg)
    return df


def _save_outputs(
    df_processed: pd.DataFrame, out_path: str, changelog_path: str
) -> bool:
    """Save processed dataframe and changelog to CSV files."""
    try:
        df_processed.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Processed dataset saved to: {out_path}")
    except Exception as e:
        print(f"Error saving processed dataset: {e}")
        return False

    df_changelog = pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS)
    try:
        df_changelog.to_csv(changelog_path, index=False, encoding="utf-8-sig")
        print(f"Changelog saved to: {changelog_path}")
    except Exception as e:
        print(f"Error saving changelog: {e}")
        return False
    return True


def _perform_integrity_checks(
    pre_load_count: int,
    post_edit_count: int,
    post_filter_count: int,
    df_changelog: pd.DataFrame,
):
    """Perform and print results of integrity checks."""
    print("\n--- Integrity Checks ---")
    print(f"Pre-load golden dataset count: {pre_load_count}")
    print(f"Post-edit golden dataset count: {post_edit_count}")
    print(f"Post-filter final dataset count: {post_filter_count}")

    try:
        assert (
            post_edit_count >= post_filter_count
        ), "Assertion Failed: Post-edit count cannot be less than post-filter count."

        filtered_out_log_count = 0
        if not df_changelog.empty:
            filtered_out_log_count = len(
                df_changelog[df_changelog["column_changed"] == "_RECORD_FILTERED_OUT"]
            )

        msg_filtered_count = (
            f"Number of '_RECORD_FILTERED_OUT' entries in changelog: "
            f"{filtered_out_log_count}"
        )
        print(msg_filtered_count)

        assert (post_edit_count - post_filter_count) == filtered_out_log_count, (
            f"Assertion Failed: Mismatch between rows removed from dataset "
            f"({post_edit_count - post_filter_count}) and '_RECORD_FILTERED_OUT' "
            f"changelog entries ({filtered_out_log_count})."
        )

        print("Integrity checks passed successfully.")
    except AssertionError as e:
        print(f"Integrity check FAILED: {e}")
    except Exception as e:
        print(f"An error occurred during integrity checks: {e}")


def main():
    """
    Main function to process the golden dataset with QA edits.
    """
    args = _parse_args()

    print("Starting golden dataset processing...")
    print(f"Golden dataset: {args.golden}")
    print(f"QA edits: {args.qa}")
    print(f"Output dataset: {args.out}")
    print(f"Changelog: {args.changelog}")
    print(f"Changed by: {args.changed_by}")

    df_golden, df_qa = _load_dataframes(args.golden, args.qa)

    if df_golden is None or df_qa is None:
        print("Exiting due to errors loading dataframes.")
        return

    pre_load_count = len(df_golden)
    print(f"Initial records in golden dataset: {pre_load_count}")

    df_edited = _apply_transformations(df_golden, df_qa, args.changed_by, args.qa)
    post_edit_count = len(df_edited)

    df_final = _handle_filter_column(df_edited.copy(), args.drop_filter_col)
    post_filter_count = len(df_final)

    if not _save_outputs(df_final, args.out, args.changelog):
        print("Exiting due to errors saving output files.")
        return

    # For integrity checks, create df_changelog from the global list
    df_changelog_for_checks = pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS)
    _perform_integrity_checks(
        pre_load_count, post_edit_count, post_filter_count, df_changelog_for_checks
    )

    print("\nGolden dataset processing complete.")


if __name__ == "__main__":
    main()
