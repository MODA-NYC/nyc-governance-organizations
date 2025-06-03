import io
import sys  # For capturing stderr

import pandas as pd

# Target file
target_csv_file = "data/output/intermediate_golden.csv"
num_rows_to_read = 15

print(
    f"--- Testing with default pandas read (nrows={num_rows_to_read}) "
    f"on file: {target_csv_file} ---"
)
try:
    df_default = pd.read_csv(target_csv_file, nrows=num_rows_to_read)
    print(f"Default read successful. DataFrame shape: {df_default.shape}")
    # print(df_default.head(num_rows_to_read))
except Exception as e:
    print(f"Default read failed: {e}")

print(
    f"\n--- Testing with engine='python' (nrows={num_rows_to_read}) "
    f"on file: {target_csv_file} ---"
)
try:
    df_python_engine = pd.read_csv(
        target_csv_file, nrows=num_rows_to_read, engine="python"
    )
    print(f"Python engine read successful. DataFrame shape: {df_python_engine.shape}")
    # print(df_python_engine.head(num_rows_to_read))
except Exception as e:
    print(f"Python engine read failed: {e}")

print(
    f"\n--- Testing with on_bad_lines='warn' (nrows={num_rows_to_read}) "
    f"on file: {target_csv_file} ---"
)
# Capture stderr to check for warnings
old_stderr = sys.stderr
sys.stderr = captured_stderr = io.StringIO()
try:
    df_warn_bad_lines = pd.read_csv(
        target_csv_file, nrows=num_rows_to_read, on_bad_lines="warn"
    )
    print(
        f"on_bad_lines='warn' read attempt. DataFrame shape: "
        f"{df_warn_bad_lines.shape}"
    )
    # print(df_warn_bad_lines.head(num_rows_to_read))
except Exception as e:
    print(f"on_bad_lines='warn' read failed: {e}")
finally:
    sys.stderr = old_stderr  # Restore stderr
    warnings_output = captured_stderr.getvalue()
    if warnings_output:
        print("Stderr warnings captured:")
        print(warnings_output)
    else:
        print("No warnings captured on stderr.")
