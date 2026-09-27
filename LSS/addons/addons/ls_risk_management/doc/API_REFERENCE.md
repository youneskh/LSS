# API Reference

## Life Sciences Suite - Risk Management (`ls_risk_management`)

This document is generated from the module sources by
`tools_generate_docs.py` using the Python `ast` module. It reflects
what the code actually declares rather than a hand-maintained list.

Models declared: **17**.

---

## `ls.risk.category`

- **Class**: `LsRiskCategory` in `models/ls_risk_category.py`
- **Kind**: Persistent
- **Description**: Risk Category
- **Order**: `complete_name`

Hierarchical category used to classify risk register entries.

### Fields (10)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Name |  | yes |  |
| `code` | Char | Code |  | yes |  |
| `complete_name` | Char | Complete Name |  |  | compute `_compute_complete_name`, stored |
| `parent_id` | Many2one | Parent Category | `ls.risk.category` |  |  |
| `parent_path` | Char |  |  |  |  |
| `child_ids` | One2many | Child Categories | `ls.risk.category` |  |  |
| `company_id` | Many2one | Company | `res.company` | yes |  |
| `active` | Boolean | Active |  |  |  |
| `description` | Text | Description |  |  |  |
| `risk_count` | Integer | Risk Count |  |  | compute `_compute_risk_count` |

### Database constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_code_company_uniq` | `UNIQUE(code, company_id)` | The risk category code must be unique per company. |

### Internal methods (5)

- `_compute_complete_name()` - Build the slash-separated path of the category.
- `_compute_risk_count()` - Count the risks directly attached to each category.
- `_check_category_recursion()` - Forbid cycles in the category hierarchy.
- `_check_parent_company()` - Keep a category and its parent within the same company.
- `_compute_display_name()` - Display the full hierarchical path.

---

## `ls.risk.matrix`

- **Class**: `LsRiskMatrix` in `models/ls_risk_matrix.py`
- **Kind**: Persistent
- **Description**: Risk Matrix
- **Inherits**: `mail.thread`, `ls.risk.role.mixin`
- **Order**: `sequence, name`

A named, approvable set of risk acceptability criteria.

### Fields (21)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Name |  | yes |  |
| `code` | Char | Code |  | yes |  |
| `sequence` | Integer | Sequence |  |  |  |
| `active` | Boolean | Active |  |  |  |
| `company_id` | Many2one | Company | `res.company` | yes |  |
| `state` | Selection | Status |  | yes |  |
| `is_default` | Boolean | Default Matrix |  |  |  |
| `reference_document` | Char | Reference Document |  |  |  |
| `description` | Text | Description |  |  |  |
| `approved_by_id` | Many2one | Approved By | `res.users` |  |  |
| `approval_date` | Datetime | Approval Date |  |  |  |
| `obsolete_reason` | Text | Obsolescence Reason |  |  |  |
| `level_ids` | One2many | Levels | `ls.risk.matrix.level` |  |  |
| `severity_level_ids` | One2many | Severity Levels | `ls.risk.matrix.level` |  |  |
| `probability_level_ids` | One2many | Probability Levels | `ls.risk.matrix.level` |  |  |
| `cell_ids` | One2many | Cells | `ls.risk.matrix.cell` |  |  |
| `severity_level_count` | Integer | Severity Level Count |  |  | compute `_compute_level_counts` |
| `probability_level_count` | Integer | Probability Level Count |  |  | compute `_compute_level_counts` |
| `cell_count` | Integer | Cell Count |  |  | compute `_compute_level_counts` |
| `expected_cell_count` | Integer | Expected Cell Count |  |  | compute `_compute_level_counts` |
| `is_complete` | Boolean | Complete |  |  | compute `_compute_level_counts` |

### Database constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_code_company_uniq` | `UNIQUE(code, company_id)` | The matrix code must be unique per company. |

### Public methods (4)

- `get_cell(severity_value, probability_value)` - Return the cell for a (severity, probability) pair.
- `action_generate_cells()` - Create the missing cells of the grid, leaving existing cells intact.
- `action_approve()` - Approve the matrix so that it can be used on assessments.
- `action_set_obsolete()` - Mark the matrix obsolete, preventing its use on new assessments.

### Internal methods (4)

- `_compute_level_counts()` - Count levels and cells and derive matrix completeness.
- `_has_all_cells()` - Return whether every (severity, probability) pair has one cell.
- `_compute_display_name()` - Show the matrix code together with its name.
- `_check_single_default()` - Forbid more than one active default matrix per company.

---

## `ls.risk.matrix.level`

- **Class**: `LsRiskMatrixLevel` in `models/ls_risk_matrix.py`
- **Kind**: Persistent
- **Description**: Risk Matrix Level
- **Order**: `matrix_id, scale, value`

One ordinal level of a severity or probability scale.

### Fields (6)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `matrix_id` | Many2one | Matrix | `ls.risk.matrix` | yes |  |
| `scale` | Selection | Scale |  | yes |  |
| `value` | Integer | Value |  | yes |  |
| `name` | Char | Label |  | yes |  |
| `description` | Text | Definition |  |  |  |
| `company_id` | Many2one | Company | `res.company` |  | related `matrix_id.company_id` |

### Database constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_value_uniq` | `UNIQUE(matrix_id, scale, value)` | Each level value may appear only once per scale within a matrix. |
| `_value_positive` | `CHECK(value > 0)` | A risk matrix level value must be strictly positive. |

### Internal methods (1)

- `_compute_display_name()` - Show the ordinal value alongside the label.

---

## `ls.risk.matrix.cell`

- **Class**: `LsRiskMatrixCell` in `models/ls_risk_matrix.py`
- **Kind**: Persistent
- **Description**: Risk Matrix Cell
- **Order**: `matrix_id, severity_value desc, probability_value desc`

The risk band and acceptability decision for one matrix cell.

### Fields (6)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `matrix_id` | Many2one | Matrix | `ls.risk.matrix` | yes |  |
| `severity_value` | Integer | Severity Value |  | yes |  |
| `probability_value` | Integer | Probability Value |  | yes |  |
| `risk_level` | Selection | Risk Level |  | yes |  |
| `acceptability` | Selection | Acceptability |  | yes |  |
| `company_id` | Many2one | Company | `res.company` |  | related `matrix_id.company_id` |

### Database constraints (3)

| Name | Definition | Message |
|---|---|---|
| `_cell_uniq` | `UNIQUE(matrix_id, severity_value, probability_value)` | Only one cell may exist per severity and probability combination. |
| `_severity_positive` | `CHECK(severity_value > 0)` | The severity value of a matrix cell must be strictly positive. |
| `_probability_positive` | `CHECK(probability_value > 0)` | The probability value of a matrix cell must be strictly positive. |

### Internal methods (2)

- `_check_values_exist()` - Ensure a cell only references levels declared on its matrix.
- `_compute_display_name()` - Show the coordinates and resulting band of the cell.

---

## `ls.risk.register`

- **Class**: `LsRiskRegister` in `models/ls_risk_register.py`
- **Kind**: Persistent
- **Description**: Risk Register Entry
- **Inherits**: `mail.thread`, `mail.activity.mixin`, `ls.risk.role.mixin`
- **Order**: `identified_date desc, id desc`

An identified risk under active management.

### Fields (50)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Reference |  | yes |  |
| `title` | Char | Title |  | yes |  |
| `description` | Text | Description |  |  |  |
| `company_id` | Many2one | Company | `res.company` | yes |  |
| `category_id` | Many2one | Category | `ls.risk.category` |  |  |
| `risk_type` | Selection | Risk Type |  | yes |  |
| `owner_id` | Many2one | Risk Owner | `res.users` | yes |  |
| `identified_by_id` | Many2one | Identified By | `res.users` | yes |  |
| `identified_date` | Date | Identification Date |  | yes |  |
| `active` | Boolean | Active |  |  |  |
| `state` | Selection | Status |  | yes |  |
| `intended_use` | Text | Intended Use and Reasonably Foreseeable Misuse |  |  |  |
| `safety_characteristics` | Text | Characteristics Related to Safety |  |  |  |
| `hazard` | Text | Hazard |  |  |  |
| `hazardous_situation` | Text | Hazardous Situation |  |  |  |
| `sequence_of_events` | Text | Sequence of Events |  |  |  |
| `harm` | Text | Harm |  |  |  |
| `matrix_id` | Many2one | Risk Matrix | `ls.risk.matrix` | yes |  |
| `assessment_ids` | One2many | Assessments | `ls.risk.assessment` |  |  |
| `assessment_count` | Integer | Assessment Count |  |  | compute `_compute_assessment_data`, stored |
| `initial_assessment_id` | Many2one | Initial Assessment | `ls.risk.assessment` |  | compute `_compute_assessment_data`, stored |
| `current_assessment_id` | Many2one | Current Assessment | `ls.risk.assessment` |  | compute `_compute_assessment_data`, stored |
| `initial_risk_level` | Selection | Initial Risk Level |  |  | compute `_compute_assessment_data`, stored |
| `current_risk_level` | Selection | Current Risk Level |  |  | compute `_compute_assessment_data`, stored |
| `current_acceptability` | Selection | Current Acceptability |  |  | compute `_compute_assessment_data`, stored |
| `mitigation_ids` | One2many | Risk Control Measures | `ls.risk.mitigation` |  |  |
| `mitigation_count` | Integer | Control Measure Count |  |  | compute `_compute_mitigation_data`, stored |
| `mitigation_open_count` | Integer | Open Control Measures |  |  | compute `_compute_mitigation_data`, stored |
| `all_mitigations_verified` | Boolean | All Control Measures Verified |  |  | compute `_compute_mitigation_data`, stored |
| `benefit_risk_analysis` | Text | Benefit-Risk Analysis |  |  |  |
| `control_completeness_confirmed` | Boolean | Risk Control Completeness Confirmed |  |  |  |
| `control_completeness_by_id` | Many2one | Completeness Confirmed By | `res.users` |  |  |
| `control_completeness_date` | Datetime | Completeness Confirmation Date |  |  |  |
| `residual_risk_accepted` | Boolean | Residual Risk Accepted |  |  |  |
| `residual_risk_accepted_by_id` | Many2one | Residual Risk Accepted By | `res.users` |  |  |
| `residual_risk_acceptance_date` | Datetime | Residual Risk Acceptance Date |  |  |  |
| `residual_risk_justification` | Text | Residual Risk Acceptance Justification |  |  |  |
| `overall_residual_risk_assessment` | Text | Overall Residual Risk Assessment |  |  |  |
| `review_interval_months` | Integer | Review Interval (Months) |  | yes |  |
| `next_review_date` | Date | Next Review Date |  |  |  |
| `last_review_date` | Date | Last Review Date |  |  |  |
| `review_overdue` | Boolean | Review Overdue |  |  | compute `_compute_review_overdue` |
| `closure_reason` | Text | Closure Reason |  |  |  |
| `closed_by_id` | Many2one | Closed By | `res.users` |  |  |
| `closed_date` | Datetime | Closure Date |  |  |  |
| `cancel_reason` | Text | Cancellation Reason |  |  |  |
| `linked_model_id` | Many2one | Linked Model | `ir.model` |  |  |
| `linked_res_id` | Integer | Linked Record ID |  |  |  |
| `fmea_line_ids` | One2many | Originating FMEA Lines | `ls.risk.fmea.line` |  |  |
| `fmea_line_count` | Integer | FMEA Line Count |  |  | compute `_compute_fmea_line_count` |

### Database constraints (3)

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The risk reference must be unique per company. |
| `_review_interval_positive` | `CHECK(review_interval_months > 0)` | The review interval must be strictly positive. |
| `_linked_res_id_non_negative` | `CHECK(linked_res_id >= 0)` | The linked record identifier cannot be negative. |

### Public methods (15)

- `create(vals_list)` - Assign the register reference from the configured sequence.
- `unlink()` - Restrict deletion to draft and cancelled risks.
- `copy_data(default)` - Reset workflow evidence when a risk is duplicated.
- `action_start_assessment()` - Move a draft risk to the assessed state.
- `action_start_risk_control()` - Move an assessed risk into the risk control state.
- `action_confirm_control_completeness()` - Record the risk control completeness confirmation (clause 7.6).
- `action_accept_residual_risk()` - Open the residual risk acceptance wizard.
- `action_start_monitoring()` - Move a risk under risk control into the monitoring state.
- `action_open_close_wizard()` - Open the closure wizard for the selected risks.
- `action_cancel()` - Open the cancellation wizard for the selected risks.
- `action_reset_to_draft()` - Return a cancelled risk to the draft state.
- `action_open_assess_wizard()` - Open the assessment wizard for the selected risks.
- `action_view_assessments()` - Open the assessments of this risk.
- `action_view_mitigations()` - Open the risk control measures of this risk.
- `action_open_linked_record()` - Open the record referenced by the technical extension point.

### Internal methods (12)

- `_default_matrix_id()` - Return the active default approved matrix of the current company.
- `_compute_assessment_data()` - Derive assessment counts and the initial and current assessments.
- `_compute_mitigation_data()` - Derive risk control measure counts and verification completeness.
- `_compute_fmea_line_count()` - Count the FMEA lines that gave rise to each risk.
- `_compute_review_overdue()` - Flag open risks whose review date has passed.
- `_compute_display_name()` - Show the reference followed by the title.
- `_check_matrix_company()` - Keep the matrix and the risk within the same company.
- `_check_category_company()` - Keep the category and the risk within the same company.
- `_check_linked_record()` - Require both parts of the optional technical link, or neither.
- `_compute_next_review_date(from_date)` - Return the next review date derived from the review interval.
- `_requires_residual_decision()` - Return whether an explicit residual risk decision is required.
- `_cron_notify_review_due()` - Notify risk owners of open risks whose review date has passed.

---

## `ls.risk.assessment`

- **Class**: `LsRiskAssessment` in `models/ls_risk_assessment.py`
- **Kind**: Persistent
- **Description**: Risk Assessment
- **Inherits**: `mail.thread`, `ls.risk.role.mixin`
- **Order**: `assessment_date desc, id desc`

One dated, approvable estimation and evaluation of a risk.

### Fields (21)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Reference |  | yes |  |
| `risk_id` | Many2one | Risk | `ls.risk.register` | yes |  |
| `company_id` | Many2one | Company | `res.company` |  | related `risk_id.company_id` |
| `assessment_type` | Selection | Assessment Type |  | yes |  |
| `matrix_id` | Many2one | Risk Matrix | `ls.risk.matrix` | yes |  |
| `severity_level_id` | Many2one | Severity | `ls.risk.matrix.level` | yes |  |
| `probability_level_id` | Many2one | Probability | `ls.risk.matrix.level` | yes |  |
| `severity_value` | Integer | Severity Value |  |  | related `severity_level_id.value` |
| `probability_value` | Integer | Probability Value |  |  | related `probability_level_id.value` |
| `matrix_cell_id` | Many2one | Matrix Cell | `ls.risk.matrix.cell` |  | compute `_compute_evaluation`, stored |
| `risk_level` | Selection | Risk Level |  |  | compute `_compute_evaluation`, stored |
| `acceptability` | Selection | Acceptability |  |  | compute `_compute_evaluation`, stored |
| `ordinal_index` | Integer | Ordinal Index |  |  | compute `_compute_evaluation`, stored |
| `estimation_rationale` | Text | Estimation Rationale |  |  |  |
| `assessed_by_id` | Many2one | Assessed By | `res.users` | yes |  |
| `assessment_date` | Date | Assessment Date |  | yes |  |
| `approved_by_id` | Many2one | Approved By | `res.users` |  |  |
| `approval_date` | Datetime | Approval Date |  |  |  |
| `state` | Selection | Status |  | yes |  |
| `cancel_reason` | Text | Cancellation Reason |  |  |  |
| `note` | Text | Notes |  |  |  |

### Database constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The assessment reference must be unique per company. |

### Public methods (7)

- `create(vals_list)` - Assign the reference and inherit the matrix from the risk.
- `write(vals)` - Prevent modification of the estimation once approved.
- `unlink()` - Restrict deletion to draft assessments.
- `action_confirm()` - Confirm the estimation and submit it for approval.
- `action_approve()` - Approve a confirmed assessment.
- `action_open_cancel_wizard()` - Open the assessment cancellation wizard.
- `action_reset_to_draft()` - Return a confirmed assessment to draft for correction.

### Internal methods (5)

- `_compute_evaluation()` - Resolve the matrix cell and copy its evaluation onto the record.
- `_compute_display_name()` - Show the assessment reference and its type.
- `_onchange_risk_id()` - Copy the matrix from the risk and clear incompatible levels.
- `_check_levels_belong_to_matrix()` - Ensure both levels come from the assessment's matrix and scale.
- `_check_single_initial_assessment()` - Allow at most one non-cancelled initial assessment per risk.

---

## `ls.risk.mitigation`

- **Class**: `LsRiskMitigation` in `models/ls_risk_mitigation.py`
- **Kind**: Persistent
- **Description**: Risk Control Measure
- **Inherits**: `mail.thread`, `mail.activity.mixin`, `ls.risk.role.mixin`
- **Order**: `risk_id, option_priority, sequence, id`

One risk control measure with implementation and effectiveness evidence.

### Fields (26)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Reference |  | yes |  |
| `risk_id` | Many2one | Risk | `ls.risk.register` | yes |  |
| `company_id` | Many2one | Company | `res.company` |  | related `risk_id.company_id` |
| `sequence` | Integer | Sequence |  |  |  |
| `title` | Char | Title |  | yes |  |
| `description` | Text | Description |  | yes |  |
| `control_option` | Selection | Risk Control Option |  | yes |  |
| `option_priority` | Integer | Option Priority |  |  | compute `_compute_option_priority`, stored |
| `option_analysis` | Text | Option Analysis |  |  |  |
| `responsible_id` | Many2one | Responsible | `res.users` | yes |  |
| `due_date` | Date | Due Date |  |  |  |
| `state` | Selection | Status |  | yes |  |
| `is_overdue` | Boolean | Overdue |  |  | compute `_compute_is_overdue` |
| `approved_by_id` | Many2one | Approved By | `res.users` |  |  |
| `approval_date` | Datetime | Approval Date |  |  |  |
| `implementation_date` | Date | Implementation Date |  |  |  |
| `implementation_evidence` | Text | Implementation Evidence |  |  |  |
| `implementation_verified_by_id` | Many2one | Implementation Verified By | `res.users` |  |  |
| `implementation_verification_date` | Datetime | Implementation Verification Date |  |  |  |
| `effectiveness_evidence` | Text | Effectiveness Evidence |  |  |  |
| `effectiveness_verified_by_id` | Many2one | Effectiveness Verified By | `res.users` |  |  |
| `effectiveness_verification_date` | Datetime | Effectiveness Verification Date |  |  |  |
| `introduces_new_risk` | Boolean | Introduces New Risk |  |  |  |
| `new_risk_description` | Text | New Risk Description |  |  |  |
| `new_risk_id` | Many2one | New Risk Record | `ls.risk.register` |  |  |
| `cancel_reason` | Text | Cancellation Reason |  |  |  |

### Database constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The risk control measure reference must be unique per company. |

### Public methods (9)

- `create(vals_list)` - Assign the measure reference from the configured sequence.
- `write(vals)` - Protect verification evidence once a measure is verified.
- `unlink()` - Restrict deletion to draft measures.
- `action_approve()` - Approve a draft measure for implementation.
- `action_start()` - Mark an approved measure as being implemented.
- `action_mark_implemented()` - Record that the measure has been implemented.
- `action_verify_effectiveness()` - Verify the effectiveness of an implemented measure.
- `action_create_new_risk()` - Create a risk register entry for the risk this measure introduces.
- `action_open_cancel_wizard()` - Open the risk control measure cancellation wizard.

### Internal methods (5)

- `_compute_option_priority()` - Map the control option onto its numeric priority.
- `_compute_is_overdue()` - Flag measures past their due date that are not yet verified.
- `_compute_display_name()` - Show the reference followed by the title.
- `_check_new_risk_described()` - Require a description whenever a new risk is declared.
- `_check_new_risk_not_self()` - Forbid pointing the introduced risk at the risk being controlled.

---

## `ls.risk.fmea`

- **Class**: `LsRiskFmea` in `models/ls_risk_fmea.py`
- **Kind**: Persistent
- **Description**: FMEA Worksheet
- **Inherits**: `mail.thread`, `mail.activity.mixin`, `ls.risk.role.mixin`
- **Order**: `id desc`

An FMEA worksheet covering a defined scope.

### Fields (25)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `name` | Char | Reference |  | yes |  |
| `title` | Char | Title |  | yes |  |
| `company_id` | Many2one | Company | `res.company` | yes |  |
| `fmea_type` | Selection | FMEA Type |  | yes |  |
| `scope` | Text | Scope |  | yes |  |
| `assumptions` | Text | Assumptions and Boundaries |  |  |  |
| `revision` | Integer | Revision |  | yes |  |
| `revision_reason` | Text | Revision Reason |  |  |  |
| `facilitator_id` | Many2one | Facilitator | `res.users` | yes |  |
| `team_member_ids` | Many2many | Team Members | `res.users` |  |  |
| `start_date` | Date | Start Date |  | yes |  |
| `rpn_threshold` | Integer | RPN Action Threshold |  | yes |  |
| `severity_action_threshold` | Integer | Severity Action Threshold |  | yes |  |
| `state` | Selection | Status |  | yes |  |
| `active` | Boolean | Active |  |  |  |
| `line_ids` | One2many | Failure Modes | `ls.risk.fmea.line` |  |  |
| `line_count` | Integer | Failure Mode Count |  |  | compute `_compute_line_statistics`, stored |
| `max_rpn` | Integer | Highest RPN |  |  | compute `_compute_line_statistics`, stored |
| `action_required_count` | Integer | Lines Requiring Action |  |  | compute `_compute_line_statistics`, stored |
| `open_action_count` | Integer | Open Actions |  |  | compute `_compute_line_statistics`, stored |
| `reviewed_by_id` | Many2one | Reviewed By | `res.users` |  |  |
| `review_date` | Datetime | Review Date |  |  |  |
| `approved_by_id` | Many2one | Approved By | `res.users` |  |  |
| `approval_date` | Datetime | Approval Date |  |  |  |
| `cancel_reason` | Text | Cancellation Reason |  |  |  |

### Database constraints (4)

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The FMEA reference must be unique per company. |
| `_revision_positive` | `CHECK(revision > 0)` | The FMEA revision number must be strictly positive. |
| `_rpn_threshold_range` | `CHECK(rpn_threshold >= 1 AND rpn_threshold <= 1000)` | The RPN action threshold must be between 1 and 1000. |
| `_severity_threshold_range` | `CHECK(severity_action_threshold >= 1 AND severity_action_threshold <= 10)` | The severity action threshold must be between 1 and 10. |

### Public methods (9)

- `create(vals_list)` - Assign the worksheet reference from the configured sequence.
- `unlink()` - Restrict deletion to draft and cancelled worksheets.
- `action_start()` - Move a draft worksheet into the in-progress state.
- `action_submit_review()` - Submit an in-progress worksheet for review.
- `action_review()` - Record the review of a worksheet.
- `action_approve()` - Approve a reviewed worksheet.
- `action_close()` - Close an approved worksheet.
- `action_open_cancel_wizard()` - Open the FMEA cancellation wizard.
- `action_create_revision()` - Create the next revision of an approved or closed worksheet.

### Internal methods (2)

- `_compute_line_statistics()` - Derive worksheet level statistics from its lines.
- `_compute_display_name()` - Show the reference, title and revision.

---

## `ls.risk.fmea.line`

- **Class**: `LsRiskFmeaLine` in `models/ls_risk_fmea.py`
- **Kind**: Persistent
- **Description**: FMEA Failure Mode
- **Order**: `fmea_id, sequence, id`

One failure mode row of an FMEA worksheet.

### Fields (25)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `fmea_id` | Many2one | FMEA | `ls.risk.fmea` | yes |  |
| `company_id` | Many2one | Company | `res.company` |  | related `fmea_id.company_id` |
| `sequence` | Integer | Sequence |  |  |  |
| `item` | Char | Item |  | yes |  |
| `item_function` | Char | Function |  | yes |  |
| `failure_mode` | Char | Failure Mode |  | yes |  |
| `failure_effect` | Text | Effect of Failure |  | yes |  |
| `severity` | Integer | Severity (S) |  | yes |  |
| `failure_cause` | Text | Potential Cause |  | yes |  |
| `occurrence` | Integer | Occurrence (O) |  | yes |  |
| `current_controls` | Text | Current Controls |  |  |  |
| `detection` | Integer | Detection (D) |  | yes |  |
| `rpn` | Integer | RPN |  |  | compute `_compute_rpn`, stored |
| `action_required` | Boolean | Action Required |  |  | compute `_compute_action_required`, stored |
| `recommended_action` | Text | Recommended Action |  |  |  |
| `responsible_id` | Many2one | Responsible | `res.users` |  |  |
| `target_date` | Date | Target Date |  |  |  |
| `actions_taken` | Text | Actions Taken |  |  |  |
| `action_state` | Selection | Action Status |  | yes |  |
| `revised_severity` | Integer | Revised Severity |  |  |  |
| `revised_occurrence` | Integer | Revised Occurrence |  |  |  |
| `revised_detection` | Integer | Revised Detection |  |  |  |
| `revised_rpn` | Integer | Revised RPN |  |  | compute `_compute_revised_rpn`, stored |
| `rpn_reduction` | Integer | RPN Reduction |  |  | compute `_compute_revised_rpn`, stored |
| `risk_id` | Many2one | Risk Register Entry | `ls.risk.register` |  |  |

### Database constraints (6)

| Name | Definition | Message |
|---|---|---|
| `_severity_range` | `CHECK(severity >= 1 AND severity <= 10)` | Severity must be between 1 and 10. |
| `_occurrence_range` | `CHECK(occurrence >= 1 AND occurrence <= 10)` | Occurrence must be between 1 and 10. |
| `_detection_range` | `CHECK(detection >= 1 AND detection <= 10)` | Detection must be between 1 and 10. |
| `_revised_severity_range` | `CHECK(revised_severity >= 0 AND revised_severity <= 10)` | Revised severity must be between 1 and 10, or left empty. |
| `_revised_occurrence_range` | `CHECK(revised_occurrence >= 0 AND revised_occurrence <= 10)` | Revised occurrence must be between 1 and 10, or left empty. |
| `_revised_detection_range` | `CHECK(revised_detection >= 0 AND revised_detection <= 10)` | Revised detection must be between 1 and 10, or left empty. |

### Public methods (1)

- `action_create_risk()` - Raise a risk register entry from this failure mode.

### Internal methods (6)

- `_compute_rpn()` - Compute the Risk Priority Number as S x O x D.
- `_compute_action_required()` - Flag lines that meet either worksheet action threshold.
- `_compute_revised_rpn()` - Compute the revised RPN and the reduction achieved.
- `_compute_display_name()` - Show the item and its failure mode.
- `_check_revised_ratings_complete()` - Require all three revised ratings together, or none of them.
- `_onchange_ratings()` - Open the action when a rating change makes action required.

---

## `ls.risk.role.mixin`

- **Class**: `LsRiskRoleMixin` in `models/ls_risk_role_mixin.py`
- **Kind**: Abstract
- **Description**: Risk Management Role Checks

Provide a reusable Risk Manager role assertion.

### Internal methods (1)

- `_ensure_risk_manager(operation)` - Raise unless the current user belongs to the Risk Manager group.

---

## `ls.risk.assess.wizard`

- **Class**: `LsRiskAssessWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Assess Risks

Create one assessment for each of the selected risks.

### Fields (7)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `risk_ids` | Many2many | Risks | `ls.risk.register` | yes |  |
| `matrix_id` | Many2one | Risk Matrix | `ls.risk.matrix` |  | compute `_compute_matrix_id`, stored |
| `assessment_type` | Selection | Assessment Type |  | yes |  |
| `severity_level_id` | Many2one | Severity | `ls.risk.matrix.level` | yes |  |
| `probability_level_id` | Many2one | Probability | `ls.risk.matrix.level` | yes |  |
| `assessment_date` | Date | Assessment Date |  | yes |  |
| `estimation_rationale` | Text | Estimation Rationale |  | yes |  |

### Public methods (1)

- `action_create_assessments()` - Create one assessment per selected risk.

### Internal methods (1)

- `_compute_matrix_id()` - Adopt the shared matrix of the selected risks.

---

## `ls.risk.residual.wizard`

- **Class**: `LsRiskResidualWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Accept Residual Risk

Record the residual risk acceptance decision for one risk.

### Fields (5)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `risk_id` | Many2one | Risk | `ls.risk.register` | yes |  |
| `current_risk_level` | Selection | Current Risk Level |  |  | related `risk_id.current_risk_level` |
| `current_acceptability` | Selection | Current Acceptability |  |  | related `risk_id.current_acceptability` |
| `justification` | Text | Acceptance Justification |  | yes |  |
| `benefit_risk_analysis` | Text | Benefit-Risk Analysis |  |  |  |

### Public methods (1)

- `action_accept()` - Record the acceptance decision on the risk.

---

## `ls.risk.close.wizard`

- **Class**: `LsRiskCloseWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Close Risks

Close the selected risks against a recorded reason.

### Fields (2)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `risk_ids` | Many2many | Risks | `ls.risk.register` | yes |  |
| `closure_reason` | Text | Closure Reason |  | yes |  |

### Public methods (1)

- `action_close()` - Close each selected risk after checking its evidence.

---

## `ls.risk.cancel.wizard`

- **Class**: `LsRiskCancelWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Cancel Risks

Cancel the selected risks against a recorded reason.

### Fields (2)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `risk_ids` | Many2many | Risks | `ls.risk.register` | yes |  |
| `cancel_reason` | Text | Cancellation Reason |  | yes |  |

### Public methods (1)

- `action_cancel()` - Cancel each selected risk.

---

## `ls.risk.assessment.cancel.wizard`

- **Class**: `LsRiskAssessmentCancelWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Cancel Risk Assessments

Cancel the selected assessments against a recorded reason.

### Fields (2)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `assessment_ids` | Many2many | Assessments | `ls.risk.assessment` | yes |  |
| `cancel_reason` | Text | Cancellation Reason |  | yes |  |

### Public methods (1)

- `action_cancel()` - Cancel each selected assessment.

---

## `ls.risk.mitigation.cancel.wizard`

- **Class**: `LsRiskMitigationCancelWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Cancel Risk Control Measures

Cancel the selected risk control measures against a recorded reason.

### Fields (2)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `mitigation_ids` | Many2many | Risk Control Measures | `ls.risk.mitigation` | yes |  |
| `cancel_reason` | Text | Cancellation Reason |  | yes |  |

### Public methods (1)

- `action_cancel()` - Cancel each selected risk control measure.

---

## `ls.risk.fmea.cancel.wizard`

- **Class**: `LsRiskFmeaCancelWizard` in `wizards/ls_risk_wizards.py`
- **Kind**: Transient
- **Description**: Cancel FMEA Worksheets

Cancel the selected FMEA worksheets against a recorded reason.

### Fields (2)

| Field | Type | Label | Target | Req. | Stored compute / related |
|---|---|---|---|---|---|
| `fmea_ids` | Many2many | FMEA Worksheets | `ls.risk.fmea` | yes |  |
| `cancel_reason` | Text | Cancellation Reason |  | yes |  |

### Public methods (1)

- `action_cancel()` - Cancel each selected FMEA worksheet.

---

## Totals

- Models: 17
- Fields: 212
- Methods: 96
- Database constraints: 22
