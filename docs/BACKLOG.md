# NYCGO Project Backlog

This document tracks features and improvements that have been explored, partially implemented, or deferred for future consideration.

---

## Backburnered: Appointments Monitor - Departure Validation

**Status:** Backburnered (January 2026)
**Priority:** Low
**Location:** `src/nycgo_pipeline/appointments/`

### What Was Built

An "Appointments Monitor" feature that scans public data sources to identify potential principal officer changes:

1. **Appointment Scanning** (`--days 30` mode)
   - Fetches personnel records from NYC Open Data (Socrata API, dataset `wq4v-8hyb`)
   - Matches records to NYCGO organizations using fuzzy matching
   - Scores candidates based on org match, title relevance, name differentiation
   - Generates reports (JSON, CSV, Markdown)

2. **Departure Validation** (`--check-departures` mode)
   - Searches City Record Online (CROL) for each principal officer
   - Identifies departure records (RESIGNED, RETIRED, TERMINATED)
   - Attempts to match departures to current organization

3. **CROL Scraper** (`fetch_crol.py`)
   - Working scraper for City Record Online
   - Rate-limited, cached requests
   - Can search by name, date range, action type

### What Works Well

- **Appointment scanning** successfully identifies new personnel actions
- **CROL scraper** reliably fetches and parses personnel records
- **Person search** is useful for researching specific individuals' career history
- Good test coverage (56 tests passing)

### Key Limitations Discovered

1. **Data Lag (~2-6 months)**
   - NYC Open Data: ~2.5 months behind (latest data: Oct 2025 as of Jan 2026)
   - CROL: Similar lag, plus additional delay for vacation/leave time
   - Executive departures may not appear for months after "last day in office"

2. **Departure Check False Positives (High)**
   - Finding *any* departure in someone's history, not just from current role
   - Career transitions flagged incorrectly (e.g., Leila Bozorg left City Planning Commissioner role → became Deputy Mayor)
   - Elected officials leaving Council for higher office flagged incorrectly
   - Name collisions with unrelated people

3. **Fundamental Challenge**
   - To properly identify stale records, need to fetch FULL career history and check if most recent action is a departure with no subsequent appointment
   - This dramatically increases API calls and complexity
   - CROL tracks payroll/HR actions, not advisory board positions

### Files Created

```
src/nycgo_pipeline/appointments/
├── __init__.py           # Package exports
├── cli.py                # CLI with --check-departures mode
├── fetch_open_data.py    # NYC Open Data Socrata client
├── fetch_crol.py         # City Record Online scraper
├── normalize.py          # Name/title normalization
├── match.py              # Organization matching
├── score.py              # Confidence scoring
├── check_departures.py   # Departure validation logic
└── report.py             # Report generation

scripts/
└── scan_appointments.py  # Entry point

tests/test_appointments/
├── test_normalize.py     # 24 tests
├── test_match.py         # 9 tests
├── test_score.py         # 12 tests
└── test_integration.py   # 11 tests

docs/
└── APPOINTMENTS_MONITOR.md  # Design document
```

### Usage (Current State)

```bash
# Scan for new appointments (works reasonably well)
python scripts/scan_appointments.py --days 60

# Check departures (high false positive rate - use with caution)
python scripts/scan_appointments.py --check-departures

# Search for specific person's CROL history (useful utility)
python -c "from nycgo_pipeline.appointments.fetch_crol import search_person; print(search_person('Matthew Fraser'))"
```

### If Resuming This Work

To make departure validation useful, consider:

1. **Full Career History Analysis**
   - Fetch all CROL records (appointments AND departures) for each person
   - Sort chronologically
   - Only flag if most recent action is departure with no subsequent appointment
   - Significant increase in API calls

2. **Agency Matching Improvements**
   - Better mapping between CROL agency names and NYCGO organization names
   - Handle cases where someone leads an advisory body but isn't a city employee

3. **Alternative Approaches**
   - News/press release monitoring for leadership announcements
   - Integration with official appointment announcements
   - Manual quarterly review of key agencies

### Why Backburnered

- Signal-to-noise ratio too low for departure validation
- Appointment scanning provides some value but data lag limits usefulness
- Other NYCGO priorities more impactful
- Can revisit if data sources improve or manual review burden increases

---

## Future Ideas

### Data Quality Improvements
- [ ] Automated detection of URL changes/broken links
- [ ] Cross-reference with official NYC.gov agency directory
- [ ] Validate organization operational status against external sources

### Pipeline Enhancements
- [ ] Scheduled/automated pipeline runs
- [ ] Email notifications for detected changes
- [ ] Integration with admin UI for streamlined review

### Schema Expansions
- [ ] Phase II: 46-field schema with 9 new orgs (currently deferred)
- [ ] Additional relationship fields (parent/child orgs)
- [ ] Historical tracking of principal officer changes

---

*Last updated: January 2026*
