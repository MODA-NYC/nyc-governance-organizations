"""Socrata API client for NYC Open Data Changes in Personnel dataset."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import requests

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

# Dataset configuration
DATASET_ID = "wq4v-8hyb"
BASE_URL = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
USER_AGENT = "NYCGO-Appointments-Monitor/1.0 (NYC Governance Organizations Research)"

# Rate limiting
REQUEST_DELAY_SECONDS = 1.0
BATCH_SIZE = 1000
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

# Cache settings
DEFAULT_CACHE_DIR = Path(".cache/appointments/open_data")
CACHE_TTL_HOURS = 24


@dataclass
class PersonnelRecord:
    """A single personnel change record from NYC Open Data."""

    end_date: datetime | None
    agency_name: str
    description: str
    raw_record: dict

    # Parsed fields from description
    effective_date: datetime | None = None
    provisional_status: str | None = None
    title_code: str | None = None
    reason_for_change: str | None = None
    salary: float | None = None
    employee_name: str | None = None


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse ISO datetime string to datetime object."""
    if not date_str:
        return None
    try:
        # Handle Socrata datetime format: "2025-10-18T00:00:00.000"
        return datetime.fromisoformat(date_str.replace("Z", "+00:00").split(".")[0])
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse date: {date_str}")
        return None


def _get_cache_path(start_date: datetime, end_date: datetime, cache_dir: Path) -> Path:
    """Generate cache file path for a query."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    return cache_dir / f"{DATASET_ID}_{start_str}_{end_str}.json"


def _is_cache_valid(cache_path: Path, ttl_hours: int = CACHE_TTL_HOURS) -> bool:
    """Check if cache file exists and is not expired."""
    if not cache_path.exists():
        return False
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600
    return age_hours < ttl_hours


def _load_from_cache(cache_path: Path) -> list[dict] | None:
    """Load cached records from file."""
    if not _is_cache_valid(cache_path):
        return None
    try:
        with open(cache_path) as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} records from cache: {cache_path}")
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_to_cache(records: list[dict], cache_path: Path) -> None:
    """Save records to cache file."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(records, f, indent=2, default=str)
        logger.info(f"Saved {len(records)} records to cache: {cache_path}")
    except OSError as e:
        logger.warning(f"Failed to save cache: {e}")


def fetch_personnel_records(
    start_date: datetime,
    end_date: datetime,
    use_cache: bool = True,
    cache_dir: Path | None = None,
    app_token: str | None = None,
) -> list[PersonnelRecord]:
    """Fetch personnel change records from NYC Open Data.

    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        use_cache: Whether to use cached results
        cache_dir: Directory for cache files
        app_token: Optional Socrata app token for higher rate limits

    Returns:
        List of PersonnelRecord objects
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    # Check cache first
    cache_path = _get_cache_path(start_date, end_date, cache_dir)
    if use_cache:
        cached = _load_from_cache(cache_path)
        if cached is not None:
            return [_parse_record(r) for r in cached]

    # Fetch from API
    logger.info(f"Fetching records from {start_date.date()} to {end_date.date()}")
    raw_records = list(_fetch_paginated(start_date, end_date, app_token))

    # Cache results
    if use_cache and raw_records:
        _save_to_cache(raw_records, cache_path)

    return [_parse_record(r) for r in raw_records]


def _fetch_paginated(
    start_date: datetime,
    end_date: datetime,
    app_token: str | None = None,
) -> Iterator[dict]:
    """Fetch records with pagination."""
    headers = {"User-Agent": USER_AGENT}
    if app_token:
        headers["X-App-Token"] = app_token

    offset = 0
    total_fetched = 0

    while True:
        # Build query
        # Filter by end_date (publication date) within range
        start_str = start_date.strftime("%Y-%m-%dT00:00:00")
        end_str = end_date.strftime("%Y-%m-%dT23:59:59")

        params = {
            "$where": f"end_date >= '{start_str}' AND end_date <= '{end_str}'",
            "$limit": BATCH_SIZE,
            "$offset": offset,
            "$order": "end_date DESC",
        }

        url = f"{BASE_URL}?{urlencode(params)}"
        logger.debug(f"Fetching: {url}")

        # Fetch with retry
        records = _fetch_with_retry(url, headers)

        if not records:
            break

        yield from records
        total_fetched += len(records)
        logger.info(f"Fetched {total_fetched} records so far...")

        if len(records) < BATCH_SIZE:
            break

        offset += BATCH_SIZE
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"Completed fetching {total_fetched} total records")


def _fetch_with_retry(url: str, headers: dict) -> list[dict]:
    """Fetch URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 429:
                # Rate limited
                wait_time = RETRY_BACKOFF ** (attempt + 1)
                logger.warning(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF ** (attempt + 1)
                logger.warning(f"Request failed: {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Request failed after {MAX_RETRIES} attempts: {e}")
                raise

    return []


def _parse_record(raw: dict) -> PersonnelRecord:
    """Parse raw API record into PersonnelRecord."""
    record = PersonnelRecord(
        end_date=_parse_date(raw.get("end_date")),
        agency_name=raw.get("agency_name", "").strip(),
        description=raw.get("additional_description_1", "").strip(),
        raw_record=raw,
    )

    # Parse description field
    _parse_description_into_record(record)

    return record


def _parse_description_into_record(record: PersonnelRecord) -> None:  # noqa: C901
    """Parse the description field and populate record fields."""
    if not record.description:
        return

    # Format: "Key: Value; Key: Value; ..."
    parts = record.description.split(";")

    for part in parts:
        part = part.strip()
        if ":" not in part:
            continue

        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "effective date":
            try:
                record.effective_date = datetime.strptime(value, "%m/%d/%Y")
            except ValueError:
                pass
        elif key == "provisional status":
            record.provisional_status = value
        elif key == "title code":
            record.title_code = value
        elif key == "reason for change":
            record.reason_for_change = value
        elif key == "salary":
            try:
                record.salary = float(value.replace(",", ""))
            except ValueError:
                pass
        elif key == "employee name":
            record.employee_name = value


def get_appointment_records(
    start_date: datetime,
    end_date: datetime,
    **kwargs,
) -> list[PersonnelRecord]:
    """Fetch only appointment-related records (not separations).

    Filters for records with reason_for_change indicating new appointment:
    - APPOINTED
    - PROMOTED
    - REASSIGNED

    Args:
        start_date: Start of date range
        end_date: End of date range
        **kwargs: Additional arguments passed to fetch_personnel_records

    Returns:
        Filtered list of appointment records
    """
    all_records = fetch_personnel_records(start_date, end_date, **kwargs)

    appointment_reasons = {"APPOINTED", "PROMOTED", "REASSIGNED"}

    return [
        r
        for r in all_records
        if r.reason_for_change and r.reason_for_change.upper() in appointment_reasons
    ]


def get_separation_records(
    start_date: datetime,
    end_date: datetime,
    **kwargs,
) -> list[PersonnelRecord]:
    """Fetch only separation records (may indicate vacancy).

    Filters for records with reason_for_change indicating departure:
    - RETIRED
    - RESIGNED
    - TERMINATED
    - DECEASED

    Args:
        start_date: Start of date range
        end_date: End of date range
        **kwargs: Additional arguments passed to fetch_personnel_records

    Returns:
        Filtered list of separation records
    """
    all_records = fetch_personnel_records(start_date, end_date, **kwargs)

    separation_reasons = {"RETIRED", "RESIGNED", "TERMINATED", "DECEASED"}

    return [
        r
        for r in all_records
        if r.reason_for_change and r.reason_for_change.upper() in separation_reasons
    ]
