# API REFERENCE — `ls_lab`

**Generated from source by `tools/` AST extraction. Do not edit by hand.**

Generated: 2026-08-07

Total fields declared: 253.
Models: 13 concrete, 2 abstract mixins.

---

## `ls.lab.controlled.mixin`

*Life Sciences Laboratory Controlled Record Mixin*  
Source: `models/ls_lab_mixin.py`  

**Public methods**

- `create()` — Assign the document code from the model's sequence when absent.
- `write()` — Refuse changes to controlled fields while the record is frozen.
- `unlink()` — Refuse deletion of records that have left the draft state.

**Internal methods**

- `_create_successor_version()` — Return a new draft record superseding ``self``.
- `_assert_state()` — Raise a :class:`UserError` unless every record is in ``expected``.

---

## `ls.lab.signed.mixin`

*Life Sciences Laboratory Signature Intent Mixin*  
Source: `models/ls_lab_mixin.py`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `signature_user_id` | Many2one | Signed By | `res.users` | readonly |
| `signature_date` | Datetime | Signature Date |  | readonly |
| `signature_meaning` | Char | Signature Meaning |  | readonly |

**Public methods**

- `action_signature_apply()` — Record signature intent and run the model's signed action.

**Internal methods**

- `_signature_target_action()` — Perform the action the signature authorises. Overridden downstream.

---

## `ls.lab.storage_condition`

*Laboratory Storage Condition*  
Source: `models/ls_lab_storage_condition.py`  
Order: `sequence, code`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Name |  | required |
| `code` | Char | Code |  | required |
| `sequence` | Integer | Sequence |  |  |
| `temperature_c` | Float | Temperature (deg C) |  |  |
| `temperature_tolerance_c` | Float | Temperature Tolerance (+/- deg C) |  |  |
| `humidity_rh` | Float | Relative Humidity (%) |  |  |
| `humidity_tolerance_rh` | Float | Humidity Tolerance (+/- %) |  |  |
| `light_condition` | Selection | Light Condition |  | required |
| `description` | Text | Description |  |  |
| `reference` | Char | Reference |  |  |
| `active` | Boolean | Active |  |  |
| `company_id` | Many2one | Company | `res.company` |  |

**SQL constraints** (`models.Constraint`):

- `_code_uniq`: `UNIQUE (code)` — The storage condition code must be unique.

**Internal methods**

- `_compute_display_name()` — Show the code together with the descriptive name.

---

## `ls.lab.test_method`

*Laboratory Test Method*  
Source: `models/ls_lab_test_method.py`  
Inherits: `ls.lab.controlled.mixin`, `mail.thread`, `mail.activity.mixin`  
Order: `code, version desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Method Name |  | required |
| `code` | Char | Method Code |  | required, readonly |
| `version` | Integer | Version |  | required, readonly |
| `state` | Selection | Status |  | required |
| `technique` | Selection | Technique |  | required |
| `result_type` | Selection | Result Type |  | required |
| `default_uom_id` | Many2one | Default Unit of Measure | `uom.uom` |  |
| `decimal_precision` | Integer | Decimal Places |  |  |
| `reference_document` | Char | Reference Document |  |  |
| `procedure_summary` | Text | Procedure Summary |  |  |
| `description` | Text | Description |  |  |
| `instrument_required` | Boolean | Instrument Required |  |  |
| `instrument_category` | Char | Instrument Category |  |  |
| `validation_status` | Selection | Method Validation Status |  | required |
| `validation_reference` | Char | Validation Reference |  |  |
| `approved_by_id` | Many2one | Approved By | `res.users` | readonly |
| `approval_date` | Datetime | Approval Date |  | readonly |
| `obsolete_reason` | Text | Obsolescence Reason |  |  |
| `predecessor_id` | Many2one | Supersedes | `ls.lab.test_method` | readonly |
| `successor_id` | Many2one | Superseded By | `ls.lab.test_method` | readonly |
| `specification_line_ids` | One2many | Used In Specifications | `ls.lab.specification_line` |  |
| `specification_line_count` | Integer | Specification Usage | compute `_compute_specification_line_count` | computed |
| `active` | Boolean | Active |  |  |
| `company_id` | Many2one | Company | `res.company` |  |

**SQL constraints** (`models.Constraint`):

- `_code_version_uniq`: `UNIQUE (code, version)` — A test method version must be unique for a given method code.

**Public methods**

- `action_submit_review()` — Move a draft method to Under Review.
- `action_reset_draft()` — Return a method under review to Draft.
- `action_approve()` — Approve a method under review and freeze it.
- `action_set_obsolete()` — Make an approved method obsolete.
- `action_create_revision()` — Create the next draft version of an approved method.

**Internal methods**

- `_compute_specification_line_count()` — Count the specification lines referencing each method.
- `_compute_display_name()` — Display code, version and name so that versions are distinguishable.
- `_cron_notify_method_review_due()` — Post a notice on approved methods due for periodic review.

---

## `ls.lab.specification`

*Laboratory Product Specification*  
Source: `models/ls_lab_specification.py`  
Inherits: `ls.lab.controlled.mixin`, `mail.thread`, `mail.activity.mixin`  
Order: `code, version desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Specification Name |  | required |
| `code` | Char | Specification Code |  | required, readonly |
| `version` | Integer | Version |  | required, readonly |
| `state` | Selection | Status |  | required |
| `product_id` | Many2one | Product | `product.product` | required |
| `spec_type` | Selection | Specification Type |  | required |
| `effective_date` | Date | Effective Date |  |  |
| `line_ids` | One2many | Acceptance Criteria | `ls.lab.specification_line` |  |
| `line_count` | Integer | Criteria Count | compute `_compute_line_count` | computed |
| `notes` | Text | Notes |  |  |
| `approved_by_id` | Many2one | Approved By | `res.users` | readonly |
| `approval_date` | Datetime | Approval Date |  | readonly |
| `obsolete_reason` | Text | Obsolescence Reason |  |  |
| `predecessor_id` | Many2one | Supersedes | `ls.lab.specification` | readonly |
| `successor_id` | Many2one | Superseded By | `ls.lab.specification` | readonly |
| `active` | Boolean | Active |  |  |
| `company_id` | Many2one | Company | `res.company` |  |

**SQL constraints** (`models.Constraint`):

- `_code_version_uniq`: `UNIQUE (code, version)` — A specification version must be unique for a given specification code.

**Public methods**

- `action_submit_review()` — Move a draft specification to Under Review.
- `action_reset_draft()` — Return a specification under review to Draft.
- `action_approve()` — Approve a specification under review and freeze it.
- `action_set_obsolete()` — Make an approved specification obsolete, requiring a reason.
- `action_create_revision()` — Create the next draft version, copying the acceptance criteria.

**Internal methods**

- `_compute_line_count()` — Store the number of acceptance criteria for listing and filtering.
- `_compute_display_name()` — Display code, version and name so that versions are distinguishable.
- `_check_single_approved_version()` — Forbid two concurrently approved specifications for the same scope.
- `_check_lines_present_on_approval()` — A specification without criteria cannot be approved.

---

## `ls.lab.specification_line`

*Laboratory Specification Line*  
Source: `models/ls_lab_specification_line.py`  
Order: `specification_id, sequence, id`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `specification_id` | Many2one | Specification | `ls.lab.specification` | required |
| `sequence` | Integer | Sequence |  |  |
| `test_method_id` | Many2one | Test Method | `ls.lab.test_method` | required |
| `result_type` | Selection | Result Type | related `test_method_id.result_type` | readonly |
| `criterion_type` | Selection | Criterion Type |  | required |
| `min_value` | Float | Minimum |  |  |
| `max_value` | Float | Maximum |  |  |
| `target_value` | Float | Target |  |  |
| `text_criterion` | Char | Expected Text |  |  |
| `uom_id` | Many2one | Unit of Measure | `uom.uom` |  |
| `decimal_precision` | Integer | Decimal Places |  |  |
| `is_mandatory` | Boolean | Mandatory |  |  |
| `report_on_coa` | Boolean | Show On CoA |  |  |
| `criterion_display` | Char | Acceptance Criterion | compute `_compute_criterion_display` | computed |
| `company_id` | Many2one | Company | related `specification_id.company_id` |  |

**SQL constraints** (`models.Constraint`):

- `_sequence_positive`: `CHECK (sequence >= 0)` — The specification line sequence must be zero or positive.

**Public methods**

- `create()` — Refuse creation of a line on a frozen specification (BRU-03).
- `write()` — Refuse modification of a line on a frozen specification (BRU-03).
- `unlink()` — Refuse deletion of a line on a frozen specification (BRU-03).

**Internal methods**

- `_compute_criterion_display()` — Render the acceptance criterion as readable text.
- `_compute_display_name()` — Show the method name with its criterion.
- `_check_method_approved()` — Only approved test methods may be referenced (BRU-04).
- `_check_criterion_consistency()` — Each criterion type must carry the values it needs (BRU-30).
- `_assert_parent_editable()` — Raise if any given specification is approved or obsolete.
- `_evaluate()` — Return the conformity verdict for a recorded result.

---

## `ls.lab.sample`

*Laboratory Sample*  
Source: `models/ls_lab_sample.py`  
Inherits: `ls.lab.signed.mixin`, `mail.thread`, `mail.activity.mixin`  
Order: `received_date desc, name desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Sample Reference |  | required, readonly |
| `description` | Char | Description |  |  |
| `sample_type` | Selection | Sample Type |  | required |
| `state` | Selection | Status |  | required |
| `product_id` | Many2one | Product | `product.product` | required |
| `lot_id` | Many2one | Lot / Serial Number | `stock.lot` |  |
| `batch_reference` | Char | Batch Reference |  |  |
| `specification_id` | Many2one | Specification | `ls.lab.specification` | required |
| `quantity` | Float | Quantity |  |  |
| `uom_id` | Many2one | Unit of Measure | `uom.uom` |  |
| `sampled_date` | Datetime | Sampling Date |  |  |
| `received_date` | Datetime | Receipt Date |  | required |
| `due_date` | Date | Due Date |  |  |
| `priority` | Selection | Priority |  |  |
| `sampled_by_id` | Many2one | Sampled By | `res.users` |  |
| `received_by_id` | Many2one | Received By | `res.users` |  |
| `sampling_point` | Char | Sampling Point |  |  |
| `storage_condition_id` | Many2one | Storage Condition | `ls.lab.storage_condition` |  |
| `result_ids` | One2many | Test Results | `ls.lab.test_result` |  |
| `result_count` | Integer | Results | compute `_compute_result_statistics` | computed |
| `pending_result_count` | Integer | Pending Results | compute `_compute_result_statistics` | computed |
| `overall_result` | Selection | Overall Result | compute `_compute_overall_result` | computed |
| `oos_ids` | One2many | OOS / OOT Investigations | `ls.lab.oos` |  |
| `open_oos_count` | Integer | Open Investigations | compute `_compute_open_oos_count` | computed |
| `reviewed_by_id` | Many2one | Reviewed By | `res.users` | readonly |
| `review_date` | Datetime | Review Date |  | readonly |
| `approved_by_id` | Many2one | Approved By | `res.users` | readonly |
| `approval_date` | Datetime | Approval Date |  | readonly |
| `reported_by_id` | Many2one | Reported By | `res.users` | readonly |
| `report_date` | Datetime | Report Date |  | readonly |
| `cancel_reason` | Text | Cancellation Reason |  | readonly |
| `cancelled_by_id` | Many2one | Cancelled By | `res.users` | readonly |
| `stability_timepoint_id` | Many2one | Stability Time Point | `ls.lab.stability_timepoint` | readonly |
| `coa_ids` | One2many | Certificates of Analysis | `ls.lab.coa` |  |
| `coa_count` | Integer | Certificates | compute `_compute_coa_count` | computed |
| `company_id` | Many2one | Company | `res.company` |  |

**SQL constraints** (`models.Constraint`):

- `_name_uniq`: `UNIQUE (name)` — The sample reference must be unique.

**Public methods**

- `create()` — Assign the sample reference and generate the test list.
- `action_start()` — Move a received sample into preparation.
- `action_start_testing()` — Open the sample for result entry.
- `action_record_results()` — Confirm that all mandatory results have been entered (BRU-11).
- `action_review()` — Record second-person review of the sample (BRU-12).
- `action_approve()` — Approve the sample, refusing while an investigation is open (BRU-15).
- `action_report()` — Mark the sample as reported.
- `action_open_cancel_wizard()` — Open the cancellation wizard, which requires a reason (BRU-26).
- `action_view_results()` — Open the result lines of this sample.
- `action_view_oos()` — Open the investigations raised on this sample.
- `action_view_coa()` — Open the certificates issued from this sample.
- `action_open_approval_signature()` — Open the signature-intent wizard for sample approval.

**Internal methods**

- `_compute_result_statistics()` — Count total results and those still awaiting entry.
- `_compute_overall_result()` — Derive the sample verdict from its result lines.
- `_compute_open_oos_count()` — Count investigations on the sample that are not yet closed.
- `_compute_coa_count()` — Count certificates issued from the sample.
- `_compute_display_name()` — Show the sample reference with its product.
- `_check_specification_approved()` — A sample must reference an approved specification (BRU-06).
- `_check_reviewer_segregation()` — The sample reviewer may not have produced any of its results.
- `_check_approver_segregation()` — The approver may not be the reviewer (BRU-14).
- `_generate_result_lines()` — Create one result line per specification line, once.
- `_assert_state()` — Raise unless every sample is in one of the expected states.
- `_signature_target_action()` — Approve the sample once signature intent has been recorded.
- `_cron_notify_overdue_samples()` — Post a notice on samples past their due date.

---

## `ls.lab.test_result`

*Laboratory Test Result*  
Source: `models/ls_lab_test_result.py`  
Inherits: `mail.thread`, `mail.activity.mixin`  
Order: `sample_id, sequence, id`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `sample_id` | Many2one | Sample | `ls.lab.sample` | required |
| `specification_line_id` | Many2one | Specification Line | `ls.lab.specification_line` | required |
| `test_method_id` | Many2one | Test Method | related `specification_line_id.test_method_id` |  |
| `sequence` | Integer | Sequence | related `specification_line_id.sequence` |  |
| `criterion_display` | Char | Acceptance Criterion | related `specification_line_id.criterion_display` |  |
| `result_type` | Selection | Result Type | related `specification_line_id.result_type` |  |
| `criterion_type` | Selection | Criterion Type | related `specification_line_id.criterion_type` |  |
| `is_mandatory` | Boolean | Mandatory | related `specification_line_id.is_mandatory` |  |
| `product_id` | Many2one | Product | related `sample_id.product_id` |  |
| `state` | Selection | Status |  | required |
| `result_numeric` | Float | Numeric Result |  |  |
| `result_text` | Char | Text Result |  |  |
| `result_boolean` | Selection | Pass / Fail Result |  |  |
| `result_display` | Char | Result | compute `_compute_result_display` | computed |
| `uom_id` | Many2one | Unit of Measure | `uom.uom` |  |
| `evaluation` | Selection | Evaluation | compute `_compute_evaluation` | readonly, computed |
| `is_oot` | Boolean | Out Of Trend |  |  |
| `oot_justification` | Text | Out Of Trend Justification |  |  |
| `analyst_id` | Many2one | Analyst | `res.users` | readonly |
| `test_date` | Datetime | Test Date |  |  |
| `instrument_reference` | Char | Instrument Reference |  |  |
| `reviewed_by_id` | Many2one | Reviewed By | `res.users` | readonly |
| `review_date` | Datetime | Review Date |  | readonly |
| `oos_id` | Many2one | Investigation | `ls.lab.oos` | readonly |
| `is_retest` | Boolean | Is Retest |  | readonly |
| `retest_of_id` | Many2one | Retest Of | `ls.lab.test_result` | readonly |
| `remarks` | Text | Remarks |  |  |
| `company_id` | Many2one | Company | related `sample_id.company_id` |  |

**SQL constraints** (`models.Constraint`):

- `_sequence_positive`: `CHECK (sequence >= 0)` — The test result sequence must be zero or positive.

**Public methods**

- `create()` — Guard manual creation and enforce retest authorisation (BRU-17).
- `write()` — Refuse modification of a reviewed result.
- `unlink()` — Refuse deletion of a result that carries recorded data.
- `action_enter()` — Record the result, evaluate it, and raise an OOS on failure.
- `action_review()` — Record second-person review of the result (BRU-10).
- `action_reset_draft()` — Return an entered result to draft, before any review.

**Internal methods**

- `_compute_evaluation()` — Derive conformity from the approved specification line.
- `_compute_result_display()` — Render the recorded result as readable text.
- `_compute_display_name()` — Show the sample reference with the method name.
- `_check_reviewer_segregation()` — The reviewer of a result may not be its analyst (BRU-10).
- `_check_oot_justified()` — An out-of-trend assertion requires a justification (BRU-28).
- `_check_line_belongs_to_specification()` — A result must reference a line of its sample's specification.
- `_assert_retest_authorised()` — Refuse a retest result unless its investigation authorised one.
- `_raise_investigations()` — Create an investigation for each non-conforming or OOT result.

---

## `ls.lab.oos`

*Laboratory OOS / OOT Investigation*  
Source: `models/ls_lab_oos.py`  
Inherits: `mail.thread`, `mail.activity.mixin`  
Order: `opened_date desc, name desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Investigation Reference |  | required, readonly |
| `oos_type` | Selection | Type |  | required |
| `state` | Selection | Status |  | required |
| `test_result_id` | Many2one | Originating Result | `ls.lab.test_result` | required |
| `sample_id` | Many2one | Sample | related `test_result_id.sample_id` |  |
| `product_id` | Many2one | Product | related `test_result_id.product_id` |  |
| `test_method_id` | Many2one | Test Method | related `test_result_id.test_method_id` |  |
| `recorded_value` | Char | Recorded Value | related `test_result_id.result_display` |  |
| `acceptance_criterion` | Char | Acceptance Criterion | related `test_result_id.criterion_display` |  |
| `investigator_id` | Many2one | Investigator | `res.users` | required |
| `opened_date` | Datetime | Opened On |  | required, readonly |
| `description` | Text | Description |  |  |
| `chk_analyst_interview` | Boolean | Analyst Interviewed |  |  |
| `chk_calculation_verified` | Boolean | Calculation Verified |  |  |
| `chk_instrument_verified` | Boolean | Instrument Performance Verified |  |  |
| `chk_standard_verified` | Boolean | Standards And Reagents Verified |  |  |
| `chk_sample_integrity` | Boolean | Sample Integrity Verified |  |  |
| `chk_method_followed` | Boolean | Method Adherence Verified |  |  |
| `phase1_findings` | Text | Phase I Findings |  |  |
| `phase1_conclusion` | Selection | Phase I Conclusion |  |  |
| `phase1_completed_by_id` | Many2one | Phase I Completed By | `res.users` | readonly |
| `phase1_date` | Datetime | Phase I Completion Date |  | readonly |
| `phase2_findings` | Text | Phase II Findings |  |  |
| `manufacturing_review` | Text | Manufacturing Review |  |  |
| `root_cause` | Text | Root Cause |  |  |
| `phase2_completed_by_id` | Many2one | Phase II Completed By | `res.users` | readonly |
| `phase2_date` | Datetime | Phase II Completion Date |  | readonly |
| `retest_authorised` | Boolean | Retest Authorised |  | readonly |
| `retest_justification` | Text | Retest Justification |  |  |
| `retest_authorised_by_id` | Many2one | Retest Authorised By | `res.users` | readonly |
| `retest_authorisation_date` | Datetime | Retest Authorisation Date |  | readonly |
| `resample_authorised` | Boolean | Resample Authorised |  | readonly |
| `resample_justification` | Text | Resample Justification |  |  |
| `resample_authorised_by_id` | Many2one | Resample Authorised By | `res.users` | readonly |
| `resample_authorisation_date` | Datetime | Resample Authorisation Date |  | readonly |
| `retest_result_ids` | One2many | Related Results | `ls.lab.test_result` |  |
| `retest_result_count` | Integer | Related Result Count | compute `_compute_retest_result_count` | computed |
| `final_conclusion` | Selection | Final Conclusion |  |  |
| `product_disposition` | Selection | Product Disposition |  |  |
| `disposition_justification` | Text | Disposition Justification |  |  |
| `capa_reference` | Char | CAPA Reference |  |  |
| `qa_approver_id` | Many2one | Quality Approver | `res.users` | readonly |
| `closure_date` | Datetime | Closure Date |  | readonly |
| `cancel_reason` | Text | Cancellation Reason |  |  |
| `company_id` | Many2one | Company | related `sample_id.company_id` |  |

**SQL constraints** (`models.Constraint`):

- `_name_uniq`: `UNIQUE (name)` — The investigation reference must be unique.

**Public methods**

- `create()` — Assign the investigation reference from the sequence.
- `unlink()` — Refuse deletion of an investigation in any state.
- `action_start_phase1()` — Begin the laboratory phase of the investigation.
- `action_complete_phase1()` — Close the laboratory phase, requiring findings and a conclusion.
- `action_start_phase2()` — Extend the investigation beyond the laboratory (BRU-21).
- `action_complete_phase2()` — Close the full investigation, requiring findings and a root cause.
- `action_conclude()` — Conclude directly after Phase I when a laboratory cause was found.
- `action_authorise_retest()` — Record retest authorisation with its justification (BRU-18).
- `action_authorise_resample()` — Record resample authorisation with its justification.
- `action_close()` — Close the investigation with a conclusion and disposition (BRU-19).
- `action_cancel()` — Cancel the investigation, requiring a recorded reason.
- `action_view_results()` — Open the results linked to this investigation.

**Internal methods**

- `_compute_retest_result_count()` — Count the results linked to this investigation.
- `_compute_display_name()` — Show the investigation reference with its product.
- `_check_approver_segregation()` — The quality approver may not be the investigator (BRU-20).
- `_assert_state()` — Raise unless every investigation is in one of the expected states.

---

## `ls.lab.stability_study`

*Laboratory Stability Study*  
Source: `models/ls_lab_stability.py`  
Inherits: `mail.thread`, `mail.activity.mixin`  
Order: `start_date desc, name desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Study Reference |  | required, readonly |
| `description` | Char | Description |  |  |
| `state` | Selection | Status |  | required |
| `product_id` | Many2one | Product | `product.product` | required |
| `lot_id` | Many2one | Lot / Serial Number | `stock.lot` |  |
| `batch_reference` | Char | Batch Reference |  |  |
| `batch_size` | Float | Batch Size |  |  |
| `batch_size_uom_id` | Many2one | Batch Size Unit | `uom.uom` |  |
| `manufacture_date` | Date | Manufacturing Date |  |  |
| `study_type` | Selection | Study Type |  | required |
| `storage_condition_id` | Many2one | Storage Condition | `ls.lab.storage_condition` | required |
| `container_closure` | Char | Container Closure System |  |  |
| `specification_id` | Many2one | Specification | `ls.lab.specification` |  |
| `protocol_reference` | Char | Protocol Reference |  |  |
| `start_date` | Date | Start Date |  |  |
| `planned_end_date` | Date | Planned End Date |  |  |
| `timepoint_ids` | One2many | Time Points | `ls.lab.stability_timepoint` |  |
| `timepoint_count` | Integer | Time Points | compute `_compute_timepoint_statistics` | computed |
| `completed_timepoint_count` | Integer | Completed Time Points | compute `_compute_timepoint_statistics` | computed |
| `approved_by_id` | Many2one | Approved By | `res.users` | readonly |
| `approval_date` | Datetime | Approval Date |  | readonly |
| `termination_reason` | Text | Termination Reason |  |  |
| `company_id` | Many2one | Company | `res.company` |  |

**SQL constraints** (`models.Constraint`):

- `_name_uniq`: `UNIQUE (name)` — The stability study reference must be unique.

**Public methods**

- `create()` — Assign the study reference from the sequence.
- `action_approve()` — Approve the study protocol.
- `action_start()` — Start the study, requiring a start date.
- `action_complete()` — Complete the study once no time point remains planned.
- `action_terminate()` — Terminate the study early, requiring a reason.
- `action_view_timepoints()` — Open the time points of this study.

**Internal methods**

- `_compute_timepoint_statistics()` — Count time points in total and those completed.
- `_compute_display_name()` — Show the study reference with its product.
- `_assert_state()` — Raise unless every study is in one of the expected states.
- `_cron_notify_due_timepoints()` — Post a notice listing time points due or overdue.

---

## `ls.lab.stability_timepoint`

*Laboratory Stability Time Point*  
Source: `models/ls_lab_stability.py`  
Order: `study_id, sequence, interval_months, id`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `study_id` | Many2one | Stability Study | `ls.lab.stability_study` | required |
| `name` | Char | Time Point |  | required |
| `sequence` | Integer | Sequence |  |  |
| `interval_months` | Integer | Interval (months) |  | required |
| `window_days` | Integer | Window (days) |  |  |
| `scheduled_date` | Date | Scheduled Date | compute `_compute_scheduled_date` | computed |
| `state` | Selection | Status |  | required |
| `sample_id` | Many2one | Pull Sample | `ls.lab.sample` | readonly |
| `actual_pull_date` | Date | Actual Pull Date |  | readonly |
| `notes` | Text | Notes |  |  |
| `company_id` | Many2one | Company | related `study_id.company_id` |  |

**SQL constraints** (`models.Constraint`):

- `_interval_positive`: `CHECK (interval_months >= 0)` — The stability time point interval must be zero or positive.

**Public methods**

- `action_open_pull_wizard()` — Open the wizard that creates the pull sample (BRU-24).
- `action_mark_tested()` — Record that the pull sample has completed testing.
- `action_mark_completed()` — Close the time point.
- `action_mark_missed()` — Record a missed time point, requiring notes (BRU-27).

**Internal methods**

- `_compute_scheduled_date()` — Derive the due date from the study start date (BRU-25).
- `_compute_display_name()` — Show the study reference with the time point label.

---

## `ls.lab.coa`

*Certificate of Analysis*  
Source: `models/ls_lab_coa.py`  
Inherits: `ls.lab.signed.mixin`, `mail.thread`, `mail.activity.mixin`  
Order: `issue_date desc, name desc, version desc`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `name` | Char | Certificate Reference |  | required, readonly |
| `version` | Integer | Version |  | required, readonly |
| `state` | Selection | Status |  | required |
| `sample_id` | Many2one | Sample | `ls.lab.sample` | required |
| `product_id` | Many2one | Product | related `sample_id.product_id` |  |
| `lot_id` | Many2one | Lot / Serial Number | related `sample_id.lot_id` |  |
| `batch_reference` | Char | Batch Reference | related `sample_id.batch_reference` |  |
| `specification_id` | Many2one | Specification | related `sample_id.specification_id` |  |
| `overall_result` | Selection | Overall Result | related `sample_id.overall_result` |  |
| `conclusion` | Selection | Conclusion | compute `_compute_conclusion` | computed |
| `reportable_result_ids` | Many2many | Reported Results | `ls.lab.test_result` | computed |
| `customer_id` | Many2one | Customer | `res.partner` |  |
| `remarks` | Text | Remarks |  |  |
| `issued_by_id` | Many2one | Issued By | `res.users` | readonly |
| `issue_date` | Datetime | Issue Date |  | readonly |
| `cancel_reason` | Text | Cancellation Reason |  |  |
| `predecessor_id` | Many2one | Supersedes | `ls.lab.coa` | readonly |
| `successor_id` | Many2one | Superseded By | `ls.lab.coa` | readonly |
| `revision_reason` | Text | Revision Reason |  |  |
| `company_id` | Many2one | Company | related `sample_id.company_id` |  |

**SQL constraints** (`models.Constraint`):

- `_name_version_uniq`: `UNIQUE (name, version)` — A certificate version must be unique for a given certificate reference.

**Public methods**

- `create()` — Assign the certificate reference from the sequence.
- `write()` — Refuse changes to an issued certificate (BRU-23).
- `unlink()` — Refuse deletion of a certificate that has been issued.
- `action_issue()` — Issue the certificate from an approved sample (BRU-22).
- `action_cancel()` — Cancel a draft certificate, requiring a reason.
- `action_create_revision()` — Create a new version superseding an issued certificate.
- `action_open_issue_signature()` — Open the signature-intent wizard for certificate issue.

**Internal methods**

- `_compute_conclusion()` — Derive the certificate conclusion from the sample verdict.
- `_compute_reportable_result_ids()` — Select the results the specification marks as reportable.
- `_compute_display_name()` — Show the certificate reference, version and product.
- `_signature_target_action()` — Issue the certificate once signature intent has been recorded.

---

## `ls.lab.sample_cancel_wizard`

*Laboratory Sample Cancellation Wizard*  
Source: `wizard/ls_lab_sample_cancel_wizard.py`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `sample_id` | Many2one | Sample | `ls.lab.sample` | required, readonly |
| `sample_state` | Selection | Current Status | related `sample_id.state` | readonly |
| `reason` | Text | Cancellation Reason |  | required |

**Public methods**

- `action_confirm()` — Cancel the sample and record who cancelled it and why.

---

## `ls.lab.stability_pull_wizard`

*Laboratory Stability Pull Wizard*  
Source: `wizard/ls_lab_stability_pull_wizard.py`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `timepoint_id` | Many2one | Time Point | `ls.lab.stability_timepoint` | required, readonly |
| `study_id` | Many2one | Stability Study | related `timepoint_id.study_id` | readonly |
| `product_id` | Many2one | Product | related `timepoint_id.study_id.product_id` | readonly |
| `scheduled_date` | Date | Scheduled Date | related `timepoint_id.scheduled_date` | readonly |
| `specification_id` | Many2one | Specification | `ls.lab.specification` | required |
| `storage_condition_id` | Many2one | Storage Condition | `ls.lab.storage_condition` |  |
| `pull_date` | Date | Actual Pull Date |  | required |
| `quantity` | Float | Quantity |  |  |
| `uom_id` | Many2one | Unit of Measure | `uom.uom` |  |
| `due_date` | Date | Testing Due Date |  |  |

**Public methods**

- `action_confirm()` — Create the pull sample and link it to the time point.

**Internal methods**

- `_onchange_timepoint_id()` — Default the specification and storage condition from the study.

---

## `ls.lab.signature_wizard`

*Laboratory Signature Intent Wizard*  
Source: `wizard/ls_lab_signature_wizard.py`  

| Field | Type | Label | Target / Detail | Flags |
|-------|------|-------|-----------------|-------|
| `res_model` | Char | Target Model |  | required, readonly |
| `res_id` | Integer | Target Record |  | required, readonly |
| `record_label` | Char | Record | compute `_compute_record_label` | readonly, computed |
| `meaning` | Selection | Meaning Of Signature |  | required |
| `limitation_notice` | Text | Limitation |  | readonly |
| `acknowledged` | Boolean | I confirm this action |  |  |

**Public methods**

- `action_confirm()` — Record the signature intent and run the authorised action.

**Internal methods**

- `_default_limitation_notice()` — Return the limitation text shown on the wizard.
- `_compute_record_label()` — Show the display name of the record being signed.

---
