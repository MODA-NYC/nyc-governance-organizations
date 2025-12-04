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
    latest_published_symlink = latest_dir / "NYCGovernanceOrganizations_latest.csv"
    shutil.copy2(golden_source, latest_golden)
    shutil.copy2(published_source, latest_published)
    # Create latest symlink/copy for GitHub releases
    shutil.copy2(published_source, latest_published_symlink)

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
        "published_latest_symlink": latest_published_symlink,
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
            "evidence_url": raw_rows.get("evidence_url", ""),  # Extract from internal changelog
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


def generate_release_notes(  # noqa: C901
    run_dir: Path,
    version: str,
    run_id: str,
    final_paths: dict[str, Path],
    summary: dict,
    changelog_rows: int,
    latest_dir: Path,
) -> Path:
    """Generate release notes markdown file for GitHub releases."""
    outputs_dir = run_dir / "outputs"
    run_changelog = outputs_dir / "run_changelog.csv"

    # Read run summary data
    counts = summary.get("counts", {})
    inputs_original = summary.get("inputs_original", {})
    inputs_copied = summary.get("inputs", {})
    changed_by = summary.get("changed_by", "unknown")

    # Count records in published dataset
    published_path = final_paths["published_final"]
    df_published = pd.read_csv(published_path, dtype=str)
    record_count = len(df_published)

    # Get input file names from original sources (preferred) or fall back
    input_files = []
    if inputs_original:
        # New format: use original source paths
        if "golden_source" in inputs_original:
            golden_source_path = Path(inputs_original["golden_source"])
            input_files.append(f"`{golden_source_path.name}`")
        if "qa_sources" in inputs_original:
            for qa_path_str in inputs_original["qa_sources"]:
                qa_path = Path(qa_path_str)
                input_files.append(f"`{qa_path.name}`")
    else:
        # Fall back: try to extract from changelog and infer golden dataset
        # Check changelog for QA source file names
        qa_files_found = set()
        if run_changelog.exists():
            changelog_df = pd.read_csv(run_changelog, dtype=str)
            if "feedback_source" in changelog_df.columns:
                source_files = changelog_df["feedback_source"].dropna().unique()
                for source_file in source_files:
                    if source_file and source_file.strip():
                        qa_files_found.add(Path(source_file).name)

        # Infer golden dataset from version (if publishing v1.1.0, likely used v1.0.0)
        # This is a heuristic - in future runs, inputs_original will have actual path
        version_num = version.replace("v", "")
        parts = version_num.split(".")
        if len(parts) >= 2:
            try:
                major = int(parts[0])
                minor = int(parts[1]) - 1 if int(parts[1]) > 0 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                prev_version_formatted = f"{major}.{minor}.{patch}"
                golden_file_name = f"NYCGO_golden_dataset_v{prev_version_formatted}.csv"
                input_files.append(f"`{golden_file_name}`")
            except (ValueError, IndexError):
                # Fallback: use v1.0.0
                input_files.append("`NYCGO_golden_dataset_v1.0.0.csv`")
        else:
            # Fallback: use v1.0.0
            input_files.append("`NYCGO_golden_dataset_v1.0.0.csv`")

        # Add QA files from changelog
        for qa_file in sorted(qa_files_found):
            input_files.append(f"`{qa_file}`")

        # If still no files found, use copied names as last resort
        if not input_files:
            for key, path_str in inputs_copied.items():
                if "golden" in key.lower():
                    input_files.append(f"`{Path(path_str).name}`")
                elif "qa" in key.lower():
                    input_files.append(f"`{Path(path_str).name}`")

    # Count changelog entries
    changelog_entry_count = 0
    if run_changelog.exists():
        changelog_df = pd.read_csv(run_changelog, dtype=str)
        changelog_entry_count = len(changelog_df)

    # Generate notes
    notes_lines = [
        f"# Release {version}",
        "",
        f"**Run ID:** `{run_id}`",
        f"**Published by:** {changed_by}",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        "",
        f"Ran the pipeline on {datetime.now().strftime('%Y-%m-%d')} (`{run_id}`) "
        f"using {', '.join(input_files)}.",
        "",
        f"**Output:** Produced `NYCGovernanceOrganizations_{version}.csv` "
        f"({record_count} records) and versioned golden export; "
        f"appended {changelog_rows} changelog row(s) to `data/changelog.csv`.",
        "",
        "## Changes",
        "",
    ]

    if changelog_entry_count > 0:
        notes_lines.append(f"- **Total changes:** {changelog_entry_count}")
        notes_lines.append(f"- **QA edits:** {counts.get('qa_changes', 0)}")
        notes_lines.append(
            f"- **Global rules:** {counts.get('global_rules_changes', 0)}"
        )
        notes_lines.append(
            f"- **Directory field changes:** {counts.get('directory_field_changes', 0)}"
        )
    else:
        notes_lines.append("- No changes recorded in this run")

    notes_lines.extend(
        [
            "",
            "## Bundle Contents",
            "",
            (
                "Bundle includes the full run artifacts "
                "(inputs, outputs, run summary, changelog) for traceability."
            ),
            "",
            "## Attached Assets",
            "",
            f"- `nycgo-run-{run_id}.zip` - Full run artifacts bundle",
            f"- `NYCGovernanceOrganizations_{version}.csv` - Published dataset",
            (
                "- `NYCGovernanceOrganizations_latest.csv` - "
                "Latest published dataset (copy)"
            ),
            "- `run_changelog.csv` - Run-specific changelog",
        ]
    )

    release_notes_path = latest_dir.parent / f"RELEASE_NOTES_{version}.md"
    release_notes_path.write_text("\n".join(notes_lines), encoding="utf-8")
    return release_notes_path


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

    # Copy zip file to latest directory for GitHub releases
    zip_in_latest: Path | None = None
    if zip_path and zip_path.exists():
        zip_in_latest = latest_dir / zip_path.name
        shutil.copy2(zip_path, zip_in_latest)

    summary_path = run_dir / "outputs" / "run_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    # Generate release notes
    release_notes_path = generate_release_notes(
        run_dir, version, run_dir.name, final_paths, summary, changelog_rows, latest_dir
    )

    # Copy release notes to latest directory
    release_notes_in_latest = latest_dir / release_notes_path.name
    shutil.copy2(release_notes_path, release_notes_in_latest)

    # Copy run changelog to latest directory
    run_changelog_source = run_dir / "outputs" / "run_changelog.csv"
    run_changelog_in_latest: Path | None = None
    if run_changelog_source.exists():
        run_changelog_in_latest = latest_dir / "run_changelog.csv"
        shutil.copy2(run_changelog_source, run_changelog_in_latest)

    summary.setdefault("publish", {})
    summary["publish"].update(
        {
            "version": version,
            "golden_final": str(final_paths["golden_final"]),
            "published_final": str(final_paths["published_final"]),
            "golden_latest": str(final_paths["golden_latest"]),
            "published_latest": str(final_paths["published_latest"]),
            "published_latest_symlink": str(final_paths["published_latest_symlink"]),
            "run_summary_latest": (
                str(final_paths["run_summary_latest"])
                if final_paths["run_summary_latest"]
                else None
            ),
            "archive_zip": str(zip_path) if zip_path else None,
            "archive_zip_in_latest": str(zip_in_latest) if zip_in_latest else None,
            "release_notes": str(release_notes_path),
            "release_notes_in_latest": str(release_notes_in_latest),
            "run_changelog_in_latest": (
                str(run_changelog_in_latest) if run_changelog_in_latest else None
            ),
            "changelog_appended": changelog_appended,
            "changelog_rows_appended": changelog_rows,
        }
    )
    summary_path.write_text(json.dumps(summary, indent=2))

    return summary["publish"]
