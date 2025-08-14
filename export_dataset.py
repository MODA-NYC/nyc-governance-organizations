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
import pathlib
import re
import sys

import pandas as pd


def to_snake_case(name: str) -> str:
    """Converts a PascalCase or CamelCase string to snake_case."""
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s2 = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s1)
    return s2.lower()


### START OF FINAL CORRECTED HELPER FUNCTION ###
def add_nycgov_directory_column(df):  # noqa: C901
    """Applies business logic to determine if a record should be on the NYC.gov Agency
    Directory.

    The listed_in_nyc_gov_agency_directory field is TRUE if:

    Part A (ALL must be true):
    * operational_status IS Active
    * organization_type IS NOT "Nonprofit Organization"
    * URL does NOT contain "ny.gov" (if URL exists)

    AND

    Part B (at least ONE must be true):
    * URL is non-null
    * PrincipalOfficerName is non-null
    * PrincipalOfficerContactURL is non-null

    OR

    Part C (Manual Override):
    * RecordID is in the manual override list
    """
    print(
        "Applying final, corrected logic for 'listed_in_nyc_gov_agency_directory' "
        "column..."
    )
    df_processed = df.copy()

    # --- Manual Override Lists: Records that should always be TRUE or FALSE ---
    manual_override_true_record_ids = [
        # Add RecordIDs here that should always be marked as TRUE
        # Example: "NYC_GOID_000123",
        # Example: "NYC_GOID_000456",
        "NYC_GOID_000038",
        "NYC_GOID_000149",
        "NYC_GOID_000310",
        "NYC_GOID_000335",
        "NYC_GOID_000402",
    ]

    manual_override_false_record_ids = [
        # Add RecordIDs here that should always be marked as FALSE
        # Example: "NYC_GOID_000789",
        # Example: "NYC_GOID_000999",
        "NYC_GOID_000120",
        "NYC_GOID_000121",
        "NYC_GOID_000122",
        "NYC_GOID_000232",
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

    # --- Part A: Gatekeeping Conditions (must pass ALL of these) ---
    # Handle NaN values properly for operational_status
    is_active = (
        df_processed["operational_status"].fillna("").str.strip().str.lower()
        == "active"
    )

    # Handle NaN values properly for organization_type
    is_not_nonprofit = (
        df_processed["organization_type"].fillna("").str.strip().str.lower()
        != "nonprofit organization"
    )

    # Check if URL contains ny.gov - if it does, exclude the record
    # Records with no URL are OK, but if URL exists and contains ny.gov, exclude
    has_url = df_processed["url"].notna() & (df_processed["url"].str.strip() != "")
    url_contains_nygov = has_url & df_processed["url"].str.contains(
        "ny.gov", case=False, na=False
    )
    url_ok = ~url_contains_nygov  # Either no URL or URL doesn't contain ny.gov

    gatekeeper_mask = is_active & is_not_nonprofit & url_ok

    # Debug: Print counts for Part A conditions
    print("Debug - Part A conditions:")
    print(f"  - Records with operational_status = 'active': {is_active.sum()}")
    print(
        "  - Records with organization_type != 'nonprofit organization': "
        f"{is_not_nonprofit.sum()}"
    )
    print(f"  - Records with URLs containing 'ny.gov': {url_contains_nygov.sum()}")
    print(f"  - Records without 'ny.gov' in URL (or no URL): {url_ok.sum()}")
    print(f"  - Records passing ALL Part A conditions: {gatekeeper_mask.sum()}")

    # --- Part B: Contact Info Conditions (must have AT LEAST ONE of these) ---
    # Check if URL is non-null AND non-empty
    has_url_value = df_processed["url"].notna() & (
        df_processed["url"].str.strip() != ""
    )

    # Check if principal_officer_full_name is non-null AND non-empty
    has_officer_name = df_processed["principal_officer_full_name"].notna() & (
        df_processed["principal_officer_full_name"].str.strip() != ""
    )

    # Check if principal_officer_contact_url is non-null AND non-empty
    has_officer_contact_url = df_processed["principal_officer_contact_url"].notna() & (
        df_processed["principal_officer_contact_url"].str.strip() != ""
    )

    contact_info_mask = has_url_value | has_officer_name | has_officer_contact_url

    # Debug: Print counts for Part B conditions
    print("\nDebug - Part B conditions:")
    print(f"  - Records with non-empty URL: {has_url_value.sum()}")
    print(
        "  - Records with non-empty principal_officer_full_name: "
        f"{has_officer_name.sum()}"
    )
    print(
        "  - Records with non-empty principal_officer_contact_url: "
        f"{has_officer_contact_url.sum()}"
    )
    print(
        f"  - Records with at least one Part B condition met: {contact_info_mask.sum()}"
    )

    # --- Final Combination: A record is included if it passes Part A AND Part B OR is in manual TRUE override, but not if in manual FALSE override ---
    automatic_mask = gatekeeper_mask & contact_info_mask
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
    print(f"  - Automatic matches: {automatic_mask.sum()}")
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
                f"  - {row['name']}{override_note}: "
                f"URL='{row['url']}', "
                f"Officer='{row['principal_officer_full_name']}', "
                f"Contact='{row['principal_officer_contact_url']}'"
            )

    # Debug: Show any records with ny.gov URLs that might have slipped through
    if final_mask.sum() > 0:
        nygov_true = df_processed[
            final_mask
            & has_url
            & df_processed["url"].str.contains("ny.gov", case=False, na=False)
        ]
        if len(nygov_true) > 0:
            print(
                "\nWARNING: Found "
                f"{len(nygov_true)} "
                "records with ny.gov URLs marked as TRUE (should be 0):"
            )
            for _idx, row in nygov_true.iterrows():
                print(f"  - {row['name']}: URL='{row['url']}'")

    return df_processed


### END OF FINAL CORRECTED HELPER FUNCTION ###


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
    args = parser.parse_args()

    # Load Input CSV
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

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
    df_public = df_public[in_org_chart | has_ops_name | is_mta_exception].copy()
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
        "Description",
        "URL",
        "AlternateOrFormerNames",
        "Acronym",
        "AlternateOrFormerAcronyms",
        "PrincipalOfficerFullName",
        "PrincipalOfficerFirstName",
        "PrincipalOfficerLastName",
        "PrincipalOfficerTitle",
        "PrincipalOfficerContactURL",
        "InOrgChart",
        "ReportsTo",
    ]
    missing_cols = [
        col for col in required_output_columns if col not in df_public.columns
    ]
    if missing_cols:
        print(f"Error: Expected columns missing for public export: {missing_cols}")
        sys.exit(1)

    df_selected = df_public[required_output_columns]

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
    df_selected = add_nycgov_directory_column(df_selected)

    # Save final published file
    try:
        args.output_published.parent.mkdir(parents=True, exist_ok=True)
        df_selected.to_csv(args.output_published, index=False, encoding="utf-8-sig")
        print(f"✅ Published dataset saved successfully to: {args.output_published}")
    except Exception as e:
        print(f"Error saving published dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
