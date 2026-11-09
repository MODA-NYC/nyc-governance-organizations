# Contributing

We accept contributions in two ways.

## Dataset or content updates

Use the [NYC GO Change Request Form](https://airtable.com/app7XmwsZnK325UiH/pagw5O7ZNWHJMkzxl/form). The form supports:

- Updates to existing records
- "Can't find it" reports
- Proposing a new organization

Please include an official source. Accepted evidence includes official nyc.gov pages showing the value, Executive Orders, press releases, or relevant Charter sections.

Staff review each request and enter accepted changes, which appear in a later release.

## Code changes or tooling ideas

Open a [GitHub Issue](https://github.com/MODA-NYC/nyc-governance-organizations/issues) to discuss scope and approach.

Please do not open pull requests unless a maintainer explicitly invites one on an accepted issue. Unsolicited PRs may be closed.

**Why**: this repository runs a governed, production pipeline for a public dataset. Issue-first keeps changes reviewable and predictable.

## For maintainers

- Setup, tests, and local pipeline runs: see the [README](README.md#running-the-pipeline-locally).
- Operations (credentials, failed runs, editors): see [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md).
- Schema changes: follow the steps under "Schema governance" in the README and record the change in [`schemas/SCHEMA_CHANGELOG.md`](schemas/SCHEMA_CHANGELOG.md).
- AI-assisted work: see [`AI_USAGE.md`](AI_USAGE.md). Keep the `Co-Authored-By` trailer on AI-assisted commits.
