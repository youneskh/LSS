# Release Notes — ls_recall 19.0.1.0.0

**Date:** 27 July 2026
**Platform:** Odoo 19.0 Community Edition
**Licence:** AGPL-3
**Status:** Beta — ready to enter qualification, not qualified

---

## What this release is

A complete recall and field action management module: recall plans,
five action types, distribution tracing from stock, consignee
reconciliation, controlled communications, effectiveness checks with
sampling levels, reports with frozen figures, and gated closure.

Nine models, 22 access rules, six multi-company rules, two wizards, two
printable documents, two scheduled actions, 99 tests, 15 documents.

## What was verified

Executed in the build environment:

* All 25 Python files compile.
* All 17 XML files are well-formed.
* Static analysis passes with no blocking finding: manifest/disk
  agreement, view field references resolved against model fields, button
  methods resolved, XML id references resolved, access rights CSV
  validated, style and docstrings checked.
* The static analyser was itself checked with four injected faults and
  detected all four.

Eight defects were found and fixed during review, two of which would
have prevented installation.

## What was not verified

* **The 99 tests have never been executed.** No Odoo runtime was
  available.
* **Coverage is unmeasured.** The 95% figure requested by the source
  specification is not claimed.
* `flake8` and `pylint-odoo` were not run; they could not be installed,
  as the shell had no network access.
* The module has never been installed or upgraded.

Sixteen specific technical assumptions are listed in
`doc/14_verification_register.md` §A, each with its risk and the effort
needed to correct it. The most likely to need adjustment is the stock
fixture in `tests/test_traceability.py`.

## Before you deploy

1. Read `doc/14_verification_register.md`.
2. Install on a clean 19.0 database, and again with demo data.
3. Run the suite; triage `test_traceability.py` first.
4. Measure coverage; run `flake8` and `pylint-odoo`.
5. Replace the `author` and `website` metadata.
6. Qualify the module against your own intended use.

## Upgrade notes

Not applicable; this is the first release.

## Compatibility

Odoo 19.0 Community only. The module uses `models.Constraint` and
`res.groups.privilege`, neither of which exists in Odoo 18 or earlier,
so it will not install on them.
