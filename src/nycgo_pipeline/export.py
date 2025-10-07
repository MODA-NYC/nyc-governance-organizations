"""Export utilities bridging the pipeline to the existing export script."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

export_dataset = import_module("scripts.process.export_dataset")


def export_datasets(
    df,
    *,
    output_golden: Path,
    output_published: Path,
    run_dir: Path,
    run_id: str,
    operator: str,
    previous_export: Path | None,
) -> dict[str, Any]:
    output_golden.parent.mkdir(parents=True, exist_ok=True)
    output_published.parent.mkdir(parents=True, exist_ok=True)

    export_dataset.main_with_dataframe(
        df,
        output_golden=output_golden,
        output_published=output_published,
        run_dir=run_dir,
        run_id=run_id,
        operator=operator,
        previous_export=previous_export,
    )

    return {
        "golden_pre_release": str(output_golden),
        "published_pre_release": str(output_published),
    }
