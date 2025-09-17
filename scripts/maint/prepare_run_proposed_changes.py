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


def load_legacy_changelog(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Map legacy column names to proposed schema columns
            record_id = row.get("record_id") or row.get("RecordID") or ""
            column_changed = (
                row.get("column_changed")
                or row.get("ColumnChanged")
                or row.get("column")
                or ""
            )
            field = LEGACY_FIELD_MAP.get(column_changed, "")
            feedback_source = row.get("feedback_source") or row.get("FeedbackSource")
            evidence_url = feedback_source if is_url(feedback_source) else ""
            source_ref = "" if evidence_url else (feedback_source or "")
            rows.append(
                {
                    "timestamp_utc": "",  # will backfill later
                    "run_id": "",  # will set later
                    "record_id": nfc_trim(record_id),
                    "field": nfc_trim(field),
                    "old_value": nfc_trim(row.get("old_value") or row.get("OldValue")),
                    "new_value": nfc_trim(row.get("new_value") or row.get("NewValue")),
                    "reason": nfc_trim(row.get("reason") or row.get("Reason")),
                    "evidence_url": nfc_trim(evidence_url),
                    "source_ref": nfc_trim(source_ref),
                    "operator": nfc_trim(row.get("changed_by") or row.get("ChangedBy")),
                    "notes": nfc_trim(row.get("notes") or row.get("Notes")),
                }
            )
        return rows


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
            rr["timestamp_utc"] = ts
            rr["run_id"] = run_id
            rr["phase"] = phase
            out.append(rr)
        return out

    if args.combined and args.combined.exists():
        rows = load_legacy_changelog(args.combined)
        stamped = stamp_rows(rows, "combined")
        write_csv(
            run_dir / "proposed_changes.csv",
            [
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
            ],
            stamped,
        )
        (run_dir / "proposed_changes_step1.csv").write_text("")
        (run_dir / "proposed_changes_step2.csv").write_text("")
        summary = {"run_id": run_id, "counts": {"proposed": len(stamped)}}
        (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))
        print(f"Prepared combined proposed changes at {run_dir}/proposed_changes.csv")
        return 0

    if args.step1 and args.step1.exists():
        rows_step1 = stamp_rows(load_legacy_changelog(args.step1), "step1")
        write_csv(
            run_dir / "proposed_changes_step1.csv",
            (
                list(rows_step1[0].keys())
                if rows_step1
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
            rows_step1,
        )

    if args.step2 and args.step2.exists():
        rows_step2 = stamp_rows(load_legacy_changelog(args.step2), "step2")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
