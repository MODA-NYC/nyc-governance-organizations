# NYC Agencies and Governance Organizations

An analysis-ready reference of NYC agencies and governance organizaitons—standardized names, acronyms, principal officers, reporting lines, and stable IDs—powering the Agency Directory on nyc.gov.



### Quick links
- **Dataset on NYC Open Data (t3jq-9nkf)**: [NYC Agencies and Governance Organizations](https://data.cityofnewyork.us/d/t3jq-9nkf/)
- **Feedback & corrections (Airtable form)**: [Submit a change request](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Contributing (CONTRIBUTING.md)**: (TODO: add)

## Overview
NYC Agencies and Governance Organizations is a standardized reference list of NYC agencies and other governance organizations. It standardizes official names, acronyms, leadership, and reporting relationships so New Yorkers—and City staff—can speak the same language about government. It consolidates the citywide organizational chart into a single, analysis-ready table and powers the revamped Agency Directory on nyc.gov, which presents a curated subset of these records for public browsing.

Each record is included in at least one of two authoritative sources: the Citywide Org Chart or an internal list of NYC governance organizations maintained by the Mayor’s Office of Operations. Each record includes the organization’s preferred and alternate names, acronyms, type classification, operational status, principal officer information, reporting relationship, official website, and directory-inclusion flags. All organizations in this dataset are formally established through a legal or administrative instrument, such as an NYC Charter provision, Mayoral Executive Order, or local or state enabling statute.

To make this data publicly available, we built a repeatable publication pipeline with rule-based cleaning, Unicode/encoding fixes, name parsing, de-duplication, and a comprehensive audit trail of every change. The workflow supports structured QA, supplemental edits, and scripted exports for publication—so the dataset can keep pace as executive orders or Charter updates create, merge, or retire units. NYC Agencies and Governance Organizations helps New Yorkers and City staff understand who’s who in government and how units relate. It can be paired with budgets, contracts, performance metrics, or program datasets to analyze services and accountability across the enterprise. The dataset and accompanying crosswalks in this GitHub repository are designed to combine other datasets that use legacy names or system-specific codes, improving interoperability citywide. Documentation and processing scripts are available in this repository, and the Agency Directory provides an accessible front door for the public.

## Public schema (current release)
Initial public release exposes 17 fields; legal lineage (citations, founding/sunset) is planned for a later release.

| Field | Description |
|-------|-------------|
| record_id | Stable internal ID (immutable) |
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
| reports_to | Reporting/administrative/oversight relationship |
| in_org_chart | Flag used for citywide org chart |
| listed_in_nyc_gov_agency_directory | Flag used for nyc.gov Agency Directory |

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

### Data-Processing Workflow

#### 1 · Prepare Schema *(optional)*
~~~bash
python manage_schema.py \
  --input_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --output_csv data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
  --add_columns "PrincipalOfficerFullName,PrincipalOfficerGivenName,PrincipalOfficerMiddleNameOrInitial,PrincipalOfficerFamilyName,PrincipalOfficerSuffix" \
  --default_value ""
~~~

#### 2 · Main Processing Run
~~~bash
python src/process_golden_dataset.py \
  --golden    data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
  --qa        data/input/Agency_Name_QA_Edits.csv \
  --out       data/output/processed_run1_mainQA.csv \
  --changelog data/output/changelog_run1_mainQA.csv \
  --changed-by "DataAnalyst_Run1"
~~~
*Review changelog for `POLICY_QUERY` or `NAME_PARSE_REVIEW_NEEDED` flags.*

#### 3 · Supplemental Edits Run
~~~bash
python src/process_golden_dataset.py \
  --golden    data/output/processed_run1_mainQA.csv \
  --qa        data/input/supplemental_edits_v1.csv \
  --out       data/output/processed_run2_supplemental.csv \
  --changelog data/output/changelog_run2_supplemental.csv \
  --changed-by "DataAnalyst_Run2_Supplemental"
~~~
` supplemental_edits.csv ` can include:
``Delete RecordID ORG-123`` or
``Append records from CSV data/input/community_board_new_row_additions.csv``

#### 4 · Final Export for Publication
~~~bash
# Basic export (no changelog tracking)
python scripts/process/export_dataset.py \
  --input_csv data/output/processed_run2_supplemental.csv \
  --output_golden data/published/NYCGO_golden_dataset_v0_19.csv \
  --output_published data/published/NYCGovernanceOrganizations_v0_19.csv

# Export WITH changelog tracking for directory field changes
RUN_ID=$(python scripts/maint/make_run_id.py)
python scripts/process/export_dataset.py \
  --input_csv data/output/processed_run2_supplemental.csv \
  --output_golden data/published/NYCGO_golden_dataset_v0_19.csv \
  --output_published data/published/NYCGovernanceOrganizations_v0_19.csv \
  --run-dir data/audit/runs/$RUN_ID \
  --run-id $RUN_ID \
  --operator "$USER" \
  --previous-export data/published/latest/NYCGovernanceOrganizations_v0_18.csv

# Then follow the review → append workflow
python scripts/maint/review_changes.py --run-dir data/audit/runs/$RUN_ID
python scripts/maint/append_changelog.py --run-dir data/audit/runs/$RUN_ID \
  --changelog data/changelog.csv --operator "$USER"
~~~

#### 5 · Audit & Compare *(optional)*
~~~bash
python compare_datasets.py \
  --original_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --processed_csv data/published/NYCGovernanceOrganizations_v2.8.csv \
  --output_report_csv data/audit/comparison_report_v2.8.csv
~~~

#### 6 · Changelog (append-only) — new audit flow
The per-run audit artifacts are produced locally under `data/audit/runs/<run_id>/` and ignored by Git. After review, approved rows are appended to the tracked `data/changelog.csv`.

Basic flow:
~~~bash
# 1) Create a run id
python scripts/maint/make_run_id.py > /tmp/run_id
RUN_ID=$(cat /tmp/run_id)

# 2) Your processing step should write proposed_changes.csv into the run dir
#    e.g., data/audit/runs/$RUN_ID/proposed_changes.csv

# 3) Review & approve (auto-approve by default)
python scripts/maint/review_changes.py \
  --run-dir data/audit/runs/$RUN_ID

# 4) Append approved rows to the append-only changelog (idempotent)
python scripts/maint/append_changelog.py \
  --run-dir data/audit/runs/$RUN_ID \
  --changelog data/changelog.csv \
  --operator "$USER"
~~~

### 7 · Step 4: Publish changelog run (review → append → optional commit/release)

If your pipeline emits step-wise changelogs under `data/output/`, use the adapter to prepare per-run proposed changes:

~~~bash
python scripts/maint/prepare_run_proposed_changes.py \
  --run-id $RUN_ID \
  --step1 data/output/changelog_step1.csv \
  --step2 data/output/changelog_step2.csv
~~~

Then review → append (dry-run):

~~~bash
python scripts/maint/publish_changelog_run.py \
  --run-dir data/audit/runs/$RUN_ID
~~~

Append & commit (optionally tag/release):

~~~bash
python scripts/maint/publish_changelog_run.py \
  --run-dir data/audit/runs/$RUN_ID \
  --apply --commit --operator "$USER"

# optional tagging/release marker
python scripts/maint/publish_changelog_run.py \
  --run-dir data/audit/runs/$RUN_ID \
  --apply --commit --tag v1.0.0 --release --operator "$USER"
~~~

### Script Reference

| Script | Purpose | Key Args |
|--------|---------|----------|
| **manage_schema.py** | Add blank columns to a CSV | `--input_csv` · `--output_csv` · `--add_columns` |
| **process_golden_dataset.py** | Core processor — global rules + QA edits | `--golden` · `--qa` · `--out` · `--changelog` · `--changed-by` |
| **export_dataset.py** | Final cleanup & column mapping; tracks directory field changes | `--input_csv` · `--output_golden` · `--output_published` · `--run-dir` (optional) · `--run-id` (optional) · `--operator` (optional) · `--previous-export` (optional) |
| **compare_datasets.py** | Audit RecordID adds / drops | `--original_csv` · `--processed_csv` · `--output_report_csv` |

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
