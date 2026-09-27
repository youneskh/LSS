# CHANGELOG

All notable changes to `ls_training` are recorded here.
Format based on Keep a Changelog. Versioning follows the Odoo convention
`<odoo_version>.<major>.<minor>.<patch>`.

---

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-04: the 8 database constraints are declared with `models.Constraint`.
- F-42: the daily certification job saves the recomputed status.
- Session capacity is checked when an attendance is added; a requirement without target is refused on creation.
- F-44: demo data loaded with `noupdate="1"`. F-27: the learner role implies Internal User. Tests ported (F-40).

## [19.0.1.0.0] — 2026-07

### Added

**Models**
- `ls.training.course` — course master data with a four-state approval
  lifecycle (draft, review, approved, obsolete), versioning, delivery
  modes, validity period and assessment configuration.
- `ls.training.session` — five-state delivery lifecycle (draft, confirmed,
  in progress, done, cancelled) with capacity control and trainer
  assignment.
- `ls.training.attendance` — presence and score capture with a derived,
  non-writable pass/fail outcome.
- `ls.training.certification` — append-only qualification records with a
  frozen course version, derived expiry, four-state status and revocation.
- `ls.training.competency` — competency master data with minimum
  acceptable level and reassessment interval.
- `ls.training.competency.assessment` — assessed competence with named
  assessor, written evidence and a confirmation lock.
- `ls.training.requirement` — role-, department- or individual-based
  training requirements.
- `hr.employee` extension — training tab, certification and assessment
  lists, compliance counters and rate.

**Wizards**
- Bulk session registration with four selection modes and an
  already-certified exclusion.
- Training matrix generation, scoped by company, department and job
  position, with a 20 000-line guard.

**Automation**
- Daily scheduled action refreshing certification status.
- Daily scheduled action sending expiry reminders.
- Configurable warning window via `ls_training.expiry_warning_days`.
- Email template for expiry reminders.
- Three sequences for course, session and certification references.

**Reporting**
- Training Certificate QWeb PDF report.
- Individual Training Record QWeb PDF report.
- List, form, search, calendar and pivot views across all models.

**Security**
- Four cumulative groups: Learner, Viewer, Trainer, Manager, under an
  Odoo 19 `res.groups.privilege`.
- 31 access-control lines.
- 13 record rules: 7 global multi-company, 3 Learner self-scope, 3 Viewer
  full-scope.

**Documentation**
- 16 documents covering all ten development phases, plus
  `verification_notes.md` recording every unverified API assumption.

**Tests**
- 146 test methods across 8 modules with a shared fixture.

### Known issues

- The test suite has never been executed. See `test_report.md`.
- The `ir.rule` group field name for Odoo 19 could not be verified. Both
  variants ship; see `verification_notes.md` §2.
- Four further Odoo 19 API assumptions are unverified; see
  `verification_notes.md` §3–§6.
