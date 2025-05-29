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


class QAAction(Enum):
    DIRECT_SET = "direct_set"
    CHAR_FIX = "char_fix"
    BLANK_VALUE = "blank_value"
    DEDUP_SEMICOLON = "dedup_semicolon"
    POLICY_QUERY = "policy_query"
    DATA_ENRICH = "data_enrich"
    NOT_FOUND = "not_found"


@dataclass
class QAEditRule:
    pattern: re.Pattern
    action: QAAction
    value_parser: typing.Callable | None


CHANGELOG_COLUMNS = [
    "timestamp",
    "record_id",
    "column_changed",
    "old_value",
    "new_value",
    "feedback_source",
    "notes",
    "changed_by",
]

# Illustrative example rules
RULES = {
    # Example: "Set Name to NYC311"
    r"Set (?P<column>\w+) to (?P<value>.+)": QAAction.DIRECT_SET,
    # Example: "Fix special characters in Description"
    r"Fix special characters(?: in (?P<column>\w+))?": QAAction.CHAR_FIX,
    # Example: "Remove value of PrincipalOfficerContactURL"
    r"Remove value of (?P<column>\w+)": QAAction.BLANK_VALUE,
    # Example: "What is the logic of adding NYC..."
    r"What is the logic.*": QAAction.POLICY_QUERY,
    # Example: "Repeated values error" - could be a policy query or
    # a specific fix depending on context
    r"Repeated values error": QAAction.POLICY_QUERY,  # Or a more specific action
    # if defined
    # Example: "Consider elimination of Notes field..."
    r"Consider elimination of (?P<column>\w+) field.*": QAAction.POLICY_QUERY,
    # New policy query patterns
    (
        r"(What is the logic|What's the process|How should we handle|Is this correct)"
    ): QAAction.POLICY_QUERY,
    (
        r"(Consider elimination|Consider merging|Should we delete|"
        r"Review for removal|Discuss)"
    ): QAAction.POLICY_QUERY,
}


def log_change(
    record_id: str,
    column_changed: str,
    old_value: typing.Any,
    new_value: typing.Any,
    feedback_source: str,
    notes: str | None,
    changed_by: str,
):
    """Logs a change to the changelog_entries list."""
    global changelog_entries
    entry = {
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "column_changed": column_changed,
        "old_value": old_value,
        "new_value": new_value,
        "feedback_source": feedback_source,
        "notes": notes,
        "changed_by": changed_by,
    }
    changelog_entries.append(entry)
    # print(f"Change logged: {entry}") # For debugging


def detect_rule(feedback: str) -> QAAction:
    for pattern, action in RULES.items():
        if re.search(pattern, feedback, re.IGNORECASE):
            return action
    return QAAction.NOT_FOUND


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
    new_value = ""
    log_change(
        record_id,
        column_to_edit,
        old_value,
        new_value,
        feedback_source,
        notes,
        changed_by,
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
        # Strip whitespace from each item, filter out empty strings, then deduplicate
        stripped_items = [item.strip() for item in items]
        unique_items = list(
            dict.fromkeys([item for item in stripped_items if item])
        )  # Preserves order of first appearance

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
    # This handler's signature might also need adjustment based on how it's called.
    # For now, keeping it distinct.
    log_change(
        record_id=record_id,
        column_changed=column_to_edit if column_to_edit else "Policy Question",
        old_value="N/A",
        new_value="N/A",
        feedback_source=feedback_source,
        notes=original_feedback,  # Use original_feedback as notes
        changed_by=changed_by,
    )
    # print(
    # f"Called handle_policy_query for column '{column_to_edit}' "
    # f"with feedback: {original_feedback}"
    # )
    # Potentially log this interaction as well, though it's not a direct data edit.
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
    pass


def handle_not_found(
    row_series: pd.Series,
    original_feedback: str,
    record_id: str | None,
    feedback_source: str | None,
    changed_by: str | None,
    notes: str | None = None,
):
    print(f"Called handle_not_found for feedback: {original_feedback}")
    pass


ACTION_HANDLERS = {
    QAAction.DIRECT_SET: handle_direct_set,
    QAAction.CHAR_FIX: handle_char_fix,
    QAAction.BLANK_VALUE: handle_blank_value,
    QAAction.DEDUP_SEMICOLON: handle_dedup_semicolon,
    QAAction.POLICY_QUERY: handle_policy_query,  # Stub, signature might change
    QAAction.DATA_ENRICH: handle_data_enrich,  # Stub, signature might change
    QAAction.NOT_FOUND: handle_not_found,  # Stub, signature might change
}


def apply_qa_edits(df):
    """
    Apply QA edits to the DataFrame.
    (This function is a placeholder and needs to be implemented)
    """
    # TODO: Implement QA edits
    return df


def main():
    """
    Main function to process the golden dataset.
    (This function is a placeholder and needs to be implemented)
    """
    # TODO: Implement main processing logic
    print("Processing golden dataset...")

    # Example usage (replace with actual logic):
    # parser = argparse.ArgumentParser(description="Process the golden dataset.")
    # parser.add_argument("input_file", help="Path to the input golden dataset CSV.")
    # parser.add_argument("output_file", help="Path to save the processed dataset CSV.")
    # args = parser.parse_args()

    # print(f"Input file: {args.input_file}")
    # print(f"Output file: {args.output_file}")

    # df = pd.read_csv(args.input_file)
    # df_processed = apply_qa_edits(df.copy())
    # df_processed.to_csv(args.output_file, index=False)

    print("Golden dataset processing complete.")


if __name__ == "__main__":
    main()
