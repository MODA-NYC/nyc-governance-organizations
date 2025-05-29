import re
import typing
from dataclasses import dataclass
from enum import Enum


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
}


def detect_rule(feedback: str) -> QAAction:
    for pattern, action in RULES.items():
        if re.search(pattern, feedback, re.IGNORECASE):
            return action
    return QAAction.NOT_FOUND


# Stub handler functions
def handle_direct_set(row, column_to_edit, new_value=None, original_feedback=None):
    print(
        f"Called handle_direct_set for column '{column_to_edit}' "
        f"with value '{new_value}'"
    )
    pass


def handle_char_fix(row, column_to_edit, new_value=None, original_feedback=None):
    print(f"Called handle_char_fix for column '{column_to_edit}'")
    pass


def handle_blank_value(row, column_to_edit, new_value=None, original_feedback=None):
    print(f"Called handle_blank_value for column '{column_to_edit}'")
    pass


def handle_dedup_semicolon(row, column_to_edit, new_value=None, original_feedback=None):
    print(f"Called handle_dedup_semicolon for column '{column_to_edit}'")
    pass


def handle_policy_query(row, column_to_edit, new_value=None, original_feedback=None):
    print(
        f"Called handle_policy_query for column '{column_to_edit}' "
        f"with feedback: {original_feedback}"
    )
    pass


def handle_data_enrich(row, column_to_edit, new_value=None, original_feedback=None):
    print(f"Called handle_data_enrich for column '{column_to_edit}'")
    pass


def handle_not_found(row, column_to_edit, new_value=None, original_feedback=None):
    print(f"Called handle_not_found for feedback: {original_feedback}")
    pass


ACTION_HANDLERS = {
    QAAction.DIRECT_SET: handle_direct_set,
    QAAction.CHAR_FIX: handle_char_fix,
    QAAction.BLANK_VALUE: handle_blank_value,
    QAAction.DEDUP_SEMICOLON: handle_dedup_semicolon,
    QAAction.POLICY_QUERY: handle_policy_query,
    QAAction.DATA_ENRICH: handle_data_enrich,
    QAAction.NOT_FOUND: handle_not_found,
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
