#!/usr/bin/env python3
"""CLI wrapper around :mod:`nycgo_pipeline.source_checks.compare_to_source`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from nycgo_pipeline.source_checks import compare_to_source


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the golden dataset to a source extract."
    )
    parser.add_argument(
        "--golden", type=Path, required=True, help="Path to golden dataset CSV"
    )
    parser.add_argument(
        "--crosswalk", type=Path, required=True, help="Path to crosswalk CSV"
    )
    parser.add_argument(
        "--source-file", type=Path, required=True, help="Path to source extract CSV"
    )
    parser.add_argument(
        "--source-name", type=str, required=True, help="Source system name in crosswalk"
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        required=True,
        help="Destination for comparison report",
    )
    args = parser.parse_args()

    try:
        result = compare_to_source.compare_against_source(
            args.golden,
            args.crosswalk,
            args.source_file,
            args.source_name,
        )
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"❌ Error: {exc}", file=sys.stderr)
        return 1

    new_names = result["new_names"]
    missing_names = result["missing_names"]

    rows: list[dict[str, str]] = []
    for name in new_names:
        rows.append(
            {
                "Source": args.source_name,
                "RecordID": "",
                "Status": "new_in_source",
                "Name": name,
            }
        )
    for name in missing_names:
        rows.append(
            {
                "Source": args.source_name,
                "RecordID": "",
                "Status": "missing_from_source",
                "Name": name,
            }
        )

    if not rows:
        print("✅ No differences detected.")
        return 0

    df = pd.DataFrame(rows, columns=["Source", "RecordID", "Status", "Name"])
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Saved comparison report with {len(rows)} rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
