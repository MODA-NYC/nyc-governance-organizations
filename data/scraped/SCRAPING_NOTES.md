# NYC.gov Appointments Page Scraping Notes

**Date:** November 14, 2024
**URL:** https://www.nyc.gov/content/appointments/pages/boards-commissions

---

## Finding: JavaScript-Rendered Content

The appointments page content is **dynamically loaded via JavaScript**, not present in the initial HTML.

### Evidence:
- Static HTML fetch: 396 lines, but **0 mentions** of "board" or "commission"
- Page uses multiple JavaScript frameworks and tracking scripts
- Content appears empty when scraped with basic requests/BeautifulSoup

### Impact:
**Standard web scraping (requests + BeautifulSoup) will NOT work** for this page.

---

## Solutions

### Option 1: Use Playwright MCP ⭐ RECOMMENDED
We have Playwright MCP configured specifically for this scenario.

**Approach:**
- Use Playwright to load page and wait for JavaScript execution
- Extract rendered content after page fully loads
- Playwright handles dynamic content automatically

**Configuration:** Already set up in `configs/mcp-development.json`

### Option 2: Find API Endpoint
Many NYC.gov pages have underlying API endpoints that return JSON data.

**Next Steps:**
1. Inspect browser Network tab while loading the page
2. Look for API calls to `/api/` or similar endpoints
3. If found, we can query the API directly (simpler than browser automation)

### Option 3: Manual Data Entry
If automated scraping proves too complex, could manually transcribe the data.

**Not recommended:** ~200-300 entities would be time-consuming

---

## Recommended Next Steps

1. **Inspect the page in a browser:**
   - Open https://www.nyc.gov/content/appointments/pages/boards-commissions
   - Open Developer Tools → Network tab
   - Look for API calls loading the boards/commissions data
   - Document the API endpoint if found

2. **If API endpoint exists:**
   - Update scraping script to query API directly
   - Much simpler than browser automation

3. **If no API (use Playwright):**
   - Create Playwright-based scraping script
   - Use Playwright MCP server
   - Wait for page load, extract rendered content

---

## Page Structure (Confirmed)

After browser inspection, the page uses **accordion card structure**:

```html
<div class="card">
  <a class="card-header h4 collapse" id="acc-button-04">
    <span class="title">Banking Commission - Department of Finance</span>
  </a>
  <div class="collapse show" id="panel-acc-button-04">
    <div class="card-body">
      <p>Description text... <a href="...">Visit the site</a></p>
    </div>
  </div>
</div>
```

### Selectors:
- **Container:** `div.card`
- **Entity Name:** `span.title` (within card-header)
- **Description:** `div.card-body > p` (text content)
- **URL:** `div.card-body > p > a[href]`

### Findings:
- ✅ No API endpoint found - content is rendered via JavaScript
- ✅ Accordion/card structure confirmed
- ❌ Content not available in static HTML (requires JavaScript rendering)

---

## Solution: Manual HTML Save + Parse

Due to browser automation permission issues on macOS, using a **hybrid approach**:

### Recommended Process:
1. **Manual HTML save:**
   - Visit https://www.nyc.gov/content/appointments/pages/boards-commissions
   - Wait for all accordion content to load
   - Right-click → "Save Page As..." → Complete HTML
   - Save to: `data/scraped/appointments_page.html`

2. **Automated parsing:**
   - Run: `python scripts/data_collection/scrape_moa_appointments_from_html.py`
   - Script parses saved HTML using BeautifulSoup
   - Extracts all entities to CSV

### Why This Approach:
- ✅ Avoids browser automation permission issues (Playwright, pyppeteer)
- ✅ Works reliably across different environments
- ✅ User can verify page loaded completely before saving
- ✅ Fast parsing once HTML is saved
- ⚠️ Requires one-time manual step (30 seconds)

---

## Files

### Working Scripts:
- **HTML Parser (recommended):** `scripts/data_collection/scrape_moa_appointments_from_html.py`
- **Static scraper (updated with selectors):** `scripts/data_collection/scrape_moa_appointments.py`
- **Playwright scraper (has permission issues):** `scripts/data_collection/scrape_moa_appointments_playwright.py`

### Support Files:
- **Page inspection helper:** `scripts/data_collection/inspect_page_structure.py`

---

## Troubleshooting Notes

### Playwright Issues:
- **Error:** `TargetClosedError: BrowserType.launch` with EPERM kill error
- **Cause:** macOS security restrictions preventing automated browser launch
- **Attempted fixes:**
  - Headless mode (failed - same error)
  - requests-html library (dependency conflicts with pyee)
- **Status:** Browser automation not reliable in this environment

### Dependency Conflicts:
- playwright 1.55.0 requires pyee>=13
- requests-html (pyppeteer) requires pyee>=11,<12
- Cannot install both simultaneously

---

**Status:** HTML parser script ready. User needs to save rendered page, then run parser.
