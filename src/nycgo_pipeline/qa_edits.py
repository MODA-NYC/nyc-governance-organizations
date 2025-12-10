"""Module for applying QA edits to the golden dataset."""

from __future__ import annotations

import pathlib
import re
from collections.abc import Iterable
from datetime import datetime
from enum import Enum

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
    "evidence_url",
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

# Column synonyms for backward compatibility with edit files
# Maps common variations to canonical snake_case names
SYNONYM_COLUMN_MAP = {
    "principal_officer_first_name": "principal_officer_given_name",
    "principal_officer_last_name": "principal_officer_family_name",
}


def reset_changelog() -> None:
    global changelog_entries, changelog_id_counter
    changelog_entries = []
    changelog_id_counter = 0


def _get_column(df_columns: Iterable[str], provided_col_name: str | None) -> str | None:
    """Find matching column name in dataframe.

    Handles snake_case columns and common synonyms.
    """
    if not provided_col_name or pd.isna(provided_col_name):
        return None
    provided_lower = str(provided_col_name).strip().lower()
    # Check synonym mapping
    synonym_target = SYNONYM_COLUMN_MAP.get(provided_lower)
    if synonym_target and synonym_target in df_columns:
        return synonym_target
    # Direct match (case-insensitive)
    for col in df_columns:
        if col.lower() == provided_lower:
            return col
    # Try with underscores replaced by nothing (to match legacy PascalCase)
    snake_version = provided_lower.replace(" ", "_")
    for col in df_columns:
        if col.lower() == snake_version:
            return col
    return None


def _sanitize_wrapped_text(text: str | None) -> str | None:
    if text is None:
        return None
    s = str(text).strip()
    while len(s) > 1 and (
        (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    if s.endswith('"') or s.endswith("'"):
        s = s.rstrip("\"'").strip()
    return s


def _get_qa_column(
    qa_row: pd.Series, old_name: str, new_name: str, default: str = ""
) -> str:
    """
    Get column value with backward compatibility for renamed columns.

    Checks for new column name first, then falls back to old name.
    This allows gradual migration from old to new column names.

    Args:
        qa_row: Row from QA edits CSV
        old_name: Legacy column name (e.g., "Row(s)")
        new_name: New column name (e.g., "record_id")
        default: Default value if neither column exists

    Returns:
        Column value as string
    """
    # Try new name first
    if new_name in qa_row.index:
        val = qa_row.get(new_name)
        if pd.notna(val) and str(val).strip():
            return str(val).strip()
    # Fall back to old name
    if old_name in qa_row.index:
        val = qa_row.get(old_name)
        if pd.notna(val) and str(val).strip():
            return str(val).strip()
    return default


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
    evidence_url: str = "",
) -> None:
    """
    Log a change to the changelog.

    Args:
        record_id: RecordID of the changed record
        record_name: Name of the changed record
        column_changed: Name of the field that changed
        old_value: Previous value
        new_value: New value
        feedback_source: Source file/name for this change
        notes: Additional notes (e.g., original feedback text)
        reason: Narrative justification for the change
        changed_by: User/operator who made the change
        rule_action: Type of action (DIRECT_SET, POLICY_QUERY, etc.)
        version_prefix: Prefix for ChangeID
        evidence_url: URL(s) providing evidence (pipe-separated if multiple)
    """
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
        "evidence_url": evidence_url,
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


def handle_delete_record(
    df: pd.DataFrame,
    record_id: str,
    src: str,
    user: str,
    notes: str,
    reason: str,
    prefix: str,
    evidence_url: str = "",
) -> pd.DataFrame:
    if record_id in df["record_id"].values:
        record_name = df[df["record_id"] == record_id].iloc[0].get("name", "N/A")
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
            evidence_url=evidence_url,
        )
        return df[df["record_id"] != record_id].copy()
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
        evidence_url=evidence_url,
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
    evidence_url: str = "",
) -> pd.DataFrame:
    path_obj = (
        base_dir / path_str
        if not path_str.startswith("data/")
        else pathlib.Path(path_str)
    )
    try:
        new_records = pd.read_csv(path_obj, dtype=str, encoding="utf-8-sig").fillna("")
        for _, row in new_records.iterrows():
            log_change(
                row.get("record_id", "N/A"),
                row.get("name"),
                "_ROW_ADDED",
                "N/A",
                row.get("name"),
                src,
                notes,
                reason,
                user,
                QAAction.APPEND_FROM_CSV,
                prefix,
                evidence_url=evidence_url,
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
    raw_record_id = _get_qa_column(qa_row, "Row(s)", "record_id")
    # Handle "NEW" records separately - they are processed in apply_qa_edits
    # before this function
    if pd.isna(raw_record_id) or str(raw_record_id).strip().upper() == "NEW":
        return
    # Normalize record_id to match dataframe format
    record_id = _normalize_record_id(raw_record_id, df_mod["record_id"])
    if record_id not in df_mod["record_id"].values:
        return

    # Get record_name from edits file if provided, otherwise lookup from dataset
    provided_record_name = _get_qa_column(qa_row, "", "record_name")
    if provided_record_name:
        # Validate that provided name matches dataset (if record exists)
        dataset_record_name = (
            df_mod[df_mod["record_id"] == record_id].iloc[0].get("name", "")
        )
        if dataset_record_name and provided_record_name != dataset_record_name:
            # Log warning but continue (allows for name corrections)
            print(
                f"Warning: record_name mismatch for record_id {record_id}: "
                f"provided '{provided_record_name}' vs dataset '{dataset_record_name}'"
            )

    provided_col = _get_qa_column(qa_row, "Column", "field_name") or (
        match.group("column") if "column" in match.groupdict() else None
    )
    target_col = _get_column(df_mod.columns, provided_col)
    if not target_col:
        return
    val_str = match.group("value")
    clean_val = _sanitize_wrapped_text(val_str)
    if clean_val is None:
        clean_val = ""
    target_indices = df_mod[df_mod["record_id"] == record_id].index
    for index in target_indices:
        # Use provided record_name if available, otherwise lookup from dataset
        record_name = (
            provided_record_name if provided_record_name else df_mod.loc[index, "name"]
        )
        old_val = df_mod.loc[index, target_col]
        justification = _get_qa_column(qa_row, "reason", "justification")
        evidence_url = _get_qa_column(qa_row, "", "evidence_url")
        # Store evidence_url separately; keep reason as just the justification
        # (evidence_url will be mapped to published changelog separately)
        reason = justification
        log_change(
            record_id,
            record_name,
            target_col,
            old_val,
            clean_val,
            src_name,
            feedback,
            reason,
            user,
            QAAction.DIRECT_SET,
            prefix,
            evidence_url=evidence_url,
        )
        df_mod.loc[index, target_col] = clean_val


def handle_policy_query(
    df_mod: pd.DataFrame,
    qa_row: pd.Series,
    src_name: str,
    user: str,
    prefix: str,
    feedback: str,
) -> None:
    raw_record_id = _get_qa_column(qa_row, "Row(s)", "record_id")
    if pd.isna(raw_record_id):
        return
    # Normalize record_id to match dataframe format
    record_id = _normalize_record_id(raw_record_id, df_mod["record_id"])
    if record_id not in df_mod["record_id"].values:
        return

    # Get record_name from edits file if provided, otherwise lookup from dataset
    provided_record_name = _get_qa_column(qa_row, "", "record_name")

    provided_col = _get_qa_column(qa_row, "Column", "field_name")
    target_col = _get_column(df_mod.columns, provided_col)
    target_indices = df_mod[df_mod["record_id"] == record_id].index
    for index in target_indices:
        # Use provided record_name if available, otherwise lookup from dataset
        record_name = (
            provided_record_name if provided_record_name else df_mod.loc[index, "name"]
        )
        justification = _get_qa_column(qa_row, "reason", "justification")
        evidence_url = _get_qa_column(qa_row, "", "evidence_url")
        # Store evidence_url separately; keep reason as just the justification
        reason = justification
        log_change(
            record_id,
            record_name,
            target_col or "Policy Question",
            "N/A",
            "N/A",
            src_name,
            feedback,
            reason,
            user,
            QAAction.POLICY_QUERY,
            prefix,
            evidence_url=evidence_url,
        )


def _normalize_record_id(record_id: str, df_columns: pd.Index) -> str:
    """
    Normalize a record_id to match the format used in the dataframe.

    Handles both NYC_GOID_XXXXXX and numeric (100XXX) formats by checking
    what exists in the dataframe.

    Args:
        record_id: The record_id from QA edits (may be numeric or old format)
        df_columns: The RecordID column values from the dataframe

    Returns:
        The record_id in the format that exists in the dataframe,
        or original if no match.
    """
    record_id = str(record_id).strip()

    # If already in dataframe, return as-is
    if record_id in df_columns.values:
        return record_id

    # Try converting from numeric to NYC_GOID format
    if re.match(r"^\d{5,6}$", record_id):
        # Numeric format like 100430 - convert to NYC_GOID_000430
        numeric = int(record_id)
        if numeric >= 100000:
            suffix = numeric - 100000
            old_format = f"NYC_GOID_{suffix:06d}"
            if old_format in df_columns.values:
                return old_format

    # Try converting from NYC_GOID to numeric format
    match = re.match(r"NYC_GOID_(\d+)", record_id)
    if match:
        numeric = int(match.group(1))
        new_format = str(100000 + numeric)
        if new_format in df_columns.values:
            return new_format

    # Return original if no conversion found
    return record_id


def _convert_recordid_to_new_format(old_id: str) -> int | None:
    """
    Convert RecordID from old format (NYC_GOID_XXXXXX) to new format (6-digit numeric).

    Returns the numeric value in new format, or None if invalid.
    Examples:
    - NYC_GOID_000022 → 100022
    - NYC_GOID_000318 → 100318
    - NYC_GOID_100026 → 110026
    """
    if pd.isna(old_id) or old_id == "":
        return None

    old_id_str = str(old_id).strip()

    # Check if already in new format (6-digit numeric)
    if re.match(r"^\d{6}$", old_id_str):
        return int(old_id_str)

    # Check if in old format (NYC_GOID_XXXXXX)
    match = re.match(r"NYC_GOID_(\d+)", old_id_str)
    if not match:
        return None

    numeric_str = match.group(1)
    numeric_int = int(numeric_str)

    # Convert to new format
    # If 6 digits starting with "1", take last 4 digits and add "11" prefix
    if len(numeric_str) == 6 and numeric_str.startswith("1"):
        last_four = int(numeric_str[2:])  # Skip first 2 digits
        new_id = int(f"11{last_four:04d}")
    else:
        # Add "1" prefix and pad to 6 digits
        new_id = int(f"1{numeric_int:05d}")

    return new_id


def _generate_next_record_id(df: pd.DataFrame) -> str:
    """
    Generate the next available record_id in new 6-digit numeric format.

    Ensures uniqueness by:
    1. Converting all existing IDs to new format
    2. Finding the maximum ID
    3. Generating next sequential ID (max + 1)
    4. Verifying the generated ID doesn't already exist (handles edge cases)

    Returns:
        A 6-digit numeric string (e.g., "100318")

    Note: This approach ensures uniqueness within the current dataset.
    For concurrent operations, ensure records are added sequentially or
    use a transaction/locking mechanism.
    """
    existing_ids = df["record_id"].astype(str)

    # Convert all existing IDs to new format and find max
    max_new_id = 100000  # Start from minimum valid ID
    existing_new_format_ids = set()

    for record_id in existing_ids:
        if pd.isna(record_id):
            continue
        try:
            new_format_id = _convert_recordid_to_new_format(str(record_id))
            if new_format_id is not None:
                existing_new_format_ids.add(new_format_id)
                max_new_id = max(max_new_id, new_format_id)
        except (ValueError, AttributeError):
            continue

    # Generate next ID in new 6-digit format
    next_num = max_new_id + 1

    # Safety check: ensure generated ID doesn't already exist
    # (handles edge cases like gaps in sequence or concurrent operations)
    while next_num in existing_new_format_ids:
        next_num += 1

    # Ensure it's 6 digits (should already be, but pad just in case)
    generated_id = f"{next_num:06d}"

    # Final validation: ensure we haven't exceeded 6-digit range
    if len(generated_id) > 6 or int(generated_id) > 999999:
        raise ValueError(
            f"RecordID sequence exhausted. Generated ID {generated_id} exceeds "
            "6-digit limit. Consider migrating to a new ID format."
        )

    return generated_id


def _create_new_record(
    df_mod: pd.DataFrame,
    new_record_fields: dict,
    src_name: str,
    user: str,
    prefix: str,
) -> pd.DataFrame:
    """Create a new record from collected field values."""
    # Generate record_id
    new_record_id = _generate_next_record_id(df_mod)

    # Create new row with all columns initialized to empty string
    new_row = {col: "" for col in df_mod.columns}

    # Set record_id
    new_row["record_id"] = new_record_id

    # Apply all collected field values
    for target_col, value in new_record_fields.items():
        if target_col in df_mod.columns:
            new_row[target_col] = value

    # Get record name for changelog
    record_name = new_record_fields.get("name", "New Record")

    # Log the creation
    log_change(
        new_record_id,
        record_name,
        "_ROW_ADDED",
        "N/A",
        record_name,
        src_name,
        f"New record created with {len(new_record_fields)} fields",
        "",
        user,
        QAAction.DIRECT_SET,
        prefix,
    )

    # Append new row to dataframe
    new_df = pd.DataFrame([new_row])
    return pd.concat([df_mod, new_df], ignore_index=True)


def apply_qa_edits(  # noqa: C901
    df: pd.DataFrame,
    qa_path: pathlib.Path,
    user: str,
    prefix: str,
) -> pd.DataFrame:
    """
    Apply QA edits from CSV file to golden dataset.

    CSV Column Names (supports old and new names for backward compatibility):
    - record_id (old: Row(s)): RecordID for existing records, or 'NEW'
    - record_name (optional): Entity name for human review and validation
    - field_name (old: Column): Name of the field to modify
    - action (old: feedback): Action instruction, e.g., 'Set to "value"'
    - justification (old: reason): Narrative explanation for the change
    - evidence_url (new): URL(s) providing evidence (pipe-separated)

    Note: record_name is optional but recommended for existing records to
    improve human review and changelog traceability. If not provided, the
    pipeline will lookup the name from the dataset. For NEW records,
    record_name is not needed (name field serves this purpose).

    Supports two types of edits:
    1. Edits to existing records: Use RecordID in 'record_id' column
    2. New record creation: Use 'NEW' in 'record_id' column

    NEW Record Handling:
    - Multiple NEW records per file are supported
    - Each NEW record should include a 'name' field to distinguish it
    - The 'name' field value is used as the key to group fields
    - Best practice: Include 'name' field as the first field
    - If 'name' field comes after other fields, those fields will be temporarily tracked
      and migrated to the name-based key when the name field is encountered

    Example NEW record structure::

        NEW,name,'Set to "Entity Name"',Justification text,https://evidence.url
        NEW,operational_status,'Set to "Active"',Justification,https://evidence.url
        NEW,name,'Set to "Another Entity"',Justification,https://evidence.url
        NEW,operational_status,'Set to "Inactive"',Justification,
    """
    df_mod = df.copy()
    src_name, base_dir = qa_path.name, qa_path.parent
    qa_df = pd.read_csv(qa_path, dtype=str).fillna("")

    # First pass: collect all "NEW" record edits
    # Uses entity name as key to support multiple NEW records per file
    new_records: dict[str, dict[str, str]] = {}  # Maps entity name to field dict
    new_record_counter = (
        0  # Counter for NEW records encountered (for temp keys before name is seen)
    )
    current_new_record_key = (
        None  # Current NEW record key (name if seen, otherwise sequence-based temp key)
    )

    # Process all rows to collect NEW record data
    for _, qa_row in qa_df.iterrows():
        raw_feedback = str(_get_qa_column(qa_row, "feedback", "action", ""))
        feedback = _sanitize_wrapped_text(raw_feedback)
        if not raw_feedback.strip() and not feedback:
            continue

        record_id = (
            str(_get_qa_column(qa_row, "Row(s)", "record_id", "")).strip().upper()
        )

        # Collect NEW record fields
        if record_id == "NEW":
            action, match = detect_rule(raw_feedback)
            if action == QAAction.DIRECT_SET and match:
                provided_col = _get_qa_column(qa_row, "Column", "field_name") or (
                    match.group("column") if "column" in match.groupdict() else None
                )
                if provided_col:
                    target_col = _get_column(df_mod.columns, provided_col)
                    if target_col:
                        val_str = match.group("value")
                        clean_val = _sanitize_wrapped_text(val_str)
                        if clean_val is None:
                            clean_val = ""

                        # Determine key for this NEW record
                        # If this is a 'name' field, use it as the key
                        if target_col == "name":
                            key = clean_val
                            # If tracking a temp key, migrate fields to name-based
                            if (
                                current_new_record_key
                                and current_new_record_key.startswith("NEW_RECORD_")
                            ):
                                # Migrate any fields collected under temporary key
                                if current_new_record_key in new_records:
                                    if key not in new_records:
                                        new_records[key] = {}
                                    new_records[key].update(
                                        new_records[current_new_record_key]
                                    )
                                    del new_records[current_new_record_key]
                            # Initialize record if it doesn't exist
                            if key not in new_records:
                                new_records[key] = {}
                            new_records[key][target_col] = clean_val
                            # Update current key to use name going forward
                            current_new_record_key = key
                        else:
                            # Not a name field - determine which NEW record this is
                            if current_new_record_key is None:
                                # Start tracking a new NEW record sequence
                                new_record_counter += 1
                                current_new_record_key = (
                                    f"NEW_RECORD_{new_record_counter}"
                                )

                            # Use current key (name-based or temp sequence-based)
                            key = current_new_record_key

                            if key not in new_records:
                                new_records[key] = {}
                            new_records[key][target_col] = clean_val
        else:
            # Not a NEW record - reset current key tracker
            current_new_record_key = None

    # Create NEW records before processing edits to existing records
    # Note: Temp keys (NEW_RECORD_N) should have migrated to name-based keys.
    # Remaining temp keys indicate missing name field.
    for _key, fields in new_records.items():
        df_mod = _create_new_record(df_mod, fields, src_name, user, prefix)

    # Second pass: process edits to existing records
    for _, qa_row in qa_df.iterrows():
        raw_feedback = str(_get_qa_column(qa_row, "feedback", "action", ""))
        feedback = _sanitize_wrapped_text(raw_feedback)
        if not raw_feedback.strip() and not feedback:
            continue

        record_id = (
            str(_get_qa_column(qa_row, "Row(s)", "record_id", "")).strip().upper()
        )
        # Skip NEW records - already processed
        if record_id == "NEW":
            continue

        justification = _get_qa_column(qa_row, "reason", "justification")
        evidence_url = _get_qa_column(qa_row, "", "evidence_url")
        # Store evidence_url separately; keep reason as just the justification
        reason = justification
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
                evidence_url=evidence_url,
            )
        elif action == QAAction.DIRECT_SET and match:
            handle_direct_set(df_mod, qa_row, match, src_name, user, prefix, feedback)
        elif action == QAAction.POLICY_QUERY:
            handle_policy_query(df_mod, qa_row, src_name, user, prefix, feedback)

    return df_mod
