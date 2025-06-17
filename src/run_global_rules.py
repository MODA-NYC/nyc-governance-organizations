#!/usr/bin/env python3
"""
run_global_rules.py - Applies global transformation rules to the dataset.

This is the first processing stage. It takes a dataset and applies universal
cleaning and enrichment rules that do not depend on external QA feedback.
This includes character fixing, deduplication of semicolon-separated fields,
and parsing of officer names.
"""
import argparse
import pathlib
import sys
import unicodedata
from datetime import datetime

import ftfy
import pandas as pd
from nameparser import HumanName

# This script will have its own changelog mechanism, separate from the edit application.
changelog_entries = []
changelog_id_counter = 0

CHANGELOG_COLUMNS = [
    "ChangeID",
    "timestamp",
    "record_id",
    "column_changed",
    "old_value",
    "new_value",
    "feedback_source",
    "notes",
    "changed_by",
    "RuleAction",
]


def log_change(
    record_id: str,
    column_changed: str,
    old_value: any,
    new_value: any,
    feedback_source: str,
    notes: str | None,
    changed_by: str,
    rule_action: str | None,
):
    """Logs a change to the changelog_entries list."""
    global changelog_entries, changelog_id_counter
    changelog_id_counter += 1

    entry = {
        "ChangeID": changelog_id_counter,
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "column_changed": column_changed,
        "old_value": old_value,
        "new_value": new_value,
        "feedback_source": feedback_source,
        "notes": notes,
        "changed_by": changed_by,
        "RuleAction": rule_action if rule_action else "unknown",
    }
    changelog_entries.append(entry)


def apply_global_deduplication(
    df_input: pd.DataFrame, changed_by_user: str
) -> pd.DataFrame:
    """Apply global deduplication to specified semicolon-separated columns."""
    semicolon_columns_to_dedup = [
        "AlternateOrFormerNames",
        "AlternateOrFormerAcronyms",
    ]
    df_processed = df_input.copy()

    for col_name in semicolon_columns_to_dedup:
        if col_name not in df_processed.columns:
            continue

        for index, row in df_processed.iterrows():
            old_value = row.get(col_name)
            if isinstance(old_value, str) and old_value.strip():
                items = [item.strip() for item in old_value.split(";") if item.strip()]
                unique_items = list(dict.fromkeys(items))
                new_value = ";".join(unique_items)
                if new_value != old_value:
                    log_change(
                        row["RecordID"],
                        col_name,
                        old_value,
                        new_value,
                        "System_GlobalRule",
                        "Global deduplication applied",
                        changed_by_user,
                        "DEDUP_SEMICOLON",
                    )
                    df_processed.loc[index, col_name] = new_value
    return df_processed


def apply_global_character_fixing(
    df_input: pd.DataFrame, changed_by_user: str
) -> pd.DataFrame:
    """Apply global character fixing to specified text columns."""
    text_columns_to_fix = [
        "Name",
        "NameAlphabetized",
        "Description",
        "AlternateOrFormerNames",
        "AlternateOrFormerAcronyms",
        "PrincipalOfficerName",
        "PrincipalOfficerTitle",
        "Notes",
    ]
    df_processed = df_input.copy()

    for col_name in text_columns_to_fix:
        if col_name not in df_processed.columns:
            continue

        for index, row in df_processed.iterrows():
            old_value = row.get(col_name)
            if isinstance(old_value, str):
                new_value = ftfy.fix_text(old_value)
                new_value = unicodedata.normalize("NFKC", new_value)
                new_value = new_value.strip()
                if new_value != old_value:
                    log_change(
                        row["RecordID"],
                        col_name,
                        old_value,
                        new_value,
                        "System_GlobalCharFix",
                        "Global character/Unicode fixing applied",
                        changed_by_user,
                        "CHAR_FIX",
                    )
                    df_processed.loc[index, col_name] = new_value
    return df_processed


def populate_officer_name_parts(
    df_input: pd.DataFrame, changed_by_user: str
) -> pd.DataFrame:
    """Populates detailed name parts from PrincipalOfficerName."""
    df_processed = df_input.copy()
    name_cols = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]
    for col in name_cols:
        if col not in df_processed.columns:
            df_processed[col] = ""

    for index, row in df_processed.iterrows():
        name_str = row.get("PrincipalOfficerName")
        if isinstance(name_str, str) and name_str.strip():
            parsed = HumanName(name_str)
            updates = {
                "PrincipalOfficerFullName": name_str,
                "PrincipalOfficerGivenName": parsed.first,
                "PrincipalOfficerMiddleNameOrInitial": parsed.middle,
                "PrincipalOfficerFamilyName": parsed.last,
                "PrincipalOfficerSuffix": parsed.suffix,
            }
            for col, new_val in updates.items():
                if new_val and row.get(col) != new_val:
                    log_change(
                        row["RecordID"],
                        col,
                        row.get(col),
                        new_val,
                        "System_NameParseRule",
                        f"Parsed from: '{name_str}'",
                        changed_by_user,
                        "NAME_PARSE_SUCCESS",
                    )
                    df_processed.loc[index, col] = new_val
    return df_processed


def apply_mayoral_budget_code_rule(
    df_input: pd.DataFrame, changed_by_user: str
) -> pd.DataFrame:
    """
    Sets BudgetCode to '002' for records where OrganizationType is 'Mayoral Office'.
    """
    print("Applying Mayoral Office budget code rule...")
    df_processed = df_input.copy()

    # Define the condition and the default value
    condition = df_processed["OrganizationType"] == "Mayoral Office"
    default_code = "002"

    # Iterate only over the rows that meet the condition
    for index in df_processed[condition].index:
        old_value = df_processed.loc[index, "BudgetCode"]
        # Apply the rule only if the current value is blank or different
        if pd.isna(old_value) or old_value.strip() == "" or old_value != default_code:
            log_change(
                record_id=df_processed.loc[index, "RecordID"],
                column_changed="BudgetCode",
                old_value=old_value,
                new_value=default_code,
                feedback_source="System_GlobalRule",
                notes="Set default budget code for Mayoral Office",
                changed_by=changed_by_user,
                rule_action="CONDITIONAL_SET_BUDGET_CODE",
            )
            df_processed.loc[index, "BudgetCode"] = default_code

    return df_processed


def format_budget_codes(df_input: pd.DataFrame, changed_by_user: str) -> pd.DataFrame:
    """
    Ensures all existing, valid BudgetCode values are formatted as a three-digit
    text string, preserving nulls.
    """
    print("Formatting budget codes to three-digit strings...")
    df_processed = df_input.copy()

    if "BudgetCode" not in df_processed.columns:
        return df_processed

    # We will build a new series for the column to avoid
    # modification-while-iterating warnings
    new_codes = df_processed["BudgetCode"].copy()

    # Create a mask to identify only the rows with actual, non-blank data
    mask = df_processed["BudgetCode"].notna() & (
        df_processed["BudgetCode"].astype(str).str.strip() != ""
    )

    # Iterate only over the rows that have data
    for index in df_processed[mask].index:
        old_value = str(df_processed.loc[index, "BudgetCode"]).strip()

        try:
            # Convert to float first to handle strings like "2.0", then to int
            numeric_value = int(float(old_value))
            new_value = str(numeric_value).zfill(3)

            if new_value != old_value:
                log_change(
                    record_id=df_processed.loc[index, "RecordID"],
                    column_changed="BudgetCode",
                    old_value=old_value,
                    new_value=new_value,
                    feedback_source="System_GlobalRule",
                    notes="Formatted BudgetCode to three digits with leading zeros",
                    changed_by=changed_by_user,
                    rule_action="FORMAT_BUDGET_CODE",
                )
                # Update our new series, not the DataFrame we are iterating over
                new_codes.loc[index] = new_value
        except (ValueError, TypeError):
            print(
                "Warning: Could not format non-numeric BudgetCode "
                f"'{old_value}' for RecordID {df_processed.loc[index, 'RecordID']}."
            )

    # Assign the fully processed series back to the DataFrame at the end.
    # This correctly preserves nulls (which were never iterated on) and applies
    # all changes.
    df_processed["BudgetCode"] = new_codes

    return df_processed


def main():
    """Main function to run the global rules processing."""
    parser = argparse.ArgumentParser(
        description="Apply global transformation rules to a dataset."
    )
    parser.add_argument(
        "--input_csv",
        type=pathlib.Path,
        required=True,
        help="Path to the input dataset CSV.",
    )
    parser.add_argument(
        "--output_csv",
        type=pathlib.Path,
        required=True,
        help="Path to save the processed dataset CSV.",
    )
    parser.add_argument(
        "--changelog",
        type=pathlib.Path,
        required=True,
        help="Path to save the changelog for this run.",
    )
    parser.add_argument(
        "--changed_by",
        type=str,
        required=True,
        help="Identifier for who is running the script.",
    )
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    print("Applying global rules...")
    df_processed = apply_global_character_fixing(df, args.changed_by)
    df_processed = apply_global_deduplication(df_processed, args.changed_by)
    df_processed = populate_officer_name_parts(df_processed, args.changed_by)
    df_processed = apply_mayoral_budget_code_rule(df_processed, args.changed_by)
    df_processed = format_budget_codes(df_processed, args.changed_by)
    print("Global rules applied successfully.")

    # Save outputs
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"Processed dataset saved to: {args.output_csv}")

    args.changelog.parent.mkdir(parents=True, exist_ok=True)
    df_changelog = pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS)
    df_changelog.to_csv(args.changelog, index=False, encoding="utf-8-sig")
    print(f"Changelog for global rules saved to: {args.changelog}")

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
