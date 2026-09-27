# Changelog

All notable changes to `ls_complaint` are recorded here. The format follows
Keep a Changelog, and the versioning follows the Odoo convention
`<odoo-version>.<major>.<minor>.<patch>`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-04: the 5 database constraints are declared with `models.Constraint`.
- The product-required and reportability-rationale rules are also checked when the state changes (the state is now a trigger of the constraints).
- F-27: the viewer role implies Internal User.
- Tests ported (F-40): `user_ids` instead of `users`, Odoo 19 boolean search operator, onchange tested on a form record.

## [19.0.1.0.0] — 2026-07-28

### Added
- `ls.complaint`: complaint master record with a seven-state machine
  (Received, Assessment, Investigation, CAPA Required, Resolution, Closed,
  Cancelled), 64 fields, sequence-generated reference, message tracking.
- `ls.complaint.category`: configuration model carrying the classification and
  the four configurable time targets, all defaulting to *not configured*.
- `ls.complaint.investigation`: root cause analysis with methodology, root cause
  category and description, conclusion, batch impact assessment, and an approval
  refused to the investigator of the record.
- `ls.complaint.adverse_event`: vigilance record with seriousness, outcome,
  causality, pseudonymised subject data, reportability decision with a mandatory
  rationale, configurable reporting deadline and submission tracking.
- `ls.complaint.resolution`: action record requiring completion evidence.
- `ls.complaint.close.wizard` and `ls.complaint.cancel.wizard`.
- Four cumulative access levels, 21 access rules, 5 global multi-company record
  rules, 2 write record rules implementing ownership segregation.
- Freezing of closed and cancelled complaints, approved and rejected
  investigations, done and cancelled resolutions, closed adverse events.
- Deletion blocked for any record past its initial state.
- Two daily scheduled actions for overdue complaints and overdue adverse event
  reports, both idempotent and bounded.
- QWeb PDF complaint record report.
- List, form, search, graph and pivot views; two mail templates; three
  sequences; demonstration data.
- 103 tests across 9 files.
- 15 documents, including an explicit verification and limitation register.

### Deliberately not included
- Any hard-coded regulatory deadline, threshold or classification.
- A dependency on `ls_qms` or `ls_capa`, which do not exist.
- A kanban view, whose Odoo 19 template API could not be verified offline.
- A `.pot` translation template, which requires a running Odoo instance.
- Electronic signatures and a tamper-evident audit trail, which the source
  specification allocates to `ls_electronic_signature` and `ls_audit_trail`.

### Known gaps
- The module was never installed, executed or tested. See
  `docs/00_verification_and_limitations.md`.
- No coverage figure exists. See `docs/06_test_report.md`.
- `flake8`, `pylint` and `pylint-odoo` were never run. See
  `docs/07_static_analysis_report.md`.

## [Planned]
- `ls_complaint_capa` bridge module once `ls_capa` exists.
- Upgrade tests, meaningful from version 19.0.1.1.0 onwards.
- Kanban view, once the target instance API is confirmed.
- Translation template and a first language.
