"""Top-level orchestration for the NYC Governance Organizations pipeline."""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import export as export_utils
from . import global_rules, qa_edits
from .review import build_review_artifacts


@dataclass(slots=True)
class RunArtifacts:
    run_dir: Path
    inputs_dir: Path
    outputs_dir: Path
    review_dir: Path


def ensure_run_dirs(run_dir: Path) -> RunArtifacts:
    inputs = run_dir / "inputs"
    outputs = run_dir / "outputs"
    review = run_dir / "review"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    review.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(run_dir, inputs, outputs, review)


def copy_into_inputs(
    artifacts: RunArtifacts, sources: dict[str, Path]
) -> dict[str, Path]:
    copied: dict[str, Path] = {}
    for dest_name, src in sources.items():
        destination = artifacts.inputs_dir / dest_name
        if src.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(src, destination)
        else:
            shutil.copy2(src, destination)
        copied[dest_name] = destination
    return copied


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def orchestrate_pipeline(
    *,
    golden_source: Path,
    qa_paths: Sequence[Path],
    run_id: str,
    changed_by: str,
    operator: str,
    run_dir: Path,
    previous_export: Path | None,
    output_golden: Path,
    output_published: Path,
) -> dict:
    run_artifacts = ensure_run_dirs(run_dir)
    start_time = time.time()

    inputs_map = {"golden_snapshot.csv": golden_source}
    for idx, qa_path in enumerate(qa_paths, start=1):
        inputs_map[f"qa_{idx:02d}.csv"] = qa_path
    if previous_export:
        inputs_map["previous_published.csv"] = previous_export
    copied_inputs = copy_into_inputs(run_artifacts, inputs_map)

    df = pd.read_csv(golden_source, dtype=str).fillna("")
    global_rules.reset_changelog()
    prefix = run_id.replace("/", "_")
    df_rules = global_rules.apply_global_character_fixing(df, changed_by, prefix)
    df_rules = global_rules.apply_global_deduplication(df_rules, changed_by, prefix)
    df_rules = global_rules.format_budget_codes(df_rules, changed_by, prefix)
    df_rules = global_rules.sync_nycgov_directory_status(df_rules, changed_by, prefix)

    qa_edits.reset_changelog()
    current_df = df_rules.copy()
    for qa_path in qa_paths:
        current_df = qa_edits.apply_qa_edits(current_df, qa_path, changed_by, prefix)

    df_final = current_df

    export_outputs = export_utils.export_datasets(
        df_final,
        output_golden=output_golden,
        output_published=output_published,
        run_dir=run_artifacts.run_dir,
        run_id=run_id,
        operator=operator,
        previous_export=previous_export,
    )

    golden_output = run_artifacts.outputs_dir / "golden_pre-release.csv"
    published_output = run_artifacts.outputs_dir / "published_pre-release.csv"
    run_changelog_path = run_artifacts.outputs_dir / "run_changelog.csv"
    combined_changelog = global_rules.changelog_entries + qa_edits.changelog_entries
    changelog_df = pd.DataFrame(combined_changelog, columns=qa_edits.CHANGELOG_COLUMNS)
    changelog_df.to_csv(run_changelog_path, index=False, encoding="utf-8-sig")

    review_artifacts = build_review_artifacts(
        run_artifacts.review_dir,
        golden_output,
        published_output,
        previous_export,
    )

    # Store both copied paths and original source paths
    inputs_copied = {name: str(path) for name, path in copied_inputs.items()}
    inputs_original = {
        "golden_source": str(golden_source),
        "qa_sources": [str(qa_path) for qa_path in qa_paths],
    }
    if previous_export:
        inputs_original["previous_export"] = str(previous_export)

    summary = {
        "run_id": run_id,
        "changed_by": changed_by,
        "operator": operator,
        "inputs": inputs_copied,
        "inputs_original": inputs_original,
        "outputs": {
            "golden_pre_release": str(golden_output),
            "published_pre_release": str(published_output),
            "run_changelog": str(run_changelog_path),
            "review_artifacts": review_artifacts,
        },
        "counts": {
            "global_rules_changes": len(global_rules.changelog_entries),
            "qa_changes": len(qa_edits.changelog_entries),
            "records_after_pipeline": len(df_final),
            "directory_field_changes": export_outputs.get("directory_changes", 0),
        },
        "timing_seconds": round(time.time() - start_time, 2),
    }

    summary_path = run_artifacts.outputs_dir / "run_summary.json"
    write_json(summary_path, summary)
    summary["outputs"]["run_summary_json"] = str(summary_path)
    return summary
