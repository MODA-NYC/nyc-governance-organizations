import argparse
from pathlib import Path

import pandas as pd


def find_column_name(
    df_columns: list, target_name: str, csv_path_for_error: Path
) -> str | None:
    """
    Tries to find a column name with fallbacks:
    1. Exact match.
    2. Case-insensitive match.
    3. Snake_case version of target if target has spaces.
    """
    if target_name in df_columns:
        return target_name

    # Case-insensitive match
    for col in df_columns:
        if col.lower() == target_name.lower():
            print(
                f"Info: Found column '{col}' for target '{target_name}' "
                f"(case-insensitive) in {csv_path_for_error}."
            )
            return col

    # Snake_case match (if target_name contains spaces)
    if " " in target_name:
        snake_target = target_name.lower().replace(" ", "_")
        for col in df_columns:
            if col.lower() == snake_target:
                print(
                    f"Info: Found column '{col}' for target '{target_name}' "
                    f"(snake_case match to '{snake_target}') in {csv_path_for_error}."
                )
                return col

    print(
        f"Error: Could not find a suitable column for target '{target_name}' "
        f"in {csv_path_for_error}. Columns available: {df_columns}"
    )
    return None


def compare_datasets(  # noqa: C901
    original_csv_path: Path,
    processed_csv_path: Path,
    output_report_csv_path: Path,
):
    """
    Compares an original filtered dataset with a processed dataset,
    identifies differences in RecordIDs, and generates a report.
    """
    try:
        # Load Datasets
        df_original_full = pd.read_csv(
            original_csv_path, dtype=str, keep_default_na=False
        )
        df_processed = pd.read_csv(processed_csv_path, dtype=str, keep_default_na=False)
    except FileNotFoundError as e:
        print(f"Error: {e}. Please check the input file paths.")
        return
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return

    # --- Filter df_original_full ---
    target_filter_col_name = "NYC.gov Agency Directory"
    actual_filter_col = find_column_name(
        df_original_full.columns.tolist(), target_filter_col_name, original_csv_path
    )
    if not actual_filter_col:
        return

    df_original_filtered = df_original_full[
        df_original_full[actual_filter_col].astype(str).str.upper() == "TRUE"
    ]
    num_original_filtered = len(df_original_filtered)
    print(
        f"Number of rows in original dataset after filtering: "
        f"{num_original_filtered}"
    )

    # --- Identify Common RecordIDs / record_ids ---
    target_original_id_col = "RecordID"
    target_processed_id_col = "record_id"

    actual_original_id_col = find_column_name(
        df_original_filtered.columns.tolist(), target_original_id_col, original_csv_path
    )
    if not actual_original_id_col:
        return

    actual_processed_id_col = find_column_name(
        df_processed.columns.tolist(), target_processed_id_col, processed_csv_path
    )
    if not actual_processed_id_col:
        return

    try:
        original_ids = set(
            df_original_filtered[actual_original_id_col].dropna().astype(str)
        )
        processed_ids = set(df_processed[actual_processed_id_col].dropna().astype(str))
    except KeyError as e:
        print(
            f"Error: ID column {e} not found. "
            f"This shouldn't happen after find_column_name."
        )
        return
    except Exception as e:
        print(f"Error extracting IDs: {e}")
        return

    # --- Perform Comparisons ---
    original_in_processed_ids = original_ids.intersection(processed_ids)
    original_not_in_processed_ids = sorted(list(original_ids - processed_ids))
    processed_not_in_original_ids = sorted(list(processed_ids - original_ids))

    num_processed_rows = len(df_processed)
    num_original_in_processed = len(original_in_processed_ids)
    num_original_not_in_processed = len(original_not_in_processed_ids)
    num_processed_not_in_original = len(processed_not_in_original_ids)

    # --- Generate Console Summary ---
    print("\n--- Dataset Comparison Summary ---")
    print(f"Number of rows in original filtered dataset: {num_original_filtered}")
    print(f"Number of rows in processed dataset: {num_processed_rows}")
    print(
        f"Number of original (filtered) records found in processed dataset: "
        f"{num_original_in_processed}"
    )
    print(
        f"Number of original (filtered) records NOT found in processed dataset: "
        f"{num_original_not_in_processed}"
    )
    print(
        f"Number of processed records NOT found in original (filtered) dataset "
        f"(new records): {num_processed_not_in_original}"
    )

    # --- Create Report DataFrame ---
    report_data = []
    for record_id_val in original_not_in_processed_ids:
        report_data.append(
            {"Status": "Original_RecordID_Not_In_Processed", "RecordID": record_id_val}
        )

    for record_id_val in processed_not_in_original_ids:
        report_data.append(
            {
                "Status": "Processed_RecordID_Not_In_Original_Filtered",
                "RecordID": record_id_val,
            }
        )

    if not report_data:  # If both lists are empty
        report_df = pd.DataFrame(columns=["Status", "RecordID"])
        print("\nNo discrepancies found between the datasets in terms of RecordIDs.")
    else:
        report_df = pd.DataFrame(report_data)

    # --- Save Report CSV ---
    try:
        output_report_csv_path.parent.mkdir(parents=True, exist_ok=True)
        report_df.to_csv(output_report_csv_path, index=False, encoding="utf-8-sig")
        print(f"\nComparison report saved to: {output_report_csv_path}")
    except Exception as e:
        print(f"Error saving report CSV: {e}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare an original filtered dataset with a final processed dataset."
        )
    )
    parser.add_argument(
        "--original_csv",
        type=Path,
        required=True,
        help=(
            "Path to the original dataset CSV file (e.g., "
            "data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv)"
        ),
    )
    parser.add_argument(
        "--processed_csv",
        type=Path,
        required=True,
        help=(
            "Path to the final processed dataset CSV file (e.g., "
            "data/published/NYCGovernanceOrganizations_v0_3.csv)"
        ),
    )
    parser.add_argument(
        "--output_report_csv",
        type=Path,
        required=True,
        help=(
            "Path to save the CSV report detailing the comparison (e.g., "
            "data/audit/dataset_comparison_report.csv)"
        ),
    )

    args = parser.parse_args()
    compare_datasets(args.original_csv, args.processed_csv, args.output_report_csv)


if __name__ == "__main__":
    main()
