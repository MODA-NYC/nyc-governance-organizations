#!/usr/bin/env python3
"""
Validate NYCGO release assets against the Table Schema.

Validates CSV files against the Frictionless Table Schema and produces
a machine-readable validation report for downstream consumers.

Usage:
    python scripts/validate_release_asset.py \
        --input path/to/output.csv \
        --schema schemas/nycgo_golden_dataset.tableschema.json \
        --out validation_report.json

Exit codes:
    0 - Validation passed
    1 - Validation failed
    2 - Script error (file not found, etc.)
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_schema_hash(schema: dict) -> str:
    """Compute a hash of the schema for versioning."""
    schema_str = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:12]


def is_valid_url(value: str) -> bool:
    """Check if a string is a valid URL."""
    if not value or pd.isna(value) or value.strip() == "":
        return True  # Empty is allowed (optional field)
    try:
        result = urlparse(value.strip())
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def validate_csv(  # noqa: C901
    csv_path: str, schema: dict, warnings_as_errors: bool = False
) -> dict:
    """
    Validate a CSV file against a Frictionless Table Schema.

    Returns a validation report dict.
    """
    errors: list[dict] = []
    warnings: list[dict] = []
    checks: list[dict] = []

    # Load CSV
    try:
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        checks.append(
            {
                "name": "file_parseable",
                "passed": True,
                "message": "CSV parsed successfully",
            }
        )
    except Exception as e:
        return {
            "valid": False,
            "checks": [{"name": "file_parseable", "passed": False, "message": str(e)}],
            "errors": [
                {"check": "file_parseable", "message": f"Failed to parse CSV: {e}"}
            ],
            "warnings": [],
        }

    # Build field lookup from schema
    schema_fields = {f["name"]: f for f in schema.get("fields", [])}
    expected_columns = list(schema_fields.keys())

    # Check 1: Row count > 0
    row_count = len(df)
    if row_count > 0:
        checks.append(
            {
                "name": "row_count_positive",
                "passed": True,
                "message": f"Row count: {row_count}",
            }
        )
    else:
        checks.append(
            {"name": "row_count_positive", "passed": False, "message": "CSV has 0 rows"}
        )
        errors.append(
            {"check": "row_count_positive", "message": "Dataset contains no records"}
        )

    # Check 2: Required columns present
    actual_columns = list(df.columns)
    missing_columns = set(expected_columns) - set(actual_columns)
    extra_columns = set(actual_columns) - set(expected_columns)

    if not missing_columns:
        checks.append(
            {
                "name": "required_columns_present",
                "passed": True,
                "message": f"All {len(expected_columns)} expected columns present",
            }
        )
    else:
        checks.append(
            {
                "name": "required_columns_present",
                "passed": False,
                "message": f"Missing columns: {sorted(missing_columns)}",
            }
        )
        missing_list = sorted(missing_columns)
        errors.append(
            {
                "check": "required_columns_present",
                "message": f"Missing {len(missing_columns)} columns: {missing_list}",
            }
        )

    if extra_columns:
        warnings.append(
            {
                "check": "extra_columns",
                "message": f"Unexpected columns in CSV: {sorted(extra_columns)}",
            }
        )

    # Check 3: Column order matches schema
    if actual_columns == expected_columns:
        checks.append(
            {
                "name": "column_order",
                "passed": True,
                "message": "Column order matches schema",
            }
        )
    else:
        # Not a hard error, just a warning
        checks.append(
            {
                "name": "column_order",
                "passed": True,
                "message": "Column order differs from schema (not enforced)",
            }
        )
        warnings.append(
            {
                "check": "column_order",
                "message": "Column order differs from schema definition",
            }
        )

    # Check 4: Primary key uniqueness
    primary_key = schema.get("primaryKey")
    if primary_key and primary_key in df.columns:
        duplicates = df[df[primary_key].duplicated(keep=False)]
        if len(duplicates) == 0:
            checks.append(
                {
                    "name": "primary_key_unique",
                    "passed": True,
                    "message": f"All {row_count} {primary_key} values are unique",
                }
            )
        else:
            dup_values = duplicates[primary_key].unique().tolist()[:10]
            checks.append(
                {
                    "name": "primary_key_unique",
                    "passed": False,
                    "message": f"Found {len(duplicates)} duplicate primary keys",
                }
            )
            errors.append(
                {
                    "check": "primary_key_unique",
                    "field": primary_key,
                    "message": f"Duplicate primary key values: {dup_values}",
                    "row_count": len(duplicates),
                }
            )

    # Check 5: Required fields not empty
    required_fields = [
        f["name"]
        for f in schema.get("fields", [])
        if f.get("constraints", {}).get("required", False)
    ]
    for field in required_fields:
        if field not in df.columns:
            continue
        empty_mask = df[field].isna() | (df[field].str.strip() == "")
        empty_count = empty_mask.sum()
        if empty_count == 0:
            checks.append(
                {
                    "name": f"required_field_{field}",
                    "passed": True,
                    "message": f"Field '{field}' has no empty values",
                }
            )
        else:
            empty_rows = df[empty_mask].index.tolist()[:10]
            checks.append(
                {
                    "name": f"required_field_{field}",
                    "passed": False,
                    "message": f"Field '{field}' has {empty_count} empty values",
                }
            )
            msg = f"Required field '{field}' has {empty_count} empty values"
            errors.append(
                {
                    "check": "required_field_not_empty",
                    "field": field,
                    "message": msg,
                    "sample_rows": empty_rows,
                }
            )

    # Check 6: Pattern validation (regex)
    for field_def in schema.get("fields", []):
        field_name = field_def["name"]
        if field_name not in df.columns:
            continue
        pattern = field_def.get("constraints", {}).get("pattern")
        if pattern:
            non_empty = df[field_name][df[field_name].str.strip() != ""]
            invalid_mask = ~non_empty.str.match(pattern, na=False)
            invalid_count = invalid_mask.sum()
            if invalid_count == 0:
                checks.append(
                    {
                        "name": f"pattern_{field_name}",
                        "passed": True,
                        "message": f"Field '{field_name}' matches pattern",
                    }
                )
            else:
                invalid_values = non_empty[invalid_mask].head(5).tolist()
                pattern_msg = (
                    f"Field '{field_name}' has {invalid_count} "
                    "values not matching pattern"
                )
                checks.append(
                    {
                        "name": f"pattern_{field_name}",
                        "passed": False,
                        "message": pattern_msg,
                    }
                )
                errors.append(
                    {
                        "check": "pattern_validation",
                        "field": field_name,
                        "pattern": pattern,
                        "message": pattern_msg,
                        "sample_invalid": invalid_values,
                    }
                )

    # Check 7: Enum validation
    for field_def in schema.get("fields", []):
        field_name = field_def["name"]
        if field_name not in df.columns:
            continue
        enum_values = field_def.get("constraints", {}).get("enum")
        if enum_values:
            actual_values = df[field_name].unique()
            invalid_values = [v for v in actual_values if v not in enum_values]
            if not invalid_values:
                checks.append(
                    {
                        "name": f"enum_{field_name}",
                        "passed": True,
                        "message": f"Field '{field_name}' has valid enum values",
                    }
                )
            else:
                num_invalid = len(invalid_values)
                enum_msg = f"Field '{field_name}' has {num_invalid} bad enums"
                checks.append(
                    {
                        "name": f"enum_{field_name}",
                        "passed": False,
                        "message": enum_msg,
                    }
                )
                sample_invalid = invalid_values[:5]
                errors.append(
                    {
                        "check": "enum_validation",
                        "field": field_name,
                        "allowed": enum_values,
                        "invalid": invalid_values[:10],
                        "message": f"Bad enums in '{field_name}': {sample_invalid}",
                    }
                )

    # Check 8: URL format validation (warnings only - data quality, not structural)
    url_fields = [
        f["name"] for f in schema.get("fields", []) if f.get("format") == "uri"
    ]
    for field_name in url_fields:
        if field_name not in df.columns:
            continue
        non_empty = df[field_name][df[field_name].str.strip() != ""]
        invalid_urls = non_empty[~non_empty.apply(is_valid_url)]
        if len(invalid_urls) == 0:
            checks.append(
                {
                    "name": f"url_format_{field_name}",
                    "passed": True,
                    "message": f"Field '{field_name}' contains valid URLs",
                }
            )
        else:
            sample_invalid = invalid_urls.head(5).tolist()
            num_invalid = len(invalid_urls)
            # URL format issues are warnings, not errors (data quality)
            checks.append(
                {
                    "name": f"url_format_{field_name}",
                    "passed": True,
                    "message": f"Field '{field_name}' has {num_invalid} bad URLs",
                }
            )
            warnings.append(
                {
                    "check": "url_format",
                    "field": field_name,
                    "message": f"Field '{field_name}' has {num_invalid} invalid URLs",
                    "sample_invalid": sample_invalid,
                }
            )

    # Compute final validity
    check_failures = [c for c in checks if not c["passed"]]
    valid = len(check_failures) == 0
    if warnings_as_errors and warnings:
        valid = False

    return {
        "valid": valid,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "total_checks": len(checks),
            "passed_checks": len([c for c in checks if c["passed"]]),
            "failed_checks": len(check_failures),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }


def create_validation_report(
    csv_path: str,
    schema_path: str,
    schema: dict,
    validation_result: dict,
    version: str | None = None,
) -> dict:
    """Create the full validation report with metadata."""
    csv_path_obj = Path(csv_path)
    file_size = csv_path_obj.stat().st_size
    sha256 = compute_sha256(csv_path)
    schema_hash = compute_schema_hash(schema)

    # Count rows
    try:
        df = pd.read_csv(csv_path, dtype=str)
        row_count = len(df)
        column_count = len(df.columns)
    except Exception:
        row_count = 0
        column_count = 0

    report = {
        "validation_report_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": schema.get("name", "unknown"),
            "title": schema.get("title", ""),
            "schema_version": schema.get("version", "unknown"),
            "schema_hash": schema_hash,
            "version": version,
        },
        "asset": {
            "filename": csv_path_obj.name,
            "filepath": str(csv_path),
            "sha256": sha256,
            "size_bytes": file_size,
            "row_count": row_count,
            "column_count": column_count,
        },
        "schema": {
            "filepath": schema_path,
            "field_count": len(schema.get("fields", [])),
        },
        "valid": validation_result["valid"],
        "summary": validation_result.get("stats", {}),
        "checks": validation_result["checks"],
        "errors": validation_result["errors"],
        "warnings": validation_result["warnings"],
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate NYCGO release assets against schema"
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to CSV file to validate"
    )
    parser.add_argument(
        "--schema", "-s", required=True, help="Path to Table Schema JSON file"
    )
    parser.add_argument(
        "--out", "-o", required=True, help="Path to write validation report JSON"
    )
    parser.add_argument("--version", "-v", help="Version string to include in report")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    args = parser.parse_args()

    # Verify input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    # Verify schema file exists
    if not os.path.exists(args.schema):
        print(f"Error: Schema file not found: {args.schema}", file=sys.stderr)
        sys.exit(2)

    # Load schema
    try:
        with open(args.schema) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}", file=sys.stderr)
        sys.exit(2)

    # Run validation
    print(f"Validating: {args.input}")
    print(f"Schema: {args.schema}")

    validation_result = validate_csv(args.input, schema, warnings_as_errors=args.strict)

    # Create report
    report = create_validation_report(
        csv_path=args.input,
        schema_path=args.schema,
        schema=schema,
        validation_result=validation_result,
        version=args.version,
    )

    # Write report
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report written to: {args.out}")

    # Print summary
    print()
    print("=" * 60)
    if report["valid"]:
        print("VALIDATION PASSED")
    else:
        print("VALIDATION FAILED")
    print("=" * 60)
    passed = report["summary"]["passed_checks"]
    total = report["summary"]["total_checks"]
    print(f"  Checks: {passed}/{total} passed")
    print(f"  Errors: {report['summary']['error_count']}")
    print(f"  Warnings: {report['summary']['warning_count']}")
    print(f"  Rows: {report['asset']['row_count']}")
    print(f"  SHA-256: {report['asset']['sha256']}")
    print()

    if not report["valid"]:
        print("Errors:")
        for error in report["errors"]:
            print(f"  - [{error.get('check', 'unknown')}] {error['message']}")
        print()

    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - [{warning.get('check', 'unknown')}] {warning['message']}")
        print()

    # Exit with appropriate code
    sys.exit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
