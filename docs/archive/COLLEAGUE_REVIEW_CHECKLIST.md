# Phase II Schema Changes - Colleague Review Checklist

**Date:** November 14, 2024
**For Review:** Phase II.0 & II.1 Completion (v2.0.0 Schema Expansion)
**Documentation:** See `docs/PHASE_II_SCHEMA.md` for full details

---

## 🔴 CRITICAL DECISIONS NEEDED

### A) Review the New Field Definitions
**Action Required:** Team review and approval of 4 new fields

#### New Fields Added (v2.0.0):
1. **`org_chart_oversight`** - Administrative oversight from Mayor's org charts
   - Captures org chart placement vs. legal reporting
   - Distinguishes political coordination from formal authority
   - Example: Dept of City Planning appears under Deputy Mayor in org chart

2. **`authorizing_authority`** - Legal basis for entity's existence
   - **100% population target** (required for all 433 entities)
   - Format: "NYC Charter § 1301", "Local Law 128 of 2013", etc.
   - Critical for understanding legal jurisdictional boundaries

3. **`authorizing_url`** - Link to authorizing legal documents
   - **90%+ population target**
   - Must be official government sources (NYC.gov, State Legislature, etc.)
   - Enhances transparency and auditability

4. **`appointments_summary`** - How leadership is appointed
   - Free text describing appointment mechanisms
   - Example: "Commissioner appointed by Mayor; Deputy Commissioners appointed by Commissioner"
   - Target: All entities with mayoral appointments

**Questions for Team:**
- [ ] Do these field definitions align with project goals?
- [ ] Are the population targets (100%, 90%) reasonable given resources?
- [ ] Any concerns about data collection burden for these fields?
- [ ] Should any fields be marked as optional vs. required?

---

### B) Decide: Deprecate or Redefine `ReportsTo` Field?
**Action Required:** Choose approach for handling breaking change

#### The Issue:
In v1.0.0, the `ReportsTo` field conflated multiple concepts:
- Legal/Charter-defined reporting relationships
- Organizational chart placement
- Political oversight

This created ambiguity and made the field less useful for analysis.

#### Option 1: REDEFINE (Current Approach) ⭐ RECOMMENDED
**What happens:**
- `ReportsTo` is **redefined** to mean ONLY legal/managerial reporting
- Org chart relationships move to new `org_chart_oversight` field
- This is a **BREAKING CHANGE** (requires v2.0.0 major version bump)

**Pros:**
- Preserves field name (less disruptive to users)
- Clarifies semantics (single, clear meaning)
- Maintains dataset continuity

**Cons:**
- Breaking change for v1.0.0 users who relied on old definition
- Requires user migration (documented in `docs/PHASE_II_SCHEMA.md`)
- Some values will need to be moved between fields

**Migration Impact:**
- Values that reflected ONLY org chart placement → move to `org_chart_oversight`
- Values that reflected legal reporting → stay in `ReportsTo`
- Example: "Dept of City Planning" changes from "Deputy Mayor" → "Mayor" in ReportsTo, "Deputy Mayor" in org_chart_oversight

#### Option 2: DEPRECATE (Alternative)
**What happens:**
- Mark `ReportsTo` as deprecated in v2.0.0
- Create NEW field `legal_reports_to` with clear definition
- Keep old `ReportsTo` for 1-2 versions for backward compatibility
- Eventually remove in v3.0.0

**Pros:**
- Clearer signal to users that semantics changed
- Old field remains for backward compatibility period
- Users can migrate gradually

**Cons:**
- Extra field in dataset (3 reporting-related fields instead of 2)
- More complex migration path
- Dataset bloat during transition period

#### Option 3: KEEP AS-IS (Not Recommended)
**What happens:**
- Leave `ReportsTo` with ambiguous definition
- Add new `org_chart_oversight` field
- Accept that `ReportsTo` conflates multiple concepts

**Pros:**
- No breaking change

**Cons:**
- Perpetuates confusion
- Less useful for analysis
- Doesn't solve the original problem

**Questions for Team:**
- [ ] Which option do you prefer? (1, 2, or 3)
- [ ] Are you comfortable with a breaking change (v2.0.0)?
- [ ] What's the user base impact? (How many people use ReportsTo field?)
- [ ] Do we have capacity to support migration documentation?
- [ ] Timeline concerns with either approach?

**Current Implementation:** Option 1 (Redefine) is implemented in code. Can change if team prefers Option 2 or 3.

---

## 📊 TECHNICAL REVIEW

### C) Validate Data Quality Targets
**Current Targets:**
- `authorizing_authority`: **100%** (all 433 entities)
- `authorizing_url`: **90%+** (400+ entities)
- `org_chart_oversight`: **80%+** (350+ entities)
- `appointments_summary`: MOA entities only (~200-250 estimated)

**Questions:**
- [ ] Are these targets achievable with available resources?
- [ ] Should any targets be adjusted up/down?
- [ ] What's the tolerance for missing data at launch?
- [ ] Do we need a phased rollout (e.g., pilot with 50 entities first)?

---

### D) Resource and Timeline Assessment

**Estimated Remaining Work for v2.0.0:**
- Phase II.2 (MOA Data Collection): 2-3 weeks
- Phase II.3 (Crosswalk Expansion): 1-2 weeks
- Phase II.4 (Data Population): 2-3 weeks
- Phase II.5 (QA & Release): 1 week

**Total:** 7-9 weeks

**Questions:**
- [ ] Does this timeline align with organizational priorities?
- [ ] Who will be responsible for each research phase?
- [ ] Do we have legal/charter expertise available for authorizing_authority research?
- [ ] Budget/resources available for web scraping and data validation?

---

### E) Research Methodology & Sources

**Planned Approaches:**
1. **authorizing_authority**: Manual research of NYC Charter, Admin Code, Local Laws
2. **authorizing_url**: Finding and validating official source documents
3. **org_chart_oversight**: Extracting from published Mayor's org charts
4. **appointments_summary**: Scraping NYC.gov appointments page + Charter research

**Questions:**
- [ ] Are these research methods acceptable?
- [ ] Any preferred sources or restrictions on sources?
- [ ] Legal review needed for authorizing_authority citations?
- [ ] Approval needed for web scraping NYC.gov?

---

### F) Breaking Changes & User Communication

**v1.0.0 → v2.0.0 Breaking Changes:**
1. `ReportsTo` field semantics changed (if we proceed with Option 1)
2. Schema expanded (38 → 42 fields)

**Planned Communication:**
- Migration guide in `docs/PHASE_II_SCHEMA.md` ✅
- Release notes documenting all changes
- GitHub release with breaking change warnings
- NYC Open Data dataset update with change notes

**Questions:**
- [ ] Who are the primary users of v1.0.0?
- [ ] How should we notify them of breaking changes?
- [ ] Support window for v1.0.0 after v2.0.0 release?
- [ ] Any other stakeholders who need advance notice?

---

### G) Dataset Publishing Strategy

**Options:**
1. **In-place update** (replace v1.0.0 on NYC Open Data with v2.0.0)
2. **New dataset** (publish v2.0.0 as separate dataset, keep v1.0.0 available)
3. **Staged rollout** (beta release to select users first)

**Questions:**
- [ ] Which publishing approach?
- [ ] NYC Open Data team consulted about breaking change?
- [ ] Archive v1.0.0 or keep available indefinitely?
- [ ] Version numbering strategy going forward?

---

## 📝 LOWER PRIORITY ITEMS

### H) Field Naming Conventions
**Current:** Phase II fields use `snake_case` in exports (org_chart_oversight)
**v1.0.0:** Used `PascalCase` for internal schema, converted to snake_case in public exports

**Questions:**
- [ ] Happy with current naming?
- [ ] Any preference for internal representation?

### I) Validation Rules Review
Validation rules added for:
- URL format validation
- RecordID reference validation
- Completeness checks

**Questions:**
- [ ] Review validation rules in `src/nycgo_pipeline/global_rules.py`?
- [ ] Any additional validation needed?

### J) Documentation Completeness
Created:
- `docs/PHASE_II_SCHEMA.md` (410 lines) - Comprehensive field definitions
- `docs/PHASE_II_PROGRESS.md` - Progress tracking
- `PHASE_II_STATUS.md` - Quick reference

**Questions:**
- [ ] Documentation sufficient?
- [ ] Any gaps in documentation?
- [ ] User-facing docs needed beyond what's written?

---

## ✅ ACTION ITEMS SUMMARY

**MUST DECIDE BEFORE PROCEEDING:**
- [ ] **A) Approve new field definitions** (or request changes)
- [ ] **B) Choose ReportsTo strategy** (Redefine vs. Deprecate vs. Keep)

**SHOULD REVIEW:**
- [ ] **C) Validate data quality targets** (100%, 90%, 80%)
- [ ] **D) Confirm timeline and resources** (7-9 weeks)
- [ ] **E) Approve research methodology**
- [ ] **F) Plan user communication strategy**
- [ ] **G) Decide dataset publishing approach**

**OPTIONAL:**
- [ ] H) Review field naming conventions
- [ ] I) Review validation rules
- [ ] J) Review documentation completeness

---

## 📎 Reference Documents

- **Full Schema Documentation:** `docs/PHASE_II_SCHEMA.md`
- **Progress Tracking:** `docs/PHASE_II_PROGRESS.md`
- **Quick Reference:** `PHASE_II_STATUS.md`
- **Project Plan:** `PHASE_II_PLAN.md`

---

**Next Steps After Team Review:**
1. Discuss items A & B with team (critical decisions)
2. Get approval or feedback on items C-G
3. Document decisions in this file
4. Proceed with Phase II.2 (data collection) based on approved approach

---

**Review By:** _[Team Member Names]_
**Review Date:** _[Date]_
**Decisions Made:** _[To be filled in after review]_
