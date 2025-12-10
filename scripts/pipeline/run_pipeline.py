#!/usr/bin/env python3
"""CLI to run the NYC Governance Organizations pipeline end-to-end."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from nycgo_pipeline.pipeline import orchestrate_pipeline
from nycgo_pipeline.run_ids import generate_run_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the NYC Governance Organizations pipeline."
    )
    parser.add_argument(
        "--golden", type=Path, required=True, help="Path to the golden dataset CSV"
    )
    parser.add_argument(
        "--qa",
        type=Path,
        action="append",
        required=True,
        help="QA CSV(s) to apply (can be specified multiple times)",
    )
    parser.add_argument(
        "--output-golden",
        type=Path,
        help=(
            "Destination for golden pre-release CSV "
            "(defaults to run_dir/outputs/golden_pre-release.csv)"
        ),
    )
    parser.add_argument(
        "--output-published",
        type=Path,
        help=(
            "Destination for published pre-release CSV "
            "(defaults to run_dir/outputs/published_pre-release.csv)"
        ),
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Optional explicit run directory (defaults to data/audit/runs/<run_id>)",
    )
    parser.add_argument(
        "--changed-by",
        type=str,
        default=os.environ.get("USER", "unknown"),
        help="User or system applying the changes (defaults to $USER env var)",
    )
    parser.add_argument(
        "--operator", type=str, default="", help="Operator for changelog attribution"
    )
    parser.add_argument(
        "--previous-export",
        type=Path,
        help=(
            "Optional path to previous published dataset for "
            "directory changelog comparisons"
        ),
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help=(
            "Explicit run identifier. If omitted, the CLI generates one using "
            "the current time and Git SHA (falling back to 'nogit')."
        ),
    )
    parser.add_argument(
        "--descriptor",
        type=str,
        help=(
            "Optional descriptor appended to the generated run id (ignored when "
            "--run-id provided)"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or generate_run_id(args.descriptor)
    operator = args.operator or args.changed_by

    run_dir = (args.run_dir or Path("data/audit/runs") / run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "review").mkdir(parents=True, exist_ok=True)

    golden_output = args.output_golden or run_dir / "outputs" / "golden_pre-release.csv"
    published_output = (
        args.output_published or run_dir / "outputs" / "published_pre-release.csv"
    )

    summary = orchestrate_pipeline(
        golden_source=args.golden,
        qa_paths=args.qa,
        run_id=run_id,
        changed_by=args.changed_by,
        operator=operator,
        run_dir=run_dir,
        previous_export=args.previous_export,
        output_golden=golden_output,
        output_published=published_output,
    )

    print("Run complete.")
    print(f"Run ID: {run_id}")
    print(f"Run summary written to {summary['outputs']['run_summary_json']}")
    print("Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
