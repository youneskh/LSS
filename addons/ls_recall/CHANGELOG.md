# Changelog

All notable changes to `ls_recall` are recorded here.
Format based on Keep a Changelog; versioning follows the Odoo
convention `<odoo-version>.<major>.<minor>.<patch>`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-03: the lot indicators are computed with superuser rights, so inventory users without a recall role can open lots.
- F-06: a customer delivery of a lot named in an open recall (rehearsals excluded) is refused.
- F-07: tracing follows the lots produced from the recalled lots (`produce_line_ids`, recursively). F-17: quantities in the product unit; stock data read on behalf of the coordinator; recall viewers read lots and transfers.
- F-35: effectiveness checks are generated (consignee precomputed and passed explicitly). Plan revisions no longer violate the reference constraint (unique per version).
- F-27: the viewer role implies Internal User. Tests ported (F-40).

## [19.0.1.0.0] — 2026-07-27

Initial release.

### Added

* `ls.recall.plan` — versioned recall plan with review, approval,
  revision and rehearsal scheduling.
* `ls.recall.execution` — field action with a seven-state gated
  workflow, distribution tracing, reconciliation and closure gating.
* `ls.recall.line` — per-consignee, per-lot reconciliation.
* `ls.recall.communication` — controlled communications with five
  mandatory content confirmations on notices.
* `ls.recall.effectiveness` — effectiveness checks with sampling levels
  A to E, escalation and repeat attempts.
* `ls.recall.report` — status and final reports with figures frozen on
  approval and reviewer/approver separation.
* `stock.lot` extension — under-recall ribbon and smart button.
* Two wizards: initiate and close/cancel.
* Three security roles, 22 access rules, six global multi-company rules.
* Two scheduled actions, both activity-only.
* Two QWeb documents: recall notice and recall report.
* 99 automated tests.
* 15 documents plus this changelog.

### Deviations from the source specification

* **D-01** Dependencies reduced to `mail` and `stock`; `ls_qms` and
  `ls_complaint` do not exist. Couplings preserved as reference fields.
* **D-02** Added `ls.recall.line` and `ls.recall.effectiveness`, without
  which the specification's own effectiveness-check state has nothing to
  operate on.
* **D-03** `stock.lot` used instead of the specification's
  `stock.production.lot`, which was renamed in Odoo 16.
* **D-04** Added a `cancelled` state, so a reversed decision can be
  recorded rather than deleted or falsely closed.

### Not implemented, deliberately

* 21 CFR Part 11 electronic signatures.
* Field-level audit trail.
* Outbound sending of communications.
* Automatic stock quarantine.

### Known open items

The test suite has not been executed and coverage is unmeasured.
`flake8` and `pylint-odoo` have not been run. See
`doc/14_verification_register.md`.
