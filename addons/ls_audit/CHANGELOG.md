# Changelog

All notable changes to `ls_audit` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the module
uses the Odoo five-component version scheme `19.0.MAJOR.MINOR.PATCH`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-04: the 10 database constraints declared with the removed `_sql_constraints` are declared with `models.Constraint` and are created again (unique references and codes, checklist version > 0, one qualification per auditor and company).
- F-42: the daily auditor qualification job saves the recomputed status (stored computed fields are recomputed through the ORM).
- F-23: deletion guards use `@api.ondelete(at_uninstall=False)` instead of raising in `unlink()`.
- Reports: `t-field` moved from table cells to inner `<span>` (Odoo 19 refuses widgets on `td`).
- Tests ported to Odoo 19 (F-40): programme approved before scheduling, `all_group_ids`, recursion error type.

## [19.0.1.0.0] — 2026-07-24

Initial release. Targets Odoo 19.0 Community Edition.

### Added

**Configuration**
- `ls.audit.type` — audit classification, internal or external, with an
  optional default checklist.
- `ls.audit.area` — hierarchical auditable areas with an owner, used for
  the auditor independence check.
- `ls.audit.auditor` — auditor qualification register with expiry, lead
  auditor flag, qualified scope and a computed qualification status.
- `ls.audit.finding.category` — severity, response deadline, and whether a
  root cause and a CAPA reference are mandatory. Five categories shipped as
  non-updatable master data.

**Checklists**
- `ls.audit.checklist` / `ls.audit.checklist.line` — versioned templates
  with a draft/approved/obsolete lifecycle. Approved checklists are
  immutable; changes require a new version.

**Workflow**
- `ls.audit.program` — periodic audit programme with completion statistics.
- `ls.audit.schedule` — the audit engagement, with a six-state lifecycle,
  conformity rate, finding counts and an overdue flag.
- `ls.audit.response` — one assessed question, with the question text
  copied from the template at load time.
- `ls.audit.finding` — six-state finding lifecycle with deadline
  computation from the category and mandatory verification before closure.
- `ls.audit.report` — four-state report lifecycle with prepare, review,
  approve and issue as separate, separately-attributed acts.

**Wizards**
- Checklist load, finding response, and a generic cancellation wizard that
  requires a written justification.

**Security**
- Four hierarchical groups: auditee, auditor, lead auditor, manager.
- 37 access rules and 10 global multi-company record rules, plus row-level
  rules restricting auditees to their own records and to issued reports on
  which they appear as recipients.

**Automation**
- Three scheduled actions: overdue audits, overdue findings, expiring
  auditor qualifications.

**Reporting**
- Two QWeb PDF reports: the audit report and the finding notice.

**Other**
- Demo data covering a full audit setup with four independent users.
- 11 test modules.
- Translation template covering the Python strings.

### Notes

- The approvals in this release are **not** 21 CFR Part 11 electronic
  signatures. See README §1.2.
- The test suite has **not** been executed. See README §1.3, item 1.
