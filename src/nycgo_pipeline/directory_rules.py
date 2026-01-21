"""
NYC.gov Agency Directory Eligibility Rules

This module is the SINGLE SOURCE OF TRUTH for directory eligibility logic.
Rules defined here are used for:
1. Evaluating record eligibility (True/False)
2. Generating reasoning strings (for golden dataset and UI)
3. Generating documentation (docs/DIRECTORY_LOGIC.md)

IMPORTANT: After changing rules, regenerate documentation:
    python scripts/generate_directory_docs.py --changed-by "your_username"

See docs/ARCHITECTURE_DIRECTORY_LOGIC.md for full architecture explanation.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Rule:
    """A single eligibility rule."""

    name: str
    description: str  # Human-readable, shown in UI and docs
    check: Callable[[dict], bool]
    category: str  # "gatekeeper", "type_specific", "exemption", "override"
    details_on_match: Callable[[dict], str] | None = None  # For specific match info


# =============================================================================
# EXEMPTION LISTS
# =============================================================================

NONPROFIT_EXEMPTIONS = [
    "Brooklyn Public Library",
    "New York City Tourism + Conventions",
    "New York Public Library",
    "Queens Public Library",
    "Gracie Mansion Conservancy",
    "Mayor's Fund to Advance New York City",
]

ADVISORY_EXEMPTIONS = [
    "Board of Elections",
    "Campaign Finance Board",
    "Rent Guidelines Board",
]

PUBLISHED_EXPORT_EXCEPTIONS = [
    ("NYC_GOID_000354", "Office of Collective Bargaining"),
    ("NYC_GOID_000476", "MTA (Metropolitan Transportation Authority)"),
    ("NYC_GOID_100030", "Office of Digital Assets and Blockchain"),
]

# Manual overrides (empty by default)
MANUAL_OVERRIDE_TRUE: list[str] = []
MANUAL_OVERRIDE_FALSE: list[str] = []

# Pension Fund allowlist - only these Comptroller-administered city employee
# pension funds are included in the directory. Other pension funds (e.g.,
# Cultural Institutions Retirement System) serve non-city employees and are excluded.
PENSION_FUND_ALLOWLIST = [
    "Board of Education Retirement System",
    "Fire Department Pension Fund and Related Funds",
    "New York City Employee Retirement System",
    "New York City Police Pension Fund",
    "Teachers' Retirement System of City of New York",
]

# State Government Agency exemptions (bypass the no_state_nygov_url gatekeeper)
# These are NYC-affiliated state agencies that should be included even if they
# have .ny.gov URLs (though currently none of them do)
STATE_GOVERNMENT_EXEMPTIONS = [
    "Bronx County Public Administrator",
    "City University of New York",
    "Kings County Public Administrator",
    "New York County Public Administrator",
    "Public Administrator of Queens County",
    "Richmond County Public Administrator",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def is_state_nygov_url(url: str) -> bool:
    """Check if URL is state .ny.gov (not city .nyc.gov)."""
    if not url:
        return False
    has_ny_gov = bool(re.search(r"\.ny\.gov", url, re.IGNORECASE))
    has_nyc_gov = bool(re.search(r"\.nyc\.gov", url, re.IGNORECASE))
    return has_ny_gov and not has_nyc_gov


def has_main_nyc_gov_url(url: str) -> bool:
    """Check if URL is a main nyc.gov page (contains index.page)."""
    if not url:
        return False
    return bool(
        re.search(r"nyc\.gov", url, re.IGNORECASE)
        and re.search(r"index\.page", url, re.IGNORECASE)
    )


def _is_truthy(value: str) -> bool:
    """Check if a string value represents a truthy boolean."""
    return str(value).strip().lower() in ("true", "1", "t", "yes")


# =============================================================================
# GATEKEEPER RULES (all must pass)
# =============================================================================

GATEKEEPER_RULES = [
    Rule(
        name="active_status",
        description="OperationalStatus must be 'Active'",
        check=lambda r: str(r.get("operational_status", "")).strip().lower()
        == "active",
        category="gatekeeper",
    ),
    Rule(
        name="no_state_nygov_url",
        description="URL must not be state .ny.gov (city .nyc.gov is OK)",
        check=lambda r: not is_state_nygov_url(str(r.get("url", ""))),
        category="gatekeeper",
    ),
    Rule(
        name="has_contact_info",
        description="Must have: URL, principal officer name, or officer contact URL",
        check=lambda r: bool(
            str(r.get("url", "")).strip()
            or str(r.get("principal_officer_full_name", "")).strip()
            or str(r.get("principal_officer_contact_url", "")).strip()
        ),
        category="gatekeeper",
    ),
]


# =============================================================================
# TYPE-SPECIFIC RULES (at least one must pass, after gatekeepers)
# =============================================================================

TYPE_SPECIFIC_RULES = [
    Rule(
        name="mayoral_agency",
        description="Mayoral Agency: always included",
        check=lambda r: r.get("organization_type") == "Mayoral Agency",
        category="type_specific",
    ),
    Rule(
        name="mayoral_office",
        description="Mayoral Office: always included",
        check=lambda r: r.get("organization_type") == "Mayoral Office",
        category="type_specific",
    ),
    Rule(
        name="elected_office",
        description="Elected Office: always included",
        check=lambda r: r.get("organization_type") == "Elected Office",
        category="type_specific",
    ),
    Rule(
        name="pension_fund",
        description="Pension Fund: included if on allowlist (city employee funds)",
        check=lambda r: (
            r.get("organization_type") == "Pension Fund"
            and r.get("name") in PENSION_FUND_ALLOWLIST
        ),
        category="type_specific",
        details_on_match=lambda r: f"Allowlist: {r.get('name')}",
    ),
    Rule(
        name="state_government_agency",
        description="State Government Agency: always included",
        check=lambda r: r.get("organization_type") == "State Government Agency",
        category="type_specific",
    ),
    Rule(
        name="division_in_org_chart",
        description="Division: included if in Org Chart",
        check=lambda r: (
            r.get("organization_type") == "Division"
            and _is_truthy(r.get("in_org_chart", ""))
        ),
        category="type_specific",
        details_on_match=lambda r: "In Org Chart",
    ),
    Rule(
        name="public_benefit_in_org_chart",
        description="Public Benefit or Development Org: included if in Org Chart",
        check=lambda r: (
            r.get("organization_type") == "Public Benefit or Development Organization"
            and _is_truthy(r.get("in_org_chart", ""))
        ),
        category="type_specific",
        details_on_match=lambda r: "In Org Chart",
    ),
    Rule(
        name="nonprofit_in_org_chart_or_exemption",
        description="Nonprofit Organization: included if in Org Chart OR exemption",
        check=lambda r: (
            r.get("organization_type") == "Nonprofit Organization"
            and (
                _is_truthy(r.get("in_org_chart", ""))
                or r.get("name") in NONPROFIT_EXEMPTIONS
            )
        ),
        category="type_specific",
        details_on_match=lambda r: (
            f"Exemption: {r.get('name')}"
            if r.get("name") in NONPROFIT_EXEMPTIONS
            else "In Org Chart"
        ),
    ),
    Rule(
        name="advisory_in_org_chart_or_url_or_exemption",
        description="Advisory/Regulatory Org: Org Chart, main nyc.gov URL, or exempt",
        check=lambda r: (
            r.get("organization_type") == "Advisory or Regulatory Organization"
            and (
                _is_truthy(r.get("in_org_chart", ""))
                or has_main_nyc_gov_url(str(r.get("url", "")))
                or r.get("name") in ADVISORY_EXEMPTIONS
            )
        ),
        category="type_specific",
        details_on_match=lambda r: (
            f"Exemption: {r.get('name')}"
            if r.get("name") in ADVISORY_EXEMPTIONS
            else (
                "Has main nyc.gov URL"
                if has_main_nyc_gov_url(str(r.get("url", "")))
                else "In Org Chart"
            )
        ),
    ),
]


# =============================================================================
# EVALUATION ENGINE
# =============================================================================


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_name: str
    description: str
    passed: bool
    category: str
    details: str | None = None


@dataclass
class EligibilityResult:
    """Complete eligibility evaluation result."""

    eligible: bool
    reasoning: str  # Human-readable summary
    reasoning_detailed: str  # Full details for debugging/audit
    rule_results: list[RuleResult]


def evaluate_eligibility(record: dict) -> EligibilityResult:
    """
    Evaluate a record's eligibility for NYC.gov Agency Directory.

    Returns eligibility status AND detailed reasoning.
    """
    results: list[RuleResult] = []

    # Check manual overrides first
    record_id = record.get("record_id", "")
    if record_id in MANUAL_OVERRIDE_TRUE:
        return EligibilityResult(
            eligible=True,
            reasoning="Manual override: forced TRUE",
            reasoning_detailed="Manual override: forced TRUE",
            rule_results=[],
        )
    if record_id in MANUAL_OVERRIDE_FALSE:
        return EligibilityResult(
            eligible=False,
            reasoning="Manual override: forced FALSE",
            reasoning_detailed="Manual override: forced FALSE",
            rule_results=[],
        )

    # Evaluate gatekeeper rules
    for rule in GATEKEEPER_RULES:
        passed = rule.check(record)
        details = None
        if passed and rule.details_on_match:
            details = rule.details_on_match(record)
        results.append(
            RuleResult(
                rule_name=rule.name,
                description=rule.description,
                passed=passed,
                category=rule.category,
                details=details,
            )
        )

    # Check if all gatekeepers passed
    gatekeeper_results = [r for r in results if r.category == "gatekeeper"]
    all_gatekeepers_passed = all(r.passed for r in gatekeeper_results)

    if not all_gatekeepers_passed:
        # Failed gatekeepers - not eligible
        reasoning = format_reasoning(results, eligible=False)
        reasoning_detailed = format_reasoning_detailed(results)
        return EligibilityResult(
            eligible=False,
            reasoning=reasoning,
            reasoning_detailed=reasoning_detailed,
            rule_results=results,
        )

    # Evaluate type-specific rules
    for rule in TYPE_SPECIFIC_RULES:
        passed = rule.check(record)
        details = None
        if passed and rule.details_on_match:
            details = rule.details_on_match(record)
        results.append(
            RuleResult(
                rule_name=rule.name,
                description=rule.description,
                passed=passed,
                category=rule.category,
                details=details,
            )
        )

    # Check if any type-specific rule passed
    type_results = [r for r in results if r.category == "type_specific"]
    any_type_passed = any(r.passed for r in type_results)

    eligible = all_gatekeepers_passed and any_type_passed
    reasoning = format_reasoning(results, eligible=eligible)
    reasoning_detailed = format_reasoning_detailed(results)

    return EligibilityResult(
        eligible=eligible,
        reasoning=reasoning,
        reasoning_detailed=reasoning_detailed,
        rule_results=results,
    )


def format_reasoning(results: list[RuleResult], eligible: bool) -> str:
    """Format a concise reasoning string for display."""
    parts = []

    for r in results:
        if r.category == "gatekeeper":
            symbol = "\u2713" if r.passed else "\u2717"
            # Shorten description for display
            short_desc = (
                r.description.split(":")[0] if ":" in r.description else r.description
            )
            parts.append(f"{short_desc}: {symbol}")
        elif r.category == "type_specific" and r.passed:
            detail = f" ({r.details})" if r.details else ""
            type_name = (
                r.description.split(":")[0] if ":" in r.description else r.description
            )
            parts.append(f"{type_name}{detail}: \u2713")

    return " | ".join(parts)


def format_reasoning_detailed(results: list[RuleResult]) -> str:
    """Format detailed reasoning for audit/debugging."""
    lines = []

    lines.append("GATEKEEPER RULES (all must pass):")
    for r in results:
        if r.category == "gatekeeper":
            symbol = "\u2713" if r.passed else "\u2717"
            lines.append(f"  {symbol} {r.description}")

    lines.append("")
    lines.append("TYPE-SPECIFIC RULES (at least one must pass):")
    for r in results:
        if r.category == "type_specific":
            symbol = "\u2713" if r.passed else "\u2717"
            detail = f" [{r.details}]" if r.details else ""
            lines.append(f"  {symbol} {r.description}{detail}")

    return "\n".join(lines)
