---
Observations (Markdown)
---

### Golden Dataset (`data/input/NYCGovernanceOrganizations_DRAFT_20250410.csv`)

*   **Total Rows:** 417
*   **Column Names:** ['RecordID', 'Name', 'NameAlphabetized', 'OperationalStatus', 'OrganizationType', 'Description', 'URL', 'AlternateNames', 'Acronym', 'AlternateAcronyms', 'BudgetCode', 'OpenDatasetsURL', 'FoundingYear', 'PrincipalOfficerName', 'PrincipalOfficerTitle', 'PrincipalOfficerContactURL', 'Notes', 'InstanceOf', 'Name - NYC.gov Agency List', "Name - NYC.gov Mayor's Office", 'Name - NYC Open Data Portal', 'Name - ODA', 'Name - CPO', 'Name - WeGov', 'Name - Greenbook', 'Name - Checkbook', 'Name - HOO', 'Name - Ops', 'NYC.gov Agency Directory', 'Jan 2025 Org Chart']
*   **Columns with Missing Values (Top 5 or as available if significant):**
    *   `Notes`: 411 missing values (98.56%)
    *   `AlternateAcronyms`: 400 missing values (95.92%)
    *   `AlternateNames`: 392 missing values (94.00%)
    *   `InstanceOf`: 376 missing values (90.17%)
    *   `Name - Checkbook`: 358 missing values (85.85%)

*   **'Jan 2025 Org Chart' Column Insights:**
    *   `False`: 270 occurrences
    *   `True`: 147 occurrences
    *   Counts - True: 147, False: 270, NaN/Missing: 0. The most common value is `False`.


### QA Dataset (`data/input/Agency_Name_QA_Edits.csv`)

*   **Total Rows:** 40
*   **Column Names:** ['Column', 'Row(s)', 'Feedback']
*   **Columns Most Frequently Targeted for QA (Top 5 or as available):**
    *   `PrincipalOfficersName`: 7 times
    *   `Acronym`: 5 times
    *   `Description`: 4 times
    *   `PrincipalOfficerTitle`: 4 times
    *   `Name`: 3 times

*   **Most Typical Types of Feedback/Requested Changes (Top 10 common words from 'Feedback' column):**
    *   `field` (appears 5 times)
    *   `oti` (appears 5 times)
    *   `but` (appears 4 times)
    *   `description` (appears 4 times)
    *   `have` (appears 4 times)
    *   `values` (appears 4 times)
    *   `consider` (appears 4 times)
    *   `fix` (appears 3 times)
    *   `office` (appears 3 times)
    *   `like` (appears 3 times)
    *   Common themes from these words might relate to data quality (e.g., 'missing', 'fix', 'error'), specific fields ('name', 'description', 'officer'), or entities ('mayor', 'office').
