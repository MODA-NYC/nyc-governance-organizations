#!/usr/bin/env python3
"""Analyst wrapper to compare selected fields against a source extract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nycgo_pipeline.source_checks.compare_field_values import (
    SourceConfig,
    run_comparison,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare configured fields against a source extract"
    )
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--source-name-column", type=str, default="Agency Name")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument(
        "--field",
        action="append",
        nargs=2,
        metavar=("GOLDEN_FIELD", "SOURCE_FIELD"),
        help="Field mapping to compare (repeatable)",
    )
    args = parser.parse_args()

    if not args.field:
        print("❌ At least one --field mapping is required", file=sys.stderr)
        return 1

    field_map = {golden: source for golden, source in args.field}

    try:
        df = run_comparison(
            args.golden,
            args.crosswalk,
            args.source_file,
            SourceConfig(
                source_name_column=args.source_name_column,
                field_mappings=field_map,
            ),
        )
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"❌ Error: {exc}", file=sys.stderr)
        return 1

    if df.empty:
        print("✅ No discrepancies found.")
        return 0

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Saved discrepancy report with {len(df)} rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
