#!/usr/bin/env python3
"""
Analyze MOA coverage gaps in NYCGO dataset.

Identifies:
- Entities in NYCGO but not in MOA data (should they be in MOA?)
- Entities in MOA data but not in NYCGO (need to add)
- Coverage statistics

Usage:
    python scripts/analysis/analyze_moa_coverage.py

Inputs:
    - data/crosswalk/moa_to_nycgo_mapping.csv
    - data/working/NYCGO_golden_dataset_v2.0.0-dev.csv

Output:
    - data/analysis/moa_coverage_gaps.csv
"""

import sys
from pathlib import Path

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK_INPUT = PROJECT_ROOT / "data" / "crosswalk" / "moa_to_nycgo_mapping.csv"
NYCGO_INPUT = PROJECT_ROOT / "data" / "working" / "NYCGO_golden_dataset_v2.0.0-dev.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "analysis" / "moa_coverage_gaps.csv"


def analyze_coverage(crosswalk_df: pd.DataFrame, nycgo_df: pd.DataFrame) -> tuple:
    """
    Analyze coverage gaps.

    Args:
        crosswalk_df: MOA crosswalk data
        nycgo_df: NYCGO dataset

    Returns:
        Tuple of (entities_in_moa_not_nycgo, entities_in_nycgo_not_moa)
    """
    print("\n🔍 Analyzing coverage gaps...")

    # Entities in MOA but not matched to NYCGO
    moa_not_in_nycgo = crosswalk_df[crosswalk_df["match_confidence"] == "none"].copy()

    moa_not_in_nycgo["gap_type"] = "in_moa_not_nycgo"
    moa_not_in_nycgo["priority"] = "high"  # These are on MOA page, should be in dataset
    moa_not_in_nycgo["action_needed"] = "add_to_nycgo"

    # Entities in NYCGO but not in MOA data
    # First, get all NYCGO Record IDs that were matched
    matched_record_ids = set(
        crosswalk_df[crosswalk_df["nycgo_record_id"].notna()]["nycgo_record_id"]
    )

    # Filter for active entities not matched (MOA should mostly have active entities)
    nycgo_not_in_moa = nycgo_df[
        (~nycgo_df["RecordID"].isin(matched_record_ids))
        & (nycgo_df["OperationalStatus"] == "Active")
    ].copy()

    # Create gap records for NYCGO entities not in MOA
    nycgo_gap_records = []
    for _, row in nycgo_not_in_moa.iterrows():
        nycgo_gap_records.append(
            {
                "moa_entity_name": "",
                "moa_url": "",
                "moa_description": "",
                "nycgo_record_id": row["RecordID"],
                "nycgo_name": row["Name"],
                "nycgo_org_type": row.get("OrganizationType", ""),
                "similarity_score": 0.0,
                "match_confidence": "n/a",
                "gap_type": "in_nycgo_not_moa",
                "priority": "medium",  # May or may not need to be on MOA page
                "action_needed": "verify_if_should_be_in_moa",
                "notes": "",
            }
        )

    nycgo_not_matched_df = pd.DataFrame(nycgo_gap_records)

    return moa_not_in_nycgo, nycgo_not_matched_df


def prioritize_gaps(gaps_df: pd.DataFrame) -> pd.DataFrame:
    """Assign priority levels to gaps based on entity characteristics."""
    # For MOA entities not in NYCGO: all high priority (they're on official MOA page)

    # For NYCGO entities not in MOA: prioritize by organization type
    if "nycgo_org_type" in gaps_df.columns:
        # High priority types that should likely be in MOA
        high_priority_types = [
            "Advisory or Regulatory Organization",
            "Mayoral Office",
            "Board",
            "Commission",
        ]

        # Medium priority
        medium_priority_types = [
            "Public Benefit or Development Organization",
            "Pension Fund",
        ]

        # Set priorities
        mask_high = gaps_df["nycgo_org_type"].isin(high_priority_types)
        mask_medium = gaps_df["nycgo_org_type"].isin(medium_priority_types)

        gaps_df.loc[mask_high & (gaps_df["priority"] != "high"), "priority"] = "high"
        gaps_df.loc[mask_medium & (gaps_df["priority"] == "low"), "priority"] = "medium"

    return gaps_df


def combine_and_save_gaps(
    moa_gaps: pd.DataFrame, nycgo_gaps: pd.DataFrame, output_file: Path
):
    """Combine gap analyses and save to file."""
    # Ensure columns align
    all_columns = [
        "gap_type",
        "priority",
        "action_needed",
        "moa_entity_name",
        "moa_url",
        "moa_description",
        "nycgo_record_id",
        "nycgo_name",
        "nycgo_org_type",
        "similarity_score",
        "match_confidence",
        "notes",
    ]

    # Add missing columns with empty values
    for col in all_columns:
        if col not in moa_gaps.columns:
            moa_gaps[col] = ""
        if col not in nycgo_gaps.columns:
            nycgo_gaps[col] = ""

    # Reorder columns
    moa_gaps = moa_gaps[all_columns]
    nycgo_gaps = nycgo_gaps[all_columns]

    # Combine
    all_gaps = pd.concat([moa_gaps, nycgo_gaps], ignore_index=True)

    # Prioritize
    all_gaps = prioritize_gaps(all_gaps)

    # Sort by priority then gap type
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_gaps["_priority_sort"] = all_gaps["priority"].map(priority_order)
    all_gaps = all_gaps.sort_values(["_priority_sort", "gap_type"]).drop(
        "_priority_sort", axis=1
    )

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    all_gaps.to_csv(output_file, index=False, encoding="utf-8-sig")

    return all_gaps


def print_summary(
    moa_gaps: pd.DataFrame, nycgo_gaps: pd.DataFrame, combined_gaps: pd.DataFrame
):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("  Coverage Gap Analysis Summary")
    print("=" * 60)

    print(f"\nEntities in MOA but NOT in NYCGO: {len(moa_gaps)}")
    if len(moa_gaps) > 0:
        print("  Sample (first 10):")
        for _, row in moa_gaps.head(10).iterrows():
            print(f"    - {row['moa_entity_name']}")
        if len(moa_gaps) > 10:
            print(f"    ... and {len(moa_gaps) - 10} more")

    print(f"\nActive NYCGO entities NOT in MOA: {len(nycgo_gaps)}")

    # Break down by organization type
    if len(nycgo_gaps) > 0 and "nycgo_org_type" in nycgo_gaps.columns:
        print("\n  By Organization Type:")
        type_counts = nycgo_gaps["nycgo_org_type"].value_counts().head(10)
        for org_type, count in type_counts.items():
            print(f"    - {org_type}: {count}")

    # Priority breakdown
    print(f"\nTotal gaps: {len(combined_gaps)}")
    priority_counts = combined_gaps["priority"].value_counts()
    for priority in ["high", "medium", "low"]:
        count = priority_counts.get(priority, 0)
        print(f"  - {priority.capitalize()} priority: {count}")

    print("\n📊 Recommendations:")
    high_priority = len(combined_gaps[combined_gaps["priority"] == "high"])
    print(f"  1. Review {high_priority} high-priority gaps first")
    print(f"  2. Add MOA entities to NYCGO dataset: {len(moa_gaps)}")
    print(f"  3. Verify if NYCGO entities should be in MOA: {len(nycgo_gaps)}")

    print("=" * 60)


def main():
    """Main execution."""
    print("=" * 60)
    print("  MOA Coverage Gap Analysis")
    print("  Phase II.2 Data Collection")
    print("=" * 60)

    # Check inputs exist
    if not CROSSWALK_INPUT.exists():
        print(f"\n❌ Error: Crosswalk file not found: {CROSSWALK_INPUT}")
        print("   Run crosswalk script first:")
        print("   scripts/data_collection/create_moa_crosswalk.py")
        return 1

    if not NYCGO_INPUT.exists():
        print(f"\n❌ Error: NYCGO file not found: {NYCGO_INPUT}")
        return 1

    # Load data
    print("\nLoading data...")
    crosswalk_df = pd.read_csv(CROSSWALK_INPUT, dtype=str).fillna("")
    nycgo_df = pd.read_csv(NYCGO_INPUT, dtype=str).fillna("")

    print(f"✅ Loaded {len(crosswalk_df)} crosswalk records")
    print(f"✅ Loaded {len(nycgo_df)} NYCGO entities")

    # Analyze gaps
    moa_gaps, nycgo_gaps = analyze_coverage(crosswalk_df, nycgo_df)

    # Combine and save
    combined_gaps = combine_and_save_gaps(moa_gaps, nycgo_gaps, OUTPUT_FILE)
    print(f"\n✅ Saved gap analysis to: {OUTPUT_FILE}")

    # Print summary
    print_summary(moa_gaps, nycgo_gaps, combined_gaps)

    print("\n📝 NEXT STEPS:")
    print("1. Review high-priority gaps in output file")
    print("2. Add missing MOA entities to NYCGO dataset")
    print("3. Verify NYCGO entities against MOA scope")
    print("4. Update crosswalk with manual corrections")

    return 0


if __name__ == "__main__":
    sys.exit(main())
