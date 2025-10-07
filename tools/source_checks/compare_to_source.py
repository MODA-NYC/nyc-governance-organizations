#!/usr/bin/env python3
"""Wrapper to compare golden dataset against a source extract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from nycgo_pipeline.source_checks import compare_to_source


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the golden dataset against a source extract using the " "crosswalk"
        )
    )
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--source-name", type=str, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    try:
        diff = compare_to_source.compare_against_source(
            args.golden, args.crosswalk, args.source_file, args.source_name
        )
    except Exception as exc:  # pragma: no cover - surface CLI errors
        print(f"❌ Error: {exc}", file=sys.stderr)
        return 1

    rows: list[dict[str, str]] = []
    for name in diff["new_names"]:
        rows.append({"status": "new_in_source", "name": name})
    for name in diff["missing_names"]:
        rows.append({"status": "missing_from_source", "name": name})

    if not rows:
        print("✅ No differences detected.")
        return 0

    df = pd.DataFrame(rows, columns=["status", "name"])
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Saved comparison report with {len(rows)} rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
