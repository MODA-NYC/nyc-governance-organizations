#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

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


def nfc_trim(value: str) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    s = " ".join(s.split())
    try:
        import unicodedata

        s = unicodedata.normalize("NFC", s)
    except Exception:
        pass
    return s


def is_url(value: str) -> bool:
    v = (value or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://")


def compute_run_id(run_id_opt: str | None) -> str:
    if run_id_opt:
        return run_id_opt
    try:
        out = subprocess.check_output(
            ["python", "scripts/maint/make_run_id.py"], timeout=10
        ).decode("utf-8")
        return out.strip()
    except Exception:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%MZ")
        return f"{now}_nogit"


def load_input_rows(path: Path) -> tuple[list[dict], dict]:
    """Load rows from a step changelog CSV and return (rows, stats).

    Ensures a canonical 'field' value. If only 'column_changed' exists, maps via
    LEGACY_FIELD_MAP. Rows with unmapped fields are skipped. Applies provenance
    rules from 'feedback_source'. Preserves free-text 'reason' and 'notes'.
    """
    stats = {"skipped_unmapped": 0, "unmapped_fields": set()}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows: list[dict] = []
        for raw in reader:
            record_id = raw.get("record_id") or raw.get("RecordID") or ""
            # Determine canonical field
            field = raw.get("field") or ""
            if not field:
                column_changed = (
                    raw.get("column_changed")
                    or raw.get("ColumnChanged")
                    or raw.get("column")
                    or ""
                )
                field = LEGACY_FIELD_MAP.get(column_changed, "")
                if not field:
                    stats["skipped_unmapped"] += 1
                    if column_changed:
                        stats["unmapped_fields"].add(column_changed)
                    continue

            # Provenance from feedback_source
            feedback_source = raw.get("feedback_source") or raw.get("FeedbackSource")
            evidence_url = ""
            source_ref = ""
            if feedback_source:
                if is_url(feedback_source):
                    evidence_url = feedback_source
                else:
                    source_ref = feedback_source

            row = {
                "timestamp_utc": nfc_trim(raw.get("timestamp_utc") or ""),
                "run_id": nfc_trim(raw.get("run_id") or ""),
                "record_id": nfc_trim(record_id),
                "record_name": nfc_trim(raw.get("record_name") or raw.get("Name") or raw.get("name") or ""),
                "field": nfc_trim(field),
                "old_value": nfc_trim(raw.get("old_value") or raw.get("OldValue")),
                "new_value": nfc_trim(raw.get("new_value") or raw.get("NewValue")),
                "reason": nfc_trim(raw.get("reason") or raw.get("Reason")),
                "evidence_url": nfc_trim(evidence_url or raw.get("evidence_url") or ""),
                "source_ref": nfc_trim(source_ref or raw.get("source_ref") or ""),
                "operator": nfc_trim(
                    raw.get("operator") or raw.get("changed_by") or raw.get("ChangedBy")
                ),
                "notes": nfc_trim(raw.get("notes") or raw.get("Notes")),
            }
            rows.append(row)
    return rows, stats


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def coalesce(step1: list[dict], step2: list[dict]) -> list[dict]:
    kept: dict[tuple[str, str], dict] = {}
    for r in step1:
        key = (r.get("record_id", ""), r.get("field", ""))
        kept[key] = r
    for r in step2:
        key = (r.get("record_id", ""), r.get("field", ""))
        kept[key] = r  # step2 overrides
    return list(kept.values())


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare per-run proposed_changes from existing step changelog files"
        )
    )
    parser.add_argument("--run-id")
    parser.add_argument("--step1", type=Path)
    parser.add_argument("--step2", type=Path)
    parser.add_argument("--combined", type=Path)
    args = parser.parse_args()

    run_id = compute_run_id(args.run_id)
    run_dir = Path("data/audit/runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Load inputs
    rows_step1: list[dict] = []
    rows_step2: list[dict] = []

    def stamp_rows(rows: list[dict], phase: str) -> list[dict]:
        ts = datetime.now(timezone.utc).isoformat()
        out = []
        for r in rows:
            rr = {k: nfc_trim(v) for k, v in r.items()}
            rr["timestamp_utc"] = rr.get("timestamp_utc") or ts
            rr["run_id"] = run_id
            rr["phase"] = phase
            out.append(rr)
        return out

    if args.combined and args.combined.exists():
        rows, stats_combined = load_input_rows(args.combined)
        stamped = stamp_rows(rows, "combined")
        write_csv(
            run_dir / "proposed_changes.csv",
            [
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
                "phase",
            ],
            stamped,
        )
        (run_dir / "proposed_changes_step1.csv").write_text("")
        (run_dir / "proposed_changes_step2.csv").write_text("")
        summary = {"run_id": run_id, "counts": {"proposed": len(stamped)}}
        (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))
        print(f"Prepared combined proposed changes at {run_dir}/proposed_changes.csv")
        if stats_combined.get("skipped_unmapped"):
            print(
                "Skipped "
                + str(stats_combined["skipped_unmapped"])
                + " rows with unmapped fields: "
                + str(sorted(stats_combined["unmapped_fields"]))
            )
        return 0

    stats_step1 = {"skipped_unmapped": 0, "unmapped_fields": set()}
    stats_step2 = {"skipped_unmapped": 0, "unmapped_fields": set()}

    if args.step1 and args.step1.exists():
        r1, s1 = load_input_rows(args.step1)
        stats_step1 = s1
        rows_step1 = stamp_rows(r1, "step1")
        write_csv(
            run_dir / "proposed_changes_step1.csv",
            (
                list(rows_step1[0].keys())
                if rows_step1
                else [
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
                    "phase",
                ]
            ),
            rows_step1,
        )

    if args.step2 and args.step2.exists():
        r2, s2 = load_input_rows(args.step2)
        stats_step2 = s2
        rows_step2 = stamp_rows(r2, "step2")
        write_csv(
            run_dir / "proposed_changes_step2.csv",
            (
                list(rows_step2[0].keys())
                if rows_step2
                else [
                    "timestamp_utc",
                    "run_id",
                    "record_id",
                    "field",
                    "old_value",
                    "new_value",
                    "reason",
                    "evidence_url",
                    "source_ref",
                    "operator",
                    "notes",
                    "phase",
                ]
            ),
            rows_step2,
        )

    proposed_rows = coalesce(rows_step1, rows_step2)
    # Filter invalids
    proposed_rows = [r for r in proposed_rows if r.get("record_id") and r.get("field")]
    write_csv(
        run_dir / "proposed_changes.csv",
        [
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
            "phase",
        ],
        proposed_rows,
    )
    summary = {"run_id": run_id, "counts": {"proposed": len(proposed_rows)}}
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Prepared proposed changes at {run_dir}/proposed_changes.csv")
    skipped_total = stats_step1.get("skipped_unmapped", 0) + stats_step2.get(
        "skipped_unmapped", 0
    )
    unmapped_union = sorted(
        set(stats_step1.get("unmapped_fields", set())).union(
            set(stats_step2.get("unmapped_fields", set()))
        )
    )
    if skipped_total:
        print(
            "Skipped "
            + str(skipped_total)
            + " rows with unmapped fields across steps: "
            + str(unmapped_union)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
