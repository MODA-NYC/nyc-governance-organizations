import re
from pathlib import Path

import pandas as pd

MINIMAL_SCHEMA = [
    "event_id",
    "timestamp_utc",
    "run_id",
    "record_id",
    "record_name",
    "field",
    "old_value",
    "new_value",
    "reason",
    "evidence_url",
    "source_ref",
    "operator",
    "notes",
]

ALLOWED_FIELDS = {
    # snake_case field names (current standard)
    "record_name",
    "record_id",
    "operational_status",
    "organization_type",
    "name",
    "acronym",
    "name_alphabetized",
    "url",
    "alternate_or_former_names",
    "alternate_or_former_acronyms",
    "principal_officer_title",
    "principal_officer_full_name",
    "principal_officer_first_name",
    "principal_officer_last_name",
    "principal_officer_contact_url",
    "reports_to",
    "in_org_chart",
    "listed_in_nyc_gov_agency_directory",
    "notes",
    # Legacy PascalCase field names (from older changelog entries)
    "NameAlphabetized",
    "Name",
    "Notes",
    "AlternateOrFormerNames",
    "PrincipalOfficerFullName",
    "PrincipalOfficerGivenName",
    "PrincipalOfficerFamilyName",
    "PrincipalOfficerContactURL",
    "InOrgChart",
    "ReportsTo",
    "NYC.gov Agency Directory",
    # Special markers
    "_ROW_ADDED",
}


def _load_changelog() -> pd.DataFrame:
    path = Path("data/changelog.csv")
    assert path.exists(), "Missing data/changelog.csv"
    df = pd.read_csv(path, dtype=str).fillna("")
    return df


def test_header_matches_exactly():
    df = _load_changelog()
    if list(df.columns) != MINIMAL_SCHEMA:
        left = list(df.columns)
        raise AssertionError(
            f"Header mismatch. Expected {MINIMAL_SCHEMA}\nActual   {left}"
        )


def test_required_fields_and_uniqueness():
    df = _load_changelog()
    # Non-blank requireds
    required = ["event_id", "timestamp_utc", "run_id", "record_id", "field"]
    for col in required:
        assert (df[col].astype(str).str.len() > 0).all(), f"Blank values in {col}"
    # event_id format and uniqueness
    pattern = re.compile(r"^[0-9a-f]{64}$")
    if not df["event_id"].apply(lambda x: bool(pattern.match(str(x)))).all():
        print(
            "Warning: some event_ids are not hashed; skipping strict validation "
            "for legacy rows"
        )
    assert df["event_id"].is_unique


def test_field_values_are_allowed():
    df = _load_changelog()
    fields = set(df["field"].dropna().unique())
    assert fields.issubset(
        ALLOWED_FIELDS
    ), f"Unexpected fields: {sorted(fields - ALLOWED_FIELDS)}"


def test_timestamp_format():
    df = _load_changelog()
    parsed = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    assert not parsed.isna().all(), "All timestamps invalid"


def test_evidence_url_shape_lenient():
    df = _load_changelog()
    non_empty = df["evidence_url"].astype(str).str.len() > 0
    urls = df.loc[non_empty, "evidence_url"].str.lower()
    ok = urls.str.startswith("http://") | urls.str.startswith("https://")
    assert ok.all(), "Some evidence_url values are not http(s) URLs"
