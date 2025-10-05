#!/usr/bin/env python3
# ruff: noqa: E501, C901, B007
"""
export_dataset.py - Prepares and exports datasets for different destinations.

This script takes a final, processed "golden" dataset and produces two outputs:
1.  A versioned copy of the full golden dataset, saved to data/output/.
2.  A cleaned, filtered, and transformed public-facing version, saved to
    data/published/.
"""
import argparse
import csv
import pathlib
import re
import sys
from datetime import datetime, timezone

import pandas as pd


def to_snake_case(name: str) -> str:
    """Converts a PascalCase or CamelCase string to snake_case."""
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s2 = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s1)
    return s2.lower()


def write_proposed_changes(run_dir, changes, run_id, operator):
    """Write changes to proposed_changes.csv in run directory.

    Args:
        run_dir: Path to run directory
        changes: List of change dictionaries
        run_id: Run identifier
        operator: Person/system making the change
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    proposed_path = run_dir / "proposed_changes.csv"

    timestamp = datetime.now(timezone.utc).isoformat()

    fieldnames = [
        "timestamp_utc",
        "run_id",
        "record_id",
        "field",
        "old_value",
        "new_value",
        "reason",
        "evidence_url",
        "source_ref",
        "operator",
        "notes",
    ]

    # Append or create
    file_exists = proposed_path.exists() and proposed_path.stat().st_size > 0
    with proposed_path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for change in changes:
            writer.writerow(
                {
                    "timestamp_utc": timestamp,
                    "run_id": run_id or "",
                    "record_id": change["record_id"],
                    "field": change["field"],
                    "old_value": change.get("old_value", ""),
                    "new_value": change["new_value"],
                    "reason": change.get("reason", "directory_logic_v1"),
                    "evidence_url": "",
                    "source_ref": change.get(
                        "source_ref", "export_dataset.py::add_nycgov_directory_column"
                    ),
                    "operator": operator,
                    "notes": change.get("notes", ""),
                }
            )

    print(f"✅ Wrote {len(changes)} directory field changes to {proposed_path}")


### START OF DIRECTORY FIELD LOGIC (v2) ###
def add_nycgov_directory_column(
    df, df_before_snake_case=None, df_previous_export=None, run_id=None
):  # noqa: C901
    """Applies business logic (v2) to determine if a record should be on the NYC.gov
    Agency Directory.

    BLANKET GATEKEEPER RULES (all must be true):
    * operational_status IS Active
    * URL does NOT contain state "ny.gov" (but city "nyc.gov" is OK)
    * At least one of: url, principal_officer_full_name, or principal_officer_contact_url

    THEN apply ORGANIZATION TYPE SPECIFIC RULES:
    * Mayoral Agency: all included
    * Mayoral Office: all included
    * Division: only if in Org Chart
    * Elected Office: all included
    * Nonprofit Organization: only if in Org Chart OR in exemption list
    * Pension Fund: all included
    * State Government Agency: all included
    * Public Benefit or Development Organization: only if in Org Chart
    * Advisory or Regulatory Organization: if in Org Chart OR has main nyc.gov/index.page
      URL OR in exemption list

    Manual overrides can force TRUE or FALSE for specific record IDs.

    Args:
        df: Current dataframe (after snake_case conversion)
        df_before_snake_case: Original dataframe before snake_case conversion (deprecated)
        df_previous_export: Previous export file to compare against for changelog
        run_id: Run identifier for changelog tracking

    Returns:
        tuple: (processed_df, list_of_changes) if run_id provided, else just processed_df
    """
    print(
        "Applying final, corrected logic for 'listed_in_nyc_gov_agency_directory' "
        "column..."
    )
    # Reset index to ensure masks align correctly
    df_processed = df.copy().reset_index(drop=True)

    # Capture old values if tracking is enabled
    old_values = {}
    if run_id and df_previous_export is not None:
        # Check for the field in PascalCase or snake_case in the previous export
        old_col = None
        for possible_col in [
            "ListedInNycGovAgencyDirectory",
            "listed_in_nyc_gov_agency_directory",
        ]:
            if possible_col in df_previous_export.columns:
                old_col = possible_col
                break

        if old_col:
            # Build mapping of record_id -> old value
            record_id_col = None
            for possible_id in ["RecordID", "record_id"]:
                if possible_id in df_previous_export.columns:
                    record_id_col = possible_id
                    break

            if record_id_col:
                for idx, row in df_previous_export.iterrows():
                    old_values[row[record_id_col]] = str(row.get(old_col, ""))
            print(
                f"  - Loaded {len(old_values)} old values for change tracking from previous export"
            )
        else:
            print(
                "  - Warning: Previous export does not contain directory field column"
            )
    elif run_id and df_previous_export is None:
        print("  - No previous export provided; will track all values as new")

    # --- Exemption Lists for Organization Types ---
    nonprofit_exemptions = [
        "Brooklyn Public Library",
        "New York City Tourism + Conventions",
        "New York Public Library",
        "Queens Public Library",
        "Gracie Mansion Conservancy",
        "Mayor's Fund to Advance New York City",
    ]

    advisory_exemptions = [
        "Board of Elections",
        "Campaign Finance Board",
        "Rent Guidelines Board",
    ]

    # Keep manual overrides for any edge cases not covered by type rules
    manual_override_true_record_ids = [
        # Add RecordIDs here that should always be marked as TRUE
        # Example: "NYC_GOID_000123",
    ]

    manual_override_false_record_ids = [
        # Add RecordIDs here that should always be marked as FALSE
        # Example: "NYC_GOID_000789",
    ]

    # Create manual override masks
    manual_override_true_mask = df_processed["record_id"].isin(
        manual_override_true_record_ids
    )
    manual_override_false_mask = df_processed["record_id"].isin(
        manual_override_false_record_ids
    )

    if manual_override_true_mask.sum() > 0:
        print(
            "Manual override TRUE: "
            f"{manual_override_true_mask.sum()} "
            "records will be forced to TRUE"
        )
        for record_id in manual_override_true_record_ids:
            if record_id in df_processed["record_id"].values:
                record_name = df_processed[df_processed["record_id"] == record_id][
                    "name"
                ].iloc[0]
                print(f"  - {record_id}: {record_name}")

    if manual_override_false_mask.sum() > 0:
        print(
            "Manual override FALSE: "
            f"{manual_override_false_mask.sum()} "
            "records will be forced to FALSE"
        )
        for record_id in manual_override_false_record_ids:
            if record_id in df_processed["record_id"].values:
                record_name = df_processed[df_processed["record_id"] == record_id][
                    "name"
                ].iloc[0]
                print(f"  - {record_id}: {record_name}")

    # --- BLANKET GATEKEEPER RULES (must pass ALL of these) ---
    # 1. Must be Active
    is_active = (
        df_processed["operational_status"].fillna("").str.strip().str.lower()
        == "active"
    )

    # 2. URL must NOT contain state "ny.gov" (but city "nyc.gov" is OK)
    # Check for state URLs like ".ny.gov" but exclude city URLs ".nyc.gov"
    has_url = df_processed["url"].notna() & (df_processed["url"].str.strip() != "")
    # Match ".ny.gov" but not ".nyc.gov" - check for "ny.gov" but not preceded by "c"
    url_contains_state_nygov = has_url & (
        df_processed["url"].str.contains(r"\.ny\.gov", case=False, na=False, regex=True)
        & ~df_processed["url"].str.contains(
            r"\.nyc\.gov", case=False, na=False, regex=True
        )
    )
    url_ok = ~url_contains_state_nygov

    # 3. Must have at least ONE contact field
    has_url_value = df_processed["url"].notna() & (
        df_processed["url"].str.strip() != ""
    )
    has_officer_name = df_processed["principal_officer_full_name"].notna() & (
        df_processed["principal_officer_full_name"].str.strip() != ""
    )
    has_officer_contact_url = df_processed["principal_officer_contact_url"].notna() & (
        df_processed["principal_officer_contact_url"].str.strip() != ""
    )
    has_contact_info = has_url_value | has_officer_name | has_officer_contact_url

    # Blanket rules: Active AND no state ny.gov AND has contact info
    passes_blanket_rules = is_active & url_ok & has_contact_info

    print("Debug - Blanket gatekeeper rules:")
    print(f"  - Records with operational_status = 'active': {is_active.sum()}")
    print(
        f"  - Records with state 'ny.gov' URLs (excluded): {url_contains_state_nygov.sum()}"
    )
    print(f"  - Records with at least one contact field: {has_contact_info.sum()}")
    print(f"  - Records passing ALL blanket rules: {passes_blanket_rules.sum()}")

    # --- ORGANIZATION TYPE SPECIFIC RULES ---
    org_type = df_processed["organization_type"].fillna("").str.strip()
    in_org_chart = (
        df_processed.get("in_org_chart", pd.Series([False] * len(df_processed)))
        .fillna("")
        .astype(str)
        .str.lower()
        .isin(["true", "1", "t", "yes"])
    )
    org_name = df_processed["name"].fillna("").str.strip()

    # Check for nyc.gov URLs with index.page (for Advisory orgs)
    has_main_nyc_gov = has_url & (
        df_processed["url"].str.contains(r"nyc\.gov", case=False, na=False, regex=True)
        & df_processed["url"].str.contains(
            r"index\.page", case=False, na=False, regex=True
        )
    )

    # Build type-specific inclusion masks
    type_mask = pd.Series([False] * len(df_processed))

    # Mayoral Agency: all included
    type_mask |= org_type == "Mayoral Agency"

    # Mayoral Office: all included
    type_mask |= org_type == "Mayoral Office"

    # Division: only if in Org Chart
    type_mask |= (org_type == "Division") & in_org_chart

    # Elected Office: all included
    type_mask |= org_type == "Elected Office"

    # Nonprofit Organization: only if in Org Chart OR in exemption list
    type_mask |= (org_type == "Nonprofit Organization") & (
        in_org_chart | org_name.isin(nonprofit_exemptions)
    )

    # Pension Fund: all included
    type_mask |= org_type == "Pension Fund"

    # State Government Agency: all included
    type_mask |= org_type == "State Government Agency"

    # Public Benefit or Development Organization: only if in Org Chart
    type_mask |= (
        org_type == "Public Benefit or Development Organization"
    ) & in_org_chart

    # Advisory or Regulatory Organization: if in org chart OR has main nyc.gov url OR in exemption list
    type_mask |= (org_type == "Advisory or Regulatory Organization") & (
        in_org_chart | has_main_nyc_gov | org_name.isin(advisory_exemptions)
    )

    print("\nDebug - Organization type specific rules:")
    print(f"  - Mayoral Agency: {(org_type == 'Mayoral Agency').sum()} total")
    print(f"  - Mayoral Office: {(org_type == 'Mayoral Office').sum()} total")
    print(
        f"  - Division (in Org Chart): {((org_type == 'Division') & in_org_chart).sum()} included"
    )
    print(f"  - Elected Office: {(org_type == 'Elected Office').sum()} total")
    print(
        f"  - Nonprofit (in Org Chart or exemption): {((org_type == 'Nonprofit Organization') & (in_org_chart | org_name.isin(nonprofit_exemptions))).sum()} included"
    )
    print(f"  - Pension Fund: {(org_type == 'Pension Fund').sum()} total")
    print(
        f"  - State Government Agency: {(org_type == 'State Government Agency').sum()} total"
    )
    print(
        f"  - Public Benefit/Dev (in Org Chart): {((org_type == 'Public Benefit or Development Organization') & in_org_chart).sum()} included"
    )
    print(
        f"  - Advisory/Regulatory: {((org_type == 'Advisory or Regulatory Organization') & (in_org_chart | has_main_nyc_gov | org_name.isin(advisory_exemptions))).sum()} included"
    )

    # --- FINAL COMBINATION ---
    # Must pass blanket rules AND type-specific rules
    automatic_mask = passes_blanket_rules & type_mask

    # Apply manual overrides last
    final_mask = (
        automatic_mask | manual_override_true_mask
    ) & ~manual_override_false_mask

    # Apply the final boolean mask to the new column
    df_processed["listed_in_nyc_gov_agency_directory"] = final_mask

    print(
        "\nFinal result: "
        f"{final_mask.sum()} "
        "records meeting the NYC.gov Agency Directory criteria."
    )
    print(f"  - Passed blanket rules & type rules: {automatic_mask.sum()}")
    print(f"  - Manual TRUE overrides: {manual_override_true_mask.sum()}")
    print(f"  - Manual FALSE overrides: {manual_override_false_mask.sum()}")

    # Debug: Show a few examples of records that are marked TRUE
    if final_mask.sum() > 0:
        print("\nFirst 5 records marked as TRUE:")
        true_records = df_processed[final_mask].head(5)
        for _idx, row in true_records.iterrows():
            is_manual_true = row["record_id"] in manual_override_true_record_ids
            is_manual_false = row["record_id"] in manual_override_false_record_ids
            if is_manual_true:
                override_note = " (MANUAL TRUE OVERRIDE)"
            elif is_manual_false:
                override_note = " (MANUAL FALSE OVERRIDE)"
            else:
                override_note = ""
            print(
                f"  - {row['name']}{override_note} [{row['organization_type']}]: "
                f"URL='{row['url']}'"
            )

    # Debug: Show any records with state ny.gov URLs that might have slipped through
    if final_mask.sum() > 0:
        state_nygov_true = df_processed[final_mask & url_contains_state_nygov]
        if len(state_nygov_true) > 0:
            print(
                "\nWARNING: Found "
                f"{len(state_nygov_true)} "
                "records with state 'ny.gov' URLs marked as TRUE (should be 0):"
            )
            for _idx, row in state_nygov_true.iterrows():
                print(f"  - {row['name']}: URL='{row['url']}'")

    # Track changes if run_id provided
    changes = []
    if run_id:
        print("\nTracking changes to listed_in_nyc_gov_agency_directory...")
        for idx, row in df_processed.iterrows():
            record_id = row["record_id"]
            new_val = str(row["listed_in_nyc_gov_agency_directory"])
            old_val = old_values.get(record_id, "")

            # Normalize boolean representations (True/False/true/false/1/0 -> "True"/"False")
            def normalize_bool(val):
                if not val or val.strip() == "":
                    return ""
                val_lower = str(val).strip().lower()
                if val_lower in ["true", "1", "t", "yes"]:
                    return "True"
                elif val_lower in ["false", "0", "f", "no"]:
                    return "False"
                return ""

            new_normalized = normalize_bool(new_val)
            old_normalized = normalize_bool(old_val)

            # Track if value changed
            if new_normalized != old_normalized:
                # Determine context for the change
                is_manual_true = record_id in manual_override_true_record_ids
                is_manual_false = record_id in manual_override_false_record_ids
                row_data = df_processed[df_processed["record_id"] == record_id].iloc[0]
                org_type_val = row_data.get("organization_type", "")
                org_name_val = row_data.get("name", "")

                # Build detailed notes
                notes = ""
                if is_manual_true:
                    notes = "Manual override: forced to TRUE"
                elif is_manual_false:
                    notes = "Manual override: forced to FALSE"
                else:
                    # Describe why the change occurred based on type and exemptions
                    if org_name_val in nonprofit_exemptions:
                        notes = f"Type-based inclusion: {org_type_val} (Nonprofit exemption)"
                    elif org_name_val in advisory_exemptions:
                        notes = (
                            f"Type-based inclusion: {org_type_val} (Advisory exemption)"
                        )
                    else:
                        notes = f"Type-based inclusion: {org_type_val}"

                changes.append(
                    {
                        "record_id": record_id,
                        "field": "listed_in_nyc_gov_agency_directory",
                        "old_value": old_normalized,
                        "new_value": new_normalized,
                        "reason": "directory_logic_v2",
                        "source_ref": "export_dataset.py::add_nycgov_directory_column",
                        "notes": notes,
                    }
                )

        print(f"  - Detected {len(changes)} changes to directory field")
        return df_processed, changes

    return df_processed


### END OF DIRECTORY FIELD LOGIC (v2) ###


def main():
    """Main function to process the dataset for export."""
    parser = argparse.ArgumentParser(
        description=(
            "Processes a dataset CSV for final export, creating a versioned golden "
            "copy and a public-facing, transformed version."
        )
    )
    parser.add_argument(
        "--input_csv",
        required=True,
        type=pathlib.Path,
        help="Path to the final processed dataset to be exported.",
    )
    parser.add_argument(
        "--output_golden",
        required=True,
        type=pathlib.Path,
        help="Path to save the full, versioned golden dataset.",
    )
    parser.add_argument(
        "--output_published",
        required=True,
        type=pathlib.Path,
        help="Path to save the final, transformed, public-facing dataset.",
    )
    parser.add_argument(
        "--run-dir",
        type=pathlib.Path,
        help="Optional: Run directory for changelog tracking (e.g., data/audit/runs/<run_id>)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Optional: Run identifier for changelog tracking",
    )
    parser.add_argument(
        "--operator",
        type=str,
        default="",
        help="Optional: Operator name for changelog tracking",
    )
    parser.add_argument(
        "--previous-export",
        type=pathlib.Path,
        help="Optional: Path to previous export file (e.g., NYCGovernanceOrganizations_v0_18.csv) for changelog comparison",
    )
    args = parser.parse_args()

    # Load Input CSV
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    # Load previous export if provided (for changelog comparison)
    df_previous_export = None
    if args.previous_export:
        try:
            df_previous_export = pd.read_csv(args.previous_export, dtype=str)
            print(f"Loaded previous export from {args.previous_export} for comparison")
        except FileNotFoundError:
            print(
                f"Warning: Previous export file not found at '{args.previous_export}'",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Warning: Could not load previous export: {e}", file=sys.stderr)

    # --- Step 1: Save the full, versioned Golden Dataset ---
    print(f"Saving full golden dataset to {args.output_golden}...")
    try:
        args.output_golden.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output_golden, index=False, encoding="utf-8-sig")
        print("✅ Golden dataset saved successfully.")
    except Exception as e:
        print(f"Error saving golden dataset: {e}")
        sys.exit(1)

    # --- Step 2: Process and save the Published Dataset ---
    print("\nProcessing data for public export...")
    df_public = df.copy()

    # Rename columns for clarity
    rename_map = {
        "PrincipalOfficerGivenName": "PrincipalOfficerFirstName",
        "PrincipalOfficerFamilyName": "PrincipalOfficerLastName",
    }
    df_public.rename(columns=rename_map, inplace=True)

    # --- Filter for records to include in public output ---
    print("Applying filters for public export...")
    rows_before_filter = len(df_public)
    in_org_chart = (
        df_public.get("InOrgChart", pd.Series([False] * len(df_public)))
        .astype(str)
        .str.lower()
        .map({"true": True})
        .fillna(False)
    )
    has_ops_name = df_public.get(
        "Name - Ops", pd.Series([False] * len(df_public))
    ).notna() & (
        df_public.get("Name - Ops", pd.Series([""] * len(df_public))).str.strip() != ""
    )
    is_mta_exception = (
        df_public.get("RecordID", pd.Series([""] * len(df_public))) == "NYC_GOID_000476"
    )
    # New requirement: only export records where OperationalStatus is Active
    active_only = (
        df_public.get("OperationalStatus", pd.Series([""] * len(df_public)))
        .astype(str)
        .str.strip()
        .str.lower()
        == "active"
    )

    df_public = df_public[
        (in_org_chart | has_ops_name | is_mta_exception) & active_only
    ].copy()
    print(
        f"Kept {len(df_public)} rows out of {rows_before_filter} after applying combined filter."
    )

    # --- Select and order columns for final output ---
    required_output_columns = [
        "RecordID",
        "Name",
        "NameAlphabetized",
        "OperationalStatus",
        "OrganizationType",
        "URL",
        "AlternateOrFormerNames",
        "Acronym",
        "AlternateOrFormerAcronyms",
        "PrincipalOfficerFullName",
        "PrincipalOfficerFirstName",
        "PrincipalOfficerLastName",
        "PrincipalOfficerTitle",
        "PrincipalOfficerContactURL",
        "ReportsTo",
        "InOrgChart",
    ]
    missing_cols = [
        col for col in required_output_columns if col not in df_public.columns
    ]
    if missing_cols:
        print(f"Error: Expected columns missing for public export: {missing_cols}")
        sys.exit(1)

    df_selected = df_public[required_output_columns]

    # --- Save a copy BEFORE snake_case conversion for change tracking ---
    df_before_snake_case = df_selected.copy()

    # --- Convert headers to snake_case ---
    df_selected.columns = [to_snake_case(col) for col in df_selected.columns]
    print("Converted public column headers to snake_case.")

    # --- Normalize in_org_chart: fill blanks as False and coerce to booleans ---
    if "in_org_chart" in df_selected.columns:
        df_selected["in_org_chart"] = (
            df_selected["in_org_chart"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": True, "false": False})
            .fillna(False)
        )

    # --- Add NYC.gov Directory column AFTER snake_case conversion ---
    result = add_nycgov_directory_column(
        df_selected,
        df_before_snake_case=df_before_snake_case if args.run_dir else None,
        df_previous_export=df_previous_export,
        run_id=args.run_id,
    )

    # Handle return value (tuple if tracking, dataframe otherwise)
    if args.run_dir and isinstance(result, tuple):
        df_selected, directory_changes = result
    else:
        df_selected = result
        directory_changes = []

    # Save final published file
    try:
        args.output_published.parent.mkdir(parents=True, exist_ok=True)
        df_selected.to_csv(args.output_published, index=False, encoding="utf-8-sig")
        print(f"✅ Published dataset saved successfully to: {args.output_published}")
    except Exception as e:
        print(f"Error saving published dataset: {e}")
        sys.exit(1)

    # Also write a copy of the full golden to data/published for convenience
    try:
        published_golden_path = args.output_published.parent / args.output_golden.name
        df.to_csv(published_golden_path, index=False, encoding="utf-8-sig")
        print(f"✅ Golden dataset also saved to: {published_golden_path}")
    except Exception as e:
        print(f"Warning: Failed to save golden to published folder: {e}")

    # --- Write changelog for directory field changes ---
    if args.run_dir and directory_changes:
        print(
            f"\n📝 Writing changelog for {len(directory_changes)} directory field changes..."
        )
        write_proposed_changes(
            args.run_dir, directory_changes, args.run_id, args.operator
        )
        print("\nNext steps:")
        print(
            f"  1. Review changes: python scripts/maint/review_changes.py --run-dir {args.run_dir}"
        )
        print(
            f'  2. Append to changelog: python scripts/maint/append_changelog.py --run-dir {args.run_dir} --changelog data/changelog.csv --operator "$USER"'
        )
    elif args.run_dir and not directory_changes:
        print("\n✅ No changes detected in listed_in_nyc_gov_agency_directory field")


if __name__ == "__main__":
    main()
