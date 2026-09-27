# Phase 7 — Test Report

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Execution status

**The test suite has been written but has not been executed.** The
environment in which this module was produced has no Odoo installation and no
network access, therefore neither Odoo nor a PostgreSQL server could be
installed. Every statement below describes the tests as written, not as
passed.

What was verified in this environment:

| Verification | Tool | Result |
|--------------|------|--------|
| Python syntax of the nine test modules | `ast.parse` | Pass |
| Absence of unused imports | AST analysis | Pass |
| Presence of a docstring on every test method | AST analysis | Pass |
| Line length, whitespace, final newline | Text analysis | Pass |

What could **not** be verified and must be verified in the target
environment before this report can be signed:

| Item | Why |
|------|-----|
| That the tests pass | No Odoo runtime available |
| The measured coverage | Requires `coverage` and a running instance |
| The exception type raised by a `models.Constraint` violation | The assertions accept both `psycopg2.IntegrityError` and `ValidationError` for this reason |
| The name of the users-to-groups field | Resolved at run time by `common._users_group_field()` |
| The signature of `_render_qweb_html` in Odoo 19 | Used as `(report_ref, res_ids)` |

## 2. Test inventory

| Module | Test methods |
|--------|--------------|
| `tests/test_constraints.py` | 14 |
| `tests/test_cron.py` | 10 |
| `tests/test_instrument.py` | 16 |
| `tests/test_plan.py` | 15 |
| `tests/test_record_workflow.py` | 25 |
| `tests/test_report.py` | 4 |
| `tests/test_security.py` | 11 |
| `tests/test_wizards.py` | 6 |

**Total: 101 test methods.**

All classes are tagged `post_install` and `-at_install`, because they require
the complete registry, the access rights and the report engine.

## 3. Coverage by test level

| Level | Where | Content |
|-------|-------|---------|
| Unit | `test_plan`, `test_instrument` | Interval arithmetic, acceptance limits, deviations, display names, status classification |
| Integration | `test_record_workflow`, `test_plan` | Propagation of an approval to the plan and to the instrument, loading of the test points from a plan |
| Functional | `test_record_workflow`, `test_wizards` | Complete calibration cycle, generation and rejection wizards |
| Security | `test_security` | Access rights of the three groups, group hierarchy, presence of the record rules |
| Constraint | `test_constraints` | Six database constraints, four Python constraints, certificate life cycle |
| Workflow | `test_instrument`, `test_plan`, `test_record_workflow` | The four state machines, including their invalid transitions |
| Installation | `test_cron` | Presence of the sequences, of the scheduled actions and of their configuration |
| Report | `test_report` | Rendering of both reports and presence of their data |
| Access-right | `test_security` | Refusal of creation, of writing and of deletion per group |

## 4. Traceability from the business rules to the tests

| Rule | Test |
|------|------|
| BRU-01 unique instrument reference | `test_instrument_code_is_unique` |
| BRU-02 measuring range | `test_instrument_range_consistency` |
| BRU-03 non-negative values | `test_instrument_alert_lead_days_positive`, `test_plan_point_tolerance_is_positive` |
| BRU-04 positive interval | `test_plan_interval_is_positive` |
| BRU-05 plan belongs to the instrument | `test_record_plan_belongs_to_instrument` |
| BRU-06 no self standard | `test_record_standard_is_not_the_instrument` |
| BRU-07 certificate validity dates | `test_certificate_validity_dates` |
| BRU-08 certificate record consistency | `test_certificate_record_belongs_to_instrument` |
| BRU-09 plan needs a test point | `test_activation_requires_points` |
| BRU-10 completeness before submission | `test_submit_requires_calibration_date`, `test_submit_requires_performer`, `test_submit_requires_lines`, `test_submit_requires_standard`, `test_submit_accepts_external_standard` |
| BRU-11 out-of-tolerance assessment | `test_submit_requires_oot_assessment` |
| BRU-12 overdue standard refused | `test_submit_refuses_overdue_standard` |
| BRU-13 segregation of duties | `test_approval_segregation_of_duties` |
| BRU-14 approval restricted to managers | `test_technician_cannot_approve`, `test_manager_can_approve` |
| BRU-15 approved record locked | `test_approved_record_is_locked` |
| BRU-16 deletion restricted to draft | `test_unlink_only_in_draft` |
| BRU-17 lines locked with the record | `test_approved_record_is_locked`, `test_line_cannot_be_added_to_locked_record` |
| BRU-18 issued certificate locked | `test_certificate_workflow` |
| BRU-19 external certificate needs a document | `test_external_certificate_requires_document` |
| BRU-20 retirement closes the plans | `test_retire_makes_plans_obsolete` |

Every business rule of the functional specification is covered by at least
one test.

## 5. Untested areas

Declared explicitly rather than left implicit.

| Area | Reason | Compensating control |
|------|--------|----------------------|
| Rendering of the views by the web client | Requires a browser-based tour | The views use only standard elements; the XML is validated |
| PDF generation | Requires `wkhtmltopdf` | The HTML rendering of both reports is tested |
| Behaviour under concurrent access | Requires a multi-worker instance | The workflow transitions are guarded by state checks that re-read the state |
| Performance on a large register | Requires a volume database | Documented in the architecture review, finding PERF-01 |
| Migration from a previous version | The module has no previous version | Not applicable |

## 6. Coverage target

The framework sets a target of 95 %. **The coverage has not been measured and
is therefore not claimed.** To measure it:

```
coverage run --source=<addons_path>/ls_calibration $(which odoo-bin) \
    -d <test_db> -i ls_calibration --test-enable \
    --test-tags ls_calibration --stop-after-init
coverage report -m
```

Expected uncovered areas: the exception branches of `_search_calibration_status`
for the unsupported operators, which is covered, and the fallback branch of
`_cron_notify_due_calibrations` used when the standard activity type is
absent from the database, which is not covered.

## Gate

**Phase 7: CONDITIONAL PASS.** 101 test methods covering the nine required
test levels and every business rule have been written and are syntactically
valid. The gate cannot be closed as a full pass because the suite has not
been executed. Required action before closure: run the suite on an Odoo 19
Community instance, measure the coverage, and record the result in this
document.
