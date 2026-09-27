# Changelog

All notable changes to `ls_risk_management` are recorded here.
The format follows Keep a Changelog. Versioning is Odoo's
`19.0.<major>.<minor>.<patch>` convention.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-39: an FMEA revision copies its failure modes.
- Control completeness can be confirmed when no control measure is pending (a risk without measure is decided at the start of monitoring).
- Reports: `t-field` moved out of table cells. F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

## [19.0.1.0.0] - 2026-07-30

### Added

- Risk register (`ls.risk.register`) with a six-state lifecycle and the
  hazard, sequence of events, hazardous situation and harm chain recorded as
  separate fields.
- Configurable risk matrix (`ls.risk.matrix` with `.level` and `.cell`)
  holding organisation-defined acceptability criteria, with a draft, approved
  and obsolete lifecycle.
- Risk assessment (`ls.risk.assessment`) with four assessment types, matrix
  driven evaluation, and approval segregated from assessment at ORM level.
- Risk control measures (`ls.risk.mitigation`) with the three control option
  categories, separate implementation and effectiveness verification, and
  declaration of risks introduced by the measure itself.
- FMEA (`ls.risk.fmea` and `ls.risk.fmea.line`) with RPN computation, dual
  action thresholds, revised ratings, worksheet revisions, and promotion of a
  failure mode into the risk register.
- Hierarchical risk taxonomy (`ls.risk.category`) with 10 shipped categories.
- Six wizards: batch assessment, residual risk acceptance, risk closure, and
  cancellation of risks, assessments, control measures and FMEA worksheets.
- Three security groups with implication, 35 access control lines, and 9
  global multi-company record rules.
- Two QWeb PDF reports.
- A daily scheduled action notifying owners of overdue risk reviews.
- 161 automated tests across 8 modules.
- Offline static analyser with 22 negative controls.
- Documentation set of 12 documents, including a verification log recording
  every verified and unverified fact with its source.

### Known limitations

- The module has never been installed or executed. See `VALIDATION_REPORT.md`.
- No risk management plan or risk management file (deviation D-09).
- Approvals are not 21 CFR Part 11 electronic signatures (deviation D-10).
- No kanban view (deviation D-07).
- No ANPP or ICH Q9 mapping is claimed; neither could be verified.
