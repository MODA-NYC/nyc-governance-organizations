"""Tests for confidence scoring."""

from __future__ import annotations

import pytest

from nycgo_pipeline.appointments.match import (
    Candidate,
    MatchType,
    OrgMatch,
    RecommendedAction,
)
from nycgo_pipeline.appointments.score import (
    ConfidenceLevel,
    ScoreBreakdown,
    calculate_score,
    calculate_score_breakdown,
    filter_candidates,
    score_candidates,
)


@pytest.fixture
def high_confidence_candidate():
    """Create a high-confidence candidate."""
    return Candidate(
        candidate_id="APPT_0001",
        candidate_name="DOE,JANE M.",
        candidate_name_normalized="Jane M. Doe",
        candidate_title_code="1002A",
        effective_date="2025-12-15",
        reason_for_change="APPOINTED",
        agency_name_raw="Department of Buildings",
        nycgo_record_id="NYC_GOID_000001",
        nycgo_org_name="Department of Buildings",
        current_principal_officer="John Smith",  # Different person
        org_match=OrgMatch(
            record_id="NYC_GOID_000001",
            org_name="Department of Buildings",
            match_type=MatchType.EXACT,
            confidence=1.0,
        ),
        name_match_score=0.2,  # Low similarity = different person
        sources=[{"type": "open_data", "dataset_id": "wq4v-8hyb"}],
        recommended_action=RecommendedAction.UPDATE_OFFICER,
    )


@pytest.fixture
def low_confidence_candidate():
    """Create a low-confidence candidate."""
    return Candidate(
        candidate_id="APPT_0002",
        candidate_name="NOBODY,SOME",
        candidate_name_normalized="Some Nobody",
        candidate_title_code="9999X",
        effective_date="2025-12-01",
        reason_for_change="APPOINTED",
        agency_name_raw="Unknown Agency XYZ",
        nycgo_record_id=None,  # No org match
        nycgo_org_name="",
        current_principal_officer="",
        org_match=None,  # No match
        name_match_score=0.0,
        sources=[{"type": "open_data", "dataset_id": "wq4v-8hyb"}],
        recommended_action=RecommendedAction.MANUAL_REVIEW,
    )


@pytest.fixture
def same_person_candidate():
    """Create a candidate that appears to be the same person."""
    return Candidate(
        candidate_id="APPT_0003",
        candidate_name="WALKER,GLEN M.",
        candidate_name_normalized="Glen M. Walker",
        effective_date="2025-12-10",
        reason_for_change="RETIRED",
        agency_name_raw="Law Department",
        nycgo_record_id="NYC_GOID_000002",
        nycgo_org_name="Law Department",
        current_principal_officer="Glen M. Walker",  # Same person
        org_match=OrgMatch(
            record_id="NYC_GOID_000002",
            org_name="Law Department",
            match_type=MatchType.EXACT,
            confidence=1.0,
        ),
        name_match_score=1.0,  # Perfect match = same person
        sources=[{"type": "open_data", "dataset_id": "wq4v-8hyb"}],
        recommended_action=RecommendedAction.VERIFY_VACANCY,
    )


class TestCalculateScore:
    """Tests for calculate_score function."""

    def test_high_confidence_score(self, high_confidence_candidate):
        """Test high-confidence candidate gets high score."""
        score = calculate_score(high_confidence_candidate)
        assert score >= 70  # Should be high due to good org match and different name
        assert high_confidence_candidate.score == score

    def test_low_confidence_score(self, low_confidence_candidate):
        """Test low-confidence candidate gets low score."""
        score = calculate_score(low_confidence_candidate)
        assert score < 50  # No org match = low score
        assert low_confidence_candidate.score == score

    def test_score_range(self, high_confidence_candidate):
        """Test score is within valid range."""
        score = calculate_score(high_confidence_candidate)
        assert 0 <= score <= 100


class TestScoreBreakdown:
    """Tests for score breakdown."""

    def test_breakdown_components(self, high_confidence_candidate):
        """Test breakdown includes all components."""
        breakdown = calculate_score_breakdown(high_confidence_candidate)

        assert isinstance(breakdown, ScoreBreakdown)
        assert breakdown.org_match_score >= 0
        assert breakdown.title_relevance_score >= 0
        assert breakdown.name_differentiation_score >= 0
        assert breakdown.recency_score >= 0
        assert breakdown.evidence_score >= 0

    def test_breakdown_to_dict(self, high_confidence_candidate):
        """Test breakdown can be converted to dict."""
        breakdown = calculate_score_breakdown(high_confidence_candidate)
        d = breakdown.to_dict()

        assert "org_match" in d
        assert "title_relevance" in d
        assert "total" in d
        assert "level" in d

    def test_org_match_score_calculation(self, high_confidence_candidate):
        """Test org match contributes to score."""
        breakdown = calculate_score_breakdown(high_confidence_candidate)
        # With confidence=1.0 and max=40, should get 40 points
        assert breakdown.org_match_score == 40.0

    def test_no_org_match_score(self, low_confidence_candidate):
        """Test no org match gives 0 points."""
        breakdown = calculate_score_breakdown(low_confidence_candidate)
        assert breakdown.org_match_score == 0.0


class TestConfidenceLevel:
    """Tests for confidence level classification."""

    def test_high_confidence_level(self, high_confidence_candidate):
        """Test high score gets HIGH level."""
        breakdown = calculate_score_breakdown(high_confidence_candidate)
        # Depending on score, check level
        if breakdown.total >= 80:
            assert breakdown.level == ConfidenceLevel.HIGH

    def test_low_confidence_level(self, low_confidence_candidate):
        """Test low score gets LOW or NOISE level."""
        breakdown = calculate_score_breakdown(low_confidence_candidate)
        assert breakdown.level in {ConfidenceLevel.LOW, ConfidenceLevel.NOISE}


class TestScoreCandidates:
    """Tests for batch scoring."""

    def test_score_multiple_candidates(
        self, high_confidence_candidate, low_confidence_candidate
    ):
        """Test scoring multiple candidates."""
        candidates = [high_confidence_candidate, low_confidence_candidate]
        scored = score_candidates(candidates)

        # All should have scores
        assert all(c.score >= 0 for c in scored)

        # Should be sorted by score descending
        assert scored[0].score >= scored[1].score


class TestFilterCandidates:
    """Tests for candidate filtering."""

    def test_filter_by_min_score(
        self, high_confidence_candidate, low_confidence_candidate
    ):
        """Test filtering by minimum score."""
        # Score them first
        score_candidates([high_confidence_candidate, low_confidence_candidate])

        candidates = [high_confidence_candidate, low_confidence_candidate]
        filtered = filter_candidates(candidates, min_score=50)

        # Only high-confidence should pass
        for c in filtered:
            assert c.score >= 50

    def test_filter_by_action(
        self, high_confidence_candidate, low_confidence_candidate
    ):
        """Test filtering by excluded actions."""
        score_candidates([high_confidence_candidate, low_confidence_candidate])

        candidates = [high_confidence_candidate, low_confidence_candidate]
        filtered = filter_candidates(candidates, exclude_actions={"MANUAL_REVIEW"})

        # Should exclude manual review candidates
        for c in filtered:
            assert c.recommended_action.value != "MANUAL_REVIEW"
