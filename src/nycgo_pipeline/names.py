"""Name parsing utilities for principal officer fields."""

from __future__ import annotations

import pandas as pd
from nameparser import HumanName


def populate_officer_name_parts(df_input: pd.DataFrame) -> pd.DataFrame:
    """Populate detailed officer name parts from ``PrincipalOfficerName`` values."""

    df_processed = df_input.copy()
    required_columns = [
        "PrincipalOfficerFullName",
        "PrincipalOfficerGivenName",
        "PrincipalOfficerMiddleNameOrInitial",
        "PrincipalOfficerFamilyName",
        "PrincipalOfficerSuffix",
    ]

    for col in required_columns:
        if col not in df_processed.columns:
            df_processed[col] = ""

    name_series = df_processed.get("PrincipalOfficerName")
    if name_series is None:
        return df_processed

    for idx, name_str in name_series.items():
        if not isinstance(name_str, str) or not name_str.strip():
            continue

        parsed = HumanName(name_str)
        updates = {
            "PrincipalOfficerFullName": name_str,
            "PrincipalOfficerGivenName": parsed.first,
            "PrincipalOfficerMiddleNameOrInitial": parsed.middle,
            "PrincipalOfficerFamilyName": parsed.last,
            "PrincipalOfficerSuffix": parsed.suffix,
        }

        for column_name, new_value in updates.items():
            if new_value:
                df_processed.at[idx, column_name] = new_value

    return df_processed


__all__ = ["populate_officer_name_parts"]
