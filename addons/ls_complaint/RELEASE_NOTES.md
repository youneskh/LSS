# Release Notes — ls_complaint 19.0.1.0.0

**Date:** 28 July 2026
**Target:** Odoo 19.0 Community Edition
**Licence:** AGPL-3
**Status:** Beta — see the warning below

## What this release contains

A complete complaint handling process for regulated life sciences
organisations: intake from any channel, classification against configurable
categories, documented impact assessment, adverse event records with their own
reportability lifecycle, root cause investigation with an independent approval,
resolution actions with mandatory evidence, and a reviewed closure after which
the record becomes read-only.

Seven models, 143 fields, four access levels, 21 access rules, seven record
rules, two scheduled actions, one PDF report, two mail templates, 103 tests and
15 documents.

## Read this before installing

This release was **never installed, never executed and never tested**. It was
produced in an environment with no Odoo runtime and no network access.

- Install it first on a scratch database, never on a production or validated
  instance.
- If it fails to load, consult the risk register in
  `docs/00_verification_and_limitations.md`, which lists fifteen
  version-sensitive API points and the fallback for each.
- Run the delivered test suite and measure coverage yourself; no coverage figure
  is claimed here.

## Two things this release deliberately does not do

**It encodes no regulatory value.** Acknowledgement, investigation and closure
targets, and the adverse event reporting deadline, are all configuration fields
defaulting to *not configured*. No due date is produced until the organisation
sets them. This is intentional: a deadline depends on the product, the market
and the authority, and none of that was verified here.

**It does not provide electronic signatures or a tamper-evident audit trail.**
Field tracking and server-side record freezing are not equivalent to FDA
21 CFR Part 11 controls. `docs/02_regulatory_analysis.md` section 4 explains
precisely what is missing.

## Compatibility

Community Edition only. Depends on `base`, `mail`, `product` and `stock`. No
Enterprise module and no third-party Python package is required. No dependency
on `ls_qms` or `ls_capa`: CAPA linkage is an extension point, and the bridge
module contract is specified in `docs/developer_manual.md`.

## Upgrade

First release; no upgrade path applies.

## Known limitations

1. No kanban view.
2. No translation file.
3. No automatic acknowledgement to the complainant; the template exists, sending
   is a manual decision.
4. No verification of the CAPA reference, which is free text until a CAPA module
   exists.
5. No automatic transmission of any report to any authority.
6. No retention policy and no automatic archival.
7. Upgrade tests and performance tests are not delivered.
