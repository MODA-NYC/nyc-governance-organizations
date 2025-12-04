# NYC Agencies and Governance Organizations

An analysis-ready reference of NYC agencies and governance organizaitons—standardized names, acronyms, principal officers, reporting lines, and stable IDs—powering the Agency Directory on nyc.gov.



### Quick links
- **Dataset on NYC Open Data (t3jq-9nkf)**: [NYC Agencies and Governance Organizations](https://data.cityofnewyork.us/d/t3jq-9nkf/)
- **Feedback & corrections (Airtable form)**: [Submit a change request](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form)
- **Baseline run artifacts spec**: [`docs/Run_Artifacts.md`](docs/Run_Artifacts.md)
- **Release history**: see [Release History](#release-history) in this README
- **Contributing (CONTRIBUTING.md)**: (TODO: add)

## Overview
NYC Agencies and Governance Organizations is a standardized reference list of NYC agencies and other governance organizations. It standardizes official names, acronyms, leadership, and reporting relationships so New Yorkers—and City staff—can speak the same language about government. It consolidates the citywide organizational chart into a single, analysis-ready table and powers the revamped Agency Directory on nyc.gov, which presents a curated subset of these records for public browsing.

Each record is included in at least one of two authoritative sources: the Citywide Org Chart or an internal list of NYC governance organizations maintained by the Mayor’s Office of Operations. Each record includes the organization’s preferred and alternate names, acronyms, type classification, operational status, principal officer information, reporting relationship, official website, and directory-inclusion flags. All organizations in this dataset are formally established through a legal or administrative instrument, such as an NYC Charter provision, Mayoral Executive Order, or local or state enabling statute.

To make this data publicly available, we built a repeatable publication pipeline with rule-based cleaning, Unicode/encoding fixes, name parsing, de-duplication, and a comprehensive audit trail of every change. The workflow supports structured QA, supplemental edits, and scripted exports for publication—so the dataset can keep pace as executive orders or Charter updates create, merge, or retire units. NYC Agencies and Governance Organizations helps New Yorkers and City staff understand who's who in government and how units relate. It can be paired with budgets, contracts, performance metrics, or program datasets to analyze services and accountability across the enterprise. The dataset and accompanying crosswalks in this GitHub repository are designed to combine other datasets that use legacy names or system-specific codes, improving interoperability citywide. Documentation and processing scripts are available in this repository, and the Agency Directory provides an accessible front door for the public.

## Phase I vs Phase II

This repository maintains two versions of the dataset schema:

### Phase I (v1.1.1) - Final Release
- **Released**: November 21, 2024
- **Golden Dataset Fields**: 38 fields
- **Public Export Fields**: 16 fields (+ 1 computed field: `listed_in_nyc_gov_agency_directory`)
- **Entity Count**: 434
- **RecordID Format**: `NYC_GOID_XXXXXX` (e.g., `NYC_GOID_000318`)
- **Relationship Field**: `reports_to` (text field capturing both org chart and parent-child relationships)
- **Documentation**: See [`docs/PHASE_I_PIPELINE.md`](docs/PHASE_I_PIPELINE.md) for complete Phase I workflow and schema details

### Phase II (v2.0.0-dev) - Current Development
- **Status**: In development
- **Golden Dataset Fields**: 46 fields (38 original - 1 retired + 9 new)
- **Public Export Fields**: 25 fields
- **Entity Count**: 433 (will be 434 when complete)
- **RecordID Format**: 6-digit numeric (e.g., `100318`)
- **Relationship Fields**: 
  - `org_chart_oversight_record_id` and `org_chart_oversight_name` (for org chart/political oversight)
  - `parent_organization_record_id` and `parent_organization_name` (for parent-child governance relationships)
- **New Fields**: `governance_structure`, `authorizing_authority`, `authorizing_authority_type`, `authorizing_url`, `appointments_summary`
- **Retired Fields**: `reports_to` (replaced by new relationship fields)
- **Documentation**: See [`PHASE_II_PLAN.md`](PHASE_II_PLAN.md) for Phase II implementation details

**Note**: For urgent Phase I-compatible updates during Phase II development, use [`scripts/pipeline/export_phase_i.py`](scripts/pipeline/export_phase_i.py) to generate Phase I-compatible exports from Phase II datasets.

## Public schema

### Phase II Public Schema (v2.0.0-dev)

The current development version exposes 25 fields. For Phase I schema (16 fields), see [`docs/PHASE_I_SCHEMA.md`](docs/PHASE_I_SCHEMA.md).

| Field | Description |
|-------|-------------|
| record_id | Stable internal ID (immutable, 6-digit numeric format) |
| operational_status | Current status of the organization |
| organization_type | Category (e.g., Mayoral Agency, Advisory/Regulatory, etc.) |
| name | Official/preferred name |
| acronym | Official acronym (if any) |
| name_alphabetized | Name normalized for sorting |
| url | Official website URL |
| alternate_or_former_names | Other names seen in official sources |
| alternate_or_former_acronyms | Other acronyms seen in official sources |
| principal_officer_title | Title of the principal officer |
| principal_officer_full_name | Full name of the principal officer |
| principal_officer_first_name | Given name (derived/maintained) |
| principal_officer_last_name | Family name (derived/maintained) |
| principal_officer_contact_url | Profile/contact page for principal officer |
| in_org_chart | Flag used for citywide org chart |
| listed_in_nyc_gov_agency_directory | Flag used for nyc.gov Agency Directory |
| governance_structure | Narrative description of governance structure (e.g., board composition) |
| org_chart_oversight_record_id | RecordID of entity providing org chart/political oversight |
| org_chart_oversight_name | Name of entity providing org chart/political oversight |
| parent_organization_record_id | RecordID of parent organization (for specialized boards, divisions) |
| parent_organization_name | Name of parent organization |
| authorizing_authority | Legal authority establishing the organization (e.g., "NYC Charter § 2203") |
| authorizing_authority_type | Type of legal authority (NYC Charter, Mayoral Executive Order, etc.) |
| authorizing_url | URL to legal document or statute |
| appointments_summary | Description of how appointments/selection works |

## Run artifacts baseline

All processing runs must emit a structured artifact bundle under `data/audit/runs/<run_id>/`. Each bundle contains:

- `inputs/`: golden snapshot used, prior published snapshot, and the edits CSV that triggered the run
- `outputs/`: regenerated golden dataset, regenerated published dataset, run changelog CSV, and a `run_summary.json` with record counts and key metrics; all outputs remain in pre-release form (`*_pre-release.*`)
- `review/`: QA aids such as source comparison reports and summary statistics

Run folders follow the convention `YYYYMMDD-HHMM_<descriptor>` with a timezone indicator (UTC recommended). See [`docs/run_artifacts.md`](docs/run_artifacts.md) for detailed guidance plus examples of where review aids should land.

## Versioning & release policy

- Semantic versioning resumes at `v1.0.0` for the next publish event. Code changes before the publish CLI launches use the development version `1.0.0-dev` in `pyproject.toml`.
- Every run folder must record its dataset linkage in `data/audit/run_manifest.csv` so we can trace published artifacts back to the originating run.
- Legacy releases up to `2.8.0` are retained for context but new tags will begin at `v1.0.0` once the publish workflow is live.

## Release history

- **Unreleased / in-flight** – pipeline restructure phases (complete). Focus areas: new `nycgo_pipeline` package, run/publish CLIs, data layout cleanup.
- **2.8.0 (2025-06-10)** – Baseline prior to the refactor. Introduced the modular scripts (`manage_schema.py`, `process_golden_dataset.py`, `export_dataset.py`, `compare_datasets.py`), name parsing utilities, the maintenance scripts for the changelog workflow, and the current pytest suite and linting config. This release also added the append-only changelog (`data/changelog.csv`) and accompanying spec in `docs/CHANGELOG_SPEC.md`.

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

## How to run this repo

### Prerequisites & install
- **Python 3.10+**
- `pyenv` (recommended)

~~~bash
git clone https://github.com/MODA-NYC/nyc-governance-organizations.git
cd nyc-governance-organizations
make setup             # creates .venv & installs deps
source .venv/bin/activate
~~~

### Pipeline Workflow

**Note**: Current pipeline generates Phase II format (v2.0.0-dev). For Phase I format workflow, see [`docs/PHASE_I_PIPELINE.md`](docs/PHASE_I_PIPELINE.md). For urgent Phase I-compatible updates during Phase II development, use [`scripts/pipeline/export_phase_i.py`](scripts/pipeline/export_phase_i.py).

#### 1 · Prepare Schema *(optional)*
~~~bash
python scripts/process/manage_schema.py \
  --input_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --output_csv data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
  --add_columns "PrincipalOfficerFullName,PrincipalOfficerGivenName,PrincipalOfficerMiddleNameOrInitial,PrincipalOfficerFamilyName,PrincipalOfficerSuffix" \
  --default_value ""
~~~

#### 2 · Run the pipeline orchestrator
The new CLI stages inputs, applies global rules + QA edits, exports pre-release outputs, and emits the per-run changelog and summary.
~~~bash
make run-pipeline GOLDEN=data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
                 QA=data/input/Agency_Name_QA_Edits.csv \
                 DESCRIPTOR=qa-pass
~~~
_The CLI will create a run id when one is not supplied and writes artifacts under `data/audit/runs/<run_id>/`._

#### 3 · Review outputs
- Inspect `data/audit/runs/<run_id>/outputs/run_changelog.csv` and `run_summary.json`.
- Use aids in `review/` to validate (comparison reports, stats).

#### 4 · Publish the run
Promote the pre-release artifacts and append changelog rows to the dataset manifest.
~~~bash
make publish-run RUN_ID=<run_id> VERSION=v1.0.0
~~~
_Publish creates `_final` artifacts in `data/published/`, updates `latest/`, archives prior `latest/` snapshots, zips the run folder, and appends rows to `data/changelog.csv`._

#### 5 · Audit & Compare *(optional)*
~~~bash
python compare_datasets.py \
  --original_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --processed_csv data/published/NYCGovernanceOrganizations_v2.8.csv \
  --output_report_csv data/audit/comparison_report_v2.8.csv
~~~

### Script Reference

| Script | Purpose | Key Args |
|--------|---------|----------|
| **pipeline/run_pipeline.py** | End-to-end run orchestration | `--golden` · `--qa` · `--descriptor` · `--previous-export` |
| **pipeline/publish_run.py** | Promote pre-release artifacts to final | `--run-dir` · `--version` · `--append-changelog` |
| **process/manage_schema.py** | Add blank columns to a CSV | `--input_csv` · `--output_csv` · `--add_columns` |
| **process/export_dataset.py** | (Legacy) export helper leveraged by pipeline package | `--input_csv` · `--output_golden` · `--output_published` |

### Development

#### Run Tests
~~~bash
make test
~~~

#### Format & Lint
~~~bash
make format
~~~

## Versioning & changelog
See [CHANGELOG.md](CHANGELOG.md) (append-only). Changes to `name`, `url`, `listed_in_nyc_gov_agency_directory`, `in_org_chart`, and major structural updates will be called out.

## Contributing (policy)

We accept contributions in two ways:

- Dataset/content updates → Use the NYC GO Change Request Form (Airtable). Please include an official source.
👉 https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form

- Code changes or tooling ideas → Open a GitHub Issue in this repo to discuss scope and approach.
Please do not open pull requests unless a maintainer explicitly invites one on an accepted issue. Unsolicited PRs may be closed.

Why: This repository runs a governed, production pipeline for a public dataset. Issue-first keeps changes reviewable, predictable, and compliant.

## Governance & credits
Maintained by OTI’s Office of Data Analytics (Data Governance), with partner teams across NYC government. Archived predecessor repo: [Agency-Name-Project](https://github.com/MODA-NYC/Agency-Name-Project).

## License
**MIT** – see `pyproject.toml` for full text.
