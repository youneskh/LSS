# ls_capa — Test Report

**Module:** `ls_capa` 19.0.1.0.0
**Date:** July 2026

---

## 1. Execution status

> **The test suite has NOT been executed.**
>
> Authoring took place in an environment with no Odoo installation, no
> PostgreSQL instance and no network access. Odoo tests cannot run
> outside a live Odoo registry with a database.
>
> No pass rate and no coverage percentage are reported here, because any
> figure would be fabricated. This document is therefore a **test
> inventory and design record**, not a results report. It becomes a
> results report only after the CI workflow in
> `.github/workflows/ci.yml` has run.

## 2. How to produce the results

```bash
coverage run --source=ls_capa $(which odoo-bin) \
    --addons-path=<odoo>/addons,<custom> \
    -d ci_ls_capa -i ls_capa --test-enable --stop-after-init
coverage report -m
coverage report --fail-under=95
```

The specification sets a 95% coverage target. The CI job fails the build
below that threshold rather than reporting an unverified number.

## 3. Test inventory

| Module | Class | Tests | Focus |
|---|---|---|---|
| `test_capa_action.py` | `TestCapaAction` | 21 | Action lifecycle, lateness and project task integration. |
| `test_capa_constraints.py` | `TestCapaConstraints` | 8 | Database and application level integrity rules. |
| `test_capa_effectiveness.py` | `TestCapaEffectiveness` | 14 | Verification lifecycle, conclusions and follow-up escalation. |
| `test_capa_issue.py` | `TestCapaIssue` | 24 | Creation, sequencing, computed fields and scheduled actions. |
| `test_capa_root_cause.py` | `TestCapaRootCause` | 15 | Analysis methods, computed RPN and confirmation lifecycle. |
| `test_capa_security.py` | `TestCapaSecurity` | 10 | Verify that each group holds the intended permissions. |
| `test_capa_workflow.py` | `TestCapaWorkflow` | 20 | Every transition of the eight-state CAPA lifecycle. |
| **Total** | | **112** | |

## 4. Test case register

Each test and the behaviour it asserts.

### `test_capa_action.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_sequence_allocated` | An action receives a reference from the sequence. |
| 2 | `test_start_moves_to_in_progress` | Starting a draft action moves it to In Progress. |
| 3 | `test_start_blocked_when_not_draft` | Only draft actions can be started. |
| 4 | `test_done_requires_evidence` | Completion requires documented completion evidence. |
| 5 | `test_done_stamps_completion_date` | Completion records the actual completion date. |
| 6 | `test_done_blocked_when_cancelled` | A cancelled action cannot be completed. |
| 7 | `test_cancel_requires_reason` | Cancelling without a reason is rejected. |
| 8 | `test_cancel_blocked_when_done` | A completed action cannot be cancelled. |
| 9 | `test_reset_to_draft_clears_reason` | Resetting a cancelled action clears the cancellation reason. |
| 10 | `test_reset_blocked_when_not_cancelled` | Only cancelled actions can be reset to draft. |
| 11 | `test_is_late_flag` | An open action past its planned date is late. |
| 12 | `test_is_not_late_when_done` | A completed action is never late. |
| 13 | `test_search_is_late` | The late flag is searchable. |
| 14 | `test_search_is_late_negative` | Searching for non-late actions excludes late ones. |
| 15 | `test_search_is_late_rejects_operator` | The late search raises on an unsupported operator. |
| 16 | `test_root_cause_must_belong_to_same_issue` | An action cannot reference another CAPA's root cause. |
| 17 | `test_root_cause_same_issue_accepted` | An action can reference a root cause of its own CAPA. |
| 18 | `test_create_task` | A project task can be generated from an action. |
| 19 | `test_create_task_twice_blocked` | An action cannot be linked to two tasks. |
| 20 | `test_create_task_uses_configured_project` | The configured default project is applied when set. |
| 21 | `test_cascade_delete_with_issue` | Deleting a CAPA removes its actions. |

### `test_capa_constraints.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_due_date_before_identification_rejected` | The due date cannot precede the identification date. |
| 2 | `test_due_date_equal_to_identification_accepted` | A same-day due date is accepted. |
| 3 | `test_capa_reference_unique_per_company` | Two CAPA records in one company cannot share a reference. |
| 4 | `test_category_code_unique_per_company` | Category codes are unique within a company. |
| 5 | `test_category_lead_time_must_be_positive` | A category lead time of zero is rejected by the database. |
| 6 | `test_category_code_cannot_be_blank` | A whitespace-only category code is rejected. |
| 7 | `test_action_reference_unique` | Action references are unique. |
| 8 | `test_cancelled_action_requires_reason_on_write` | Writing the cancelled state without a reason is rejected. |

### `test_capa_effectiveness.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_sequence_allocated` | An effectiveness check receives a reference from the sequence. |
| 2 | `test_default_result_pending` | A new check starts with a Pending result. |
| 3 | `test_plan_moves_to_planned` | Planning a draft check moves it to Planned. |
| 4 | `test_plan_blocked_when_not_draft` | Only draft checks can be planned. |
| 5 | `test_conclude_requires_conclusion` | A conclusion is mandatory before completing a check. |
| 6 | `test_mark_effective` | Concluding Effective stamps the verification date. |
| 7 | `test_mark_not_effective` | Concluding Not Effective is recorded. |
| 8 | `test_conclude_twice_blocked` | A completed check cannot be concluded again. |
| 9 | `test_done_state_requires_decided_result` | A completed check cannot keep a Pending result. |
| 10 | `test_planned_before_identification_rejected` | A check cannot be planned before the CAPA was identified. |
| 11 | `test_followup_requires_not_effective` | A follow-up CAPA needs a Not Effective conclusion. |
| 12 | `test_followup_creates_new_capa` | A Not Effective conclusion can raise a follow-up CAPA. |
| 13 | `test_followup_twice_blocked` | Only one follow-up CAPA can be raised per check. |
| 14 | `test_cascade_delete_with_issue` | Deleting a CAPA removes its effectiveness checks. |

### `test_capa_issue.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_sequence_allocated_on_create` | A CAPA reference is taken from the sequence on creation. |
| 2 | `test_sequence_unique_across_records` | Two CAPA records never share the same reference. |
| 3 | `test_explicit_name_is_preserved` | An explicitly supplied reference is not overwritten. |
| 4 | `test_copy_reallocates_reference` | Duplicating a CAPA allocates a fresh reference. |
| 5 | `test_default_state_is_identified` | A new CAPA starts in the Identified state. |
| 6 | `test_due_date_computed_from_category` | The due date is derived from the category lead time. |
| 7 | `test_due_date_recomputed_when_category_changes` | Changing the category re-proposes the due date. |
| 8 | `test_due_date_manually_overridable` | A manually entered due date is retained. |
| 9 | `test_relation_counts` | Smart button counters reflect the linked records. |
| 10 | `test_progress_zero_without_actions` | Progress is zero when no action exists. |
| 11 | `test_progress_ignores_cancelled_actions` | Cancelled actions are excluded from the progress denominator. |
| 12 | `test_progress_partial` | Progress reports the share of completed actions. |
| 13 | `test_is_overdue_flag` | An open CAPA past its due date is flagged as overdue. |
| 14 | `test_is_not_overdue_when_due_in_future` | A CAPA with a future due date is not overdue. |
| 15 | `test_is_overdue_false_without_due_date` | A CAPA without a due date is never overdue. |
| 16 | `test_search_overdue_true` | Searching on the overdue flag returns overdue records. |
| 17 | `test_search_overdue_false` | Searching for non-overdue records excludes overdue ones. |
| 18 | `test_search_overdue_rejects_unsupported_operator` | The overdue search raises on an unsupported operator. |
| 19 | `test_unlink_allowed_in_identified_state` | A CAPA still in Identified can be deleted. |
| 20 | `test_unlink_blocked_after_progress` | A CAPA that progressed cannot be deleted. |
| 21 | `test_cron_posts_message_on_overdue` | The scheduled action posts a reminder on overdue records. |
| 22 | `test_cron_ignores_closed_records` | The scheduled action skips closed CAPA records. |
| 23 | `test_navigation_actions_return_domains` | The smart button actions target the correct models. |
| 24 | `test_category_issue_count_and_action` | The category counts its CAPA records and opens them. |

### `test_capa_root_cause.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_sequence_allocated` | A root cause analysis receives a reference from the sequence. |
| 2 | `test_default_state_is_draft` | A new analysis starts in Draft. |
| 3 | `test_confirm_sets_state` | Confirming moves the analysis to Confirmed. |
| 4 | `test_confirm_twice_is_blocked` | A confirmed analysis cannot be confirmed again. |
| 5 | `test_reset_to_draft` | A confirmed analysis can return to Draft before execution. |
| 6 | `test_reset_blocked_after_execution_started` | Reset is refused once the CAPA started execution. |
| 7 | `test_five_whys_requires_first_why` | A Five Whys analysis must document the first Why. |
| 8 | `test_ishikawa_requires_category` | An Ishikawa analysis must name a diagram category. |
| 9 | `test_ishikawa_accepts_category` | An Ishikawa analysis with a category is accepted. |
| 10 | `test_fmea_rpn_computed` | The RPN is the product of severity, occurrence and detection. |
| 11 | `test_fmea_rpn_zero_for_other_methods` | Non-FMEA analyses report a zero RPN. |
| 12 | `test_fmea_rating_out_of_range_rejected` | FMEA ratings outside the 1 to 10 scale are rejected. |
| 13 | `test_fmea_rating_zero_rejected` | A zero FMEA rating is rejected. |
| 14 | `test_company_propagated_from_issue` | The company is inherited from the parent CAPA. |
| 15 | `test_cascade_delete_with_issue` | Deleting a CAPA removes its root cause analyses. |

### `test_capa_security.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_viewer_cannot_create_capa` | A viewer has read-only access to CAPA records. |
| 2 | `test_viewer_can_read_capa` | A viewer can read existing CAPA records. |
| 3 | `test_investigator_can_create_capa` | An investigator can raise a CAPA. |
| 4 | `test_investigator_cannot_create_action` | Action planning is reserved to coordinators and above. |
| 5 | `test_coordinator_can_create_action` | A coordinator can plan actions. |
| 6 | `test_coordinator_cannot_delete_capa` | Deletion is reserved to CAPA managers. |
| 7 | `test_manager_can_delete_capa` | A manager can delete a CAPA still in Identified. |
| 8 | `test_viewer_cannot_manage_categories` | Configuration is reserved to CAPA managers. |
| 9 | `test_group_implication_chain` | Each group implies the permissions of the group below it. |
| 10 | `test_multi_company_rule_hides_other_company_records` | The record rule hides CAPA records of another company. |

### `test_capa_workflow.py`

| # | Test | Asserted behaviour |
|---|---|---|
| 1 | `test_full_happy_path` | A CAPA can travel the whole lifecycle to Closed. |
| 2 | `test_assess_requires_impact_assessment` | Assessment is blocked until an impact assessment is documented. |
| 3 | `test_assess_succeeds_with_impact_assessment` | Assessment succeeds once the impact assessment is present. |
| 4 | `test_assess_rejects_whitespace_only_assessment` | A whitespace-only impact assessment does not satisfy the gate. |
| 5 | `test_transition_from_wrong_state_is_blocked` | A transition raises when the source state is wrong. |
| 6 | `test_action_planning_requires_confirmed_root_cause` | Action planning is blocked without a confirmed root cause. |
| 7 | `test_action_planning_succeeds_after_confirmation` | Confirming the root cause unblocks action planning. |
| 8 | `test_start_progress_requires_an_action` | Execution cannot start with no planned action. |
| 9 | `test_complete_requires_all_actions_settled` | Completion is blocked while an action is still open. |
| 10 | `test_complete_accepts_cancelled_actions` | Cancelled actions do not block completion. |
| 11 | `test_verify_requires_effective_check` | Verification needs at least one Effective conclusion. |
| 12 | `test_verify_blocked_by_pending_check` | A check still open blocks verification. |
| 13 | `test_close_requires_summary` | Closure is blocked without a closure summary. |
| 14 | `test_close_summary_constraint` | A closed record cannot have its summary cleared. |
| 15 | `test_close_wizard_closes_the_capa` | The closure wizard writes the summary and closes the CAPA. |
| 16 | `test_close_wizard_rejects_blank_summary` | The wizard refuses a whitespace-only summary. |
| 17 | `test_close_wizard_defaults_from_issue` | The wizard pre-fills an existing summary from the CAPA. |
| 18 | `test_open_close_wizard_action` | The CAPA exposes an action opening the closure wizard. |
| 19 | `test_open_close_wizard_blocked_before_verified` | The closure wizard cannot be opened before verification. |
| 20 | `test_state_changes_are_logged` | Each transition posts a message in the chatter. |

## 5. Coverage design

Coverage is pursued by construction rather than by measurement in this
environment. The mapping below records which tests exercise which
requirement.

| Requirement | Covering tests |
|---|---|
| Sequence allocation on all four models | `test_sequence_allocated` in four modules |
| Full eight-state lifecycle | `test_full_happy_path` |
| Gate: impact assessment before Assessed | `test_assess_requires_impact_assessment`, `test_assess_rejects_whitespace_only_assessment` |
| Gate: confirmed root cause before Action Planning | `test_action_planning_requires_confirmed_root_cause` |
| Gate: at least one action before In Progress | `test_start_progress_requires_an_action` |
| Gate: all actions settled before Completed | `test_complete_requires_all_actions_settled`, `test_complete_accepts_cancelled_actions` |
| Gate: effective check before Verified | `test_verify_requires_effective_check`, `test_verify_blocked_by_pending_check` |
| Gate: summary before Closed | `test_close_requires_summary`, `test_close_summary_constraint` |
| Wrong-state transitions rejected | `test_transition_from_wrong_state_is_blocked` |
| Five Whys validation | `test_five_whys_requires_first_why` |
| Ishikawa validation | `test_ishikawa_requires_category`, `test_ishikawa_accepts_category` |
| FMEA RPN and 1–10 scale | `test_fmea_rpn_computed`, `test_fmea_rating_out_of_range_rejected`, `test_fmea_rating_zero_rejected`, `test_fmea_rpn_zero_for_other_methods` |
| Action evidence and cancellation rules | `test_done_requires_evidence`, `test_cancel_requires_reason` |
| project.task integration | `test_create_task`, `test_create_task_twice_blocked`, `test_create_task_uses_configured_project` |
| Follow-up CAPA escalation | `test_followup_creates_new_capa`, `test_followup_requires_not_effective`, `test_followup_twice_blocked` |
| Searchable computed flags | `test_search_overdue_true/false`, `test_search_is_late`, plus operator rejection tests |
| Scheduled action | `test_cron_posts_message_on_overdue`, `test_cron_ignores_closed_records` |
| Deletion restriction | `test_unlink_allowed_in_identified_state`, `test_unlink_blocked_after_progress` |
| Cascade deletion | `test_cascade_delete_with_issue` in three modules |
| SQL constraints | `test_capa_reference_unique_per_company`, `test_category_code_unique_per_company`, `test_category_lead_time_must_be_positive`, `test_action_reference_unique` |
| Access rights, all four groups | ten tests in `test_capa_security.py` |
| Multi-company isolation | `test_multi_company_rule_hides_other_company_records` |

## 6. Static analysis actually executed

The lint toolchain could not be installed (no network). Equivalent
checks were executed with the Python standard library and **did run**:

| Check | Method | Result |
|---|---|---|
| Python syntax, 20 files | `py_compile` | 0 failures |
| PEP 8 line length ≤ 79 | AST line scan | 0 violations (3 found and fixed) |
| Docstring coverage | AST walk | 0 missing |
| XML well-formedness, 15 files | `xml.dom.minidom` | 0 failures |
| Manifest data file existence | path check | 16/16 resolve |
| ACL model references | CSV vs AST | 20/20 resolve |
| ACL group references | CSV vs groups XML | 4/4 resolve |
| View field references exist on model | AST + comodel walk | 0 unknown |
| View button methods exist | AST + XML walk | 0 missing |
| Placeholder / TODO / FIXME scan | text scan | 0 hits |
| Menu icon target exists | path check | resolves |

`flake8`, `pylint-odoo` and `pre-commit` remain **outstanding** and run
in the CI workflow.

## 7. Defects found and fixed during authoring

| # | Defect | Detection | Resolution |
|---|---|---|---|
| D-01 | Invalid keyword argument on `ls.capa.root_cause.issue_id`; would raise `TypeError` at registry load | Review immediately after writing | Removed before Phase 6 completion |
| D-02 | Three lines exceeding 79 columns | AST line-length scan | Refactored |
| D-03 | README stated 88 tests; actual count 112 | Programmatic count | Corrected to 112 |
| D-04 | `ir.cron` record used removed fields `numbercall`/`doall`; raised `ValueError` on install against Odoo 19 | Live install attempt | Fields removed; recurrence via `interval_number`/`interval_type` only |

D-03 is recorded because an unverified figure in documentation is the
same class of error as an unverified figure in a test report.

## 8. Residual risks

| Risk | Impact | Mitigation |
|---|---|---|
| Suite never executed | Unknown runtime defects may exist | CI must pass before release |
| Coverage unmeasured | 95% target unproven | CI enforces `--fail-under=95` |
| `res.users` groups field name unconfirmed | Test fixture could fail on some builds | Runtime registry resolution; CI probes the Odoo source |
| Lint tools not run | Style or Odoo-specific findings possible | CI lint job |
