"""City Record Online (CROL) HTML parsing for supplemental evidence.

This module provides CROL scraping capability for personnel change records.
CROL is the official publication source for NYC personnel changes.

Note: CROL data has approximately the same lag as NYC Open Data (~2 months),
as both are fed from the same source systems.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# CROL configuration
CROL_BASE_URL = "https://a856-cityrecord.nyc.gov"
USER_AGENT = "NYCGO-Appointments-Monitor/1.0 (NYC Governance Organizations Research)"

# Rate limiting
REQUEST_DELAY_SECONDS = 2.0
MAX_REQUESTS_PER_RUN = 50
MAX_RETRIES = 3
RETRY_BACKOFF = 3.0

# Cache settings
DEFAULT_CACHE_DIR = Path(".cache/appointments/crol")
CACHE_TTL_HOURS = 24

# Section IDs
SECTION_CHANGES_IN_PERSONNEL = "8"


@dataclass
class CROLNotice:
    """A notice from City Record Online."""

    publication_date: datetime | None
    effective_date: datetime | None
    agency_name: str
    employee_name: str
    employee_title: str
    action_type: str  # APPOINTED, RESIGNED, RETIRED, INCREASE, TERMINATED, etc.
    url: str
    raw_text: str = ""


def _get_cache_path(query: str, cache_dir: Path) -> Path:
    """Generate cache file path for a search query."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
    return cache_dir / f"search_{query_hash}.json"


def _is_cache_valid(cache_path: Path, ttl_hours: int = CACHE_TTL_HOURS) -> bool:
    """Check if cache file exists and is not expired."""
    if not cache_path.exists():
        return False
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600
    return age_hours < ttl_hours


def _load_from_cache(cache_path: Path) -> list[dict] | None:
    """Load cached notices from file."""
    if not _is_cache_valid(cache_path):
        return None
    try:
        with open(cache_path) as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} notices from cache: {cache_path}")
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_to_cache(notices: list[dict], cache_path: Path) -> None:
    """Save notices to cache file."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(notices, f, indent=2, default=str)
        logger.info(f"Saved {len(notices)} notices to cache: {cache_path}")
    except OSError as e:
        logger.warning(f"Failed to save cache: {e}")


class CROLRateLimiter:
    """Simple rate limiter for CROL requests."""

    def __init__(self, max_requests: int = MAX_REQUESTS_PER_RUN):
        self.max_requests = max_requests
        self.request_count = 0
        self.last_request_time: datetime | None = None

    def can_request(self) -> bool:
        """Check if we can make another request."""
        return self.request_count < self.max_requests

    def wait(self) -> None:
        """Wait appropriate time before next request."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < REQUEST_DELAY_SECONDS:
                time.sleep(REQUEST_DELAY_SECONDS - elapsed)

    def record_request(self) -> None:
        """Record that a request was made."""
        self.request_count += 1
        self.last_request_time = datetime.now()


# Global rate limiter instance
_rate_limiter = CROLRateLimiter()


def search_personnel_changes(
    name: str | None = None,
    agency: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    action_types: set[str] | None = None,
    use_cache: bool = True,
    cache_dir: Path | None = None,
) -> list[CROLNotice]:
    """Search CROL for personnel change notices.

    Args:
        name: Person name to search for (optional)
        agency: Agency name to filter by (optional)
        start_date: Start date for search (MM/DD/YYYY format)
        end_date: End date for search (MM/DD/YYYY format)
        action_types: Filter by action type (e.g., {"RESIGNED", "RETIRED"})
        use_cache: Whether to use cached results
        cache_dir: Directory for cache files

    Returns:
        List of matching CROLNotice objects
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    # Build cache key
    query_parts = [name or "", agency or "", start_date or "", end_date or ""]
    query = "|".join(query_parts)

    # Check cache
    cache_path = _get_cache_path(query, cache_dir)
    if use_cache:
        cached = _load_from_cache(cache_path)
        if cached is not None:
            notices = [_dict_to_notice(d) for d in cached]
            if action_types:
                notices = [n for n in notices if n.action_type.upper() in action_types]
            return notices

    # Check rate limiter
    if not _rate_limiter.can_request():
        logger.warning("CROL rate limit reached, skipping request")
        return []

    # Make request
    _rate_limiter.wait()

    try:
        notices = _fetch_personnel_notices(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )
        _rate_limiter.record_request()

        # Cache results
        if use_cache and notices:
            notice_dicts = [_notice_to_dict(n) for n in notices]
            _save_to_cache(notice_dicts, cache_path)

        # Filter by action type
        if action_types:
            notices = [n for n in notices if n.action_type.upper() in action_types]

        # Filter by agency if specified
        if agency:
            agency_lower = agency.lower()
            notices = [n for n in notices if agency_lower in n.agency_name.lower()]

        return notices

    except Exception as e:
        logger.error(f"CROL search failed: {e}")
        return []


def _fetch_personnel_notices(
    name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int = 10,
) -> list[CROLNotice]:
    """Fetch personnel change notices from CROL.

    Uses the Advanced Search endpoint with Changes in Personnel section.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup not installed, skipping CROL search")
        return []

    headers = {"User-Agent": USER_AGENT}
    session = requests.Session()

    # Initialize session
    session.get(CROL_BASE_URL, headers=headers, timeout=30)

    all_notices = []

    for page in range(max_pages):
        _rate_limiter.wait()

        search_data = {
            "SearchText": name or "",
            "OrderBy": "Newest",
            "SectionId": SECTION_CHANGES_IN_PERSONNEL,
            "AgencyCode": "0",
            "CategoryId": "0",
            "SectionName": "All",
            "SearchWithinTitle": "False",
            "AllKeywords": "True",
            "SearchWithinDocuments": "False",
            "startDate": start_date or "",
            "endDate": end_date or "",
            "PageNumber": str(page),
            "SearchWithinCurrentAds": "false",
            "NoticeTypeId": "0",
        }

        try:
            resp = session.post(
                f"{CROL_BASE_URL}/Search/Advanced",
                data=search_data,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            page_notices = _parse_notice_containers(soup)

            if not page_notices:
                break

            all_notices.extend(page_notices)
            _rate_limiter.record_request()

            # Check if we've got all pages
            content = soup.find("div", {"class": "page-content"})
            if content:
                text = content.get_text()
                match = re.search(
                    r"Displaying\s*(\d+)\s*-\s*(\d+)\s*of\s*([\d,]+)", text
                )
                if match:
                    end_idx = int(match.group(2))
                    total = int(match.group(3).replace(",", ""))
                    if end_idx >= total:
                        break

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch page {page}: {e}")
            break

    logger.info(f"Fetched {len(all_notices)} personnel notices from CROL")
    return all_notices


def _parse_notice_containers(soup: BeautifulSoup) -> list[CROLNotice]:
    """Parse notice containers from CROL search results."""
    notices = []

    content = soup.find("div", {"class": "page-content"})
    if not content:
        return notices

    for div in content.find_all("div", {"class": "notice-container"}):
        try:
            notice = _parse_single_notice(div)
            if notice:
                notices.append(notice)
        except Exception as e:
            logger.debug(f"Failed to parse notice: {e}")
            continue

    return notices


def _parse_single_notice(container) -> CROLNotice | None:
    """Parse a single notice container element."""
    raw_text = container.get_text(strip=True)

    # Skip non-personnel notices
    if "CHANGES IN PERSONNEL" not in raw_text:
        return None

    # Extract employee name from header
    # Pattern: "CHANGES IN PERSONNEL - MM/DD/YYYY FOR FIRSTNAME M. LASTNAME"
    header_match = re.search(
        r"CHANGES IN PERSONNEL - (\d{1,2}/\d{1,2}/\d{4}) FOR ([A-Z\s\.]+?)(?:from|$)",
        raw_text,
    )

    if header_match:
        pub_date_str = header_match.group(1)
        employee_name = header_match.group(2).strip()
    else:
        pub_date_str = ""
        employee_name = ""

    # Extract agency
    agency_match = re.search(
        r"from([A-Z\s&']+?)(?:APPOINTED|RESIGNED|RETIRED|INCREASE|TERMINATED|DECEASED)",
        raw_text,
    )
    agency_name = agency_match.group(1).strip() if agency_match else ""

    # Extract action type
    action_match = re.search(
        r"(APPOINTED|RESIGNED|RETIRED|INCREASE|TERMINATED|DECEASED)", raw_text
    )
    action_type = action_match.group(1) if action_match else ""

    # Extract effective date (appears after action type)
    eff_date_match = re.search(
        rf"{action_type}(\d{{1,2}}/\d{{1,2}}/\d{{4}})",
        raw_text,
    )
    eff_date_str = eff_date_match.group(1) if eff_date_match else ""

    # Extract title
    title_match = re.search(r"Employee Title:\s*([A-Z\s\-\(\)]+)", raw_text)
    employee_title = title_match.group(1).strip() if title_match else ""

    # Extract URL from link
    link = container.find("a", href=True)
    url = f"{CROL_BASE_URL}{link.get('href', '')}" if link else ""

    # Parse dates
    pub_date = _parse_date(pub_date_str)
    eff_date = _parse_date(eff_date_str)

    if not employee_name:
        return None

    return CROLNotice(
        publication_date=pub_date,
        effective_date=eff_date,
        agency_name=agency_name,
        employee_name=employee_name,
        employee_title=employee_title,
        action_type=action_type,
        url=url,
        raw_text=raw_text,
    )


def _parse_date(date_str: str) -> datetime | None:
    """Parse date string from CROL."""
    if not date_str:
        return None

    formats = [
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None


def _notice_to_dict(notice: CROLNotice) -> dict:
    """Convert CROLNotice to dictionary for caching."""
    return {
        "publication_date": (
            notice.publication_date.isoformat() if notice.publication_date else None
        ),
        "effective_date": (
            notice.effective_date.isoformat() if notice.effective_date else None
        ),
        "agency_name": notice.agency_name,
        "employee_name": notice.employee_name,
        "employee_title": notice.employee_title,
        "action_type": notice.action_type,
        "url": notice.url,
        "raw_text": notice.raw_text,
    }


def _dict_to_notice(data: dict) -> CROLNotice:
    """Convert dictionary to CROLNotice."""
    pub_date = None
    if data.get("publication_date"):
        try:
            pub_date = datetime.fromisoformat(data["publication_date"])
        except (ValueError, TypeError):
            pass

    eff_date = None
    if data.get("effective_date"):
        try:
            eff_date = datetime.fromisoformat(data["effective_date"])
        except (ValueError, TypeError):
            pass

    return CROLNotice(
        publication_date=pub_date,
        effective_date=eff_date,
        agency_name=data.get("agency_name", ""),
        employee_name=data.get("employee_name", ""),
        employee_title=data.get("employee_title", ""),
        action_type=data.get("action_type", ""),
        url=data.get("url", ""),
        raw_text=data.get("raw_text", ""),
    )


def search_person(
    name: str,
    use_cache: bool = True,
) -> list[CROLNotice]:
    """Search CROL for all notices mentioning a specific person.

    Args:
        name: Person name to search for
        use_cache: Whether to use cached results

    Returns:
        List of matching CROLNotice objects, sorted by date (newest first)
    """
    notices = search_personnel_changes(
        name=name,
        use_cache=use_cache,
    )

    # Sort by effective date, newest first
    notices.sort(
        key=lambda n: n.effective_date or datetime.min,
        reverse=True,
    )

    return notices


def check_departures(
    start_date: str | None = None,
    end_date: str | None = None,
    use_cache: bool = True,
) -> list[CROLNotice]:
    """Search for departure notices (resignations, retirements, terminations).

    Args:
        start_date: Start date for search (MM/DD/YYYY format)
        end_date: End date for search (MM/DD/YYYY format)
        use_cache: Whether to use cached results

    Returns:
        List of departure notices
    """
    return search_personnel_changes(
        start_date=start_date,
        end_date=end_date,
        action_types={"RESIGNED", "RETIRED", "TERMINATED", "DECEASED"},
        use_cache=use_cache,
    )


def get_latest_data_date() -> datetime | None:
    """Get the most recent effective date in CROL personnel data.

    This helps understand the current data lag.

    Returns:
        Most recent effective date, or None if unable to determine
    """
    notices = search_personnel_changes(
        start_date=None,
        end_date=None,
        use_cache=False,
    )

    if not notices:
        return None

    dates = [n.effective_date for n in notices if n.effective_date]
    if not dates:
        return None

    return max(dates)


def reset_rate_limiter() -> None:
    """Reset the rate limiter for a new run."""
    global _rate_limiter
    _rate_limiter = CROLRateLimiter()
