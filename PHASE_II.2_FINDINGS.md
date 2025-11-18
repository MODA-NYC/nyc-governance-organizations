# Phase II.2 Data Collection - Initial Findings

**Date:** November 15, 2024
**Status:** Week 1 Complete - Data Collection Successful ✅

---

## 📊 Summary Statistics

### Data Extraction
- **MOA Entities Scraped:** 109
- **Entities with descriptions:** 109 (100%)
- **Entities with URLs:** 75 (68.8%)
- **Source:** https://www.nyc.gov/content/appointments/pages/boards-commissions

### Crosswalk Matching (MOA → NYCGO)
- **Total matches:** 103 (94.5%)
- **Exact matches:** 47 (43.1%)
- **High confidence:** 7 (6.4%)
- **Medium confidence:** 12 (11.0%)
- **Low confidence (needs review):** 37 (33.9%)
- **No match found:** 6 (5.5%)

### Coverage Gaps
- **MOA entities not in NYCGO:** 6 (need to add)
- **NYCGO entities not in MOA:** 250
- **High-priority gaps:** 120
- **Medium-priority gaps:** 136

---

## 🎯 Key Findings

### 1. MOA Universe is Smaller Than Expected
The Mayor's Office of Appointments page lists **109 entities**, which is approximately **25% of the 433 entities** in the NYCGO dataset. This means:
- MOA focuses on boards/commissions with mayoral appointments
- Many NYCGO entities (agencies, offices, etc.) don't appear on MOA page
- This is expected - MOA is appointments-specific

### 2. Strong Matching Success
**94.5% of MOA entities matched** to NYCGO dataset:
- 54 exact or high-confidence matches (49.5%)
- 49 medium or low-confidence matches (45%)
- Only 6 completely unmatched (5.5%)

This indicates:
- ✅ NYCGO dataset has good coverage of appointed boards/commissions
- ✅ Entity naming is generally consistent
- ⚠️ Some manual review needed for low-confidence matches

### 3. Entities to Add to NYCGO Dataset

The following **6 MOA entities** are not in NYCGO and should be added:

1. **New York City Global Partners, Inc - Board of Directors**
   - URL: http://www.nyc.gov/html/unccp/scp/html/about/organization.shtml
   - Type: Non-profit partnership board

2. **Quadrennial Advisory Commission for the Review of Compensation Levels of Elected Officials**
   - URL: (none provided)
   - Type: Advisory commission

3. **SWMP Converted Marine Transfer Station Community Advisory Group - Gansevoort (Manhattan)**
   - URL: (none provided)
   - Type: Community advisory group

4. **Teachers' Retirement Board - Teachers' Retirement System**
   - URL: https://www.trsnyc.org/memberportal/About-Us/ourRetirementBoard
   - Type: Pension fund board

5. **Veterans' Advisory Board - Mayor's Office of Veterans' Affairs**
   - URL: https://www1.nyc.gov/site/veterans/community/veterans-advisory-board.page
   - Type: Advisory board

6. **World Trade Center Memorial Foundation - Board of Directors National September 11 Memorial and Museum at the WTC**
   - URL: https://www.911memorial.org/about/board-trustees
   - Type: Nonprofit foundation board

### 4. NYCGO Entities Not on MOA Page

**250 active NYCGO entities** are not on the MOA appointments page. Breakdown by type:

| Organization Type | Count | Notes |
|------------------|-------|-------|
| Mayoral Office | 78 | Expected - not appointment-based |
| Nonprofit Organization | 52 | Some may be partners, not City entities |
| Advisory or Regulatory Organization | 36 | **Should review** - may belong on MOA |
| Mayoral Agency | 29 | Expected - not appointment-based |
| Division | 20 | Expected - internal units |
| Public Benefit or Development Organization | 15 | May have appointed boards |
| Elected Office | 14 | Expected - not mayoral appointments |
| State Government Agency | 5 | Expected - not City |
| Pension Fund | 1 | Expected - separate governance |

**Action needed:** Review 36 "Advisory or Regulatory Organization" entities in NYCGO that aren't on MOA page to determine if they should be.

---

## 🔍 Entities Needing Manual Review (43 total)

### Low-Confidence Matches (37 entities)

These matched with similarity scores below 0.80 and need verification:

**Examples:**
- **Banking Commission - Department of Finance** → matched to "Department of Finance" (0.667)
  - *Likely incorrect* - should create separate entity for Banking Commission

- **Brooklyn Public Library - Board of Trustees** → matched to "Brooklyn Public Library" (0.697)
  - *Needs decision* - keep as one entity or separate board?

- **Central Park Conservancy - Board of Trustees** → matched to "Central Park Conservancy" (0.706)
  - *Needs decision* - keep as one entity or separate board?

**Pattern observed:** Many MOA entries are "X - Board of Trustees" while NYCGO has just "X". Need to decide:
- Option A: Keep parent organization only (collapse boards into parent)
- Option B: Create separate entities for boards
- Option C: Mixed approach based on governance structure

### Review Needed Items

See `data/crosswalk/moa_to_nycgo_mapping.csv` where `needs_manual_review = yes` (43 rows).

---

## 📋 Recommended Actions

### Immediate (This Week)

1. **Add 6 new entities to NYCGO dataset**
   - Create RecordIDs (NYC_GOID_XXXXX)
   - Populate basic fields (Name, Type, URL, Description)
   - Use MOA descriptions as starting point

2. **Review low-confidence matches**
   - Focus on "Board of Trustees" pattern (appears ~15 times)
   - Decide on governance structure approach
   - Update crosswalk with corrections

3. **Validate high-priority gaps**
   - Review 36 Advisory/Regulatory orgs not in MOA
   - Determine if any should be on MOA page
   - Document reasoning for exclusions

### Short-Term (Next 2 Weeks)

4. **Populate Phase II fields for MOA entities**
   - `appointments_summary`: Use MOA descriptions (already have 109)
   - `authorizing_url`: Extract from MOA page (have 75 URLs)
   - `authorizing_authority`: Research needed
   - `org_chart_oversight`: Match to parent agencies

5. **Integrate MOO dataset** (when available)
   - Cross-reference with MOA data
   - Add authorizing authority information
   - Identify additional entities

### Medium-Term (Weeks 3-4)

6. **Legal research for authorizing authorities**
   - NYC Charter sections
   - Admin Code references
   - Executive orders
   - Target: 100% of 433 entities

---

## 📁 Output Files Created

### Primary Data Files
1. **`data/scraped/moa_appointments_raw.csv`**
   - 109 MOA entities
   - Fields: entity_name, description, url, scraped_date, source_url

2. **`data/crosswalk/moa_to_nycgo_mapping.csv`**
   - 109 rows (one per MOA entity)
   - Match confidence levels, similarity scores
   - 43 flagged for manual review

3. **`data/analysis/moa_coverage_gaps.csv`**
   - 256 gap records (6 in MOA + 250 in NYCGO)
   - Priority levels assigned
   - Action recommendations

### Documentation
4. **`data/scraped/SCRAPING_NOTES.md`**
   - Technical notes on scraping approach
   - HTML structure documentation
   - Troubleshooting guide

5. **`data/scraped/README.md`**
   - Step-by-step instructions for data collection
   - Quick start guide for future updates

---

## 💡 Insights & Observations

### Data Quality
- ✅ **MOA descriptions are comprehensive** - averaging ~150-200 words per entity
- ✅ **URLs mostly complete** - 68.8% have official websites
- ✅ **Naming generally consistent** with NYCGO dataset
- ⚠️ **Board vs. Parent org ambiguity** - need governance structure policy

### Coverage Assessment
- **MOA page is well-maintained** - represents current appointment entities
- **NYCGO has broader scope** - includes non-appointment entities (correct)
- **Minimal missing entities** - only 6 to add (1.4% of NYCGO)
- **Good foundation for Phase II fields** - descriptions can populate `appointments_summary`

### Next Phase Readiness
- **Ready for field population:** Can immediately populate `appointments_summary` for 103 matched entities
- **URLs available:** 75 entities have `authorizing_url` candidates
- **Research needed:** `authorizing_authority` requires legal research for most entities
- **Org chart work:** `org_chart_oversight` needs parent agency mapping

---

## 🎯 Success Metrics - Week 1

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| MOA entities scraped | ~100-200 | 109 | ✅ |
| Crosswalk created | Yes | Yes | ✅ |
| Gap analysis complete | Yes | Yes | ✅ |
| Validation script ready | Yes | Yes | ✅ |
| Entities to add identified | N/A | 6 | ✅ |
| Match rate | >80% | 94.5% | ✅ |

**Overall:** Week 1 objectives exceeded. Data collection infrastructure complete and ready for field population phase.

---

## 📝 Notes for Colleagues

### Review Priorities
1. **Governance structure decision** - How to handle "Board of" entities (see "Low-Confidence Matches" section)
2. **6 new entities** - Approve additions before creating RecordIDs
3. **Advisory org gaps** - 36 entities in NYCGO not on MOA - verify this is correct

### Questions to Address
- Should we create separate entities for boards vs. parent organizations?
- Are all 36 Advisory/Regulatory orgs correctly excluded from MOA scope?
- What's the timeline for receiving the MOO dataset?
- Which authorizing authority sources are authoritative (Charter vs. Admin Code vs. EO)?

---

**Next Update:** After manual review and new entity additions
