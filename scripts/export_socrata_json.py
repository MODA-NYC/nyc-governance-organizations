#!/usr/bin/env python3
"""
Export NYC Governance Organizations data to Socrata-compatible JSON format.

Converts the public export CSV to the same JSON format returned by the
NYC Open Data API (https://data.cityofnewyork.us/resource/t3jq-9nkf.json).

Key transformations:
- URL fields become nested objects: {"url": "https://..."}
- Boolean strings ("True"/"False") become actual booleans (true/false)
- Field names are adjusted to match Socrata conventions
- Empty/null fields are omitted from the JSON output

Usage:
    python scripts/export_socrata_json.py \
        --input data/published/latest/NYCGovernanceOrganizations_latest.csv \
        --output data/published/latest/NYCGovernanceOrganizations_latest.json

The output can be served as a static file to replace the Open Data API endpoint.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def convert_to_socrata_format(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to Socrata-compatible JSON format.

    Transformations:
    - url -> {"url": "..."} (nested object)
    - principal_officer_contact_url -> principal_officer_contact: {"url": "..."}
    - listed_in_nyc_gov_agency_directory -> listed_in_nyc_gov_agency (truncated name)
    - Boolean strings -> actual booleans
    - Empty fields are omitted
    """
    records = []

    for _, row in df.iterrows():
        record = {}

        # Process each field with appropriate transformations
        for col in df.columns:
            value = row[col]

            # Skip empty/null values
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                continue

            # URL field transformations (nested objects)
            if col == "url":
                record["url"] = {"url": value}

            elif col == "principal_officer_contact_url":
                # Rename to match Socrata convention (strips _url suffix)
                record["principal_officer_contact"] = {"url": value}

            # Boolean field transformations
            elif col in ("in_org_chart", "listed_in_nyc_gov_agency_directory"):
                # Convert string to boolean
                bool_value = str(value).strip().lower() == "true"

                # Rename listed_in_nyc_gov_agency_directory to truncated version
                if col == "listed_in_nyc_gov_agency_directory":
                    record["listed_in_nyc_gov_agency"] = bool_value
                else:
                    record[col] = bool_value

            else:
                # All other fields pass through as strings
                record[col] = value

        records.append(record)

    return records


def main():
    parser = argparse.ArgumentParser(
        description="Convert NYC GO public CSV to Socrata-compatible JSON"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input CSV file (NYCGovernanceOrganizations_*.csv)",
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Path to output JSON file"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )
    parser.add_argument(
        "--compact", action="store_true", help="Output compact JSON (no indentation)"
    )

    args = parser.parse_args()

    # Verify input exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Load CSV
    print(f"Loading: {args.input}")
    try:
        df = pd.read_csv(args.input, dtype=str, encoding="utf-8-sig")
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Records: {len(df)}")
    print(f"  Columns: {len(df.columns)}")

    # Convert to Socrata format
    print("Converting to Socrata JSON format...")
    records = convert_to_socrata_format(df)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    indent = None if args.compact else 2
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=indent, ensure_ascii=False)

    print(f"Written: {args.output}")
    print(f"  Records: {len(records)}")
    print(f"  Size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
