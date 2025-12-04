# Slack Message: RecordID Format Change Proposal

---

Hi team! 👋

Proposing a RecordID format change for Phase II:

**Current:** `NYC_GOID_000318` (uppercase, underscores, leading zeros)
**Proposed:** `100318` (6-digit numeric, no prefix)

**Why change now:**
- ✅ Dataset is still new (~433 entities) - minimal adoption risk
- ✅ Already doing major schema change (Phase II) - perfect timing
- ✅ Avoids zip code conflicts (6 digits vs 5-digit zip codes)
- ✅ Easier joins/queries (simpler format, no case sensitivity)
- ✅ Future-proof capacity (~1M IDs)

**Migration:** Crosswalk file provided (old → new ID mapping)

**Examples:**
- `NYC_GOID_000022` → `100022`
- `NYC_GOID_000318` → `100318`
- `NYC_GOID_100026` → `110026`

Open to feedback!
