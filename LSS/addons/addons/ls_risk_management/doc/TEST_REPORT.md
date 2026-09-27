# Test Report

## Life Sciences Suite - Risk Management (`ls_risk_management`)

Date: 30 July 2026

---

## 1. Statement of execution status

**The automated tests described in this report have been written. They have
never been executed.**

No Odoo runtime and no PostgreSQL instance were available in the build
environment, and package installation was blocked because the shell had no
network access. It is therefore not possible to report a pass rate, a failure
count, or a coverage percentage.

The development framework for this suite sets a coverage target of 95%.
**That target has not been demonstrated.** No coverage measurement was
performed, because measuring coverage requires executing the tests. Any figure
stated here would be fabricated.

What this report can state is what was written, what it is designed to
exercise, and what was verified by other means.

---

## 2. Test inventory

| Module | Tests | Focus |
|---|---:|---|
| `test_matrix.py` | 19 | Grid generation and idempotence, completeness gating, cell resolution, approval and obsolescence, single default per company, cross-matrix rejection, display names |
| `test_register.py` | 28 | Numbering, default matrix, lifecycle gating, derived evaluation from approved assessments only, initial versus current divergence, review date arithmetic, overdue flagging, the scheduled action, deletion guards, duplication reset, company constraints |
| `test_assessment.py` | 22 | Matrix inheritance, evaluation resolution, ordinal index, rationale requirement, approval segregation of duties, unapproved matrix rejection, immutability after approval, single initial assessment, wrong scale and wrong matrix rejection |
| `test_mitigation.py` | 18 | Control option priority and ordering, the full four-step verification path, evidence requirements, segregation between implementation and effectiveness verification, immutability after verification, new risk declaration and promotion, overdue flagging |
| `test_fmea.py` | 29 | RPN arithmetic including both scale bounds, both action thresholds, threshold change recomputation, revised RPN and reduction, rating range constraints, worksheet statistics, review and approval gating, closure with open actions, revision copying, promotion to the register |
| `test_wizards.py` | 16 | Batch assessment, mixed-matrix rejection, residual acceptance including the benefit-risk requirement and non-repeatability, closure gating, cancellation guards for all four cancel wizards |
| `test_security.py` | 17 | Read/write/create/unlink enforcement per group, configuration protection from analysts, manager-only wizard access, multi-company isolation, record rule scope |
| `test_install.py` | 12 | Model registration, ACL coverage of every model, group installation and implication, privilege linkage, sequences, cron, shipped data state, reports, menus, clause map integrity |
| **Total** | **161** | |

Shared fixtures live in `tests/common.py`: three role-separated users created
with `new_test_user` and group external identifiers, a second company for
isolation testing, and an approved square matrix whose corner cells are set so
that all three acceptability branches are reachable.

---

## 3. Requirements coverage by design

Each row states which tests are intended to exercise a requirement. This is a
design mapping, not evidence of execution.

| Requirement | Intended coverage |
|---|---|
| Acceptability criteria are data, never code | `test_matrix` approval gating; `test_install.test_example_matrix_ships_unapproved` |
| An assessment cannot be approved by its author | `test_assessment.test_approve_blocks_self_approval` |
| An assessment cannot be approved by a non-manager through the ORM | `test_assessment.test_approve_requires_manager_role` |
| An approved assessment is immutable | `test_assessment.test_approved_assessment_is_immutable` |
| Effectiveness cannot be verified by the implementation verifier | `test_mitigation.test_effectiveness_blocks_same_verifier` |
| Residual acceptance requires a benefit-risk analysis when not acceptable | `test_wizards.test_residual_wizard_requires_benefit_risk` |
| A risk cannot be closed without the required residual decision | `test_wizards.test_close_wizard_requires_residual_decision` |
| Records are not deleted once they carry evidence | `test_register`, `test_assessment`, `test_mitigation`, `test_fmea` unlink guards |
| Companies are isolated | `test_security` isolation tests |
| High severity requires action regardless of RPN | `test_fmea.test_action_required_by_severity_alone` |

---

## 4. What was actually verified

These results are real, reproducible in the build environment, and were
obtained on 30 July 2026.

| Check | Method | Result |
|---|---|---|
| Python syntax, all 21 files | `python3 -m py_compile` | **Pass** |
| XML well-formedness, all 16 files | `lxml.etree.parse` | **Pass** |
| Static analysis | `static_check.py` | **Pass**, no findings |
| Static analyser credibility | `negative_controls.py`, 22 fault injections | **22/22 detected**, clean baseline |

The static analyser verifies: every view field resolves on its model including
inside embedded views; every object button method exists; every external
identifier resolves; every model has an ACL and every ACL resolves; the
manifest and the files on disk agree; no forbidden token, no raw SQL, no
`<tree>`, no `_sql_constraints`; and a PEP 8 subset.

The negative controls matter more than the clean result. A checker that has
never been shown to fail proves nothing, so 22 deliberate faults were injected
one at a time into throwaway copies of the module and each was confirmed to be
reported.

---

## 5. What was not verified

| Not verified | Why |
|---|---|
| That the module installs | No Odoo runtime |
| That any test passes | No Odoo runtime |
| Test coverage percentage | Requires execution |
| `flake8`, `pylint`, `pylint-odoo` | No network access, so no package installation |
| That the views render | No web client |
| That the QWeb reports produce a PDF | No wkhtmltopdf and no runtime |
| That the scheduled action runs under a real cron | No runtime |
| Behaviour under concurrent access | No database |
| Performance at scale | No database |

---

## 6. Required actions before use

1. Install on an Odoo 19.0 Community instance and record the outcome.
2. Execute the test suite and record the actual pass rate.
3. Measure coverage and record the actual figure against the 95% target.
4. Run `flake8`, `pylint` and `pylint-odoo` and resolve any findings.
5. Render both PDF reports and confirm the layouts.
6. Confirm the runtime items listed in `VERIFICATION_LOG.md` section 1.2,
   particularly the `<chatter/>` element, the `res.groups.privilege` records
   and the `ir.cron` field set.
7. Complete installation, operational and performance qualification under your
   own validation procedures.
