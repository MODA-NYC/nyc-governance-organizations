"""Report generation for appointments monitoring."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nycgo_pipeline.appointments.match import Candidate

logger = logging.getLogger(__name__)


def generate_reports(
    candidates: list[Candidate],
    output_dir: Path,
    scan_metadata: dict,
) -> dict[str, Path]:
    """Generate all report formats.

    Args:
        candidates: List of scored candidates
        output_dir: Directory for output files
        scan_metadata: Metadata about the scan

    Returns:
        Dictionary mapping format to output path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # Generate JSON report
    json_path = output_dir / "candidates.json"
    generate_json_report(candidates, json_path, scan_metadata)
    outputs["json"] = json_path

    # Generate CSV report (bulk upload compatible)
    csv_path = output_dir / "candidates.csv"
    generate_csv_report(candidates, csv_path)
    outputs["csv"] = csv_path

    # Generate Markdown summary
    md_path = output_dir / "candidates_summary.md"
    generate_markdown_report(candidates, md_path, scan_metadata)
    outputs["markdown"] = md_path

    logger.info(f"Generated reports in: {output_dir}")
    return outputs


def generate_json_report(
    candidates: list[Candidate],
    output_path: Path,
    scan_metadata: dict,
) -> None:
    """Generate detailed JSON report.

    Args:
        candidates: List of scored candidates
        output_path: Path to output file
        scan_metadata: Metadata about the scan
    """
    from nycgo_pipeline.appointments.score import calculate_score_breakdown

    report = {
        "scan_metadata": {
            **scan_metadata,
            "generated_at": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "high_confidence": sum(1 for c in candidates if c.score >= 80),
            "medium_confidence": sum(1 for c in candidates if 50 <= c.score < 80),
            "low_confidence": sum(1 for c in candidates if c.score < 50),
        },
        "candidates": [],
    }

    for candidate in candidates:
        breakdown = calculate_score_breakdown(candidate)

        candidate_data = {
            "candidate_id": candidate.candidate_id,
            "nycgo_record_id": candidate.nycgo_record_id,
            "nycgo_org_name": candidate.nycgo_org_name,
            "current_principal_officer": candidate.current_principal_officer,
            "candidate_name": candidate.candidate_name,
            "candidate_name_normalized": candidate.candidate_name_normalized,
            "candidate_title_code": candidate.candidate_title_code,
            "effective_date": candidate.effective_date,
            "reason_for_change": candidate.reason_for_change,
            "agency_name_raw": candidate.agency_name_raw,
            "sources": candidate.sources,
            "match_details": {
                "org_match_type": (
                    candidate.org_match.match_type.value
                    if candidate.org_match
                    else None
                ),
                "org_match_confidence": (
                    candidate.org_match.confidence if candidate.org_match else 0.0
                ),
                "org_matched_field": (
                    candidate.org_match.matched_field if candidate.org_match else None
                ),
                "org_matched_value": (
                    candidate.org_match.matched_value if candidate.org_match else None
                ),
                "title_relevance": candidate.title_relevance,
                "name_match_score": candidate.name_match_score,
            },
            "score": candidate.score,
            "score_breakdown": breakdown.to_dict(),
            "recommended_action": candidate.recommended_action.value,
            "reviewer_notes": candidate.reviewer_notes,
        }

        report["candidates"].append(candidate_data)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Generated JSON report: {output_path}")


def generate_csv_report(
    candidates: list[Candidate],
    output_path: Path,
    min_score: int = 50,
) -> None:
    """Generate CSV report compatible with bulk upload workflow.

    Only includes candidates with score >= min_score and actionable recommendations.

    CSV format:
    record_id,record_name,field_name,action,justification,evidence_url

    Args:
        candidates: List of scored candidates
        output_path: Path to output file
        min_score: Minimum score to include
    """
    from nycgo_pipeline.appointments.match import RecommendedAction

    # Filter to actionable candidates
    actionable = [
        c
        for c in candidates
        if c.score >= min_score
        and c.nycgo_record_id
        and c.recommended_action
        in {RecommendedAction.UPDATE_OFFICER, RecommendedAction.ADD_OFFICER}
    ]

    rows = []

    for candidate in actionable:
        # Build justification
        justification = (
            f"{candidate.reason_for_change or 'Appointment'} of "
            f"{candidate.candidate_name_normalized} "
            f"per City Record {candidate.effective_date or 'unknown date'} "
            f"(confidence: {candidate.score}%)"
        )

        # Build evidence URL
        evidence_url = "https://data.cityofnewyork.us/resource/wq4v-8hyb.json"

        # Principal officer full name
        if candidate.candidate_name_normalized:
            rows.append(
                {
                    "record_id": candidate.nycgo_record_id,
                    "record_name": candidate.nycgo_org_name,
                    "field_name": "principal_officer_full_name",
                    "action": "direct_set",
                    "justification": justification,
                    "evidence_url": evidence_url,
                }
            )

    # Write CSV
    fieldnames = [
        "record_id",
        "record_name",
        "field_name",
        "action",
        "justification",
        "evidence_url",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Generated CSV report with {len(rows)} rows: {output_path}")


def generate_markdown_report(
    candidates: list[Candidate],
    output_path: Path,
    scan_metadata: dict,
) -> None:
    """Generate human-readable Markdown summary.

    Args:
        candidates: List of scored candidates
        output_path: Path to output file
        scan_metadata: Metadata about the scan
    """

    high_conf = [c for c in candidates if c.score >= 80]
    medium_conf = [c for c in candidates if 50 <= c.score < 80]
    low_conf = [c for c in candidates if 20 <= c.score < 50]

    lines = [
        "# Appointments Monitor Scan Report",
        "",
        f"**Scan Date**: {scan_metadata.get('scan_date', 'Unknown')}",
        f"**Period**: {scan_metadata.get('start_date', 'Unknown')} to "
        f"{scan_metadata.get('end_date', 'Unknown')}",
        f"**Golden Dataset Version**: {scan_metadata.get('golden_version', 'Unknown')}",
        "",
        "## Summary",
        "",
        f"- **Records Scanned**: {scan_metadata.get('records_scanned', 0)}",
        f"- **Candidates Found**: {len(candidates)}",
        f"- **High Confidence (80+)**: {len(high_conf)}",
        f"- **Medium Confidence (50-79)**: {len(medium_conf)}",
        f"- **Low Confidence (<50)**: {len(low_conf)}",
        "",
    ]

    if high_conf:
        lines.extend(["## High Confidence Candidates", ""])
        for i, c in enumerate(high_conf, 1):
            lines.extend(_format_candidate_md(i, c))

    if medium_conf:
        lines.extend(["## Medium Confidence Candidates", ""])
        for i, c in enumerate(medium_conf, 1):
            lines.extend(_format_candidate_md(i, c))

    if low_conf:
        lines.extend(["## Low Confidence Candidates", ""])
        lines.append(
            f"*{len(low_conf)} candidates with score < 50 - likely false positives*"
        )
        lines.append("")
        lines.append("| Organization | Candidate | Score | Action |")
        lines.append("|--------------|-----------|-------|--------|")
        for c in low_conf[:10]:  # Limit to first 10
            org = c.nycgo_org_name or c.agency_name_raw
            name = c.candidate_name_normalized
            action = c.recommended_action.value
            lines.append(f"| {org} | {name} | {c.score} | {action} |")
        if len(low_conf) > 10:
            lines.append(f"| ... | *{len(low_conf) - 10} more* | ... | ... |")
        lines.append("")

    lines.extend(
        [
            "## Next Steps",
            "",
            "1. Review high-confidence candidates in admin UI",
            "2. Verify medium-confidence candidates with secondary sources",
            "3. Import approved candidates via `candidates.csv` using bulk upload",
            "4. Discard low-confidence candidates or investigate further",
            "",
            "---",
            "",
            "*Generated by NYCGO Appointments Monitor*",
        ]
    )

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated Markdown report: {output_path}")


def _format_candidate_md(index: int, candidate: Candidate) -> list[str]:
    """Format a single candidate as Markdown."""
    lines = [
        f"### {index}. {candidate.nycgo_org_name or candidate.agency_name_raw}",
        "",
        f"- **Candidate**: {candidate.candidate_name_normalized}",
        f"- **Effective Date**: {candidate.effective_date or 'Unknown'}",
        f"- **Reason**: {candidate.reason_for_change or 'Unknown'}",
        f"- **Current Officer**: {candidate.current_principal_officer or 'None'}",
        f"- **Score**: {candidate.score}/100",
        f"- **Action**: {candidate.recommended_action.value}",
    ]

    if candidate.org_match:
        lines.append(
            f"- **Match Type**: {candidate.org_match.match_type.value} "
            f"(confidence: {candidate.org_match.confidence:.0%})"
        )

    if candidate.reviewer_notes:
        lines.append(f"- **Notes**: {candidate.reviewer_notes}")

    lines.append("")
    return lines
