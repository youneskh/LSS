# 03 — Functional Specification

Phase 3 deliverable. Status: **PASS**.

## 1. Menu structure

Root menu **Quality Management** (`menu_ls_qms_root`), visible to the group
Viewer and above.

| Menu | Action | Model |
|---|---|---|
| Quality Policy | `ls_qms_policy_action` | `ls.qms.policy` |
| Quality Objectives | `ls_qms_objective_action` | `ls.qms.objective` |
| Procedures | `ls_qms_sop_action` | `ls.qms.sop` |
| Work Instructions | `ls_qms_work_instruction_action` | `ls.qms.work_instruction` |
| Quality Planning | `ls_qms_quality_plan_action` | `ls.qms.quality_plan` |
| Quality Records | `ls_qms_quality_record_action` | `ls.qms.quality_record` |
| Reporting → Objective Analysis | `ls_qms_objective_action_analysis` | `ls.qms.objective` |
| Reporting → Measurements | `ls_qms_objective_measurement_action` | `ls.qms.objective.measurement` |
| Reporting → Procedures Due for Review | `ls_qms_sop_action_review_due` | `ls.qms.sop` |
| Reporting → Records Past Retention | `ls_qms_quality_record_action_retention` | `ls.qms.quality_record` |
| Configuration → System Parameters | `ls_qms_config_parameter_action` | `ir.config_parameter` |

The Configuration menu is restricted to `base.group_system`.

## 2. State machines

### 2.1 Controlled documents

States: `draft`, `under_review`, `approved`, `published`, `under_revision`,
`obsolete`.

| From | To | Trigger | Required group |
|---|---|---|---|
| draft | under_review | Submit for Review | User |
| under_review | approved | Approve | Approver |
| under_review | draft | Reject | Approver |
| approved | published | Publish | Approver |
| approved | draft | Reset to Draft | Manager |
| under_review | draft | Reset to Draft | Manager |
| published | under_revision | New Revision | User |
| published | obsolete | Set Obsolete | Manager |
| under_revision | obsolete | Publication of the next revision | automatic |

### 2.2 Quality objectives

States: `draft`, `in_progress`, `achieved`, `not_achieved`, `cancelled`.
Transitions: draft → in_progress → achieved or not_achieved; any state except
cancelled → cancelled; achieved, not_achieved or cancelled → draft.

### 2.3 Quality records

States: `draft`, `confirmed`, `archived`, `disposed`. Transitions:
draft → confirmed → archived → disposed. Disposal requires the group Manager,
the state `archived` and a retention date already elapsed.

## 3. Business rules

| Identifier | Rule |
|---|---|
| BR-01 | The reference is allocated from a sequence at creation and is never regenerated on revision |
| BR-02 | The version starts at 1 and is incremented by one at each revision |
| BR-03 | The pair reference and version is unique per company |
| BR-04 | Only one revision of a given reference may be in the state published |
| BR-05 | The author cannot approve, unless the segregation parameter is false |
| BR-06 | The effective date cannot precede the approval date |
| BR-07 | The next review date is the effective date plus the review period in months |
| BR-08 | A review period of zero disables the periodic review |
| BR-09 | A negative review period is refused |
| BR-10 | A policy requires a statement before submission |
| BR-11 | A procedure requires a purpose, a scope and a body before submission |
| BR-12 | A work instruction requires a body before submission |
| BR-13 | A quality plan requires at least one control line before submission |
| BR-14 | A work instruction cannot be published while its procedure is not published |
| BR-15 | A work instruction belongs to a procedure of the same company |
| BR-16 | A reason for change is mandatory to open a revision |
| BR-17 | A reason is mandatory to reject |
| BR-18 | The target of an objective must be consistent with its direction |
| BR-19 | The tolerance of an objective cannot be negative |
| BR-20 | The target date cannot precede the start date |
| BR-21 | A measurement cannot be dated before the start of its objective |
| BR-22 | The current value of an objective is the value of its most recent measurement, or the baseline when there is none |
| BR-23 | A confirmed record is writable only by a manager |
| BR-24 | A record is deletable only in the state draft |
| BR-25 | A retention period of zero means an unlimited retention |

## 4. Achievement formulas

Implemented by `compute_achievement_rate`, floored at zero, not capped above
one hundred.

| Direction | Formula |
|---|---|
| increase | (current − baseline) ÷ (target − baseline) × 100 |
| decrease | (baseline − current) ÷ (baseline − target) × 100 |
| maintain, tolerance greater than zero | 100 − ( abs(current − target) ÷ tolerance ) × 100 |
| maintain, tolerance equal to zero | 100 when current equals target, otherwise 0 |

When the denominator is zero the function returns zero, because no progress
can be expressed on a null span.

Performance status compares the achievement with the elapsed share of the
period: `target_reached` at one hundred percent or more, `on_track` at or
above the elapsed share, `at_risk` at or above eighty percent of the elapsed
share, `off_track` below, `no_data` when no measurement exists.

## 5. Scheduled actions

| Action | Interval | Effect |
|---|---|---|
| Document Review Reminder | daily | One activity per published document reaching its review date within the lead window, on the author, without duplication |
| Objective Monitoring | weekly | One activity per objective in progress approaching its target date below one hundred percent, without duplication |
| Record Retention Review | monthly | One activity per confirmed or archived record past its retention date, without duplication |

## 6. Reports

Three PDF documents, each printing a control block with the reference, the
version, the status, the effective date, the author, the approver and the
approval date, followed by a notice stating that a printed copy is not
controlled.

| Report action | Applies to | Filename pattern |
|---|---|---|
| `action_report_ls_qms_policy` | `ls.qms.policy` | reference-version |
| `action_report_ls_qms_sop` | `ls.qms.sop` | reference-version |
| `action_report_ls_qms_quality_plan` | `ls.qms.quality_plan` | reference-version |

## 7. Views, filters and grouping

Every document model has a list view, a form view with a status bar, a
chatter and an attachment counter, and a search view. Objectives additionally
have a graph view and a pivot view. Measurements have a graph view.

| Model | Filters | Group by |
|---|---|---|
| Documents | My documents, Draft, Under review, Published, Obsolete, Review overdue, Review due soon | State, Department, Author, Review status |
| Objectives | My objectives, In progress, Achieved, Off track, At risk | State, Department, Responsible, Performance |
| Records | My records, Draft, Confirmed, Archived, Retention expired | Type, State, Department, Author |

## 8. Wizards

| Wizard | Purpose | Mandatory input |
|---|---|---|
| `ls.qms.new.revision.wizard` | Open the next revision of a document | Reason for change |
| `ls.qms.reject.wizard` | Return a document to its author | Reason |
