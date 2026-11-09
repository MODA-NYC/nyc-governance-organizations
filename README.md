# NYC Agencies and Governance Organizations

An analysis-ready reference of NYC agencies and governance organizations—standardized names, acronyms, principal officers, reporting lines, and stable IDs—powering the Agency Directory on nyc.gov.

### Quick links
- **Dataset on NYC Open Data (t3jq-9nkf)**: [NYC Agencies and Governance Organizations](https://data.cityofnewyork.us/d/t3jq-9nkf/)
- **Feedback & corrections (Airtable form)**: [Submit a change request](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form)
- **Releases**: [GitHub Releases](https://github.com/MODA-NYC/nyc-governance-organizations/releases) (latest: [`releases/latest`](https://github.com/MODA-NYC/nyc-governance-organizations/releases/latest))
- **Schema**: [`docs/SCHEMA.md`](docs/SCHEMA.md) and the [data dictionary](docs/NYC_Agencies_and_Governance_Organizations_Data_Dictionary.xlsx)
- **Pipeline diagram**: [View interactive BPMN](https://moda-nyc.github.io/nyc-governance-organizations/nycgo-edit-publish-pipeline-standalone.html) | [Mermaid version](docs/nycgo-edit-publish-pipeline.mermaid.md)
- **AI usage**: [`AI_USAGE.md`](AI_USAGE.md)
- **Maintenance runbook**: [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md)
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Overview
NYC Agencies and Governance Organizations is a standardized reference list of NYC agencies and other governance organizations. It standardizes official names, acronyms, leadership, and reporting relationships so New Yorkers—and City staff—can speak the same language about government. It consolidates the citywide organizational chart into a single, analysis-ready table and powers the revamped Agency Directory on nyc.gov, which presents a curated subset of these records for public browsing.

Each record is included in at least one of two authoritative sources: the Citywide Org Chart or an internal list of NYC governance organizations maintained by the Mayor’s Office of Operations. Each record includes the organization’s preferred and alternate names, acronyms, type classification, operational status, principal officer information, reporting relationship, official website, and directory-inclusion flags. All organizations in this dataset are formally established through a legal or administrative instrument, such as an NYC Charter provision, Mayoral Executive Order, or local or state enabling statute.

To make this data publicly available, we built a repeatable publication pipeline with rule-based cleaning, Unicode/encoding fixes, name parsing, de-duplication, and a comprehensive audit trail of every change. The dataset can be paired with budgets, contracts, performance metrics, or program datasets to analyze services and accountability across City government. The dataset and the crosswalk in this repository are designed to help combine other datasets that use legacy names or system-specific codes.

## The dataset

The dataset exists in two forms:

| Form | Fields | Records | File |
|------|--------|---------|------|
| **Golden dataset** | 38 | All records, including inactive and dissolved organizations | [`data/published/latest/NYCGO_golden_dataset_latest.csv`](data/published/latest/NYCGO_golden_dataset_latest.csv) |
| **Published dataset** | 17 | Active records only (see below) | [`data/published/latest/NYCGovernanceOrganizations_latest.csv`](data/published/latest/NYCGovernanceOrganizations_latest.csv) |

- **Primary key**: `record_id`, format `NYC_GOID_XXXXXX` (e.g., `NYC_GOID_000318`). IDs are stable.
- **Column names**: snake_case.
- **Current record counts**: see `counts` in [`data/published/latest/run_summary.json`](data/published/latest/run_summary.json).
- **Which records are published**: a record is in the published dataset when its `operational_status` is `Active` and it is in the citywide org chart or on the Mayor's Office of Operations list. A small number of named exceptions are set in [`scripts/process/export_dataset.py`](scripts/process/export_dataset.py).
- **Which records appear on nyc.gov**: the `listed_in_nyc_gov_agency_directory` flag marks the subset shown in the Agency Directory. The rules are documented in [`docs/DIRECTORY_LOGIC.md`](docs/DIRECTORY_LOGIC.md).

### Published schema (17 fields)

| Field | Description |
|-------|-------------|
| record_id | Stable internal identifier (immutable primary key) |
| name | Official/preferred name |
| name_alphabetized | Name normalized for alphabetical sorting |
| operational_status | Current status of the organization |
| organization_type | Category (e.g., Mayoral Agency, Advisory or Regulatory Organization) |
| url | Official website URL |
| alternate_or_former_names | Other names seen in official sources (semicolon-separated) |
| acronym | Official acronym (if any) |
| alternate_or_former_acronyms | Other acronyms seen in official sources |
| principal_officer_full_name | Full name of the principal officer |
| principal_officer_first_name | First name (derived from the full name) |
| principal_officer_last_name | Last name (derived from the full name) |
| principal_officer_title | Title of the principal officer |
| principal_officer_contact_url | Profile/contact page for the principal officer |
| reports_to | Reporting, administrative, or oversight relationship |
| in_org_chart | Whether the organization appears in the citywide org chart |
| listed_in_nyc_gov_agency_directory | Computed flag: whether the record appears in the nyc.gov Agency Directory |

All 38 golden fields are listed in [`docs/SCHEMA.md`](docs/SCHEMA.md).

### Schema expansion (deferred)

A larger schema ("Phase II": governance structure, legal authority, and parent-organization fields) was designed and is deferred. See [`docs/sprints/PHASE_II.md`](docs/sprints/PHASE_II.md). The `configs/`, `skills/`, and `.env.template` files in this repository belong to that work and are not needed to run the pipeline.

## How the dataset is updated

1. An authorized editor submits a change in the Admin UI with a justification and, where available, an evidence URL.
2. The editor commits the generated edit file under their own GitHub account.
3. A GitHub Actions workflow runs the pipeline on the edit: rule-based cleaning, name parsing, directory-eligibility rules, and schema validation.
4. If validation passes, a versioned GitHub Release is published and each field change is appended to [`data/changelog.csv`](data/changelog.csv) with who, when, why, and evidence.
5. A separate automated process monitors this repository's releases and updates the dataset on NYC Open Data.

Members of the public can request a change through the [Airtable form](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form); staff review each request and enter accepted changes.

For how AI tools were and were not used, see [`AI_USAGE.md`](AI_USAGE.md).

## Admin UI integration

This repository works with **nycgo-admin-ui**, an internal web interface where authorized editors submit record edits without running the pipeline manually.

> **Note**: The Admin UI repository ([MODA-NYC/nycgo-admin-ui](https://github.com/MODA-NYC/nycgo-admin-ui)) is **internal** and requires organization membership to access.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  nycgo-admin-ui (internal)                                              │
│  ├── Web UI for searching/editing organizations                         │
│  ├── pending-edits/     ← User commits CSV edits here                   │
│  ├── scheduled-edits/   ← Future-dated edits (promoted hourly)          │
│  └── .github/workflows/process-edit.yml  ← Triggers on CSV commit       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Workflow clones this repo,
                                    │ runs pipeline, commits results
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  nyc-governance-organizations (this repo)                               │
│  ├── data/published/latest/   ← Golden dataset (source of truth)        │
│  ├── data/audit/runs/         ← Run artifacts with full audit trail     │
│  ├── .github/workflows/publish-release.yml  ← Creates GitHub releases   │
│  └── Releases                 ← Versioned datasets + validation reports │
└─────────────────────────────────────────────────────────────────────────┘
```

The Admin UI loads its data from this repository's `data/published/latest/NYCGO_golden_dataset_latest.csv`.

## Versioning and change history

- **Releases** are tagged `vX.Y.Z`. Each release lists its changes in the release notes and attaches the files below.
- **Edits submitted through the Admin UI** are currently released as patch versions.
- **Schema changes** use a minor or major version and are recorded in [`schemas/SCHEMA_CHANGELOG.md`](schemas/SCHEMA_CHANGELOG.md).
- **Field-level history**: every change to every record is in [`data/changelog.csv`](data/changelog.csv) (append-only; format in [`docs/CHANGELOG_SPEC.md`](docs/CHANGELOG_SPEC.md)).
- **Directory rule changes** are tracked in [`docs/DIRECTORY_FIELD_CHANGELOG.md`](docs/DIRECTORY_FIELD_CHANGELOG.md).
- **Earlier numbering**: releases up to `2.8.0` (June 2025) predate the current pipeline; numbering restarted at `v1.0.0` afterward. See [`docs/archive/CHANGELOG.md`](docs/archive/CHANGELOG.md).

## Release validation contract

Each GitHub Release includes a machine-readable validation report that downstream consumers can use to verify data integrity before updating their cached copies.

### Release assets

| Asset | Description |
|-------|-------------|
| `NYCGO_golden_dataset_v{X.Y.Z}.csv` | Versioned golden dataset (38 fields, all records) |
| `NYCGO_golden_dataset_latest.csv` | Same file with a stable name for automated fetching |
| `NYCGovernanceOrganizations_v{X.Y.Z}.csv` | Published dataset (17 fields, active records) |
| `NYCGovernanceOrganizations_v{X.Y.Z}.json` | Socrata-compatible JSON export of the published dataset |
| `NYCGovernanceOrganizations_latest.csv` | Same CSV with a stable name |
| `NYCGovernanceOrganizations_latest.json` | Same JSON with a stable name |
| `NYCGO_validation_report.json` | Golden dataset validation report |
| `nycgo_golden_dataset.tableschema.json` | Golden dataset schema (Frictionless Table Schema) |
| `run_changelog.csv` | Field changes in this release |
| `nycgo-run-{run_id}.zip` | Full run bundle (inputs, outputs, review files) |

The published dataset's validation report and schema are not attached to releases. They are in the repository at `data/published/latest/NYCGO_published_validation_report.json` and `schemas/nycgo_published_dataset.tableschema.json`.

### Schema governance

Schema changes are tracked in [`schemas/SCHEMA_CHANGELOG.md`](schemas/SCHEMA_CHANGELOG.md).

**Schema files:**
- `schemas/nycgo_golden_dataset.tableschema.json` - Golden dataset (38 fields)
- `schemas/nycgo_published_dataset.tableschema.json` - Published dataset (17 fields)

**Making schema changes:**
1. Update the schema file with new field definitions
2. Update the version number in the schema file
3. Document the change in `schemas/SCHEMA_CHANGELOG.md`
4. If changing the published schema, update `PUBLISHED_COLUMN_ORDER` in `scripts/process/export_dataset.py`
5. Run the pipeline to validate outputs match the new schema
6. Use a minor or major version bump (not patch) for schema changes

### Validation report structure

The `NYCGO_validation_report.json` file contains:

```json
{
  "validation_report_version": "1.0.0",
  "generated_at": "2025-01-15T12:00:00+00:00",
  "dataset": {
    "name": "nycgo_golden_dataset",
    "schema_version": "1.6.0",
    "schema_hash": "abc123...",
    "version": "v1.7.0"
  },
  "asset": {
    "filename": "NYCGO_golden_dataset_v1.7.0.csv",
    "sha256": "abc123...",
    "size_bytes": 225512,
    "row_count": 434,
    "column_count": 38
  },
  "valid": true,
  "summary": {
    "total_checks": 17,
    "passed_checks": 17,
    "failed_checks": 0,
    "error_count": 0,
    "warning_count": 0
  },
  "checks": [...],
  "errors": [],
  "warnings": []
}
```

### Consumer integration pattern

1. **Fetch the validation report first**:
   ```bash
   curl -sL "https://github.com/MODA-NYC/nyc-governance-organizations/releases/latest/download/NYCGO_validation_report.json"
   ```

2. **Check validity**:
   - If `valid == false`: reject the release, keep serving cached data
   - If `valid == true`: proceed to download the dataset

3. **Verify the checksum**:
   ```bash
   # Download dataset
   curl -sL "https://github.com/MODA-NYC/nyc-governance-organizations/releases/latest/download/NYCGO_golden_dataset_latest.csv" -o dataset.csv
   # Verify SHA-256 matches the value in the validation report
   sha256sum dataset.csv
   ```

4. **Update the cache** only if the checksum matches

### Validation checks

The pipeline validates the following before publishing:

| Check | Blocking? | Description |
|-------|-----------|-------------|
| File parseable | Yes | CSV can be read without errors |
| Row count > 0 | Yes | Dataset contains records |
| Required columns | Yes | All 38 expected columns present |
| Primary key unique | Yes | No duplicate `record_id` values |
| Required fields | Yes | `record_id` and `name` are never empty |
| Pattern validation | Yes | `record_id` matches `NYC_GOID_XXXXXX` format |
| Enum validation | Yes | `operational_status`, `organization_type` contain valid values |
| URL format | No | URL fields contain valid http/https URLs (warning only) |

If any blocking check fails, the release workflow aborts and no GitHub Release is created.

### Local validation

Run validation locally against any CSV:

```bash
python scripts/validate_release_asset.py \
  --input data/published/latest/NYCGO_golden_dataset_latest.csv \
  --schema schemas/nycgo_golden_dataset.tableschema.json \
  --out validation_report.json \
  --version vX.Y.Z
```

Use `--strict` to treat warnings as errors.

## API quick start (Socrata)
Examples use dataset `t3jq-9nkf`.

- **curl (JSON)**: select `name,acronym,organization_type`, filter to `organization_type = 'Mayoral Agency'`, order by `name`.
```bash
curl -G "https://data.cityofnewyork.us/resource/t3jq-9nkf.json" \
  --data-urlencode "$select=name,acronym,organization_type" \
  --data-urlencode "$where=organization_type='Mayoral Agency'" \
  --data-urlencode "$order=name"
```

- **CSV download URL** (same filter):
```bash
https://data.cityofnewyork.us/resource/t3jq-9nkf.csv?$select=name,acronym,organization_type&$where=organization_type='Mayoral%20Agency'&$order=name
```

- **Python (requests)**: fetch a page of results with the same filter.
```python
import requests

BASE = "https://data.cityofnewyork.us/resource/t3jq-9nkf.json"
params = {
    "$select": "name,acronym,organization_type",
    "$where": "organization_type='Mayoral Agency'",
    "$order": "name",
    "$limit": 50,
}
resp = requests.get(BASE, params=params, timeout=30)
resp.raise_for_status()
rows = resp.json()
print(len(rows), "rows")
print(rows[:3])
```

## How to suggest fixes or new organizations
Use the Airtable Change Request Form: [Submit a change request](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form).

Accepted evidence includes official nyc.gov pages showing the value, Executive Orders, press releases, or relevant Charter sections. The form supports:
- Updates to existing records
- “Can’t find it” reports
- Proposing a new organization

## Running the pipeline locally

Routine updates go through the Admin UI and need none of this. Maintainers run the pipeline locally for bulk edits, schema changes, and testing.

### Prerequisites & install
- **Python 3.10+**
- **[UV](https://docs.astral.sh/uv/)** - Python package manager

~~~bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

git clone https://github.com/MODA-NYC/nyc-governance-organizations.git
cd nyc-governance-organizations
make setup             # uses UV to create .venv & install deps from lockfile
~~~

**Running commands**: Use `uv run <command>` or activate the venv with `source .venv/bin/activate`.

### 1 · Run the pipeline
The CLI stages inputs, applies global rules and the edits file, exports pre-release outputs, and writes the per-run changelog and summary.
~~~bash
make run-pipeline GOLDEN=data/published/latest/NYCGO_golden_dataset_latest.csv \
                 QA=data/input/pending/my_edits.csv \
                 DESCRIPTOR=qa-pass
~~~
_The CLI creates a run id when one is not supplied and writes artifacts under `data/audit/runs/<run_id>/`._

Edit files use these columns, the same format the Admin UI produces:
```
record_id,record_name,field_name,new_value,justification,evidence_url
```
Use `NEW` as the `record_id` for every row of a new organization. See [`data/input/README.md`](data/input/README.md) for where edit files go.

To run with no data changes (for example, to test a schema or rule change), omit the edits file:

```bash
python scripts/pipeline/run_pipeline.py \
  --golden data/published/latest/NYCGO_golden_dataset_latest.csv \
  --descriptor "Schema-only-run"
```

### 2 · Review outputs
- Inspect `data/audit/runs/<run_id>/outputs/run_changelog.csv` and `run_summary.json`.
- Use the files in `review/` to check the result.

Each run folder contains `inputs/` (the golden snapshot, the prior published dataset, and the edits applied), `outputs/` (pre-release golden and published datasets, run changelog, run summary), and `review/`. See [`docs/run_artifacts.md`](docs/run_artifacts.md).

### 3 · Publish the run
Promote the pre-release outputs and append the run's changes to the changelog.
~~~bash
make publish-run RUN_ID=<run_id> VERSION=vX.Y.Z
~~~

In normal operation the `publish-release.yml` workflow does this step and creates the GitHub Release.

### 4 · Compare datasets *(optional)*
~~~bash
python scripts/maint/compare_datasets.py \
  --original_csv  data/published/latest/NYCGO_golden_dataset_latest.csv \
  --processed_csv data/audit/runs/<run_id>/outputs/golden_pre-release.csv \
  --output_report_csv data/audit/comparison_report.csv
~~~

### Script reference

| Script | Purpose | Key Args |
|--------|---------|----------|
| **pipeline/run_pipeline.py** | End-to-end run orchestration | `--golden` · `--qa` (optional) · `--descriptor` · `--previous-export` |
| **pipeline/publish_run.py** | Promote pre-release artifacts to final | `--run-dir` · `--version` · `--append-changelog` |
| **process/manage_schema.py** | Add blank columns to a CSV | `--input_csv` · `--output_csv` · `--add_columns` |
| **process/export_dataset.py** | Export logic used by the pipeline package | `--input_csv` · `--output_golden` · `--output_published` |
| **validate_release_asset.py** | Validate a CSV against a schema | `--input` · `--schema` · `--out` · `--version` |

### Development

~~~bash
make test      # run tests
make format    # black + ruff
~~~

## Contributing

- **Dataset or content updates** → use the [change request form](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form) and include an official source.
- **Code changes or tooling ideas** → open a GitHub Issue first. Please do not open pull requests unless a maintainer invites one.

Details are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Governance & credits
Maintained by OTI’s Office of Data Analytics (Data Governance), with partner teams across NYC government. Archived predecessor repo: [Agency-Name-Project](https://github.com/MODA-NYC/Agency-Name-Project).

## License
**MIT**, as declared in `pyproject.toml`.
