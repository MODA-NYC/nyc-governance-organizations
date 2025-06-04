import argparse
import pathlib
import re
import sys

import pandas as pd


def to_snake_case(name: str) -> str:
    """
    Convert a PascalCase or CamelCase string to snake_case.
    Handles cases like 'RecordID' -> 'record_id' and
    'PrincipalOfficerFirstName' -> 'principal_officer_first_name'.
    """
    # Insert an underscore before any uppercase letter that is
    # preceded by a lowercase letter or digit, or that is followed
    # by a lowercase letter and preceded by another uppercase letter
    # (e.g. ABBRSomething -> ABBR_Something)
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    # Insert an underscore before any uppercase letter that is
    # followed by a lowercase letter, and is not at the beginning
    # of the string (if the string starts with multiple uppercase,
    # e.g. IDName -> ID_Name)
    s2 = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s1)
    return s2.lower()


def main():
    """
    Main function to process the dataset.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Processes a dataset CSV: renames columns, selects specific columns, "
            "converts headers to snake_case, and saves the output."
        )
    )
    parser.add_argument(
        "--input_csv",
        required=True,
        type=pathlib.Path,
        help="Path to the final processed dataset CSV.",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        type=pathlib.Path,
        help="Path to save the final, versioned, published dataset.",
    )

    args = parser.parse_args()

    # Load Input CSV
    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV file '{args.input_csv}': {e}")
        sys.exit(1)

    # Verify and Perform Hardcoded Column Renames
    rename_map = {
        "PrincipalOfficerGivenName": "PrincipalOfficerFirstName",
        "PrincipalOfficerFamilyName": "PrincipalOfficerLastName",
    }

    for old_name, new_name in rename_map.items():
        if old_name not in df.columns:
            print(
                f"Error: Expected column '{old_name}' not found in "
                f"input CSV '{args.input_csv}'."
            )
            sys.exit(1)
        df.rename(columns={old_name: new_name}, inplace=True)
        print(f"Renamed column '{old_name}' to '{new_name}'.")

    # Filter by InOrgChart column
    in_org_chart_col = "InOrgChart"
    if in_org_chart_col in df.columns:
        print(f"Filtering by column '{in_org_chart_col}'.")
        rows_before_filter = len(df)
        # Convert to string, lowercase, then map to boolean
        # Handles actual booleans, strings 'True'/'False' (case-insensitive),
        # and treats NaN/empty/other as False.
        df[in_org_chart_col] = (
            df[in_org_chart_col]
            .astype(str)
            .str.lower()
            .map({"true": True})
            .fillna(False)
        )
        df = df[df[in_org_chart_col]].copy()
        rows_after_filter = len(df)
        print(
            f"Kept {rows_after_filter} rows out of {rows_before_filter} "
            f"after filtering by '{in_org_chart_col}' == True."
        )
        if rows_after_filter == 0:
            print(
                f"Warning: No rows remained after filtering by '{in_org_chart_col}'. "
                "Output CSV will be empty or have only headers."
            )
    else:
        print(
            f"Warning: Column '{in_org_chart_col}' not found in input CSV. "
            "Proceeding without filtering by this column."
        )

    # Define and Verify Hardcoded Column Selection and Order
    required_output_columns = [
        "RecordID",
        "Name",
        "NameAlphabetized",
        "OperationalStatus",
        "OrganizationType",
        "Description",
        "URL",
        "AlternateOrFormerNames",
        "Acronym",
        "AlternateOrFormerAcronyms",
        "BudgetCode",
        "OpenDatasetsURL",
        "FoundingYear",
        "PrincipalOfficerFirstName",  # New name
        "PrincipalOfficerLastName",  # New name
        "PrincipalOfficerTitle",
        "PrincipalOfficerContactURL",
        "InOrgChart",
        "ReportsTo",
    ]

    missing_columns = [col for col in required_output_columns if col not in df.columns]
    if missing_columns:
        print(
            f"Error: The following expected columns are missing from the input CSV "
            f"'{args.input_csv}' (after renames): {', '.join(missing_columns)}"
        )
        sys.exit(1)

    # Create a new DataFrame with selected columns in the specified order
    try:
        df_selected = df[required_output_columns].copy()
    except KeyError as e:
        # This should ideally be caught by the missing_columns check above,
        # but as an extra precaution:
        print(
            f"Error during column selection: {e}. "
            "This indicates an unexpected issue."
        )
        sys.exit(1)

    # Convert All Selected Column Headers to Snake Case
    df_selected.columns = [to_snake_case(col) for col in df_selected.columns]
    print("Converted all selected column headers to snake_case.")

    # Save Output CSV
    try:
        # Ensure output directory exists
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        df_selected.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"Error saving output CSV to '{args.output_csv}': {e}")
        sys.exit(1)

    print(f"Successfully exported dataset to '{args.output_csv}'")


if __name__ == "__main__":
    main()
