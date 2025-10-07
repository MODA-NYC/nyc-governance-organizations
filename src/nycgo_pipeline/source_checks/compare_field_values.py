"""Field-level comparison between golden dataset and a source extract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(slots=True)
class SourceConfig:
    source_name_column: str
    field_mappings: Mapping[str, str]


def compare_fields(
    golden_df: pd.DataFrame,
    crosswalk_df: pd.DataFrame,
    source_df: pd.DataFrame,
    *,
    config: SourceConfig,
) -> pd.DataFrame:
    filtered = crosswalk_df.copy()
    merged = pd.merge(golden_df, filtered, on="RecordID", how="inner")
    merged = pd.merge(
        merged,
        source_df,
        left_on="SourceName",
        right_on=config.source_name_column,
        how="inner",
        suffixes=("_golden", "_source"),
    )

    discrepancies: list[dict[str, str]] = []
    for golden_field, source_field in config.field_mappings.items():
        if golden_field not in merged.columns or source_field not in merged.columns:
            continue
        for _, row in merged.iterrows():
            g_val = str(row[golden_field]).strip()
            s_val = str(row[source_field]).strip()
            if g_val != s_val:
                discrepancies.append(
                    {
                        "RecordID": row["RecordID"],
                        "Column": golden_field,
                        "GoldenValue": g_val,
                        "SourceValue": s_val,
                    }
                )

    return pd.DataFrame(discrepancies)


def run_comparison(
    golden_path: Path,
    crosswalk_path: Path,
    source_path: Path,
    config: SourceConfig,
) -> pd.DataFrame:
    golden_df = pd.read_csv(golden_path, dtype=str).fillna("")
    crosswalk_df = pd.read_csv(crosswalk_path, dtype=str).fillna("")
    source_df = pd.read_csv(source_path, dtype=str).fillna("")

    return compare_fields(
        golden_df,
        crosswalk_df,
        source_df,
        config=config,
    )


__all__ = ["SourceConfig", "compare_fields", "run_comparison"]
