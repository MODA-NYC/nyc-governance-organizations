"""Tests for RecordID generation and uniqueness."""

import pandas as pd

from nycgo_pipeline.qa_edits import (
    _convert_recordid_to_new_format,
    _generate_next_record_id,
)


def test_convert_recordid_to_new_format():
    """Test RecordID format conversion."""
    # Standard cases
    assert _convert_recordid_to_new_format("NYC_GOID_000022") == 100022
    assert _convert_recordid_to_new_format("NYC_GOID_000318") == 100318

    # Edge case: 6-digit starting with "1"
    assert _convert_recordid_to_new_format("NYC_GOID_100026") == 110026

    # Already in new format
    assert _convert_recordid_to_new_format("100318") == 100318

    # Invalid formats
    assert _convert_recordid_to_new_format("INVALID") is None
    assert _convert_recordid_to_new_format("") is None


def test_generate_next_record_id_basic():
    """Test basic RecordID generation."""
    df = pd.DataFrame(
        {
            "record_id": ["NYC_GOID_000000", "NYC_GOID_000001", "NYC_GOID_000002"],
            "name": ["Entity 1", "Entity 2", "Entity 3"],
        }
    )

    next_id = _generate_next_record_id(df)
    assert next_id == "NYC_GOID_000003"
    assert next_id.startswith("NYC_GOID_")


def test_generate_next_record_id_with_old_format():
    """Test ID generation when dataset has old format IDs."""
    df = pd.DataFrame(
        {
            "record_id": ["NYC_GOID_000000", "NYC_GOID_000001", "NYC_GOID_000002"],
            "name": ["Entity 1", "Entity 2", "Entity 3"],
        }
    )

    next_id = _generate_next_record_id(df)
    # Should generate next in NYC_GOID_ format
    assert next_id == "NYC_GOID_000003"
    assert next_id.startswith("NYC_GOID_")


def test_generate_next_record_id_uniqueness():
    """Test that generated IDs are unique."""
    df = pd.DataFrame(
        {
            "record_id": [
                "NYC_GOID_000000",
                "NYC_GOID_000001",
                "NYC_GOID_000003",
            ],  # Gap at 000002
            "name": ["Entity 1", "Entity 2", "Entity 3"],
        }
    )

    next_id = _generate_next_record_id(df)
    # Should generate 000004 (next after max), not fill gap
    assert next_id == "NYC_GOID_000004"

    # Verify it's not in existing IDs
    assert next_id not in df["record_id"].values


def test_generate_next_record_id_mixed_formats():
    """Test ID generation with mixed old and new format IDs."""
    df = pd.DataFrame(
        {
            "record_id": ["100000", "NYC_GOID_000001", "100002"],
            "name": ["Entity 1", "Entity 2", "Entity 3"],
        }
    )

    next_id = _generate_next_record_id(df)
    # Should handle both formats and generate next in NYC_GOID_ format
    assert next_id == "NYC_GOID_000003"


def test_generate_next_record_id_edge_case_100xxx():
    """Test ID generation with edge case IDs starting with 100xxx."""
    df = pd.DataFrame(
        {
            "record_id": ["NYC_GOID_100026", "NYC_GOID_100027"],
            "name": ["Entity 1", "Entity 2"],
        }
    )

    next_id = _generate_next_record_id(df)
    # Should convert 100027 → internal 110027, then generate 110028 → NYC_GOID_100028
    assert next_id == "NYC_GOID_100028"


def test_generate_next_record_id_empty_dataset():
    """Test ID generation with empty dataset."""
    df = pd.DataFrame({"record_id": [], "name": []})

    next_id = _generate_next_record_id(df)
    # Should start from minimum + 1 (100000 is reserved/minimum)
    assert next_id == "NYC_GOID_000001"


def test_generate_next_record_id_handles_duplicates():
    """Test that generation handles potential duplicate IDs."""
    df = pd.DataFrame(
        {
            "record_id": [
                "NYC_GOID_000000",
                "NYC_GOID_000001",
                "NYC_GOID_000001",
            ],  # Duplicate
            "name": ["Entity 1", "Entity 2", "Entity 3"],
        }
    )

    next_id = _generate_next_record_id(df)
    # Should still generate unique ID
    assert next_id == "NYC_GOID_000002"
    assert next_id not in df["record_id"].values


def test_generate_next_record_id_sequential_generation():
    """Test generating multiple IDs sequentially."""
    df = pd.DataFrame({"record_id": ["NYC_GOID_000000"], "name": ["Entity 1"]})

    # Generate first ID
    id1 = _generate_next_record_id(df)
    assert id1 == "NYC_GOID_000001"

    # Add it and generate next
    df = pd.concat(
        [df, pd.DataFrame({"record_id": [id1], "name": ["Entity 2"]})],
        ignore_index=True,
    )
    id2 = _generate_next_record_id(df)
    assert id2 == "NYC_GOID_000002"

    # Verify both are unique
    assert id1 != id2
    assert id1 in df["record_id"].values
    assert id2 not in df["record_id"].values
