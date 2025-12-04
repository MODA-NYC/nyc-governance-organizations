#!/usr/bin/env python3
"""
Validate MOA crosswalk mappings against Phase 2 edits.

This script reconciles the MOA-to-NYCGO crosswalk file with Phase 2 edits
to identify discrepancies that need correction before adding Name - MOA field.

Validation checks:
1. NEW entity conflicts: MOA entities where phase2 adds as NEW but crosswalk maps to existing
2. Mapping corrections: Where phase2 edits an entity that crosswalk maps differently
3. Unmapped MOA entities: MOA entities with no crosswalk mapping (confidence: none)
4. Duplicate MOA mappings: Multiple MOA entries mapping to same NYCGO record_id

Output: CSV report with discrepancies and recommended corrections.
"""

import csv
import re
from pathlib import Path
from collections import defaultdict


def convert_record_id(old_format: str) -> str:
    """Convert NYC_GOID_XXXXXX format to numeric format (100XXX)."""
    if not old_format:
        return ""
    match = re.match(r'NYC_GOID_(\d+)', old_format)
    if match:
        numeric = int(match.group(1))
        return f"100{numeric:03d}" if numeric < 1000 else str(100000 + numeric)
    return old_format


def load_crosswalk(crosswalk_path: Path) -> dict:
    """Load MOA crosswalk and return dict keyed by moa_entity_name."""
    crosswalk = {}
    with open(crosswalk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            moa_name = row.get('moa_entity_name', '').strip()
            if moa_name:
                crosswalk[moa_name] = {
                    'moa_entity_name': moa_name,
                    'moa_url': row.get('moa_url', ''),
                    'moa_description': row.get('moa_description', ''),
                    'nycgo_record_id': row.get('nycgo_record_id', ''),
                    'nycgo_name': row.get('nycgo_name', ''),
                    'similarity_score': row.get('similarity_score', ''),
                    'match_confidence': row.get('match_confidence', ''),
                    'needs_manual_review': row.get('needs_manual_review', ''),
                    'notes': row.get('notes', ''),
                }
    return crosswalk


def load_phase2_edits(edits_path: Path) -> tuple:
    """
    Load Phase 2 edits and return:
    - new_entities: set of entity names being added as NEW
    - edited_entities: dict of record_id -> list of edits for existing entities
    """
    new_entities = set()
    edited_entities = defaultdict(list)

    with open(edits_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_id = row.get('record_id', '').strip()
            record_name = row.get('record_name', '').strip()
            field_name = row.get('field_name', '').strip()
            action = row.get('action', '').strip()
            justification = row.get('justification', '').strip()

            if record_id == 'NEW':
                new_entities.add(record_name)
            else:
                edited_entities[record_id].append({
                    'record_name': record_name,
                    'field_name': field_name,
                    'action': action,
                    'justification': justification,
                })

    return new_entities, edited_entities


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


def validate_crosswalk(crosswalk: dict, new_entities: set, edited_entities: dict, golden: dict) -> list:
    """
    Validate crosswalk against phase2 edits and return list of discrepancies.
    """
    discrepancies = []

    # Track which record_ids have MOA mappings (for duplicate check)
    record_id_to_moa = defaultdict(list)

    for moa_name, mapping in crosswalk.items():
        crosswalk_record_id = mapping['nycgo_record_id']
        crosswalk_nycgo_name = mapping['nycgo_name']
        confidence = mapping['match_confidence']

        # Track for duplicate detection
        if crosswalk_record_id:
            record_id_to_moa[crosswalk_record_id].append(moa_name)

        # Check 1: NEW entity conflicts
        # MOA name matches a NEW entity being added, but crosswalk maps to something else
        for new_name in new_entities:
            # Check if MOA name is similar to new entity name
            if (moa_name.lower() in new_name.lower() or
                new_name.lower() in moa_name.lower() or
                _fuzzy_match(moa_name, new_name)):

                if crosswalk_record_id:
                    discrepancies.append({
                        'moa_entity_name': moa_name,
                        'crosswalk_record_id': crosswalk_record_id,
                        'crosswalk_nycgo_name': crosswalk_nycgo_name,
                        'crosswalk_confidence': confidence,
                        'phase2_action': f'NEW entity: {new_name}',
                        'conflict_type': 'NEW_ENTITY_CONFLICT',
                        'recommended_correction': f'Update crosswalk: map to NEW entity or clear mapping',
                    })

        # Check 2: Unmapped MOA entities (confidence: none or empty record_id)
        if not crosswalk_record_id or confidence == 'none':
            discrepancies.append({
                'moa_entity_name': moa_name,
                'crosswalk_record_id': crosswalk_record_id or '(empty)',
                'crosswalk_nycgo_name': crosswalk_nycgo_name or '(empty)',
                'crosswalk_confidence': confidence or '(empty)',
                'phase2_action': '(no mapping)',
                'conflict_type': 'UNMAPPED',
                'recommended_correction': 'Verify if MOA entity should map to existing NYCGO entity or be added as NEW',
            })

        # Check 3: Low confidence mappings that may need review
        if confidence == 'low' and crosswalk_record_id:
            # Check if this entity is being edited in phase2
            numeric_id = convert_record_id(crosswalk_record_id)
            if numeric_id in edited_entities:
                edits = edited_entities[numeric_id]
                edit_summary = '; '.join([f"{e['field_name']}" for e in edits[:3]])
                discrepancies.append({
                    'moa_entity_name': moa_name,
                    'crosswalk_record_id': crosswalk_record_id,
                    'crosswalk_nycgo_name': crosswalk_nycgo_name,
                    'crosswalk_confidence': confidence,
                    'phase2_action': f'Edits: {edit_summary}...',
                    'conflict_type': 'LOW_CONFIDENCE_WITH_EDITS',
                    'recommended_correction': 'Verify mapping is correct given phase2 edits',
                })

    # Check 4: Duplicate MOA mappings (multiple MOA entities -> same NYCGO record)
    for record_id, moa_names in record_id_to_moa.items():
        if len(moa_names) > 1:
            nycgo_name = golden.get(record_id, golden.get(convert_record_id(record_id), '(unknown)'))
            for moa_name in moa_names:
                discrepancies.append({
                    'moa_entity_name': moa_name,
                    'crosswalk_record_id': record_id,
                    'crosswalk_nycgo_name': nycgo_name,
                    'crosswalk_confidence': crosswalk[moa_name]['match_confidence'],
                    'phase2_action': f'Also maps: {[n for n in moa_names if n != moa_name]}',
                    'conflict_type': 'DUPLICATE_MAPPING',
                    'recommended_correction': 'Review if both MOA entities should map to same NYCGO entity',
                })

    return discrepancies


def _fuzzy_match(s1: str, s2: str) -> bool:
    """Simple fuzzy match - check if strings share significant common words."""
    words1 = set(s1.lower().replace('-', ' ').replace(',', ' ').split())
    words2 = set(s2.lower().replace('-', ' ').replace(',', ' ').split())
    # Remove common stop words
    stop_words = {'the', 'of', 'and', 'a', 'an', 'for', 'to', 'in', 'on', 'at', 'by', 'nyc', 'new', 'york', 'city', 'board', 'commission', 'committee', 'department', 'office'}
    words1 = words1 - stop_words
    words2 = words2 - stop_words
    # Check overlap
    if not words1 or not words2:
        return False
    overlap = words1 & words2
    return len(overlap) >= 2 or (len(overlap) >= 1 and len(words1) <= 2)


def write_report(discrepancies: list, output_path: Path):
    """Write discrepancy report to CSV."""
    fieldnames = [
        'moa_entity_name',
        'crosswalk_record_id',
        'crosswalk_nycgo_name',
        'crosswalk_confidence',
        'phase2_action',
        'conflict_type',
        'recommended_correction',
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(discrepancies, key=lambda x: (x['conflict_type'], x['moa_entity_name'])):
            writer.writerow(row)

    print(f"Wrote {len(discrepancies)} discrepancies to {output_path}")


def print_summary(discrepancies: list):
    """Print summary of discrepancies by type."""
    by_type = defaultdict(list)
    for d in discrepancies:
        by_type[d['conflict_type']].append(d)

    print("\n=== MOA Crosswalk Validation Summary ===\n")

    for conflict_type in ['NEW_ENTITY_CONFLICT', 'UNMAPPED', 'LOW_CONFIDENCE_WITH_EDITS', 'DUPLICATE_MAPPING']:
        items = by_type.get(conflict_type, [])
        print(f"{conflict_type}: {len(items)} issues")
        if items and len(items) <= 10:
            for item in items:
                print(f"  - {item['moa_entity_name']} -> {item['crosswalk_nycgo_name'] or '(unmapped)'}")
        elif items:
            for item in items[:5]:
                print(f"  - {item['moa_entity_name']} -> {item['crosswalk_nycgo_name'] or '(unmapped)'}")
            print(f"  ... and {len(items) - 5} more")
        print()

    print(f"Total discrepancies: {len(discrepancies)}")


def main():
    # Paths
    base_path = Path(__file__).parent.parent.parent
    crosswalk_path = base_path / 'data' / 'crosswalk' / 'moa_to_nycgo_mapping.csv'
    edits_path = base_path / 'data' / 'input' / 'NYCGO_phase2_edits_to_make_20251118.csv'
    golden_path = base_path / 'data' / 'published' / 'latest' / 'NYCGO_golden_dataset_v1.1.1.csv'
    output_path = base_path / 'data' / 'analysis' / 'moa_crosswalk_validation.csv'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading crosswalk...")
    crosswalk = load_crosswalk(crosswalk_path)
    print(f"  Loaded {len(crosswalk)} MOA entities")

    print("Loading phase2 edits...")
    new_entities, edited_entities = load_phase2_edits(edits_path)
    print(f"  Found {len(new_entities)} NEW entities")
    print(f"  Found {len(edited_entities)} edited entities")

    print("Loading golden dataset...")
    golden = load_golden_dataset(golden_path)
    print(f"  Loaded {len(golden)//2} entities")

    print("\nValidating crosswalk...")
    discrepancies = validate_crosswalk(crosswalk, new_entities, edited_entities, golden)

    print_summary(discrepancies)
    write_report(discrepancies, output_path)

    return discrepancies


if __name__ == '__main__':
    main()
