# Phase 7 — Test Report

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS for test design and authoring;
execution NOT performed in the build environment — see §7.1**

---

## 7.1 Statement of what was and was not executed

This section is deliberately first, because everything else in this report
depends on it.

**What was executed in the build environment:**

| Check | Tool | Result |
|-------|------|--------|
| Every Python file compiles | `python -m py_compile` | Pass, all 33 files |
| Every XML file is well formed | `lxml.etree.parse` | Pass, all 33 files |
| Module-wide consistency checks | `tools/static_check.py` | **PASS**, 0 findings |
| Translation extraction | `tools/extract_pot.py` | 511 entries written |

**What was NOT executed:**

| Item | Reason |
|------|--------|
| The Odoo test suite | No Odoo installation and no PostgreSQL database in the build environment. |
| `flake8` | Not installed; no network access to install it. |
| `pylint` with `pylint-odoo` | Same. |
| Coverage measurement | Requires an executed test run. |
| Module installation and upgrade on a live database | No Odoo instance. |

**Therefore this report does not claim a coverage percentage, does not claim
the suite passes, and does not claim the module installs.** It states what the
suite is designed to verify and gives the command to run it. Anyone validating
this module must execute §7.6 and record the actual result. A claim of
"95 % coverage" would be an invention, and this document will not make one.

## 7.2 Test design

141 test methods across 14 modules, all tagged `post_install, -at_install`
because the module extends `purchase` and needs a complete registry.

| Module | Methods | Scope |
|--------|---------|-------|
| `test_install.py` | 7 | Models registered, descriptions present, sequences, scheduled actions callable, report actions, starter data loaded, group hierarchy |
| `test_category_and_criterion.py` | 9 | Configuration models, interval and weight constraints, threshold ordering, template duplication, display names |
| `test_qualification_workflow.py` | 16 | The full dossier lifecycle: sequence, inherited criticality, blocking reasons, submission guard, happy path, audit-required path, critical-finding block, suspend, reinstate, disqualify, requalify, field locking, deletion guard, copy, next dates, risk level, expiry status |
| `test_assessment.py` | 16 | Frozen rules, template loading, start guard, weighted score, conditional band, mandatory-fail override, scale bound, comment requirement, conclusion requirement, signature creation, review segregation, self-review when disabled, finality, deletion guard, criterion uniqueness, exposure on the dossier |
| `test_audit.py` | 12 | Sequence, finding counters, stage order, report guards, response lead time, outcome consistency, closure guard, the six-step finding workflow, corrective-action requirement, signature entries, deletion guard, date chronology |
| `test_material_scope.py` | 6 | Qualification date stamping, date requirement, validity chronology, product uniqueness, suspension guard, expiry cron |
| `test_performance.py` | 13 | Frozen weights, indicator derivation, weighted score and rating, action flag, percentage bounds, counter consistency, period validity, overlap rejection, deletion guard, exposure on the dossier, guarded automatic counters |
| `test_review.py` | 12 | Sequence, evidence collection, all five decisions and their effect on the dossier, conditions requirement, justification requirement, finality, signature entry |
| `test_signature.py` | 9 | Field population, immutability of write and unlink, chain increment and linkage, verification pass, **detection of direct SQL tampering**, JSON payload, dossier back-reference, notification action |
| `test_constraints.py` | 12 | Live-dossier uniqueness, reuse after disqualification, approval completeness, conditional conditions, date chronology, segregation of duties both ways, wizard login check, wizard date check, company threshold and weight constraints |
| `test_security.py` | 11 | Viewer read-only, assessor limits, manager rights, signature log write-proof for every group, assessment ownership rule, manager override, multi-company rule presence |
| `test_cron.py` | 6 | Expiry transition, untouched valid approvals, reminder activity, non-duplication, due dates, idempotent scope expiry |
| `test_purchase_control.py` | 8 | All three control levels, approved supplier passes, expired approval blocks, scope check, warning field, partner flag and search |
| `test_reports.py` | 4 | All three QWeb templates render to HTML with expected content, file names |

## 7.3 Requirement traceability

| Business requirement | Verified by |
|----------------------|-------------|
| BR-01 one live dossier per supplier per company | `test_constraints.test_single_active_dossier_per_supplier`, `test_second_dossier_allowed_after_disqualification` |
| BR-02 explicit qualified scope required | `test_qualification_workflow.test_blocking_reasons_listed_in_draft`, `test_material_scope.*` |
| BR-03 category-driven prerequisites | `test_qualification_workflow.test_audit_required_blocks_approval` |
| BR-04 weighted reproducible result | `test_assessment.test_weighted_score_and_pass_result`, `test_conditional_result_between_thresholds` |
| BR-05 frozen scoring rules | `test_assessment.test_rules_frozen_from_template` |
| BR-06 mandatory criterion forces Fail | `test_assessment.test_failed_mandatory_criterion_forces_fail` |
| BR-07 critical finding blocks approval | `test_qualification_workflow.test_open_critical_finding_blocks_approval` |
| BR-08 segregation of duties | `test_constraints.test_segregation_of_duties_blocks_assessor_approval`, `test_segregation_of_duties_can_be_disabled` |
| BR-09 append-only signature log | `test_signature.*` (9 methods) |
| BR-10 validity from interval, overridable | `test_qualification_workflow.test_happy_path_to_approval`, `test_review.test_maintain_uses_interval_when_no_date_given` |
| BR-11 daily expiry and warning | `test_cron.*` (6 methods) |
| BR-12 three-level purchase control | `test_purchase_control.*` (8 methods) |
| BR-13 audit closure and corrective actions | `test_audit.test_cannot_close_with_open_finding`, `test_major_finding_requires_corrective_action` |
| BR-14 frozen performance weights | `test_performance.test_weights_frozen_from_company` |
| BR-15 review decision applied to dossier | `test_review.*` (12 methods) |
| BR-16 three PDF reports | `test_reports.*` (4 methods) |

Every business requirement of Phase 1 has at least one corresponding test.

## 7.4 Test levels covered

| Level | Where |
|-------|-------|
| Unit | Compute and constraint methods exercised directly: `_compute_scores`, `_compute_overall_score`, `_compute_risk_level`, `_compute_hash`, every `@api.constrains`. |
| Integration | Cross-model effects: an assessment result changing the dossier's blocking reasons; a review decision writing onto the dossier; a finding closure unblocking an audit. |
| Functional | Complete flows end to end, including the two wizards. |
| Security | `test_security.py`, using four users covering the three groups. |
| Installation | `test_install.py`, verifying every shipped data record and every scheduled action. |
| Constraint | `test_constraints.py`, plus constraint tests inside each model's module. |
| Workflow | Every state machine, including refusal of invalid transitions. |
| Upgrade | **Not covered by an automated test.** Version 1.0.0 has no predecessor. See §7.7. |
| Performance | **Not covered by an automated test.** See §7.7. |

## 7.5 Coverage expectation

The suite is written to exercise every public method, every state transition,
every constraint and every scheduled action. Areas deliberately left to manual
verification, and therefore expected to lower a measured figure:

* PDF binary rendering (wkhtmltopdf). The tests render the QWeb templates to
  HTML, which exercises every template expression; the PDF conversion step is a
  platform concern.
* E-mail delivery. Templates are exercised through `send_mail`; SMTP is out of
  scope.
* View rendering in a browser. Views are validated as XML and by the field
  references Odoo resolves at install; visual layout is manual.
* Two branches guarded by environment: the `purchase_stock` field check, where
  `test_performance.test_automatic_counters_require_purchase_stock` covers
  whichever branch the target database presents.

**Do not record a coverage figure in a validation package without measuring
it.** The command is in §7.6.

## 7.6 How to execute the suite

```bash
odoo-bin -d <test_database> \
    -i ls_supplier_qualification \
    --test-enable \
    --test-tags /ls_supplier_qualification \
    --stop-after-init \
    --log-level=test
```

With coverage:

```bash
coverage run --source=/path/to/addons/ls_supplier_qualification \
    odoo-bin -d <test_database> -i ls_supplier_qualification \
    --test-enable --test-tags /ls_supplier_qualification --stop-after-init
coverage report -m
coverage html
```

Record, in the validation package: the Odoo version and build, the PostgreSQL
version, the date, the operator, the count of tests run, passed and failed, and
the coverage figure with the HTML report attached.

## 7.7 Tests not automated, and how to cover them

| Area | Why not automated | Manual procedure |
|------|-------------------|------------------|
| Upgrade | No previous version exists. | From version 1.1.0 onward, install the previous version, create records in every state, upgrade, verify no data loss and that `noupdate` data was preserved. |
| Performance under volume | Meaningful figures need production-like data. | Load 5 000 dossiers with a full evidence history; time the dossier list, the expiry cron and a chain verification; record the figures. |
| PDF rendering | Depends on wkhtmltopdf. | Print each of the three reports and check pagination, headers and the dossier report footer. |
| Browser rendering | Requires a browser. | Walk the user manual on a test database with each of the three groups. |
| Multi-company isolation | Needs a multi-company database. | Create two companies, one supplier with a dossier in each, and confirm a user of company A never sees company B's status on the contact form or in any list. |
| E-mail delivery | Requires an SMTP server. | Configure SMTP, approve a dossier, confirm the responsible receives the notification. |

## 7.8 Test data policy

No test creates data outside the transaction; every test module inherits
`TransactionCase`, so the database is rolled back. Fixtures use `.invalid`
e-mail addresses, so no message can leave a test database. Demo data is
separate from test data and is never relied upon by a test.

---

**Phase 7 gate: PASS for design and authoring, with execution formally
outstanding.**
141 tests written, covering every business requirement of Phase 1. The suite
has not been run, because the build environment had no Odoo instance. §7.6 must
be executed and its result recorded before this module is used in a regulated
environment. Phase 8 may start.
