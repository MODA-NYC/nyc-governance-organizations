# Research Prompt: ID Prefix Best Practices

## Context

I'm working on a public government dataset (NYC Governance Organizations) and need to decide on a RecordID format. We're migrating from a complex format to a simpler one.

**Current format:** `NYC_GOID_000318` (uppercase, underscores, leading zeros, long prefix)

**Feedback received:** "record_id could be simpler. Avoiding uppercase letters, leading zeros and no or shorter prefix. This would all just make it a more reliable join and easier to handle."

**Proposed formats under consideration:**
- `nycgo100318` (5-char prefix: "nycgo")
- `nycgoid100318` (8-char prefix: "nycgoid")
- `100318` (no prefix, just numeric)

## Dataset Details

- **Type:** Public government dataset (NYC agencies/organizations)
- **Size:** ~433 entities currently, expected to grow to potentially thousands
- **Use case:** Public data release, joins with other datasets, API queries
- **Users:** Data analysts, researchers, developers, general public
- **Format:** CSV files, will be published on NYC Open Data portal

## Specific Questions

1. **Prefix length best practices:** For public datasets, is there a recommended prefix length? Should prefixes be kept short (3-5 chars) or is longer acceptable if it adds clarity?

2. **Clarity vs brevity:** For public datasets, should IDs prioritize being self-documenting (`nycgoid100318`) or concise (`nycgo100318`)? What's the industry standard?

3. **No prefix option:** Is it acceptable/advisable to use purely numeric IDs (`100318`) for public datasets, or do prefixes provide important benefits (namespace collision avoidance, clarity)?

4. **Government/public data conventions:** Are there established conventions for government/public dataset IDs? Do agencies like Census Bureau, Data.gov, or similar use prefixes?

5. **Join reliability:** The feedback mentioned "more reliable join" - does prefix length/format actually impact join performance or reliability in practice?

6. **Examples:** Can you provide examples of well-designed ID formats from reputable public datasets (government, open data portals, etc.)?

## Constraints

- Must avoid zip code conflicts (5-digit numbers 00000-99999)
- Need ~200k+ ID capacity
- Must be URL-safe (no special characters)
- Should be easy to type/copy-paste
- Will be used in CSV files, APIs, and joins with other datasets

Please provide research-backed recommendations with examples from real-world public datasets.
