"""Organization and person matching logic for appointments monitoring."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

from nycgo_pipeline.appointments.normalize import (
    name_similarity,
    normalize_agency_name,
    normalize_name,
)

if TYPE_CHECKING:
    from nycgo_pipeline.appointments.fetch_open_data import PersonnelRecord

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of organization matches."""

    EXACT = "exact"
    ALTERNATE_NAME = "alternate_name"
    ACRONYM = "acronym"
    SOURCE_NAME = "source_name"
    FUZZY = "fuzzy"
    NONE = "none"


class RecommendedAction(Enum):
    """Recommended actions for matched candidates."""

    UPDATE_OFFICER = "UPDATE_OFFICER"
    ADD_OFFICER = "ADD_OFFICER"
    VERIFY_VACANCY = "VERIFY_VACANCY"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    VERIFY = "VERIFY"
    IGNORE = "IGNORE"


@dataclass
class OrgMatch:
    """A match between a personnel record and an NYCGO organization."""

    record_id: str
    org_name: str
    match_type: MatchType
    confidence: float
    matched_field: str = ""
    matched_value: str = ""


@dataclass
class Candidate:
    """A candidate for principal officer update."""

    # Identity
    candidate_id: str = ""

    # Personnel record info
    candidate_name: str = ""
    candidate_name_normalized: str = ""
    candidate_title_code: str | None = None
    effective_date: str | None = None
    reason_for_change: str | None = None
    agency_name_raw: str = ""

    # NYCGO match info
    nycgo_record_id: str | None = None
    nycgo_org_name: str = ""
    current_principal_officer: str = ""

    # Match details
    org_match: OrgMatch | None = None
    title_relevance: float = 0.5
    name_match_score: float = 0.0

    # Evidence
    sources: list[dict] = field(default_factory=list)

    # Classification
    score: int = 0
    recommended_action: RecommendedAction = RecommendedAction.MANUAL_REVIEW
    reviewer_notes: str = ""


# Source name columns in golden dataset
SOURCE_NAME_COLUMNS = [
    "name_nycgov_agency_list",
    "name_nycgov_mayors_office",
    "name_nyc_open_data_portal",
    "name_oda",
    "name_cpo",
    "name_wegov",
    "name_greenbook",
    "name_checkbook",
    "name_hoo",
    "name_ops",
]


def load_golden_dataset(path: str | None = None) -> pd.DataFrame:
    """Load the golden dataset for matching.

    Args:
        path: Optional explicit path, otherwise uses default location

    Returns:
        DataFrame with NYCGO organizations
    """
    if path is None:
        # Default to latest published dataset
        from pathlib import Path

        repo_root = Path(__file__).parent.parent.parent.parent
        path = (
            repo_root
            / "data"
            / "published"
            / "latest"
            / "NYCGO_golden_dataset_latest.csv"
        )

    logger.info(f"Loading golden dataset from: {path}")
    df = pd.read_csv(path, dtype=str).fillna("")
    logger.info(f"Loaded {len(df)} organizations")

    return df


def match_organization(  # noqa: C901
    agency_name: str,
    golden_df: pd.DataFrame,
) -> list[OrgMatch]:
    """Find NYCGO organizations matching an agency name.

    Args:
        agency_name: Agency name from personnel record
        golden_df: Golden dataset DataFrame

    Returns:
        List of OrgMatch objects, sorted by confidence (highest first)
    """
    matches: list[OrgMatch] = []
    agency_normalized = normalize_agency_name(agency_name)

    if not agency_normalized:
        return matches

    # 1. Exact match on primary name
    for _idx, row in golden_df.iterrows():
        name_normalized = normalize_agency_name(row.get("name", ""))
        if agency_normalized == name_normalized:
            matches.append(
                OrgMatch(
                    record_id=row.get("record_id", ""),
                    org_name=row.get("name", ""),
                    match_type=MatchType.EXACT,
                    confidence=1.0,
                    matched_field="name",
                    matched_value=row.get("name", ""),
                )
            )

    # 2. Match on alternate/former names
    for _idx, row in golden_df.iterrows():
        alt_names = row.get("alternate_or_former_names", "")
        if alt_names:
            for alt in alt_names.split(";"):
                alt_normalized = normalize_agency_name(alt.strip())
                if agency_normalized == alt_normalized:
                    # Check if we already have this org
                    record_id = row.get("record_id", "")
                    if not any(m.record_id == record_id for m in matches):
                        matches.append(
                            OrgMatch(
                                record_id=record_id,
                                org_name=row.get("name", ""),
                                match_type=MatchType.ALTERNATE_NAME,
                                confidence=0.9,
                                matched_field="alternate_or_former_names",
                                matched_value=alt.strip(),
                            )
                        )

    # 3. Match on acronym
    for _idx, row in golden_df.iterrows():
        acronym = row.get("acronym", "").strip().lower()
        if acronym and agency_normalized == acronym:
            record_id = row.get("record_id", "")
            if not any(m.record_id == record_id for m in matches):
                matches.append(
                    OrgMatch(
                        record_id=record_id,
                        org_name=row.get("name", ""),
                        match_type=MatchType.ACRONYM,
                        confidence=0.85,
                        matched_field="acronym",
                        matched_value=row.get("acronym", ""),
                    )
                )

    # 4. Match on source name columns
    for col in SOURCE_NAME_COLUMNS:
        if col not in golden_df.columns:
            continue
        for _idx, row in golden_df.iterrows():
            source_name = row.get(col, "")
            if source_name:
                source_normalized = normalize_agency_name(source_name)
                if agency_normalized == source_normalized:
                    record_id = row.get("record_id", "")
                    if not any(m.record_id == record_id for m in matches):
                        matches.append(
                            OrgMatch(
                                record_id=record_id,
                                org_name=row.get("name", ""),
                                match_type=MatchType.SOURCE_NAME,
                                confidence=0.8,
                                matched_field=col,
                                matched_value=source_name,
                            )
                        )

    # 5. Fuzzy matching (token overlap)
    if not matches:
        for _idx, row in golden_df.iterrows():
            name_normalized = normalize_agency_name(row.get("name", ""))
            similarity = _token_similarity(agency_normalized, name_normalized)
            if similarity >= 0.7:
                record_id = row.get("record_id", "")
                if not any(m.record_id == record_id for m in matches):
                    matches.append(
                        OrgMatch(
                            record_id=record_id,
                            org_name=row.get("name", ""),
                            match_type=MatchType.FUZZY,
                            confidence=similarity * 0.7,  # Cap at 0.7
                            matched_field="name",
                            matched_value=row.get("name", ""),
                        )
                    )

    # Sort by confidence
    matches.sort(key=lambda m: m.confidence, reverse=True)

    return matches


def _token_similarity(text1: str, text2: str) -> float:
    """Calculate token overlap similarity between two strings."""
    if not text1 or not text2:
        return 0.0

    tokens1 = set(text1.split())
    tokens2 = set(text2.split())

    # Remove common stopwords
    stopwords = {"the", "of", "and", "for", "in", "on", "at", "to", "a", "an"}
    tokens1 = tokens1 - stopwords
    tokens2 = tokens2 - stopwords

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def match_organizations(
    records: list[PersonnelRecord],
    golden_df: pd.DataFrame,
) -> list[Candidate]:
    """Match personnel records to NYCGO organizations.

    Args:
        records: List of personnel records from Open Data
        golden_df: Golden dataset DataFrame

    Returns:
        List of Candidate objects with match information
    """
    candidates: list[Candidate] = []

    for i, record in enumerate(records):
        # Normalize the name from the record
        normalized_name = normalize_name(record.employee_name or "")

        # Find matching organizations
        org_matches = match_organization(record.agency_name, golden_df)

        if org_matches:
            # Use best match
            best_match = org_matches[0]

            # Get current officer from golden dataset
            org_row = golden_df[golden_df["record_id"] == best_match.record_id]
            current_officer = ""
            if not org_row.empty:
                current_officer = org_row.iloc[0].get("principal_officer_full_name", "")

            # Calculate name match if there's a current officer
            name_match_score = 0.0
            if current_officer:
                name_match_score = name_similarity(
                    normalized_name.full, current_officer
                )

            candidate = Candidate(
                candidate_id=f"APPT_{i:04d}",
                candidate_name=record.employee_name or "",
                candidate_name_normalized=normalized_name.full,
                candidate_title_code=record.title_code,
                effective_date=(
                    record.effective_date.isoformat() if record.effective_date else None
                ),
                reason_for_change=record.reason_for_change,
                agency_name_raw=record.agency_name,
                nycgo_record_id=best_match.record_id,
                nycgo_org_name=best_match.org_name,
                current_principal_officer=current_officer,
                org_match=best_match,
                name_match_score=name_match_score,
                sources=[
                    {
                        "type": "open_data",
                        "dataset_id": "wq4v-8hyb",
                        "raw_record": record.raw_record,
                    }
                ],
            )

            # Determine recommended action
            candidate.recommended_action = _determine_action(candidate)
            candidates.append(candidate)

        else:
            # No org match found
            candidate = Candidate(
                candidate_id=f"APPT_{i:04d}",
                candidate_name=record.employee_name or "",
                candidate_name_normalized=normalized_name.full,
                candidate_title_code=record.title_code,
                effective_date=(
                    record.effective_date.isoformat() if record.effective_date else None
                ),
                reason_for_change=record.reason_for_change,
                agency_name_raw=record.agency_name,
                sources=[
                    {
                        "type": "open_data",
                        "dataset_id": "wq4v-8hyb",
                        "raw_record": record.raw_record,
                    }
                ],
                recommended_action=RecommendedAction.MANUAL_REVIEW,
                reviewer_notes=f"No organization match found for: {record.agency_name}",
            )
            candidates.append(candidate)

    logger.info(
        f"Matched {len(candidates)} candidates, "
        f"{sum(1 for c in candidates if c.nycgo_record_id)} with org matches"
    )

    return candidates


def _determine_action(candidate: Candidate) -> RecommendedAction:
    """Determine the recommended action for a candidate."""
    # Check if it's likely the same person (no change needed)
    if candidate.name_match_score > 0.85:
        return RecommendedAction.IGNORE

    # Check reason for change
    reason = (candidate.reason_for_change or "").upper()

    if reason in {"RETIRED", "RESIGNED", "TERMINATED", "DECEASED"}:
        # This is a separation - may indicate vacancy
        if candidate.name_match_score > 0.5:
            # Person leaving matches current officer
            return RecommendedAction.VERIFY_VACANCY
        else:
            return RecommendedAction.VERIFY

    if reason in {"APPOINTED", "PROMOTED", "REASSIGNED"}:
        # This is an appointment
        if candidate.current_principal_officer:
            return RecommendedAction.UPDATE_OFFICER
        else:
            return RecommendedAction.ADD_OFFICER

    # Unknown reason
    return RecommendedAction.MANUAL_REVIEW
