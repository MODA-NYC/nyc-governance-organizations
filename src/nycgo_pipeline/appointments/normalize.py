"""Name and title normalization utilities for appointments monitoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from nameparser import HumanName

if TYPE_CHECKING:
    pass


@dataclass
class NormalizedName:
    """A normalized person name with variants for matching."""

    raw: str
    first: str
    middle: str
    last: str
    suffix: str
    full: str

    # Variants for matching
    variants: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Generate name variants for fuzzy matching."""
        self.variants = self._generate_variants()

    def _generate_variants(self) -> list[str]:
        """Generate name variants for matching."""
        variants = []

        # Full name
        if self.full:
            variants.append(self.full.lower())

        # First Last (no middle)
        if self.first and self.last:
            variants.append(f"{self.first} {self.last}".lower())

        # First M. Last (middle initial)
        if self.first and self.middle and self.last:
            initial = self.middle[0] if self.middle else ""
            variants.append(f"{self.first} {initial}. {self.last}".lower())

        # Last, First (reversed)
        if self.first and self.last:
            variants.append(f"{self.last}, {self.first}".lower())

        # F. Last (first initial)
        if self.first and self.last:
            variants.append(f"{self.first[0]}. {self.last}".lower())

        return list(set(variants))


@dataclass
class ParsedDescription:
    """Parsed personnel change description fields."""

    effective_date: datetime | None = None
    provisional_status: str | None = None
    title_code: str | None = None
    reason_for_change: str | None = None
    salary: float | None = None
    employee_name: str | None = None
    raw: str = ""


# Title relevance mapping
TITLE_KEYWORDS_HIGH = {
    "commissioner",
    "director",
    "executive director",
    "chair",
    "chairperson",
    "chairman",
    "president",
    "ceo",
    "chief executive",
    "administrator",
    "counsel",
    "corporation counsel",
    "general counsel",
}

TITLE_KEYWORDS_MEDIUM = {
    "deputy commissioner",
    "deputy director",
    "chief of staff",
    "secretary",
    "treasurer",
    "vice president",
    "chief",
    "assistant commissioner",
}

TITLE_KEYWORDS_LOW = {
    "manager",
    "supervisor",
    "analyst",
    "specialist",
    "coordinator",
    "officer",
}

# Known title code mappings (built from observation)
TITLE_CODE_MAP: dict[str, dict] = {
    # These would be populated from observed data
    # Format: "CODE": {"title": "Title Name", "relevance": 0.0-1.0}
}


def normalize_name(raw_name: str) -> NormalizedName:
    """Normalize a name from Open Data format to standard form.

    Handles formats like:
    - "WALKER,GLEN M."
    - "DOE, JANE"
    - "SMITH,JOHN ROBERT JR."

    Args:
        raw_name: Raw name string from data source

    Returns:
        NormalizedName with parsed components and variants
    """
    if not raw_name or not raw_name.strip():
        return NormalizedName(
            raw=raw_name or "",
            first="",
            middle="",
            last="",
            suffix="",
            full="",
        )

    name = raw_name.strip()

    # Handle "LASTNAME,FIRSTNAME MI" format
    if "," in name:
        parts = name.split(",", 1)
        last_raw = parts[0].strip()
        first_middle = parts[1].strip() if len(parts) > 1 else ""

        # Parse first and middle from remainder
        first_parts = first_middle.split()
        first_raw = first_parts[0] if first_parts else ""
        middle_raw = " ".join(first_parts[1:]) if len(first_parts) > 1 else ""

        # Handle suffix in middle part
        parsed = HumanName(f"{first_raw} {middle_raw} {last_raw}")
    else:
        # Standard name format
        parsed = HumanName(name)

    # Apply title case
    first = parsed.first.title() if parsed.first else ""
    middle = parsed.middle.title() if parsed.middle else ""
    last = parsed.last.title() if parsed.last else ""
    suffix = parsed.suffix if parsed.suffix else ""

    # Build full name
    parts = [first]
    if middle:
        parts.append(middle)
    parts.append(last)
    if suffix:
        parts.append(suffix)
    full = " ".join(p for p in parts if p)

    return NormalizedName(
        raw=raw_name,
        first=first,
        middle=middle,
        last=last,
        suffix=suffix,
        full=full,
    )


def parse_description(description: str) -> ParsedDescription:
    """Parse the additional_description_1 field from Open Data.

    Format: "Key: Value; Key: Value; ..."
    Example: "Effective Date: 10/18/2025; Provisional Status: Yes; ..."

    Args:
        description: Raw description string

    Returns:
        ParsedDescription with extracted fields
    """
    result = ParsedDescription(raw=description)

    if not description:
        return result

    # Split by semicolon
    parts = description.split(";")

    for part in parts:
        part = part.strip()
        if ":" not in part:
            continue

        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "effective date":
            result.effective_date = _parse_date(value)
        elif key == "provisional status":
            result.provisional_status = value
        elif key == "title code":
            result.title_code = value
        elif key == "reason for change":
            result.reason_for_change = value
        elif key == "salary":
            result.salary = _parse_salary(value)
        elif key == "employee name":
            result.employee_name = value

    return result


def _parse_date(date_str: str) -> datetime | None:
    """Parse date string in various formats."""
    formats = [
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def _parse_salary(salary_str: str) -> float | None:
    """Parse salary string to float."""
    try:
        # Remove currency symbols, commas
        cleaned = re.sub(r"[,$]", "", salary_str)
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def get_title_relevance(title_code: str | None, title_text: str | None = None) -> float:
    """Calculate relevance score for a title (0.0 to 1.0).

    Higher scores indicate positions more likely to be principal officers.

    Args:
        title_code: Numeric title code from Open Data
        title_text: Optional title text (if available)

    Returns:
        Relevance score from 0.0 to 1.0
    """
    # Check title code mapping first
    if title_code and title_code in TITLE_CODE_MAP:
        return TITLE_CODE_MAP[title_code].get("relevance", 0.5)

    # Check title text against keywords
    if title_text:
        text_lower = title_text.lower()

        for keyword in TITLE_KEYWORDS_HIGH:
            if keyword in text_lower:
                return 1.0

        for keyword in TITLE_KEYWORDS_MEDIUM:
            if keyword in text_lower:
                return 0.6

        for keyword in TITLE_KEYWORDS_LOW:
            if keyword in text_lower:
                return 0.2

    # Unknown title code, default to medium relevance
    return 0.5


def normalize_agency_name(name: str) -> str:
    """Normalize agency name for comparison.

    Applies:
    - Lowercase
    - Remove punctuation
    - Normalize whitespace
    - Common abbreviation expansion

    Args:
        name: Raw agency name

    Returns:
        Normalized agency name
    """
    if not name:
        return ""

    normalized = name.lower().strip()

    # Remove common punctuation
    normalized = re.sub(r"[.,;:'\"-]", "", normalized)

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    # Common abbreviations (expand for matching)
    abbreviations = {
        "dept": "department",
        "admin": "administration",
        "svcs": "services",
        "svc": "service",
        "mgmt": "management",
        "dev": "development",
        "info": "information",
        "tech": "technology",
        "comm": "commission",
        "auth": "authority",
        "corp": "corporation",
        "bd": "board",
        "off": "office",
        "nyc": "new york city",
    }

    words = normalized.split()
    expanded = [abbreviations.get(w, w) for w in words]
    normalized = " ".join(expanded)

    return normalized


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names (0.0 to 1.0).

    Uses token-based comparison to handle name variations.

    Args:
        name1: First name
        name2: Second name

    Returns:
        Similarity score from 0.0 to 1.0
    """
    if not name1 or not name2:
        return 0.0

    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    # Exact match
    if norm1.full.lower() == norm2.full.lower():
        return 1.0

    # Check variants
    variants1 = set(norm1.variants)
    variants2 = set(norm2.variants)

    if variants1 & variants2:
        return 0.9

    # Token overlap
    tokens1 = set(norm1.full.lower().split())
    tokens2 = set(norm2.full.lower().split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    jaccard = len(intersection) / len(union) if union else 0.0

    # Boost if last names match
    if norm1.last.lower() == norm2.last.lower() and norm1.last:
        jaccard = min(1.0, jaccard + 0.3)

    return jaccard
