# NYC Governance Organizations: Golden Dataset Processor

## Overview
This project refines a **"golden dataset"** of NYC governance organizations.
It applies automated global transformations, ingests structured QA feedback, supports manual supplemental edits, and emits:

* A clean, public-ready dataset
* A detailed, machine-readable changelog tracking every modification

---

## Key Features
- **Rule-Based Processing** – Regex-driven engine ingests QA CSVs and applies fixes.
- **Automated Data Cleaning** – Handles text-encoding glitches (`ftfy`), duplicate semi-colon lists, Unicode normalization.
- **Advanced Name Parsing** – `nameparser` splits full names into first / middle / last / suffix.
- **Comprehensive Auditing** – Per-run changelog lists each change, its source, and triggering rule.
- **Modular CLI Workflow** – Discrete scripts for schema tweaks, processing, export, and audit.
- **High Code Quality** – `black` + `ruff` via `pre-commit` hooks.
- **Test Coverage** – Core logic verified by `pytest`.

---

## Project History & Context
Successor to the (archived) **NYC Agency Name Standardization Project**.

| Phase | Summary |
|-------|---------|
| **1** | Initial integration & cleaning in Google Colab |
| **2** | Migration to modular Python repo (this project) |
| **Now** | Formal CLI pipeline · rules engine · full audit trail · modern dev practices |

---

## Project Structure
├── data/ # CSV inputs / outputs / audits
│ ├── input/
│ ├── output/
│ ├── published/
│ └── audit/
├── src/
│ └── process_golden_dataset.py
├── tests/ # pytest specs
├── compare_datasets.py
├── export_dataset.py
├── manage_schema.py
├── Makefile
├── pyproject.toml
└── README.md


---

## Getting Started

### Prerequisites
- **Python 3.10+**
- `pyenv` (recommended)

### Installation
~~~bash
git clone https://github.com/MODA-NYC/nyc-governance-organizations.git
cd nyc-governance-organizations
make setup             # creates .venv & installs deps
source .venv/bin/activate
~~~

---

## Data-Processing Workflow

### 1 · Prepare Schema *(optional)*
~~~bash
python manage_schema.py \
  --input_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --output_csv data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
  --add_columns "PrincipalOfficerFullName,PrincipalOfficerGivenName,PrincipalOfficerMiddleNameOrInitial,PrincipalOfficerFamilyName,PrincipalOfficerSuffix" \
  --default_value ""
~~~

### 2 · Main Processing Run
~~~bash
python src/process_golden_dataset.py \
  --golden    data/input/NYCGovernanceOrganizations_DRAFT_20250604.csv \
  --qa        data/input/Agency_Name_QA_Edits.csv \
  --out       data/output/processed_run1_mainQA.csv \
  --changelog data/output/changelog_run1_mainQA.csv \
  --changed-by "DataAnalyst_Run1"
~~~
*Review changelog for `POLICY_QUERY` or `NAME_PARSE_REVIEW_NEEDED` flags.*

### 3 · Supplemental Edits Run
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

### 4 · Final Export for Publication
~~~bash
python export_dataset.py \
  --input_csv  data/output/processed_run2_supplemental.csv \
  --output_csv data/published/NYCGovernanceOrganizations_v2.8.csv
~~~

### 5 · Audit & Compare *(optional)*
~~~bash
python compare_datasets.py \
  --original_csv  data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv \
  --processed_csv data/published/NYCGovernanceOrganizations_v2.8.csv \
  --output_report_csv data/audit/comparison_report_v2.8.csv
~~~

---

## Script Reference

| Script | Purpose | Key Args |
|--------|---------|----------|
| **manage_schema.py** | Add blank columns to a CSV | `--input_csv` · `--output_csv` · `--add_columns` |
| **process_golden_dataset.py** | Core processor — global rules + QA edits | `--golden` · `--qa` · `--out` · `--changelog` · `--changed-by` |
| **export_dataset.py** | Final cleanup & column mapping | `--input_csv` · `--output_csv` |
| **compare_datasets.py** | Audit RecordID adds / drops | `--original_csv` · `--processed_csv` · `--output_report_csv` |

---

## Development

### Run Tests
~~~bash
make test
~~~

### Format & Lint
~~~bash
make format
~~~

---

## Contributing
1. Fork → `git checkout -b feature/your-feature`
2. Code → `make format` & `make test`
3. Commit → Push → PR

---

## License
**MIT** – see `pyproject.toml` for full text.
