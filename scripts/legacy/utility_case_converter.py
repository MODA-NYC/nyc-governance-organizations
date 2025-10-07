"""Utilities for converting case formats used in edits and exports."""

from __future__ import annotations

import pandas as pd


def to_pascal_case(snake_case_str: str) -> str:
    """Convert a snake_case string to PascalCase."""
    if not isinstance(snake_case_str, str):
        return ""
    return "".join(word.capitalize() for word in snake_case_str.split("_"))


def snake_case_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with column names converted to snake_case."""
    df_copy = df.copy()

    def to_snake_case(name: str) -> str:
        s1 = name.replace(" ", "_")
        snake = ""
        for idx, char in enumerate(s1):
            if char.isupper() and idx and s1[idx - 1] not in {"_", "-"}:
                snake += "_"
            snake += char.lower()
        return snake

    df_copy.columns = [to_snake_case(col) for col in df_copy.columns]
    return df_copy
