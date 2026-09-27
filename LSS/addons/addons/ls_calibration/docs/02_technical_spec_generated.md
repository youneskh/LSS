# ls_calibration — Technical Specification

Phases 4 and 5 of the development framework.

This inventory is generated directly from the module source by AST
analysis (`docs/generate_inventory.py`), not maintained by hand.
Counts and names therefore match the shipped code exactly.

---

## 4.1 Model inventory

| Model | Class | Fields | Constraints | Computes | Onchanges | Actions |
|---|---|---|---|---|---|---|
| `ls.calibration.instrument.category` | LsCalibrationInstrumentCategory | 14 | 3 | 3 | 0 | 1 |
| `ls.calibration.instrument` | LsCalibrationInstrument | 46 | 5 | 6 | 1 | 10 |
| `ls.calibration.point` | LsCalibrationPoint | 13 | 4 | 2 | 0 | 0 |
| `ls.calibration.standard` | LsCalibrationStandard | 20 | 1 | 3 | 0 | 0 |
| `ls.calibration.plan` | LsCalibrationPlan | 23 | 4 | 3 | 2 | 5 |
| `ls.calibration.record` | LsCalibrationRecord | 38 | 6 | 4 | 2 | 10 |
| `ls.calibration.reading` | LsCalibrationReading | 18 | 2 | 2 | 2 | 0 |
| `ls.calibration.certificate` | LsCalibrationCertificate | 15 | 4 | 1 | 0 | 1 |
| `ls.calibration.oot` | LsCalibrationOot | 21 | 2 | 1 | 0 | 4 |
| `ls.calibration.plan.generate` | LsCalibrationPlanGenerate | 6 | 0 | 0 | 0 | 1 |
| `ls.calibration.record.reject` | LsCalibrationRecordReject | 3 | 0 | 0 | 0 | 1 |
| **Total** | **11** | **217** | **31** | | | |

### `ls.calibration.instrument.category`

*Calibration Instrument Category*

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `complete_name` | Char |  | yes | yes |  |
| `code` | Char | yes |  |  |  |
| `parent_id` | Many2one |  |  |  |  |
| `parent_path` | Char |  |  |  |  |
| `child_ids` | One2many |  |  |  |  |
| `default_interval_value` | Integer |  |  |  |  |
| `default_interval_uom` | Selection |  |  |  |  |
| `default_criticality` | Selection |  |  |  |  |
| `description` | Text |  |  |  |  |
| `instrument_ids` | One2many |  |  |  |  |
| `instrument_count` | Integer |  | yes |  |  |
| `company_id` | Many2one | yes |  |  |  |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_code_company_uniq` — `UNIQUE(code, company_id)`
- SQL: `_default_interval_positive` — `CHECK(default_interval_value > 0)`
- Python: `_check_category_recursion`

**Public actions**: `action_open_instruments`


### `ls.calibration.instrument`

*Calibration Instrument*

Inherits: `mail.thread`, `mail.activity.mixin`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `code` | Char | yes |  |  |  |
| `category_id` | Many2one | yes |  |  |  |
| `manufacturer` | Char |  |  |  |  |
| `model_reference` | Char |  |  |  |  |
| `serial_number` | Char |  |  |  |  |
| `asset_tag` | Char |  |  |  |  |
| `location` | Char |  |  |  |  |
| `responsible_user_id` | Many2one |  |  |  |  |
| `partner_id` | Many2one |  |  |  |  |
| `unit_label` | Char |  |  |  |  |
| `range_min` | Float |  |  |  |  |
| `range_max` | Float |  |  |  |  |
| `span` | Float |  | yes | yes |  |
| `resolution` | Float |  |  |  |  |
| `accuracy_class` | Char |  |  |  |  |
| `criticality` | Selection | yes |  |  |  |
| `is_gxp_critical` | Boolean |  | yes | yes |  |
| `requires_oot_assessment` | Boolean |  |  |  |  |
| `calibration_interval_value` | Integer | yes |  |  |  |
| `calibration_interval_uom` | Selection | yes |  |  |  |
| `due_soon_threshold_days` | Integer | yes |  |  |  |
| `last_calibration_date` | Date |  | yes | yes |  |
| `last_record_id` | Many2one |  | yes | yes |  |
| `next_due_date` | Date |  | yes | yes |  |
| `days_to_due` | Integer |  | yes |  |  |
| `calibration_status` | Selection |  | yes | yes |  |
| `state` | Selection | yes |  |  |  |
| `commissioning_date` | Date |  |  |  |  |
| `retirement_date` | Date |  |  |  |  |
| `quarantine_reason` | Text |  |  |  |  |
| `point_ids` | One2many |  |  |  |  |
| `plan_ids` | One2many |  |  |  |  |
| `record_ids` | One2many |  |  |  |  |
| `certificate_ids` | One2many |  |  |  |  |
| `oot_ids` | One2many |  |  |  |  |
| `point_count` | Integer |  | yes |  |  |
| `plan_count` | Integer |  | yes |  |  |
| `record_count` | Integer |  | yes |  |  |
| `certificate_count` | Integer |  | yes |  |  |
| `oot_count` | Integer |  | yes |  |  |
| `open_oot_count` | Integer |  | yes |  |  |
| `external_equipment_reference` | Char |  |  |  |  |
| `description` | Text |  |  |  |  |
| `company_id` | Many2one | yes |  |  |  |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_code_company_uniq` — `UNIQUE(code, company_id)`
- SQL: `_interval_positive` — `CHECK(calibration_interval_value > 0)`
- SQL: `_due_soon_threshold_non_negative` — `CHECK(due_soon_threshold_days >= 0)`
- Python: `_check_range`
- Python: `_check_lifecycle_dates`

**Public actions**: `action_place_in_service`, `action_quarantine`, `action_take_out_of_service`, `action_retire`, `action_reset_to_draft`, `action_open_points`, `action_open_plans`, `action_open_records`, `action_open_certificates`, `action_open_oot`

**Scheduled methods**: `_cron_refresh_calibration_status`


### `ls.calibration.point`

*Calibration Point*

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `sequence` | Integer |  |  |  |  |
| `instrument_id` | Many2one | yes |  |  |  |
| `nominal_value` | Float | yes |  |  |  |
| `unit_label` | Char |  |  |  | yes |
| `tolerance_type` | Selection | yes |  |  |  |
| `tolerance_value` | Float | yes |  |  |  |
| `tolerance_absolute` | Float |  | yes | yes |  |
| `lower_limit` | Float |  | yes | yes |  |
| `upper_limit` | Float |  | yes | yes |  |
| `reading_ids` | One2many |  |  |  |  |
| `company_id` | Many2one |  |  | yes | yes |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_tolerance_non_negative` — `CHECK(tolerance_value >= 0)`
- SQL: `_point_name_instrument_uniq` — `UNIQUE(instrument_id, name)`
- Python: `_check_nominal_within_range`
- Python: `_check_span_available_for_percent_of_span`


### `ls.calibration.standard`

*Calibration Reference Standard*

Inherits: `mail.thread`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `code` | Char | yes |  |  |  |
| `manufacturer` | Char |  |  |  |  |
| `model_reference` | Char |  |  |  |  |
| `serial_number` | Char |  |  |  |  |
| `description` | Text |  |  |  |  |
| `traceability_reference` | Char |  |  |  |  |
| `issuing_body` | Char |  |  |  |  |
| `accreditation_reference` | Char |  |  |  |  |
| `certificate_date` | Date |  |  |  |  |
| `valid_until` | Date | yes |  |  |  |
| `is_valid` | Boolean |  | yes | yes |  |
| `certificate_document` | Binary |  |  |  |  |
| `certificate_filename` | Char |  |  |  |  |
| `uncertainty` | Float |  |  |  |  |
| `uncertainty_unit` | Char |  |  |  |  |
| `record_ids` | Many2many |  |  |  |  |
| `record_count` | Integer |  | yes |  |  |
| `company_id` | Many2one | yes |  |  |  |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_code_company_uniq` — `UNIQUE(code, company_id)`

**Scheduled methods**: `_cron_refresh_validity`


### `ls.calibration.plan`

*Calibration Plan*

Inherits: `mail.thread`, `mail.activity.mixin`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `instrument_id` | Many2one | yes |  |  |  |
| `instrument_code` | Char |  |  | yes | yes |
| `category_id` | Many2one |  |  | yes | yes |
| `interval_value` | Integer | yes |  |  |  |
| `interval_uom` | Selection | yes |  |  |  |
| `start_date` | Date | yes |  |  |  |
| `end_date` | Date |  |  |  |  |
| `next_generation_date` | Date |  | yes | yes |  |
| `provider_type` | Selection | yes |  |  |  |
| `service_provider_id` | Many2one |  |  |  |  |
| `responsible_user_id` | Many2one | yes |  |  |  |
| `procedure_reference` | Char |  |  |  |  |
| `method_description` | Text |  |  |  |  |
| `state` | Selection | yes |  |  |  |
| `approved_by_user_id` | Many2one |  |  |  |  |
| `approved_date` | Datetime |  |  |  |  |
| `suspension_reason` | Text |  |  |  |  |
| `closure_reason` | Text |  |  |  |  |
| `record_ids` | One2many |  |  |  |  |
| `record_count` | Integer |  | yes |  |  |
| `company_id` | Many2one |  |  | yes | yes |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_interval_positive` — `CHECK(interval_value > 0)`
- Python: `_check_effective_dates`
- Python: `_check_external_provider`
- Python: `_check_single_active_plan`

**Public actions**: `action_approve`, `action_suspend`, `action_resume`, `action_close`, `action_open_records`


### `ls.calibration.record`

*Calibration Record*

Inherits: `mail.thread`, `mail.activity.mixin`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `instrument_id` | Many2one | yes |  |  |  |
| `instrument_code` | Char |  |  | yes | yes |
| `category_id` | Many2one |  |  | yes | yes |
| `criticality` | Selection |  |  | yes | yes |
| `plan_id` | Many2one |  |  |  |  |
| `scheduled_date` | Date | yes |  |  |  |
| `performed_date` | Date |  |  |  |  |
| `provider_type` | Selection | yes |  |  |  |
| `performed_by_user_id` | Many2one |  |  |  |  |
| `performed_by_name` | Char |  |  |  |  |
| `service_provider_id` | Many2one |  |  |  |  |
| `procedure_reference` | Char |  |  |  |  |
| `standard_ids` | Many2many |  |  |  |  |
| `ambient_temperature` | Float |  |  |  |  |
| `ambient_temperature_unit` | Char |  |  |  |  |
| `ambient_humidity` | Float |  |  |  |  |
| `reading_ids` | One2many |  |  |  |  |
| `reading_count` | Integer |  | yes | yes |  |
| `as_found_result` | Selection |  | yes | yes |  |
| `as_left_result` | Selection |  | yes | yes |  |
| `overall_result` | Selection |  | yes | yes |  |
| `adjustment_performed` | Boolean |  |  |  |  |
| `failed_point_count` | Integer |  | yes | yes |  |
| `next_due_date` | Date |  | yes | yes |  |
| `state` | Selection | yes |  |  |  |
| `reviewed_by_user_id` | Many2one |  |  |  |  |
| `reviewed_date` | Datetime |  |  |  |  |
| `approved_by_user_id` | Many2one |  |  |  |  |
| `approved_date` | Datetime |  |  |  |  |
| `rejection_reason` | Text |  |  |  |  |
| `cancellation_reason` | Text |  |  |  |  |
| `remarks` | Text |  |  |  |  |
| `certificate_ids` | One2many |  |  |  |  |
| `certificate_count` | Integer |  | yes |  |  |
| `oot_ids` | One2many |  |  |  |  |
| `oot_count` | Integer |  | yes |  |  |
| `company_id` | Many2one | yes |  |  |  |

**Constraints**

- SQL: `_name_company_uniq` — `UNIQUE(name, company_id)`
- SQL: `_humidity_range` — `CHECK(ambient_humidity >= 0 AND ambient_humidity <= 100)`
- Python: `_check_plan_instrument_consistency`
- Python: `_check_performed_date`
- Python: `_check_segregation_of_duties`
- Python: `_check_performed_completeness`

**Public actions**: `action_start`, `action_mark_performed`, `action_submit_for_review`, `action_approve`, `action_review`, `action_open_reject_wizard`, `action_reject`, `action_cancel`, `action_open_certificates`, `action_open_oot`

**Scheduled methods**: `_cron_notify_upcoming_calibrations`


### `ls.calibration.reading`

*Calibration Reading*

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `record_id` | Many2one | yes |  |  |  |
| `point_id` | Many2one | yes |  |  |  |
| `sequence` | Integer |  |  | yes | yes |
| `instrument_id` | Many2one |  |  | yes | yes |
| `record_state` | Selection |  |  |  | yes |
| `nominal_value` | Float |  |  | yes | yes |
| `lower_limit` | Float |  |  | yes | yes |
| `upper_limit` | Float |  |  | yes | yes |
| `unit_label` | Char |  |  |  | yes |
| `as_found_value` | Float |  |  |  |  |
| `as_found_recorded` | Boolean |  |  |  |  |
| `as_left_value` | Float |  |  |  |  |
| `as_left_recorded` | Boolean |  |  |  |  |
| `as_found_deviation` | Float |  | yes | yes |  |
| `as_left_deviation` | Float |  | yes | yes |  |
| `as_found_in_tolerance` | Boolean |  | yes | yes |  |
| `as_left_in_tolerance` | Boolean |  | yes | yes |  |
| `company_id` | Many2one |  |  | yes | yes |

**Constraints**

- SQL: `_point_record_uniq` — `UNIQUE(record_id, point_id)`
- Python: `_check_point_belongs_to_instrument`


### `ls.calibration.certificate`

*Calibration Certificate*

Inherits: `mail.thread`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `record_id` | Many2one | yes |  |  |  |
| `instrument_id` | Many2one |  |  | yes | yes |
| `certificate_type` | Selection | yes |  |  |  |
| `issue_date` | Date | yes |  |  |  |
| `issuer_name` | Char |  |  |  |  |
| `issuer_partner_id` | Many2one |  |  |  |  |
| `accreditation_reference` | Char |  |  |  |  |
| `valid_until` | Date |  |  | yes | yes |
| `document` | Binary |  |  |  |  |
| `document_filename` | Char |  |  |  |  |
| `overall_result` | Selection |  |  | yes | yes |
| `notes` | Text |  |  |  |  |
| `company_id` | Many2one |  |  | yes | yes |
| `active` | Boolean |  |  |  |  |

**Constraints**

- SQL: `_name_company_uniq` — `UNIQUE(name, company_id)`
- Python: `_check_issue_date`
- Python: `_check_external_document`
- Python: `_check_record_approved`

**Public actions**: `action_print`


### `ls.calibration.oot`

*Calibration Out-of-Tolerance Event*

Inherits: `mail.thread`, `mail.activity.mixin`

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `name` | Char | yes |  |  |  |
| `record_id` | Many2one | yes |  |  |  |
| `instrument_id` | Many2one |  |  | yes | yes |
| `criticality` | Selection |  |  | yes | yes |
| `detection_date` | Date | yes |  |  |  |
| `affected_period_start` | Date |  |  |  |  |
| `affected_period_end` | Date | yes |  |  |  |
| `description` | Text | yes |  |  |  |
| `impact_assessment` | Text |  |  |  |  |
| `product_impact` | Selection |  |  |  |  |
| `affected_batches` | Text |  |  |  |  |
| `disposition` | Selection |  |  |  |  |
| `disposition_justification` | Text |  |  |  |  |
| `capa_reference` | Char |  |  |  |  |
| `state` | Selection | yes |  |  |  |
| `assessed_by_user_id` | Many2one |  |  |  |  |
| `assessed_date` | Datetime |  |  |  |  |
| `closed_by_user_id` | Many2one |  |  |  |  |
| `closed_date` | Datetime |  |  |  |  |
| `responsible_user_id` | Many2one |  |  |  |  |
| `company_id` | Many2one | yes |  |  |  |

**Constraints**

- SQL: `_name_company_uniq` — `UNIQUE(name, company_id)`
- Python: `_check_affected_period`

**Public actions**: `action_start_assessment`, `action_complete_assessment`, `action_close`, `action_open_record`


### `ls.calibration.plan.generate`

*Generate Scheduled Calibrations*

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `horizon_date` | Date | yes |  |  |  |
| `plan_ids` | Many2many |  |  |  |  |
| `category_id` | Many2one |  |  |  |  |
| `criticality` | Selection |  |  |  |  |
| `company_id` | Many2one | yes |  |  |  |
| `generated_count` | Integer |  |  |  |  |

**Public actions**: `action_generate`


### `ls.calibration.record.reject`

*Reject Calibration Record*

| Field | Type | Required | Computed | Stored | Related |
|---|---|---|---|---|---|
| `record_id` | Many2one | yes |  |  |  |
| `instrument_id` | Many2one |  |  |  | yes |
| `reason` | Text | yes |  |  |  |

**Public actions**: `action_confirm`
