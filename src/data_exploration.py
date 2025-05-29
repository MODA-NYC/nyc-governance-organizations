import re
from collections import Counter

import pandas as pd

# 1. Define file paths
golden_dataset_path = "data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv"
qa_dataset_path = "data/input/Agency_Name_QA_Edits.csv"

# Initialize variables for markdown in case of file load errors
golden_rows_val = "N/A"
golden_cols_list = "N/A"
golden_nulls_str_md = (
    "    *   Could not determine missing values (dataset might not have loaded or an"
    " error occurred).\n"
)
golden_org_chart_counts_str_md = (
    "    *   Data for 'Jan 2025 Org Chart' not available (column not found,"
    " dataset not loaded, or an error occurred).\n"
)

qa_rows_val = "N/A"
qa_cols_list_md = "N/A"
qa_column_counts_str_md = (
    "    *   Could not determine QA target columns (dataset not loaded, 'Column'"
    " field missing, or an error occurred).\n"
)
most_common_words_str_md = (
    "    *   Could not determine common feedback types (dataset not loaded,"
    " 'Feedback' field missing/empty, or an error occurred).\n"
)


print("--- Data Exploration Script ---")

# 2. Load and Analyze Golden Dataset
print("\n--- Golden Dataset Analysis ---")
try:
    golden_df = pd.read_csv(golden_dataset_path)
    print(f"Total rows: {len(golden_df)}")
    golden_rows_val = len(golden_df)

    print(f"Column names: {golden_df.columns.tolist()}")
    golden_cols_list = golden_df.columns.tolist()

    print("\nNull value counts per column:")
    null_counts = golden_df.isnull().sum()
    print(null_counts)

    temp_golden_nulls_str = ""
    significant_nulls = null_counts[null_counts > 0].sort_values(ascending=False)
    if not significant_nulls.empty:
        for col, count in significant_nulls.head(5).items():  # Top 5 or all if fewer
            temp_golden_nulls_str += (
                f"    *   `{col}`: {count} missing values "
                f"({count / golden_rows_val * 100:.2f}%)\n"
            )
    else:
        temp_golden_nulls_str = "    *   No missing values found.\n"
    golden_nulls_str_md = temp_golden_nulls_str

    print("\nValue counts for 'Jan 2025 Org Chart':")
    if "Jan 2025 Org Chart" in golden_df.columns:
        org_chart_counts = golden_df["Jan 2025 Org Chart"].value_counts(dropna=False)
        print(org_chart_counts)

        temp_golden_org_chart_str = ""
        for value, count in org_chart_counts.items():
            temp_golden_org_chart_str += f"    *   `{value}`: {count} occurrences\n"

        if not org_chart_counts.empty:
            # Handle potential NaN/None keys from value_counts
            counts_dict = {
                str(k) if pd.isna(k) else k: v for k, v in org_chart_counts.items()
            }
            true_count = counts_dict.get(True, 0)
            false_count = counts_dict.get(False, 0)
            nan_count = counts_dict.get("nan", 0) + counts_dict.get("None", 0)

            if true_count > 0 or false_count > 0:  # Check if boolean values are primary
                most_common_val = org_chart_counts.idxmax()
                summary_line = (
                    f"    *   Counts - True: {true_count}, False: {false_count},"
                    f" NaN/Missing: {nan_count}. "
                )
                if pd.isna(most_common_val):
                    summary_line += "The most common category is missing/NaN.\n"
                elif isinstance(most_common_val, bool):
                    summary_line += (
                        f"Most organizations appear to be "
                        f"{'included' if most_common_val is True else 'excluded'}"
                        f" in the Jan 2025 Org Chart.\n"
                    )
                else:  # Non-boolean, non-NaN max
                    summary_line += f"The most common value is `{most_common_val}`.\n"
                temp_golden_org_chart_str += summary_line
            else:  # Only NaNs or other string values
                temp_golden_org_chart_str += (
                    f"    *   The column contains non-boolean data or is mostly empty."
                    f" (NaN/Missing: {nan_count})\n"
                )

        golden_org_chart_counts_str_md = temp_golden_org_chart_str
    else:
        print("'Jan 2025 Org Chart' column not found.")
        golden_org_chart_counts_str_md = (
            "    *   'Jan 2025 Org Chart' column not found.\n"
        )

except FileNotFoundError:
    print(f"Error: Golden dataset not found at {golden_dataset_path}")
except Exception as e:
    print(f"An error occurred while processing the golden dataset: {e}")
    golden_nulls_str_md = f"    *   An error occurred: {e}\n"
    golden_org_chart_counts_str_md = f"    *   An error occurred: {e}\n"


# 3. Load and Analyze QA Dataset
print("\n--- QA Dataset Analysis ---")
try:
    qa_df = pd.read_csv(qa_dataset_path)
    print(f"Total rows: {len(qa_df)}")
    qa_rows_val = len(qa_df)

    print(f"Column names: {qa_df.columns.tolist()}")
    qa_cols_list_md = qa_df.columns.tolist()

    if "Column" in qa_df.columns:
        print("\nUnique values in 'Column':")
        unique_qa_columns = qa_df["Column"].unique()
        print(unique_qa_columns)

        qa_column_counts = qa_df["Column"].value_counts()
        temp_qa_col_counts_str = ""
        for col, count in qa_column_counts.head(5).items():  # Top 5
            temp_qa_col_counts_str += f"    *   `{col}`: {count} times\n"
        qa_column_counts_str_md = (
            temp_qa_col_counts_str
            if temp_qa_col_counts_str
            else "    *   No data for 'Column' value counts.\n"
        )
    else:
        print("'Column' column not found.")
        qa_column_counts_str_md = "    *   'Column' field not found in QA dataset.\n"

    if "Feedback" in qa_df.columns:
        print("\nTen most common words in 'Feedback':")
        # Ensure 'Feedback' is string, handle NaN by dropping, then join.
        all_feedback_text = " ".join(qa_df["Feedback"].dropna().astype(str))
        all_feedback_text_lower = all_feedback_text.lower()
        # Remove punctuation, keep alphanumeric and spaces
        all_feedback_text_cleaned = re.sub(r"[^\w\s]", "", all_feedback_text_lower)
        words = all_feedback_text_cleaned.split()

        # Basic stop words list
        stop_words = {
            "the",
            "is",
            "a",
            "to",
            "of",
            "and",
            "in",
            "for",
            "with",
            "on",
            "an",
            "it",
            "this",
            "not",
            "be",
            "are",
            "has",
            "we",
            "or",
            "all",
            "if",
            "do",
            "should",
            "can",
        }
        # Filter words: not in stop_words and length > 2
        filtered_words = [
            word
            for word in words
            if word.strip() and word not in stop_words and len(word) > 2
        ]

        word_counts = Counter(filtered_words)
        most_common_words = word_counts.most_common(10)
        print(most_common_words)

        temp_most_common_str = ""
        if most_common_words:
            for phrase, count in most_common_words:
                temp_most_common_str += f"    *   `{phrase}` (appears {count} times)\n"
            temp_most_common_str += (
                "    *   Common themes from these words might relate to data quality"
                " (e.g., 'missing', 'fix', 'error'), specific fields ('name',"
                " 'description', 'officer'), or entities ('mayor', 'office').\n"
            )
        else:
            temp_most_common_str = (
                "    *   No common words found after filtering or 'Feedback' column is"
                " empty/non-informative.\n"
            )
        most_common_words_str_md = temp_most_common_str
    else:
        print("'Feedback' column not found.")
        most_common_words_str_md = "    *   'Feedback' field not found in QA dataset.\n"

except FileNotFoundError:
    print(f"Error: QA dataset not found at {qa_dataset_path}")
except Exception as e:
    print(f"An error occurred while processing the QA dataset: {e}")
    qa_column_counts_str_md = f"    *   An error occurred: {e}\n"
    most_common_words_str_md = f"    *   An error occurred: {e}\n"


# 4. Print Observations as Markdown
markdown_observations = (
    f"---\n"
    f"Observations (Markdown)\n"
    f"---\n\n"
    f"### Golden Dataset (`{golden_dataset_path}`)\n\n"
    f"*   **Total Rows:** {golden_rows_val}\n"
    f"*   **Column Names:** {golden_cols_list}\n"
    f"*   **Columns with Missing Values (Top 5 or as available if significant):**\n"
    f"{golden_nulls_str_md}"
    f"*   **'Jan 2025 Org Chart' Column Insights:**\n"
    f"{golden_org_chart_counts_str_md}\n\n"
    f"### QA Dataset (`{qa_dataset_path}`)\n\n"
    f"*   **Total Rows:** {qa_rows_val}\n"
    f"*   **Column Names:** {qa_cols_list_md}\n"
    f"*   **Columns Most Frequently Targeted for QA (Top 5 or as available):**\n"
    f"{qa_column_counts_str_md}"
    f"*   **Most Typical Types of Feedback/Requested Changes "
    f"(Top 10 common words from 'Feedback' column):**\n"
    f"{most_common_words_str_md}"
)

print(markdown_observations)
