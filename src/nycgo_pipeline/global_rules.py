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
    - RecordID format: Must be 6-digit numeric (e.g., 100318)
    - org_chart_oversight_record_id: Must reference valid RecordID if populated
    - parent_organization_record_id: Must reference valid RecordID if populated
    - Relationship validation: Entity cannot be its own parent/oversight
    - authorizing_url: Must be valid HTTP/HTTPS URL format
    - authorizing_authority_type: Controlled vocabulary check
    - authorizing_authority: Warn if empty (100% population target)
    """
    df_processed = df.copy()

    # Validate RecordID format (6-digit numeric)
    if "RecordID" in df_processed.columns:
        recordid_pattern = re.compile(r"^\d{6}$")
        for _i, row in df_processed.iterrows():  # noqa: B007
            record_id = str(row.get("RecordID", "")).strip()
            if record_id and not recordid_pattern.match(record_id):
                log_change(
                    record_id,
                    row.get("Name", ""),
                    "RecordID",
                    record_id,
                    None,
                    "System_Validation",
                    (
                        f"RecordID must be 6-digit numeric format "
                        f"(e.g., 100318), got: {record_id}"
                    ),
                    "VALIDATION_WARNING",
                    user,
                    "VALIDATE_RECORDID_FORMAT",
                    prefix,
                )

    # Get valid RecordIDs for reference validation
    valid_record_ids = set(df_processed["RecordID"].astype(str).str.strip().tolist())

    # Validate org_chart_oversight_record_id references valid RecordID
    oversight_cols = [
        "OrgChartOversightRecordID",
        "org_chart_oversight_record_id",
    ]
    for col in oversight_cols:
        if col in df_processed.columns:
            for _i, row in df_processed.iterrows():  # noqa: B007
                oversight_value = str(row.get(col, "")).strip()
                record_id = str(row.get("RecordID", "")).strip()

                if oversight_value:
                    # Check if it references a valid RecordID
                    if oversight_value not in valid_record_ids:
                        log_change(
                            record_id,
                            row.get("Name", ""),
                            col,
                            oversight_value,
                            None,
                            "System_Validation",
                            f"RecordID '{oversight_value}' not found in dataset",
                            "VALIDATION_WARNING",
                            user,
                            "VALIDATE_RECORDID_REF",
                            prefix,
                        )
                    # Check if entity is referencing itself
                    elif oversight_value == record_id:
                        log_change(
                            record_id,
                            row.get("Name", ""),
                            col,
                            oversight_value,
                            None,
                            "System_Validation",
                            "Entity cannot be its own org chart oversight",
                            "VALIDATION_WARNING",
                            user,
                            "VALIDATE_SELF_REFERENCE",
                            prefix,
                        )

    # Validate parent_organization_record_id references valid RecordID
    parent_cols = [
        "ParentOrganizationRecordID",
        "parent_organization_record_id",
    ]
    for col in parent_cols:
        if col in df_processed.columns:
            for _i, row in df_processed.iterrows():  # noqa: B007
                parent_value = str(row.get(col, "")).strip()
                record_id = str(row.get("RecordID", "")).strip()

                if parent_value:
                    # Check if it references a valid RecordID
                    if parent_value not in valid_record_ids:
                        log_change(
                            record_id,
                            row.get("Name", ""),
                            col,
                            parent_value,
                            None,
                            "System_Validation",
                            f"RecordID '{parent_value}' not found in dataset",
                            "VALIDATION_WARNING",
                            user,
                            "VALIDATE_RECORDID_REF",
                            prefix,
                        )
                    # Check if entity is referencing itself
                    elif parent_value == record_id:
                        log_change(
                            record_id,
                            row.get("Name", ""),
                            col,
                            parent_value,
                            None,
                            "System_Validation",
                            "Entity cannot be its own parent organization",
                            "VALIDATION_WARNING",
                            user,
                            "VALIDATE_SELF_REFERENCE",
                            prefix,
                        )

    # Validate authorizing_url format
    url_cols = ["AuthorizingURL", "authorizing_url"]
    for col in url_cols:
        if col in df_processed.columns:
            url_pattern = re.compile(r"^https?://[^\s]+$")
            for _i, row in df_processed.iterrows():  # noqa: B007
                url_value = str(row.get(col, "")).strip()
                if url_value and not url_pattern.match(url_value):
                    # Check if it's pipe-separated multiple URLs
                    urls = [u.strip() for u in url_value.split("|") if u.strip()]
                    invalid_urls = [u for u in urls if not url_pattern.match(u)]
                    if invalid_urls:
                        log_change(
                            row["RecordID"],
                            row.get("Name", ""),
                            col,
                            url_value,
                            None,  # No automatic fix, just warning
                            "System_Validation",
                            f"Invalid URL format: {invalid_urls}",
                            "VALIDATION_WARNING",
                            user,
                            "VALIDATE_URL",
                            prefix,
                        )

    # Validate authorizing_authority_type controlled vocabulary
    auth_type_cols = [
        "AuthorizingAuthorityType",
        "authorizing_authority_type",
    ]
    valid_auth_types = {
        "NYC Charter",
        "NYC Administrative Code",
        "City Council Local Law",
        "Mayoral Executive Order",
        "New York State Law",
        "Federal Law",
        "Other",
    }
    for col in auth_type_cols:
        if col in df_processed.columns:
            for _i, row in df_processed.iterrows():  # noqa: B007
                auth_type = str(row.get(col, "")).strip()
                if auth_type and auth_type not in valid_auth_types:
                    log_change(
                        row["RecordID"],
                        row.get("Name", ""),
                        col,
                        auth_type,
                        None,
                        "System_Validation",
                        (
                            f"Invalid authorizing_authority_type. "
                            f"Valid values: {', '.join(sorted(valid_auth_types))}"
                        ),
                        "VALIDATION_WARNING",
                        user,
                        "VALIDATE_CONTROLLED_VOCAB",
                        prefix,
                    )

    # Check authorizing_authority population (100% target)
    auth_cols = ["AuthorizingAuthority", "authorizing_authority"]
    for col in auth_cols:
        if col in df_processed.columns:
            empty_count = 0
            for _i, row in df_processed.iterrows():  # noqa: B007
                auth_value = str(row.get(col, "")).strip()
                if not auth_value:
                    empty_count += 1
            if empty_count > 0:
                # Log a single warning about missing authorizing_authority values
                msg = (
                    f"{empty_count} entities missing {col} "
                    f"(target: 100% population)"
                )
                log_change(
                    "DATASET",
                    "DATASET",
                    col,
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


def sync_nycgov_directory_status(
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
    """Sync NYC.gov Agency Directory field based on OperationalStatus.

    Records with OperationalStatus != 'Active' should have NYC.gov Agency Directory
    set to False. This ensures the golden dataset stays in sync with the business
    rules applied during export.

    Args:
        df: DataFrame to process
        user: User making the change (for changelog)
        prefix: Version prefix for changelog IDs

    Returns:
        Processed DataFrame with synced directory field
    """
    df_processed = df.copy()
    col = "NYC.gov Agency Directory"

    if col not in df_processed.columns:
        return df_processed

    if "OperationalStatus" not in df_processed.columns:
        return df_processed

    for i, row in df_processed.iterrows():
        op_status = str(row.get("OperationalStatus", "")).strip().lower()
        current_val = str(row.get(col, "")).strip()

        # If not Active and currently marked as True, set to False
        if op_status != "active" and current_val.lower() == "true":
            log_change(
                row["RecordID"],
                row.get("Name", ""),
                col,
                current_val,
                "False",
                "System_GlobalRule",
                (
                    f"OperationalStatus is '{row.get('OperationalStatus', '')}', "
                    "not Active"
                ),
                "SYNC_DIRECTORY_STATUS",
                user,
                "SYNC_NYCGOV_DIRECTORY",
                prefix,
            )
            df_processed.loc[i, col] = "False"

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
    df_processed = sync_nycgov_directory_status(
        df_processed, changed_by, version_prefix
    )
    df_processed = validate_phase_ii_fields(df_processed, changed_by, version_prefix)
    return df_processed
