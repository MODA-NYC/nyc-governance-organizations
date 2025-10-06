"""Module for applying QA edits to the golden dataset."""

from __future__ import annotations

import pathlib
import re
from datetime import datetime
from enum import Enum
from typing import Iterable

import pandas as pd

changelog_entries: list[dict] = []
changelog_id_counter = 0

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
    r"Set (?P<column>[\w_]+) to\s*(?P<value>.*)": QAAction.DIRECT_SET,
    r"Set to\s*(?P<value>.*)": QAAction.DIRECT_SET,
    r".*\?": QAAction.POLICY_QUERY,
}

SYNONYM_COLUMN_MAP = {
    "principal_officer_first_name": "PrincipalOfficerGivenName",
    "principal_officer_last_name": "PrincipalOfficerFamilyName",
    "principal_officer_contact_url": "PrincipalOfficerContactURL",
}


def reset_changelog() -> None:
    global changelog_entries, changelog_id_counter
    changelog_entries = []
    changelog_id_counter = 0


def _get_pascal_case_column(df_columns: Iterable[str], provided_col_name: str | None) -> str | None:
    if not provided_col_name or pd.isna(provided_col_name):
        return None
    provided_lower = str(provided_col_name).strip().lower()
    synonym_target = SYNONYM_COLUMN_MAP.get(provided_lower)
    if synonym_target and synonym_target in df_columns:
        return synonym_target
    for col in df_columns:
        if col.lower() == provided_lower:
            return col
    pascal_version = "".join(word.capitalize() for word in str(provided_col_name).strip().split("_"))
    if pascal_version in df_columns:
        return pascal_version
    return None


def _sanitize_wrapped_text(text: str | None) -> str | None:
    if text is None:
        return None
    s = str(text).strip()
    while len(s) > 1 and ((s.startswith("\"") and s.endswith("\"")) or (s.startswith("'") and s.endswith("'"))):
        s = s[1:-1].strip()
    if s.endswith("\"") or s.endswith("'"):
        s = s.rstrip("\"'").strip()
    return s


def log_change(
    record_id: str,
    record_name: str,
    column_changed: str,
    old_value,
    new_value,
    feedback_source: str,
    notes: str,
    reason: str,
    changed_by: str,
    rule_action: QAAction,
    version_prefix: str,
) -> None:
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
        "reason": reason,
        "changed_by": changed_by,
        "RuleAction": rule_action.value,
    }
    changelog_entries.append(entry)


def detect_rule(feedback: str) -> tuple[QAAction, re.Match | None]:
    for pattern, action in RULES.items():
        match = re.search(pattern, feedback, re.IGNORECASE)
        if match:
            return action, match
    return QAAction.POLICY_QUERY, None


def handle_delete_record(df: pd.DataFrame, record_id: str, src: str, user: str, notes: str, reason: str, prefix: str) -> pd.DataFrame:
    if record_id in df["RecordID"].values:
        record_name = df[df["RecordID"] == record_id].iloc[0].get("Name", "N/A")
        log_change(
            record_id,
            record_name,
            "_ROW_DELETED",
            record_name,
            "N/A",
            src,
            notes,
            reason,
            user,
            QAAction.DELETE_RECORD,
            prefix,
        )
        return df[df["RecordID"] != record_id].copy()
    log_change(
        record_id,
        "N/A",
        "_ROW_DELETE_FAILED",
        "Record Not Found",
        "N/A",
        src,
        f"Deletion failed: {notes}",
        reason,
        user,
        QAAction.DELETE_RECORD,
        prefix,
    )
    return df


def handle_append_from_csv(
    df: pd.DataFrame,
    path_str: str,
    base_dir: pathlib.Path,
    src: str,
    user: str,
    notes: str,
    reason: str,
    prefix: str,
) -> pd.DataFrame:
    path_obj = base_dir / path_str if not path_str.startswith("data/") else pathlib.Path(path_str)
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
                reason,
                user,
                QAAction.APPEND_FROM_CSV,
                prefix,
            )
        return pd.concat([df, new_records], ignore_index=True)
    except FileNotFoundError:
        return df


def handle_direct_set(
    df_mod: pd.DataFrame,
    qa_row: pd.Series,
    match: re.Match,
    src_name: str,
    user: str,
    prefix: str,
    feedback: str,
) -> None:
    record_id = qa_row.get("Row(s)")
    if pd.isna(record_id) or record_id not in df_mod["RecordID"].values:
        return
    provided_col = qa_row.get("Column") or (match.group("column") if "column" in match.groupdict() else None)
    pascal_col = _get_pascal_case_column(df_mod.columns, provided_col)
    if not pascal_col:
        return
    val_str = match.group("value")
    clean_val = _sanitize_wrapped_text(val_str)
    if clean_val is None:
        clean_val = ""
    target_indices = df_mod[df_mod["RecordID"] == record_id].index
    for index in target_indices:
        record_name = df_mod.loc[index, "Name"]
        old_val = df_mod.loc[index, pascal_col]
        reason = qa_row.get("reason", "")
        log_change(
            record_id,
            record_name,
            pascal_col,
            old_val,
            clean_val,
            src_name,
            feedback,
            reason,
            user,
            QAAction.DIRECT_SET,
            prefix,
        )
        df_mod.loc[index, pascal_col] = clean_val


def handle_policy_query(
    df_mod: pd.DataFrame,
    qa_row: pd.Series,
    src_name: str,
    user: str,
    prefix: str,
    feedback: str,
) -> None:
    record_id = qa_row.get("Row(s)")
    if pd.isna(record_id) or record_id not in df_mod["RecordID"].values:
        return
    pascal_col = _get_pascal_case_column(df_mod.columns, qa_row.get("Column"))
    target_indices = df_mod[df_mod["RecordID"] == record_id].index
    for index in target_indices:
        record_name = df_mod.loc[index, "Name"]
        reason = qa_row.get("reason", "")
        log_change(
            record_id,
            record_name,
            pascal_col or "Policy Question",
            "N/A",
            "N/A",
            src_name,
            feedback,
            reason,
            user,
            QAAction.POLICY_QUERY,
            prefix,
        )


def apply_qa_edits(
    df: pd.DataFrame,
    qa_path: pathlib.Path,
    user: str,
    prefix: str,
) -> pd.DataFrame:
    df_mod = df.copy()
    src_name, base_dir = qa_path.name, qa_path.parent
    qa_df = pd.read_csv(qa_path, dtype=str).fillna("")

    for _, qa_row in qa_df.iterrows():
        raw_feedback = str(qa_row.get("feedback", ""))
        feedback = _sanitize_wrapped_text(raw_feedback)
        if not raw_feedback.strip() and not feedback:
            continue
        reason = qa_row.get("reason", "")
        action, match = detect_rule(raw_feedback)

        if action == QAAction.DELETE_RECORD and match:
            df_mod = handle_delete_record(
                df_mod,
                match.group("record_id_to_delete"),
                src_name,
                user,
                feedback,
                reason,
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
                reason,
                prefix,
            )
        elif action == QAAction.DIRECT_SET and match:
            handle_direct_set(df_mod, qa_row, match, src_name, user, prefix, feedback)
        elif action == QAAction.POLICY_QUERY:
            handle_policy_query(df_mod, qa_row, src_name, user, prefix, feedback)

    return df_mod
