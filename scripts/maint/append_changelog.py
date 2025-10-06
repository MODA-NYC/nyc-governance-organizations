#!/usr/bin/env python3
import argparse
import csv
import json
import pathlib
import sys

SYNCED_RECORD_NAMES: dict[str, str] = {}


def read_existing_event_ids(changelog_path: pathlib.Path):
    if not changelog_path.exists() or changelog_path.stat().st_size == 0:
        return set()
    with changelog_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        event_ids = set()
        for row in reader:
            event_id = row.get("event_id")
            record_id = row.get("record_id", "")
            record_name = row.get("record_name", "")
            if event_id:
                event_ids.add(event_id)
                if event_id not in SYNCED_RECORD_NAMES and record_id and record_name:
                    SYNCED_RECORD_NAMES[event_id] = record_name
        return event_ids


def load_record_name_map() -> dict[str, str]:
    """Return mapping of record_id -> name from current golden dataset."""
    golden_path = pathlib.Path("data/published/latest/NYCGO_golden_dataset_v0_19.csv")
    mapping: dict[str, str] = {}
    if not golden_path.exists():
        return mapping
    with golden_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row.get("RecordID")
            name = row.get("Name") or ""
            if rid:
                mapping[rid] = name
    return mapping


def append_rows(changelog_path: pathlib.Path, fieldnames, rows):
    # Ensure header exists
    file_exists = changelog_path.exists() and changelog_path.stat().st_size > 0
    with changelog_path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)
            event_id = r.get("event_id")
            record_name = r.get("record_name", "")
            if event_id and record_name:
                SYNCED_RECORD_NAMES[event_id] = record_name


def main():
    parser = argparse.ArgumentParser(
        description="Append approved reviewed changes to changelog (idempotent)"
    )
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument(
        "--changelog", type=pathlib.Path, default=pathlib.Path("data/changelog.csv")
    )
    parser.add_argument("--operator", type=str, default="")
    parser.add_argument("--require-new", action="store_true")
    parser.add_argument(
        "--skip-record-name-sync",
        action="store_true",
        help="Do not try to backfill record_name from golden dataset",
    )
    args = parser.parse_args()

    reviewed_path = args.run_dir / "reviewed_changes.csv"
    summary_path = args.run_dir / "run_summary.json"

    if not reviewed_path.exists():
        print(
            f"Error: not found {reviewed_path}. Run review step first.", file=sys.stderr
        )
        sys.exit(1)

    with reviewed_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        reviewed_rows = [dict(r) for r in reader]

    approved = [r for r in reviewed_rows if r.get("review_status") == "approved"]

    record_name_map = {}
    if not args.skip_record_name_sync:
        record_name_map = load_record_name_map()

    existing = read_existing_event_ids(args.changelog)
    to_append = []
    for r in approved:
        if r.get("event_id") in existing:
            continue
        # Build minimal schema row
        reason = r.get("reason") or r.get("reason_code") or ""
        # URL validation
        url = r.get("evidence_url", "").strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = ""
        # source_ref from non-URL feedback_source or source_ref
        source_ref = r.get("source_ref") or r.get("feedback_source") or ""
        if source_ref.startswith("http://") or source_ref.startswith("https://"):
            source_ref = ""
        operator = args.operator or r.get("operator", "")
        record_name = r.get("record_name", "")
        if not record_name and not args.skip_record_name_sync:
            record_name = record_name_map.get(r.get("record_id", ""), "")
        if r.get("event_id") in SYNCED_RECORD_NAMES and not record_name:
            record_name = SYNCED_RECORD_NAMES[r.get("event_id")]
        out_row = {
            "event_id": r.get("event_id", ""),
            "timestamp_utc": r.get("timestamp_utc", ""),
            "run_id": r.get("run_id", ""),
            "record_id": r.get("record_id", ""),
            "record_name": record_name,
            "field": r.get("field", ""),
            "old_value": r.get("old_value", ""),
            "new_value": r.get("new_value", ""),
            "reason": reason,
            "evidence_url": url,
            "source_ref": source_ref,
            "operator": operator,
            "notes": r.get("notes", ""),
        }
        to_append.append(out_row)

    # No-op behavior
    if not to_append and args.require_new:
        print("No new rows to append.", file=sys.stderr)
        sys.exit(2)

    # Append
    fieldnames = [
        "event_id",
        "timestamp_utc",
        "run_id",
        "record_id",
        "record_name",
        "field",
        "old_value",
        "new_value",
        "reason",
        "evidence_url",
        "source_ref",
        "operator",
        "notes",
    ]
    if to_append:
        append_rows(args.changelog, fieldnames, to_append)

    appended_count = len(to_append)
    # Update summary counts
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
        except Exception:
            summary = {}
    counts = summary.get("counts", {})
    counts["appended"] = appended_count
    summary["counts"] = counts
    summary_path.write_text(json.dumps(summary, indent=2))

    print(f"Appended {appended_count} new rows to {args.changelog}")


if __name__ == "__main__":
    main()
