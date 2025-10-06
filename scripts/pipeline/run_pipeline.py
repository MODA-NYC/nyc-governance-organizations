#!/usr/bin/env python3
"""CLI to run the NYC Governance Organizations pipeline end-to-end."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nycgo_pipeline.pipeline import orchestrate_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NYC Governance Organizations pipeline.")
    parser.add_argument("--golden", type=Path, required=True, help="Path to the golden dataset CSV")
    parser.add_argument(
        "--qa",
        type=Path,
        action="append",
        required=True,
        help="QA CSV(s) to apply (can be specified multiple times)",
    )
    parser.add_argument("--output-golden", type=Path, required=True, help="Destination for golden pre-release CSV")
    parser.add_argument(
        "--output-published",
        type=Path,
        required=True,
        help="Destination for published pre-release CSV",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Run directory under data/audit/runs/<run_id>",
    )
    parser.add_argument("--changed-by", type=str, required=True, help="User or system applying the changes")
    parser.add_argument("--operator", type=str, default="", help="Operator for changelog attribution")
    parser.add_argument(
        "--previous-export",
        type=Path,
        help="Optional path to previous published dataset for directory changelog comparisons",
    )
    parser.add_argument("--run-id", type=str, required=True, help="Explicit run identifier")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    operator = args.operator or args.changed_by

    summary = orchestrate_pipeline(
        golden_source=args.golden,
        qa_paths=args.qa,
        run_id=args.run_id,
        changed_by=args.changed_by,
        operator=operator,
        run_dir=args.run_dir,
        previous_export=args.previous_export,
        output_golden=args.output_golden,
        output_published=args.output_published,
    )

    print("Run complete.")
    print(f"Run ID: {args.run_id}")
    print(f"Run summary written to {args.run_dir / 'outputs' / 'run_summary.json'}")
    print("Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
