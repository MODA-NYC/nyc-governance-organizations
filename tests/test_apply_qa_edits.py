import pandas as pd
import pytest

import process_golden_dataset as pgd


# Fixture to clear changelog_entries before each test
@pytest.fixture(autouse=True)
def clear_changelog(monkeypatch):
    # Create a new empty list for changelog_entries for each test
    # This ensures test isolation.
    new_changelog = []
    monkeypatch.setattr(pgd, "changelog_entries", new_changelog)
    return new_changelog  # Return it so tests can inspect it if needed


def test_changelog_columns_definition():
    assert pgd.CHANGELOG_COLUMNS == [
        "timestamp",
        "record_id",
        "column_changed",
        "old_value",
        "new_value",
        "feedback_source",
        "notes",
        "changed_by",
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
    modified_row = pgd.handle_direct_set(
        row_series, column_to_edit, new_name, record_id, feedback_source, changed_by
    )

    # Assert DataFrame update
    assert modified_row[column_to_edit] == new_name

    # Assert log_change call
    assert len(clear_changelog) == 1
    log_entry = clear_changelog[0]
    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == column_to_edit
    assert log_entry["old_value"] == "Old Name"
    assert log_entry["new_value"] == new_name
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["changed_by"] == changed_by


def test_blank_out_value(clear_changelog):
    data = {"record_id": ["NYC_GOID_002"], "Description": ["Initial Description"]}
    df = pd.DataFrame(data)
    row_series = df.iloc[0].copy()

    record_id = "NYC_GOID_002"
    column_to_edit = "Description"
    feedback_source = "Test"
    changed_by = "Tester"

    modified_row = pgd.handle_blank_value(
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

    modified_row = pgd.handle_char_fix(
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

    modified_row = pgd.handle_char_fix(
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

    modified_row = pgd.handle_dedup_semicolon(
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

    modified_row = pgd.handle_dedup_semicolon(
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

    modified_row = pgd.handle_dedup_semicolon(
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

    modified_row = pgd.handle_dedup_semicolon(
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

    modified_row = pgd.handle_dedup_semicolon(
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

    modified_row = pgd.handle_dedup_semicolon(
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
    modified_row = pgd.handle_policy_query(
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

    assert log_entry["record_id"] == record_id
    assert log_entry["column_changed"] == (column_to_edit or "Policy Question")
    assert log_entry["old_value"] == "N/A"
    assert log_entry["new_value"] == "N/A"
    assert (
        log_entry["notes"] == original_feedback
    ), "Logged notes do not match original feedback"
    assert log_entry["feedback_source"] == feedback_source
    assert log_entry["changed_by"] == changed_by
