"""Helpers for per-run directory changelog generation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CHANGELOG_COLUMNS = [
    "timestamp_utc",
    "run_id",
    "record_id",
    "record_name",
    "field",
    "old_value",
    "new_value",
    "reason",
    "evidence_url",
    "source_ref",
    "operator",
    "notes",
]


@dataclass(slots=True)
class DirectoryChange:
    """A single change entry used to build the per-run changelog."""

    record_id: str
    record_name: str
    field: str
    old_value: str
    new_value: str
    reason: str
    source_ref: str
    notes: str


def write_run_changelog(
    run_dir: Path,
    changes: Iterable[DirectoryChange],
    *,
    run_id: str,
    operator: str,
) -> Path:
    """Persist the supplied directory changes to ``outputs/run_changelog.csv``."""

    timestamp = datetime.now(timezone.utc).isoformat()
    rows = []
    for entry in changes:
        rows.append(
            {
                "timestamp_utc": timestamp,
                "run_id": run_id,
                "record_id": entry.record_id,
                "record_name": entry.record_name,
                "field": entry.field,
                "old_value": entry.old_value,
                "new_value": entry.new_value,
                "reason": entry.reason,
                "evidence_url": "",
                "source_ref": entry.source_ref,
                "operator": operator,
                "notes": entry.notes,
            }
        )

    changelog_df = pd.DataFrame(rows, columns=CHANGELOG_COLUMNS)

    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    changelog_path = outputs_dir / "run_changelog.csv"
    changelog_df.to_csv(changelog_path, index=False, encoding="utf-8-sig")
    return changelog_path


__all__ = ["DirectoryChange", "write_run_changelog", "CHANGELOG_COLUMNS"]
