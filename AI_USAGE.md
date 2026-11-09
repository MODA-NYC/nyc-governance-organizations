# AI Usage

This page describes where AI tools were used in building and maintaining
this dataset and repository, and where they were not.

## Summary

- AI assisted with writing code and with some research.
- AI does not make or publish data changes. Every value in the dataset was
  entered or approved by City staff.
- The publication pipeline is rule-based. It contains no AI step.

## Code

The pipeline scripts, tests, GitHub Actions workflows and the Admin UI were
written by staff using AI coding assistants (primarily Claude Code). Staff
directed, reviewed and tested the work. AI-assisted commits are labeled in
the git history with a `Co-Authored-By` trailer.

## Research on field values

For some field values, AI tools were used to find and summarize candidate
values from public sources such as nyc.gov pages, the City Charter and
executive orders. A staff member checked each candidate against an official
source before it entered the dataset. No AI output was loaded unreviewed.
Which fields this covered was not recorded at the time.

## How the dataset is updated

1. An authorized editor submits a change in the Admin UI with a
   justification and, where available, an evidence URL.
2. The editor commits the generated edit file under their own GitHub account.
3. An automated workflow applies the edit: rule-based cleaning, name
   parsing, directory-eligibility rules and schema validation.
4. If validation passes, a versioned release is published and each field
   change is appended to `data/changelog.csv` with who, when, why and evidence.
5. A separate automated process monitors this repository's releases and
   updates the dataset on NYC Open Data.

No AI is involved in any of these steps.

## A note on the changelog

In `data/changelog.csv`, about 1,000 rows from one December 2025 run list
`Claude` in the `operator` column. That run was started from an AI coding
assistant session, and the label records who started it. The changes
themselves were made by the pipeline's fixed formatting rules (boolean and
year formats), as the `source_ref` and `notes` columns show. They are not
AI-researched values.

## Questions and corrections

Maintained by OTI's Office of Data Analytics. Report errors through the
change request form linked in the [README](README.md).

_Last reviewed: 2026-11-09_
