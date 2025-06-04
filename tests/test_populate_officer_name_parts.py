"""
Test suite for the populate_officer_name_parts function.

This module tests the name parsing functionality that populates detailed
officer name fields from the PrincipalOfficerName field.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from process_golden_dataset import QAAction, populate_officer_name_parts


class TestPopulateOfficerNameParts:
    """Test class for populate_officer_name_parts function."""

    @pytest.fixture
    def mock_log_change(self):
        """Fixture for mock log_change function."""
        return MagicMock()

    @pytest.fixture
    def sample_df(self):
        """Fixture providing a sample DataFrame with various name formats."""
        return pd.DataFrame(
            {
                "RecordID": ["REC001", "REC002", "REC003", "REC004", "REC005"],
                "PrincipalOfficerName": [
                    "John Smith",
                    "Mary Jane Johnson",
                    "Dr. Robert A. Williams Jr.",
                    "",  # Empty string
                    None,  # None value
                ],
                # Existing columns with some data
                "PrincipalOfficerGivenName": ["", "Mary", "", "", ""],
                "PrincipalOfficerFamilyName": ["", "Johnson", "", "", ""],
            }
        )

    def test_successful_simple_name_parsing(self, sample_df, mock_log_change):
        """Test parsing of simple first and last names."""
        result_df = populate_officer_name_parts(
            sample_df.copy(), "test_user", mock_log_change, QAAction
        )

        # Check John Smith was parsed correctly
        assert result_df.loc[0, "PrincipalOfficerFullName"] == "John Smith"
        assert result_df.loc[0, "PrincipalOfficerGivenName"] == "John"
        assert result_df.loc[0, "PrincipalOfficerFamilyName"] == "Smith"
        assert result_df.loc[0, "PrincipalOfficerMiddleNameOrInitial"] == ""
        assert result_df.loc[0, "PrincipalOfficerSuffix"] == ""

        # Verify log_change was called for the full name copy and parsed fields
        assert mock_log_change.call_count >= 3  # FullName + GivenName + FamilyName

    def test_name_with_middle_name(self, sample_df, mock_log_change):
        """Test parsing of names with middle names."""
        result_df = populate_officer_name_parts(
            sample_df.copy(), "test_user", mock_log_change, QAAction
        )

        # Check Mary Jane Johnson
        assert result_df.loc[1, "PrincipalOfficerFullName"] == "Mary Jane Johnson"
        assert result_df.loc[1, "PrincipalOfficerGivenName"] == "Mary"
        assert result_df.loc[1, "PrincipalOfficerMiddleNameOrInitial"] == "Jane"
        assert result_df.loc[1, "PrincipalOfficerFamilyName"] == "Johnson"

    def test_name_with_title_and_suffix(self, sample_df, mock_log_change):
        """Test parsing of names with titles and suffixes."""
        result_df = populate_officer_name_parts(
            sample_df.copy(), "test_user", mock_log_change, QAAction
        )

        # Check Dr. Robert A. Williams Jr.
        full_name = result_df.loc[2, "PrincipalOfficerFullName"]
        assert full_name == "Dr. Robert A. Williams Jr."
        assert result_df.loc[2, "PrincipalOfficerGivenName"] == "Robert"
        assert result_df.loc[2, "PrincipalOfficerMiddleNameOrInitial"] == "A."
        assert result_df.loc[2, "PrincipalOfficerFamilyName"] == "Williams"
        assert result_df.loc[2, "PrincipalOfficerSuffix"] == "Jr."

    def test_empty_name_handling(self, sample_df, mock_log_change):
        """Test handling of empty string names."""
        populate_officer_name_parts(
            sample_df.copy(), "test_user", mock_log_change, QAAction
        )

        # Check empty string case (index 3)
        # Should log as needing review
        review_calls = [
            call
            for call in mock_log_change.call_args_list
            if call[1].get("column_changed") == "PrincipalOfficerName_ParseReview"
        ]
        assert any("REC004" in str(call[1].get("record_id")) for call in review_calls)

    def test_none_name_handling(self, sample_df, mock_log_change):
        """Test handling of None/null names."""
        populate_officer_name_parts(
            sample_df.copy(), "test_user", mock_log_change, QAAction
        )

        # Check None case (index 4)
        # Should log as needing review
        review_calls = [
            call
            for call in mock_log_change.call_args_list
            if call[1].get("column_changed") == "PrincipalOfficerName_ParseReview"
        ]
        assert any("REC005" in str(call[1].get("record_id")) for call in review_calls)

    def test_missing_columns_creation(self, mock_log_change):
        """Test that missing columns are created."""
        # Create DataFrame without the required columns
        df = pd.DataFrame(
            {"RecordID": ["REC001"], "PrincipalOfficerName": ["John Doe"]}
        )

        result_df = populate_officer_name_parts(
            df, "test_user", mock_log_change, QAAction
        )

        # Check all required columns exist
        required_cols = [
            "PrincipalOfficerFullName",
            "PrincipalOfficerGivenName",
            "PrincipalOfficerMiddleNameOrInitial",
            "PrincipalOfficerFamilyName",
            "PrincipalOfficerSuffix",
        ]
        for col in required_cols:
            assert col in result_df.columns

    def test_complex_names(self, mock_log_change):
        """Test parsing of various complex name formats."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001", "REC002", "REC003", "REC004"],
                "PrincipalOfficerName": [
                    "Maria de la Cruz",  # Multi-part last name
                    "Jean-Claude Van Damme",  # Hyphenated first name
                    "Mary Elizabeth Smith-Jones",  # Hyphenated last name
                    "Jose Carlos Santos da Silva",  # Portuguese style name
                ],
            }
        )

        result_df = populate_officer_name_parts(
            df, "test_user", mock_log_change, QAAction
        )

        # Check that all names have been processed
        assert result_df.loc[0, "PrincipalOfficerFullName"] == "Maria de la Cruz"
        assert result_df.loc[1, "PrincipalOfficerFullName"] == "Jean-Claude Van Damme"
        name_2 = result_df.loc[2, "PrincipalOfficerFullName"]
        assert name_2 == "Mary Elizabeth Smith-Jones"
        name_3 = result_df.loc[3, "PrincipalOfficerFullName"]
        assert name_3 == "Jose Carlos Santos da Silva"

    def test_single_name_handling(self, mock_log_change):
        """Test handling of single names (no last name)."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001", "REC002"],
                "PrincipalOfficerName": ["Madonna", "Cher"],  # Single names
            }
        )

        populate_officer_name_parts(df, "test_user", mock_log_change, QAAction)

        # These should be logged as needing review since they don't have
        # both first and last names
        review_calls = [
            call
            for call in mock_log_change.call_args_list
            if call[1].get("column_changed") == "PrincipalOfficerName_ParseReview"
        ]
        assert len(review_calls) >= 2  # Both single names should need review

    def test_logging_behavior(self, mock_log_change):
        """Test that appropriate logging occurs for different scenarios."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001"],
                "PrincipalOfficerName": ["John Smith"],
                "PrincipalOfficerFullName": [""],  # Empty, so should log change
                "PrincipalOfficerGivenName": [""],
                "PrincipalOfficerFamilyName": [""],
            }
        )

        populate_officer_name_parts(df, "test_user", mock_log_change, QAAction)

        # Check logging for successful parsing
        success_logs = [
            call
            for call in mock_log_change.call_args_list
            if call[1].get("rule_action") == QAAction.NAME_PARSE_SUCCESS.value
        ]
        assert len(success_logs) >= 3  # FullName, GivenName, FamilyName

    def test_no_changes_when_values_unchanged(self, mock_log_change):
        """Test that no logging occurs when values don't change."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001"],
                "PrincipalOfficerName": ["John Smith"],
                "PrincipalOfficerFullName": ["John Smith"],  # Already correct
                "PrincipalOfficerGivenName": ["John"],  # Already correct
                "PrincipalOfficerFamilyName": ["Smith"],  # Already correct
            }
        )

        populate_officer_name_parts(df, "test_user", mock_log_change, QAAction)

        # Should have minimal logging since values already match
        assert mock_log_change.call_count < 3

    @patch("nameparser.HumanName")
    def test_nameparser_exception_handling(self, mock_humanname, mock_log_change):
        """Test handling when nameparser raises an exception."""
        # Make HumanName raise an exception
        mock_humanname.side_effect = Exception("Parsing error")

        df = pd.DataFrame(
            {"RecordID": ["REC001"], "PrincipalOfficerName": ["John Smith"]}
        )

        populate_officer_name_parts(df, "test_user", mock_log_change, QAAction)

        # Should log as error/review needed
        error_logs = [
            call
            for call in mock_log_change.call_args_list
            if "Error parsing name" in str(call[1].get("notes", ""))
        ]
        assert len(error_logs) >= 1

    def test_nameparser_not_installed(self, mock_log_change, capsys):
        """Test behavior when nameparser is not installed."""
        with patch.dict(sys.modules, {"nameparser": None}):
            df = pd.DataFrame(
                {"RecordID": ["REC001"], "PrincipalOfficerName": ["John Smith"]}
            )

            result_df = populate_officer_name_parts(
                df, "test_user", mock_log_change, QAAction
            )

            # Should return unchanged dataframe
            assert result_df.equals(df)

            # Check error message was printed
            captured = capsys.readouterr()
            assert "nameparser library not installed" in captured.out

    def test_special_characters_in_names(self, mock_log_change):
        """Test parsing names with special characters."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001", "REC002", "REC003"],
                "PrincipalOfficerName": [
                    "José García",  # Accented characters
                    "Mary O'Brien",  # Apostrophe
                    "Anne-Marie D'Angelo",  # Hyphens and apostrophe
                ],
            }
        )

        result_df = populate_officer_name_parts(
            df, "test_user", mock_log_change, QAAction
        )

        # Check that names were processed without errors
        assert result_df.loc[0, "PrincipalOfficerFullName"] == "José García"
        assert result_df.loc[1, "PrincipalOfficerFullName"] == "Mary O'Brien"
        assert result_df.loc[2, "PrincipalOfficerFullName"] == "Anne-Marie D'Angelo"

    def test_numeric_and_invalid_types(self, mock_log_change):
        """Test handling of non-string types in name field."""
        df = pd.DataFrame(
            {
                "RecordID": ["REC001", "REC002", "REC003"],
                "PrincipalOfficerName": [
                    12345,  # Numeric
                    ["John", "Smith"],  # List
                    {"first": "John", "last": "Smith"},  # Dict
                ],
            }
        )

        populate_officer_name_parts(df, "test_user", mock_log_change, QAAction)

        # All should be logged as needing review
        review_calls = [
            call
            for call in mock_log_change.call_args_list
            if call[1].get("column_changed") == "PrincipalOfficerName_ParseReview"
        ]
        assert len(review_calls) >= 3


# Additional integration-style tests
def test_end_to_end_processing():
    """Test the complete flow with a realistic dataset."""
    # Create a more realistic dataset
    df = pd.DataFrame(
        {
            "RecordID": [f"NYC{i:04d}" for i in range(1, 11)],
            "PrincipalOfficerName": [
                "John Smith",
                "Maria Elena Rodriguez-Garcia",
                "Dr. William Chen, Ph.D.",
                "Sarah Johnson-Williams",
                "Robert James Miller III",
                "",
                None,
                "Acting Director Jane Doe",
                "José María de la Cruz y García",
                "Mary",
            ],
        }
    )

    mock_log = MagicMock()
    result = populate_officer_name_parts(df, "integration_test", mock_log, QAAction)

    # Verify all records were processed
    assert len(result) == len(df)

    # Verify required columns exist
    required_cols = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]
    for col in required_cols:
        assert col in result.columns

    # Check that some names were successfully parsed
    success_count = sum(
        1
        for call in mock_log.call_args_list
        if call[1].get("rule_action") == QAAction.NAME_PARSE_SUCCESS.value
        and call[1].get("column_changed") != "PrincipalOfficerFullName"
    )
    assert success_count > 0

    # Check that some names needed review
    review_count = sum(
        1
        for call in mock_log.call_args_list
        if call[1].get("rule_action") == QAAction.NAME_PARSE_REVIEW_NEEDED.value
    )
    assert review_count > 0  # Empty, None, and single name should need review


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
