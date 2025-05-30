import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import process_golden_dataset


# Fixture to clear changelog_entries before each test
@pytest.fixture(autouse=True)
def clear_changelog(monkeypatch):
    # Create a new empty list for changelog_entries for each test
    # This ensures test isolation.
    new_changelog = []
    monkeypatch.setattr(process_golden_dataset, "changelog_entries", new_changelog)
    # Reset the changelog counter for each test
    monkeypatch.setattr(process_golden_dataset, "changelog_id_counter", 0)
    return new_changelog  # Return it so tests can inspect it if needed


def test_changelog_columns_definition():
    assert process_golden_dataset.CHANGELOG_COLUMNS == [
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


def test_name_replacement(clear_changelog):
    # Mock DataFrame
    data = {"record_id": ["NYC_GOID_001"], "Name": ["Old Name"]}
    row_series = pd.Series(data, index=["Name"])  # Simulate a row

    # Simulate a row by taking the first (and only) row of a DataFrame
    df = pd.DataFrame(data)
    row_series = df.iloc[
        0
    ].copy()  # Important to copy to avoid modifying the original tiny df directly

    record_id = "NYC_GOID_001"
    column_to_edit = "Name"
    new_name = "NYC311"
    feedback_source = "Test"
    changed_by = "Tester"

    # Apply the handler
    modified_row = process_golden_dataset.handle_direct_set(
        row_series, column_to_edit, new_name, record_id, feedback_source, changed_by
    )

    # Assert DataFrame update
    assert modified_row[column_to_edit] == new_name

    # Assert log_change call
    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["ChangeID"] == 1  # First entry should have ID 1
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["old_value"] == "Old Name"
    assert log_entry["new_value"] == new_name
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["changed_by"] == changed_by
    assert log_entry["RuleAction"] == process_golden_dataset.QAAction.DIRECT_SET.value


def test_blank_out_value(clear_changelog):
    data = {"record_id": ["NYC_GOID_002"], "Description": ["Initial Description"]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_002"
    column_to_edit = "Description"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_blank_value(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == ""

    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["old_value"] == "Initial Description"
    assert log_entry["new_value"] == ""
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["changed_by"] == changed_by


def test_char_fix_strip_whitespace(clear_changelog):
    original_value = "  Padded Name  "
    expected_value = "Padded Name"
    data = {"record_id": ["NYC_GOID_003"], "Name": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_003"
    column_to_edit = "Name"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_char_fix(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == expected_value
    assert len(clear_changelog) == 1  # Logged because value changed
    log_entry = clear_changelog[0]
    assert log_entry["old_value"] == original_value
    assert log_entry["new_value"] == expected_value


def test_char_fix_no_change(clear_changelog):
    original_value = "Clean Name"
    data = {"record_id": ["NYC_GOID_004"], "Name": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_004"
    column_to_edit = "Name"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_char_fix(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == original_value
    assert len(clear_changelog) == 0  # Not logged because value did not change


def test_deduplicate_semicolon_list(clear_changelog):
    original_value = "NameA; NameB ; NameA ; NameC;NameB;  ; NameD "  # Extra spaces
    expected_value = (
        "NameA;NameB;NameC;NameD"  # Order preserved, spaces stripped, empty removed
    )

    data = {"record_id": ["NYC_GOID_005"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_005"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == expected_value

    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["old_value"] == original_value
    assert log_entry["new_value"] == expected_value


def test_deduplicate_semicolon_list_no_duplicates(clear_changelog):
    original_value = "NameA;NameB;NameC"
    data = {"record_id": ["NYC_GOID_006"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_006"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == original_value
    assert (
        len(clear_changelog) == 0
    )  # Not logged as value didn't change after processing


def test_deduplicate_semicolon_list_empty_input(clear_changelog):
    original_value = ""
    data = {"record_id": ["NYC_GOID_007"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_007"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == ""  # Should remain empty
    assert len(clear_changelog) == 0


def test_deduplicate_semicolon_list_single_item(clear_changelog):
    original_value = "NameA"
    data = {"record_id": ["NYC_GOID_008"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_008"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == "NameA"
    assert len(clear_changelog) == 0


def test_deduplicate_semicolon_list_with_only_semicolons(clear_changelog):
    original_value = ";;;"
    expected_value = ""  # Empty items are removed
    data = {"record_id": ["NYC_GOID_009"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_009"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == expected_value
    assert len(clear_changelog) == 1  # Logged as value changed
    log_entry = clear_changelog[0]
    assert log_entry["old_value"] == original_value
    assert log_entry["new_value"] == expected_value


def test_deduplicate_semicolon_non_string_input(clear_changelog):
    original_value = 123  # Not a string
    data = {"record_id": ["NYC_GOID_010"], "AlternateNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_010"
    column_to_edit = "AlternateNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == original_value  # Should not change
    assert len(clear_changelog) == 0  # No logging as no change


def test_policy_query_logs_and_does_not_mutate(clear_changelog):
    # Mock DataFrame
    data = {
        "record_id": ["NYC_GOID_POLICY_001"],
        "Name": ["Test Name"],
        "Notes": ["Initial notes content"],
    }
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()
    original_row_copy = row_series.copy()  # Capture original state

    # Example parameters
    record_id = "NYC_GOID_POLICY_001"
    column_to_edit = "Notes"  # Can be a specific column or None
    original_feedback = "Consider elimination of Notes field."
    feedback_source = "QA Team"
    changed_by = "PolicyBot"

    # Call the handle_policy_query function
    modified_row = process_golden_dataset.handle_policy_query(
        row_series,
        column_to_edit,
        original_feedback,
        record_id,
        feedback_source,
        changed_by,
        notes=original_feedback,  # Pass original_feedback as notes for consistency
    )

    # Assert Data Integrity: DataFrame row should not be changed
    assert original_row_copy.equals(
        modified_row
    ), "DataFrame row was modified by handle_policy_query"

    # Assert Changelog Entry
    assert (
        len(clear_changelog) == 1
    ), "log_change was not called or called multiple times"
    log_entry = clear_changelog[0]

    assert log_entry["ChangeID"] == 1  # First entry should have ID 1
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == (column_to_edit or "Policy Question")
    assert log_entry["old_value"] == "N/A"
    assert log_entry["new_value"] == "N/A"
    assert (
        log_entry["notes"] == original_feedback
    ), "Logged notes do not match original feedback"
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["changed_by"] == changed_by
    assert log_entry["RuleAction"] == process_golden_dataset.QAAction.POLICY_QUERY.value


# Tests for REMOVE_ACTING_PREFIX
@pytest.mark.parametrize(
    (
        "record_id, column, initial_title, expected_title, feedback, "
        "log_expected, expected_notes_substring"
    ),
    [
        (
            "ID001",
            "Title",
            "Acting Director",
            "Director",
            "Confirmed, so no longer Acting",
            True,
            (
                "Removed 'Acting' prefix from 'Acting Director' to get 'Director'. "
                "Original feedback: 'Confirmed, so no longer Acting'"
            ),
        ),
        (
            "ID002",
            "Title",
            "ACTING Commissioner",
            "Commissioner",
            "no longer Acting",
            True,
            (
                "Removed 'Acting' prefix from 'ACTING Commissioner' "
                "to get 'Commissioner'. Original feedback: 'no longer Acting'"
            ),
        ),
        (
            "ID003",
            "Title",
            "Director",
            "Director",
            "Confirmed, no longer Acting",
            True,  # Logged because rule triggered but no change
            (
                "Rule 'Confirmed, no longer Acting' triggered, but no 'Acting ' "
                "prefix found/changed in 'Director'."
            ),
        ),
        (
            "ID004",
            "Title",
            "Acting",  # This specific case
            "",
            "no longer Acting",
            True,
            (
                "Changed 'Acting' to empty string based on 'no longer Acting' "
                "feedback: 'no longer Acting'"
            ),
        ),
        (
            "ID005",
            "Title",
            "Acting  ",  # With extra spaces, also becomes empty
            "",
            "no longer Acting",
            True,
            (
                "Changed 'Acting  ' to empty string based on 'no longer Acting' "
                "feedback: 'no longer Acting'"
            ),
        ),
        (
            "ID006",
            "Title",
            None,  # Non-string value
            None,
            "no longer Acting",
            True,  # Logged because rule triggered but no change
            ("Rule 'no longer Acting' triggered on None value. No action taken."),
        ),
        (
            "ID007",
            "Title",
            12345,  # Non-string value
            12345,
            "no longer Acting",
            True,  # Logged because rule triggered but no change
            (
                "Rule 'no longer Acting' triggered on non-string value '12345'. "
                "No action taken."
            ),
        ),
        (
            "ID008",
            "Title",
            "Director (Acting)",  # Suffix, should not be removed by this rule
            "Director (Acting)",
            "no longer Acting",
            True,  # Logged because rule triggered but no change
            (
                "Rule 'no longer Acting' triggered, but no 'Acting ' prefix "
                "found/changed in 'Director (Acting)'."
            ),
        ),
    ],
)
def test_remove_acting_prefix(  # noqa: C901
    clear_changelog,
    record_id,
    column,
    initial_title,
    expected_title,
    feedback,
    log_expected,
    expected_notes_substring,
):
    golden_data = pd.DataFrame([{"RecordID": record_id, column: initial_title}])
    qa_data = pd.DataFrame(
        [{"Row(s)": record_id, "Column": column, "feedback": feedback}]
    )
    changed_by = "test_user"
    qa_filename = "test_qa.csv"

    processed_df = process_golden_dataset.apply_qa_edits(
        golden_data, qa_data, changed_by, qa_filename
    )
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)

    expected_data = pd.DataFrame([{"RecordID": record_id, column: expected_title}])

    # Adjust dtypes for accurate comparison if None or numeric values are involved
    if initial_title is None and expected_title is None:
        expected_data[column] = expected_data[column].astype(object)
        if column in processed_df.columns:
            processed_df[column] = processed_df[column].astype(object)
    elif isinstance(initial_title, int | float) and initial_title == expected_title:
        # If original and expected are same numeric, processed should also be
        # numeric or comparable
        if column in processed_df.columns and pd.api.types.is_numeric_dtype(
            processed_df[column]
        ):
            pass  # types are consistent
        elif column in processed_df.columns:  # if processed became string
            expected_data[column] = expected_data[column].astype(str)
    else:
        # Default to string comparison for most other cases unless specific
        # handling needed
        if expected_title is not None:
            expected_data[column] = str(
                expected_title
            )  # Ensure expected value is string for comparison if not None
        # Ensure processed_df column is string if it exists and isn't None for
        # fair comparison
        # This is tricky because apply_qa_edits might change type to string by
        # default
        if column in processed_df.columns and processed_df[column].iloc[0] is not None:
            processed_df[column] = processed_df[column].astype(str)
        if (
            column in expected_data.columns
            and expected_data[column].iloc[0] is not None
        ):
            expected_data[column] = expected_data[column].astype(str)

    assert_frame_equal(processed_df, expected_data, check_dtype=False)

    if log_expected:
        assert (
            len(changelog_df) == 1
        ), f"Expected 1 log entry, found {len(changelog_df)}"
        log_entry = changelog_df.iloc[0]
        assert log_entry["record_id"] == record_id
        assert log_entry["column_changed"] == column

        # Handle NaN comparison carefully for old_value in log
        if pd.isna(initial_title):
            assert pd.isna(log_entry["old_value"]), (
                f"Expected old_value in log to be NaN for initial_title None, "
                f"but got {log_entry['old_value']}"
            )
        else:
            assert str(initial_title) == str(log_entry["old_value"]), (
                f"Old value mismatch: expected {initial_title}, "
                f"got {log_entry['old_value']}"
            )

        # Handle new_value comparison in log
        if pd.isna(expected_title):
            assert pd.isna(log_entry["new_value"]), (
                f"Expected new_value in log to be NaN for expected_title None, "
                f"but got {log_entry['new_value']}"
            )
        else:
            assert str(expected_title) == str(log_entry["new_value"]), (
                f"New value mismatch: expected {expected_title}, "
                f"got {log_entry['new_value']}"
            )

        assert log_entry["changed_by"] == changed_by
        assert expected_notes_substring in log_entry["notes"], (
            f"Expected substring '{expected_notes_substring}' not found in notes: "
            f"'{log_entry['notes']}'"
        )
    else:
        assert (
            len(changelog_df) == 0
        ), f"Expected no log entries, found {len(changelog_df)}"


def test_blank_value_on_departure(clear_changelog):
    record_id = "NYC_GOID_00268"
    column_to_edit = "PrincipalOfficersName"
    initial_name = "Jose Bayona"
    feedback_text = (
        "Jose Bayona has left the City"  # This feedback will now trigger POLICY_QUERY
    )
    changed_by = "test_user"
    feedback_source = "test_qa_departure.csv"  # For the log

    golden_data = pd.DataFrame([{"RecordID": record_id, column_to_edit: initial_name}])
    # The actual feedback in qa_data is what's tested against RULES
    qa_data = pd.DataFrame(
        [{"Row(s)": record_id, "Column": column_to_edit, "feedback": feedback_text}]
    )

    # Apply the QA edits, which should now trigger POLICY_QUERY instead of BLANK_VALUE
    processed_df = process_golden_dataset.apply_qa_edits(
        golden_data, qa_data, changed_by, feedback_source
    )

    # Assert DataFrame update - value should remain unchanged
    assert processed_df.loc[0, column_to_edit] == initial_name

    # Assert log_change call
    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["ChangeID"] == 1  # First entry should have ID 1
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["old_value"] == "N/A"  # Policy queries use N/A
    assert log_entry["new_value"] == "N/A"  # Policy queries use N/A
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["notes"] == feedback_text  # Original feedback preserved in notes
    assert log_entry["changed_by"] == changed_by
    assert log_entry["RuleAction"] == process_golden_dataset.QAAction.POLICY_QUERY.value


@pytest.mark.parametrize(
    (
        "initial_value, feedback, should_log, expected_final_value, "
        "expected_log_note_substring"
    ),
    [
        (
            "Old Name",
            "John Doe has left the City",
            True,
            "Old Name",  # Value remains unchanged
            "John Doe has left the City",
        ),
        (
            "Another Name",
            "Someone is no longer with us",
            True,
            "Another Name",  # Value remains unchanged
            "Someone is no longer with us",
        ),
        (
            "Current Occupant",
            "Occupant is no longer at the post",
            True,
            "Current Occupant",  # Value remains unchanged
            "Occupant is no longer at the post",
        ),
        (
            "No Change Needed",
            "This person is still here",
            True,  # Changed to True - will now be logged as POLICY_QUERY
            "No Change Needed",  # Value still remains unchanged
            "This person is still here",
        ),
        (
            "",
            "Field is already empty",
            True,  # Changed to True - will now be logged as POLICY_QUERY
            "",  # Value still remains unchanged
            "Field is already empty",
        ),
    ],
)
def test_blank_value_on_departure_parametrized(
    clear_changelog,
    initial_value,
    feedback,
    should_log,
    expected_final_value,
    expected_log_note_substring,
):
    record_id = "ID_DEPART"
    column_to_edit = "OfficerName"
    changed_by = "test_user"
    feedback_source = "departure_qa.csv"

    golden_data = pd.DataFrame([{"RecordID": record_id, column_to_edit: initial_value}])
    qa_data = pd.DataFrame(
        [{"Row(s)": record_id, "Column": column_to_edit, "feedback": feedback}]
    )

    processed_df = process_golden_dataset.apply_qa_edits(
        golden_data, qa_data, changed_by, feedback_source
    )

    assert processed_df.loc[0, column_to_edit] == expected_final_value

    # All feedback should now generate a changelog entry
    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["ChangeID"] == 1  # First entry should have ID 1
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["notes"] == feedback  # Original feedback preserved in notes
    assert log_entry["changed_by"] == changed_by

    # For departure patterns, expect POLICY_QUERY action and N/A values
    if any(
        pattern in feedback.lower()
        for pattern in ["has left", "no longer with", "no longer at"]
    ):
        assert log_entry["old_value"] == "N/A"
        assert log_entry["new_value"] == "N/A"
        assert (
            log_entry["RuleAction"]
            == process_golden_dataset.QAAction.POLICY_QUERY.value
        )
    else:
        # For unmatched patterns, also expect POLICY_QUERY action and N/A values
        assert log_entry["old_value"] == "N/A"
        assert log_entry["new_value"] == "N/A"
        assert (
            log_entry["RuleAction"]
            == process_golden_dataset.QAAction.POLICY_QUERY.value
        )
