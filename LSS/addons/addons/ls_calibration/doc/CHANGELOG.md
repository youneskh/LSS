# Changelog

All notable changes to `ls_calibration` are recorded here. The format follows
Keep a Changelog, and the module uses the Odoo versioning scheme
`19.0.MAJOR.MINOR.PATCH`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-18: the dead parallel implementation is removed (13 Python files, 14 XML files, 3 test files that were never loaded).
- F-23: `@api.ondelete` deletion guards. Tests ported (F-40): constraint assertions without tuple `assertRaises`.

## [19.0.1.0.0] — July 2026

First release.

### Added

* Instrument register `ls.calibration.instrument` with metrological data,
  criticality, GxP impact, life cycle states, and a calibration status
  computed at read time.
* Calibration plans `ls.calibration.plan` with interval, written procedure
  reference, externalisation, and a due date derived from the last approved
  calibration.
* Test points `ls.calibration.plan.point` with absolute or relative
  tolerances and computed acceptance limits.
* Calibration records `ls.calibration.record` with reference standards,
  ambient conditions, a review and approval workflow, and locking after
  approval.
* Test point results `ls.calibration.record.line` with as-found and as-left
  readings, deviations and verdicts.
* Calibration certificates `ls.calibration.certificate`, internal or
  external, with the certificate document attached.
* Segregation of duties: the performer of a calibration cannot approve it.
* Mandatory impact assessment on an out-of-tolerance as-found result.
* Refusal of a reference standard whose own calibration is overdue.
* Two scheduled actions: notification of the due and overdue instruments,
  generation of the calibration records of the due plans.
* Two wizards: bulk generation of calibration records, rejection with a
  mandatory reason.
* Two QWeb PDF reports: calibration record, calibration certificate.
* Three security groups, 21 access rules, six multi-company record rules.
* Four sequences, one system parameter.
* 101 automated tests across nine modules.
* Seventeen documents covering the ten phases of the development framework.

### Known limitations

See `doc/14_validation_report.md`, section 4.
