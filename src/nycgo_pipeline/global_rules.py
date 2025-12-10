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
    for col in ["alternate_or_former_names", "alternate_or_former_acronyms"]:
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
                            row["record_id"],
                            row.get("name", ""),
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
        "name",
        "name_alphabetized",
        "description",
        "alternate_or_former_names",
        "alternate_or_former_acronyms",
        "principal_officer_name",
        "principal_officer_title",
        "notes",
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
                            row["record_id"],
                            row.get("name", ""),
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
    if "budget_code" not in df_processed.columns:
        return df_processed
    mask = df_processed["budget_code"].notna() & (
        df_processed["budget_code"].astype(str).str.strip() != ""
    )
    for i in df_processed[mask].index:
        old_val = str(df_processed.loc[i, "budget_code"]).strip()
        try:
            new_val = str(int(float(old_val))).zfill(3)
            if new_val != old_val:
                log_change(
                    df_processed.loc[i, "record_id"],
                    df_processed.loc[i].get("name", ""),
                    "budget_code",
                    old_val,
                    new_val,
                    "System_GlobalRule",
                    "Formatted budget_code",
                    "",
                    user,
                    "FORMAT_BUDGET_CODE",
                    prefix,
                )
                df_processed.loc[i, "budget_code"] = new_val
        except (ValueError, TypeError):
            continue
    return df_processed


def validate_phase_ii_fields(  # noqa: C901
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
    """
    Validate Phase II fields (v2.0.0 schema).

    Validates:
    - record_id format: Must be 6-digit numeric (e.g., 100318)
    - org_chart_oversight_record_id: Must reference valid record_id if populated
    - parent_organization_record_id: Must reference valid record_id if populated
    - Relationship validation: Entity cannot be its own parent/oversight
    - authorizing_url: Must be valid HTTP/HTTPS URL format
    - authorizing_authority_type: Controlled vocabulary check
    - authorizing_authority: Warn if empty (100% population target)
    """
    df_processed = df.copy()

    # Validate record_id format (6-digit numeric)
    if "record_id" in df_processed.columns:
        recordid_pattern = re.compile(r"^\d{6}$")
        for _i, row in df_processed.iterrows():  # noqa: B007
            record_id = str(row.get("record_id", "")).strip()
            if record_id and not recordid_pattern.match(record_id):
                log_change(
                    record_id,
                    row.get("name", ""),
                    "record_id",
                    record_id,
                    None,
                    "System_Validation",
                    (
                        f"record_id must be 6-digit numeric format "
                        f"(e.g., 100318), got: {record_id}"
                    ),
                    "VALIDATION_WARNING",
                    user,
                    "VALIDATE_RECORDID_FORMAT",
                    prefix,
                )

    # Get valid record_ids for reference validation
    valid_record_ids = set(df_processed["record_id"].astype(str).str.strip().tolist())

    # Validate org_chart_oversight_record_id references valid record_id
    if "org_chart_oversight_record_id" in df_processed.columns:
        col = "org_chart_oversight_record_id"
        for _i, row in df_processed.iterrows():  # noqa: B007
            oversight_value = str(row.get(col, "")).strip()
            record_id = str(row.get("record_id", "")).strip()

            if oversight_value:
                # Check if it references a valid record_id
                if oversight_value not in valid_record_ids:
                    log_change(
                        record_id,
                        row.get("name", ""),
                        col,
                        oversight_value,
                        None,
                        "System_Validation",
                        f"record_id '{oversight_value}' not found in dataset",
                        "VALIDATION_WARNING",
                        user,
                        "VALIDATE_RECORDID_REF",
                        prefix,
                    )
                # Check if entity is referencing itself
                elif oversight_value == record_id:
                    log_change(
                        record_id,
                        row.get("name", ""),
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

    # Validate parent_organization_record_id references valid record_id
    if "parent_organization_record_id" in df_processed.columns:
        col = "parent_organization_record_id"
        for _i, row in df_processed.iterrows():  # noqa: B007
            parent_value = str(row.get(col, "")).strip()
            record_id = str(row.get("record_id", "")).strip()

            if parent_value:
                # Check if it references a valid record_id
                if parent_value not in valid_record_ids:
                    log_change(
                        record_id,
                        row.get("name", ""),
                        col,
                        parent_value,
                        None,
                        "System_Validation",
                        f"record_id '{parent_value}' not found in dataset",
                        "VALIDATION_WARNING",
                        user,
                        "VALIDATE_RECORDID_REF",
                        prefix,
                    )
                # Check if entity is referencing itself
                elif parent_value == record_id:
                    log_change(
                        record_id,
                        row.get("name", ""),
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
    if "authorizing_url" in df_processed.columns:
        col = "authorizing_url"
        url_pattern = re.compile(r"^https?://[^\s]+$")
        for _i, row in df_processed.iterrows():  # noqa: B007
            url_value = str(row.get(col, "")).strip()
            if url_value and not url_pattern.match(url_value):
                # Check if it's pipe-separated multiple URLs
                urls = [u.strip() for u in url_value.split("|") if u.strip()]
                invalid_urls = [u for u in urls if not url_pattern.match(u)]
                if invalid_urls:
                    log_change(
                        row["record_id"],
                        row.get("name", ""),
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
    valid_auth_types = {
        "NYC Charter",
        "NYC Administrative Code",
        "City Council Local Law",
        "Mayoral Executive Order",
        "New York State Law",
        "Federal Law",
        "Other",
    }
    if "authorizing_authority_type" in df_processed.columns:
        col = "authorizing_authority_type"
        for _i, row in df_processed.iterrows():  # noqa: B007
            auth_type = str(row.get(col, "")).strip()
            if auth_type and auth_type not in valid_auth_types:
                log_change(
                    row["record_id"],
                    row.get("name", ""),
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
    if "authorizing_authority" in df_processed.columns:
        col = "authorizing_authority"
        empty_count = 0
        for _i, row in df_processed.iterrows():  # noqa: B007
            auth_value = str(row.get(col, "")).strip()
            if not auth_value:
                empty_count += 1
        if empty_count > 0:
            # Log a single warning about missing authorizing_authority values
            msg = f"{empty_count} entities missing {col} " f"(target: 100% population)"
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


def format_boolean_fields(df: pd.DataFrame, user: str, prefix: str) -> pd.DataFrame:
    """Standardize boolean fields to uppercase TRUE/FALSE format (Sprint 5 Phase 1).

    Converts True/False/true/false/1/0/yes/no to uppercase TRUE/FALSE.
    Matches Excel/spreadsheet conventions and published format.

    Args:
        df: DataFrame to process
        user: User making the change (for changelog)
        prefix: Version prefix for changelog IDs

    Returns:
        Processed DataFrame with standardized boolean values
    """
    df_processed = df.copy()
    boolean_fields = [
        "in_org_chart",
        "listed_in_nyc_gov_agency_directory",
        "jan_2025_org_chart",
    ]

    for col in boolean_fields:
        if col not in df_processed.columns:
            continue

        for i, row in df_processed.iterrows():
            old_val = str(row.get(col, "")).strip()
            if not old_val:
                continue

            # Normalize to uppercase TRUE/FALSE
            val_lower = old_val.lower()
            if val_lower in ("true", "1", "t", "yes"):
                new_val = "TRUE"
            elif val_lower in ("false", "0", "f", "no"):
                new_val = "FALSE"
            else:
                continue  # Leave non-boolean values unchanged

            if new_val != old_val:
                log_change(
                    row["record_id"],
                    row.get("name", ""),
                    col,
                    old_val,
                    new_val,
                    "System_GlobalRule",
                    "Standardized boolean format",
                    "",
                    user,
                    "FORMAT_BOOLEAN",
                    prefix,
                )
                df_processed.loc[i, col] = new_val

    return df_processed


def format_founding_year(df: pd.DataFrame, user: str, prefix: str) -> pd.DataFrame:
    """Remove .0 suffix from founding_year field (Sprint 5 Phase 2).

    Converts float-formatted years like "1996.0" to clean integers like "1996".

    Args:
        df: DataFrame to process
        user: User making the change (for changelog)
        prefix: Version prefix for changelog IDs

    Returns:
        Processed DataFrame with cleaned founding_year values
    """
    df_processed = df.copy()
    col = "founding_year"

    if col not in df_processed.columns:
        return df_processed

    for i, row in df_processed.iterrows():
        old_val = str(row.get(col, "")).strip()
        if not old_val:
            continue

        try:
            # Handle float inputs (e.g., "1996.0" -> "1996")
            if "." in old_val:
                new_val = str(int(float(old_val)))
                if new_val != old_val:
                    log_change(
                        row["record_id"],
                        row.get("name", ""),
                        col,
                        old_val,
                        new_val,
                        "System_GlobalRule",
                        "Removed .0 suffix from year",
                        "",
                        user,
                        "FORMAT_YEAR",
                        prefix,
                    )
                    df_processed.loc[i, col] = new_val
        except (ValueError, TypeError):
            continue

    return df_processed


def sync_nycgov_directory_status(
    df: pd.DataFrame, user: str, prefix: str
) -> pd.DataFrame:
    """Sync listed_in_nyc_gov_agency_directory field based on operational_status.

    Records with operational_status != 'Active' should have the directory field
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
    col = "listed_in_nyc_gov_agency_directory"

    if col not in df_processed.columns:
        return df_processed

    if "operational_status" not in df_processed.columns:
        return df_processed

    for i, row in df_processed.iterrows():
        op_status = str(row.get("operational_status", "")).strip().lower()
        current_val = str(row.get(col, "")).strip()

        # If not Active and currently marked as True, set to False
        if op_status != "active" and current_val.lower() == "true":
            log_change(
                row["record_id"],
                row.get("name", ""),
                col,
                current_val,
                "False",
                "System_GlobalRule",
                (
                    f"operational_status is '{row.get('operational_status', '')}', "
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
    df_processed = format_boolean_fields(df_processed, changed_by, version_prefix)
    df_processed = format_founding_year(df_processed, changed_by, version_prefix)
    df_processed = sync_nycgov_directory_status(
        df_processed, changed_by, version_prefix
    )
    df_processed = validate_phase_ii_fields(df_processed, changed_by, version_prefix)
    return df_processed
