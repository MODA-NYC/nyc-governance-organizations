"""Confidence scoring for appointment candidates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from nycgo_pipeline.appointments.normalize import get_title_relevance

if TYPE_CHECKING:
    from nycgo_pipeline.appointments.match import Candidate


logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level classifications."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOISE = "NOISE"


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of confidence score components."""

    org_match_score: float = 0.0
    title_relevance_score: float = 0.0
    name_differentiation_score: float = 0.0
    recency_score: float = 0.0
    evidence_score: float = 0.0
    total: int = 0
    level: ConfidenceLevel = ConfidenceLevel.NOISE

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "org_match": self.org_match_score,
            "title_relevance": self.title_relevance_score,
            "name_differentiation": self.name_differentiation_score,
            "recency": self.recency_score,
            "evidence": self.evidence_score,
            "total": self.total,
            "level": self.level.value,
        }


# Score component weights (max points)
MAX_ORG_MATCH = 40
MAX_TITLE_RELEVANCE = 20
MAX_NAME_DIFF = 25
MAX_RECENCY = 10
MAX_EVIDENCE = 5


def calculate_score(candidate: Candidate) -> int:
    """Calculate confidence score for a candidate.

    Score range: 0-100
    Components:
    - Organization match quality: 0-40 points
    - Title relevance: 0-20 points
    - Name differentiation: 0-25 points
    - Recency bonus: 0-10 points
    - Evidence count: 0-5 points

    Args:
        candidate: Candidate object with match information

    Returns:
        Confidence score (0-100)
    """
    breakdown = calculate_score_breakdown(candidate)
    candidate.score = breakdown.total
    return breakdown.total


def calculate_score_breakdown(candidate: Candidate) -> ScoreBreakdown:
    """Calculate detailed score breakdown for a candidate.

    Args:
        candidate: Candidate object with match information

    Returns:
        ScoreBreakdown with component scores
    """
    breakdown = ScoreBreakdown()

    # 1. Organization match quality (0-40 points)
    if candidate.org_match:
        breakdown.org_match_score = candidate.org_match.confidence * MAX_ORG_MATCH
    else:
        breakdown.org_match_score = 0.0

    # 2. Title relevance (0-20 points)
    candidate.title_relevance = get_title_relevance(candidate.candidate_title_code)
    breakdown.title_relevance_score = candidate.title_relevance * MAX_TITLE_RELEVANCE

    # 3. Name differentiation (0-25 points)
    # We want DIFFERENT names (new person), so penalize similar names
    breakdown.name_differentiation_score = _calculate_name_diff_score(candidate)

    # 4. Recency bonus (0-10 points)
    breakdown.recency_score = _calculate_recency_score(candidate)

    # 5. Evidence count (0-5 points)
    breakdown.evidence_score = _calculate_evidence_score(candidate)

    # Calculate total
    raw_total = (
        breakdown.org_match_score
        + breakdown.title_relevance_score
        + breakdown.name_differentiation_score
        + breakdown.recency_score
        + breakdown.evidence_score
    )

    breakdown.total = max(0, min(100, round(raw_total)))
    breakdown.level = _classify_score(breakdown.total)

    return breakdown


def _calculate_name_diff_score(candidate: Candidate) -> float:
    """Calculate name differentiation score.

    Higher score = more likely to be a different person.
    """

    # If no current officer, this is an ADD action - full points
    if not candidate.current_principal_officer:
        return MAX_NAME_DIFF

    # If this is a separation record (retirement/resignation), different logic
    reason = (candidate.reason_for_change or "").upper()
    if reason in {"RETIRED", "RESIGNED", "TERMINATED", "DECEASED"}:
        # For separations, high similarity is GOOD (confirms right person leaving)
        if candidate.name_match_score > 0.8:
            return MAX_NAME_DIFF * 0.8  # Good - confirms vacancy
        else:
            return MAX_NAME_DIFF * 0.3  # Less certain

    # For appointments, we want different names
    if candidate.name_match_score > 0.9:
        # Very similar names - likely same person, not a change
        return 0.0
    elif candidate.name_match_score > 0.7:
        # Somewhat similar - might be same person
        return MAX_NAME_DIFF * 0.3
    elif candidate.name_match_score > 0.5:
        # Moderately different
        return MAX_NAME_DIFF * 0.6
    else:
        # Very different - likely a new person
        return MAX_NAME_DIFF


def _calculate_recency_score(candidate: Candidate) -> float:
    """Calculate recency bonus score."""
    if not candidate.effective_date:
        return MAX_RECENCY * 0.5  # Unknown date, middle score

    try:
        effective = datetime.fromisoformat(candidate.effective_date)
        days_old = (datetime.now() - effective).days

        if days_old < 0:
            # Future date - might be planned appointment
            return MAX_RECENCY * 0.8
        elif days_old <= 7:
            return MAX_RECENCY
        elif days_old <= 14:
            return MAX_RECENCY * 0.8
        elif days_old <= 30:
            return MAX_RECENCY * 0.5
        elif days_old <= 60:
            return MAX_RECENCY * 0.3
        else:
            return MAX_RECENCY * 0.1

    except (ValueError, TypeError):
        return MAX_RECENCY * 0.5


def _calculate_evidence_score(candidate: Candidate) -> float:
    """Calculate evidence count score."""
    num_sources = len(candidate.sources)

    if num_sources >= 3:
        return MAX_EVIDENCE
    elif num_sources == 2:
        return MAX_EVIDENCE * 0.8
    elif num_sources == 1:
        return MAX_EVIDENCE * 0.5
    else:
        return 0.0


def _classify_score(score: int) -> ConfidenceLevel:
    """Classify score into confidence level."""
    if score >= 80:
        return ConfidenceLevel.HIGH
    elif score >= 50:
        return ConfidenceLevel.MEDIUM
    elif score >= 20:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.NOISE


def score_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Score all candidates and sort by score.

    Args:
        candidates: List of candidates to score

    Returns:
        Candidates sorted by score (highest first)
    """
    for candidate in candidates:
        calculate_score(candidate)

    # Sort by score descending
    candidates.sort(key=lambda c: c.score, reverse=True)

    # Log summary
    high = sum(1 for c in candidates if c.score >= 80)
    medium = sum(1 for c in candidates if 50 <= c.score < 80)
    low = sum(1 for c in candidates if 20 <= c.score < 50)
    noise = sum(1 for c in candidates if c.score < 20)

    logger.info(
        f"Scored {len(candidates)} candidates: "
        f"HIGH={high}, MEDIUM={medium}, LOW={low}, NOISE={noise}"
    )

    return candidates


def filter_candidates(
    candidates: list[Candidate],
    min_score: int = 0,
    exclude_actions: set[str] | None = None,
) -> list[Candidate]:
    """Filter candidates by score and action.

    Args:
        candidates: List of candidates to filter
        min_score: Minimum score to include
        exclude_actions: Actions to exclude (e.g., {"IGNORE", "NOISE"})

    Returns:
        Filtered list of candidates
    """
    if exclude_actions is None:
        exclude_actions = set()

    filtered = [
        c
        for c in candidates
        if c.score >= min_score and c.recommended_action.value not in exclude_actions
    ]

    logger.info(
        f"Filtered {len(candidates)} to {len(filtered)} candidates "
        f"(min_score={min_score})"
    )

    return filtered
