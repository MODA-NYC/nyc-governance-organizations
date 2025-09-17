#!/usr/bin/env python3
"""
manage_schema.py - A tool for managing structural schema changes to CSV files.

This script provides functionality to modify the schema of CSV files, starting with
the ability to add new columns with default values.
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


def add_columns_to_csv(input_csv, output_csv, new_columns, default_value=""):
    """
    Add new columns to a CSV file.

    Args:
        input_csv (Path): Path to the input CSV file
        output_csv (Path): Path to save the modified CSV file
        new_columns (list): List of column names to add
        default_value (str): Default value for new columns

    Returns:
        tuple: (added_columns, skipped_columns)
    """
    # Load the CSV file
    print(f"Loading CSV from: {input_csv}")
    df = pd.read_csv(input_csv, encoding="utf-8-sig")

    # Track which columns were added and which were skipped
    added_columns = []
    skipped_columns = []

    # Process each new column
    for column_name in new_columns:
        column_name = column_name.strip()  # Remove any whitespace

        if column_name in df.columns:
            print(f"⚠️  Warning: Column '{column_name}' already exists. Skipping...")
            skipped_columns.append(column_name)
        else:
            msg = f"✓ Adding column: '{column_name}'"
            print(f"{msg} with default value: '{default_value}'")
            df[column_name] = default_value
            added_columns.append(column_name)

    # Save the modified DataFrame
    print(f"\nSaving modified CSV to: {output_csv}")
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    return added_columns, skipped_columns


def parse_column_list(columns_string):
    """
    Parse a comma-separated string of column names into a list.

    Args:
        columns_string (str): Comma-separated column names

    Returns:
        list: List of column names
    """
    return [col.strip() for col in columns_string.split(",") if col.strip()]


def setup_argparser():
    """Set up and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Manage structural schema changes to CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single column with default empty string
  python manage_schema.py --input_csv data.csv \\
    --output_csv data_modified.csv --add_columns "NewColumn"

  # Add multiple columns with default value
  python manage_schema.py --input_csv data.csv \\
    --output_csv data_modified.csv \\
    --add_columns "Column1,Column2,Column3" --default_value "N/A"

  # Add columns with None/NaN as default
  python manage_schema.py --input_csv data.csv \\
    --output_csv data_modified.csv \\
    --add_columns "Score,Rating" --default_value "None"
        """,
    )

    # Define command-line arguments
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="Path to the input CSV file whose schema will be modified",
    )

    parser.add_argument(
        "--output_csv",
        type=str,
        required=True,
        help="Path to save the CSV file with the new schema",
    )

    parser.add_argument(
        "--add_columns",
        type=str,
        required=True,
        help="Comma-separated string of new column names to add",
    )

    parser.add_argument(
        "--default_value",
        type=str,
        default="",
        help='Default value to fill in the new columns (default: empty string "")',
    )

    return parser


def print_summary(added, skipped, input_path, output_path):
    """Print a summary of the changes made."""
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if added:
        print(f"✅ Successfully added {len(added)} column(s):")
        for col in added:
            print(f"   - {col}")

    if skipped:
        print(f"\n⚠️  Skipped {len(skipped)} existing column(s):")
        for col in skipped:
            print(f"   - {col}")

    print("\n✅ Schema modification complete!")
    print(f"   Output saved to: {output_path}")

    # Optional: Log the changes (simple console logging for now)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n📝 Change log:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_path}")
    if added:
        print(f"   Added columns: {', '.join(added)}")
    if skipped:
        print(f"   Skipped columns: {', '.join(skipped)}")


def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = setup_argparser()
    args = parser.parse_args()

    # Convert paths to Path objects
    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    # Validate input file exists
    if not input_path.exists():
        print(f"❌ Error: Input file '{input_path}' does not exist.")
        return 1

    # Parse column names
    new_columns = parse_column_list(args.add_columns)

    if not new_columns:
        print("❌ Error: No valid column names provided.")
        return 1

    # Process default value
    default_value = args.default_value
    if default_value.lower() == "none":
        default_value = None  # This will become NaN in pandas

    # Print initial information
    print(f"\n{'='*60}")
    print("Schema Management Tool - Add Columns")
    print(f"{'='*60}")
    print(f"Input CSV: {input_path}")
    print(f"Output CSV: {output_path}")
    print(f"Columns to add: {', '.join(new_columns)}")
    default_display = "None (NaN)" if default_value is None else repr(default_value)
    print(f"Default value: {default_display}")
    print(f"{'='*60}\n")

    try:
        # Add columns to the CSV
        added, skipped = add_columns_to_csv(
            input_path, output_path, new_columns, default_value
        )

        # Print summary of changes
        print_summary(added, skipped, input_path, output_path)
        return 0

    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
