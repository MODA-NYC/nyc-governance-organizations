#!/usr/bin/env python3
"""
Generate Name - MOA edits for all mapped MOA entities.

Reads the MOA crosswalk and generates phase2 edit rows to set the
Name - MOA field for each entity with a valid nycgo_record_id.
"""

import csv
import re
from pathlib import Path


def convert_record_id(old_format: str) -> str:
    """Convert NYC_GOID_XXXXXX format to numeric format.

    NYC_GOID_000XXX -> 100XXX (add 100000)
    NYC_GOID_100XXX -> 100XXX (already in new format, just strip prefix)
    """
    if not old_format:
        return ""
    match = re.match(r'NYC_GOID_(\d+)', old_format)
    if match:
        numeric = int(match.group(1))
        # If it's already a 6-digit ID starting with 1, keep it as is
        if numeric >= 100000:
            return str(numeric)
        # Otherwise add 100000 to convert old format
        return str(100000 + numeric)
    return old_format


def load_golden_dataset(golden_path: Path) -> dict:
    """Load golden dataset and return dict of record_id -> name."""
    golden = {}
    with open(golden_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_id = row.get('RecordID', '').strip()
            name = row.get('Name', '').strip()
            if record_id:
                # Store both old and new format
                golden[record_id] = name
                numeric_id = convert_record_id(record_id)
                if numeric_id != record_id:
                    golden[numeric_id] = name
    return golden


def load_crosswalk(crosswalk_path: Path) -> list:
    """Load MOA crosswalk and return list of mappings with valid record_ids."""
    mappings = []
    with open(crosswalk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            moa_name = row.get('moa_entity_name', '').strip()
            nycgo_record_id = row.get('nycgo_record_id', '').strip()
            confidence = row.get('match_confidence', '').strip()

            # Only include entities with valid mappings (not none/empty)
            if moa_name and nycgo_record_id and confidence != 'none':
                mappings.append({
                    'moa_entity_name': moa_name,
                    'nycgo_record_id': nycgo_record_id,
                    'nycgo_name': row.get('nycgo_name', '').strip(),
                    'match_confidence': confidence,
                })
    return mappings


def generate_edits(mappings: list, golden: dict, use_original_record_id: bool = True) -> list:
    """Generate Name - MOA edit rows for each mapping.

    Handles duplicate MOA mappings to same entity by combining names with semicolons.

    Args:
        mappings: List of MOA-to-NYCGO mappings from crosswalk
        golden: Dict mapping record_id -> entity name
        use_original_record_id: If True, use NYC_GOID_XXXXXX format; if False, use numeric format
    """
    # First, group MOA names by record_id
    by_record_id = {}
    for mapping in mappings:
        old_record_id = mapping['nycgo_record_id']
        # Use original format (NYC_GOID_...) or convert to numeric
        record_id_for_edit = old_record_id if use_original_record_id else convert_record_id(old_record_id)
        moa_name = mapping['moa_entity_name']
        nycgo_name = golden.get(old_record_id) or golden.get(convert_record_id(old_record_id)) or mapping['nycgo_name']

        if record_id_for_edit not in by_record_id:
            by_record_id[record_id_for_edit] = {
                'nycgo_name': nycgo_name,
                'moa_names': [],
            }
        by_record_id[record_id_for_edit]['moa_names'].append(moa_name)

    # Generate one edit per record_id, combining MOA names if multiple
    edits = []
    for record_id, data in by_record_id.items():
        moa_names = data['moa_names']
        # Combine multiple MOA names with semicolons
        combined_moa_name = '; '.join(sorted(set(moa_names)))

        edit = {
            'record_id': record_id,
            'record_name': data['nycgo_name'],
            'field_name': 'Name - MOA',
            'action': f'Set to "{combined_moa_name}"',
            'justification': 'MOA crosswalk mapping - exact name from MOA appointments page',
            'evidence_url': 'https://www.nyc.gov/content/appointments/pages/boards-commissions',
        }
        edits.append(edit)

    return edits


def write_edits(edits: list, output_path: Path):
    """Write edits to CSV file."""
    fieldnames = ['record_id', 'record_name', 'field_name', 'action', 'justification', 'evidence_url']

    def sort_key(x):
        """Sort by record_id, handling both NYC_GOID and numeric formats."""
        rid = x['record_id']
        if rid.startswith('NYC_GOID_'):
            return int(rid.replace('NYC_GOID_', ''))
        elif rid == 'NEW':
            return 999999  # NEW records at end
        return int(rid)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for edit in sorted(edits, key=sort_key):
            writer.writerow(edit)

    print(f"Wrote {len(edits)} Name - MOA edits to {output_path}")


def main():
    # Paths
    base_path = Path(__file__).parent.parent.parent
    crosswalk_path = base_path / 'data' / 'crosswalk' / 'moa_to_nycgo_mapping.csv'
    golden_path = base_path / 'data' / 'published' / 'latest' / 'NYCGO_golden_dataset_v1.1.1.csv'
    output_path = base_path / 'data' / 'input' / 'NYCGO_name_moa_edits.csv'

    print("Loading golden dataset...")
    golden = load_golden_dataset(golden_path)
    print(f"  Loaded {len(golden)//2} entities")

    print("Loading crosswalk...")
    mappings = load_crosswalk(crosswalk_path)
    print(f"  Found {len(mappings)} MOA entities with valid mappings")

    print("Generating Name - MOA edits...")
    edits = generate_edits(mappings, golden)

    write_edits(edits, output_path)

    # Print summary
    print("\n=== Summary ===")
    print(f"Total Name - MOA edits: {len(edits)}")

    return edits


if __name__ == '__main__':
    main()
