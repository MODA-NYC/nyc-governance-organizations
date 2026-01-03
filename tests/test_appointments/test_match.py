"""Tests for organization and person matching."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nycgo_pipeline.appointments.match import (
    MatchType,
    OrgMatch,
    RecommendedAction,
    match_organization,
)


@pytest.fixture
def golden_df():
    """Load sample golden dataset fixture."""
    fixture_path = (
        Path(__file__).parent.parent / "fixtures" / "appointments" / "golden_sample.csv"
    )
    return pd.read_csv(fixture_path, dtype=str).fillna("")


class TestMatchOrganization:
    """Tests for match_organization function."""

    def test_exact_match(self, golden_df):
        """Test exact name match."""
        matches = match_organization("Department of Buildings", golden_df)

        assert len(matches) >= 1
        best = matches[0]
        assert best.match_type == MatchType.EXACT
        assert best.confidence == 1.0
        assert best.record_id == "NYC_GOID_000001"

    def test_alternate_name_match(self, golden_df):
        """Test match on alternate name."""
        matches = match_organization("DOB", golden_df)

        # Should match Department of Buildings via alternate name
        assert len(matches) >= 1
        # Could be acronym or alternate name match
        assert any(m.record_id == "NYC_GOID_000001" for m in matches)

    def test_acronym_match(self, golden_df):
        """Test match on acronym."""
        matches = match_organization("FDNY", golden_df)

        assert len(matches) >= 1
        best = matches[0]
        assert best.record_id == "NYC_GOID_000004"
        assert best.match_type in {MatchType.ACRONYM, MatchType.ALTERNATE_NAME}

    def test_no_match(self, golden_df):
        """Test no match for unknown agency."""
        matches = match_organization("Unknown Agency XYZ", golden_df)

        # Should return empty or fuzzy matches with low confidence
        if matches:
            assert all(m.confidence < 0.7 for m in matches)

    def test_normalized_match(self, golden_df):
        """Test match with different casing/spacing."""
        matches = match_organization("DEPARTMENT OF BUILDINGS", golden_df)

        assert len(matches) >= 1
        best = matches[0]
        assert best.record_id == "NYC_GOID_000001"

    def test_abbreviation_expansion_match(self, golden_df):
        """Test match with abbreviations."""
        # Match via acronym DCAS
        matches = match_organization("DCAS", golden_df)

        assert len(matches) >= 1
        # Should match Department of Citywide Administrative Services
        assert any(m.record_id == "NYC_GOID_000003" for m in matches)

    def test_source_name_match(self, golden_df):
        """Test match on source name columns."""
        # name_nycgov_mayors_office for DOE is "DOE"
        matches = match_organization("DOE", golden_df)

        # Should have matches
        assert len(matches) >= 1


class TestOrgMatch:
    """Tests for OrgMatch dataclass."""

    def test_org_match_creation(self):
        """Test creating OrgMatch."""
        match = OrgMatch(
            record_id="NYC_GOID_000001",
            org_name="Department of Buildings",
            match_type=MatchType.EXACT,
            confidence=1.0,
            matched_field="name",
            matched_value="Department of Buildings",
        )

        assert match.record_id == "NYC_GOID_000001"
        assert match.confidence == 1.0
        assert match.match_type == MatchType.EXACT


class TestRecommendedAction:
    """Tests for RecommendedAction enum."""

    def test_action_values(self):
        """Test action enum values."""
        assert RecommendedAction.UPDATE_OFFICER.value == "UPDATE_OFFICER"
        assert RecommendedAction.ADD_OFFICER.value == "ADD_OFFICER"
        assert RecommendedAction.VERIFY_VACANCY.value == "VERIFY_VACANCY"
        assert RecommendedAction.MANUAL_REVIEW.value == "MANUAL_REVIEW"
