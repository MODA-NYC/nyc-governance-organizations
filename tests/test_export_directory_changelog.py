#!/usr/bin/env python3
"""
Test export_dataset.py changelog tracking of directory field changes.
"""
import csv

# Import the functions we need to test
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.process.export_dataset import (
    add_nycgov_directory_column,
    write_proposed_changes,
)


def test_directory_column_change_tracking():
    """Test that changes to listed_in_nyc_gov_agency_directory are tracked correctly."""

    # Create a sample dataframe with snake_case columns (after conversion)
    df_current = pd.DataFrame(
        {
            "record_id": ["NYC_GOID_000001", "NYC_GOID_000002", "NYC_GOID_000003"],
            "name": ["Agency A", "Agency B", "Agency C"],
            "operational_status": ["Active", "Active", "Active"],
            "organization_type": [
                "Mayoral Agency",
                "Mayoral Agency",
                "Nonprofit Organization",
            ],
            "url": [
                "https://example.com/a",
                "https://example.ny.gov/b",
                "https://example.com/c",
            ],
            "principal_officer_full_name": ["John Doe", "", "Jane Smith"],
            "principal_officer_contact_url": ["", "", ""],
        }
    )

    # Create "before" state dataframe (PascalCase, before snake_case)
    df_before = pd.DataFrame(
        {
            "RecordID": ["NYC_GOID_000001", "NYC_GOID_000002", "NYC_GOID_000003"],
            "Name": ["Agency A", "Agency B", "Agency C"],
            "ListedInNycGovAgencyDirectory": ["False", "True", ""],  # Previous values
        }
    )

    # Run the function with tracking enabled
    df_result, changes = add_nycgov_directory_column(
        df_current,
        df_before_snake_case=df_before,
        df_previous_export=df_before,
        run_id="test_run_123",
    )

    # Verify the dataframe has the new column
    assert "listed_in_nyc_gov_agency_directory" in df_result.columns

    # Verify changes were detected
    assert len(changes) > 0, "Should detect at least one change"

    # Check the structure of change records
    for change in changes:
        assert "record_id" in change
        assert "field" in change
        assert change["field"] == "listed_in_nyc_gov_agency_directory"
        assert "old_value" in change
        assert "new_value" in change
        assert "reason" in change
        assert change["reason"] == "directory_logic_v2"  # Updated to v2
        assert "source_ref" in change
        assert "notes" in change

    # Verify specific changes
    changes_by_id = {c["record_id"]: c for c in changes}

    # NYC_GOID_000001: Should change from False to True (has URL and officer name)
    if "NYC_GOID_000001" in changes_by_id:
        change = changes_by_id["NYC_GOID_000001"]
        assert change["old_value"] in {"", "False"}
        assert change["new_value"] == "True"

    # NYC_GOID_000002: Has ny.gov URL, should be False (excluded)
    # Changed from True to False
    if "NYC_GOID_000002" in changes_by_id:
        change = changes_by_id["NYC_GOID_000002"]
        assert change["old_value"] in {"", "True"}
        assert change["new_value"] == "False"


def test_write_proposed_changes():
    """Test that proposed changes are written to CSV correctly."""

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "test_run"

        changes = [
            {
                "record_id": "NYC_GOID_000001",
                "record_name": "Agency A",
                "field": "listed_in_nyc_gov_agency_directory",
                "old_value": "False",
                "new_value": "True",
                "reason": "directory_logic_v2",  # Updated to v2
                "source_ref": "export_dataset.py::add_nycgov_directory_column",
                "notes": "Type-based inclusion: Mayoral Agency",
            },
            {
                "record_id": "NYC_GOID_000002",
                "record_name": "Agency B",
                "field": "listed_in_nyc_gov_agency_directory",
                "old_value": "",
                "new_value": "False",
                "reason": "directory_logic_v2",  # Updated to v2
                "source_ref": "export_dataset.py::add_nycgov_directory_column",
                "notes": "Manual override: forced to FALSE",
            },
        ]

        write_proposed_changes(
            run_dir, changes, run_id="test_run_456", operator="test_user"
        )

        # Verify the file was created
        proposed_path = run_dir / "outputs" / "run_changelog.csv"
        assert proposed_path.exists()

        # Read and verify contents
        with proposed_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2

        # Verify required columns are present
        required_cols = [
            "timestamp_utc",
            "run_id",
            "record_id",
            "record_name",
            "field",
            "old_value",
            "new_value",
            "reason",
            "evidence_url",
            "source_ref",
            "operator",
            "notes",
        ]
        for col in required_cols:
            assert col in rows[0], f"Missing column: {col}"

        # Verify data
        assert rows[0]["record_id"] == "NYC_GOID_000001"
        assert rows[0]["field"] == "listed_in_nyc_gov_agency_directory"
        assert rows[0]["old_value"] == "False"
        assert rows[0]["new_value"] == "True"
        assert rows[0]["run_id"] == "test_run_456"
        assert rows[0]["operator"] == "test_user"

        assert rows[1]["record_id"] == "NYC_GOID_000002"
        assert rows[1]["notes"] == "Manual override: forced to FALSE"


def test_no_changes_when_values_unchanged():
    """Test that no changes are tracked when values don't change."""

    # Create identical before/after states
    df_current = pd.DataFrame(
        {
            "record_id": ["NYC_GOID_000001"],
            "name": ["Agency A"],
            "operational_status": ["Active"],
            "organization_type": ["Mayoral Agency"],
            "url": ["https://example.com/a"],
            "principal_officer_full_name": ["John Doe"],
            "principal_officer_contact_url": [""],
            "listed_in_nyc_gov_agency_directory": [True],  # Already set
        }
    )

    df_before = pd.DataFrame(
        {
            "RecordID": ["NYC_GOID_000001"],
            "ListedInNycGovAgencyDirectory": ["True"],  # Same as current
        }
    )

    df_result, changes = add_nycgov_directory_column(
        df_current,
        df_before_snake_case=df_before,
        df_previous_export=df_before,
        run_id="test_run_789",
    )

    # Should detect no changes since values are the same
    assert len(changes) == 0, "Should not detect changes when values are unchanged"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
