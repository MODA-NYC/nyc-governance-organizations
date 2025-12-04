#!/usr/bin/env python3
"""
Apply reports_to migration to dataset.

This script applies the migration mapping created by migrate_reports_to.py to
populate Phase II relationship fields and remove ReportsTo.

Usage:
    python scripts/maint/apply_reports_to_migration.py \
      --input data/working/NYCGO_golden_dataset_v2.0.0-dev.csv \
      --migration data/crosswalk/reports_to_migration.csv \
      --output data/working/NYCGO_golden_dataset_v2.0.0-dev.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def apply_migration(
    df: pd.DataFrame, migration_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply reports_to migration to dataset.
    
    Adds Phase II fields if missing, populates them from migration mapping,
    and removes ReportsTo field.
    """
    df_processed = df.copy()
    
    # Add Phase II fields if missing
    phase_ii_fields = {
        "org_chart_oversight_record_id": "",
        "org_chart_oversight_name": "",
        "parent_organization_record_id": "",
        "parent_organization_name": "",
    }
    
    for field, default_value in phase_ii_fields.items():
        if field not in df_processed.columns:
            df_processed[field] = default_value
            print(f"Added missing field: {field}")
    
    # Create mapping from new RecordID (current dataset format) to migration row
    # The dataset has new format RecordIDs, so we need to map using new_record_id
    migration_map = {}
    for _, row in migration_df.iterrows():
        # Map using the new RecordID format (what's in the current dataset)
        new_record_id = str(row.get("new_record_id", "")).strip()
        if new_record_id:
            migration_map[new_record_id] = row
        # Also map using old RecordID for backward compatibility
        old_record_id = str(row["record_id_old"]).strip()
        if old_record_id:
            migration_map[old_record_id] = row
    
    # Apply migration
    applied_count = 0
    for idx, row in df_processed.iterrows():
        old_record_id = str(row["RecordID"]).strip()
        
        if old_record_id not in migration_map:
            continue
        
        migration_row = migration_map[old_record_id]
        relationship_type = str(migration_row["relationship_type"]).strip()
        target_record_id_new = str(migration_row["target_record_id_new"]).strip()
        target_entity_name = str(migration_row["target_entity_name"]).strip()
        
        # Skip if no target found
        if not target_record_id_new or target_record_id_new == "":
            continue
        
        # Apply based on relationship type
        if relationship_type == "org_chart_oversight":
            df_processed.at[idx, "org_chart_oversight_record_id"] = target_record_id_new
            if target_entity_name:
                df_processed.at[idx, "org_chart_oversight_name"] = target_entity_name
            applied_count += 1
        elif relationship_type == "parent_organization":
            df_processed.at[idx, "parent_organization_record_id"] = target_record_id_new
            if target_entity_name:
                df_processed.at[idx, "parent_organization_name"] = target_entity_name
            applied_count += 1
    
    print(f"\nApplied migration to {applied_count} records")
    
    # Remove ReportsTo field if it exists
    if "ReportsTo" in df_processed.columns:
        df_processed = df_processed.drop(columns=["ReportsTo"])
        print("Removed ReportsTo field")
    
    return df_processed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply reports_to migration to dataset. "
            "Populates Phase II relationship fields and removes ReportsTo."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input dataset CSV",
    )
    parser.add_argument(
        "--migration",
        type=Path,
        required=True,
        help="Path to migration mapping CSV from migrate_reports_to.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to save updated dataset CSV",
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
    
    # Load migration mapping
    print(f"Loading migration mapping from {args.migration}...")
    try:
        migration_df = pd.read_csv(args.migration, dtype=str)
        print(f"Loaded {len(migration_df)} migration records")
    except Exception as e:
        print(f"Error loading migration mapping: {e}")
        return 1
    
    # Apply migration
    df_processed = apply_migration(df, migration_df)
    
    # Save output
    print(f"\nSaving updated dataset to {args.output}...")
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df_processed.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"✅ Updated dataset saved successfully")
        print(f"   Records: {len(df_processed)}")
        print(f"   File: {args.output}")
    except Exception as e:
        print(f"Error saving output: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

