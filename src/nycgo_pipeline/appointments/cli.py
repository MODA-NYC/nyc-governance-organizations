"""CLI logic for appointments monitoring."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Optional argument list (for testing)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Scan for principal officer changes in NYC government orgs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan last 30 days for new appointments
  python scripts/scan_appointments.py

  # Scan last 60 days
  python scripts/scan_appointments.py --days 60

  # Scan specific date range
  python scripts/scan_appointments.py --start-date 2025-11-01 --end-date 2025-12-01

  # Include CROL supplemental data
  python scripts/scan_appointments.py --include-crol

  # Filter by minimum score
  python scripts/scan_appointments.py --min-score 50

  # Check if current principal officers have departure records in CROL
  python scripts/scan_appointments.py --check-departures

  # Check departures for specific org types only
  python scripts/scan_appointments.py --check-departures \\
      --org-types "Mayoral Agency,Public Authority"
        """,
    )

    # Mode selection
    mode_group = parser.add_argument_group("Mode")
    mode_group.add_argument(
        "--check-departures",
        action="store_true",
        help="Check if current principal officers have departure records in CROL",
    )
    mode_group.add_argument(
        "--org-types",
        type=str,
        help="Comma-separated org types to check (for --check-departures)",
    )

    # Date range options
    date_group = parser.add_argument_group("Date Range")
    date_group.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    date_group.add_argument(
        "--start-date",
        type=str,
        help="Explicit start date (YYYY-MM-DD)",
    )
    date_group.add_argument(
        "--end-date",
        type=str,
        help="Explicit end date (YYYY-MM-DD, default: today)",
    )

    # Data source options
    source_group = parser.add_argument_group("Data Sources")
    source_group.add_argument(
        "--include-crol",
        action="store_true",
        help="Include CROL HTML scraping for supplemental evidence",
    )
    source_group.add_argument(
        "--golden-path",
        type=Path,
        help="Path to golden dataset (default: data/published/latest/...latest.csv)",
    )
    source_group.add_argument(
        "--app-token",
        type=str,
        help="Socrata app token for higher API limits",
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: data/reports/appointments_YYYYMMDD/)",
    )
    output_group.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum score to include in output (default: 0)",
    )

    # Cache options
    cache_group = parser.add_argument_group("Caching")
    cache_group.add_argument(
        "--use-cache",
        action="store_true",
        default=True,
        help="Use cached API responses (default: enabled)",
    )
    cache_group.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching, fetch fresh data",
    )
    cache_group.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".cache/appointments"),
        help="Cache directory (default: .cache/appointments/)",
    )

    # Logging
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args(args)


def run_scan(args: argparse.Namespace) -> int:
    """Run the appointments scan.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from nycgo_pipeline.appointments.fetch_open_data import fetch_personnel_records
    from nycgo_pipeline.appointments.match import (
        load_golden_dataset,
        match_organizations,
    )
    from nycgo_pipeline.appointments.report import generate_reports
    from nycgo_pipeline.appointments.score import filter_candidates, score_candidates

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Calculate date range
        end_date = datetime.now()
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        else:
            start_date = end_date - timedelta(days=args.days)

        logger.info(f"Scanning from {start_date.date()} to {end_date.date()}")

        # Determine output directory
        if args.output:
            output_dir = args.output
        else:
            output_dir = (
                Path("data/reports")
                / f"appointments_{datetime.now().strftime('%Y%m%d')}"
            )

        # Determine cache usage
        use_cache = args.use_cache and not args.no_cache

        # Load golden dataset
        golden_df = load_golden_dataset(
            str(args.golden_path) if args.golden_path else None
        )

        # Get golden dataset version from filename or metadata
        golden_version = "unknown"
        if args.golden_path:
            golden_version = args.golden_path.stem
        else:
            golden_version = "latest"

        # Fetch personnel records from Open Data
        logger.info("Fetching personnel records from NYC Open Data...")
        records = fetch_personnel_records(
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache,
            cache_dir=args.cache_dir / "open_data" if args.cache_dir else None,
            app_token=args.app_token,
        )
        logger.info(f"Fetched {len(records)} personnel records")

        if not records:
            logger.warning("No personnel records found in date range")
            # Still generate empty reports
            records = []

        # Match to NYCGO organizations
        logger.info("Matching records to NYCGO organizations...")
        candidates = match_organizations(records, golden_df)
        logger.info(f"Generated {len(candidates)} candidates")

        # Optionally supplement with CROL
        if args.include_crol:
            logger.info("Supplementing with CROL data...")
            _supplement_with_crol(candidates, use_cache, args.cache_dir)

        # Score candidates
        logger.info("Scoring candidates...")
        candidates = score_candidates(candidates)

        # Filter by minimum score
        if args.min_score > 0:
            candidates = filter_candidates(candidates, min_score=args.min_score)

        # Generate reports
        scan_metadata = {
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "golden_version": golden_version,
            "records_scanned": len(records),
            "sources_queried": ["open_data"] + (["crol"] if args.include_crol else []),
        }

        outputs = generate_reports(candidates, output_dir, scan_metadata)

        # Print summary
        print(f"\n{'='*60}")
        print("APPOINTMENTS MONITOR SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Records scanned: {len(records)}")
        print(f"Candidates found: {len(candidates)}")
        high = sum(1 for c in candidates if c.score >= 80)
        med = sum(1 for c in candidates if 50 <= c.score < 80)
        low = sum(1 for c in candidates if c.score < 50)
        print(f"  - High confidence (80+): {high}")
        print(f"  - Medium confidence (50-79): {med}")
        print(f"  - Low confidence (<50): {low}")
        print("\nReports generated:")
        for fmt, path in outputs.items():
            print(f"  - {fmt}: {path}")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        logger.exception(f"Scan failed: {e}")
        return 1


def _supplement_with_crol(
    candidates: list,
    use_cache: bool,
    cache_dir: Path | None,
) -> None:
    """Supplement candidates with CROL evidence."""
    from nycgo_pipeline.appointments.fetch_crol import (
        reset_rate_limiter,
        supplement_candidate_with_crol,
    )

    reset_rate_limiter()

    # Only supplement high/medium confidence candidates to limit requests
    for candidate in candidates:
        if candidate.score >= 50:
            evidence = supplement_candidate_with_crol(
                candidate_name=candidate.candidate_name_normalized,
                agency_name=candidate.agency_name_raw,
                use_cache=use_cache,
            )
            if evidence:
                candidate.sources.extend(evidence)
                logger.debug(
                    f"Added {len(evidence)} CROL sources for {candidate.candidate_id}"
                )


def run_check_departures(args: argparse.Namespace) -> int:
    """Run the departure check against CROL.

    Validates that current principal officers in the golden dataset
    don't have departure records in City Record Online.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from nycgo_pipeline.appointments.check_departures import (
        check_all_departures,
        generate_departure_report,
    )

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Determine golden dataset path
        if args.golden_path:
            golden_path = args.golden_path
        else:
            golden_path = Path("data/published/latest/NYCGO_golden_dataset_latest.csv")

        if not golden_path.exists():
            logger.error(f"Golden dataset not found: {golden_path}")
            return 1

        # Parse org types if specified
        org_types = None
        if args.org_types:
            org_types = {t.strip() for t in args.org_types.split(",")}
            logger.info(f"Filtering to org types: {org_types}")

        # Determine output directory
        if args.output:
            output_dir = args.output
        else:
            output_dir = (
                Path("data/reports")
                / f"departure_check_{datetime.now().strftime('%Y%m%d')}"
            )

        # Determine cache usage
        use_cache = args.use_cache and not args.no_cache

        logger.info(f"Loading golden dataset from: {golden_path}")
        logger.info("Checking principal officers against CROL departure records...")
        logger.info("(This may take several minutes due to rate limiting)")

        # Run the check
        results = check_all_departures(
            golden_path=golden_path,
            use_cache=use_cache,
            org_types=org_types,
        )

        # Count results
        departures = [r for r in results if r.has_departure]
        checked = [r for r in results if r.checked]
        errors = [r for r in results if r.error]

        # Generate reports
        outputs = generate_departure_report(results, output_dir)

        # Print summary
        print(f"\n{'='*60}")
        print("DEPARTURE CHECK COMPLETE")
        print(f"{'='*60}")
        print(f"Principal officers checked: {len(checked)}")
        print(f"Potential stale records found: {len(departures)}")
        print(f"Errors: {len(errors)}")

        if departures:
            print(f"\n{'='*60}")
            print("POTENTIAL STALE RECORDS:")
            print(f"{'='*60}")
            for result in departures:
                best = result.best_match
                date_str = (
                    best.crol_effective_date.strftime("%Y-%m-%d")
                    if best.crol_effective_date
                    else "unknown"
                )
                print(f"\n  {result.org_name}")
                print(f"    Current PO: {result.principal_officer}")
                print(f"    CROL shows: {best.crol_action} on {date_str}")
                print(f"    Confidence: {best.overall_confidence:.0%}")

        print(f"\n{'='*60}")
        print("Reports generated:")
        for fmt, path in outputs.items():
            print(f"  - {fmt}: {path}")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        logger.exception(f"Departure check failed: {e}")
        return 1


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Optional argument list (for testing)

    Returns:
        Exit code
    """
    parsed_args = parse_args(args)

    if parsed_args.check_departures:
        return run_check_departures(parsed_args)
    else:
        return run_scan(parsed_args)
