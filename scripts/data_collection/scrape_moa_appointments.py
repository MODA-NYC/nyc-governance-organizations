#!/usr/bin/env python3
"""
Scrape NYC.gov Mayor's Office of Appointments - Boards & Commissions Page

Extracts:
- Entity name
- Description
- URL

Output: CSV file with scraped data

Usage:
    python scripts/data_collection/scrape_moa_appointments.py

Requirements:
    - requests
    - beautifulsoup4
    - pandas
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuration
MOA_URL = "https://www.nyc.gov/content/appointments/pages/boards-commissions"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "scraped"
OUTPUT_FILE = OUTPUT_DIR / "moa_appointments_raw.csv"
USER_AGENT = (
    "NYC-Governance-Research/2.0 "
    "(Phase II Data Collection; Research Project; "
    "Contact: [contact info])"
)


def scrape_appointments_page(url: str) -> list[dict]:  # noqa: C901
    """
    Scrape the NYC.gov appointments page.

    Args:
        url: URL of the appointments page

    Returns:
        List of dictionaries with entity data
    """
    print(f"Fetching: {url}")

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        sys.exit(1)

    print(f"✅ Page fetched successfully (status: {response.status_code})")

    soup = BeautifulSoup(response.content, "html.parser")

    entities = []

    # HTML Structure: Accordion cards
    # <div class="card">
    #   <a class="card-header">
    #     <span class="title">Entity Name</span>
    #   </a>
    #   <div class="card-body">
    #     <p>Description... <a href="url">Visit the site</a></p>
    #   </div>
    # </div>

    print("\n🔍 Parsing accordion card structure...")

    # Find all card containers
    cards = soup.find_all("div", class_="card")

    print(f"   Found {len(cards)} card elements")

    for idx, card in enumerate(cards, 1):
        name = None
        description = None
        url = None

        # Extract entity name from <span class="title">
        title_elem = card.find("span", class_="title")
        if title_elem:
            name = title_elem.get_text(strip=True)

        # Extract description and URL from card-body
        card_body = card.find("div", class_="card-body")
        if card_body:
            # Get paragraph text
            paragraph = card_body.find("p")
            if paragraph:
                # Extract description (full paragraph text)
                description = paragraph.get_text(strip=True)

                # Extract URL from link within paragraph
                link_elem = paragraph.find("a", href=True)
                if link_elem:
                    url = link_elem["href"]
                    # Convert relative URLs to absolute
                    if url and not url.startswith("http"):
                        url = (
                            f"https://www.nyc.gov{url}" if url.startswith("/") else url
                        )

                    # Remove link text from description
                    link_text = link_elem.get_text(strip=True)
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
    print("  NYC.gov Appointments Page Scraper")
    print("  Phase II.2 Data Collection")
    print("=" * 60)
    print(f"\nTarget URL: {MOA_URL}")
    print(f"Output file: {OUTPUT_FILE}\n")

    # Scrape the page
    entities = scrape_appointments_page(MOA_URL)

    # Save to CSV
    save_to_csv(entities, OUTPUT_FILE)

    # Print summary
    print_summary(entities)

    print("\n⚠️  NEXT STEPS:")
    print("1. Inspect the output CSV to verify data quality")
    print("2. Update HTML selectors in this script if needed")
    print("3. Re-run scraping if extraction was incomplete")
    print("4. Proceed to crosswalk creation")

    return 0


if __name__ == "__main__":
    sys.exit(main())
