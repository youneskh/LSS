# Changelog

All notable changes to `ls_qms` are recorded here, under an Added, Changed,
Fixed, Removed structure. Versions follow the Odoo convention: the Odoo
series, then the module version.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-39: quality plans carry `previous_revision_id` / `next_revision_ids`, so a quality plan can be revised.
- F-24: `_check_company_auto` on objectives, quality plan lines, quality records and work instructions.
- F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

## 19.0.1.0.0 — July 2026

### Added

* Abstract model `ls.qms.parameter.mixin` reading the four system parameters
  with validated fallbacks.
* Abstract model `ls.qms.document.mixin` implementing the six state document
  lifecycle, the revision chain, the periodic review, the freezing of
  published content and the deletion guards.
* Models `ls.qms.policy`, `ls.qms.sop`, `ls.qms.work_instruction`,
  `ls.qms.quality_plan` and `ls.qms.quality_plan.line`.
* Models `ls.qms.objective` and `ls.qms.objective.measurement`, with the four
  documented achievement formulas and a performance status compared with the
  elapsed share of the period.
* Model `ls.qms.quality_record` with retention control, protection of
  confirmed evidence and manager controlled disposal.
* Four security groups under an Odoo 19 privilege, 26 access control list
  rows and eight global record rules.
* Six numbering sequences, three activity types, four system parameters and
  three scheduled actions.
* Two wizards, new revision and rejection, both requiring a written reason.
* Three PDF reports carrying a control block and an uncontrolled copy notice.
* Demonstration data covering every model.
* Eleven test modules and one fixture module, 115 test methods.
* Fourteen documents under `docs/`.

### Fixed during development

* `previous_revision_id` was declared on the abstract mixin, which Odoo cannot
  instantiate. Moved to each concrete model as a self reference.
* `achievement_rate` used the percentage widget, which expects a ratio between
  zero and one and would have displayed a rate of 45 as 4500 percent. The
  widget was removed.

### Known limitations

* Authenticated electronic signature is not implemented; an extension point
  is provided.
* Field level audit trail is not implemented; `mail.thread` tracking only.
* No translation template is shipped; the export command is documented.
* The module has not been installed, executed, tested or linted by its
  author. See `docs/12_test_report.md` and `docs/13_validation_report.md`.
