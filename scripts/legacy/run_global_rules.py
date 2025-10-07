#!/usr/bin/env python3
import argparse
import pathlib
import re
import sys
import unicodedata
from datetime import datetime

import ftfy
import pandas as pd

changelog_entries, changelog_id_counter = [], 0
CHANGELOG_COLUMNS = [
    "ChangeID",
    "timestamp",
    "record_id",
    "record_name",
    "column_changed",
    "old_value",
    "new_value",
    "feedback_source",
    "notes",
    "reason",
    "changed_by",
    "RuleAction",
]


def log_change(
    record_id,
    record_name,
    column_changed,
    old_value,
    new_value,
    feedback_source,
    notes,
    reason,
    changed_by,
    rule_action,
    version_prefix,
):
    global changelog_entries, changelog_id_counter
    changelog_id_counter += 1
    changelog_entries.append(
        {
            "ChangeID": f"{version_prefix}_{changelog_id_counter}",
            "timestamp": datetime.now().isoformat(),
            "record_id": record_id,
            "record_name": record_name,
            "column_changed": column_changed,
            "old_value": old_value,
            "new_value": new_value,
            "feedback_source": feedback_source,
            "notes": notes,
            "reason": reason,
            "changed_by": changed_by,
            "RuleAction": rule_action,
        }
    )


def apply_global_deduplication(df, user, prefix):
    df_processed = df.copy()
    for col in ["AlternateOrFormerNames", "AlternateOrFormerAcronyms"]:
        if col in df_processed.columns:
            for i, row in df_processed.iterrows():
                old_val = row.get(col)
                if isinstance(old_val, str) and old_val.strip():
                    items = [
                        item.strip() for item in old_val.split(";") if item.strip()
                    ]
                    new_val = ";".join(list(dict.fromkeys(items)))
                    if new_val != old_val:
                        log_change(
                            row["RecordID"],
                            row["Name"],
                            col,
                            old_val,
                            new_val,
                            "System_GlobalRule",
                            "Global deduplication",
                            "",
                            user,
                            "DEDUP_SEMICOLON",
                            prefix,
                        )
                        df_processed.loc[i, col] = new_val
    return df_processed


def apply_global_character_fixing(df, user, prefix):
    df_processed = df.copy()
    text_cols = [
        "Name",
        "NameAlphabetized",
        "Description",
        "AlternateOrFormerNames",
        "AlternateOrFormerAcronyms",
        "PrincipalOfficerName",
        "PrincipalOfficerTitle",
        "Notes",
    ]
    for col in text_cols:
        if col in df_processed.columns:
            for i, row in df_processed.iterrows():
                old_val = row.get(col)
                if isinstance(old_val, str):
                    new_val = unicodedata.normalize(
                        "NFKC", ftfy.fix_text(old_val)
                    ).strip()
                    if new_val != old_val:
                        log_change(
                            row["RecordID"],
                            row["Name"],
                            col,
                            old_val,
                            new_val,
                            "System_GlobalCharFix",
                            "Global character fixing",
                            "",
                            user,
                            "CHAR_FIX",
                            prefix,
                        )
                        df_processed.loc[i, col] = new_val
    return df_processed


def format_budget_codes(df, user, prefix):
    df_processed = df.copy()
    if "BudgetCode" not in df_processed.columns:
        return df_processed
    mask = df_processed["BudgetCode"].notna() & (
        df_processed["BudgetCode"].astype(str).str.strip() != ""
    )
    for i in df_processed[mask].index:
        old_val = str(df_processed.loc[i, "BudgetCode"]).strip()
        try:
            new_val = str(int(float(old_val))).zfill(3)
            if new_val != old_val:
                log_change(
                    df_processed.loc[i, "RecordID"],
                    df_processed.loc[i, "Name"],
                    "BudgetCode",
                    old_val,
                    new_val,
                    "System_GlobalRule",
                    "Formatted BudgetCode",
                    "",
                    user,
                    "FORMAT_BUDGET_CODE",
                    prefix,
                )
                df_processed.loc[i, "BudgetCode"] = new_val
        except (ValueError, TypeError):
            print(
                f"Warning: Could not format non-numeric BudgetCode '{old_val}' "
                f"for RecordID {df_processed.loc[i, 'RecordID']}."
            )
    return df_processed


def main():
    parser = argparse.ArgumentParser(description="Apply global transformation rules.")
    parser.add_argument("--input_csv", type=pathlib.Path, required=True)
    parser.add_argument("--output_csv", type=pathlib.Path, required=True)
    parser.add_argument(
        "--changelog",
        type=pathlib.Path,
        required=True,
        help=(
            "Path to OUTPUT changelog file "
            "(NOT data/changelog.csv - use append_changelog.py for that)"
        ),
    )
    parser.add_argument("--changed_by", type=str, required=True)
    args = parser.parse_args()

    # PROTECTION: Prevent overwriting the main append-only changelog
    if args.changelog.resolve().name == "changelog.csv" and "data/changelog.csv" in str(
        args.changelog.resolve()
    ):
        print(
            "❌ ERROR: Cannot write directly to data/changelog.csv "
            "(append-only file).\n"
            "   This script should write to a temporary changelog "
            "in data/output/.\n"
            "   Use scripts/maint/append_changelog.py to append "
            "to the main changelog.\n"
            "   Example: --changelog data/output/"
            "changelog_v0_XX_global_rules.csv",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Not found '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    match = re.search(r"v(\d+_\d+)", args.output_csv.stem)
    prefix = match.group(0) if match else "v_unknown"

    name_cols_to_ensure = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]
    for col in name_cols_to_ensure:
        if col not in df.columns:
            print(f"Adding missing column: '{col}'")
            df[col] = ""

    df_processed = apply_global_character_fixing(df, args.changed_by, prefix)
    df_processed = apply_global_deduplication(df_processed, args.changed_by, prefix)
    df_processed = format_budget_codes(df_processed, args.changed_by, prefix)

    df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS).to_csv(
        args.changelog, index=False, encoding="utf-8-sig"
    )
    print(
        f"Global rules applied. Output: {args.output_csv}, Changelog: {args.changelog}"
    )


if __name__ == "__main__":
    main()
