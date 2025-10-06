#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

TRACKED_FIELDS = [
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


def is_url(value: str) -> bool:
    v = (value or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://")


def nfc_trim_collapse(value: str) -> str:
    if value is None:
        return ""
    s = str(value)
    s = " ".join(s.strip().split())
    try:
        import unicodedata

        s = unicodedata.normalize("NFC", s)
    except Exception:
        pass
    return s


def compute_event_id(record_id: str, field: str, old_value: str, new_value: str) -> str:
    key = "|".join(
        [
            nfc_trim_collapse(record_id).lower(),
            nfc_trim_collapse(field).lower(),
            nfc_trim_collapse(old_value).lower(),
            nfc_trim_collapse(new_value).lower(),
        ]
    )
    return sha256(key.encode("utf-8")).hexdigest()


def parse_timestamp_guess(ts: str, fallback_mtime_utc_iso: str) -> str:
    s = nfc_trim_collapse(ts)
    if not s:
        return fallback_mtime_utc_iso
    # Try common formats (ISO, naive local-like with seconds)
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    return fallback_mtime_utc_iso


LEGACY_FIELD_MAP = {
    "Name": "name",
    "Acronym": "acronym",
    "NameAlphabetized": "name_alphabetized",
    "URL": "url",
    "AlternateOrFormerNames": "alternate_or_former_names",
    "AlternateOrFormerAcronyms": "alternate_or_former_acronyms",
    "PrincipalOfficerTitle": "principal_officer_title",
    "PrincipalOfficerFullName": "principal_officer_full_name",
    "PrincipalOfficerGivenName": "principal_officer_first_name",
    "PrincipalOfficerFamilyName": "principal_officer_last_name",
    "PrincipalOfficerContactURL": "principal_officer_contact_url",
    "ReportsTo": "reports_to",
    "ReportingTo": "reports_to",
    "InOrgChart": "in_org_chart",
    "ListedInNYCGovAgencyDirectory": "listed_in_nyc_gov_agency_directory",
    "ListedInAgencyDirectory": "listed_in_nyc_gov_agency_directory",
    "OperationalStatus": "operational_status",
}


def ensure_changelog_with_header(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            f.write(",".join(TRACKED_FIELDS) + "\n")


def load_existing_event_ids(path: Path) -> set:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return {row.get("event_id") for row in reader if row.get("event_id")}


def append_tracked_rows(path: Path, rows: list[dict]) -> None:
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKED_FIELDS)
        for r in rows:
            writer.writerow(r)


def run_review(run_dir: Path) -> tuple[int, int]:
    reviewed = run_dir / "reviewed_changes.csv"
    if reviewed.exists():
        with reviewed.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        approved = sum(1 for r in rows if r.get("review_status") == "approved")
        return len(rows), approved

    proposed = run_dir / "proposed_changes.csv"
    if proposed.exists():
        subprocess.check_call(
            [
                "python",
                "scripts/maint/review_changes.py",
                "--run-dir",
                str(run_dir),
            ]
        )
        return run_review(run_dir)
    return 0, 0


def append_run(run_dir: Path, changelog: Path, operator: str) -> tuple[int, int]:
    reviewed = run_dir / "reviewed_changes.csv"
    if not reviewed.exists():
        return 0, 0
    before = len(load_existing_event_ids(changelog))
    subprocess.check_call(
        [
            "python",
            "scripts/maint/append_changelog.py",
            "--run-dir",
            str(run_dir),
            "--changelog",
            str(changelog),
            "--operator",
            operator,
        ]
    )
    after = len(load_existing_event_ids(changelog))
    appended = max(0, after - before)
    skipped = 0
    return appended, skipped


def detect_version_from_filename(path: Path) -> tuple[int | None, int | None]:
    # Handles patterns like:
    #   changelog_v5.csv
    #   changelog_v0_18.csv
    #   changelog_v0_18_step2.csv
    # Capture the last numeric component after 'v' and optional '0_'
    m = re.search(r"v(?:\d+_)?(\d+)(?:_step(\d+))?", path.stem)
    if not m:
        return None, None
    version = int(m.group(1))
    step = int(m.group(2)) if m.group(2) else None
    return version, step


def stream_legacy_rows(path: Path) -> Iterable[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: nfc_trim_collapse(v) for k, v in row.items()}


def coalesce_last_per_field(rows: list[dict]) -> list[dict]:
    last_by_key: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r.get("record_id", ""), r.get("field", ""))
        last_by_key[key] = r
    # Keep insertion order of last occurrences; sort by timestamp for stability
    return list(last_by_key.values())


def build_tracked_from_legacy(path: Path) -> tuple[list[dict], dict]:
    version, step = detect_version_from_filename(path)
    mtime_iso = datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    ).isoformat()
    run_id = f"legacy_v{version}" if step is None else f"legacy_v{version}_step{step}"

    header_lower = None
    rows_out: list[dict] = []
    skipped_unmapped = 0
    seen_event_ids = set()
    unmapped_fields = set()

    for row in stream_legacy_rows(path):
        if header_lower is None:
            header_lower = {k.lower(): k for k in row.keys()}
        # Extract
        record_id = (
            row.get("RecordID") or row.get("record_id") or row.get("RecordId") or ""
        )
        column_changed = (
            row.get("column_changed")
            or row.get("ColumnChanged")
            or row.get("column")
            or ""
        )
        field_canonical = LEGACY_FIELD_MAP.get(column_changed, None)
        if not field_canonical:
            unmapped_fields.add(column_changed)
            skipped_unmapped += 1
            continue
        old_val = row.get("old_value") or row.get("OldValue") or ""
        new_val = row.get("new_value") or row.get("NewValue") or ""
        changed_by = row.get("changed_by") or row.get("ChangedBy") or ""
        feedback_source = row.get("feedback_source") or row.get("FeedbackSource") or ""
        notes = row.get("notes") or row.get("Notes") or ""
        reason = row.get("reason") or row.get("Reason") or ""
        timestamp_raw = row.get("timestamp") or row.get("Timestamp") or ""

        if not record_id or not field_canonical:
            continue

        evidence_url = feedback_source if is_url(feedback_source) else ""
        source_ref = "" if evidence_url else feedback_source
        ts_iso = parse_timestamp_guess(timestamp_raw, mtime_iso)

        event_id = compute_event_id(record_id, field_canonical, old_val, new_val)
        if event_id in seen_event_ids:
            # Duplicate exact change in same file
            continue
        seen_event_ids.add(event_id)

        rows_out.append(
            {
                "event_id": event_id,
                "timestamp_utc": ts_iso,
                "run_id": run_id,
                "record_id": record_id,
                "record_name": row.get("Name") or row.get("name") or "",
                "field": field_canonical,
                "old_value": old_val,
                "new_value": new_val,
                "reason": reason or "",
                "evidence_url": evidence_url,
                "source_ref": source_ref,
                "operator": changed_by,
                "notes": notes,
            }
        )

    # Sort by timestamp then coalesce last per (record_id, field)
    rows_out.sort(key=lambda r: (r.get("timestamp_utc", ""), r.get("run_id", "")))
    coalesced = coalesce_last_per_field(rows_out)

    meta = {
        "version": f"v{version}" if version is not None else None,
        "step": step,
        "rows_loaded": len(rows_out),
        "rows_coalesced": len(rows_out) - len(coalesced),
        "rows_skipped_unmapped": skipped_unmapped,
        "unmapped_fields": sorted(x for x in unmapped_fields if x),
    }
    return coalesced, meta


def format_summary_table(report: dict) -> str:
    lines: list[str] = []
    lines.append("Per-run directories:")
    lines.append("run_id, proposed, approved, appended, skipped_existing")
    for run_id, d in report.get("runs", {}).items():
        line = (
            f"{run_id}, {d.get('proposed', 0)}, {d.get('approved', 0)}, "
            f"{d.get('appended', 0)}, {d.get('skipped_existing', 0)}"
        )
        lines.append(line)
    lines.append("")
    lines.append("Legacy files:")
    lines.append(
        "path, version, rows_loaded, rows_skipped_unmapped, rows_coalesced, "
        "appended, skipped_existing"
    )
    for f in report.get("legacy", {}).get("files", []):
        lines.append(
            f"{f.get('path')}, {f.get('version')}, {f.get('rows_loaded', 0)}, "
            f"{f.get('rows_skipped_unmapped', 0)}, {f.get('rows_coalesced', 0)}, "
            f"{f.get('appended', 0)}, {f.get('skipped_existing', 0)}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest data/audit/* into append-only changelog"
    )
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--glob-legacy",
        type=str,
        default="data/audit/**/changelog_v0_*.csv",
    )
    parser.add_argument("--changelog", type=Path, default=Path("data/changelog.csv"))
    parser.add_argument(
        "--report", type=Path, default=Path("data/audit/ingest_report.json")
    )
    args = parser.parse_args()

    ensure_changelog_with_header(args.changelog)
    existing_ids = load_existing_event_ids(args.changelog)

    report = {"runs": {}, "legacy": {"files": [], "unmapped_fields": []}, "totals": {}}

    # Process per-run directories first
    runs_root = args.audit_root / "runs"
    if runs_root.exists():
        for child in sorted(runs_root.iterdir()):
            if not child.is_dir():
                continue
            run_id = child.name
            proposed, approved = run_review(child)
            appended = 0
            skipped_existing = 0
            if args.apply and approved > 0:
                a_appended, a_skipped = append_run(
                    child, args.changelog, os.environ.get("USER", "system")
                )
                appended = a_appended
                skipped_existing = a_skipped
            report["runs"][run_id] = {
                "proposed": proposed,
                "approved": approved,
                "appended": appended,
                "skipped_existing": skipped_existing,
            }

    # Process legacy files
    legacy_paths = sorted(Path().glob(args.glob_legacy))
    legacy_unmapped_union = set()
    total_legacy_appended = 0
    total_legacy_skipped = 0

    for lp in legacy_paths:
        rows, meta = build_tracked_from_legacy(lp)
        # Drop existing event_ids for idempotency
        new_rows = [r for r in rows if r["event_id"] not in existing_ids]
        skipped_existing = len(rows) - len(new_rows)
        appended = 0
        if args.apply and new_rows:
            append_tracked_rows(args.changelog, new_rows)
            appended = len(new_rows)
            existing_ids.update(r["event_id"] for r in new_rows)
        report["legacy"]["files"].append(
            {
                "path": str(lp),
                "version": meta.get("version"),
                "rows_loaded": meta.get("rows_loaded", 0),
                "rows_coalesced": meta.get("rows_coalesced", 0),
                "rows_skipped_unmapped": meta.get("rows_skipped_unmapped", 0),
                "appended": appended,
                "skipped_existing": skipped_existing,
            }
        )
        legacy_unmapped_union.update(meta.get("unmapped_fields", []))
        total_legacy_appended += appended
        total_legacy_skipped += skipped_existing

    report["legacy"]["unmapped_fields"] = sorted(legacy_unmapped_union)

    # Totals
    total_run_appended = sum(v.get("appended", 0) for v in report["runs"].values())
    total_run_approved = sum(v.get("approved", 0) for v in report["runs"].values())
    report["totals"] = {
        "runs_approved": total_run_approved,
        "runs_appended": total_run_appended,
        "legacy_appended": total_legacy_appended,
        "legacy_skipped_existing": total_legacy_skipped,
    }

    # Write report
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))

    # Pretty stdout summary
    print(format_summary_table(report))

    would_append = total_run_approved + total_legacy_appended
    if not args.apply and would_append > 0:
        print(
            "Dry-run: would append "
            + str(would_append)
            + " rows. Re-run with --apply to commit."
        )

    if args.apply and (total_run_appended + total_legacy_appended == 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
