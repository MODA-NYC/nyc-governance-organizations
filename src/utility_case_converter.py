import argparse
import pathlib

import pandas as pd


def to_pascal_case(snake_case_str: str) -> str:
    """Converts a snake_case string to PascalCase."""
    if not isinstance(snake_case_str, str):
        return ""
    return "".join(word.capitalize() for word in snake_case_str.split("_"))


def main():
    """Main function to run the case conversion."""
    parser = argparse.ArgumentParser(
        description=(
            "Converts the 'Column' field of an edits CSV from snake_case to "
            "PascalCase."
        )
    )
    parser.add_argument(
        "--input_csv",
        required=True,
        type=pathlib.Path,
        help="Path to the input edits CSV with snake_case columns.",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        type=pathlib.Path,
        help="Path to save the output edits CSV with PascalCase columns.",
    )
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_csv, dtype=str)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_csv}'")
        return

    if "Column" not in df.columns:
        print("Error: 'Column' field not found in the input CSV.")
        return

    # Apply the conversion
    df["Column"] = df["Column"].apply(to_pascal_case)

    # Special handling for 'name_alphabetized' which doesn't follow the rule
    df["Column"] = df["Column"].replace({"NameAlphabetized": "NameAlphabetized"})

    print(f"Successfully converted {len(df)} rows.")

    try:
        df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
        print(f"Saved pipeline-ready file to: {args.output_csv}")
    except Exception as e:
        print(f"Error saving output file: {e}")


if __name__ == "__main__":
    main()
