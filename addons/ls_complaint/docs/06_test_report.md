# Phase 7 — Test Report

## 1. Execution status — read this first

**The tests were written but NOT executed.** No Odoo runtime exists in the build
environment and the network is disabled, so `odoo-bin --test-enable` could never
be run. Consequently:

- **No test result is reported as passed.**
- **No coverage figure is reported.** The 95% target of the assignment is
  **not demonstrated** and must not be claimed.
- The only executed verification is the static analysis of Phase 8.

What follows is the **test design** and the **procedure** by which the deploying
organisation obtains the missing evidence.

## 2. Test suite inventory

| File | Test methods |
|---|---|
| `test_adverse_event.py` | 18 |
| `test_category.py` | 5 |
| `test_complaint_constraints.py` | 20 |
| `test_complaint_security.py` | 9 |
| `test_complaint_workflow.py` | 18 |
| `test_cron_and_reports.py` | 8 |
| `test_investigation.py` | 13 |
| `test_resolution.py` | 7 |
| `test_wizards.py` | 5 |
| **Total** | **103** |

All tests inherit `TransactionCase` through `tests/common.py` and are tagged
`post_install, -at_install`, so they run against the fully loaded registry.

## 3. Coverage by test level

| Level required by the assignment | Where it is covered |
|---|---|
| Unit tests | Constraints, computes, onchanges, search methods, helpers: `test_complaint_constraints`, `test_category` |
| Integration tests | Parent/child interaction, closure preconditions depending on children, stored related company: `test_complaint_workflow`, `test_investigation`, `test_adverse_event` |
| Functional tests | End-to-end lifecycle from intake to frozen closure, waiver path, CAPA path, cancellation and reset: `test_complaint_workflow` |
| Security tests | Four groups, ACL, ownership record rule, multi-company rule presence, wizard restriction: `test_complaint_security` |
| Access-right tests | `test_01` to `test_07` of `test_complaint_security` |
| Constraint tests | 20 tests in `test_complaint_constraints` plus per-model constraint tests |
| Workflow tests | Every transition and every refused transition of the four state machines |
| Installation tests | **Partially covered.** `test_cron_and_reports` asserts that sequences, crons and mail templates are present after installation, and that the report renders. Actual installation on Odoo 19 is not covered — see section 1. |
| Upgrade tests | **Not covered.** There is no previous version to upgrade from; the module is at `19.0.1.0.0`. An upgrade test becomes meaningful at version 1.1.0 and is listed in `CHANGELOG.md` as a planned item. |
| Performance tests | **Not covered.** Meaningful performance measurement requires a populated database and a target hardware profile, neither of which exists here. The performance design review is in `docs/05_architecture_review.md` section 11; measurement is the deploying organisation's PQ activity. |

Three of the ten required levels are therefore not delivered as executable
tests. That is stated here rather than disguised.

## 4. Requirement traceability

| Requirement | Test |
|---|---|
| BR-01 unique reference | `test_complaint_workflow.test_01` |
| BR-02 mandatory reception data | model `required=True` plus `test_complaint_security.test_02` |
| BR-03 product and lot | `test_complaint_constraints.test_06`, `test_08` |
| BR-04 configurable targets | `test_complaint_constraints.test_09`, `test_10`; `test_category.test_01` |
| BR-05 assessment before investigation | `test_complaint_workflow.test_04` |
| BR-06 adverse events as records | `test_adverse_event` (all) |
| BR-07 rationale mandatory | `test_adverse_event.test_05`, `test_14` |
| BR-08 approver ≠ investigator | `test_investigation.test_06`, `test_07` |
| BR-09 root cause description | `test_investigation.test_04`, `test_05` |
| BR-10 completion evidence | `test_resolution.test_03` |
| BR-11 closure preconditions | `test_complaint_workflow.test_08`, `test_11`, `test_17` |
| BR-12 reviewer ≠ responsible | `test_complaint_workflow.test_09`; `test_wizards.test_02` |
| BR-13 final records read-only | `test_complaint_workflow.test_16`; `test_investigation.test_09`; `test_resolution.test_05`; `test_adverse_event.test_11` |
| BR-14 no deletion after intake | `test_complaint_constraints.test_17`; `test_investigation.test_10`; `test_resolution.test_06`; `test_adverse_event.test_17` |
| BR-15 cancellation with reason | `test_complaint_workflow.test_14`; `test_wizards.test_05` |
| BR-16 analysable | search methods tested in `test_complaint_constraints.test_11`, `test_adverse_event.test_15` |
| BR-17 printable record | `test_cron_and_reports.test_07` |
| BR-18 overdue notification | `test_cron_and_reports.test_01`, `test_02`, `test_03` |

Every one of the eighteen business requirements has at least one test.

## 5. Method coverage design

The module declares 83 methods, of which 26 are public `action_*` methods. Each
`action_*` method has at least one test exercising its success path, and each
one that raises has at least one test exercising the refusal. The intent is full
statement coverage of the model layer; **whether that intent is achieved is
unknown until the suite is run under `coverage`.**

Deliberately untested: Odoo framework behaviour itself (sequence generation
internals, `mail.thread` mechanics, view rendering by the web client).

## 6. How to obtain the missing evidence

```bash
# 1. Install the module and run its tests on a scratch database
odoo-bin -d ls_test -i ls_complaint --test-enable --stop-after-init \
         --log-level=test --without-demo=False

# 2. Repeat with coverage measurement
coverage run --source=/path/to/addons/ls_complaint \
    odoo-bin -d ls_test_cov -i ls_complaint --test-enable --stop-after-init
coverage report -m
coverage html

# 3. Re-run the tests after an update, to cover the upgrade path
odoo-bin -d ls_test -u ls_complaint --test-enable --stop-after-init
```

Record the console output, the coverage report and the database log as the test
evidence of the validation file.

## Phase 7 gate

**CONDITIONAL PASS.**

- Design of the test suite: **PASS** — 103 tests, every business requirement
  traced, seven of the ten required test levels delivered as executable tests.
- Execution and coverage: **NOT DEMONSTRATED** — the environment cannot run
  Odoo. This is a genuine gap against the assignment, not a passed gate.
- Upgrade and performance tests: **NOT DELIVERED**, with the reasons given in
  section 3.

The corrective action is section 6 and it must be performed by the deploying
organisation before this module is used.
