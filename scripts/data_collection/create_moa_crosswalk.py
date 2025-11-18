#!/usr/bin/env python3
"""
Create crosswalk between MOA appointments data and NYCGO dataset.

Matches entities from scraped NYC.gov appointments page to existing
NYCGO entities using fuzzy name matching.

Usage:
    python scripts/data_collection/create_moa_crosswalk.py

Inputs:
    - data/scraped/moa_appointments_raw.csv (scraped data)
    - data/working/NYCGO_golden_dataset_v2.0.0-dev.csv (NYCGO dataset)

Output:
    - data/crosswalk/moa_to_nycgo_mapping.csv
"""

import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOA_INPUT = PROJECT_ROOT / "data" / "scraped" / "moa_appointments_raw.csv"
NYCGO_INPUT = PROJECT_ROOT / "data" / "working" / "NYCGO_golden_dataset_v2.0.0-dev.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "crosswalk" / "moa_to_nycgo_mapping.csv"


def normalize_name(name: str) -> str:
    """Normalize entity name for matching."""
    if not name:
        return ""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Remove common prefixes
    prefixes = ["the ", "nyc ", "new york city "]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    # Remove punctuation
    normalized = normalized.replace(",", "").replace(".", "")
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity ratio between two names."""
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_best_match(  # noqa: C901
    moa_name: str, nycgo_df: pd.DataFrame, threshold: float = 0.6
) -> dict:
    """
    Find best matching NYCGO entity for an MOA entity name.

    Args:
        moa_name: Name from MOA data
        nycgo_df: DataFrame of NYCGO entities
        threshold: Minimum similarity score (0-1) to consider a match

    Returns:
        Dict with match info: {
            'nycgo_record_id': str or None,
            'nycgo_name': str or None,
            'similarity_score': float,
            'match_confidence': str (exact/high/medium/low/none)
        }
    """
    best_match = {
        "nycgo_record_id": None,
        "nycgo_name": None,
        "similarity_score": 0.0,
        "match_confidence": "none",
    }

    # Check for exact match first
    exact_matches = nycgo_df[nycgo_df["Name"].str.lower() == moa_name.lower()]
    if not exact_matches.empty:
        match = exact_matches.iloc[0]
        best_match["nycgo_record_id"] = match["RecordID"]
        best_match["nycgo_name"] = match["Name"]
        best_match["similarity_score"] = 1.0
        best_match["match_confidence"] = "exact"
        return best_match

    # Check alternate names
    for _, row in nycgo_df.iterrows():
        alt_names = row.get("AlternateOrFormerNames", "")
        if pd.notna(alt_names) and alt_names:
            alt_names_list = [n.strip() for n in str(alt_names).split(";")]
            if moa_name.lower() in [n.lower() for n in alt_names_list]:
                best_match["nycgo_record_id"] = row["RecordID"]
                best_match["nycgo_name"] = row["Name"]
                best_match["similarity_score"] = 1.0
                best_match["match_confidence"] = "exact"
                return best_match

    # Fuzzy matching
    for _, row in nycgo_df.iterrows():
        score = calculate_similarity(moa_name, row["Name"])

        # Also check alternate names
        alt_names = row.get("AlternateOrFormerNames", "")
        if pd.notna(alt_names) and alt_names:
            alt_names_list = [n.strip() for n in str(alt_names).split(";")]
            for alt_name in alt_names_list:
                alt_score = calculate_similarity(moa_name, alt_name)
                score = max(score, alt_score)

        if score > best_match["similarity_score"]:
            best_match["nycgo_record_id"] = row["RecordID"]
            best_match["nycgo_name"] = row["Name"]
            best_match["similarity_score"] = score

    # Determine confidence level
    if best_match["similarity_score"] >= 0.95:
        best_match["match_confidence"] = "high"
    elif best_match["similarity_score"] >= 0.80:
        best_match["match_confidence"] = "medium"
    elif best_match["similarity_score"] >= threshold:
        best_match["match_confidence"] = "low"
    else:
        best_match["match_confidence"] = "none"
        best_match["nycgo_record_id"] = None
        best_match["nycgo_name"] = None

    return best_match


def create_crosswalk(moa_df: pd.DataFrame, nycgo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create crosswalk between MOA and NYCGO datasets.

    Args:
        moa_df: MOA appointments data
        nycgo_df: NYCGO dataset

    Returns:
        DataFrame with crosswalk mappings
    """
    print("\nCreating crosswalk...")
    print(f"  MOA entities: {len(moa_df)}")
    print(f"  NYCGO entities: {len(nycgo_df)}")

    crosswalk_data = []

    for idx, moa_row in moa_df.iterrows():
        moa_name = moa_row["entity_name"]
        moa_url = moa_row.get("url", "")
        moa_desc = moa_row.get("description", "")

        # Find best match
        match = find_best_match(moa_name, nycgo_df)

        crosswalk_data.append(
            {
                "moa_entity_name": moa_name,
                "moa_url": moa_url,
                "moa_description": (
                    moa_desc[:200] if moa_desc else ""
                ),  # Truncate long descriptions
                "nycgo_record_id": match["nycgo_record_id"],
                "nycgo_name": match["nycgo_name"],
                "similarity_score": round(match["similarity_score"], 3),
                "match_confidence": match["match_confidence"],
                "needs_manual_review": (
                    "yes" if match["match_confidence"] in ["low", "none"] else "no"
                ),
                "notes": "",
            }
        )

        # Progress indicator
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(moa_df)} entities...")

    return pd.DataFrame(crosswalk_data)


def print_summary(crosswalk_df: pd.DataFrame):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("  Crosswalk Summary")
    print("=" * 60)

    total = len(crosswalk_df)
    print(f"Total MOA entities: {total}")

    # Count by confidence level
    confidence_counts = crosswalk_df["match_confidence"].value_counts()
    for conf_level in ["exact", "high", "medium", "low", "none"]:
        count = confidence_counts.get(conf_level, 0)
        pct = count / total * 100 if total > 0 else 0
        print(f"  - {conf_level.capitalize()}: {count} ({pct:.1f}%)")

    needs_review = (crosswalk_df["needs_manual_review"] == "yes").sum()
    print(f"\nNeeds manual review: {needs_review} ({needs_review/total*100:.1f}%)")

    print("\nNo match found:")
    no_matches = crosswalk_df[crosswalk_df["match_confidence"] == "none"]
    for _, row in no_matches.head(10).iterrows():
        print(f"  - {row['moa_entity_name']}")
    if len(no_matches) > 10:
        print(f"  ... and {len(no_matches) - 10} more")

    print("=" * 60)


def main():
    """Main execution."""
    print("=" * 60)
    print("  MOA to NYCGO Crosswalk Creator")
    print("  Phase II.2 Data Collection")
    print("=" * 60)

    # Check input files exist
    if not MOA_INPUT.exists():
        print(f"\n❌ Error: MOA input file not found: {MOA_INPUT}")
        print("   Run scraping script first:")
        print("   scripts/data_collection/scrape_moa_appointments.py")
        return 1

    if not NYCGO_INPUT.exists():
        print(f"\n❌ Error: NYCGO input file not found: {NYCGO_INPUT}")
        return 1

    # Load data
    print("\nLoading data...")
    moa_df = pd.read_csv(MOA_INPUT, dtype=str).fillna("")
    nycgo_df = pd.read_csv(NYCGO_INPUT, dtype=str).fillna("")

    print(f"✅ Loaded {len(moa_df)} MOA entities")
    print(f"✅ Loaded {len(nycgo_df)} NYCGO entities")

    # Create crosswalk
    crosswalk_df = create_crosswalk(moa_df, nycgo_df)

    # Save output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    crosswalk_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Saved crosswalk to: {OUTPUT_FILE}")

    # Print summary
    print_summary(crosswalk_df)

    print("\n📝 NEXT STEPS:")
    print("1. Review entities marked 'needs_manual_review: yes'")
    print("2. Update 'nycgo_record_id' and 'notes' columns as needed")
    print("3. Run gap analysis: scripts/analysis/analyze_moa_coverage.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
