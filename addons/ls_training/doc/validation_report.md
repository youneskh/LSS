# VALIDATION REPORT

Module: `ls_training` · Version 19.0.1.0.0 · July 2026

---

## 1. Purpose and status

This document reports the state of the module against the ten-phase
development framework, and provides the requirement traceability needed to
begin a formal computer system validation.

**This is not a validation certificate.** Validation is performed by the
implementing organisation, in its own environment, against its own User
Requirements Specification, under its own quality system. This document is
an input to that activity, not a substitute for it.

## 2. Phase gate summary

| Phase | Deliverable | Outcome |
|-------|-------------|---------|
| 1 — Business Analysis | `business_analysis.md` | **PASS** |
| 2 — Regulatory Analysis | `regulatory_analysis.md` | **PASS** |
| 3 — Functional Specification | `functional_specification.md` | **PASS** |
| 4 — Technical Specification | `technical_specification.md` | **PASS** |
| 5 — Architecture Review | `architecture_review.md` | **PASS** (3 accepted limitations, 1 open finding) |
| 6 — Development | source code | **PASS** |
| 7 — Testing | 146 tests written | **CONDITIONAL PASS** — never executed |
| 8 — Static Analysis | 11 checks executed | **CONDITIONAL PASS** — flake8/pylint-odoo unavailable offline |
| 9 — Documentation | 16 documents | **PASS** |
| 10 — Final Validation | this report | **CONDITIONAL PASS** |

**Overall: the module is complete as an artefact and is not yet proven as a
running system.** It is releasable to a validation environment. It is not
releasable to production until §7 is closed.

## 3. Requirement traceability

| Req | Requirement | Implementation | Test |
|-----|-------------|----------------|------|
| BR-01 | Course code, version, duration, type | `ls.training.course` fields | `test_course.py` |
| BR-02 | Course approval lifecycle | `state` + 4 action methods | `test_workflow_draft_to_approved` |
| BR-03 | Certification validity period | `validity_months` | `test_expiry_derived_from_course_validity` |
| BR-04 | Assessment requirement and pass mark | `requires_assessment`, `pass_score` | `test_pass_score_bounds` |
| BR-05 | Course grants competencies | `competency_ids` | `test_competency.py` |
| BR-06 | Retired courses unschedulable | `action_set_obsolete` + domain | `test_obsolete_blocked_by_open_sessions` |
| BR-07 | Sessions schedule approved courses | `course_id` domain state=approved | `test_session_workflow.py` |
| BR-08 | Individual and bulk registration | register wizard, 4 modes | `test_wizards.py` (5 tests) |
| BR-09 | Capacity enforced | `_check_capacity` | `test_capacity_enforced` |
| BR-10 | Exactly one trainer | `_check_trainer` | `test_single_trainer_only` |
| BR-11 | Attendance and score per attendee | `ls.training.attendance` | `test_session_workflow.py` |
| BR-12 | No closure while outcome pending | `action_close` guard | `test_close_blocked_by_pending_attendance` |
| BR-13 | Automatic issuance on closure | `action_close` + `_prepare_from_attendance` | `test_full_workflow_issues_certification` |
| BR-14 | Manual external certification | direct create, `session_id` empty | `test_certification.py` |
| BR-15 | Course version frozen | `create` override | `test_course_version_frozen_on_creation` |
| BR-16 | Expiry derived, overridable | computed store readonly=False | `test_expiry_can_be_overridden` |
| BR-17 | Renewal preserves history | new record per issuance | `test_renewal_keeps_history` |
| BR-18 | Revocation with reason, no deletion | `_check_revocation_reason`, `unlink` raises | `test_certifications_cannot_be_deleted` |
| BR-19 | Printable certificate | QWeb report | *manual verification required* |
| BR-20 | Requirements by job/department/employee | `ls.training.requirement` | `test_requirement_matrix.py` (4 tests) |
| BR-21 | Mandatory vs advisory | `mandatory` | `test_non_mandatory_excluded_from_compliance` |
| BR-22 | Training matrix | matrix wizard | `test_matrix_generation` |
| BR-23 | Compliance rate per employee | `_compute_ls_training_compliance` | `test_compliance_rate_with_certification` |
| BR-24 | Individual training record | QWeb report | *manual verification required* |
| BR-25 | Competency master data | `ls.training.competency` | `test_competency.py` |
| BR-26 | Named assessor with evidence | `assessor_id`, `evidence` | `test_confirm_requires_evidence` |
| BR-27 | No self-assessment | `_check_assessor_not_employee` | `test_self_assessment_forbidden` |
| BR-28 | Confirmed assessments read-only | `write`/`unlink` overrides | `test_confirm_locks_the_record` |
| BR-29 | Periodic reassessment | `reassessment_months`, `date_next` | `test_next_assessment_date_computed` |
| BR-30 | Expiry notification | `_cron_send_expiry_reminders` | `test_reminder_queues_mail_for_expiring` |
| BR-31 | Configurable window | `_get_expiry_warning_days` | `test_warning_window_from_parameter` |
| BR-32 | Automatic status refresh | `_cron_refresh_certification_state` | `test_refresh_updates_expired_status` |

**32 of 32 requirements implemented. 30 of 32 have automated test coverage.**
BR-19 and BR-24 are PDF rendering and require visual verification on a
running instance.

## 4. Compliance checklist (Phase 10)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Follows official Odoo module architecture | **PASS** | `architecture_review.md` §2 |
| 2 | Follows OCA practices where applicable | **PASS** | `architecture_review.md` §3 |
| 3 | Odoo 19 Community only, no Enterprise code | **PASS** | Depends on `base`, `mail`, `hr` only |
| 4 | Odoo core not modified | **PASS** | Single `_inherit` on `hr.employee` |
| 5 | Inheritance used rather than replacement | **PASS** | Prefixed fields, no overridden core method |
| 6 | MVC / ORM separation respected | **PASS** | No business logic in views |
| 7 | SQL injection prevented | **PASS** | No raw SQL in shipped code |
| 8 | XSS prevented | **PASS** | No custom JS, no `t-raw` |
| 9 | Input validated | **PASS** | 8 SQL + 18 Python constraints |
| 10 | Access rights respected | **PASS** | 31 ACL lines across 4 groups |
| 11 | Record rules respected | **PASS** | 13 rules; see caveat #21 |
| 12 | No placeholders, TODO or FIXME | **PASS** | Static check, 0 found |
| 13 | No dead or commented-out code | **PASS** | Manual review + static check |
| 14 | Complete docstrings | **PASS** | 264/264 definitions |
| 15 | PEP 8 line length and whitespace | **PASS** | 0 violations |
| 16 | Fully documented | **PASS** | 16 documents |
| 17 | Fully tested (written) | **PASS** | 146 tests, all constraints and transitions |
| 18 | Tests executed | **FAIL — not performed** | No runtime |
| 19 | Coverage ≥ 95% measured | **FAIL — not measured** | No runtime |
| 20 | Installs successfully | **NOT VERIFIED** | No runtime |
| 21 | Upgrade safe | **NOT VERIFIED** | No runtime; one API assumption open (`verification_notes.md` §2) |
| 22 | No false compliance claim | **PASS** | `regulatory_analysis.md` §1 and §3.5 |

## 5. Data integrity controls implemented

| Control | Mechanism |
|---------|-----------|
| Outcome reproducible from evidence | `attendance.result` computed, not writable |
| Historical accuracy preserved | `course_version` frozen at issuance |
| Evidence not retroactively alterable | write/unlink guards on closed sessions and attendance |
| Records not destroyable | `certification.unlink` always raises |
| Withdrawal traceable | revocation requires a written reason |
| Complete history retained | renewal creates records; failures retained |
| Sequencing enforced | two state machines with explicit guards |
| Authorisation enforced | 4 groups, 31 ACL lines, 13 record rules |
| Company isolation | 7 global multi-company rules |

## 6. Known limitations carried into validation

| ID | Limitation | Disposition |
|----|-----------|-------------|
| L-1 | Matrix generation is O(employees × courses) queries | Bounded at 20 000 lines; performance-test before production |
| L-2 | Compliance rate not stored, so not searchable | Use the matrix wizard for bulk reporting |
| L-3 | No counter-approval on session closure | Integrate `ls_electronic_signature` if segregation of duties is required |
| L-4 | No electronic signature | Out of scope; do not claim Part 11 |
| L-5 | No field-level audit trail | Out of scope; integrate `ls_audit_trail` |
| L-6 | No retention scheduling | Handled by database backup policy |
| L-7 | Reminders repeat daily and do not escalate | Documented in the administrator manual |
| L-8 | Trainer qualification not enforced | Documented technical debt |
| L-9 | One Manager can submit and approve a course | Enforce procedurally or extend |
| L-10 | Employees without a linked user see nothing | Administrator checklist item |

## 7. Conditions for production release

Production release is **not recommended** until all of the following are
closed:

| # | Condition |
|---|-----------|
| 1 | Module installs on a clean Odoo 19 Community database |
| 2 | Module upgrades cleanly from 19.0.1.0.0 to itself |
| 3 | All 146 tests execute; all failures resolved |
| 4 | Coverage measured and reported |
| 5 | `flake8` and `pylint-odoo` run; blocking findings resolved |
| 6 | BR-19 and BR-24 PDF outputs visually verified |
| 7 | Matrix performance verified at production population size |
| 8 | The `ir.rule` API assumption confirmed or the alternate file adopted |
| 9 | Organisation-specific URS written and traced to this specification |
| 10 | IQ/OQ/PQ executed under the organisation's own validation procedure |

## 8. Signatures

This document carries no electronic signature. The module does not
implement electronic signatures (`regulatory_analysis.md` §3.5). Approval
of this report must be recorded through the organisation's own controlled
process.

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer (Quality) | | | |
| Approver (Validation) | | | |
