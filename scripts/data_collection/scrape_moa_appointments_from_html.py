#!/usr/bin/env python3
"""
Parse NYC.gov Mayor's Office of Appointments page from saved HTML file.

This script parses a manually saved HTML file (after JavaScript rendering)
to extract board and commission data.

Extracts:
- Entity name
- Description
- URL

Output: CSV file with scraped data

Usage:
    # First, manually save the rendered page:
    # 1. Visit https://www.nyc.gov/content/appointments/pages/boards-commissions
    # 2. Wait for all content to load
    # 3. Right-click -> "Save Page As..." -> Save as "appointments_page.html"
    # 4. Move the file to data/scraped/appointments_page.html

    python scripts/data_collection/scrape_moa_appointments_from_html.py

Requirements:
    - beautifulsoup4
    - pandas
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# Configuration
INPUT_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "input"
    / "Boards & Commissions - NYC Mayor's Office of Appointments.html"
)
OUTPUT_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "scraped"
    / "moa_appointments_raw.csv"
)
MOA_URL = "https://www.nyc.gov/content/appointments/pages/boards-commissions"


def parse_html_file(html_file: Path) -> list[dict]:  # noqa: C901
    """
    Parse the saved HTML file to extract entity data.

    Args:
        html_file: Path to saved HTML file

    Returns:
        List of dictionaries with entity data
    """
    print(f"📄 Reading HTML file: {html_file}")

    if not html_file.exists():
        print(f"❌ Error: HTML file not found: {html_file}")
        print("\n📝 To create this file:")
        print(
            "   1. Visit: https://www.nyc.gov/content/appointments/pages/boards-commissions"
        )
        print("   2. Wait for all accordion content to load")
        print("   3. Right-click -> 'Save Page As...'")
        print("   4. Save as: data/scraped/appointments_page.html")
        print("   5. Run this script again")
        sys.exit(1)

    with open(html_file, encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

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

    print("🔍 Parsing accordion card structure...")

    # Find all card containers
    cards = soup.find_all("div", class_="card")

    print(f"   Found {len(cards)} card elements")

    if len(cards) == 0:
        print("\n⚠️  Warning: No cards found in HTML file")
        print("   The page may not have been fully rendered when saved")
        print("   Or the HTML structure may have changed")

        # Try to provide debugging info
        print("\n🔍 Debugging info:")
        print(f"   Total <div> elements: {len(soup.find_all('div'))}")
        card_elements = soup.find_all(class_=lambda x: x and "card" in x)
        print(f"   Elements with 'card' in class: {len(card_elements)}")

        # Look for any text mentioning boards/commissions
        body_text = soup.get_text()
        print(f"   Mentions of 'board': {body_text.lower().count('board')}")
        print(f"   Mentions of 'commission': {body_text.lower().count('commission')}")

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
    print("  NYC.gov Appointments Page Parser")
    print("  Parse from Saved HTML File")
    print("  Phase II.2 Data Collection")
    print("=" * 60)
    print(f"\nInput file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}\n")

    # Parse the HTML file
    entities = parse_html_file(INPUT_FILE)

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
        print("   The HTML file may not contain the expected structure")
        print("   Try saving the page again after all content has loaded")

    return 0 if entities else 1


if __name__ == "__main__":
    sys.exit(main())
