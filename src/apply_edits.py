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
    r"^\s*Append records from CSV\s+"
    r"(?P<csv_path_to_add>[\w./-]+\.csv)\s*$": QAAction.APPEND_FROM_CSV,
    r"Set (?P<column>\w+) to (?P<value>.+)": QAAction.DIRECT_SET,
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
    if provided_col_name in df_columns:
        return provided_col_name

    pascal_version = "".join(word.capitalize() for word in provided_col_name.split("_"))
    if pascal_version in df_columns:
        return pascal_version

    return None  # Return None if no match is found


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
            "changed_by": changed_by,
            "RuleAction": rule_action.value,
        }
    )


def detect_rule(feedback):
    for pattern, action in RULES.items():
        if match := re.search(pattern, feedback, re.IGNORECASE):
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
    csv_path_obj = pathlib.Path(path_str)

    # Determine the correct path.
    if csv_path_obj.is_absolute() or path_str.startswith("data/"):
        resolved_csv_path = csv_path_obj
    else:
        resolved_csv_path = base_dir / csv_path_obj

    try:
        # Use 'utf-8-sig' to handle potential BOM characters in the CSV file
        print(f"📥 Attempting to read records from: {resolved_csv_path}")
        new_records = pd.read_csv(
            resolved_csv_path, dtype=str, encoding="utf-8-sig"
        ).fillna("")
        print(f"✅ Successfully read {len(new_records)} records from CSV.")

        if new_records.empty:
            print(f"⚠️ Warning: CSV file for append at '{resolved_csv_path}' is empty.")
            return df

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
        error_msg = (
            "❌ CRITICAL ERROR: File not found for append operation at "
            f"'{resolved_csv_path}'."
        )
        print(error_msg, file=sys.stderr)
        return df
    except Exception as e:
        error_msg = (
            "❌ CRITICAL ERROR: An unexpected error occurred during CSV append: " f"{e}"
        )
        print(error_msg, file=sys.stderr)
        return df


def _handle_direct_set_action(
    row_series,
    qa_row,
    match,
    df_mod,
    record_name,
    src_name,
    user,
    prefix,
):
    """Helper function to handle the direct set logic."""
    provided_col = qa_row.get("Column") or (
        match.group("column") if "column" in match.groupdict() else None
    )
    val_str = match.group("value")

    pascal_col = _get_pascal_case_column(df_mod.columns, provided_col)

    if pascal_col and val_str is not None:
        old_val = row_series.get(pascal_col)
        clean_val = val_str.strip()
        while (
            len(clean_val) > 1 and clean_val.startswith('"') and clean_val.endswith('"')
        ):
            clean_val = clean_val[1:-1].strip()
        while (
            len(clean_val) > 1 and clean_val.startswith("'") and clean_val.endswith("'")
        ):
            clean_val = clean_val[1:-1].strip()

        log_change(
            row_series["RecordID"],
            record_name,
            pascal_col,
            old_val,
            clean_val,
            src_name,
            qa_row.get("feedback"),
            user,
            QAAction.DIRECT_SET,
            prefix,
        )
        row_series[pascal_col] = clean_val
    return row_series


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
            continue
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
            continue

        record_id = qa_row.get("Row(s)")
        if pd.isna(record_id) or record_id not in df_mod["RecordID"].values:
            continue

        target_indices = df_mod[df_mod["RecordID"] == record_id].index
        for index in target_indices:
            row_series = df_mod.loc[index].copy()
            record_name = row_series.get("Name", "")

            if action == QAAction.DIRECT_SET and match:
                modified_row = _handle_direct_set_action(
                    row_series,
                    qa_row,
                    match,
                    df_mod,
                    record_name,
                    src_name,
                    user,
                    prefix,
                )
                df_mod.loc[index] = modified_row

            elif action == QAAction.POLICY_QUERY:
                log_change(
                    record_id,
                    record_name,
                    qa_row.get("Column", "Policy Question"),
                    "N/A",
                    "N/A",
                    src_name,
                    feedback,
                    user,
                    QAAction.POLICY_QUERY,
                    prefix,
                )
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

    df_processed.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(changelog_entries, columns=CHANGELOG_COLUMNS).to_csv(
        args.changelog, index=False, encoding="utf-8-sig"
    )
    print(f"Edits applied. Output: {args.output_csv}, Changelog: {args.changelog}")


if __name__ == "__main__":
    main()
