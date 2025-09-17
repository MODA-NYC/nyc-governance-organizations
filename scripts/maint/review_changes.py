#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

APPROVED = "approved"
REJECTED = "rejected"


def normalize_value(value: str) -> str:
    if value is None:
        return ""
    # Normalize whitespace and Unicode NFC
    s = str(value).strip()
    s = " ".join(s.split())
    try:
        import unicodedata

        s = unicodedata.normalize("NFC", s)
    except Exception:
        pass
    return s


def compute_event_id(record_id: str, field: str, old_value: str, new_value: str) -> str:
    norm = "|".join(
        [
            normalize_value(record_id).lower(),
            normalize_value(field).lower(),
            normalize_value(old_value).lower(),
            normalize_value(new_value).lower(),
        ]
    )
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def load_csv(path: pathlib.Path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
    return rows, reader.fieldnames


def write_csv(path: pathlib.Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description="Review proposed changes for a run.")
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--approvals-csv", type=pathlib.Path)
    args = parser.parse_args()

    run_dir = args.run_dir
    proposed_path = run_dir / "proposed_changes.csv"
    reviewed_path = run_dir / "reviewed_changes.csv"
    summary_path = run_dir / "run_summary.json"

    try:
        rows, cols = load_csv(proposed_path)
    except FileNotFoundError:
        print(f"Error: not found {proposed_path}", file=sys.stderr)
        sys.exit(1)

    required_cols = {
        "timestamp_utc",
        "run_id",
        "record_id",
        "field",
        "old_value",
        "new_value",
        "evidence_url",
        "operator",
        "notes",
    }
    missing = [c for c in required_cols if c not in cols]
    if missing:
        print(
            f"Error: proposed_changes.csv missing columns: {missing}", file=sys.stderr
        )
        sys.exit(2)

    # Normalize and compute event_id
    dedup = {}
    for r in rows:
        # Preserve optional 'reason' and 'source_ref' if present
        for k in [
            "record_id",
            "field",
            "old_value",
            "new_value",
            "evidence_url",
            "operator",
            "notes",
            "reason_code",
            "change_kind",
            "reason",
            "source_ref",
            "feedback_source",
        ]:
            r[k] = normalize_value(r.get(k, ""))
        # Validate simple URL shape if present
        url = r.get("evidence_url", "")
        if url and not (url.startswith("http://") or url.startswith("https://")):
            r["evidence_url"] = ""
        r["event_id"] = compute_event_id(
            r.get("record_id", ""),
            r.get("field", ""),
            r.get("old_value", ""),
            r.get("new_value", ""),
        )
        dedup[r["event_id"]] = r

    reviewed = list(dedup.values())

    # Default all to approved
    for r in reviewed:
        r["review_status"] = APPROVED

    # Apply optional overrides
    if args.approvals_csv and args.approvals_csv.exists():
        with args.approvals_csv.open("r", newline="", encoding="utf-8-sig") as f:
            ar = csv.DictReader(f)
            status_by_id = {
                row["event_id"].strip(): row["review_status"].strip() for row in ar
            }
        for r in reviewed:
            if r["event_id"] in status_by_id:
                r["review_status"] = status_by_id[r["event_id"]]

    # Reorder columns for output
    out_cols = [
        "event_id",
        "timestamp_utc",
        "run_id",
        "record_id",
        "field",
        "old_value",
        "new_value",
        "evidence_url",
        "operator",
        "review_status",
        "notes",
        # Optional passthroughs that may be used by append step
        "reason",
        "reason_code",
        "source_ref",
        "feedback_source",
    ]
    write_csv(reviewed_path, out_cols, reviewed)

    # Write summary
    summary = {
        "run_id": reviewed[0]["run_id"] if reviewed else "",
        "started_at": None,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": None,
        "counts": {
            "proposed": len(rows),
            "approved": sum(1 for r in reviewed if r["review_status"] == APPROVED),
            "rejected": sum(1 for r in reviewed if r["review_status"] == REJECTED),
            "appended": 0,
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(
        "Reviewed "
        + str(len(rows))
        + " → "
        + str(len(reviewed))
        + " unique events. Output: "
        + str(reviewed_path)
    )


if __name__ == "__main__":
    main()
