import argparse
import pathlib
import re
import typing
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
    r"Fix special characters(?: in (?P<column>\w+))?": QAAction.CHAR_FIX,
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
    # Example: "Repeated values error" - could be a policy query
    r"Repeated values error": QAAction.POLICY_QUERY,
    # Example: "Consider elimination of Notes field..."
    r"Consider elimination of (?P<column>\w+) field.*": QAAction.POLICY_QUERY,
    # Enhanced General Policy Query Patterns
    r"(What is the logic|What's the process|Why is|Is this an error|"
    r"How should we handle|Is this correct|Can we find|"
    r"Should we be able)": QAAction.POLICY_QUERY,
    r"(Consider elimination|Consider merging|Should we delete|"
    r"Review for removal|Discuss|Mistakenly populated field|"
    r"appears to be an error|is not an acronym)": QAAction.POLICY_QUERY,
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
        otherwise (QAAction.NOT_FOUND, None).
    """
    for pattern_str, action in RULES.items():
        match = re.search(pattern_str, feedback, re.IGNORECASE)
        if match:
            return action, match
    return QAAction.NOT_FOUND, None


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

    handler_args["column_to_edit"] = final_column_to_edit
    handler_args["new_value"] = parsed_value.strip()
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
    changed_by_user: str,
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
            changed_by_user,
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
            changed_by_user,
            action_handlers,
            rules_dict,
            qa_action_enum,
        )
        df_modified.loc[golden_row_index] = modified_row_series


def apply_qa_edits(
    df_golden: pd.DataFrame,
    df_qa: pd.DataFrame,
    changed_by_user: str,
    qa_filename: str,
) -> pd.DataFrame:
    """Apply QA edits from the QA DataFrame to the Golden DataFrame."""
    df_modified = df_golden.copy()
    feedback_source_name = pathlib.Path(qa_filename).name

    expected_qa_cols = ["Row(s)", "Column", "feedback"]
    for col in expected_qa_cols:
        if col not in df_qa.columns:
            raise ValueError(f"QA DataFrame is missing expected column: {col}")

    # Clean up encoding issues in the feedback column using ftfy
    df_qa["feedback"] = df_qa["feedback"].apply(
        lambda x: ftfy.fix_text(x) if pd.notna(x) else x
    )

    for _, qa_row in df_qa.iterrows():
        _process_single_qa_row(
            qa_row,
            df_modified,
            feedback_source_name,
            changed_by_user,
            ACTION_HANDLERS,
            RULES,
            QAAction,
        )

    return df_modified


def main():
    """
    Main function to process the golden dataset with QA edits.
    """
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
    args = parser.parse_args()

    print("Starting golden dataset processing...")
    print(f"Golden dataset: {args.golden}")
    print(f"QA edits: {args.qa}")
    print(f"Output dataset: {args.out}")
    print(f"Changelog: {args.changelog}")
    print(f"Changed by: {args.changed_by}")

    try:
        df_golden = pd.read_csv(args.golden, dtype=str)
        df_qa = pd.read_csv(args.qa, dtype=str)
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e.filename}")
        return
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return

    pre_load_count = len(df_golden)
    print(f"Initial records in golden dataset: {pre_load_count}")

    global changelog_entries
    changelog_entries = []

    df_edited = apply_qa_edits(df_golden, df_qa, args.changed_by, args.qa)
    post_edit_count = len(df_edited)

    df_final = df_edited.copy()

    if args.drop_filter_col:
        hypothetical_main_filter_column = "_RECORD_FILTERED_OUT_FLAG"
        if hypothetical_main_filter_column in df_final.columns:
            print(f"Dropping filter column: {hypothetical_main_filter_column}")
            df_final = df_final.drop(columns=[hypothetical_main_filter_column])
        else:
            msg = (  # Reformatted print message
                f"Note: --drop-filter-col specified, but column "
                f"'{hypothetical_main_filter_column}' not found in the final DataFrame."
            )
            print(msg)

    post_filter_count = len(df_final)

    try:
        df_final.to_csv(args.out, index=False)
        print(f"Processed dataset saved to: {args.out}")
    except Exception as e:
        print(f"Error saving processed dataset: {e}")
        return

    df_changelog = pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS)
    try:
        df_changelog.to_csv(args.changelog, index=False)
        print(f"Changelog saved to: {args.changelog}")
    except Exception as e:
        print(f"Error saving changelog: {e}")
        return

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

        msg_filtered_count = (  # Reformatted print message
            f"Number of '_RECORD_FILTERED_OUT' entries in changelog: "
            f"{filtered_out_log_count}"
        )
        print(msg_filtered_count)

        assert (
            post_edit_count - post_filter_count
        ) == filtered_out_log_count, (  # Reformatted assertion message
            f"Assertion Failed: Mismatch between rows removed from dataset "
            f"({post_edit_count - post_filter_count}) and '_RECORD_FILTERED_OUT' "
            f"changelog entries ({filtered_out_log_count})."
        )

        print("Integrity checks passed successfully.")
    except AssertionError as e:
        print(f"Integrity check FAILED: {e}")
    except Exception as e:
        print(f"An error occurred during integrity checks: {e}")

    print("\nGolden dataset processing complete.")


if __name__ == "__main__":
    main()
