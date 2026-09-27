# Release Notes — ls_document_management 19.0.1.0.0

**Target:** Odoo 19 Community Edition
**Date:** July 2026
**Licence:** AGPL-3.0-or-later

## Summary

First release of the Life Sciences Suite Document Management module for
Odoo 19 Community. It provides controlled document management — folders,
immutable versioning, a formal review/approval lifecycle, retention policies,
control records and record linking — for regulated Life Sciences environments,
filling the gap left by the absence of the Enterprise Documents app in the
Community edition.

## Highlights

- Draft -> Under Review -> Approved -> Published -> Archived lifecycle with a
  revision loop that keeps the effective version in force during revision.
- Immutable versions with SHA-256 integrity checksums.
- Parallel approvals with enforced segregation of authoring and approval.
- Retention monitoring that never deletes records; legal hold supported.
- Folder-level access control enforced by record rules, not just the UI.
- Document Control Record PDF.

## Compatibility

- Requires Odoo 19 Community (`base`, `mail`).
- Built specifically against Odoo 19 APIs (`models.Constraint`,
  `Many2oneReference`, `<list>`, `<chatter/>`, `res.groups.privilege`,
  `group_ids`, cron without `numbercall`/`doall`). It will not run unmodified
  on Odoo 18 or earlier.

## Important notice for adopters

This release is **code-complete and passes an offline static self-check**, but
its automated tests were **not executed** and it was **not installed** in the
build environment, which lacked an Odoo runtime and network access. Before
production use, the implementing team must:

1. Install on a clean Odoo 19 Community instance.
2. Run the test suite (`--test-enable`) and review results.
3. Run `flake8` and `pylint-odoo`.

See `validation_report.md` for the full, itemised status.

## Regulatory notice

The module **supports** document-control processes; it does **not** by itself
confer compliance with ISO 13485, 21 CFR Part 11, EU GMP Annex 11 or any other
framework, and the approval feature is **not** a Part 11 electronic signature.
Computer system validation and quality procedures remain the organisation's
responsibility.

## Known limitations

No electronic signature, no cross-model field-level audit trail, no full-text
content search, no automated record destruction (by design). See the changelog.
