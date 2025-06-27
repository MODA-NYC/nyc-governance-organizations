#!/usr/bin/env python3
import argparse
import pathlib
import re
import sys
from datetime import datetime
from enum import Enum

import pandas as pd

changelog_entries, changelog_id_counter = [], 0


class QAAction(Enum):
    DIRECT_SET = "direct_set"
    POLICY_QUERY = "policy_query"
    DELETE_RECORD = "delete_record"
    APPEND_FROM_CSV = "append_from_csv"


RULES = {
    r"Delete RecordID (?P<record_id_to_delete>\S+)": QAAction.DELETE_RECORD,
    r"^\s*Append records from CSV\s+(?P<csv_path_to_add>[\w./-]+\.csv)\s*$": (
        QAAction.APPEND_FROM_CSV
    ),
    r"Set (?P<column>[\w_]+) to (?P<value>.+)": QAAction.DIRECT_SET,
    r"Set to (?P<value>.+)": QAAction.DIRECT_SET,
    r".*\?": QAAction.POLICY_QUERY,
}
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
    "changed_by",
    "RuleAction",
]


def _get_pascal_case_column(df_columns, provided_col_name):
    """
    Finds the correct PascalCase column name from a list of columns,
    trying snake_case as a fallback.
    """
    if not provided_col_name or pd.isna(provided_col_name):
        return None
    # Add a fallback for simple case differences
    for col in df_columns:
        if col.lower() == str(provided_col_name).strip().lower():
            return col
    # Keep the original logic as a final attempt
    pascal_version = "".join(
        word.capitalize() for word in str(provided_col_name).strip().split("_")
    )
    if pascal_version in df_columns:
        return pascal_version
    print(f"⚠️ Warning: Could not find a matching column for '{provided_col_name}'.")
    return None


def log_change(
    record_id,
    record_name,
    column_changed,
    old_value,
    new_value,
    feedback_source,
    notes,
    changed_by,
    rule_action,
    version_prefix,
):
    global changelog_entries, changelog_id_counter
    changelog_id_counter += 1
    entry = {
        "ChangeID": f"{version_prefix}_{changelog_id_counter}",
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "record_name": record_name,
        "column_changed": column_changed,
        "old_value": old_value,
        "new_value": new_value,
        "feedback_source": feedback_source,
        "notes": notes,
        "changed_by": changed_by,
        "RuleAction": rule_action.value,
    }
    changelog_entries.append(entry)


def detect_rule(feedback):
    for pattern, action in RULES.items():
        match = re.search(pattern, feedback, re.IGNORECASE)
        if match:
            return action, match
    return QAAction.POLICY_QUERY, None


def handle_delete_record(df, id, src, user, notes, prefix):
    if id in df["RecordID"].values:
        record_name = df[df["RecordID"] == id].iloc[0].get("Name", "N/A")
        log_change(
            id,
            record_name,
            "_ROW_DELETED",
            record_name,
            "N/A",
            src,
            notes,
            user,
            QAAction.DELETE_RECORD,
            prefix,
        )
        return df[df["RecordID"] != id].copy()
    log_change(
        id,
        "N/A",
        "_ROW_DELETE_FAILED",
        "Record Not Found",
        "N/A",
        src,
        f"Deletion failed: {notes}",
        user,
        QAAction.DELETE_RECORD,
        prefix,
    )
    return df


def handle_append_from_csv(df, path_str, base_dir, src, user, notes, prefix):
    path_obj = (
        base_dir / path_str
        if not path_str.startswith("data/")
        else pathlib.Path(path_str)
    )
    try:
        new_records = pd.read_csv(path_obj, dtype=str, encoding="utf-8-sig").fillna("")
        for _, row in new_records.iterrows():
            log_change(
                row.get("RecordID", "N/A"),
                row.get("Name"),
                "_ROW_ADDED",
                "N/A",
                row.get("Name"),
                src,
                notes,
                user,
                QAAction.APPEND_FROM_CSV,
                prefix,
            )
        return pd.concat([df, new_records], ignore_index=True)
    except FileNotFoundError:
        print(
            f"❌ CRITICAL ERROR: File not found for append at '{path_obj}'.",
            file=sys.stderr,
        )
    return df


def handle_direct_set(df_mod, qa_row, match, src_name, user, prefix, feedback):
    record_id = qa_row.get("Row(s)")
    if pd.isna(record_id) or record_id not in df_mod["RecordID"].values:
        return

    target_indices = df_mod[df_mod["RecordID"] == record_id].index

    provided_col = qa_row.get("Column") or (
        match.group("column") if "column" in match.groupdict() else None
    )
    pascal_col = _get_pascal_case_column(df_mod.columns, provided_col)
    if not pascal_col:
        print(
            f"Warning: Skipping edit for RecordID {record_id} "
            f"due to unresolvable column '{provided_col}'."
        )
        return

    val_str = match.group("value")
    clean_val = val_str.strip()
    while len(clean_val) > 1 and (
        (clean_val.startswith('"') and clean_val.endswith('"'))
        or (clean_val.startswith("'") and clean_val.endswith("'"))
    ):
        clean_val = clean_val[1:-1].strip()

    for index in target_indices:
        record_name = df_mod.loc[index, "Name"]
        old_val = df_mod.loc[index, pascal_col]
        log_change(
            record_id,
            record_name,
            pascal_col,
            old_val,
            clean_val,
            src_name,
            feedback,
            user,
            QAAction.DIRECT_SET,
            prefix,
        )
        df_mod.loc[index, pascal_col] = clean_val


def handle_policy_query(df_mod, qa_row, src_name, user, prefix, feedback):
    record_id = qa_row.get("Row(s)")
    if pd.isna(record_id) or record_id not in df_mod["RecordID"].values:
        return

    target_indices = df_mod[df_mod["RecordID"] == record_id].index
    pascal_col = _get_pascal_case_column(df_mod.columns, qa_row.get("Column"))

    for index in target_indices:
        record_name = df_mod.loc[index, "Name"]
        log_change(
            record_id,
            record_name,
            pascal_col or "Policy Question",
            "N/A",
            "N/A",
            src_name,
            feedback,
            user,
            QAAction.POLICY_QUERY,
            prefix,
        )


def apply_qa_edits(df, qa_path, user, prefix):
    df_mod = df.copy()
    src_name, base_dir = qa_path.name, qa_path.parent
    qa_df = pd.read_csv(qa_path, dtype=str).fillna("")

    for _, qa_row in qa_df.iterrows():
        feedback = qa_row.get("feedback", "")
        if not feedback:
            continue
        action, match = detect_rule(feedback)

        if action == QAAction.DELETE_RECORD and match:
            df_mod = handle_delete_record(
                df_mod,
                match.group("record_id_to_delete"),
                src_name,
                user,
                feedback,
                prefix,
            )
        elif action == QAAction.APPEND_FROM_CSV and match:
            df_mod = handle_append_from_csv(
                df_mod,
                match.group("csv_path_to_add"),
                base_dir,
                src_name,
                user,
                feedback,
                prefix,
            )
        elif action == QAAction.DIRECT_SET and match:
            handle_direct_set(df_mod, qa_row, match, src_name, user, prefix, feedback)
        elif action == QAAction.POLICY_QUERY:
            handle_policy_query(df_mod, qa_row, src_name, user, prefix, feedback)

    return df_mod


def main():
    parser = argparse.ArgumentParser(description="Apply a QA/edits file.")
    parser.add_argument("--input_csv", type=pathlib.Path, required=True)
    parser.add_argument("--qa_csv", type=pathlib.Path, required=True)
    parser.add_argument("--output_csv", type=pathlib.Path, required=True)
    parser.add_argument("--changelog", type=pathlib.Path, required=True)
    parser.add_argument("--changed_by", type=str, required=True)
    args = parser.parse_args()
    try:
        df_input = pd.read_csv(args.input_csv, dtype=str).fillna("")
    except FileNotFoundError:
        print(f"Error: Not found '{args.input_csv}'", file=sys.stderr)
        sys.exit(1)

    match = re.search(r"v(\d+_\d+)", args.output_csv.stem)
    prefix = match.group(0) if match else "v_unknown"

    df_processed = apply_qa_edits(df_input, args.qa_csv, args.changed_by, prefix)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.changelog.parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS).to_csv(
        args.changelog, index=False, encoding="utf-8-sig"
    )
    print(f"Edits applied. Output: {args.output_csv}, Changelog: {args.changelog}")


if __name__ == "__main__":
    main()
