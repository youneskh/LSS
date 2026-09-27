# Validation Management (`ls_validation`)

Validation lifecycle management for regulated life sciences environments,
built for **Odoo 19 Community Edition**.

The module manages validation master plans, qualification and validation
protocols (DQ, IQ, OQ, PQ, PV, CV, CSV, MV), execution records with per-test
attribution, discrepancies, validation summary reports, and an append-only
electronic signature log with a SHA-256 hash chain.

## Features

- **Validation items** — equipment, utilities, facilities, processes, cleaning
  procedures, computerised systems, analytical methods and transport lanes,
  each with a GxP impact, a criticality and a system owner.
- **Validation Master Plans** — drafted, reviewed, approved with an electronic
  signature, activated, and superseded by a new version. Content is frozen
  once approved.
- **Protocols** — test cases with objective, procedure, acceptance criterion,
  expected evidence and a critical flag. Test cases are frozen at approval, so
  acceptance criteria cannot change after results are known.
- **Execution records** — generated from the approved test cases, one result
  line per test case, each stamped with its executor and timestamp. Completion
  requires a verdict and an observed result for every line, and a discrepancy
  for every failure.
- **Four-eyes principle** — the reviewer of an execution cannot be its
  executor; approval is restricted to the approver group.
- **Discrepancies** — investigation, root cause, impact assessment and
  corrective action are mandatory before resolution. An open discrepancy
  blocks the approval of its execution.
- **Validation Summary Reports** — consolidate approved executions, carry a
  conclusion and a validity period, and are the only way an item becomes
  validated. A failed critical test case forbids the conclusion *Validated*.
- **Derived status** — every item shows Not Validated, In Validation,
  Validated, Expiring, Expired or Retired. The status is computed, never
  typed.
- **Electronic signatures** — password re-authentication, recorded meaning,
  timestamp, and a SHA-256 chain per company. Signature records cannot be
  modified or deleted by anyone, including the administrator.
- **Scheduled action** — daily status refresh and one revalidation activity
  per expiring or expired item.
- **Three PDF reports** — protocol, execution record and summary report, each
  including its signature table.

## Installation

See `docs/INSTALL.md`. The module depends on `mail` only.

## Regulatory statement

This module is designed to **support** an organisation implementing processes
aligned with GMP, ISO 9001, ISO 13485, EU GMP Annex 11 and Annex 15, and
FDA 21 CFR Part 11.

**It does not deliver compliance and no compliance is claimed.** Compliance
depends on the organisation's procedures, its qualification of this
installation, its training and its administrative controls. See
`docs/VALIDATION_REPORT.md` for what has and has not been verified.

## Licence

AGPL-3.0 or later.
