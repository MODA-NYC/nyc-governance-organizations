"""Crosswalk utilities for mapping RecordID to source system names."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(slots=True)
class SourceConfig:  # noqa: D401 - simple data container
    """Configuration for a single source system."""

    golden_column: str
    source_column: str


DEFAULT_SOURCE_CONFIG: dict[str, SourceConfig] = {
    "Ops": SourceConfig("Name - Ops", "Agency Name"),
    "CPO": SourceConfig("Name - CPO", "Name - CPO"),
    "Greenbook": SourceConfig("Name - Greenbook", "Name - Greenbook"),
}


def build_crosswalk(
    df: pd.DataFrame,
    *,
    sources: dict[str, SourceConfig] | None = None,
    record_id_column: str | None = None,
) -> pd.DataFrame:
    """Return a long-format crosswalk DataFrame for the provided dataset."""

    sources = sources or DEFAULT_SOURCE_CONFIG
    if record_id_column is None:
        try:
            record_id_column = next(
                col for col in df.columns if col.lower() == "recordid"
            )
        except StopIteration as exc:  # pragma: no cover - defensive
            raise ValueError("RecordID column not found in dataframe") from exc

    frames: list[pd.DataFrame] = []
    for system_name, config in sources.items():
        if config.golden_column not in df.columns:
            continue

        subset = (
            df[[record_id_column, config.golden_column]]
            .copy()
            .rename(columns={config.golden_column: "SourceName"})
        )
        subset.dropna(subset=["SourceName"], inplace=True)
        subset = subset[subset["SourceName"].str.strip() != ""]
        if subset.empty:
            continue

        subset["SourceSystem"] = system_name
        subset["SourceColumn"] = config.source_column
        frames.append(subset)

    if not frames:
        return pd.DataFrame(
            columns=["RecordID", "SourceSystem", "SourceColumn", "SourceName"]
        )

    df_long = pd.concat(frames, ignore_index=True)
    df_long.rename(columns={record_id_column: "RecordID"}, inplace=True)
    return df_long[["RecordID", "SourceSystem", "SourceColumn", "SourceName"]]


def generate_crosswalk(input_path: Path, output_path: Path) -> Path:
    """Read the input CSV and write the crosswalk to ``output_path``."""

    df = pd.read_csv(input_path, dtype=str)
    crosswalk_df = build_crosswalk(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crosswalk_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


__all__ = [
    "SourceConfig",
    "DEFAULT_SOURCE_CONFIG",
    "build_crosswalk",
    "generate_crosswalk",
]
