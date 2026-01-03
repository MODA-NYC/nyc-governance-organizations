"""Appointments monitoring package for NYCGO pipeline.

This package provides tools to scan public data sources for potential
principal officer changes and generate reviewable candidate reports.
"""

from __future__ import annotations

from nycgo_pipeline.appointments.cli import run_scan
from nycgo_pipeline.appointments.match import match_organizations
from nycgo_pipeline.appointments.normalize import normalize_name, parse_description
from nycgo_pipeline.appointments.report import generate_reports
from nycgo_pipeline.appointments.score import calculate_score

__all__ = [
    "run_scan",
    "match_organizations",
    "normalize_name",
    "parse_description",
    "generate_reports",
    "calculate_score",
]
