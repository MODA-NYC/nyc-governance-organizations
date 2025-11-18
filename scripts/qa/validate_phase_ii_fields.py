#!/usr/bin/env python3
"""
Validate Phase II field population and quality.

Checks:
- authorizing_authority: 100% population target
- authorizing_url: 90%+ population target, valid URLs
- appointments_summary: Population for MOA entities
- org_chart_oversight: 80%+ population target, valid RecordID references

Usage:
    python scripts/qa/validate_phase_ii_fields.py

Input:
    - data/working/NYCGO_golden_dataset_v2.0.0-dev.csv

Output:
    - Validation report (console)
    - data/analysis/phase_ii_validation_report.csv
"""

import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "working" / "NYCGO_golden_dataset_v2.0.0-dev.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "analysis" / "phase_ii_validation_report.csv"

# Targets
AUTHORIZING_AUTHORITY_TARGET = 1.00  # 100%
AUTHORIZING_URL_TARGET = 0.90  # 90%
ORG_CHART_OVERSIGHT_TARGET = 0.80  # 80%


def validate_authorizing_authority(df: pd.DataFrame) -> dict:
    """Validate authorizing_authority field."""
    total = len(df)
    populated = df["authorizing_authority"].notna() & (
        df["authorizing_authority"].str.strip() != ""
    )
    count_populated = populated.sum()
    percentage = count_populated / total if total > 0 else 0

    issues = []
    for _idx, row in df[~populated].iterrows():
        issues.append(
            {
                "record_id": row["RecordID"],
                "name": row["Name"],
                "field": "authorizing_authority",
                "issue": "missing",
                "severity": "critical",
            }
        )

    return {
        "field": "authorizing_authority",
        "target": AUTHORIZING_AUTHORITY_TARGET,
        "count_populated": count_populated,
        "count_total": total,
        "percentage": percentage,
        "meets_target": percentage >= AUTHORIZING_AUTHORITY_TARGET,
        "issues": issues,
    }


def validate_url(url: str) -> tuple:
    """
    Validate URL format and accessibility.

    Returns:
        (is_valid_format, is_accessible, error_message)
    """
    if not url or not url.strip():
        return False, False, "Empty URL"

    # Check format
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, False, "Invalid URL format"
        if result.scheme not in ["http", "https"]:
            return False, False, f"Invalid scheme: {result.scheme}"
    except Exception as e:
        return False, False, f"Parse error: {str(e)}"

    # Check accessibility (optional, can be slow)
    # Uncomment to enable URL accessibility checking
    # try:
    #     response = requests.head(url, timeout=5, allow_redirects=True)
    #     if response.status_code >= 400:
    #         return True, False, f"HTTP {response.status_code}"
    # except Exception as e:
    #     return True, False, f"Connection error: {str(e)}"

    return True, True, None


def validate_authorizing_url(df: pd.DataFrame) -> dict:
    """Validate authorizing_url field."""
    total = len(df)
    populated = df["authorizing_url"].notna() & (
        df["authorizing_url"].str.strip() != ""
    )
    count_populated = populated.sum()
    percentage = count_populated / total if total > 0 else 0

    issues = []

    # Check missing URLs
    for _idx, row in df[~populated].iterrows():
        issues.append(
            {
                "record_id": row["RecordID"],
                "name": row["Name"],
                "field": "authorizing_url",
                "issue": "missing",
                "severity": "high" if percentage < AUTHORIZING_URL_TARGET else "medium",
            }
        )

    # Validate URL format for populated URLs
    for _idx, row in df[populated].iterrows():
        url = row["authorizing_url"]
        # Handle pipe-separated multiple URLs
        urls = [u.strip() for u in url.split("|") if u.strip()]
        for u in urls:
            is_valid, is_accessible, error = validate_url(u)
            if not is_valid:
                issues.append(
                    {
                        "record_id": row["RecordID"],
                        "name": row["Name"],
                        "field": "authorizing_url",
                        "issue": f"invalid_format: {error}",
                        "severity": "high",
                    }
                )

    return {
        "field": "authorizing_url",
        "target": AUTHORIZING_URL_TARGET,
        "count_populated": count_populated,
        "count_total": total,
        "percentage": percentage,
        "meets_target": percentage >= AUTHORIZING_URL_TARGET,
        "issues": issues,
    }


def validate_org_chart_oversight(df: pd.DataFrame) -> dict:
    """Validate org_chart_oversight field."""
    total = len(df)
    populated = df["org_chart_oversight"].notna() & (
        df["org_chart_oversight"].str.strip() != ""
    )
    count_populated = populated.sum()
    percentage = count_populated / total if total > 0 else 0

    # Get valid RecordIDs
    valid_record_ids = set(df["RecordID"])

    issues = []

    # Check missing values
    for _idx, row in df[~populated].iterrows():
        issues.append(
            {
                "record_id": row["RecordID"],
                "name": row["Name"],
                "field": "org_chart_oversight",
                "issue": "missing",
                "severity": (
                    "medium" if percentage < ORG_CHART_OVERSIGHT_TARGET else "low"
                ),
            }
        )

    # Validate RecordID references
    for _idx, row in df[populated].iterrows():
        oversight_id = row["org_chart_oversight"].strip()
        if oversight_id and oversight_id not in valid_record_ids:
            issues.append(
                {
                    "record_id": row["RecordID"],
                    "name": row["Name"],
                    "field": "org_chart_oversight",
                    "issue": f"invalid_record_id: {oversight_id} not found in dataset",
                    "severity": "high",
                }
            )

    return {
        "field": "org_chart_oversight",
        "target": ORG_CHART_OVERSIGHT_TARGET,
        "count_populated": count_populated,
        "count_total": total,
        "percentage": percentage,
        "meets_target": percentage >= ORG_CHART_OVERSIGHT_TARGET,
        "issues": issues,
    }


def validate_appointments_summary(
    df: pd.DataFrame, moa_crosswalk_file: Path = None
) -> dict:
    """Validate appointments_summary field."""
    # If we have MOA crosswalk, we can identify which entities should have this
    # For now, just check population percentage
    total = len(df)
    populated = df["appointments_summary"].notna() & (
        df["appointments_summary"].str.strip() != ""
    )
    count_populated = populated.sum()
    percentage = count_populated / total if total > 0 else 0

    issues = []

    # Check for very short summaries (likely incomplete)
    for _idx, row in df[populated].iterrows():
        summary = row["appointments_summary"]
        if len(summary.strip()) < 20:  # Arbitrary threshold
            issues.append(
                {
                    "record_id": row["RecordID"],
                    "name": row["Name"],
                    "field": "appointments_summary",
                    "issue": f'summary_too_short: "{summary[:50]}"',
                    "severity": "low",
                }
            )

    return {
        "field": "appointments_summary",
        "target": None,  # No fixed target - depends on MOA entity count
        "count_populated": count_populated,
        "count_total": total,
        "percentage": percentage,
        "meets_target": None,  # Cannot determine without MOA data
        "issues": issues,
    }


def print_validation_report(results: list):
    """Print validation report to console."""
    print("\n" + "=" * 70)
    print("  Phase II Field Validation Report")
    print("=" * 70)

    for result in results:
        field = result["field"]
        print(f"\n📊 {field.upper().replace('_', ' ')}")
        print("─" * 70)
        populated_str = f"{result['count_populated']}/{result['count_total']}"
        percentage_str = f"({result['percentage']:.1%})"
        print(f"  Populated: {populated_str} {percentage_str}")

        if result["target"]:
            print(f"  Target: {result['target']:.0%}")
            status = "✅ PASS" if result["meets_target"] else "❌ FAIL"
            print(f"  Status: {status}")

        # Issue summary
        if result["issues"]:
            issues_by_severity = {}
            for issue in result["issues"]:
                severity = issue["severity"]
                issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1

            print(f"\n  Issues: {len(result['issues'])} total")
            for severity in ["critical", "high", "medium", "low"]:
                count = issues_by_severity.get(severity, 0)
                if count > 0:
                    print(f"    - {severity.capitalize()}: {count}")

    print("\n" + "=" * 70)

    # Overall summary
    total_issues = sum(len(r["issues"]) for r in results)
    critical_issues = sum(
        len([i for i in r["issues"] if i["severity"] == "critical"]) for r in results
    )
    high_issues = sum(
        len([i for i in r["issues"] if i["severity"] == "high"]) for r in results
    )

    print("\n📋 Overall Summary:")
    print(f"  Total issues: {total_issues}")
    print(f"  Critical: {critical_issues}")
    print(f"  High: {high_issues}")

    if critical_issues > 0:
        print(f"\n⚠️  {critical_issues} CRITICAL issues must be resolved")
    elif high_issues > 0:
        print(f"\n⚠️  {high_issues} HIGH priority issues should be addressed")
    else:
        print("\n✅ No critical or high priority issues found!")

    print("=" * 70)


def save_issues_report(results: list, output_file: Path):
    """Save detailed issues to CSV."""
    all_issues = []
    for result in results:
        all_issues.extend(result["issues"])

    if not all_issues:
        print("\n✅ No issues to save - all validations passed!")
        return

    issues_df = pd.DataFrame(all_issues)

    # Sort by severity then field
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues_df["_severity_order"] = issues_df["severity"].map(severity_order)
    issues_df = issues_df.sort_values(["_severity_order", "field", "name"])
    issues_df = issues_df.drop("_severity_order", axis=1)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    issues_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n✅ Saved {len(issues_df)} issues to: {output_file}")


def main():
    """Main execution."""
    print("=" * 70)
    print("  Phase II Field Validation")
    print("  Quality Assurance Script")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print(f"\n❌ Error: Input file not found: {INPUT_FILE}")
        return 1

    # Load data
    print(f"\nLoading data from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, dtype=str).fillna("")
    print(f"✅ Loaded {len(df)} entities")

    # Run validations
    print("\n🔍 Running validations...")

    results = [
        validate_authorizing_authority(df),
        validate_authorizing_url(df),
        validate_org_chart_oversight(df),
        validate_appointments_summary(df),
    ]

    # Print report
    print_validation_report(results)

    # Save issues
    save_issues_report(results, OUTPUT_FILE)

    # Determine exit code
    critical_count = sum(
        len([i for i in r["issues"] if i["severity"] == "critical"]) for r in results
    )

    if critical_count > 0:
        print(f"\n❌ Validation FAILED: {critical_count} critical issues")
        return 1
    else:
        print("\n✅ Validation PASSED: No critical issues")
        return 0


if __name__ == "__main__":
    sys.exit(main())
