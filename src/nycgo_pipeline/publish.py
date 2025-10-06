"""Helper utilities to publish a run folder."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from scripts.maint.append_changelog import main as append_changelog_main
from scripts.maint.review_changes import main as review_changes_main


def ensure_archive_dir(base: Path) -> Path:
    archive_dir = base / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def move_current_latest(latest_dir: Path, archive_dir: Path, version: str) -> None:
    if not latest_dir.exists():
        return
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for item in latest_dir.iterdir():
        dest = archive_dir / f"{version}_{timestamp}_{item.name}"
        shutil.copy2(item, dest)


def copy_final_outputs(run_dir: Path, latest_dir: Path, version: str) -> dict[str, Path]:
    outputs_dir = run_dir / "outputs"
    golden_source = outputs_dir / "golden_pre-release.csv"
    published_source = outputs_dir / "published_pre-release.csv"

    final_golden = latest_dir.parent / f"NYCGO_golden_dataset_{version}.csv"
    final_published = latest_dir.parent / f"NYCGovernanceOrganizations_{version}.csv"

    shutil.copy2(golden_source, final_golden)
    shutil.copy2(published_source, final_published)

    latest_dir.mkdir(parents=True, exist_ok=True)
    for src in [final_golden, final_published]:
        shutil.copy2(src, latest_dir / src.name)

    return {
        "golden_final": final_golden,
        "published_final": final_published,
    }


def review_and_append(run_dir: Path, operator: str, changelog_path: Path) -> None:
    review_changes_main()
    append_changelog_main()


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
    artifacts: dict[str, Path],
) -> dict:
    latest_dir = Path("data/published/latest").resolve()
    archive_dir = ensure_archive_dir(latest_dir.parent)

    final_paths = copy_final_outputs(run_dir, latest_dir, version)

    if archive:
        move_current_latest(latest_dir, archive_dir, version)

    changelog_appended = False
    if append_changelog:
        review_and_append(run_dir, operator, Path("data/changelog.csv"))
        changelog_appended = True

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
            "archive_zip": str(zip_path) if zip_path else None,
            "changelog_appended": changelog_appended,
        }
    )
    summary_path.write_text(json.dumps(summary, indent=2))

    return summary["publish"]
