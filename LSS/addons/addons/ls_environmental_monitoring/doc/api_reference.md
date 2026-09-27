# API Reference — ls_environmental_monitoring

Generated directly from the module source by parsing the abstract syntax
tree, so it cannot drift from the code it documents.

---

## Model index

| Model | Kind | Description |
|---|---|---|
| `ls.env.area` | Persistent | Environmental Monitoring Area |
| `ls.env.excursion` | Persistent | Environmental Monitoring Excursion |
| `ls.env.excursion.close.wizard` | Transient | Close Environmental Monitoring Excursion |
| `ls.env.grade` | Persistent | Environmental Monitoring Cleanroom Grade |
| `ls.env.limit` | Persistent | Environmental Monitoring Limit |
| `ls.env.method` | Persistent | Environmental Monitoring Method |
| `ls.env.parameter` | Persistent | Environmental Monitoring Parameter |
| `ls.env.plan` | Persistent | Environmental Monitoring Plan |
| `ls.env.plan.line` | Persistent | Environmental Monitoring Plan Line |
| `ls.env.result` | Persistent | Environmental Monitoring Result |
| `ls.env.result.amend.wizard` | Transient | Amend Environmental Monitoring Result |
| `ls.env.sample` | Persistent | Environmental Monitoring Sample |
| `ls.env.sample.cancel.wizard` | Transient | Cancel Environmental Monitoring Sample |
| `ls.env.sampling_point` | Persistent | Environmental Monitoring Sampling Point |
| `ls.env.schedule.wizard` | Transient | Generate Scheduled Environmental Monitoring Samples |
| `ls.env.trend` | Persistent | Environmental Monitoring Trend Analysis |
| `ls.env.trend.line` | Persistent | Environmental Monitoring Trend Line |
| `ls.env.trend.wizard` | Transient | Run Environmental Monitoring Trend Analysis |

---

## `ls.env.area`

- **Description:** Environmental Monitoring Area
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_area.py`

### Fields (14)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `complete_name` | Char |  |  |
| `parent_id` | Many2one |  | `ls.env.area` |
| `parent_path` | Char |  |  |
| `child_ids` | One2many |  | `ls.env.area` |
| `grade_id` | Many2one |  | `ls.env.grade` |
| `responsible_id` | Many2one |  | `res.users` |
| `description` | Text |  |  |
| `active` | Boolean |  |  |
| `company_id` | Many2one | yes | `res.company` |
| `sampling_point_ids` | One2many |  | `ls.env.sampling_point` |
| `sampling_point_count` | Integer |  |  |
| `open_excursion_count` | Integer |  |  |

### Database constraints (1)

- `_code_company_unique`: `UNIQUE(code, company_id)`

### Public methods (2)

- `action_view_sampling_points()` — Open the sampling points of this area.
- `action_view_open_excursions()` — Open the excursions of this area that are still in progress.

### Internal methods (6)

- `_compute_complete_name()` — Build the slash-separated path from the root area downwards.
- `_compute_sampling_point_count()` — Count the sampling points defined directly in this area.
- `_compute_open_excursion_count()` — Count excursions in this area that are not closed or cancelled.
- `_check_area_hierarchy()` — Reject cycles in the area hierarchy.
- `_check_parent_company()` — Reject a parent area belonging to a different company.
- `_compute_display_name()` — Display the full hierarchical path.

---

## `ls.env.excursion`

- **Description:** Environmental Monitoring Excursion
- **Kind:** Persistent
- **Inherits:** `mail.thread`, `mail.activity.mixin`
- **Source:** `models/ls_env_excursion.py`

### Fields (22)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `sample_id` | Many2one | yes | `ls.env.sample` |
| `result_ids` | One2many |  | `ls.env.result` |
| `sampling_point_id` | Many2one |  | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `batch_reference` | Char |  |  |
| `excursion_type` | Selection | yes |  |
| `severity` | Selection |  |  |
| `detection_date` | Datetime | yes |  |
| `state` | Selection | yes |  |
| `owner_id` | Many2one |  | `res.users` |
| `immediate_actions` | Text |  |  |
| `impact_assessment` | Text |  |  |
| `product_impact` | Selection |  |  |
| `investigation_required` | Boolean |  |  |
| `root_cause` | Text |  |  |
| `corrective_actions` | Text |  |  |
| `external_reference` | Char |  |  |
| `closure_justification` | Text |  |  |
| `closed_by_id` | Many2one |  | `res.users` |
| `closure_datetime` | Datetime |  |  |
| `company_id` | Many2one |  | `res.company` |

### Database constraints (1)

- `_name_company_unique`: `UNIQUE(name, company_id)`

### Public methods (11)

- `create()` — Assign the excursion reference from the configured sequence.
- `action_start_assessment()` — Move the excursion into impact assessment.
- `action_start_investigation()` — Move the excursion into investigation.
- `action_propose_closure()` — Move the excursion to pending closure.
- `action_open_closure_wizard()` — Open the wizard that records the closure justification.
- `close()` — Close the excursion with a recorded justification.
- `action_reopen_investigation()` — Return an excursion pending closure to investigation.
- `action_cancel()` — Cancel an excursion raised in error.
- `action_create_external_record()` — Extension point for modules that manage corrective action.
- `write()` — Prevent changes to an excursion once it is closed or cancelled.
- `unlink()` — Prevent deletion of excursions.

### Internal methods (2)

- `_prepare_from_results()` — Build the values for an excursion covering ``results``.
- `_check_transition()` — Raise unless every record may move to ``target_state``.

---

## `ls.env.excursion.close.wizard`

- **Description:** Close Environmental Monitoring Excursion
- **Kind:** Transient (wizard)
- **Inherits:** -
- **Source:** `wizards/ls_env_excursion_close_wizard.py`

### Fields (2)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `excursion_id` | Many2one | yes | `ls.env.excursion` |
| `justification` | Text | yes |  |

### Public methods (1)

- `action_close()` — Close the excursion with the supplied justification.

---

## `ls.env.grade`

- **Description:** Environmental Monitoring Cleanroom Grade
- **Kind:** Persistent
- **Inherits:** -
- **Source:** `models/ls_env_grade.py`

### Fields (9)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `sequence` | Integer |  |  |
| `description` | Text |  |  |
| `reference_document` | Char |  |  |
| `active` | Boolean |  |  |
| `company_id` | Many2one | yes | `res.company` |
| `area_ids` | One2many |  | `ls.env.area` |
| `area_count` | Integer |  |  |

### Database constraints (1)

- `_code_company_unique`: `UNIQUE(code, company_id)`

### Internal methods (2)

- `_compute_area_count()` — Count the monitored areas classified at this grade.
- `_compute_display_name()` — Show the code alongside the grade label.

---

## `ls.env.limit`

- **Description:** Environmental Monitoring Limit
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_limit.py`

### Fields (22)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char |  |  |
| `sampling_point_id` | Many2one | yes | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `parameter_id` | Many2one | yes | `ls.env.parameter` |
| `occupancy_state` | Selection | yes |  |
| `direction` | Selection | yes |  |
| `alert_value` | Float |  |  |
| `action_value` | Float |  |  |
| `spec_value` | Float |  |  |
| `alert_set` | Boolean |  |  |
| `action_set` | Boolean |  |  |
| `spec_set` | Boolean |  |  |
| `escalate_alert` | Boolean |  |  |
| `justification` | Text |  |  |
| `source_reference` | Char |  |  |
| `version` | Integer |  |  |
| `state` | Selection | yes |  |
| `effective_date` | Date |  |  |
| `superseded_date` | Date |  |  |
| `approved_by_id` | Many2one |  | `res.users` |
| `superseded_by_id` | Many2one |  | `ls.env.limit` |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (4)

- `_alert_value_positive`: `CHECK(alert_value >= 0)`
- `_action_value_positive`: `CHECK(action_value >= 0)`
- `_spec_value_positive`: `CHECK(spec_value >= 0)`
- `_version_positive`: `CHECK(version > 0)`

### Public methods (5)

- `action_approve()` — Approve the limit and supersede the limit it replaces.
- `action_create_revision()` — Create a draft copy of an approved limit for revision.
- `get_thresholds()` — Return the thresholds that are enabled on this limit.
- `write()` — Prevent the thresholds of an approved limit from being altered.
- `unlink()` — Prevent deletion of a limit that has been approved.

### Internal methods (5)

- `_compute_name()` — Build a stable human-readable reference for the limit.
- `_check_at_least_one_threshold()` — Reject a limit that defines no threshold at all.
- `_check_threshold_ordering()` — Reject thresholds ordered inconsistently with the bound direction.
- `_check_single_approved_limit()` — Reject a second approved limit for the same combination.
- `_check_company_consistency()` — Reject references to records of a different company.

---

## `ls.env.method`

- **Description:** Environmental Monitoring Method
- **Kind:** Persistent
- **Inherits:** -
- **Source:** `models/ls_env_method.py`

### Fields (12)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `parameter_id` | Many2one | yes | `ls.env.parameter` |
| `media_type` | Char |  |  |
| `incubation_conditions` | Text |  |  |
| `exposure_duration_minutes` | Integer |  |  |
| `sample_volume` | Float |  |  |
| `sample_volume_uom_label` | Char |  |  |
| `reference_document` | Char |  |  |
| `description` | Text |  |  |
| `active` | Boolean |  |  |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (3)

- `_code_company_unique`: `UNIQUE(code, company_id)`
- `_exposure_duration_positive`: `CHECK(exposure_duration_minutes >= 0)`
- `_sample_volume_positive`: `CHECK(sample_volume >= 0)`

### Internal methods (2)

- `_check_parameter_company()` — Reject a parameter belonging to a different company.
- `_compute_display_name()` — Show the code alongside the method name.

---

## `ls.env.parameter`

- **Description:** Environmental Monitoring Parameter
- **Kind:** Persistent
- **Inherits:** -
- **Source:** `models/ls_env_parameter.py`

### Fields (11)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `sequence` | Integer |  |  |
| `parameter_type` | Selection | yes |  |
| `result_type` | Selection | yes |  |
| `uom_label` | Char |  |  |
| `decimal_precision` | Integer |  |  |
| `incubation_required` | Boolean |  |  |
| `description` | Text |  |  |
| `active` | Boolean |  |  |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (2)

- `_code_company_unique`: `UNIQUE(code, company_id)`
- `_decimal_precision_positive`: `CHECK(decimal_precision >= 0 AND decimal_precision <= 10)`

### Public methods (1)

- `is_quantitative()` — Return whether this parameter records a numeric value.

### Internal methods (1)

- `_compute_display_name()` — Show the code alongside the parameter name.

---

## `ls.env.plan`

- **Description:** Environmental Monitoring Plan
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_plan.py`

### Fields (14)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `version` | Integer |  |  |
| `state` | Selection | yes |  |
| `area_id` | Many2one |  | `ls.env.area` |
| `effective_date` | Date |  |  |
| `review_date` | Date |  |  |
| `superseded_date` | Date |  |  |
| `approved_by_id` | Many2one |  | `res.users` |
| `superseded_by_id` | Many2one |  | `ls.env.plan` |
| `rationale` | Text |  |  |
| `line_ids` | One2many |  | `ls.env.plan.line` |
| `line_count` | Integer |  |  |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (2)

- `_code_version_company_unique`: `UNIQUE(code, version, company_id)`
- `_version_positive`: `CHECK(version > 0)`

### Public methods (4)

- `action_approve()` — Approve the plan and supersede the previous version.
- `action_cancel()` — Cancel a plan that is not in force.
- `action_create_revision()` — Create a draft copy of an approved plan.
- `unlink()` — Prevent deletion of a plan that has been approved.

### Internal methods (3)

- `_compute_line_count()` — Count the lines of each plan.
- `_check_area_company()` — Reject a primary area belonging to a different company.
- `_compute_display_name()` — Show the code and version alongside the plan name.

---

## `ls.env.plan.line`

- **Description:** Environmental Monitoring Plan Line
- **Kind:** Persistent
- **Inherits:** -
- **Source:** `models/ls_env_plan_line.py`

### Fields (14)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `plan_id` | Many2one | yes | `ls.env.plan` |
| `plan_state` | Selection |  |  |
| `sampling_point_id` | Many2one | yes | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `parameter_id` | Many2one | yes | `ls.env.parameter` |
| `method_id` | Many2one |  | `ls.env.method` |
| `occupancy_state` | Selection | yes |  |
| `frequency_interval` | Integer | yes |  |
| `frequency_unit` | Selection | yes |  |
| `start_date` | Date |  |  |
| `next_due_date` | Date |  |  |
| `responsible_id` | Many2one |  | `res.users` |
| `notes` | Text |  |  |
| `company_id` | Many2one |  | `res.company` |

### Database constraints (2)

- `_frequency_interval_positive`: `CHECK(frequency_interval > 0)`
- `_point_parameter_occupancy_unique`: `UNIQUE(plan_id, sampling_point_id, parameter_id, occupancy_state)`

### Internal methods (7)

- `_check_method_parameter()` — Reject a method that measures a different parameter.
- `_check_company_consistency()` — Reject references to records of a different company.
- `_interval_delta()` — Return the interval between two occurrences as a relative delta.
- `_first_due_date()` — Return the date on which this requirement first falls due.
- `_reset_next_due_date()` — Initialise the next due date on lines that do not yet have one.
- `_due_dates_until()` — Return the outstanding due dates up to and including ``end_date``.
- `_compute_display_name()` — Show the sampling point and parameter together.

---

## `ls.env.result`

- **Description:** Environmental Monitoring Result
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_result.py`

### Fields (34)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `sample_id` | Many2one | yes | `ls.env.sample` |
| `sample_state` | Selection |  |  |
| `sampling_point_id` | Many2one |  | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `occupancy_state` | Selection |  |  |
| `collection_datetime` | Datetime |  |  |
| `parameter_id` | Many2one | yes | `ls.env.parameter` |
| `result_type` | Selection |  |  |
| `method_id` | Many2one |  | `ls.env.method` |
| `value_numeric` | Float |  |  |
| `value_set` | Boolean |  |  |
| `value_qualitative` | Selection |  |  |
| `uom_label` | Char |  |  |
| `microbial_identification` | Char |  |  |
| `limit_id` | Many2one |  | `ls.env.limit` |
| `applied_direction` | Char |  |  |
| `applied_alert_value` | Float |  |  |
| `applied_action_value` | Float |  |  |
| `applied_spec_value` | Float |  |  |
| `applied_alert_set` | Boolean |  |  |
| `applied_action_set` | Boolean |  |  |
| `applied_spec_set` | Boolean |  |  |
| `evaluation` | Selection |  |  |
| `evaluation_datetime` | Datetime |  |  |
| `is_breach` | Boolean |  |  |
| `is_amended` | Boolean |  |  |
| `original_value_numeric` | Float |  |  |
| `original_value_qualitative` | Selection |  |  |
| `amendment_reason` | Text |  |  |
| `amended_by_id` | Many2one |  | `res.users` |
| `amendment_datetime` | Datetime |  |  |
| `excursion_id` | Many2one |  | `ls.env.excursion` |
| `notes` | Text |  |  |
| `company_id` | Many2one |  | `res.company` |

### Database constraints (1)

- `_sample_parameter_unique`: `UNIQUE(sample_id, parameter_id)`

### Public methods (6)

- `has_value()` — Return whether a value has been recorded on this result.
- `action_evaluate()` — Evaluate each result against the limits currently approved.
- `action_amend()` — Open the amendment wizard for a result on an approved sample.
- `amend_value()` — Amend an approved result, retaining the original value.
- `write()` — Freeze the reported value once the parent sample is approved.
- `unlink()` — Prevent deletion of a result once its sample has been collected.

### Internal methods (8)

- `_compute_is_breach()` — Flag results whose outcome breached a configured threshold.
- `_check_method_parameter()` — Reject a method that measures a different parameter.
- `_check_value_not_negative()` — Reject a negative count for a parameter that counts occurrences.
- `_snapshot_limit()` — Copy the thresholds of ``limit`` onto the result.
- `_find_applicable_limit()` — Return the approved limit that applies to this result.
- `_requires_excursion()` — Return whether this result must open a formal excursion.
- `_raise_excursions_if_required()` — Create excursion records for the breaches on these results.
- `_compute_display_name()` — Show the sample reference and the parameter measured.

---

## `ls.env.result.amend.wizard`

- **Description:** Amend Environmental Monitoring Result
- **Kind:** Transient (wizard)
- **Inherits:** -
- **Source:** `wizards/ls_env_result_amend_wizard.py`

### Fields (7)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `result_id` | Many2one | yes | `ls.env.result` |
| `result_type` | Selection |  |  |
| `current_value_numeric` | Float |  |  |
| `current_value_qualitative` | Selection |  |  |
| `new_value_numeric` | Float |  |  |
| `new_value_qualitative` | Selection |  |  |
| `reason` | Text | yes |  |

### Public methods (1)

- `action_amend()` — Apply the amendment to the result.

### Internal methods (1)

- `_onchange_result_id()` — Pre-fill the corrected value with the value currently recorded.

---

## `ls.env.sample`

- **Description:** Environmental Monitoring Sample
- **Kind:** Persistent
- **Inherits:** `mail.thread`, `mail.activity.mixin`
- **Source:** `models/ls_env_sample.py`

### Fields (28)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `sampling_point_id` | Many2one | yes | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `grade_id` | Many2one |  | `ls.env.grade` |
| `plan_id` | Many2one |  | `ls.env.plan` |
| `is_unscheduled` | Boolean |  |  |
| `occupancy_state` | Selection | yes |  |
| `scheduled_date` | Date | yes |  |
| `collection_datetime` | Datetime |  |  |
| `collected_by_id` | Many2one |  | `res.users` |
| `analysis_start_datetime` | Datetime |  |  |
| `results_entered_by_id` | Many2one |  | `res.users` |
| `results_entered_datetime` | Datetime |  |  |
| `reviewed_by_id` | Many2one |  | `res.users` |
| `review_datetime` | Datetime |  |  |
| `approved_by_id` | Many2one |  | `res.users` |
| `approval_datetime` | Datetime |  |  |
| `cancellation_reason` | Text |  |  |
| `state` | Selection | yes |  |
| `result_ids` | One2many |  | `ls.env.result` |
| `result_count` | Integer |  |  |
| `overall_evaluation` | Selection |  |  |
| `excursion_ids` | One2many |  | `ls.env.excursion` |
| `excursion_count` | Integer |  |  |
| `batch_reference` | Char |  |  |
| `is_overdue` | Boolean |  |  |
| `notes` | Text |  |  |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (1)

- `_name_company_unique`: `UNIQUE(name, company_id)`

### Public methods (15)

- `create()` — Assign the sample reference from the configured sequence.
- `write()` — Prevent changes to a sample once it is approved or cancelled.
- `unlink()` — Restrict deletion to samples that were never collected.
- `action_schedule()` — Move a draft sample into the scheduled state.
- `action_collect()` — Record collection of the sample by the current user.
- `action_start_analysis()` — Record the start of analysis or incubation.
- `action_enter_results()` — Evaluate the recorded values and mark the results as entered.
- `action_review()` — Record technical review of the results.
- `action_approve()` — Approve the sample and raise excursions for any breach.
- `action_cancel()` — Cancel the sample, recording the reason supplied in the context.
- `action_reopen_analysis()` — Return a reviewed or submitted sample to analysis for correction.
- `generate_from_plans()` — Create the samples due under ``plans`` up to ``date_to``.
- `cron_notify_overdue_samples()` — Notify the responsible users of samples that are past due.
- `action_open_cancel_wizard()` — Open the wizard that records the cancellation reason.
- `action_view_excursions()` — Open the excursions raised from this sample.

### Internal methods (11)

- `_compute_is_unscheduled()` — Flag samples that did not originate from an approved plan.
- `_compute_result_count()` — Count the results attached to each sample.
- `_compute_excursion_count()` — Count the excursions raised from each sample.
- `_compute_overall_evaluation()` — Roll the result outcomes up to the sample.
- `_compute_is_overdue()` — Flag samples past their scheduled date and not yet collected.
- `_search_is_overdue()` — Translate a search on ``is_overdue`` into a stored-field domain.
- `_check_company_consistency()` — Reject a sampling point belonging to a different company.
- `_check_collection_not_in_future()` — Reject a collection timestamp in the future.
- `_check_manager_role()` — Raise unless the current user holds the manager role.
- `_check_transition()` — Raise unless every record may move to ``target_state``.
- `_get_or_create_scheduled_sample()` — Return a new sample for ``line`` on ``due_date``, or nothing.

---

## `ls.env.sample.cancel.wizard`

- **Description:** Cancel Environmental Monitoring Sample
- **Kind:** Transient (wizard)
- **Inherits:** -
- **Source:** `wizards/ls_env_sample_cancel_wizard.py`

### Fields (2)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `sample_id` | Many2one | yes | `ls.env.sample` |
| `reason` | Text | yes |  |

### Public methods (1)

- `action_cancel()` — Cancel the sample, passing the reason through the context.

---

## `ls.env.sampling_point`

- **Description:** Environmental Monitoring Sampling Point
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_sampling_point.py`

### Fields (14)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `code` | Char | yes |  |
| `sequence` | Integer |  |  |
| `area_id` | Many2one | yes | `ls.env.area` |
| `grade_id` | Many2one |  | `ls.env.grade` |
| `position_description` | Text |  |  |
| `selection_rationale` | Text |  |  |
| `is_critical` | Boolean |  |  |
| `responsible_id` | Many2one |  | `res.users` |
| `active` | Boolean |  |  |
| `company_id` | Many2one | yes | `res.company` |
| `limit_ids` | One2many |  | `ls.env.limit` |
| `approved_limit_count` | Integer |  |  |
| `sample_ids` | One2many |  | `ls.env.sample` |

### Database constraints (1)

- `_code_company_unique`: `UNIQUE(code, company_id)`

### Public methods (2)

- `find_approved_limit()` — Return the approved limit applicable to a measurement.
- `action_view_limits()` — Open the limits configured for this sampling point.

### Internal methods (4)

- `_compute_grade_id()` — Inherit the grade of the area, allowing a manual override.
- `_compute_approved_limit_count()` — Count the currently approved limits of each point.
- `_check_area_company()` — Reject an area belonging to a different company.
- `_compute_display_name()` — Show the code alongside the sampling point name.

---

## `ls.env.schedule.wizard`

- **Description:** Generate Scheduled Environmental Monitoring Samples
- **Kind:** Transient (wizard)
- **Inherits:** -
- **Source:** `wizards/ls_env_schedule_wizard.py`

### Fields (4)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `date_to` | Date | yes |  |
| `plan_ids` | Many2many |  | `ls.env.plan` |
| `company_id` | Many2one | yes | `res.company` |
| `generated_count` | Integer |  |  |

### Public methods (2)

- `action_generate()` — Create the outstanding samples and report how many were created.
- `cron_generate_scheduled_samples()` — Entry point for the scheduled job.

### Internal methods (1)

- `_plans()` — Return the approved plans in scope for this run.

---

## `ls.env.trend`

- **Description:** Environmental Monitoring Trend Analysis
- **Kind:** Persistent
- **Inherits:** `mail.thread`
- **Source:** `models/ls_env_trend.py`

### Fields (16)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `date_from` | Date | yes |  |
| `date_to` | Date | yes |  |
| `area_ids` | Many2many |  | `ls.env.area` |
| `sampling_point_ids` | Many2many |  | `ls.env.sampling_point` |
| `parameter_ids` | Many2many |  | `ls.env.parameter` |
| `change_threshold` | Float |  |  |
| `state` | Selection | yes |  |
| `line_ids` | One2many |  | `ls.env.trend.line` |
| `line_count` | Integer |  |  |
| `computed_by_id` | Many2one |  | `res.users` |
| `computed_datetime` | Datetime |  |  |
| `reviewed_by_id` | Many2one |  | `res.users` |
| `review_datetime` | Datetime |  |  |
| `conclusion` | Text |  |  |
| `company_id` | Many2one | yes | `res.company` |

### Database constraints (1)

- `_change_threshold_positive`: `CHECK(change_threshold >= 0)`

### Public methods (2)

- `action_compute()` — Recompute the analysis, replacing any previously produced lines.
- `action_review()` — Record review of the analysis and its conclusion.

### Internal methods (4)

- `_compute_line_count()` — Count the lines produced by each analysis.
- `_check_period()` — Reject a period whose end precedes its start.
- `_result_domain()` — Build the domain selecting the results in scope.
- `_prepare_line()` — Build the values of one trend line.

---

## `ls.env.trend.line`

- **Description:** Environmental Monitoring Trend Line
- **Kind:** Persistent
- **Inherits:** -
- **Source:** `models/ls_env_trend_line.py`

### Fields (22)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `trend_id` | Many2one | yes | `ls.env.trend` |
| `sampling_point_id` | Many2one | yes | `ls.env.sampling_point` |
| `area_id` | Many2one |  | `ls.env.area` |
| `parameter_id` | Many2one | yes | `ls.env.parameter` |
| `result_count` | Integer |  |  |
| `numeric_count` | Integer |  |  |
| `alert_count` | Integer |  |  |
| `action_count` | Integer |  |  |
| `spec_count` | Integer |  |  |
| `exceedance_ratio` | Float |  |  |
| `value_min` | Float |  |  |
| `value_min_available` | Boolean |  |  |
| `value_max` | Float |  |  |
| `value_max_available` | Boolean |  |  |
| `value_mean` | Float |  |  |
| `value_mean_available` | Boolean |  |  |
| `value_median` | Float |  |  |
| `value_median_available` | Boolean |  |  |
| `value_stdev` | Float |  |  |
| `value_stdev_available` | Boolean |  |  |
| `direction` | Selection |  |  |
| `company_id` | Many2one |  | `res.company` |

### Database constraints (2)

- `_trend_point_parameter_unique`: `UNIQUE(trend_id, sampling_point_id, parameter_id)`
- `_counts_not_negative`: `CHECK(result_count >= 0 AND alert_count >= 0 AND action_count >= 0 AND spec_count >= 0)`

---

## `ls.env.trend.wizard`

- **Description:** Run Environmental Monitoring Trend Analysis
- **Kind:** Transient (wizard)
- **Inherits:** -
- **Source:** `wizards/ls_env_trend_wizard.py`

### Fields (7)

| Field | Type | Required | Relates to |
|---|---|---|---|
| `name` | Char | yes |  |
| `date_from` | Date | yes |  |
| `date_to` | Date | yes |  |
| `area_ids` | Many2many |  | `ls.env.area` |
| `sampling_point_ids` | Many2many |  | `ls.env.sampling_point` |
| `parameter_ids` | Many2many |  | `ls.env.parameter` |
| `change_threshold` | Float |  |  |

### Public methods (1)

- `action_run()` — Create the analysis record, compute it and open the result.

---
