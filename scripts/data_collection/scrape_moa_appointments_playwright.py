#!/usr/bin/env python3
"""
Scrape NYC.gov Mayor's Office of Appointments - Boards & Commissions Page
Using Playwright for JavaScript rendering

Extracts:
- Entity name
- Description
- URL

Output: CSV file with scraped data

Usage:
    python scripts/data_collection/scrape_moa_appointments_playwright.py

Requirements:
    - playwright
    - pandas
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

# Configuration
MOA_URL = "https://www.nyc.gov/content/appointments/pages/boards-commissions"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "scraped"
OUTPUT_FILE = OUTPUT_DIR / "moa_appointments_raw.csv"
PAGE_LOAD_TIMEOUT = 30000  # 30 seconds


def scrape_appointments_page_playwright(url: str) -> list[dict]:  # noqa: C901
    """
    Scrape the NYC.gov appointments page using Playwright.

    Args:
        url: URL of the appointments page

    Returns:
        List of dictionaries with entity data
    """
    print("🌐 Launching browser...")

    entities = []

    with sync_playwright() as p:
        # Launch browser (headless mode)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="NYC-Governance-Research/2.0 (Phase II Data Collection)"
        )
        page = context.new_page()

        try:
            print(f"📄 Navigating to: {url}")
            page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until="networkidle")
            print("✅ Page loaded successfully")

            # Wait for cards to be rendered
            print("⏳ Waiting for content to render...")
            try:
                page.wait_for_selector("div.card", timeout=10000)
                print("✅ Content rendered")
            except PlaywrightTimeout:
                print("⚠️  Warning: Card elements not found within timeout")
                print("   Page may have different structure or")
                print("   content may not have loaded")

            # Get all card elements
            cards = page.query_selector_all("div.card")
            print(f"🔍 Found {len(cards)} card elements")

            for idx, card in enumerate(cards, 1):
                name = None
                description = None
                url = None

                # Extract entity name from <span class="title">
                title_elem = card.query_selector("span.title")
                if title_elem:
                    name = title_elem.inner_text().strip()

                # Extract description and URL from card-body
                card_body = card.query_selector("div.card-body")
                if card_body:
                    # Get paragraph element
                    paragraph = card_body.query_selector("p")
                    if paragraph:
                        # Extract full paragraph text
                        description = paragraph.inner_text().strip()

                        # Extract URL from link within paragraph
                        link_elem = paragraph.query_selector("a[href]")
                        if link_elem:
                            url = link_elem.get_attribute("href")

                            # Convert relative URLs to absolute
                            if url and not url.startswith("http"):
                                url = (
                                    f"https://www.nyc.gov{url}"
                                    if url.startswith("/")
                                    else url
                                )

                            # Remove link text from description
                            link_text = link_elem.inner_text().strip()
                            if link_text and link_text in description:
                                description = description.replace(link_text, "").strip()
                                # Clean up extra whitespace
                                description = " ".join(description.split())

                # Only add if we found at least a name
                if name:
                    entities.append(
                        {
                            "entity_name": name,
                            "description": description or "",
                            "url": url or "",
                            "scraped_date": datetime.now().isoformat(),
                            "source_url": MOA_URL,
                        }
                    )

                    # Progress indicator
                    if idx % 10 == 0:
                        print(f"   Processed {idx}/{len(cards)} cards...")

        except PlaywrightTimeout as e:
            print(f"❌ Error: Page load timeout - {e}")
            browser.close()
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            browser.close()
            sys.exit(1)
        finally:
            browser.close()

    print(f"\n✅ Extracted {len(entities)} entities")
    return entities


def save_to_csv(entities: list[dict], output_file: Path):
    """Save entities to CSV file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not entities:
        print("⚠️  No entities to save!")
        return

    df = pd.DataFrame(entities)

    # Reorder columns
    column_order = ["entity_name", "description", "url", "scraped_date", "source_url"]
    df = df[column_order]

    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\n✅ Saved {len(entities)} entities to: {output_file}")
    print(f"   File size: {output_file.stat().st_size:,} bytes")


def print_summary(entities: list[dict]):
    """Print summary statistics."""
    if not entities:
        return

    print("\n" + "=" * 60)
    print("  Scraping Summary")
    print("=" * 60)
    print(f"Total entities: {len(entities)}")

    # Count entities with each field
    with_name = sum(1 for e in entities if e.get("entity_name"))
    with_desc = sum(1 for e in entities if e.get("description"))
    with_url = sum(1 for e in entities if e.get("url"))

    print(f"  - With name: {with_name} ({with_name/len(entities)*100:.1f}%)")
    print(f"  - With description: {with_desc} ({with_desc/len(entities)*100:.1f}%)")
    print(f"  - With URL: {with_url} ({with_url/len(entities)*100:.1f}%)")

    print("\nFirst 5 entities:")
    for i, entity in enumerate(entities[:5], 1):
        print(f"\n{i}. {entity['entity_name']}")
        if entity.get("description"):
            desc_preview = entity["description"][:100]
            desc_preview += "..." if len(entity["description"]) > 100 else ""
            print(f"   Description: {desc_preview}")
        if entity.get("url"):
            print(f"   URL: {entity['url']}")

    print("=" * 60)


def main():
    """Main execution function."""
    print("=" * 60)
    print("  NYC.gov Appointments Page Scraper (Playwright)")
    print("  Phase II.2 Data Collection")
    print("=" * 60)
    print(f"\nTarget URL: {MOA_URL}")
    print(f"Output file: {OUTPUT_FILE}\n")

    # Check if playwright is installed
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        print("❌ Error: Playwright not installed")
        print("   Install with: pip install playwright")
        print("   Then run: playwright install chromium")
        return 1

    # Scrape the page
    entities = scrape_appointments_page_playwright(MOA_URL)

    # Save to CSV
    save_to_csv(entities, OUTPUT_FILE)

    # Print summary
    print_summary(entities)

    if entities:
        print("\n📝 NEXT STEPS:")
        print("1. Review the output CSV to verify data quality")
        print(
            "2. Run crosswalk creation: scripts/data_collection/create_moa_crosswalk.py"
        )
        print("3. Run gap analysis: scripts/analysis/analyze_moa_coverage.py")
    else:
        print("\n⚠️  WARNING: No entities extracted!")
        print("   Check the page structure or selectors may need adjustment")

    return 0


if __name__ == "__main__":
    sys.exit(main())
