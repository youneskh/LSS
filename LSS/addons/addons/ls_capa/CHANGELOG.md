# Changelog

All notable changes to `ls_capa` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions use the Odoo convention `<odoo-version>.<major>.<minor>.<patch>`.

---

## 19.0.1.0.2 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-04: the 6 database constraints are declared with `models.Constraint`.
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards.
- Tests ported (F-40): date fixtures, Odoo 19 boolean search operator, task deadline as datetime.

## [19.0.1.0.1] — 2026-08 — Install fix

### Fixed

- **Installation failure on Odoo 19.** The `ir.cron` record declared the
  `numbercall` and `doall` fields, which were removed from `ir.cron` as
  of Odoo 18. Installing against Odoo 19 raised
  `ValueError: Invalid field 'numbercall' in 'ir.cron'` and aborted the
  module load. Both fields were removed; the scheduled action now relies
  solely on `interval_number` and `interval_type`. No functional change
  to the notification behaviour. Reported from a live install alongside
  `ls_audit_trail` and `tracking_manager`.

---

## [19.0.1.0.0] — 2026-07 — Release candidate

### Added

- `ls.capa.issue`: CAPA record with the eight-state lifecycle
  (Identified, Assessed, Investigation, Action Planning, In Progress,
  Completed, Verified, Closed), classification by source, type,
  severity, priority and category, impact assessment, computed progress
  and searchable overdue flag.
- `ls.capa.root_cause`: root cause analysis supporting Five Whys,
  Ishikawa and FMEA, with computed Risk Priority Number and a draft to
  confirmed lifecycle.
- `ls.capa.action`: corrective and preventive actions with mandatory
  completion evidence, mandatory cancellation reason, searchable late
  flag and optional `project.task` generation.
- `ls.capa.effectiveness`: effectiveness verification against
  pre-defined acceptance criteria, with follow-up CAPA escalation.
- `ls.capa.category`: configurable classification with a default
  resolution lead time; five categories preloaded.
- `ls.capa.close.wizard`: closure wizard capturing the mandatory
  closure summary.
- Security: four groups under a `res.groups.privilege` record, 20
  access control lines, five global multi-company record rules.
- Views: form, list, kanban, search, pivot and graph for CAPA records;
  form, list and search for child models; editable list for categories.
- Reporting: QWeb PDF report covering the full CAPA record.
- Data: four sequences, five default categories, one scheduled action
  for overdue notification shipped inactive.
- Testing: 112 automated tests across seven modules.
- Documentation: README, installation, configuration, user,
  administrator and developer manuals, generated API reference, phase
  report, test report and validation report.
- Tooling: `.flake8`, `.pylintrc`, `.pre-commit-config.yaml` and a
  GitHub Actions workflow running lint, install, tests, a 95% coverage
  threshold and an upgrade test.

### Fixed during authoring

- Removed an invalid keyword argument on `ls.capa.root_cause.issue_id`
  that would have raised `TypeError` at registry load.
- Refactored three lines exceeding the 79-column limit.
- Corrected the documented test count from an unverified 88 to the
  measured 112.
- Removed the `numbercall` and `doall` fields from the `ir.cron` record.
  Both were removed from `ir.cron` as of Odoo 18 and their presence
  raised `ValueError: Invalid field 'numbercall' in 'ir.cron'` on
  installation against Odoo 19. Recurrence now uses only
  `interval_number` and `interval_type`. This was found by an actual
  install attempt, not by the pre-install static checks — the static
  checks cannot know a core field was dropped.

### Known limitations

- Electronic signatures not implemented; belongs to
  `ls_electronic_signature`.
- Audit trail is `mail.thread` tracking, not tamper-evident.
- No `ls_qms` dependency; see architectural decision AD-01.

### Not yet performed

- Execution against a live Odoo 19 instance.
- Coverage measurement.
- `flake8` and `pylint-odoo` execution.
- Upgrade test.
- Computerised system validation.
