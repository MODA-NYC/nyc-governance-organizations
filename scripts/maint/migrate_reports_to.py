#!/usr/bin/env python3
"""
Migrate reports_to field values to new Phase II relationship fields.

This script reads existing ReportsTo values from the Phase I dataset and maps them
to the new Phase II relationship fields:
- org_chart_oversight_record_id (for org chart/political oversight)
- parent_organization_record_id (for parent-child governance relationships)

Usage:
    python scripts/maint/migrate_reports_to.py \
      --input data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
      --crosswalk data/crosswalk/recordid_migration.csv \
      --output data/crosswalk/reports_to_migration.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


# Entity names that indicate org chart oversight (not parent-child relationships)
ORG_CHART_OVERSIGHT_KEYWORDS = [
    "Mayor",
    "Deputy Mayor",
    "First Deputy Mayor",
    "Chief Counsel",
    "Mayor's Office",
    "Office of the Mayor",
]


def is_org_chart_oversight(reports_to_value: str, org_type: str) -> bool:
    """
    Determine if a ReportsTo value represents org chart oversight vs parent-child.
    
    Rules:
    - Deputy Mayors, Mayor, Mayor's Office → org_chart_oversight
    - Divisions reporting to departments → parent_organization
    - Specialized boards reporting to parent → parent_organization
    - Most other cases → org_chart_oversight (default)
    """
    if pd.isna(reports_to_value) or reports_to_value.strip() == "":
        return None
    
    reports_to_lower = str(reports_to_value).lower()
    
    # Check for org chart keywords
    for keyword in ORG_CHART_OVERSIGHT_KEYWORDS:
        if keyword.lower() in reports_to_lower:
            return True
    
    # Divisions typically have parent_organization relationship
    if org_type == "Division":
        # But if it's a Deputy Mayor or Mayor, it's org chart oversight
        if any(kw.lower() in reports_to_lower for kw in ORG_CHART_OVERSIGHT_KEYWORDS):
            return True
        return False
    
    # Default: assume org chart oversight unless clearly a parent-child relationship
    return True


def find_recordid_by_name(
    df: pd.DataFrame, entity_name: str, recordid_col: str = "RecordID"
) -> str | None:
    """
    Find RecordID for an entity by name (fuzzy matching).
    
    Checks:
    1. Exact match on Name
    2. Match on AlternateOrFormerNames
    3. Partial match on Name
    """
    if pd.isna(entity_name) or entity_name.strip() == "":
        return None
    
    entity_name = str(entity_name).strip()
    
    # Try exact match on Name
    exact_match = df[df["Name"].str.strip().str.lower() == entity_name.lower()]
    if len(exact_match) > 0:
        return exact_match.iloc[0][recordid_col]
    
    # Try match on AlternateOrFormerNames
    if "AlternateOrFormerNames" in df.columns:
        for idx, row in df.iterrows():
            alt_names = str(row.get("AlternateOrFormerNames", "")).lower()
            if entity_name.lower() in alt_names:
                return row[recordid_col]
    
    # Try partial match on Name
    partial_match = df[
        df["Name"].str.strip().str.lower().str.contains(entity_name.lower(), na=False)
    ]
    if len(partial_match) == 1:
        return partial_match.iloc[0][recordid_col]
    
    # Multiple matches - return None (needs manual review)
    if len(partial_match) > 1:
        return None
    
    return None


def load_recordid_crosswalk(crosswalk_path: Path) -> dict[str, str]:
    """Load RecordID crosswalk mapping old format to new format."""
    if not crosswalk_path.exists():
        print(f"Warning: Crosswalk file not found at {crosswalk_path}")
        return {}
    
    try:
        df_crosswalk = pd.read_csv(crosswalk_path, dtype=str)
        # Create mapping: old_record_id -> new_record_id
        crosswalk_map = dict(
            zip(
                df_crosswalk["old_record_id"].astype(str).str.strip(),
                df_crosswalk["new_record_id"].astype(str).str.strip(),
            )
        )
        print(f"Loaded {len(crosswalk_map)} RecordID mappings from crosswalk")
        return crosswalk_map
    except Exception as e:
        print(f"Error loading crosswalk: {e}")
        return {}


def migrate_reports_to(
    df: pd.DataFrame, crosswalk_map: dict[str, str]
) -> pd.DataFrame:
    """
    Create migration mapping for ReportsTo field.
    
    Returns DataFrame with columns:
    - record_id (old format)
    - entity_name
    - reports_to_value (original)
    - relationship_type (org_chart_oversight or parent_organization)
    - target_record_id (new format, if found)
    - target_entity_name (if found)
    - match_confidence (exact, partial, none)
    - needs_manual_review (yes/no)
    """
    migration_rows = []
    
    # Get records with ReportsTo values
    records_with_reports_to = df[df["ReportsTo"].notna() & (df["ReportsTo"].str.strip() != "")]
    
    print(f"\nProcessing {len(records_with_reports_to)} records with ReportsTo values...")
    
    for idx, row in records_with_reports_to.iterrows():
        record_id_old = str(row["RecordID"])
        entity_name = str(row["Name"])
        reports_to_value = str(row["ReportsTo"]).strip()
        org_type = str(row.get("OrganizationType", ""))
        
        # Determine relationship type
        is_org_chart = is_org_chart_oversight(reports_to_value, org_type)
        relationship_type = (
            "org_chart_oversight" if is_org_chart else "parent_organization"
        )
        
        # Find RecordID for the ReportsTo entity
        target_record_id_old = find_recordid_by_name(df, reports_to_value)
        
        # Convert to new format if crosswalk available
        target_record_id_new = None
        if target_record_id_old and target_record_id_old in crosswalk_map:
            target_record_id_new = crosswalk_map[target_record_id_old]
        
        # Get target entity name
        target_entity_name = None
        if target_record_id_old:
            target_row = df[df["RecordID"] == target_record_id_old]
            if len(target_row) > 0:
                target_entity_name = target_row.iloc[0]["Name"]
        
        # Determine match confidence
        if target_record_id_old:
            match_confidence = "exact"
        else:
            match_confidence = "none"
        
        # Flag for manual review if:
        # - No match found
        # - Multiple potential matches
        # - Ambiguous relationship type
        needs_review = (
            target_record_id_old is None
            or (org_type == "Division" and is_org_chart)
            or reports_to_value.count(";") > 0  # Multiple values
        )
        
        migration_rows.append(
            {
                "record_id_old": record_id_old,
                "entity_name": entity_name,
                "organization_type": org_type,
                "reports_to_value": reports_to_value,
                "relationship_type": relationship_type,
                "target_record_id_old": target_record_id_old or "",
                "target_record_id_new": target_record_id_new or "",
                "target_entity_name": target_entity_name or "",
                "match_confidence": match_confidence,
                "needs_manual_review": "yes" if needs_review else "no",
            }
        )
    
    migration_df = pd.DataFrame(migration_rows)
    
    # Summary statistics
    print(f"\nMigration Summary:")
    print(f"  Total records: {len(migration_df)}")
    print(f"  Org chart oversight: {len(migration_df[migration_df['relationship_type'] == 'org_chart_oversight'])}")
    print(f"  Parent organization: {len(migration_df[migration_df['relationship_type'] == 'parent_organization'])}")
    print(f"  Matches found: {len(migration_df[migration_df['target_record_id_old'] != ''])}")
    print(f"  Needs manual review: {len(migration_df[migration_df['needs_manual_review'] == 'yes'])}")
    
    return migration_df


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate ReportsTo field values to Phase II relationship fields. "
            "Creates a migration mapping CSV with decisions for each ReportsTo value."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to Phase I/II dataset CSV with ReportsTo field",
    )
    parser.add_argument(
        "--crosswalk",
        type=Path,
        help="Path to RecordID migration crosswalk CSV (for converting to new format)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to save migration mapping CSV",
    )
    
    args = parser.parse_args()
    
    # Load input dataset
    print(f"Loading dataset from {args.input}...")
    try:
        df = pd.read_csv(args.input, dtype=str)
        print(f"Loaded {len(df)} records")
    except Exception as e:
        print(f"Error loading input dataset: {e}")
        return 1
    
    # Validate ReportsTo column exists
    if "ReportsTo" not in df.columns:
        print("Error: ReportsTo column not found in dataset")
        print(f"Available columns: {', '.join(df.columns[:10])}...")
        return 1
    
    # Load RecordID crosswalk if provided
    crosswalk_map = {}
    if args.crosswalk:
        crosswalk_map = load_recordid_crosswalk(args.crosswalk)
    
    # Perform migration
    migration_df = migrate_reports_to(df, crosswalk_map)
    
    # Save migration mapping
    print(f"\nSaving migration mapping to {args.output}...")
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        migration_df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"✅ Migration mapping saved successfully")
        print(f"   Records: {len(migration_df)}")
        print(f"   File: {args.output}")
    except Exception as e:
        print(f"Error saving output: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

