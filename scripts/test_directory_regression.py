#!/usr/bin/env python3
"""
Regression test for directory eligibility logic.

Compares the new rules-based evaluation against the current published dataset
to ensure refactoring doesn't change any values.

Usage:
    # Create baseline (run once before refactoring)
    python scripts/test_directory_regression.py --create-baseline

    # Run regression test
    python scripts/test_directory_regression.py

    # Run with verbose diff output
    python scripts/test_directory_regression.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

BASELINE_PATH = Path(__file__).parent.parent / "tests" / "directory_baseline.csv"
PUBLISHED_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "published"
    / "latest"
    / "NYCGO_golden_dataset_latest.csv"
)


# Field name mapping from CSV columns to rule-expected names
FIELD_MAP = {
    "RecordID": "record_id",
    "Name": "name",
    "OperationalStatus": "operational_status",
    "OrganizationType": "organization_type",
    "URL": "url",
    "InOrgChart": "in_org_chart",
    "PrincipalOfficerFullName": "principal_officer_full_name",
    "PrincipalOfficerContactURL": "principal_officer_contact_url",
    "NYC.gov Agency Directory": "listed_in_nyc_gov_agency_directory",
}


def normalize_record(row: pd.Series) -> dict:
    """Convert a DataFrame row to a dict with normalized field names for rules."""
    record = {}
    for csv_col, rule_field in FIELD_MAP.items():
        if csv_col in row.index:
            record[rule_field] = row[csv_col]
    return record


def normalize_bool(value: str) -> str:
    """Normalize boolean values for comparison."""
    if str(value).strip().lower() in ("true", "1", "t", "yes"):
        return "True"
    return "False"


def create_baseline() -> None:
    """Create baseline snapshot from current published dataset."""
    if not PUBLISHED_PATH.exists():
        print(f"ERROR: Published dataset not found at {PUBLISHED_PATH}")
        sys.exit(1)

    print(f"Reading published dataset from {PUBLISHED_PATH}")
    df = pd.read_csv(PUBLISHED_PATH, dtype=str).fillna("")

    # Check for required column
    if "NYC.gov Agency Directory" not in df.columns:
        print("ERROR: 'NYC.gov Agency Directory' column not found in dataset")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    baseline = df[["RecordID", "Name", "NYC.gov Agency Directory"]].copy()
    baseline.columns = ["record_id", "name", "listed_in_nyc_gov_agency_directory"]

    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(BASELINE_PATH, index=False)
    print(f"Created baseline with {len(baseline)} records at {BASELINE_PATH}")


def run_regression_test(verbose: bool = False) -> None:  # noqa: C901
    """Compare new evaluation against baseline."""
    from nycgo_pipeline.directory_rules import evaluate_eligibility

    if not BASELINE_PATH.exists():
        print(f"ERROR: Baseline not found at {BASELINE_PATH}")
        print("Run with --create-baseline first")
        sys.exit(1)

    if not PUBLISHED_PATH.exists():
        print(f"ERROR: Published dataset not found at {PUBLISHED_PATH}")
        sys.exit(1)

    print(f"Loading baseline from {BASELINE_PATH}")
    baseline = pd.read_csv(BASELINE_PATH, dtype=str).fillna("")
    baseline_dict = {row["record_id"]: row for _, row in baseline.iterrows()}

    print(f"Loading published dataset from {PUBLISHED_PATH}")
    published = pd.read_csv(PUBLISHED_PATH, dtype=str).fillna("")

    print(f"Evaluating {len(published)} records with new rules...")

    differences = []
    missing_in_baseline = []

    for _, row in published.iterrows():
        record = normalize_record(row)
        record_id = record.get("record_id", "")

        # Evaluate with new rules
        result = evaluate_eligibility(record)
        new_value = "True" if result.eligible else "False"

        # Get baseline value
        if record_id not in baseline_dict:
            missing_in_baseline.append(record_id)
            continue

        old_value = baseline_dict[record_id]["listed_in_nyc_gov_agency_directory"]
        old_normalized = normalize_bool(old_value)

        if new_value != old_normalized:
            differences.append(
                {
                    "record_id": record_id,
                    "name": record.get("name", ""),
                    "old_value": old_value,
                    "new_value": new_value,
                    "reasoning": result.reasoning,
                    "reasoning_detailed": result.reasoning_detailed,
                }
            )

    # Report missing records
    if missing_in_baseline:
        print(
            f"\nWARNING: {len(missing_in_baseline)} records in dataset not in baseline"
        )
        print("These may be new records added since baseline was created")
        if verbose:
            for rid in missing_in_baseline[:10]:
                print(f"  - {rid}")
            if len(missing_in_baseline) > 10:
                print(f"  ... and {len(missing_in_baseline) - 10} more")

    # Report differences
    if differences:
        print(f"\nDIFFERENCES FOUND: {len(differences)} records")
        print("=" * 70)

        for diff in differences:
            print(f"\n{diff['record_id']}: {diff['name']}")
            print(f"  Old: {diff['old_value']}")
            print(f"  New: {diff['new_value']}")
            if verbose:
                print(f"  Reasoning: {diff['reasoning']}")
                print("  Detailed:")
                for line in diff["reasoning_detailed"].split("\n"):
                    print(f"    {line}")

        print("\n" + "=" * 70)
        print("REGRESSION TEST FAILED")
        print(
            "Review differences above. If intentional, "
            "update baseline with --create-baseline"
        )
        sys.exit(1)
    else:
        print("\nSUCCESS: No differences found")
        print(
            f"Regression test passed - new rules produce identical results "
            f"for all {len(published)} records"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Directory eligibility regression test"
    )
    parser.add_argument(
        "--create-baseline",
        action="store_true",
        help="Create baseline snapshot from current published data",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed reasoning for differences",
    )
    args = parser.parse_args()

    if args.create_baseline:
        create_baseline()
    else:
        run_regression_test(verbose=args.verbose)


if __name__ == "__main__":
    main()
