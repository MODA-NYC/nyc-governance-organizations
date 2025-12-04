#!/usr/bin/env python3
"""
Inspect HTML structure of NYC.gov appointments page to identify selectors.

Usage:
    python scripts/data_collection/inspect_page_structure.py
"""


import requests
from bs4 import BeautifulSoup

MOA_URL = "https://www.nyc.gov/content/appointments/pages/boards-commissions"


def inspect_page():
    """Fetch and analyze page structure."""
    print(f"Fetching: {MOA_URL}\n")

    headers = {"User-Agent": "NYC-Governance-Research/2.0"}
    response = requests.get(MOA_URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Save full HTML for manual inspection
    with open("/tmp/moa_page.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print("✅ Full HTML saved to: /tmp/moa_page.html")

    # Look for main content area
    print("\n🔍 Looking for main content containers...")

    main_content = (
        soup.find("main")
        or soup.find(id="main-content")
        or soup.find(class_="main-content")
    )
    if main_content:
        print("✅ Found main content area")

        # Look for lists, grids, or cards
        print("\n📋 Looking for structured content within main...")

        # Check for various common patterns
        lists = main_content.find_all(["ul", "ol"])
        print(f"   - Found {len(lists)} list(s)")

        divs_with_card = main_content.find_all(
            "div", class_=lambda x: x and "card" in x.lower()
        )
        print(f"   - Found {len(divs_with_card)} card-like div(s)")

        articles = main_content.find_all("article")
        print(f"   - Found {len(articles)} article(s)")

        # Look for headings as indicators of entities
        headings = main_content.find_all(["h1", "h2", "h3", "h4"])
        print(f"   - Found {len(headings)} heading(s)")

        if headings:
            print("\n📝 Sample headings (first 10):")
            for i, h in enumerate(headings[:10], 1):
                text = h.get_text(strip=True)
                if len(text) > 80:
                    text = text[:77] + "..."
                print(f"   {i}. {h.name}: {text}")

        # Look for accordions (common on NYC.gov)
        accordions = main_content.find_all(
            class_=lambda x: x and "accordion" in x.lower()
        )
        print(f"\n🎯 Found {len(accordions)} accordion-like element(s)")

        # Look for tables
        tables = main_content.find_all("table")
        print(f"   Found {len(tables)} table(s)")

    else:
        print("⚠️  Could not find main content area")
        print("   Searching entire page for structured content...")

        all_headings = soup.find_all(["h2", "h3"])
        print(f"\n   Found {len(all_headings)} h2/h3 headings in entire page")
        if all_headings:
            print("\n   First 15 headings:")
            for i, h in enumerate(all_headings[:15], 1):
                print(f"   {i}. {h.get_text(strip=True)}")

    print("\n💡 NEXT STEPS:")
    print("1. Open /tmp/moa_page.html in a browser")
    print("2. Inspect the HTML to find the actual data structure")
    print("3. Identify the CSS selectors or element patterns")
    print("4. Update scrape_moa_appointments.py with correct selectors")


if __name__ == "__main__":
    inspect_page()
