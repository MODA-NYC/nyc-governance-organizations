# NYCGO Appointments Monitor

> **Status**: Implemented, Partially Backburnered
> **Last Updated**: 2026-01-02

## Current Status (January 2026)

**Implemented and working:**
- Appointment scanning via NYC Open Data
- CROL scraping for person search
- Scoring and report generation

**Backburnered:**
- Departure validation (`--check-departures`) - high false positive rate, see details below

**Key Findings from Testing:**

| Issue | Impact |
|-------|--------|
| **Data lag** | Both NYC Open Data and CROL are ~2-6 months behind actual personnel changes |
| **Departure false positives** | Finding *any* departure, not just from current role. Career transitions (e.g., Council Member → Commissioner) incorrectly flagged |
| **Advisory positions** | CROL tracks city employee payroll; advisory board chairs may not have payroll records |

**Recommendation:** Use appointment scanning for finding new appointments. For departure monitoring, rely on news/manual tracking for now. See `docs/BACKLOG.md` for full analysis.

---

## Overview

The Appointments Monitor is a batch scanning tool that identifies potential principal officer changes in NYC government organizations by querying public data sources and generating reviewable candidate reports.

**Key Principle**: This tool generates evidence and recommendations for human review. It does NOT automatically modify the golden dataset.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPOINTMENTS MONITOR PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │  NYC Open Data│     │     CROL      │     │ Golden Dataset│
  │ (Structured)  │     │ (HTML/Search) │     │   (Current)   │
  └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
          │                     │                     │
          │ Socrata API         │ HTTP/Parse          │ Load CSV
          ▼                     ▼ (optional)          ▼
  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │ Raw Personnel │     │ CROL Notices  │     │  Current Org  │
  │   Records     │     │   (backup)    │     │   Officers    │
  └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
          │                     │                     │
          └─────────┬───────────┘                     │
                    │ Parse & Normalize               │
                    ▼                                 │
          ┌───────────────┐                          │
          │  Normalized   │                          │
          │  Candidates   │                          │
          └───────┬───────┘                          │
                  │                                   │
                  │◄──────────────────────────────────┘
                  │ Match & Score
                  ▼
          ┌───────────────┐
          │   Scored      │
          │  Candidates   │
          └───────┬───────┘
                  │
                  │ Generate Reports
                  ▼
  ┌────────────────────────────────────────────────────┐
  │              OUTPUT: data/reports/appointments/    │
  │  ┌──────────────┐ ┌────────────┐ ┌──────────────┐ │
  │  │candidates.json│candidates.csv│candidates_   │ │
  │  │              │ │(bulk upload)│ │summary.md   │ │
  │  └──────────────┘ └────────────┘ └──────────────┘ │
  └────────────────────────────────────────────────────┘
                  │
                  │ Human Review
                  ▼
          ┌───────────────┐
          │  Bulk Upload  │
          │   Workflow    │
          └───────────────┘
```

---

## Data Sources

### Primary: NYC Open Data - Changes in Personnel

**Dataset ID**: `wq4v-8hyb`
**API Endpoint**: `https://data.cityofnewyork.us/resource/wq4v-8hyb.json`
**Source**: Department of Citywide Administrative Services (DCAS)
**Update Frequency**: Daily (reflects City Record publications)

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `end_date` | datetime | Publication/effective date |
| `agency_name` | text | City agency name |
| `additional_description_1` | text | Semi-structured details (see below) |

**Description Field Format** (parsed from `additional_description_1`):
```
Effective Date: MM/DD/YYYY; Provisional Status: Yes/No; Title Code: XXXX;
Reason For Change: <REASON>; Salary: XXXXX.XX; Employee Name: LASTNAME,FIRSTNAME M.
```

**Relevant "Reason For Change" Values**:
- `APPOINTED` - New appointment
- `PROMOTED` - Internal promotion
- `REASSIGNED` - Transfer to new role
- `RETIRED` - Separation (may indicate vacancy)
- `RESIGNED` - Separation (may indicate vacancy)
- `TERMINATED` - Separation (may indicate vacancy)

**Reliability**: HIGH
- Authoritative government source
- Structured, machine-readable
- Covers all city agencies
- Updated daily

**Limitations**:
- Title codes are numeric, not descriptive
- Only captures formal personnel actions
- Name format is "LASTNAME,FIRSTNAME" requiring normalization
- No direct link to NYCGO record IDs

### Secondary: City Record Online (CROL)

**Website**: `https://a856-cityrecord.nyc.gov/`
**Section**: Special Materials > Changes in Personnel

**Use Case**: Supplemental evidence when Open Data match is weak

**Reliability**: MEDIUM
- Same source data as Open Data (City Record)
- Requires HTML parsing (fragile)
- Provides additional context in notice text
- Search-based (requires name/agency query)

**Limitations**:
- No stable API
- HTML structure may change
- Rate limiting required
- Search may return false positives

---

## Matching Algorithm

### Stage 1: Name Normalization

```python
# Input: "WALKER,GLEN M."
# Output: {"first": "Glen", "middle": "M", "last": "Walker", "full": "Glen M. Walker"}

1. Parse "LASTNAME,FIRSTNAME MI" format
2. Apply title case
3. Handle suffixes (Jr., Sr., III)
4. Generate full name string
5. Create search variants (initials, no middle)
```

### Stage 2: Organization Matching

For each personnel record, attempt to match against NYCGO organizations:

| Match Type | Weight | Method |
|------------|--------|--------|
| Exact Name | 40 | `agency_name` == `name` |
| Alternate Name | 35 | `agency_name` in `alternate_or_former_names` |
| Acronym | 30 | `agency_name` == `acronym` |
| Fuzzy Match | 20 | Token overlap >= 80% |
| Source Names | 25 | Match against `name_*` columns |

**Implementation**:
```python
def match_organization(agency_name: str, golden_df: pd.DataFrame) -> list[OrgMatch]:
    """Return list of potential org matches with confidence scores."""
    matches = []

    # Exact match on primary name
    exact = golden_df[golden_df["name"].str.lower() == agency_name.lower()]
    if not exact.empty:
        matches.append(OrgMatch(record_id=..., confidence=1.0, match_type="exact"))

    # Check alternate names (semicolon-separated)
    for idx, row in golden_df.iterrows():
        alt_names = row.get("alternate_or_former_names", "").split(";")
        if any(agency_name.lower() == alt.strip().lower() for alt in alt_names):
            matches.append(OrgMatch(..., confidence=0.9, match_type="alternate"))

    # ... additional matching strategies
    return matches
```

### Stage 3: Title Relevance

Only certain titles indicate principal officer positions:

**High Relevance** (weight 1.0):
- Commissioner
- Director (Executive Director, Deputy Director)
- Chair / Chairperson
- President
- Chief Executive Officer (CEO)
- Administrator
- Counsel (Corporation Counsel, General Counsel)

**Medium Relevance** (weight 0.6):
- Deputy Commissioner
- Chief of Staff
- Secretary
- Treasurer

**Low Relevance** (weight 0.2):
- Manager
- Supervisor
- Analyst

**Title Extraction**:
The Open Data provides title codes, not title strings. We maintain a mapping:
```python
TITLE_CODE_MAP = {
    "1002D": {"title": "Assistant Corporation Counsel", "relevance": 0.6},
    # ... built from observation
}
```

For unknown codes, we flag as "UNKNOWN_TITLE" and set relevance to 0.5.

### Stage 4: Change Detection

Compare candidate against current NYCGO data:

| Scenario | Recommended Action |
|----------|-------------------|
| New person, org has officer | `UPDATE_OFFICER` |
| New person, org has no officer | `ADD_OFFICER` |
| Person leaving, org has same officer | `VERIFY_VACANCY` |
| No matching org | `MANUAL_REVIEW` |
| Low confidence match | `VERIFY` |

---

## Confidence Scoring

**Score Range**: 0-100

### Score Components

| Component | Max Points | Criteria |
|-----------|------------|----------|
| Org Match | 40 | See matching table above |
| Name Match | 25 | Against current officer if exists |
| Title Match | 20 | Relevance of position title |
| Recency | 10 | More recent = higher score |
| Evidence Count | 5 | Multiple sources = higher confidence |

### Score Interpretation

| Range | Label | Action |
|-------|-------|--------|
| 80-100 | HIGH | Strong candidate, likely valid |
| 50-79 | MEDIUM | Plausible, needs verification |
| 20-49 | LOW | Weak match, probable false positive |
| 0-19 | NOISE | Likely irrelevant, auto-filter |

### Score Calculation

```python
def calculate_score(candidate: Candidate) -> int:
    score = 0

    # Organization match quality
    score += candidate.org_match.confidence * 40

    # Title relevance
    score += candidate.title_relevance * 20

    # Name match against current officer (if updating)
    if candidate.action == "UPDATE_OFFICER":
        # Penalize if names are very similar (probably same person, no change)
        if name_similarity(candidate.name, candidate.current_officer) > 0.9:
            score -= 20  # Same person, not a change

    # Recency bonus
    days_old = (datetime.now() - candidate.effective_date).days
    if days_old <= 7:
        score += 10
    elif days_old <= 30:
        score += 5

    # Evidence count
    score += min(len(candidate.sources), 3) * 1.67  # Up to 5 points

    return max(0, min(100, round(score)))
```

---

## Output Formats

### candidates.json

Full structured output with all evidence:

```json
{
  "scan_metadata": {
    "scan_date": "2025-12-30T10:30:00Z",
    "date_range": {"start": "2025-11-30", "end": "2025-12-30"},
    "sources_queried": ["open_data", "crol"],
    "golden_dataset_version": "v1.7.12",
    "total_records_scanned": 150,
    "candidates_found": 12
  },
  "candidates": [
    {
      "candidate_id": "APPT_20251230_001",
      "nycgo_record_id": "NYC_GOID_000123",
      "nycgo_org_name": "Department of Buildings",
      "current_principal_officer": "John Smith",
      "candidate_name": "Jane Doe",
      "candidate_title": "Commissioner",
      "effective_date": "2025-12-15",
      "reason_for_change": "APPOINTED",
      "sources": [
        {
          "type": "open_data",
          "url": "https://data.cityofnewyork.us/resource/wq4v-8hyb.json?...",
          "raw_record": {...},
          "retrieved_at": "2025-12-30T10:25:00Z"
        }
      ],
      "match_details": {
        "org_match_type": "exact",
        "org_match_confidence": 1.0,
        "title_relevance": 1.0,
        "name_normalized": "Jane Doe"
      },
      "score": 85,
      "recommended_action": "UPDATE_OFFICER",
      "reviewer_notes": ""
    }
  ]
}
```

### candidates.csv

Compatible with bulk upload workflow:

```csv
record_id,record_name,field_name,action,justification,evidence_url
NYC_GOID_000123,Department of Buildings,principal_officer_full_name,direct_set,Appointment of Jane Doe as Commissioner per City Record 2025-12-15,https://data.cityofnewyork.us/...
NYC_GOID_000123,Department of Buildings,principal_officer_title,direct_set,Commissioner appointment per City Record 2025-12-15,https://data.cityofnewyork.us/...
```

**Note**: Only candidates with score >= 50 and action `UPDATE_OFFICER` or `ADD_OFFICER` are included in the CSV. Lower-confidence candidates appear only in JSON for manual review.

### candidates_summary.md

Human-readable report:

```markdown
# Appointments Monitor Scan Report
**Scan Date**: 2025-12-30
**Period**: 2025-11-30 to 2025-12-30

## Summary
- **Records Scanned**: 150
- **Candidates Found**: 12
- **High Confidence (80+)**: 3
- **Medium Confidence (50-79)**: 5
- **Low Confidence (<50)**: 4

## High Confidence Candidates

### 1. Department of Buildings - Commissioner
- **Candidate**: Jane Doe
- **Effective Date**: 2025-12-15
- **Current Officer**: John Smith
- **Score**: 85/100
- **Action**: UPDATE_OFFICER
- **Evidence**: [City Record](https://...)

[...]

## Next Steps
1. Review high-confidence candidates in admin UI
2. Verify medium-confidence candidates manually
3. Discard low-confidence candidates or investigate further
```

---

## Implementation Architecture

```
src/nycgo_pipeline/appointments/
├── __init__.py           # Package exports
├── fetch_open_data.py    # Socrata API client
├── fetch_crol.py         # CROL HTML parsing (optional, behind flag)
├── normalize.py          # Name/title normalization
├── match.py              # Organization/person matching
├── score.py              # Confidence scoring
├── report.py             # Output generation (JSON, CSV, MD)
└── cli.py                # CLI logic (called by script)

scripts/
└── scan_appointments.py  # Entry point script

tests/
├── test_appointments/
│   ├── test_normalize.py
│   ├── test_match.py
│   ├── test_score.py
│   └── test_integration.py
└── fixtures/
    └── appointments/
        ├── open_data_sample.json
        ├── crol_sample.html
        └── golden_sample.csv
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `fetch_open_data` | Query Socrata API, handle pagination, cache results |
| `fetch_crol` | Search CROL, parse HTML notices, rate limit |
| `normalize` | Parse names, normalize titles, standardize formats |
| `match` | Match candidates to NYCGO orgs, compare officers |
| `score` | Calculate confidence scores, classify actions |
| `report` | Generate JSON, CSV, and Markdown outputs |
| `cli` | Parse arguments, orchestrate pipeline, handle errors |

---

## CLI Interface

```bash
# Basic usage - scan last 30 days
python scripts/scan_appointments.py

# Custom date range
python scripts/scan_appointments.py --days 60
python scripts/scan_appointments.py --start-date 2025-11-01 --end-date 2025-12-01

# Include CROL supplemental data (slower, optional)
python scripts/scan_appointments.py --include-crol

# Specify output directory
python scripts/scan_appointments.py --output data/reports/appointments_custom/

# Filter by minimum score
python scripts/scan_appointments.py --min-score 50

# Use cached data (skip API calls)
python scripts/scan_appointments.py --use-cache

# Verbose output
python scripts/scan_appointments.py -v
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--days` | 30 | Number of days to look back |
| `--start-date` | (computed) | Explicit start date (YYYY-MM-DD) |
| `--end-date` | today | Explicit end date (YYYY-MM-DD) |
| `--include-crol` | false | Enable CROL HTML scraping |
| `--output` | `data/reports/appointments_YYYYMMDD/` | Output directory |
| `--min-score` | 0 | Minimum score to include in output |
| `--use-cache` | false | Use cached API responses |
| `--cache-dir` | `.cache/appointments/` | Cache directory |
| `-v, --verbose` | false | Verbose logging |

---

## Caching Strategy

### API Response Cache

Location: `.cache/appointments/`

```
.cache/appointments/
├── open_data/
│   └── wq4v-8hyb_2025-11-30_2025-12-30.json
└── crol/
    └── search_jane_doe_buildings.html
```

**Cache Key Format**:
- Open Data: `{dataset_id}_{start_date}_{end_date}.json`
- CROL: `search_{query_hash}.html`

**Cache TTL**: 24 hours (configurable)

### Golden Dataset Cache

The golden dataset is loaded fresh each run (no caching) to ensure current data.

---

## Rate Limiting

### NYC Open Data (Socrata)

- **Default limit**: 1000 requests/hour (unauthenticated)
- **Implementation**: 1 second delay between paginated requests
- **Batch size**: 1000 records per request
- **App token**: Optional, increases limit to 10,000/hour

### CROL

- **Implementation**: 2 second delay between requests
- **Max requests per run**: 50 (configurable)
- **Backoff**: Exponential on 429/503 errors

---

## Error Handling

| Error Type | Handling |
|------------|----------|
| Network timeout | Retry 3x with exponential backoff |
| API rate limit | Wait and retry, warn user |
| Parse error | Log warning, skip record, continue |
| No matches found | Report empty results, not an error |
| Invalid date range | Exit with clear error message |
| Missing golden dataset | Exit with error, suggest path |

---

## Limitations and Caveats

### Known Limitations

1. **Title Code Mapping**: NYC Open Data uses numeric title codes, not descriptive titles. We maintain a best-effort mapping, but some codes may be unknown.

2. **Name Ambiguity**: Common names may match multiple people. The scoring system penalizes ambiguous matches but cannot guarantee uniqueness.

3. **Organization Name Variance**: Agency names in Open Data may not exactly match NYCGO names. Fuzzy matching helps but may produce false positives.

4. **Timing Lag**: Personnel changes may appear in City Record before or after the effective date. Cross-reference with other sources when possible.

5. **Partial Coverage**: Not all leadership positions are reported in City Record. Board appointments, for example, may not appear.

6. **CROL Fragility**: HTML parsing may break if CROL redesigns their website. The CROL integration is optional and best-effort.

### What This Tool Cannot Do

- Automatically update the golden dataset
- Verify appointment information independently
- Distinguish between different people with the same name
- Find appointments not published in City Record
- Track interim or acting appointments reliably

### Recommended Workflow

1. Run scan weekly or after known leadership changes
2. Review high-confidence candidates first
3. Verify medium-confidence candidates with secondary sources
4. Discard low-confidence candidates unless pattern emerges
5. Import verified candidates via bulk upload workflow
6. Document rejected candidates for future reference

---

## Future Enhancements (Not MVP)

- **Continuous monitoring**: Scheduled runs with change detection
- **Email alerts**: Notify on high-confidence matches
- **Web dashboard**: Visual review interface
- **Historical tracking**: Build appointment history database
- **Additional sources**: Mayoral press releases, agency websites
- **Title code learning**: Build mapping from observed data
- **ML-assisted matching**: Train on verified matches (post-MVP)

---

## Running the Tool

### Prerequisites

```bash
# Install dependencies (if not already installed)
pip install -e ".[dev]"
```

### Basic Scan

```bash
# Scan last 30 days, output to default location
python scripts/scan_appointments.py

# Output:
# data/reports/appointments_20251230/
#   ├── candidates.json
#   ├── candidates.csv
#   └── candidates_summary.md
```

### Review Results

1. Open `candidates_summary.md` for quick overview
2. Review high-confidence candidates in JSON for full details
3. Import approved candidates via `candidates.csv` using bulk upload

---

## Test Fixtures

Test fixtures are stored in `tests/fixtures/appointments/`:

### open_data_sample.json

Sample Socrata API response with various personnel change types.

### golden_sample.csv

Minimal golden dataset for matching tests.

### expected_candidates.json

Expected output for integration tests.

### Adding New Fixtures

1. Query real API with specific parameters
2. Anonymize sensitive data if needed
3. Save to fixtures directory
4. Update integration tests to use new fixture
