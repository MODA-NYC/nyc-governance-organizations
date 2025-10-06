"""Top-level orchestration for the NYC Governance Organizations pipeline."""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from . import export as export_utils
from . import global_rules, qa_edits
from .utility_case_converter import snake_case_dataframe
from utility_name_parser import populate_officer_name_parts


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


def copy_into_inputs(artifacts: RunArtifacts, sources: dict[str, Path]) -> dict[str, Path]:
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
    qa_paths: Iterable[Path],
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
    copied_inputs = copy_into_inputs(run_artifacts, inputs_map)

    df = pd.read_csv(golden_source, dtype=str).fillna("")
    global_rules.reset_changelog()
    prefix = run_id.replace("/", "_")
    df_rules = global_rules.apply_global_character_fixing(df, changed_by, prefix)
    df_rules = global_rules.apply_global_deduplication(df_rules, changed_by, prefix)
    df_rules = global_rules.format_budget_codes(df_rules, changed_by, prefix)

    qa_edits.reset_changelog()
    current_df = df_rules.copy()
    for qa_path in qa_paths:
        current_df = qa_edits.apply_qa_edits(current_df, qa_path, changed_by, prefix)

    df_named = populate_officer_name_parts(current_df)
    df_snake = snake_case_dataframe(df_named)

    export_outputs = export_utils.export_datasets(
        df_snake,
        output_golden=output_golden,
        output_published=output_published,
        run_dir=run_artifacts.outputs_dir,
        run_id=run_id,
        operator=operator,
        previous_export=previous_export,
    )

    run_changelog_path = run_artifacts.outputs_dir / "run_changelog.csv"
    combined_changelog = global_rules.changelog_entries + qa_edits.changelog_entries
    changelog_df = pd.DataFrame(combined_changelog, columns=qa_edits.CHANGELOG_COLUMNS)
    changelog_df.to_csv(run_changelog_path, index=False, encoding="utf-8-sig")

    summary = {
        "run_id": run_id,
        "changed_by": changed_by,
        "operator": operator,
        "inputs": {name: str(path) for name, path in copied_inputs.items()},
        "outputs": {
            "golden_pre_release": export_outputs["golden_pre_release"],
            "published_pre_release": export_outputs["published_pre_release"],
            "run_changelog": str(run_changelog_path),
        },
        "counts": {
            "global_rules_changes": len(global_rules.changelog_entries),
            "qa_changes": len(qa_edits.changelog_entries),
            "records_after_pipeline": len(df_snake),
            "directory_field_changes": export_outputs.get("directory_changes", 0),
        },
        "timing_seconds": round(time.time() - start_time, 2),
    }

    write_json(run_artifacts.outputs_dir / "run_summary.json", summary)
    return summary
