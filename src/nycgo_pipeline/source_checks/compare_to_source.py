"""Compare the golden dataset against a source system extract using the crosswalk."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import ftfy
import pandas as pd


def normalize_name(name: str | None) -> str:
    if not isinstance(name, str):
        return ""
    name = ftfy.fix_text(name)
    name = unicodedata.normalize("NFKC", name)
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def load_inputs(
    golden_path: Path,
    crosswalk_path: Path,
    source_file_path: Path,
    source_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    df_golden = pd.read_csv(golden_path, dtype=str)
    df_crosswalk = pd.read_csv(crosswalk_path, dtype=str)
    df_source = pd.read_csv(source_file_path, dtype=str)

    filtered_crosswalk = df_crosswalk[df_crosswalk["SourceSystem"] == source_name]
    if filtered_crosswalk.empty:
        raise ValueError(f"No crosswalk entries found for source '{source_name}'")

    source_cols = filtered_crosswalk["SourceColumn"].unique()
    if len(source_cols) != 1:
        raise ValueError(
            "Expected a single SourceColumn for "
            f"'{source_name}', found {list(source_cols)}"
        )
    source_column = source_cols[0]

    if source_column not in df_source.columns:
        raise ValueError(
            f"Column '{source_column}' not present in source file '{source_file_path}'"
        )

    return df_golden, filtered_crosswalk, df_source, source_column


def compare_against_source(
    golden_path: Path,
    crosswalk_path: Path,
    source_file_path: Path,
    source_name: str,
) -> dict[str, list[str]]:
    _, crosswalk_df, source_df, source_column = load_inputs(
        golden_path, crosswalk_path, source_file_path, source_name
    )

    crosswalk_df["normalized_name"] = crosswalk_df["SourceName"].apply(normalize_name)
    source_df["normalized_name"] = source_df[source_column].apply(normalize_name)

    known = set(crosswalk_df["normalized_name"]) - {""}
    current = set(source_df["normalized_name"]) - {""}

    new_normalized = current - known
    missing_normalized = known - current

    new_names = sorted(
        source_df[source_df["normalized_name"].isin(new_normalized)][
            source_column
        ].unique()
    )
    missing_names = sorted(
        crosswalk_df[crosswalk_df["normalized_name"].isin(missing_normalized)][
            "SourceName"
        ].unique()
    )

    return {
        "new_names": list(new_names),
        "missing_names": list(missing_names),
    }


__all__ = ["compare_against_source", "normalize_name", "load_inputs"]
