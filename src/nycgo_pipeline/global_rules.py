"""Global transformation rules applied to the golden dataset."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

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


def apply_global_deduplication(
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
    df_processed = df.copy()
    for col in ["AlternateOrFormerNames", "AlternateOrFormerAcronyms"]:
        if col in df_processed.columns:
            for i, row in df_processed.iterrows():
                old_val = row.get(col)
                if isinstance(old_val, str) and old_val.strip():
                    items = [
                        item.strip() for item in old_val.split(";") if item.strip()
                    ]
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


def apply_global_character_fixing(
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
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
                    new_val = unicodedata.normalize(
                        "NFKC", ftfy.fix_text(old_val)
                    ).strip()
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


def validate_phase_ii_fields(  # noqa: C901
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
    """
    Validate Phase II fields (v2.0.0 schema).

    Validates:
    - authorizing_url: Must be valid HTTP/HTTPS URL format
    - org_chart_oversight: Must match valid RecordID if populated
    - authorizing_authority: Warn if empty (100% population target)
    """
    df_processed = df.copy()

    # Validate authorizing_url format
    if "authorizing_url" in df_processed.columns:
        url_pattern = re.compile(r"^https?://[^\s]+$")
        for _i, row in df_processed.iterrows():  # noqa: B007
            url_value = row.get("authorizing_url", "").strip()
            if url_value and not url_pattern.match(url_value):
                # Check if it's pipe-separated multiple URLs
                urls = [u.strip() for u in url_value.split("|") if u.strip()]
                invalid_urls = [u for u in urls if not url_pattern.match(u)]
                if invalid_urls:
                    log_change(
                        row["RecordID"],
                        row.get("Name", ""),
                        "authorizing_url",
                        url_value,
                        None,  # No automatic fix, just warning
                        "System_Validation",
                        f"Invalid URL format: {invalid_urls}",
                        "VALIDATION_WARNING",
                        user,
                        "VALIDATE_URL",
                        prefix,
                    )

    # Validate org_chart_oversight references valid RecordID
    if "org_chart_oversight" in df_processed.columns:
        valid_record_ids = set(df_processed["RecordID"].tolist())
        for _i, row in df_processed.iterrows():  # noqa: B007
            oversight_value = row.get("org_chart_oversight", "").strip()
            if oversight_value and oversight_value not in valid_record_ids:
                log_change(
                    row["RecordID"],
                    row.get("Name", ""),
                    "org_chart_oversight",
                    oversight_value,
                    None,
                    "System_Validation",
                    f"RecordID '{oversight_value}' not found in dataset",
                    "VALIDATION_WARNING",
                    user,
                    "VALIDATE_RECORDID_REF",
                    prefix,
                )

    # Check authorizing_authority population (100% target)
    if "authorizing_authority" in df_processed.columns:
        empty_count = 0
        for _i, row in df_processed.iterrows():  # noqa: B007
            auth_value = row.get("authorizing_authority", "").strip()
            if not auth_value:
                empty_count += 1
        if empty_count > 0:
            # Log a single warning about missing authorizing_authority values
            msg = (
                f"{empty_count} entities missing authorizing_authority "
                f"(target: 100% population)"
            )
            log_change(
                "DATASET",
                "DATASET",
                "authorizing_authority",
                None,
                None,
                "System_Validation",
                msg,
                "VALIDATION_WARNING",
                user,
                "CHECK_COMPLETENESS",
                prefix,
            )

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
    df_processed = validate_phase_ii_fields(df_processed, changed_by, version_prefix)
    return df_processed
