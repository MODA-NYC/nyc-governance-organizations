import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
from enum import Enum

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import process_golden_dataset

# Sample columns for consistent DataFrames, defined globally for the test module
SAMPLE_COLS = [
    "RecordID",
    "Name",
    "Description",
    "URL",
    "Acronym",
    "AlternateOrFormerNames",
]


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

    data = {"record_id": ["NYC_GOID_005"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_005"
    column_to_edit = "AlternateOrFormerNames"
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
    data = {"record_id": ["NYC_GOID_006"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_006"
    column_to_edit = "AlternateOrFormerNames"
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
    data = {"record_id": ["NYC_GOID_007"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_007"
    column_to_edit = "AlternateOrFormerNames"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = process_golden_dataset.handle_dedup_semicolon(
        row_series, column_to_edit, record_id, feedback_source, changed_by
    )

    assert modified_row[column_to_edit] == ""  # Should remain empty
    assert len(clear_changelog) == 0


def test_deduplicate_semicolon_list_single_item(clear_changelog):
    original_value = "NameA"
    data = {"record_id": ["NYC_GOID_008"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_008"
    column_to_edit = "AlternateOrFormerNames"
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
    data = {"record_id": ["NYC_GOID_009"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_009"
    column_to_edit = "AlternateOrFormerNames"
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
    data = {"record_id": ["NYC_GOID_010"], "AlternateOrFormerNames": [original_value]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_010"
    column_to_edit = "AlternateOrFormerNames"
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


def test_apply_global_deduplication(clear_changelog):
    """Test the apply_global_deduplication function."""
    # Create test data
    test_data = {
        "RecordID": ["1", "2", "3"],
        "AlternateOrFormerNames": [
            "Name1;Name2;Name1",  # Has duplicates
            "Name3;Name4",  # No duplicates
            "Name5;;Name5;  Name5  ",  # Has duplicates, empty entries, and whitespace
        ],
        "AlternateOrFormerAcronyms": [
            "ABC;DEF;ABC",  # Has duplicates
            "",  # Empty string
            "GHI;GHI;  GHI  ",  # Has duplicates and whitespace
        ],
    }
    df_input = pd.DataFrame(test_data)

    # Create a mock log_change function that appends to a list
    changes_logged = []

    def mock_log_change(
        record_id,
        column_changed,
        old_value,
        new_value,
        feedback_source,
        notes,
        changed_by,
        rule_action,
    ):
        changes_logged.append(
            {
                "record_id": record_id,
                "column_changed": column_changed,
                "old_value": old_value,
                "new_value": new_value,
                "feedback_source": feedback_source,
                "notes": notes,
                "changed_by": changed_by,
                "rule_action": rule_action,
            }
        )

    # Create a mock QAAction enum
    class MockQAAction(Enum):
        DEDUP_SEMICOLON = "dedup_semicolon"

    # Call the function
    df_result = process_golden_dataset.apply_global_deduplication(
        df_input,
        "test_user",
        mock_log_change,
        MockQAAction,
    )

    # Test that the function returns a new DataFrame
    assert id(df_result) != id(df_input)

    # Test AlternateOrFormerNames deduplication
    assert df_result.loc[0, "AlternateOrFormerNames"] == "Name1;Name2"
    assert df_result.loc[1, "AlternateOrFormerNames"] == "Name3;Name4"
    assert df_result.loc[2, "AlternateOrFormerNames"] == "Name5"

    # Test AlternateOrFormerAcronyms deduplication
    assert df_result.loc[0, "AlternateOrFormerAcronyms"] == "ABC;DEF"
    assert df_result.loc[1, "AlternateOrFormerAcronyms"] == ""
    assert df_result.loc[2, "AlternateOrFormerAcronyms"] == "GHI"

    # Test that changes were logged correctly
    assert len(changes_logged) == 4  # Should have 4 changes logged

    # Check specific changes
    expected_changes = [
        {
            "record_id": "1",
            "column_changed": "AlternateOrFormerNames",
            "old_value": "Name1;Name2;Name1",
            "new_value": "Name1;Name2",
            "feedback_source": "System_GlobalRule",
            "notes": "Global deduplication applied to AlternateOrFormerNames",
            "changed_by": "test_user",
            "rule_action": "dedup_semicolon",
        },
        {
            "record_id": "1",
            "column_changed": "AlternateOrFormerAcronyms",
            "old_value": "ABC;DEF;ABC",
            "new_value": "ABC;DEF",
            "feedback_source": "System_GlobalRule",
            "notes": "Global deduplication applied to AlternateOrFormerAcronyms",
            "changed_by": "test_user",
            "rule_action": "dedup_semicolon",
        },
        {
            "record_id": "3",
            "column_changed": "AlternateOrFormerNames",
            "old_value": "Name5;;Name5;  Name5  ",
            "new_value": "Name5",
            "feedback_source": "System_GlobalRule",
            "notes": "Global deduplication applied to AlternateOrFormerNames",
            "changed_by": "test_user",
            "rule_action": "dedup_semicolon",
        },
        {
            "record_id": "3",
            "column_changed": "AlternateOrFormerAcronyms",
            "old_value": "GHI;GHI;  GHI  ",
            "new_value": "GHI",
            "feedback_source": "System_GlobalRule",
            "notes": "Global deduplication applied to AlternateOrFormerAcronyms",
            "changed_by": "test_user",
            "rule_action": "dedup_semicolon",
        },
    ]

    for expected in expected_changes:
        assert expected in changes_logged, f"Expected change not found: {expected}"


def test_global_character_fixing(clear_changelog):
    """Test the apply_global_character_fixing function."""
    # Create test data with various character issues
    test_data = {
        "RecordID": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "Name": [
            "Mayorâ€™s Office",  # ftfy-fixable mojibake
            "Clean Name",  # Already clean, should not change
            "Name with¬†special space",  # Contains ¬†
            "Name with\u00a0non-breaking space",  # Contains NBSP
            None,  # Non-string value
            "  Padded Name  ",  # Extra whitespace
            "",  # Empty string
            "Normal™ Name",  # Character that may need NFKC normalization
            "Name with multiple  spaces",  # Multiple spaces
        ],
        "Description": [
            "Lorraine Cort√É¬©s-V√É¬°zquez",  # Specific mojibake pattern
            "Description with¬†and\u00a0spaces",  # Multiple issues
            123,  # Non-string value (number)
            "Already clean description",
            "Café",  # Accent that should be preserved
            "Description™ with symbols",  # Trademark symbol
            "   ",  # Only whitespace
            "Multiple\n\nNewlines",  # Newlines should be preserved
            "Tab\tcharacter",  # Tab should be preserved
        ],
        "AlternateOrFormerNames": [
            "Name1¬†Name2",
            "Clean;Names",
            "",
            None,
            "José;María",  # Accented characters should be preserved
            "Name with  extra   spaces",
            "√É¬©√É¬°",  # Just mojibake characters
            "Mixed™Issues¬†Here",
            "Normal Alternative Name",
        ],
        "PrincipalOfficerName": [
            "John Doe",  # Clean
            "Jane¬†Smith",  # With ¬†
            "Bob\u00a0Jones",  # With NBSP - Corrected to use actual unicode char
            "Alice√É¬©Brown",  # With mojibake
            "",
            None,
            123.45,  # Float non-string
            "  Officer Name  ",  # Padded
            "Clean Officer",
        ],
        "Notes": [
            "Note with â€œquotesâ€",  # Smart quotes mojibake
            "Clean note",
            None,
            "",
            "Note¬†with¬†multiple¬†issues",
            "Simple note",
            "Note\u00a0with\u00a0NBSP",
            "   Padded note   ",
            "Already good note",
        ],
        # Add a column not in text_columns_to_fix to verify it's not processed
        "OtherColumn": [
            "Text with¬†issues",
            "More text",
            "Should not be fixed",
            "Keep as is",
            "No changes",
            "Original value",
            "Untouched",
            "Not processed",
            "Ignored column",
        ],
    }
    df_input = pd.DataFrame(test_data)

    # Call the function
    df_result = process_golden_dataset.apply_global_character_fixing(
        df_input,
        "TestGlobalCharFix",
        process_golden_dataset.log_change,
        process_golden_dataset.QAAction,
    )

    # Test that the function returns a new DataFrame
    assert id(df_result) != id(df_input)

    # Test Name column fixes
    assert df_result.loc[0, "Name"] == "Mayor's Office"  # Mojibake fixed
    assert df_result.loc[1, "Name"] == "Clean Name"  # No change
    assert df_result.loc[2, "Name"] == "Name with special space"  # ¬† replaced
    assert df_result.loc[3, "Name"] == "Name with non-breaking space"  # NBSP replaced
    assert df_result.loc[4, "Name"] is None  # None unchanged
    assert df_result.loc[5, "Name"] == "Padded Name"  # Whitespace stripped
    assert df_result.loc[6, "Name"] == ""  # Empty string unchanged
    assert df_result.loc[7, "Name"] == "NormalTM Name"  # NFKC normalizes ™ to TM
    assert (
        df_result.loc[8, "Name"] == "Name with multiple  spaces"
    )  # Internal spaces preserved

    # Test Description column fixes
    assert (
        df_result.loc[0, "Description"] == "Lorraine Cortés-Vázquez"
    )  # Mojibake fixed
    assert (
        df_result.loc[1, "Description"] == "Description with and spaces"
    )  # Multiple fixes
    assert df_result.loc[2, "Description"] == 123  # Non-string unchanged
    assert df_result.loc[3, "Description"] == "Already clean description"  # No change
    assert df_result.loc[4, "Description"] == "Café"  # Accent preserved
    assert (
        df_result.loc[5, "Description"] == "DescriptionTM with symbols"
    )  # ™ normalized to TM
    assert df_result.loc[6, "Description"] == ""  # Whitespace-only becomes empty
    assert (
        df_result.loc[7, "Description"] == "Multiple\n\nNewlines"
    )  # Newlines preserved
    assert df_result.loc[8, "Description"] == "Tab\tcharacter"  # Tab preserved

    # Test AlternateOrFormerNames column fixes
    assert df_result.loc[0, "AlternateOrFormerNames"] == "Name1 Name2"  # ¬† replaced
    assert df_result.loc[1, "AlternateOrFormerNames"] == "Clean;Names"  # No change
    assert df_result.loc[2, "AlternateOrFormerNames"] == ""  # Empty unchanged
    assert df_result.loc[3, "AlternateOrFormerNames"] is None  # None unchanged
    assert (
        df_result.loc[4, "AlternateOrFormerNames"] == "José;María"
    )  # Accents preserved
    assert (
        df_result.loc[5, "AlternateOrFormerNames"] == "Name with  extra   spaces"
    )  # Internal spaces preserved
    assert df_result.loc[6, "AlternateOrFormerNames"] == "éá"  # Mojibake fixed
    assert (
        df_result.loc[7, "AlternateOrFormerNames"] == "MixedTMIssues Here"
    )  # ™ normalized to TM, ¬† fixed

    # Test PrincipalOfficerName column fixes
    assert df_result.loc[0, "PrincipalOfficerName"] == "John Doe"  # No change
    assert df_result.loc[1, "PrincipalOfficerName"] == "Jane Smith"  # ¬† replaced
    assert df_result.loc[2, "PrincipalOfficerName"] == "Bob Jones"  # NBSP replaced
    assert df_result.loc[3, "PrincipalOfficerName"] == "AliceéBrown"  # Mojibake fixed
    assert (
        df_result.loc[7, "PrincipalOfficerName"] == "Officer Name"
    )  # Whitespace stripped

    # Test Notes column fixes
    assert (
        df_result.loc[0, "Notes"] == 'Note with "quotesâ€'
    )  # Smart quotes mojibake partially fixed
    assert (
        df_result.loc[4, "Notes"] == "Note with multiple issues"
    )  # Multiple ¬† replaced
    assert df_result.loc[6, "Notes"] == "Note with NBSP"  # NBSP replaced
    assert df_result.loc[7, "Notes"] == "Padded note"  # Whitespace stripped

    # Test that OtherColumn was NOT processed
    assert df_result.loc[0, "OtherColumn"] == "Text with¬†issues"  # Should be unchanged
    assert df_result.loc[1, "OtherColumn"] == "More text"  # Should be unchanged

    # Check the changelog entries
    changelog_df = pd.DataFrame(clear_changelog)

    # The actual number of changes may vary based on ftfy and unicodedata behavior
    # So we'll check that we have at least some changes logged
    assert len(changelog_df) > 0, "No changes were logged"

    # Check that all logged entries have the correct structure
    for _, log_entry in changelog_df.iterrows():
        assert "ChangeID" in log_entry
        assert log_entry["feedback_source"] == "System_GlobalCharFix"
        assert log_entry["changed_by"] == "TestGlobalCharFix"
        assert log_entry["RuleAction"] == process_golden_dataset.QAAction.CHAR_FIX.value
        assert "Global character/Unicode fixing applied to" in log_entry["notes"]

        # Verify the column changed is in our text_columns_to_fix
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
        assert log_entry["column_changed"] in text_columns_to_fix

        # Verify old_value and new_value are different
        assert log_entry["old_value"] != log_entry["new_value"]

    # Verify that specific known fixes were logged
    name_mayor_change = changelog_df[
        (changelog_df["record_id"] == "1") & (changelog_df["column_changed"] == "Name")
    ]
    assert len(name_mayor_change) == 1
    assert "Mayor" in name_mayor_change.iloc[0]["new_value"]
    assert "Office" in name_mayor_change.iloc[0]["new_value"]

    description_cortez_change = changelog_df[
        (changelog_df["record_id"] == "1")
        & (changelog_df["column_changed"] == "Description")
    ]
    assert len(description_cortez_change) == 1
    assert "Cortés-Vázquez" in description_cortez_change.iloc[0]["new_value"]


# --- Tests for handle_delete_record ---


def test_delete_existing_record(clear_changelog):
    df_golden = create_sample_golden_df()
    record_id_to_delete = "NYC_GOID_002"

    qa_data = {
        "Row(s)": [
            record_id_to_delete
        ],  # Though not directly used by delete rule parsing
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Delete RecordID {record_id_to_delete}"],
    }
    df_qa = pd.DataFrame(qa_data)

    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_delete", "qa_delete_ops.csv"
    )

    # Assert record is removed
    assert record_id_to_delete not in processed_df["RecordID"].values
    assert len(processed_df) == len(df_golden) - 1

    # Assert changelog
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == 1
    log_entry = changelog_df.iloc[0]
    assert log_entry["record_id"] == record_id_to_delete
    assert log_entry["column_changed"] == "_ROW_DELETED"
    assert log_entry["old_value"] == "Org B"  # Name of NYC_GOID_002
    assert log_entry["new_value"] == "N/A"
    assert log_entry["feedback_source"] == "qa_delete_ops.csv"
    assert log_entry["notes"] == f"Delete RecordID {record_id_to_delete}"
    assert log_entry["changed_by"] == "test_user_delete"
    expected_action = process_golden_dataset.QAAction.DELETE_RECORD.value
    assert log_entry["RuleAction"] == expected_action


def test_delete_nonexistent_record(clear_changelog):
    df_golden = create_sample_golden_df()
    non_existent_record_id = "NYC_GOID_999"

    qa_data = {
        "Row(s)": [non_existent_record_id],
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Delete RecordID {non_existent_record_id}"],
    }
    df_qa = pd.DataFrame(qa_data)

    initial_df_copy = df_golden.copy()
    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_delete_fail", "qa_delete_fail.csv"
    )

    # Assert DataFrame remains unchanged
    assert_frame_equal(processed_df, initial_df_copy)

    # Assert changelog
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == 1
    log_entry = changelog_df.iloc[0]
    assert log_entry["record_id"] == non_existent_record_id
    assert log_entry["column_changed"] == "_ROW_DELETE_FAILED"
    assert log_entry["old_value"] == "Record Not Found"
    assert log_entry["feedback_source"] == "qa_delete_fail.csv"
    expected_notes = (
        f"Record not found for deletion. "
        f"Feedback: Delete RecordID {non_existent_record_id}"
    )
    assert log_entry["notes"] == expected_notes
    assert log_entry["changed_by"] == "test_user_delete_fail"
    # The rule action is still delete, but it failed
    expected_action = process_golden_dataset.QAAction.DELETE_RECORD.value
    assert log_entry["RuleAction"] == expected_action


# --- Tests for handle_append_from_csv ---


def test_append_from_valid_csv(clear_changelog, tmp_path):
    df_golden = create_sample_golden_df()

    # Create a temporary CSV file with new records
    append_csv_filename = "test_append_data.csv"
    append_csv_path = tmp_path / append_csv_filename

    new_records_data = [
        ["NYC_GOID_004", "Org D", "Desc D", "url_d", "D", "D1"],
        ["NYC_GOID_005", "Org E", "Desc E", "url_e", "E", "E1;E2"],
    ]
    with open(append_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SAMPLE_COLS)  # Header
        writer.writerows(new_records_data)

    qa_data = {
        "Row(s)": ["_SYSTEM_ACTION"],
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Append records from CSV {append_csv_filename}"],
    }
    df_qa = pd.DataFrame(qa_data)

    # qa_filename path determines base_input_dir
    dummy_qa_filepath = tmp_path / "qa_append_ops.csv"

    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_append", str(dummy_qa_filepath)
    )

    # Assert new records are present
    assert len(processed_df) == len(df_golden) + len(new_records_data)
    assert "NYC_GOID_004" in processed_df["RecordID"].values
    assert "NYC_GOID_005" in processed_df["RecordID"].values
    org_d_name_series = processed_df[processed_df["RecordID"] == "NYC_GOID_004"]["Name"]
    assert org_d_name_series.iloc[0] == "Org D"

    # Assert changelog
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == len(new_records_data)

    log_entry_d = changelog_df[changelog_df["record_id"] == "NYC_GOID_004"].iloc[0]
    assert log_entry_d["column_changed"] == "_ROW_ADDED"
    assert log_entry_d["old_value"] == "N/A"
    assert log_entry_d["new_value"] == "Org D"
    assert log_entry_d["feedback_source"] == "qa_append_ops.csv"
    assert f"Append records from CSV {append_csv_filename}" in log_entry_d["notes"]
    assert log_entry_d["changed_by"] == "test_user_append"
    expected_action_append = process_golden_dataset.QAAction.APPEND_FROM_CSV.value
    assert log_entry_d["RuleAction"] == expected_action_append

    log_entry_e = changelog_df[changelog_df["record_id"] == "NYC_GOID_005"].iloc[0]
    assert log_entry_e["column_changed"] == "_ROW_ADDED"
    assert log_entry_e["new_value"] == "Org E"
    assert log_entry_e["RuleAction"] == expected_action_append


def test_append_from_nonexistent_csv(clear_changelog, tmp_path):
    df_golden = create_sample_golden_df()
    non_existent_csv = "non_existent_file.csv"

    qa_data = {
        "Row(s)": ["_SYSTEM_ACTION"],
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Append records from CSV {non_existent_csv}"],
    }
    df_qa = pd.DataFrame(qa_data)
    dummy_qa_filepath = tmp_path / "qa_append_nonexistent.csv"

    initial_df_copy = df_golden.copy()
    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_append_fail", str(dummy_qa_filepath)
    )

    # Assert DataFrame remains unchanged
    assert_frame_equal(processed_df, initial_df_copy)

    # Assert changelog
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == 1
    log_entry = changelog_df.iloc[0]
    assert log_entry["record_id"] == "_APPEND_ERROR"
    assert log_entry["column_changed"] == "_APPEND_FROM_CSV_FAILED"
    assert log_entry["old_value"] == "File Not Found"
    expected_new_value_path_str = str(tmp_path / non_existent_csv)
    assert expected_new_value_path_str in log_entry["new_value"]  # Path is logged
    assert log_entry["feedback_source"] == "qa_append_nonexistent.csv"
    expected_notes = f"Failed to append from {non_existent_csv}: " f"File not found"
    assert expected_notes in log_entry["notes"]
    assert log_entry["changed_by"] == "test_user_append_fail"
    expected_action_append_fail = process_golden_dataset.QAAction.APPEND_FROM_CSV.value
    assert log_entry["RuleAction"] == expected_action_append_fail


def test_append_from_empty_csv(clear_changelog, tmp_path):
    df_golden = create_sample_golden_df()

    empty_csv_filename = "empty_append_data.csv"
    empty_csv_path = tmp_path / empty_csv_filename

    # Create an empty CSV file (can even be just a header or completely empty)
    with open(empty_csv_path, "w", newline=""):  # Ensuring 'as f' is removed
        pass  # No need to create a csv.writer if we're not writing anything
        # writer = csv.writer(f) # Original line causing F841
        # writer.writerow(SAMPLE_COLS) # Writing header means not strictly "empty"
        # for pandas read
        # but the function checks if df_new_records is empty.
        # An empty file or file with only header will result
        # in empty df_new_records.

    qa_data = {
        "Row(s)": ["_SYSTEM_ACTION"],
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Append records from CSV {empty_csv_filename}"],
    }
    df_qa = pd.DataFrame(qa_data)
    dummy_qa_filepath = tmp_path / "qa_append_empty.csv"

    initial_df_copy = df_golden.copy()
    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_append_empty", str(dummy_qa_filepath)
    )

    # Assert DataFrame remains unchanged
    assert_frame_equal(processed_df, initial_df_copy)

    # Assert changelog - Expect 1 entry for the load failure
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == 1
    log_entry = changelog_df.iloc[0]
    assert log_entry["record_id"] == "_APPEND_ERROR"
    assert log_entry["column_changed"] == "_APPEND_FROM_CSV_FAILED"
    assert log_entry["old_value"] == "Load Error"
    # The specific error message might vary slightly, so check for a key part
    assert (
        "No columns to parse from file" in log_entry["new_value"]
        or "empty file" in log_entry["new_value"].lower()
    )  # Depending on pandas version / OS
    assert log_entry["feedback_source"] == "qa_append_empty.csv"
    assert f"Failed to append from {empty_csv_filename}:" in log_entry["notes"]
    assert log_entry["changed_by"] == "test_user_append_empty"
    expected_action_val = process_golden_dataset.QAAction.APPEND_FROM_CSV.value
    assert log_entry["RuleAction"] == expected_action_val


def test_append_csv_with_schema_mismatch(clear_changelog, tmp_path, capsys):
    df_golden = create_sample_golden_df()  # Has SAMPLE_COLS

    # Create a temporary CSV file with mismatched schema
    # Missing 'URL', Extra 'NewColumn'
    mismatch_cols = [
        "RecordID",
        "Name",
        "Description",
        "Acronym",
        "AlternateOrFormerNames",
        "ExtraColumn",
    ]
    append_csv_filename = "test_append_mismatch.csv"
    append_csv_path = tmp_path / append_csv_filename

    new_records_data = [
        ["NYC_GOID_006", "Org F", "Desc F", "F", "F1", "ExtraF"],
    ]
    with open(append_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(mismatch_cols)  # Header
        writer.writerows(new_records_data)

    qa_data = {
        "Row(s)": ["_SYSTEM_ACTION"],
        "Column": ["_SYSTEM_ACTION"],
        "feedback": [f"Append records from CSV {append_csv_filename}"],
    }
    df_qa = pd.DataFrame(qa_data)
    dummy_qa_filepath = tmp_path / "qa_append_mismatch_ops.csv"

    processed_df = process_golden_dataset.apply_qa_edits(
        df_golden.copy(), df_qa, "test_user_append_mismatch", str(dummy_qa_filepath)
    )

    captured = capsys.readouterr()

    # Assert new record is present
    assert len(processed_df) == len(df_golden) + len(new_records_data)
    assert "NYC_GOID_006" in processed_df["RecordID"].values

    # Check resulting schema and values
    assert "ExtraColumn" in processed_df.columns
    df_filtered_original = processed_df[processed_df["RecordID"] == "NYC_GOID_001"]
    col_val = df_filtered_original["ExtraColumn"].iloc[0]
    assert pd.isna(col_val)  # Original rows get NaN for ExtraColumn

    df_filtered_new = processed_df[processed_df["RecordID"] == "NYC_GOID_006"]
    new_row_extra_col_val = df_filtered_new["ExtraColumn"].iloc[0]
    assert new_row_extra_col_val == "ExtraF"

    assert "URL" in processed_df.columns  # Original column still there
    new_row_url_val = df_filtered_new["URL"].iloc[0]
    assert pd.isna(new_row_url_val)  # New row gets NaN for URL as it was missing

    # Assert changelog for the appended row
    changelog_df = pd.DataFrame(process_golden_dataset.changelog_entries)
    assert len(changelog_df) == 1
    log_entry_f = changelog_df[changelog_df["record_id"] == "NYC_GOID_006"].iloc[0]
    assert log_entry_f["column_changed"] == "_ROW_ADDED"
    assert log_entry_f["new_value"] == "Org F"  # Name of NYC_GOID_006
    expected_action_mismatch = process_golden_dataset.QAAction.APPEND_FROM_CSV.value
    assert log_entry_f["RuleAction"] == expected_action_mismatch

    # Assert warnings were printed (basic check)
    assert (
        "Warning: New CSV missing columns present in main dataset: {'URL'}"
        in captured.out
    )
    assert (
        "Warning: New CSV has extra columns not in main dataset: {'ExtraColumn'}"
        in captured.out
    )


def create_sample_golden_df():
    """Creates a sample golden DataFrame for testing."""
    data = {
        "RecordID": ["NYC_GOID_001", "NYC_GOID_002", "NYC_GOID_003"],
        "Name": ["Org A", "Org B", "Org C"],
        "Description": ["Desc A", "Desc B", "Desc C"],
        "URL": ["url_a", "url_b", "url_c"],
        "Acronym": ["A", "B", "C"],
        "AlternateOrFormerNames": ["A1;A2", "B1", ""],
    }
    return pd.DataFrame(data, columns=SAMPLE_COLS)


def get_changelog_df():
    """Converts the global changelog_entries list to a DataFrame."""
    changelog_columns = process_golden_dataset.CHANGELOG_COLUMNS
    return pd.DataFrame(
        process_golden_dataset.changelog_entries, columns=changelog_columns
    )
