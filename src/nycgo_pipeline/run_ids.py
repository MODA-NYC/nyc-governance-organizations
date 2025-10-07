"""Utilities for generating stable pipeline run identifiers."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone


def generate_run_id(descriptor: str | None = None) -> str:
    """Return a timestamped run id with optional descriptor and git sha fallback.

    The format follows ``YYYYMMDD-HHMM_<descriptor>`` with the descriptor defaulting
    to the current Git SHA (or ``nogit`` when unavailable). The timestamp is in
    UTC to keep ordering consistent across environments.
    """

    now = datetime.now(timezone.utc)
    prefix = now.strftime("%Y%m%d-%H%M")

    git_descriptor = "nogit"
    try:
        git_descriptor = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], timeout=5)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_descriptor = "nogit"

    suffix = descriptor.strip() if descriptor else git_descriptor
    suffix = suffix.replace(" ", "-")
    return f"{prefix}_{suffix}"


__all__ = ["generate_run_id"]
