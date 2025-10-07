"""Helpers to create review artifacts for a pipeline run."""

from __future__ import annotations

import json
from pathlib import Path


def build_review_artifacts(
    review_dir: Path,
    golden_output: Path,
    published_output: Path,
    previous_export: Path | None,
) -> dict[str, str]:
    """Assemble basic review metadata files.

    Placeholder implementation that records the presence of key artifacts while
    downstream comparison tooling is integrated.
    """

    review_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "golden_pre_release": str(golden_output),
        "published_pre_release": str(published_output),
        "previous_published": str(previous_export) if previous_export else None,
    }

    manifest_path = review_dir / "review_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"review_manifest": str(manifest_path)}


__all__ = ["build_review_artifacts"]
