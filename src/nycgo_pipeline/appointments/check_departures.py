"""Check if current principal officers have departure records in CROL.

This module validates the golden dataset against City Record Online to identify
principal officers who may have already departed but whose records haven't been
updated in the golden dataset.

Note: CROL data has a lag of several months, so this check catches departures
that happened 3-6+ months ago, not recent ones.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from nycgo_pipeline.appointments.fetch_crol import (
    reset_rate_limiter,
    search_person,
)

logger = logging.getLogger(__name__)


@dataclass
class DepartureMatch:
    """A potential departure match from CROL."""

    # Golden dataset info
    record_id: str
    org_name: str
    principal_officer: str

    # CROL match info
    crol_name: str
    crol_agency: str
    crol_action: str
    crol_effective_date: datetime | None
    crol_title: str
    crol_url: str

    # Match quality
    name_confidence: float  # 0-1, how well names match
    agency_confidence: float  # 0-1, how well agency names match
    overall_confidence: float = 0.0

    def __post_init__(self):
        """Calculate overall confidence."""
        self.overall_confidence = (self.name_confidence + self.agency_confidence) / 2


@dataclass
class DepartureCheckResult:
    """Result of checking departures for a principal officer."""

    record_id: str
    org_name: str
    principal_officer: str
    checked: bool = True
    error: str | None = None
    matches: list[DepartureMatch] = field(default_factory=list)

    @property
    def has_departure(self) -> bool:
        """Whether a departure was found."""
        return len(self.matches) > 0

    @property
    def best_match(self) -> DepartureMatch | None:
        """Get the highest confidence match."""
        if not self.matches:
            return None
        return max(self.matches, key=lambda m: m.overall_confidence)


def load_principal_officers(golden_path: Path) -> pd.DataFrame:
    """Load principal officers from the golden dataset.

    Args:
        golden_path: Path to golden dataset CSV

    Returns:
        DataFrame with record_id, name, principal_officer_full_name columns
    """
    df = pd.read_csv(golden_path, dtype=str).fillna("")

    # Filter to records with principal officers
    df = df[df["principal_officer_full_name"].str.strip() != ""]

    # Select relevant columns
    columns = ["record_id", "name", "principal_officer_full_name"]
    if "organization_type" in df.columns:
        columns.append("organization_type")

    return df[columns].copy()


def normalize_name_for_search(name: str) -> str:
    """Normalize a name for CROL search.

    CROL search is fairly flexible, so we just need a clean version.
    """
    # Remove common suffixes/prefixes
    name = re.sub(r"\b(Jr\.?|Sr\.?|III|II|IV)\b", "", name, flags=re.IGNORECASE)
    # Remove extra whitespace
    name = " ".join(name.split())
    return name.strip()


def normalize_name_for_comparison(name: str) -> str:
    """Normalize a name for comparison matching.

    Converts to lowercase, removes punctuation, normalizes whitespace.
    """
    # Lowercase
    name = name.lower()
    # Remove punctuation
    name = re.sub(r"[.,'-]", " ", name)
    # Remove suffixes
    name = re.sub(r"\b(jr|sr|iii|ii|iv)\b", "", name)
    # Normalize whitespace
    name = " ".join(name.split())
    return name.strip()


def extract_name_parts(name: str) -> tuple[str, str, str]:
    """Extract first, middle, last name parts.

    Returns:
        Tuple of (first, middle, last)
    """
    name = normalize_name_for_comparison(name)
    parts = name.split()

    if len(parts) == 0:
        return ("", "", "")
    elif len(parts) == 1:
        return ("", "", parts[0])
    elif len(parts) == 2:
        return (parts[0], "", parts[1])
    else:
        return (parts[0], " ".join(parts[1:-1]), parts[-1])


def _score_last_name(last1: str, last2: str) -> float:
    """Score last name match (50% weight)."""
    if not last1 or not last2:
        return 0.0
    if last1 == last2:
        return 0.5
    if last1.startswith(last2) or last2.startswith(last1):
        return 0.3
    return 0.0


def _score_first_name(first1: str, first2: str) -> float:
    """Score first name match (40% weight)."""
    if not first1 or not first2:
        return 0.0
    if first1 == first2:
        return 0.4
    if first1.startswith(first2) or first2.startswith(first1):
        return 0.3
    if first1[0] == first2[0]:  # Initial match
        return 0.2
    return 0.0


def _score_middle_name(middle1: str, middle2: str) -> float:
    """Score middle name/initial match (10% weight)."""
    if not middle1 or not middle2:
        return 0.0
    if middle1 == middle2:
        return 0.1
    if middle1[0] == middle2[0]:
        return 0.05
    return 0.0


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names.

    Returns:
        Float 0-1 indicating match quality
    """
    n1 = normalize_name_for_comparison(name1)
    n2 = normalize_name_for_comparison(name2)

    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    first1, middle1, last1 = extract_name_parts(name1)
    first2, middle2, last2 = extract_name_parts(name2)

    score = (
        _score_last_name(last1, last2)
        + _score_first_name(first1, first2)
        + _score_middle_name(middle1, middle2)
    )
    return min(score, 1.0)


def calculate_agency_similarity(golden_org: str, crol_agency: str) -> float:
    """Calculate similarity between golden org name and CROL agency.

    CROL uses abbreviated agency names that differ from golden dataset names.

    Returns:
        Float 0-1 indicating match quality
    """
    if not golden_org or not crol_agency:
        return 0.0

    # Normalize both
    g = golden_org.lower()
    c = crol_agency.lower()

    # Direct containment
    if g in c or c in g:
        return 0.9

    # Common abbreviation mappings
    abbreviations = {
        "dept of info tech & telecomm": [
            "office of technology and innovation",
            "oti",
            "doitt",
        ],
        "admin for children's svcs": ["administration for children's services", "acs"],
        "dept of parks & recreation": ["parks", "department of parks"],
        "police department": ["nypd", "police"],
        "fire department": ["fdny", "fire"],
        "department of education": ["doe", "education"],
        "dept of environment protection": ["dep", "environmental protection"],
        "housing preservation & dvlpmnt": ["hpd", "housing preservation"],
        "dept of citywide admin services": ["dcas", "citywide administrative"],
        "dept of social services": ["dss", "social services", "hra"],
        "human resources administration": ["hra", "human resources"],
        "department of sanitation": ["dsny", "sanitation"],
        "department of buildings": ["dob", "buildings"],
        "department of correction": ["doc", "correction"],
        "department of health": ["dohmh", "health"],
        "taxi & limousine commission": ["tlc", "taxi"],
        "law department": ["law", "corporation counsel"],
        "office of the comptroller": ["comptroller"],
        "office of the mayor": ["mayor", "mayor's office"],
        "nyc employees retirement sys": ["nycers", "employees retirement"],
    }

    # Check abbreviation mappings
    for crol_pattern, golden_patterns in abbreviations.items():
        if crol_pattern in c:
            for gp in golden_patterns:
                if gp in g:
                    return 0.85

    # Word overlap
    g_words = set(g.split()) - {"of", "the", "and", "for", "&"}
    c_words = set(c.split()) - {"of", "the", "and", "for", "&", "dept", "department"}

    if g_words and c_words:
        overlap = len(g_words & c_words)
        total = len(g_words | c_words)
        if total > 0:
            return (overlap / total) * 0.7

    return 0.0


def check_officer_departure(
    record_id: str,
    org_name: str,
    principal_officer: str,
    use_cache: bool = True,
) -> DepartureCheckResult:
    """Check if a principal officer has a departure record in CROL.

    Args:
        record_id: Golden dataset record ID
        org_name: Organization name from golden dataset
        principal_officer: Principal officer name
        use_cache: Whether to use cached CROL results

    Returns:
        DepartureCheckResult with any matches found
    """
    result = DepartureCheckResult(
        record_id=record_id,
        org_name=org_name,
        principal_officer=principal_officer,
    )

    if not principal_officer or not principal_officer.strip():
        result.checked = False
        result.error = "No principal officer name"
        return result

    try:
        # Search CROL for this person
        search_name = normalize_name_for_search(principal_officer)
        notices = search_person(search_name, use_cache=use_cache)

        # Filter to departure notices
        departures = [
            n
            for n in notices
            if n.action_type.upper()
            in {"RESIGNED", "RETIRED", "TERMINATED", "DECEASED"}
        ]

        # Check each departure for relevance
        for notice in departures:
            name_sim = calculate_name_similarity(
                principal_officer, notice.employee_name
            )
            agency_sim = calculate_agency_similarity(org_name, notice.agency_name)

            # Only include if both name and agency have reasonable match
            if name_sim >= 0.6 and agency_sim >= 0.3:
                match = DepartureMatch(
                    record_id=record_id,
                    org_name=org_name,
                    principal_officer=principal_officer,
                    crol_name=notice.employee_name,
                    crol_agency=notice.agency_name,
                    crol_action=notice.action_type,
                    crol_effective_date=notice.effective_date,
                    crol_title=notice.employee_title,
                    crol_url=notice.url,
                    name_confidence=name_sim,
                    agency_confidence=agency_sim,
                )
                result.matches.append(match)

        # Sort matches by confidence
        result.matches.sort(key=lambda m: m.overall_confidence, reverse=True)

    except Exception as e:
        result.error = str(e)
        logger.warning(f"Error checking {principal_officer}: {e}")

    return result


def check_all_departures(
    golden_path: Path,
    use_cache: bool = True,
    org_types: set[str] | None = None,
) -> list[DepartureCheckResult]:
    """Check all principal officers for departure records.

    Args:
        golden_path: Path to golden dataset CSV
        use_cache: Whether to use cached CROL results
        org_types: Optional set of organization types to check
            (e.g., {"Mayoral Agency"})

    Returns:
        List of DepartureCheckResult for each officer checked
    """
    reset_rate_limiter()

    # Load principal officers
    df = load_principal_officers(golden_path)
    logger.info(f"Loaded {len(df)} records with principal officers")

    # Filter by org type if specified
    if org_types and "organization_type" in df.columns:
        df = df[df["organization_type"].isin(org_types)]
        logger.info(f"Filtered to {len(df)} records with org types: {org_types}")

    results = []

    for _, row in df.iterrows():
        record_id = row["record_id"]
        org_name = row["name"]
        principal_officer = row["principal_officer_full_name"]

        logger.info(f"Checking: {principal_officer} ({org_name})")

        result = check_officer_departure(
            record_id=record_id,
            org_name=org_name,
            principal_officer=principal_officer,
            use_cache=use_cache,
        )

        results.append(result)

        if result.has_departure:
            best = result.best_match
            date_str = (
                best.crol_effective_date.strftime("%Y-%m-%d")
                if best.crol_effective_date
                else "unknown"
            )
            logger.info(f"  FOUND DEPARTURE: {best.crol_action} on {date_str}")

    return results


def generate_departure_report(
    results: list[DepartureCheckResult],
    output_dir: Path,
) -> dict[str, Path]:
    """Generate reports from departure check results.

    Args:
        results: List of departure check results
        output_dir: Directory for output files

    Returns:
        Dictionary mapping format to output path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}

    # Filter to results with departures
    departures = [r for r in results if r.has_departure]
    checked = [r for r in results if r.checked]
    errors = [r for r in results if r.error]

    # Generate Markdown report
    md_path = output_dir / "departure_check_report.md"
    _generate_markdown_report(results, departures, checked, errors, md_path)
    outputs["markdown"] = md_path

    # Generate CSV of potential stale records
    csv_path = output_dir / "potential_stale_records.csv"
    _generate_csv_report(departures, csv_path)
    outputs["csv"] = csv_path

    logger.info(f"Generated departure reports in: {output_dir}")
    return outputs


def _generate_markdown_report(
    results: list[DepartureCheckResult],
    departures: list[DepartureCheckResult],
    checked: list[DepartureCheckResult],
    errors: list[DepartureCheckResult],
    output_path: Path,
) -> None:
    """Generate Markdown departure check report."""
    lines = [
        "# Principal Officer Departure Validation Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"- **Total Records Checked**: {len(checked)}",
        f"- **Potential Stale Records Found**: {len(departures)}",
        f"- **Errors**: {len(errors)}",
        "",
    ]

    if departures:
        lines.extend(
            [
                "## Potential Stale Records",
                "",
                "These principal officers have departure records in",
                "City Record Online, suggesting the golden dataset may need updating.",
                "",
            ]
        )

        for i, result in enumerate(departures, 1):
            best = result.best_match
            eff_date = (
                best.crol_effective_date.strftime("%Y-%m-%d")
                if best.crol_effective_date
                else "Unknown"
            )
            lines.extend(
                [
                    f"### {i}. {result.org_name}",
                    "",
                    f"- **Current Principal Officer**: {result.principal_officer}",
                    f"- **Record ID**: `{result.record_id}`",
                    "",
                    "**CROL Departure Record:**",
                    "",
                    f"- **Name**: {best.crol_name}",
                    f"- **Action**: {best.crol_action}",
                    f"- **Effective Date**: {eff_date}",
                    f"- **Agency**: {best.crol_agency}",
                    f"- **Title**: {best.crol_title}",
                    f"- **Confidence**: {best.overall_confidence:.0%}",
                    f"- **CROL URL**: {best.crol_url}",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "## Results",
                "",
                "No potential stale records found. All principal officers",
                "appear current based on available CROL data.",
                "",
                "*Note: CROL data has a lag of several months, so very",
                "recent departures may not yet be reflected.*",
                "",
            ]
        )

    if errors:
        lines.extend(
            [
                "## Errors",
                "",
                "The following records could not be checked:",
                "",
            ]
        )
        for result in errors:
            lines.append(f"- {result.org_name}: {result.error}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Generated by NYCGO Appointments Monitor*",
        ]
    )

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def _generate_csv_report(
    departures: list[DepartureCheckResult],
    output_path: Path,
) -> None:
    """Generate CSV of potential stale records."""
    fieldnames = [
        "record_id",
        "org_name",
        "current_principal_officer",
        "crol_name",
        "crol_action",
        "crol_effective_date",
        "crol_agency",
        "crol_title",
        "confidence",
        "crol_url",
    ]

    rows = []
    for result in departures:
        best = result.best_match
        if best:
            rows.append(
                {
                    "record_id": result.record_id,
                    "org_name": result.org_name,
                    "current_principal_officer": result.principal_officer,
                    "crol_name": best.crol_name,
                    "crol_action": best.crol_action,
                    "crol_effective_date": (
                        best.crol_effective_date.strftime("%Y-%m-%d")
                        if best.crol_effective_date
                        else ""
                    ),
                    "crol_agency": best.crol_agency,
                    "crol_title": best.crol_title,
                    "confidence": f"{best.overall_confidence:.0%}",
                    "crol_url": best.crol_url,
                }
            )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
