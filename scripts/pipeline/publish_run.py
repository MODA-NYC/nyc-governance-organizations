#!/usr/bin/env python3
"""CLI to publish a completed run: promote artifacts, archive previous versions, and finalize changelog."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from nycgo_pipeline.publish import publish_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a pipeline run.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory under data/audit/runs/<run_id>")
    parser.add_argument("--version", type=str, required=True, help="Semantic version to publish (e.g., v1.0.0)")
    parser.add_argument(
        "--append-changelog",
        action="store_true",
        help="Append run changelog to data/changelog.csv after validation",
    )
    parser.add_argument(
        "--operator",
        type=str,
        default="",
        help="Operator name for changelog attribution (defaults to $USER)",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip creating dist/nycgo-run-<run_id>.zip",
    )
    return parser.parse_args()


def ensure_required_files(run_dir: Path) -> dict[str, Path]:
    outputs_dir = run_dir / "outputs"
    required = {
        "golden": outputs_dir / "golden_pre-release.csv",
        "published": outputs_dir / "published_pre-release.csv",
        "summary": outputs_dir / "run_summary.json",
        "changelog": outputs_dir / "run_changelog.csv",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing run artifacts: {', '.join(missing)}")
    return required


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    run_id = run_dir.name
    try:
        artifacts = ensure_required_files(run_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    operator = args.operator or "publish"

    publish_run(
        run_dir=run_dir,
        version=args.version,
        operator=operator,
        append_changelog=args.append_changelog,
        archive=not args.no_archive,
        artifacts=artifacts,
    )

    print("Publish complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
