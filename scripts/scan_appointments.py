#!/usr/bin/env python3
"""Entry point for appointments monitoring.

This script provides two modes:

1. SCAN MODE (default): Scan NYC Open Data for personnel changes and generate
   reports identifying potential principal officer updates for NYCGO.

2. DEPARTURE CHECK MODE (--check-departures): Validate that current principal
   officers in the golden dataset don't have departure records in City Record
   Online (CROL). This catches stale records where someone left months ago.

Usage:
    # Scan for new appointments (last 30 days)
    python scripts/scan_appointments.py --days 30

    # Scan specific date range
    python scripts/scan_appointments.py --start-date 2025-11-01 --end-date 2025-12-01

    # Check if current principal officers have departure records
    python scripts/scan_appointments.py --check-departures

    # Check departures for specific org types
    python scripts/scan_appointments.py --check-departures --org-types "Mayoral Agency"

See --help for full options.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for package imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


if __name__ == "__main__":
    from nycgo_pipeline.appointments.cli import main

    sys.exit(main())
