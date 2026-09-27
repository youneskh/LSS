# Test Report

Module: `ls_change_control` version 19.0.1.0.0 | Date: 2026-07-24

## 1. Execution status

> **The automated test suite was written but was NOT executed.**
>
> The environment in which this module was built has no Odoo runtime, no
> PostgreSQL database and no network access, so Odoo could not be installed.
> Consequently **no test result in this document is an observed result.** The
> table in section 3 is an inventory of the tests that exist in the delivered
> source, not a record of passes.
>
> Executing the suite is the responsibility of the receiving organisation, and
> is a prerequisite to any qualification of the module.

## 2. What was actually executed

| Check | Tool | Result |
|-------|------|--------|
| Python syntax of every file | `ast.parse` | 0 error |
| Line length, whitespace, tabs, final newline | `static_check.py` | 0 error |
| Docstring on every module, class and public method | `static_check.py` | 0 error |
| Absence of removed Odoo constructs: `tree`, `attrs`, `states`, `oe_chatter`, `kanban-box`, `t-esc`, `_sql_constraints`, `read_group`, `odoo.osv`, `record._cr` | `static_check.py` | 0 occurrence |
| Absence of TODO, FIXME, XXX | `static_check.py` | 0 occurrence |
| XML well-formedness of the 20 XML files | `xmllint --noout` | 0 error |
| Every external identifier reference resolves | `static_check.py` | 0 error |
| Every manifest file exists, every XML file is declared | `static_check.py` | 0 error |
| Access rights header and values, coverage of every model | `static_check.py` | 0 error |
| `_description` on every model | `static_check.py` | 0 error |
| **Total** | **170 checks** | **0 error, 0 warning** |

Tools that could **not** be executed, because they are not installable without
network access: `flake8`, `pylint`, `pylint-odoo`, the Odoo test runner.

## 3. Test inventory

121 test methods in 11 files, all tagged `post_install`, `-at_install`.

| File | Tests | Covers |
|------|-------|--------|
| `test_install.py` | 11 | Module installed, 9 models registered, 4 groups and their hierarchy, sequence, 3 crons, 3 mail templates, seed data, menus, company defaults |
| `test_configuration.py` | 8 | Unique codes, non negative delays, unique role per category, internal approver, verification delay resolution, refusal of an impossible configuration |
| `test_request_workflow.py` | 27 | Sequence allocation, display name, subscription, every transition and its guards, idempotent generation, full lifecycle to Closed, rejection, cancellation, wizard, duplication |
| `test_constraints.py` | 13 | Temporary end date, dates before the request, internal users, archiving, workflow field protection, frozen content fields, manager only writes, deletion protection, computed verification date |
| `test_assessment.py` | 9 | One assessment per area, mandatory rationale, mandatory actions on impact, authorised completers, completion stamps, immutability, state protection, state gating |
| `test_approval.py` | 12 | One role per request, request date stamp, authorised decider, signature metadata, approval on the last mandatory decision, immutability, double decision, mandatory comment on rejection, rejection cascade, field protection, state gating, non mandatory approvals |
| `test_implementation.py` | 10 | State gating, authorised executor, start, mandatory evidence, immutability, deletion protection, cancellation rules, computation of the actual implementation date including cancelled actions, field protection |
| `test_verification.py` | 9 | Mandatory conclusion, authorised completer, effective conclusion, mandatory follow-up, blocking on a not effective result, immutability, field protection, waiver by category and by company |
| `test_security.py` | 11 | Viewer read only, ownership rule, manager override, deletion, configuration access, multi-company isolation, approver cannot force a state, cumulative groups |
| `test_scheduled_actions.py` | 7 | Approval reminder after the delay, respect of the delay, disabling, overdue implementation activity, no duplicate activity, due verification activity, skip when already verified |
| `test_reports.py` | 4 | Report action declared, templates installed, rendering of a complete record, rendering of an empty draft |

## 4. Requirements traceability

| Business requirement | Covering tests |
|----------------------|----------------|
| BR-1 description of the change | `test_request_workflow.test_sequence_is_allocated_on_create` |
| BR-2 content frozen at submission | `test_constraints.test_content_fields_are_frozen_after_submission` |
| BR-3 category drives the workflow | `test_request_workflow.test_start_assessment_generates_assessments_and_approvals` |
| BR-4 one assessment per area | `test_assessment.test_one_assessment_per_area` |
| BR-5 impact requires actions | `test_assessment.test_declared_impact_requires_actions` |
| BR-6 approval requires every guard cleared | `test_request_workflow.test_request_is_not_approved_while_an_assessment_is_pending`, `test_approval.test_request_stays_pending_until_the_last_approval` |
| BR-7 only the assigned approver decides | `test_approval.test_only_the_assigned_approver_may_decide` |
| BR-8 decisions immutable | `test_approval.test_a_decided_approval_is_immutable` |
| BR-9 evidence mandatory | `test_implementation.test_closing_requires_an_evidence_reference` |
| BR-10 implementation date computed | `test_implementation.test_actual_implementation_date_needs_every_action_closed` |
| BR-11 acceptance criteria before completion | Enforced by the required field; exercised by `test_verification` fixtures |
| BR-12 not effective blocks closure | `test_verification.test_not_effective_blocks_the_verified_state` |
| BR-13 submitted requests retained | `test_constraints.test_submitted_requests_cannot_be_deleted` |
| BR-14 record printable | `test_reports.test_report_renders_a_complete_record` |
| BR-15 automatic reminders | `test_scheduled_actions`, 7 tests |

Risk R-2, forging a state through the API, is covered by
`test_constraints.test_system_fields_cannot_be_written_directly` and
`test_security.test_approver_cannot_change_the_request_state_directly`.

## 5. Coverage

The master specification sets a target of 95 percent.

**Coverage was not measured.** Measuring it requires executing the suite under
`coverage.py` inside an Odoo runtime, which was not possible. Any figure stated
here would be fabricated.

What can be said from a reading of the source: every public method of every
model is reached by at least one test, every transition of the state machine
has at least one passing case and one refused case, and every immutability rule
has a dedicated test. The measurement remains to be performed with:

```bash
coverage run --source=ls_change_control $(which odoo-bin) \
    -d <test-db> -i ls_change_control --test-enable \
    --test-tags /ls_change_control --stop-after-init
coverage report -m
```

## 6. Known version sensitive assertions

Two assertions depend on an API contract that could not be verified against the
official Odoo 19.0 documentation. If the suite fails, check these first.

| Test | Assumption |
|------|-----------|
| `test_request_workflow.test_copy_resets_the_lifecycle` | `copy_data` returns a list of dictionaries, the behaviour introduced in Odoo 17 |
| `test_reports.test_report_renders_a_complete_record` | `_render_qweb_html(report_ref, docids)` takes the report reference as its first argument |

Both are confined to the tests. Neither contract is relied upon by the
production code, except `copy_data`, which is overridden in the request model
and would need adjusting if the contract differed.

## 7. Test environment to be used by the receiving organisation

| Item | Value |
|------|-------|
| Odoo | 19.0 Community Edition |
| Database | Dedicated test database, never production |
| Demo data | Not required; the suite builds its own fixtures |
| Command | `odoo-bin -d <test-db> -i ls_change_control --test-enable --test-tags /ls_change_control --stop-after-init --log-level=test` |

## 8. Conclusion

Static analysis: **PASS**, 170 checks, 0 error.

Automated test suite: **NOT EXECUTED**. The suite is delivered complete and
ready to run. Until it has been executed on an Odoo 19.0 instance, the module
must be considered unverified for installation and for run time behaviour.
