"""Top-level orchestration for the NYC Governance Organizations pipeline."""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from . import export as export_utils
from . import global_rules, qa_edits
from .review import build_review_artifacts


def compare_published_exports(  # noqa: C901
    previous_export: Path | None,
    new_export: Path,
) -> dict[str, Any]:
    """
    Compare previous and new published exports to find changes.

    Returns a dictionary with:
    - added: records added to Open Data
    - removed: records removed from Open Data
    - directory_status_changes: records where directory eligibility changed

    Args:
        previous_export: Path to previous published CSV (may be None)
        new_export: Path to new published CSV

    Returns:
        Dictionary with export changes
    """
    result: dict[str, Any] = {
        "added": [],
        "removed": [],
        "directory_status_changes": [],
    }

    # Load the new export
    try:
        df_new = pd.read_csv(new_export, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception as e:
        print(f"Warning: Could not load new export for comparison: {e}")
        return result

    # If no previous export, all records are "new" but we don't report them as added
    # (this avoids noise on first run)
    if previous_export is None or not previous_export.exists():
        print("No previous export available for comparison")
        return result

    # Load the previous export
    try:
        df_prev = pd.read_csv(previous_export, dtype=str, encoding="utf-8-sig").fillna(
            ""
        )
    except Exception as e:
        print(f"Warning: Could not load previous export for comparison: {e}")
        return result

    # Find record_id column (handle both cases)
    new_id_col = "record_id" if "record_id" in df_new.columns else "RecordID"
    prev_id_col = "record_id" if "record_id" in df_prev.columns else "RecordID"

    if new_id_col not in df_new.columns or prev_id_col not in df_prev.columns:
        print("Warning: Could not find record_id column in exports")
        return result

    # Get sets of record IDs
    new_ids = set(df_new[new_id_col].tolist())
    prev_ids = set(df_prev[prev_id_col].tolist())

    # Records added (in new but not in previous)
    added_ids = new_ids - prev_ids
    for record_id in sorted(added_ids):
        row = df_new[df_new[new_id_col] == record_id].iloc[0]
        name = row.get("name", row.get("Name", "Unknown"))
        result["added"].append({"id": record_id, "name": name})

    # Records removed (in previous but not in new)
    removed_ids = prev_ids - new_ids
    for record_id in sorted(removed_ids):
        row = df_prev[df_prev[prev_id_col] == record_id].iloc[0]
        name = row.get("name", row.get("Name", "Unknown"))
        result["removed"].append({"id": record_id, "name": name})

    # Directory eligibility changes (for records in both)
    common_ids = new_ids & prev_ids

    # Find directory column names
    new_dir_col = (
        "listed_in_nyc_gov_agency_directory"
        if "listed_in_nyc_gov_agency_directory" in df_new.columns
        else "ListedInNycGovAgencyDirectory"
    )
    prev_dir_col = (
        "listed_in_nyc_gov_agency_directory"
        if "listed_in_nyc_gov_agency_directory" in df_prev.columns
        else "ListedInNycGovAgencyDirectory"
    )

    if new_dir_col in df_new.columns and prev_dir_col in df_prev.columns:
        # Create lookup dicts for efficiency
        new_dir_values = dict(
            zip(df_new[new_id_col], df_new[new_dir_col], strict=False)
        )
        prev_dir_values = dict(
            zip(df_prev[prev_id_col], df_prev[prev_dir_col], strict=False)
        )
        new_names = dict(
            zip(
                df_new[new_id_col],
                df_new.get("name", df_new.get("Name", "")),
                strict=False,
            )
        )

        def normalize_bool(val: str) -> str:
            """Normalize boolean string to TRUE/FALSE."""
            if not val or str(val).strip() == "":
                return ""
            val_lower = str(val).strip().lower()
            if val_lower in ["true", "1", "t", "yes"]:
                return "TRUE"
            elif val_lower in ["false", "0", "f", "no"]:
                return "FALSE"
            return ""

        for record_id in sorted(common_ids):
            old_val = normalize_bool(prev_dir_values.get(record_id, ""))
            new_val = normalize_bool(new_dir_values.get(record_id, ""))

            if old_val != new_val and old_val and new_val:  # Both must have values
                result["directory_status_changes"].append(
                    {
                        "id": record_id,
                        "name": new_names.get(record_id, "Unknown"),
                        "from": old_val,
                        "to": new_val,
                    }
                )

    # Print summary
    print("\nPublished export comparison:")
    print(f"  - Records added to Open Data: {len(result['added'])}")
    print(f"  - Records removed from Open Data: {len(result['removed'])}")
    dir_changes_count = len(result["directory_status_changes"])
    print(f"  - Directory eligibility changes: {dir_changes_count}")

    return result


def convert_to_socrata_json(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to Socrata-compatible JSON format.

    Transformations:
    - url -> {"url": "..."} (nested object)
    - principal_officer_contact_url -> principal_officer_contact: {"url": "..."}
    - listed_in_nyc_gov_agency_directory -> listed_in_nyc_gov_agency (truncated name)
    - Boolean strings -> actual booleans
    - Empty fields are omitted
    """
    records = []

    for _, row in df.iterrows():
        record = {}

        for col in df.columns:
            value = row[col]

            # Skip empty/null values
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                continue

            # URL field transformations (nested objects)
            if col == "url":
                record["url"] = {"url": value}
            elif col == "principal_officer_contact_url":
                record["principal_officer_contact"] = {"url": value}
            # Boolean field transformations
            elif col in ("in_org_chart", "listed_in_nyc_gov_agency_directory"):
                bool_value = str(value).strip().lower() == "true"
                if col == "listed_in_nyc_gov_agency_directory":
                    record["listed_in_nyc_gov_agency"] = bool_value
                else:
                    record[col] = bool_value
            else:
                record[col] = value

        records.append(record)

    return records


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
    df_rules = global_rules.format_boolean_fields(df_rules, changed_by, prefix)
    df_rules = global_rules.format_founding_year(df_rules, changed_by, prefix)
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
    published_json_output = run_artifacts.outputs_dir / "published_pre-release.json"
    run_changelog_path = run_artifacts.outputs_dir / "run_changelog.csv"
    combined_changelog = global_rules.changelog_entries + qa_edits.changelog_entries
    changelog_df = pd.DataFrame(combined_changelog, columns=qa_edits.CHANGELOG_COLUMNS)
    changelog_df.to_csv(run_changelog_path, index=False, encoding="utf-8-sig")

    # Generate Socrata-compatible JSON from published CSV
    df_published = pd.read_csv(published_output, dtype=str, encoding="utf-8-sig")
    socrata_records = convert_to_socrata_json(df_published)
    with open(published_json_output, "w", encoding="utf-8") as f:
        json.dump(socrata_records, f, indent=2, ensure_ascii=False)

    review_artifacts = build_review_artifacts(
        run_artifacts.review_dir,
        golden_output,
        published_output,
        previous_export,
    )

    # Compare published exports to find changes for release notes
    published_export_changes = compare_published_exports(
        previous_export,
        published_output,
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
            "published_pre_release_json": str(published_json_output),
            "run_changelog": str(run_changelog_path),
            "review_artifacts": review_artifacts,
        },
        "counts": {
            "global_rules_changes": len(global_rules.changelog_entries),
            "qa_changes": len(qa_edits.changelog_entries),
            "records_after_pipeline": len(df_final),
            "directory_field_changes": export_outputs.get("directory_changes", 0),
        },
        "published_export_changes": published_export_changes,
        "timing_seconds": round(time.time() - start_time, 2),
    }

    summary_path = run_artifacts.outputs_dir / "run_summary.json"
    write_json(summary_path, summary)
    summary["outputs"]["run_summary_json"] = str(summary_path)
    return summary
