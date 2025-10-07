"""Helper utilities to publish a run folder."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from .directory_changelog import CHANGELOG_COLUMNS


def ensure_archive_dir(base: Path) -> Path:
    archive_dir = base / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def prune_latest_dir(latest_dir: Path, preserve: set[str]) -> None:
    if not latest_dir.exists():
        return
    for item in latest_dir.iterdir():
        if item.name in preserve:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def move_current_latest(
    latest_dir: Path, archive_dir: Path, version: str, run_id: str
) -> None:
    if not latest_dir.exists():
        return
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for item in latest_dir.iterdir():
        dest = archive_dir / f"{version}_{run_id}_{timestamp}_{item.name}"
        shutil.copy2(item, dest)


def copy_final_outputs(
    run_dir: Path, latest_dir: Path, version: str
) -> dict[str, Path]:
    outputs_dir = run_dir / "outputs"
    golden_source = outputs_dir / "golden_pre-release.csv"
    published_source = outputs_dir / "published_pre-release.csv"
    run_summary_source = outputs_dir / "run_summary.json"
    crosswalk_source = outputs_dir / "crosswalk.csv"

    final_golden = latest_dir.parent / f"NYCGO_golden_dataset_{version}_final.csv"
    final_published = (
        latest_dir.parent / f"NYCGovernanceOrganizations_{version}_final.csv"
    )

    shutil.copy2(golden_source, final_golden)
    shutil.copy2(published_source, final_published)

    latest_dir.mkdir(parents=True, exist_ok=True)
    preserve = {"crosswalk.csv"}
    prune_latest_dir(latest_dir, preserve)

    latest_golden = latest_dir / f"NYCGO_golden_dataset_{version}.csv"
    latest_published = latest_dir / f"NYCGovernanceOrganizations_{version}.csv"
    shutil.copy2(golden_source, latest_golden)
    shutil.copy2(published_source, latest_published)

    latest_run_summary: Path | None = None
    if run_summary_source.exists():
        latest_run_summary = latest_dir / "run_summary.json"
        shutil.copy2(run_summary_source, latest_run_summary)

    if crosswalk_source.exists():
        shutil.copy2(crosswalk_source, latest_dir / "crosswalk.csv")

    return {
        "golden_final": final_golden,
        "published_final": final_published,
        "golden_latest": latest_golden,
        "published_latest": latest_published,
        "run_summary_latest": latest_run_summary,
    }


def append_run_changelog(
    run_dir: Path, changelog_path: Path, run_id: str, default_operator: str
) -> int:
    outputs_dir = run_dir / "outputs"
    run_changelog = outputs_dir / "run_changelog.csv"
    if not run_changelog.exists():
        raise FileNotFoundError(
            "Run changelog not found; expected outputs/run_changelog.csv"
        )

    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    if changelog_path.exists():
        existing_rows = pd.read_csv(changelog_path, dtype=str).fillna("")
    else:
        existing_rows = pd.DataFrame(columns=["event_id", *CHANGELOG_COLUMNS])

    raw_rows = pd.read_csv(run_changelog, dtype=str).fillna("")

    def prep_notes(row: pd.Series) -> str:
        base_notes = row.get("notes", "")
        rule_action = row.get("RuleAction", "")
        if rule_action and rule_action not in base_notes:
            suffix = f" [rule_action={rule_action}]"
        else:
            suffix = ""
        return f"{base_notes}{suffix}".strip()

    change_ids = raw_rows.get("ChangeID")
    if change_ids is None or change_ids.eq("").all():
        change_ids = pd.Series([str(i + 1) for i in range(len(raw_rows))])

    operator_series = raw_rows.get("changed_by")
    if operator_series is None or operator_series.eq("").all():
        operator_series = pd.Series([default_operator] * len(raw_rows))
    else:
        operator_series = operator_series.fillna(default_operator).replace(
            "", default_operator
        )

    converted = pd.DataFrame(
        {
            "event_id": [f"{run_id}_{cid}" for cid in change_ids],
            "timestamp_utc": raw_rows.get("timestamp", ""),
            "run_id": run_id,
            "record_id": raw_rows.get("record_id", ""),
            "record_name": raw_rows.get("record_name", ""),
            "field": raw_rows.get("column_changed", ""),
            "old_value": raw_rows.get("old_value", ""),
            "new_value": raw_rows.get("new_value", ""),
            "reason": raw_rows.get("reason", ""),
            "evidence_url": "",
            "source_ref": raw_rows.get("feedback_source", ""),
            "operator": operator_series,
            "notes": raw_rows.apply(prep_notes, axis=1),
        }
    )

    converted = converted[["event_id", *CHANGELOG_COLUMNS]].fillna("")

    combined = pd.concat([existing_rows, converted], ignore_index=True)
    combined.drop_duplicates(subset=["event_id"], keep="last", inplace=True)
    combined.to_csv(changelog_path, index=False, encoding="utf-8-sig")
    return len(converted)


def make_zip(run_dir: Path, dist_dir: Path, run_id: str) -> Path:
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / f"nycgo-run-{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in run_dir.rglob("*"):
            zf.write(path, path.relative_to(run_dir))
    return zip_path


def publish_run(
    *,
    run_dir: Path,
    version: str,
    operator: str,
    append_changelog: bool,
    archive: bool,
) -> dict:
    latest_dir = Path("data/published/latest").resolve()
    archive_dir = ensure_archive_dir(latest_dir.parent)

    if archive:
        move_current_latest(latest_dir, archive_dir, version, run_dir.name)

    final_paths = copy_final_outputs(run_dir, latest_dir, version)

    changelog_appended = False
    changelog_rows = 0
    if append_changelog:
        changelog_rows = append_run_changelog(
            run_dir, Path("data/changelog.csv"), run_dir.name, operator
        )
        changelog_appended = changelog_rows > 0

    dist_dir = Path("dist")
    zip_path = make_zip(run_dir, dist_dir, run_dir.name) if archive else None

    summary_path = run_dir / "outputs" / "run_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    summary.setdefault("publish", {})
    summary["publish"].update(
        {
            "version": version,
            "golden_final": str(final_paths["golden_final"]),
            "published_final": str(final_paths["published_final"]),
            "golden_latest": str(final_paths["golden_latest"]),
            "published_latest": str(final_paths["published_latest"]),
            "run_summary_latest": (
                str(final_paths["run_summary_latest"])
                if final_paths["run_summary_latest"]
                else None
            ),
            "archive_zip": str(zip_path) if zip_path else None,
            "changelog_appended": changelog_appended,
            "changelog_rows_appended": changelog_rows,
        }
    )
    summary_path.write_text(json.dumps(summary, indent=2))

    return summary["publish"]
