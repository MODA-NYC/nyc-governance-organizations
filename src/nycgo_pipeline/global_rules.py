"""Global transformation rules applied to the golden dataset."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Iterable

import ftfy
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


def reset_changelog() -> None:
    """Reset global changelog state (useful for tests)."""
    global changelog_entries, changelog_id_counter
    changelog_entries = []
    changelog_id_counter = 0


def log_change(
    record_id: str,
    record_name: str,
    column_changed: str,
    old_value: str | None,
    new_value: str | None,
    feedback_source: str,
    notes: str,
    reason: str,
    changed_by: str,
    rule_action: str,
    version_prefix: str,
) -> None:
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


def apply_global_deduplication(df: pd.DataFrame, user: str, prefix: str) -> pd.DataFrame:
    df_processed = df.copy()
    for col in ["AlternateOrFormerNames", "AlternateOrFormerAcronyms"]:
        if col in df_processed.columns:
            for i, row in df_processed.iterrows():
                old_val = row.get(col)
                if isinstance(old_val, str) and old_val.strip():
                    items = [item.strip() for item in old_val.split(";") if item.strip()]
                    new_val = ";".join(dict.fromkeys(items))
                    if new_val != old_val:
                        log_change(
                            row["RecordID"],
                            row.get("Name", ""),
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


def apply_global_character_fixing(df: pd.DataFrame, user: str, prefix: str) -> pd.DataFrame:
    df_processed = df.copy()
    text_cols: Iterable[str] = [
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
                    new_val = unicodedata.normalize("NFKC", ftfy.fix_text(old_val)).strip()
                    if new_val != old_val:
                        log_change(
                            row["RecordID"],
                            row.get("Name", ""),
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


def format_budget_codes(df: pd.DataFrame, user: str, prefix: str) -> pd.DataFrame:
    df_processed = df.copy()
    if "BudgetCode" not in df_processed.columns:
        return df_processed
    mask = df_processed["BudgetCode"].notna() & (df_processed["BudgetCode"].astype(str).str.strip() != "")
    for i in df_processed[mask].index:
        old_val = str(df_processed.loc[i, "BudgetCode"]).strip()
        try:
            new_val = str(int(float(old_val))).zfill(3)
            if new_val != old_val:
                log_change(
                    df_processed.loc[i, "RecordID"],
                    df_processed.loc[i].get("Name", ""),
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
            continue
    return df_processed


def apply_rules(
    input_csv: Path,
    *,
    changed_by: str,
    version_prefix: str,
) -> pd.DataFrame:
    df = pd.read_csv(input_csv, dtype=str).fillna("")
    df_processed = apply_global_character_fixing(df, changed_by, version_prefix)
    df_processed = apply_global_deduplication(df_processed, changed_by, version_prefix)
    df_processed = format_budget_codes(df_processed, changed_by, version_prefix)
    return df_processed
