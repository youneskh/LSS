# ls_pharma - API Reference

This document is generated from the module sources by
`tools/generate_api_reference.py`, which reads the code with the
Python `ast` module. It is not maintained by hand, so it cannot
describe a field or a method that the code does not contain.

Column meanings in the field tables: **Field** is the technical
name, **Type** is the field class and, for a relational field, its
target model, **Label** is the user-visible string and
**Attributes** lists the declarative flags that the source sets.

## Contents

- [`ls.pharma.aggregation`](#lspharmaaggregation)
- [`ls.pharma.api`](#lspharmaapi)
- [`ls.pharma.batch`](#lspharmabatch)
- [`ls.pharma.batch.component`](#lspharmabatchcomponent)
- [`ls.pharma.batch.coproduct`](#lspharmabatchcoproduct)
- [`ls.pharma.batch.equipment`](#lspharmabatchequipment)
- [`ls.pharma.batch_record`](#lspharmabatch_record)
- [`ls.pharma.batch_record.clearance`](#lspharmabatch_recordclearance)
- [`ls.pharma.batch_record.control`](#lspharmabatch_recordcontrol)
- [`ls.pharma.batch_record.discrepancy`](#lspharmabatch_recorddiscrepancy)
- [`ls.pharma.batch_record.labeling`](#lspharmabatch_recordlabeling)
- [`ls.pharma.batch_record.sample`](#lspharmabatch_recordsample)
- [`ls.pharma.batch_record.step`](#lspharmabatch_recordstep)
- [`ls.pharma.batch.release`](#lspharmabatchrelease)
- [`ls.pharma.ctd_dossier`](#lspharmactd_dossier)
- [`ls.pharma.ctd.section`](#lspharmactdsection)
- [`ls.pharma.excipient`](#lspharmaexcipient)
- [`ls.pharma.material.mixin`](#lspharmamaterialmixin)
- [`ls.pharma.serialization`](#lspharmaserialization)
- [`ls.pharma.stability.condition`](#lspharmastabilitycondition)
- [`ls.pharma.stability.result`](#lspharmastabilityresult)
- [`ls.pharma.stability.sample`](#lspharmastabilitysample)
- [`ls.pharma.stability_study`](#lspharmastability_study)
- [`ls.pharma.stability.timepoint`](#lspharmastabilitytimepoint)
- [`extension of 'product.template'`](#extension-of-'producttemplate')
- [`extension of 'res.company'`](#extension-of-'rescompany')
- [`ls.pharma.batch.release.wizard`](#lspharmabatchreleasewizard)
- [`ls.pharma.serial.generate.wizard`](#lspharmaserialgeneratewizard)
- [`ls.pharma.stability.schedule.wizard`](#lspharmastabilityschedulewizard)

## `ls.pharma.aggregation`

- Python class: `LsPharmaAggregation`
- Source: `models/ls_pharma_aggregation.py`
- Description: Serialisation Aggregation Container
- Purpose: A logistics container identified by a Serial Shipping Container Code.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sscc` | Char | SSCC | required, index |  |
| `level` | Selection | Container Level | required, has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | required, index, has default |  |
| `parent_id` | Many2one &rarr; `ls.pharma.aggregation` | Parent Container | index |  |
| `child_ids` | One2many &rarr; `ls.pharma.aggregation` | Child Containers |  |  |
| `serialization_ids` | One2many &rarr; `ls.pharma.serialization` | Contained Units |  |  |
| `unit_count` | Integer | Contained Units | store, compute=_compute_counts |  |
| `child_count` | Integer | Child Containers | store, compute=_compute_counts |  |
| `element_string` | Char | GS1 Element String | store, compute=_compute_element_string |  |
| `state` | Selection | Status | required, index, has default |  |
| `date_packed` | Datetime | Packed On |  |  |
| `note` | Char | Remark |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_sscc_company_uniq` | `UNIQUE(sscc, company_id)` | A Serial Shipping Container Code must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `action_pack` | Mark the selected containers as packed and aggregate their units. |
| `action_disaggregate` | Disaggregate the selected containers. |
| `action_mark_shipped` | Record that the selected containers have been shipped. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_counts` | Count the direct contents of the container. |
| `_compute_element_string` | Build the element string of the container. |
| `_compute_display_name` | Show the container level and its code. |
| `_check_sscc` | Reject a code that is not a valid Serial Shipping Container Code. |
| `_check_parent` | Reject a container hierarchy that would form a loop. |

## `ls.pharma.api`

- Python class: `LsPharmaApi`
- Source: `models/ls_pharma_api.py`
- Inherits: `['ls.pharma.material.mixin']`
- Description: Active Pharmaceutical Ingredient
- Purpose: Master record of an active pharmaceutical ingredient.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `inn_name` | Char | International Nonproprietary Name |  |  |
| `active_moiety` | Char | Active Moiety |  |  |
| `potency_basis` | Selection | Potency Basis | required, has default |  |
| `label_assay_percentage` | Float | Label Assay (%) | has default |  |
| `is_controlled_substance` | Boolean | Controlled Substance |  |  |
| `controlled_schedule` | Char | Controlled Substance Schedule |  |  |
| `is_sterile` | Boolean | Supplied Sterile |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_code_company_uniq` | `UNIQUE(code, company_id)` | The internal code of an active pharmaceutical ingredient must be unique per company. |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_label_assay` | Reject an assay that cannot describe a real specification. |
| `_check_controlled_schedule` | Require the schedule of a qualified controlled substance. |

## `ls.pharma.batch`

- Python class: `LsPharmaBatch`
- Source: `models/ls_pharma_batch.py`
- Inherits: `['mail.thread', 'mail.activity.mixin']`
- Description: Pharmaceutical Manufacturing Batch
- Purpose: A batch of a pharmaceutical product.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Batch Reference | required, readonly, index, has default |  |
| `batch_type` | Selection | Batch Type | required, has default |  |
| `product_id` | Many2one &rarr; `product.product` | Product | required, index |  |
| `lot_id` | Many2one &rarr; `stock.lot` | Inventory Lot |  |  |
| `production_id` | Many2one &rarr; `mrp.production` | Manufacturing Order |  |  |
| `bom_id` | Many2one &rarr; `mrp.bom` | Bill of Materials |  |  |
| `warehouse_id` | Many2one &rarr; `stock.warehouse` | Manufacturing Site |  |  |
| `parent_batch_id` | Many2one &rarr; `ls.pharma.batch` | Bulk Batch | index |  |
| `child_batch_ids` | One2many &rarr; `ls.pharma.batch` | Derived Batches |  |  |
| `child_batch_count` | Integer | Derived Batch Count | compute=_compute_child_batch_count |  |
| `uom_id` | Many2one &rarr; `uom.uom` | Unit of Measure | required, has default |  |
| `planned_qty` | Float | Planned Quantity |  |  |
| `theoretical_yield_qty` | Float | Theoretical Yield |  |  |
| `actual_yield_qty` | Float | Actual Yield |  |  |
| `yield_percentage` | Float | Yield (%) | store, compute=_compute_yield_percentage |  |
| `yield_min_percentage` | Float | Minimum Yield (%) |  |  |
| `yield_max_percentage` | Float | Maximum Yield (%) |  |  |
| `yield_investigation_required` | Boolean | Yield Investigation Required | store, compute=_compute_yield_investigation_required |  |
| `yield_investigation_reference` | Char | Yield Investigation Reference |  |  |
| `date_start` | Datetime | Production Start |  |  |
| `date_end` | Datetime | Production End |  |  |
| `date_manufacture` | Date | Manufacturing Date | index |  |
| `shelf_life_months` | Integer | Shelf Life (Months) |  |  |
| `date_expiry` | Date | Expiry Date | index |  |
| `date_retest` | Date | Retest Date |  |  |
| `component_ids` | One2many &rarr; `ls.pharma.batch.component` | Components |  |  |
| `equipment_ids` | One2many &rarr; `ls.pharma.batch.equipment` | Equipment and Lines |  |  |
| `coproduct_ids` | One2many &rarr; `ls.pharma.batch.coproduct` | Co-Products |  |  |
| `batch_record_ids` | One2many &rarr; `ls.pharma.batch_record` | Batch Records |  |  |
| `batch_record_count` | Integer | Batch Record Count | compute=_compute_batch_record_count |  |
| `stability_study_ids` | One2many &rarr; `ls.pharma.stability_study` | Stability Studies |  |  |
| `stability_study_count` | Integer | Stability Study Count | compute=_compute_stability_study_count |  |
| `serialization_ids` | One2many &rarr; `ls.pharma.serialization` | Serialised Units |  |  |
| `serialization_count` | Integer | Serialised Unit Count | compute=_compute_serialization_count |  |
| `release_id` | Many2one &rarr; `ls.pharma.batch.release` | Release Decision | readonly |  |
| `user_manufactured_id` | Many2one &rarr; `res.users` | Manufactured By | readonly |  |
| `user_reviewed_id` | Many2one &rarr; `res.users` | Submitted for Review By | readonly |  |
| `state` | Selection | Status | required, index, has default |  |
| `note` | Text | Internal Notes |  |  |
| `company_id` | Many2one &rarr; `res.company` | Company | required, index, has default |  |
| `active` | Boolean | Active | has default |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The batch reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `create` | Assign the batch reference from the dedicated sequence. |
| `write` | Protect production data once a release decision has been taken. |
| `unlink` | Forbid the deletion of a batch that carries a quality decision. |
| `copy_data` | Reset the execution data when a batch is duplicated. |
| `action_start` | Start production of the selected batches. |
| `action_complete` | Declare manufacturing complete and record who declared it. |
| `action_quarantine` | Place the selected batches in quarantine. |
| `action_submit_review` | Submit the selected batches to the quality unit for record review. |
| `action_open_release_wizard` | Open the wizard that records the release decision. |
| `action_cancel` | Cancel the selected batches. |
| `action_set_draft` | Return a cancelled batch to the draft state. |
| `action_view_batch_records` | Open the batch records attached to this batch. |
| `action_view_stability_studies` | Open the stability studies that cover this batch. |
| `action_view_serialization` | Open the serialised units generated for this batch. |
| `action_view_child_batches` | Open the packaging batches derived from this batch. |
| `cron_notify_expiring_batches` | Post a message on released batches that are approaching expiry. |

### Internal methods

| Method | Purpose |
|---|---|
| `_default_uom_id` | Return the reference unit of the first unit-of-measure category. |
| `_compute_yield_percentage` | Compute the percentage of theoretical yield. |
| `_compute_yield_investigation_required` | Flag a yield that falls outside the established limits. |
| `_compute_child_batch_count` | Count the packaging batches derived from this batch. |
| `_compute_batch_record_count` | Count the batch records attached to this batch. |
| `_compute_stability_study_count` | Count the stability studies that cover this batch. |
| `_compute_serialization_count` | Count the serialised units generated for this batch. |
| `_compute_display_name` | Show the batch reference together with the product name. |
| `_onchange_product_id` | Default the yield limits, shelf life and unit from the product. |
| `_onchange_expiry_inputs` | Derive the expiry date from the manufacturing date and shelf life. |
| `_check_expiry_after_manufacture` | Reject an expiry date that precedes the manufacturing date. |
| `_check_production_window` | Reject a production end that precedes the production start. |
| `_check_yield_limits` | Reject yield limits that cannot describe an acceptance range. |
| `_check_quantities` | Reject negative quantities. |
| `_check_parent_batch` | Reject a genealogy that would form a loop. |
| `_check_parent_batch_type` | Require a packaging batch to descend from a bulk batch. |
| `_assert_state` | Raise unless every record is in one of ``expected_states``. |
| `_action_open_related` | Return an action listing the records of ``model`` in ``domain``. |

## `ls.pharma.batch.component`

- Python class: `LsPharmaBatchComponent`
- Source: `models/ls_pharma_batch_component.py`
- Description: Batch Component Charge
- Purpose: A component or in-process material charged into a batch.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `product_id` | Many2one &rarr; `product.product` | Component | required |  |
| `api_id` | Many2one &rarr; `ls.pharma.api` | Active Ingredient |  |  |
| `excipient_id` | Many2one &rarr; `ls.pharma.excipient` | Excipient |  |  |
| `component_lot_id` | Many2one &rarr; `stock.lot` | Component Lot |  |  |
| `component_lot_reference` | Char | Component Lot Reference |  |  |
| `quantity` | Float | Quantity Charged | required |  |
| `uom_id` | Many2one &rarr; `uom.uom` | Unit of Measure | required |  |
| `assay_percentage` | Float | Assay (%) |  |  |
| `compensated_quantity` | Float | Potency-Compensated Quantity | store, compute=_compute_compensated_quantity |  |
| `is_active_ingredient` | Boolean | Active Ingredient | store, compute=_compute_is_active_ingredient |  |
| `charged_by_user_id` | Many2one &rarr; `res.users` | Charged By |  |  |
| `verified_by_user_id` | Many2one &rarr; `res.users` | Verified By |  |  |
| `is_automated_charge` | Boolean | Charged by Automated Equipment |  |  |
| `date_charged` | Datetime | Charge Date and Time |  |  |
| `note` | Char | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_is_active_ingredient` | Flag the lines that carry an active pharmaceutical ingredient. |
| `_compute_compensated_quantity` | Compute the potency-compensated charge quantity. |
| `_check_quantity` | Reject a charge quantity that is not strictly positive. |
| `_check_assay` | Reject a negative assay. |
| `_check_second_person_verification` | Enforce the second-person verification of 21 CFR 211.101(d). |
| `_check_material_exclusivity` | Reject a component that is both an active ingredient and an excipient. |
| `_onchange_product_id` | Default the unit of measure from the selected component. |

## `ls.pharma.batch.coproduct`

- Python class: `LsPharmaBatchCoproduct`
- Source: `models/ls_pharma_batch_coproduct.py`
- Description: Batch Co-Product
- Purpose: An additional product obtained from the same manufacturing run.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `product_id` | Many2one &rarr; `product.product` | Co-Product | required |  |
| `lot_id` | Many2one &rarr; `stock.lot` | Inventory Lot |  |  |
| `quantity` | Float | Quantity Obtained | required |  |
| `uom_id` | Many2one &rarr; `uom.uom` | Unit of Measure | required |  |
| `note` | Char | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_quantity` | Reject a co-product quantity that is not strictly positive. |
| `_onchange_product_id` | Default the unit of measure from the selected co-product. |

## `ls.pharma.batch.equipment`

- Python class: `LsPharmaBatchEquipment`
- Source: `models/ls_pharma_batch_equipment.py`
- Description: Batch Equipment and Line Usage
- Purpose: Identity of an individual item of major equipment or a line.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `name` | Char | Equipment or Line | required |  |
| `equipment_identifier` | Char | Equipment Identifier | required |  |
| `operation` | Char | Operation |  |  |
| `cleaning_record_reference` | Char | Cleaning Record Reference |  |  |
| `cleaning_verified_by_user_id` | Many2one &rarr; `res.users` | Cleaning Verified By |  |  |
| `date_used_start` | Datetime | Used From |  |  |
| `date_used_end` | Datetime | Used Until |  |  |
| `note` | Char | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_usage_window` | Reject a usage window that ends before it starts. |

## `ls.pharma.batch_record`

- Python class: `LsPharmaBatchRecord`
- Source: `models/ls_pharma_batch_record.py`
- Inherits: `['mail.thread', 'mail.activity.mixin']`
- Description: Batch Production and Control Record
- Purpose: The batch production and control record of a batch.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Record Reference | required, readonly, index, has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `product_id` | Many2one &rarr; `product.product` | Product | store, related=batch_id.product_id |  |
| `record_type` | Selection | Record Type | required, has default |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `master_record_reference` | Char | Master Record Reference | required |  |
| `master_record_version` | Char | Master Record Version | required |  |
| `master_checked_by_user_id` | Many2one &rarr; `res.users` | Master Record Checked By |  |  |
| `master_checked_date` | Datetime | Master Record Checked On |  |  |
| `step_ids` | One2many &rarr; `ls.pharma.batch_record.step` | Manufacturing Steps |  |  |
| `control_ids` | One2many &rarr; `ls.pharma.batch_record.control` | In-Process and Laboratory Controls |  |  |
| `clearance_ids` | One2many &rarr; `ls.pharma.batch_record.clearance` | Area Inspections |  |  |
| `labeling_ids` | One2many &rarr; `ls.pharma.batch_record.labeling` | Labelling Control |  |  |
| `sample_ids` | One2many &rarr; `ls.pharma.batch_record.sample` | Samples Taken |  |  |
| `discrepancy_ids` | One2many &rarr; `ls.pharma.batch_record.discrepancy` | Discrepancies and Investigations |  |  |
| `container_closure_description` | Text | Containers and Closures |  |  |
| `examination_result` | Text | Container and Closure Examination |  |  |
| `step_count` | Integer | Steps | store, compute=_compute_counts |  |
| `step_done_count` | Integer | Steps Completed | store, compute=_compute_counts |  |
| `open_discrepancy_count` | Integer | Open Discrepancies | store, compute=_compute_counts |  |
| `nonconforming_control_count` | Integer | Non-Conforming Controls | store, compute=_compute_counts |  |
| `unreconciled_label_count` | Integer | Unreconciled Labels | store, compute=_compute_counts |  |
| `reserve_sample_count` | Integer | Reserve Samples | store, compute=_compute_counts |  |
| `completion_percentage` | Float | Execution Progress (%) | store, compute=_compute_counts |  |
| `executed_by_user_id` | Many2one &rarr; `res.users` | Execution Completed By | readonly |  |
| `date_executed` | Datetime | Execution Completed On | readonly |  |
| `reviewed_by_user_id` | Many2one &rarr; `res.users` | Reviewed By | readonly |  |
| `date_reviewed` | Datetime | Reviewed On | readonly |  |
| `review_conclusion` | Text | Review Conclusion |  |  |
| `state` | Selection | Status | required, index, has default |  |
| `active` | Boolean | Active | has default |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The batch record reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `create` | Assign the record reference from the dedicated sequence. |
| `write` | Freeze the execution content once the record has been approved. |
| `unlink` | Forbid the deletion of a record that has left the draft state. |
| `copy_data` | Reset the accountability data when a record is duplicated. |
| `action_start_execution` | Open the record for execution. |
| `action_complete_execution` | Declare the execution complete. |
| `action_submit_review` | Submit the record to the quality unit. |
| `action_approve` | Approve the record on behalf of the quality unit. |
| `action_reject` | Reject the record on behalf of the quality unit. |
| `action_return_to_execution` | Return a record under review to the execution state. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_counts` | Compute the aggregates that drive the review readiness checks. |
| `_compute_display_name` | Show the record reference together with the batch reference. |
| `_assert_state` | Raise unless every record is in one of ``expected_states``. |

## `ls.pharma.batch_record.clearance`

- Python class: `LsPharmaBatchRecordClearance`
- Source: `models/ls_pharma_batch_record_clearance.py`
- Description: Batch Record Area Inspection
- Purpose: An inspection of the packaging and labelling area.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `moment` | Selection | Moment | required, has default |  |
| `area` | Char | Area or Line | required |  |
| `date_performed` | Datetime | Performed On | required, has default |  |
| `performed_by_user_id` | Many2one &rarr; `res.users` | Performed By | has default |  |
| `verified_by_user_id` | Many2one &rarr; `res.users` | Verified By |  |  |
| `result` | Selection | Result | required, has default |  |
| `previous_product` | Char | Previous Product |  |  |
| `findings` | Text | Findings |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_failed_clearance` | Require findings to be recorded when an inspection fails. |
| `_check_independent_verification` | Reject an inspection verified by the person who performed it. |

## `ls.pharma.batch_record.control`

- Python class: `LsPharmaBatchRecordControl`
- Source: `models/ls_pharma_batch_record_control.py`
- Description: Batch Record Control Result
- Purpose: An in-process or laboratory control result.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `name` | Char | Test | required |  |
| `control_type` | Selection | Control Type | required, has default |  |
| `method_reference` | Char | Method Reference |  |  |
| `result_type` | Selection | Result Type | required, has default |  |
| `specification_text` | Char | Acceptance Criterion |  |  |
| `specification_min` | Float | Minimum |  |  |
| `specification_max` | Float | Maximum |  |  |
| `has_minimum` | Boolean | Minimum Applies |  |  |
| `has_maximum` | Boolean | Maximum Applies |  |  |
| `result_value` | Float | Result |  |  |
| `result_text` | Char | Result (Text) |  |  |
| `result_uom` | Char | Result Unit |  |  |
| `is_conform` | Boolean | Conforms | store, compute=_compute_is_conform |  |
| `performed_by_user_id` | Many2one &rarr; `res.users` | Performed By |  |  |
| `date_performed` | Datetime | Date Performed |  |  |
| `remark` | Text | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_is_conform` | Compute the conformity of a numeric result. |
| `_check_specification_range` | Reject an acceptance range whose minimum exceeds its maximum. |
| `_check_textual_result` | Require a value for a textual result that has been attributed. |

## `ls.pharma.batch_record.discrepancy`

- Python class: `LsPharmaBatchRecordDiscrepancy`
- Source: `models/ls_pharma_batch_record_discrepancy.py`
- Description: Batch Record Discrepancy and Investigation
- Purpose: An unexplained discrepancy and the investigation it triggered.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `name` | Char | Discrepancy | required |  |
| `classification` | Selection | Classification | required, has default |  |
| `description` | Text | Description | required |  |
| `date_detected` | Datetime | Detected On | required, has default |  |
| `detected_by_user_id` | Many2one &rarr; `res.users` | Detected By | has default |  |
| `investigation` | Text | Investigation |  |  |
| `extended_to_other_batches` | Boolean | Extended to Other Batches |  |  |
| `extension_scope` | Text | Extension Scope |  |  |
| `conclusion` | Text | Conclusion |  |  |
| `follow_up` | Text | Follow-Up |  |  |
| `external_reference` | Char | External Reference |  |  |
| `investigated_by_user_id` | Many2one &rarr; `res.users` | Investigated By | readonly |  |
| `date_closed` | Datetime | Closed On | readonly |  |
| `state` | Selection | Status | required, index, has default |  |

### Public methods

| Method | Purpose |
|---|---|
| `action_start_investigation` | Move the selected discrepancies to the investigation state. |
| `action_close` | Close the selected discrepancies. |
| `action_reopen` | Reopen the selected discrepancies. |

## `ls.pharma.batch_record.labeling`

- Python class: `LsPharmaBatchRecordLabeling`
- Source: `models/ls_pharma_batch_record_labeling.py`
- Description: Batch Record Labelling Control
- Purpose: Issuance, use, return and destruction of one labelling item.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `name` | Char | Labelling Item | required |  |
| `label_version` | Char | Version | required |  |
| `label_code` | Char | Item Code |  |  |
| `quantity_issued` | Float | Issued |  |  |
| `quantity_used` | Float | Used |  |  |
| `quantity_returned` | Float | Returned |  |  |
| `quantity_destroyed` | Float | Destroyed |  |  |
| `quantity_difference` | Float | Difference | store, compute=_compute_reconciliation |  |
| `is_reconciled` | Boolean | Reconciled | store, compute=_compute_reconciliation |  |
| `tolerance` | Float | Tolerance |  |  |
| `checked_by_user_id` | Many2one &rarr; `res.users` | Reconciled By |  |  |
| `date_checked` | Datetime | Reconciled On |  |  |
| `remark` | Text | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_reconciliation` | Compute the reconciliation difference and its acceptability. |
| `_check_quantities` | Reject negative labelling quantities. |

## `ls.pharma.batch_record.sample`

- Python class: `LsPharmaBatchRecordSample`
- Source: `models/ls_pharma_batch_record_sample.py`
- Description: Batch Record Sample
- Purpose: A sample taken during manufacture, packaging or holding.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `name` | Char | Sample Reference | required |  |
| `sample_type` | Selection | Sample Type | required, index, has default |  |
| `purpose` | Char | Purpose |  |  |
| `quantity` | Float | Quantity |  |  |
| `uom_id` | Many2one &rarr; `uom.uom` | Unit of Measure |  |  |
| `sampling_point` | Char | Sampling Point |  |  |
| `storage_location` | Char | Storage Location |  |  |
| `date_taken` | Datetime | Taken On | required, has default |  |
| `taken_by_user_id` | Many2one &rarr; `res.users` | Taken By | has default |  |
| `retention_until` | Date | Retain Until |  |  |
| `result_reference` | Char | Result Reference |  |  |
| `remark` | Text | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_quantity` | Reject a negative sample quantity. |
| `_check_reserve_retention` | Require a coherent retention date for a reserve sample. |

## `ls.pharma.batch_record.step`

- Python class: `LsPharmaBatchRecordStep`
- Source: `models/ls_pharma_batch_record_step.py`
- Description: Batch Record Manufacturing Step
- Purpose: A significant step in the manufacture, processing, packing or holding.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `record_id` | Many2one &rarr; `ls.pharma.batch_record` | Batch Record | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=record_id.company_id |  |
| `name` | Char | Step | required |  |
| `instruction` | Text | Instruction |  |  |
| `is_significant` | Boolean | Significant Step | has default |  |
| `is_automated` | Boolean | Performed by Automated Equipment |  |  |
| `performed_by_user_id` | Many2one &rarr; `res.users` | Performed By |  |  |
| `checked_by_user_id` | Many2one &rarr; `res.users` | Checked or Supervised By |  |  |
| `date_performed` | Datetime | Date Performed |  |  |
| `recorded_value` | Char | Recorded Value |  |  |
| `recorded_uom` | Char | Value Unit |  |  |
| `state` | Selection | Status | required, index, has default |  |
| `remark` | Text | Remark |  |  |

### Public methods

| Method | Purpose |
|---|---|
| `action_start` | Mark the selected steps as being in progress. |
| `action_done` | Complete the selected steps and stamp the executing user. |
| `action_not_applicable` | Mark the selected steps as not applicable to this batch. |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_attribution` | Enforce the attribution required by 21 CFR 211.188(b). |

## `ls.pharma.batch.release`

- Python class: `LsPharmaBatchRelease`
- Source: `models/ls_pharma_batch_release.py`
- Inherits: `['mail.thread']`
- Description: Batch Release Decision
- Purpose: The recorded decision of the quality unit on a batch.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Decision Reference | required, readonly, index, has default |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `product_id` | Many2one &rarr; `product.product` | Product | store, related=batch_id.product_id |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `decision` | Selection | Decision | required |  |
| `decision_date` | Datetime | Decision Date | required, has default |  |
| `decided_by_user_id` | Many2one &rarr; `res.users` | Decided By | required, has default |  |
| `statement` | Text | Decision Statement | required |  |
| `check_record_reviewed` | Boolean | Batch Records Reviewed and Approved |  |  |
| `check_discrepancies_closed` | Boolean | Discrepancies Investigated and Closed |  |  |
| `check_yield_within_limits` | Boolean | Yield Within Limits |  |  |
| `check_components_verified` | Boolean | Component Charge-In Verified by a Second Person |  |  |
| `check_qc_conform` | Boolean | Laboratory Results Conform |  |  |
| `check_labeling_reconciled` | Boolean | Labelling Reconciled |  |  |
| `check_reserve_samples` | Boolean | Reserve Samples Retained |  |  |
| `check_stability_programme` | Boolean | Covered by the Stability Programme |  |  |
| `checklist_complete` | Boolean | Checklist Complete | store, compute=_compute_checklist_complete |  |
| `integrity_hash` | Char | Integrity Digest | readonly |  |
| `integrity_verified` | Boolean | Digest Verified | compute=_compute_integrity_verified |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The release decision reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `get_checklist_report_lines` | Return the release checklist as printable lines. |
| `action_verify_integrity` | Verify the digest and report the outcome in the chatter. |
| `create` | Assign the reference, enforce the guards and stamp the digest. |
| `write` | Refuse to modify a decision that has already been recorded. |
| `unlink` | Refuse to delete a recorded decision. |
| `copy_data` | Refuse to duplicate a recorded decision. |
| `action_open_batch` | Open the batch that this decision applies to. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_checklist_complete` | Set when every entry of the release checklist has been confirmed. |
| `_compute_integrity_verified` | Recompute the digest and compare it with the stored value. |
| `_compute_display_name` | Show the decision reference together with the batch reference. |
| `_integrity_payload` | Return the ordered list of values covered by the integrity digest. |
| `_build_integrity_hash` | Return the digest of the canonical representation of the decision. |
| `_check_release_preconditions` | Verify the conditions that must hold before a decision is recorded. |
| `_check_release_gate` | Verify the conditions specific to a positive release decision. |
| `_apply_to_batch` | Propagate the decision to the batch. |

## `ls.pharma.ctd_dossier`

- Python class: `LsPharmaCtdDossier`
- Source: `models/ls_pharma_ctd_dossier.py`
- Inherits: `['mail.thread', 'mail.activity.mixin']`
- Description: Common Technical Document Dossier
- Purpose: A regulatory dossier organised in the Common Technical Document format.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Dossier Reference | required, readonly, index, has default |  |
| `title` | Char | Title | required |  |
| `product_id` | Many2one &rarr; `product.product` | Product | required, index |  |
| `dossier_type` | Selection | Dossier Type | required, has default |  |
| `authority_name` | Char | Regulatory Authority | required |  |
| `authority_partner_id` | Many2one &rarr; `res.partner` | Authority Contact |  |  |
| `marketing_auth_holder_id` | Many2one &rarr; `res.partner` | Marketing Authorisation Holder |  |  |
| `dossier_version` | Char | Version | required, has default |  |
| `date_submission` | Date | Submission Date |  |  |
| `date_decision` | Date | Decision Date |  |  |
| `authorisation_number` | Char | Authorisation Number |  |  |
| `section_ids` | One2many &rarr; `ls.pharma.ctd.section` | Sections |  |  |
| `section_count` | Integer | Sections | store, compute=_compute_progress |  |
| `section_complete_count` | Integer | Sections Complete | store, compute=_compute_progress |  |
| `completion_percentage` | Float | Completion (%) | store, compute=_compute_progress |  |
| `deficiency_count` | Integer | Sections in Deficiency | store, compute=_compute_progress |  |
| `state` | Selection | Status | required, index, has default |  |
| `note` | Text | Notes |  |  |
| `company_id` | Many2one &rarr; `res.company` | Company | required, index, has default |  |
| `active` | Boolean | Active | has default |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The dossier reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `create` | Assign the dossier reference from the dedicated sequence. |
| `unlink` | Forbid the deletion of a dossier that has been submitted. |
| `action_load_template` | Create the standard section structure of ICH M4(R4). |
| `action_start_preparation` | Move the selected dossiers to the preparation state. |
| `action_mark_ready` | Declare the selected dossiers ready for submission. |
| `action_submit` | Record the submission of the selected dossiers. |
| `action_record_deficiency` | Record that a deficiency has been received on the dossiers. |
| `action_approve` | Record the approval of the selected dossiers. |
| `action_withdraw` | Record the withdrawal of the selected dossiers. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_progress` | Compute the preparation progress of the dossier. |
| `_compute_display_name` | Show the dossier reference together with its title. |
| `_check_dates` | Reject a decision date that precedes the submission date. |

## `ls.pharma.ctd.section`

- Python class: `LsPharmaCtdSection`
- Source: `models/ls_pharma_ctd_section.py`
- Description: CTD Dossier Section
- Purpose: One section of a Common Technical Document dossier.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `dossier_id` | Many2one &rarr; `ls.pharma.ctd_dossier` | Dossier | index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=dossier_id.company_id |  |
| `is_template` | Boolean | Template Section | has default |  |
| `module` | Selection | CTD Module | required, index |  |
| `code` | Char | Section Number | required |  |
| `name` | Char | Section Title | required, translate |  |
| `responsible_user_id` | Many2one &rarr; `res.users` | Responsible |  |  |
| `date_due` | Date | Due Date |  |  |
| `document_reference` | Char | Document Reference |  |  |
| `state` | Selection | Status | required, index, has default |  |
| `deficiency_note` | Text | Deficiency |  |  |
| `note` | Text | Notes |  |  |

### Public methods

| Method | Purpose |
|---|---|
| `action_start` | Move the selected sections to the preparation state. |
| `action_mark_ready` | Declare the selected sections ready. |
| `action_mark_complete` | Mark the selected sections as complete. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Show the section number together with its title. |
| `_check_template_has_no_dossier` | Reject a template section that is attached to a dossier. |
| `_check_deficiency_note` | Require the deficiency to be described when it is recorded. |

## `ls.pharma.excipient`

- Python class: `LsPharmaExcipient`
- Source: `models/ls_pharma_excipient.py`
- Inherits: `['ls.pharma.material.mixin']`
- Description: Excipient
- Purpose: Master record of an excipient.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `excipient_function` | Selection | Function | required |  |
| `is_novel` | Boolean | Novel Excipient |  |  |
| `maximum_daily_intake_mg` | Float | Maximum Daily Intake (mg) |  |  |
| `requires_declaration` | Boolean | Requires Label Declaration |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_code_company_uniq` | `UNIQUE(code, company_id)` | The internal code of an excipient must be unique per company. |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_maximum_daily_intake` | Reject a negative maximum daily intake. |

## `ls.pharma.material.mixin`

- Python class: `LsPharmaMaterialMixin`
- Source: `models/ls_pharma_material_mixin.py`
- Inherits: `['mail.thread', 'mail.activity.mixin']`
- Description: Pharmaceutical Material Master Data Mixin
- Purpose: Common structure of an active ingredient or excipient master record.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Material Name | required, index |  |
| `code` | Char | Internal Code | required, index |  |
| `product_id` | Many2one &rarr; `product.product` | Inventory Item |  |  |
| `pharmacopoeia` | Selection | Specification Basis |  |  |
| `monograph_reference` | Char | Monograph Reference |  |  |
| `cas_number` | Char | CAS Number |  |  |
| `manufacturer_partner_ids` | Many2many &rarr; `res.partner` | Approved Manufacturers |  |  |
| `retest_period_months` | Integer | Retest Period (Months) |  |  |
| `storage_condition` | Char | Storage Condition |  |  |
| `of_animal_origin` | Boolean | Of Animal Origin |  |  |
| `tse_statement_reference` | Char | TSE/BSE Statement Reference |  |  |
| `state` | Selection | Status | required, has default |  |
| `note` | Text | Internal Notes |  |  |
| `company_id` | Many2one &rarr; `res.company` | Company | required, index, has default |  |
| `active` | Boolean | Active | has default |  |

### Public methods

| Method | Purpose |
|---|---|
| `action_qualify` | Move the selected materials to the qualified state. |
| `action_restrict` | Restrict the selected materials from further use. |
| `action_set_draft` | Return the selected materials to the draft state. |
| `action_obsolete` | Mark the selected materials as obsolete and archive them. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Show the internal code alongside the material name. |
| `_check_tse_statement` | Require a TSE statement before a material of animal origin is used. |
| `_check_retest_period` | Reject a negative retest period. |

## `ls.pharma.serialization`

- Python class: `LsPharmaSerialization`
- Source: `models/ls_pharma_serialization.py`
- Description: Serialised Saleable Unit
- Purpose: A single serialised saleable unit of a medicinal product.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=batch_id.company_id |  |
| `product_id` | Many2one &rarr; `product.product` | Product | store, related=batch_id.product_id |  |
| `gtin` | Char | Product Code (GTIN-14) | required, index |  |
| `serial_number` | Char | Serial Number | required, index |  |
| `batch_number` | Char | Batch Number | required |  |
| `expiry_date` | Date | Expiry Date | required |  |
| `national_number` | Char | National Reimbursement Number |  |  |
| `element_string` | Char | GS1 Element String | store, compute=_compute_element_string |  |
| `aggregation_id` | Many2one &rarr; `ls.pharma.aggregation` | Parent Container | index |  |
| `state` | Selection | Status | required, index, has default |  |
| `date_commissioned` | Datetime | Commissioned On |  |  |
| `date_decommissioned` | Datetime | Decommissioned On |  |  |
| `decommission_reason` | Char | Decommission Reason |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_gtin_serial_company_uniq` | `UNIQUE(gtin, serial_number, company_id)` | A serial number can only be used once for a given product code. |

### Public methods

| Method | Purpose |
|---|---|
| `write` | Protect the identifying data of a commissioned unit. |
| `unlink` | Forbid the deletion of a unit that has been commissioned. |
| `action_commission` | Commission the selected units. |
| `action_decommission` | Decommission the selected units. |
| `action_mark_shipped` | Record that the selected units have been shipped. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_element_string` | Build the element string of the unique identifier. |
| `_compute_display_name` | Show the product code and the serial number. |
| `_check_gtin` | Reject a product code that is not a valid GTIN-14. |
| `_check_variable_fields` | Reject data fields that exceed the length permitted by GS1. |

## `ls.pharma.stability.condition`

- Python class: `LsPharmaStabilityCondition`
- Source: `models/ls_pharma_stability_condition.py`
- Description: Stability Storage Condition
- Purpose: A storage condition under which stability samples are held.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Condition | required, translate |  |
| `code` | Char | Code | required |  |
| `condition_type` | Selection | Type | required, has default |  |
| `temperature_celsius` | Float | Temperature (Celsius) | required |  |
| `temperature_tolerance` | Float | Temperature Tolerance (Celsius) |  |  |
| `relative_humidity` | Float | Relative Humidity (%) |  |  |
| `humidity_tolerance` | Float | Relative Humidity Tolerance (%) |  |  |
| `default_duration_months` | Integer | Default Duration (Months) | required, has default |  |
| `reference` | Char | Source Reference |  |  |
| `note` | Text | Notes |  |  |
| `active` | Boolean | Active | has default |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_code_uniq` | `UNIQUE(code)` | The code of a stability storage condition must be unique. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Show the temperature and humidity alongside the condition name. |
| `_check_humidity` | Reject a relative humidity outside the range 0 to 100. |
| `_check_duration` | Reject a non-positive default duration. |

## `ls.pharma.stability.result`

- Python class: `LsPharmaStabilityResult`
- Source: `models/ls_pharma_stability_result.py`
- Description: Stability Test Result
- Purpose: One analytical result obtained at a stability time point.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `sequence` | Integer | Sequence | has default |  |
| `timepoint_id` | Many2one &rarr; `ls.pharma.stability.timepoint` | Time Point | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=timepoint_id.company_id |  |
| `study_id` | Many2one &rarr; `ls.pharma.stability_study` | Study | store, index, related=timepoint_id.study_id |  |
| `name` | Char | Test | required |  |
| `method_reference` | Char | Method Reference |  |  |
| `result_type` | Selection | Result Type | required, has default |  |
| `specification_text` | Char | Acceptance Criterion |  |  |
| `specification_min` | Float | Minimum |  |  |
| `specification_max` | Float | Maximum |  |  |
| `has_minimum` | Boolean | Minimum Applies |  |  |
| `has_maximum` | Boolean | Maximum Applies |  |  |
| `result_value` | Float | Result |  |  |
| `result_text` | Char | Result (Text) |  |  |
| `result_uom` | Char | Result Unit |  |  |
| `is_conform` | Boolean | Conforms | store, compute=_compute_is_conform |  |
| `is_significant_change` | Boolean | Significant Change |  |  |
| `tested_by_user_id` | Many2one &rarr; `res.users` | Tested By |  |  |
| `date_tested` | Date | Tested On |  |  |
| `remark` | Text | Remark |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_is_conform` | Compute the conformity of a numeric result. |
| `_onchange_is_conform` | Propose a non-conforming result as a significant change. |
| `_check_specification_range` | Reject an acceptance range whose minimum exceeds its maximum. |

## `ls.pharma.stability.sample`

- Python class: `LsPharmaStabilitySample`
- Source: `models/ls_pharma_stability_sample.py`
- Description: Stability Sample
- Purpose: A physical sample placed in a stability chamber.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Sample Reference | required |  |
| `study_id` | Many2one &rarr; `ls.pharma.stability_study` | Study | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=study_id.company_id |  |
| `timepoint_id` | Many2one &rarr; `ls.pharma.stability.timepoint` | Allocated Time Point | index |  |
| `condition_id` | Many2one &rarr; `ls.pharma.stability.condition` | Storage Condition | required |  |
| `quantity` | Float | Quantity |  |  |
| `uom_id` | Many2one &rarr; `uom.uom` | Unit of Measure |  |  |
| `chamber_reference` | Char | Chamber Reference |  |  |
| `position_reference` | Char | Position in Chamber |  |  |
| `date_placed` | Date | Placed On | required, has default |  |
| `date_removed` | Date | Removed On |  |  |
| `state` | Selection | Status | required, index, has default |  |
| `remark` | Text | Remark |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The stability sample reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `action_pull` | Record that the selected samples have been pulled. |
| `action_consume` | Record that the selected samples have been consumed by testing. |
| `action_discard` | Record that the selected samples have been discarded. |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_quantity` | Reject a negative sample quantity. |
| `_check_dates` | Reject a removal date that precedes the placement date. |
| `_check_timepoint_consistency` | Reject an allocation to a time point of another study or condition. |

## `ls.pharma.stability_study`

- Python class: `LsPharmaStabilityStudy`
- Source: `models/ls_pharma_stability_study.py`
- Inherits: `['mail.thread', 'mail.activity.mixin']`
- Description: Stability Study
- Purpose: A stability study conducted on a batch of a product.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `name` | Char | Study Reference | required, readonly, index, has default |  |
| `title` | Char | Title | required |  |
| `study_type` | Selection | Study Type | required, has default |  |
| `product_id` | Many2one &rarr; `product.product` | Product | required, index |  |
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | index |  |
| `protocol_reference` | Char | Protocol Reference | required |  |
| `packaging_description` | Char | Packaging Configuration |  |  |
| `date_start` | Date | Study Start | required, has default |  |
| `duration_months` | Integer | Planned Duration (Months) | required, has default |  |
| `date_planned_end` | Date | Planned End | store, compute=_compute_date_planned_end |  |
| `condition_ids` | Many2many &rarr; `ls.pharma.stability.condition` | Storage Conditions |  |  |
| `timepoint_ids` | One2many &rarr; `ls.pharma.stability.timepoint` | Time Points |  |  |
| `sample_ids` | One2many &rarr; `ls.pharma.stability.sample` | Stability Samples |  |  |
| `timepoint_count` | Integer | Time Points | store, compute=_compute_counts |  |
| `timepoint_overdue_count` | Integer | Overdue Time Points | store, compute=_compute_counts |  |
| `sample_count` | Integer | Samples | store, compute=_compute_counts |  |
| `has_significant_change` | Boolean | Significant Change Observed | store, compute=_compute_counts |  |
| `proposed_shelf_life_months` | Integer | Proposed Shelf Life (Months) |  |  |
| `conclusion` | Text | Conclusion |  |  |
| `state` | Selection | Status | required, index, has default |  |
| `company_id` | Many2one &rarr; `res.company` | Company | required, index, has default |  |
| `active` | Boolean | Active | has default |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_name_company_uniq` | `UNIQUE(name, company_id)` | The stability study reference must be unique per company. |

### Public methods

| Method | Purpose |
|---|---|
| `create` | Assign the study reference from the dedicated sequence. |
| `unlink` | Forbid the deletion of a study that has left the draft state. |
| `action_generate_schedule` | Generate the recommended time points for the selected studies. |
| `action_open_schedule_wizard` | Open the wizard that generates a stability schedule. |
| `action_start` | Move the selected studies to the ongoing state. |
| `action_complete` | Complete the selected studies. |
| `action_terminate` | Terminate the selected studies before their planned end. |
| `cron_flag_overdue_timepoints` | Post a message on studies that carry an overdue time point. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_date_planned_end` | Compute the planned end from the start date and the duration. |
| `_compute_counts` | Compute the aggregates displayed on the study. |
| `_compute_display_name` | Show the study reference together with its title. |
| `_check_duration` | Reject a non-positive planned duration. |
| `_check_proposed_shelf_life` | Reject a negative proposed shelf life. |
| `_check_batch_product` | Reject a batch that does not carry the product of the study. |
| `_ich_timepoint_months` | Return the time points recommended by ICH Q1A(R2). |

## `ls.pharma.stability.timepoint`

- Python class: `LsPharmaStabilityTimepoint`
- Source: `models/ls_pharma_stability_timepoint.py`
- Description: Stability Study Time Point
- Purpose: A scheduled pull point of a stability study.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `study_id` | Many2one &rarr; `ls.pharma.stability_study` | Study | required, index |  |
| `company_id` | Many2one &rarr; `res.company` | Company | store, index, related=study_id.company_id |  |
| `condition_id` | Many2one &rarr; `ls.pharma.stability.condition` | Storage Condition | required, index |  |
| `month` | Integer | Month | required |  |
| `date_scheduled` | Date | Scheduled Date | required, index |  |
| `date_pulled` | Date | Pulled On |  |  |
| `date_tested` | Date | Tested On |  |  |
| `pulled_by_user_id` | Many2one &rarr; `res.users` | Pulled By |  |  |
| `sample_ids` | One2many &rarr; `ls.pharma.stability.sample` | Samples |  |  |
| `result_ids` | One2many &rarr; `ls.pharma.stability.result` | Results |  |  |
| `result_count` | Integer | Results | store, compute=_compute_result_summary |  |
| `nonconforming_count` | Integer | Non-Conforming Results | store, compute=_compute_result_summary |  |
| `is_overdue` | Boolean | Overdue | store, compute=_compute_is_overdue |  |
| `state` | Selection | Status | required, index, has default |  |
| `remark` | Text | Remark |  |  |

### Database constraints

| Name | Definition | Message |
|---|---|---|
| `_study_condition_month_uniq` | `UNIQUE(study_id, condition_id, month)` | A stability study can only have one time point per storage condition and month. |

### Public methods

| Method | Purpose |
|---|---|
| `action_pull` | Record that the samples of the selected time points were pulled. |
| `action_record_tested` | Record that the selected time points have been tested. |
| `action_complete` | Close the selected time points on the basis of their results. |
| `action_mark_missed` | Mark the selected time points as missed. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_result_summary` | Count the results and the non-conforming results. |
| `_compute_is_overdue` | Flag a time point whose scheduled date has passed unpulled. |
| `_compute_display_name` | Show the month and the condition of the time point. |
| `_check_month` | Reject a negative month. |
| `_check_date_order` | Reject a testing date that precedes the pull date. |

## `extension of 'product.template'`

- Python class: `ProductTemplate`
- Source: `models/product_template.py`
- Inherits: `'product.template'`
- Purpose: Pharmaceutical attributes of a product.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `is_pharmaceutical` | Boolean | Pharmaceutical Product |  |  |
| `pharma_dosage_form` | Selection | Dosage Form |  |  |
| `pharma_strength` | Char | Strength |  |  |
| `pharma_gtin14` | Char | Product Code (GTIN-14) |  |  |
| `pharma_national_number` | Char | National Reimbursement Number |  |  |
| `pharma_marketing_auth_number` | Char | Marketing Authorisation Number |  |  |
| `pharma_marketing_auth_holder_id` | Many2one &rarr; `res.partner` | Marketing Authorisation Holder |  |  |
| `pharma_shelf_life_months` | Integer | Shelf Life (Months) |  |  |
| `pharma_storage_condition` | Char | Storage Condition |  |  |
| `pharma_requires_serialization` | Boolean | Requires Serialisation |  |  |
| `pharma_theoretical_yield_qty` | Float | Theoretical Yield |  |  |
| `pharma_yield_min_percentage` | Float | Minimum Yield (%) |  |  |
| `pharma_yield_max_percentage` | Float | Maximum Yield (%) |  |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_pharma_gtin14` | Reject a product code that is not a valid GTIN-14. |
| `_check_pharma_yield_limits` | Reject yield limits that cannot describe an acceptance range. |
| `_check_pharma_shelf_life` | Reject a negative shelf life. |
| `_check_serialization_requirements` | Require a product code on a product that must be serialised. |

## `extension of 'res.company'`

- Python class: `ResCompany`
- Source: `models/res_company.py`
- Inherits: `'res.company'`
- Purpose: Configuration that applies to every pharmaceutical record of a company.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `pharma_gs1_company_prefix` | Char | GS1 Company Prefix |  |  |
| `pharma_sscc_extension_digit` | Char | SSCC Extension Digit | has default |  |
| `pharma_serial_length` | Integer | Generated Serial Number Length | has default |  |
| `pharma_batch_expiry_alert_days` | Integer | Batch Expiry Alert Horizon (Days) | has default |  |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_gs1_company_prefix` | Reject a company prefix that is not a string of digits. |
| `_check_sscc_extension_digit` | Reject an extension digit that is not a single digit. |
| `_check_serial_length` | Reject a serial length outside the range permitted by AI (21). |
| `_check_expiry_alert_days` | Reject a negative alert horizon. |

## `ls.pharma.batch.release.wizard`

- Python class: `LsPharmaBatchReleaseWizard`
- Source: `wizards/ls_pharma_batch_release_wizard.py`
- Description: Batch Release Decision Wizard
- Purpose: Collect and validate a batch release decision before recording it.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, readonly |  |
| `product_id` | Many2one &rarr; `product.product` | Product | readonly, related=batch_id.product_id |  |
| `batch_state` | Selection | Batch Status | readonly, related=batch_id.state |  |
| `yield_percentage` | Float | Yield (%) | readonly, related=batch_id.yield_percentage |  |
| `yield_investigation_required` | Boolean |  | readonly, related=batch_id.yield_investigation_required |  |
| `decision` | Selection | Decision | required, has default |  |
| `statement` | Text | Decision Statement | required |  |
| `check_record_reviewed` | Boolean | Batch Records Reviewed and Approved |  |  |
| `check_discrepancies_closed` | Boolean | Discrepancies Investigated and Closed |  |  |
| `check_yield_within_limits` | Boolean | Yield Within Limits |  |  |
| `check_components_verified` | Boolean | Component Charge-In Verified by a Second Person |  |  |
| `check_qc_conform` | Boolean | Laboratory Results Conform |  |  |
| `check_labeling_reconciled` | Boolean | Labelling Reconciled |  |  |
| `check_reserve_samples` | Boolean | Reserve Samples Retained |  |  |
| `check_stability_programme` | Boolean | Covered by the Stability Programme |  |  |
| `system_evaluation` | Text | System Evaluation | compute=_compute_system_evaluation |  |

### Public methods

| Method | Purpose |
|---|---|
| `action_confirm` | Record the decision and propagate it to the batch. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_system_evaluation` | Summarise the checks that the system can evaluate on its own. |

## `ls.pharma.serial.generate.wizard`

- Python class: `LsPharmaSerialGenerateWizard`
- Source: `wizards/ls_pharma_serial_generate_wizard.py`
- Description: Serialised Unit Generation Wizard
- Purpose: Generate a requested number of serialised units for a batch.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `batch_id` | Many2one &rarr; `ls.pharma.batch` | Batch | required, readonly |  |
| `product_id` | Many2one &rarr; `product.product` | Product | readonly, related=batch_id.product_id |  |
| `gtin` | Char | Product Code (GTIN-14) | required |  |
| `batch_number` | Char | Batch Number | required |  |
| `expiry_date` | Date | Expiry Date | required |  |
| `national_number` | Char | National Reimbursement Number |  |  |
| `quantity` | Integer | Number of Units | required, has default |  |
| `serial_length` | Integer | Serial Number Length | required |  |

### Public methods

| Method | Purpose |
|---|---|
| `default_get` | Pre-fill the wizard from the batch, the product and the company. |
| `action_generate` | Create the serialised units and open them. |

### Internal methods

| Method | Purpose |
|---|---|
| `_check_quantity` | Reject a non-positive number of units. |
| `_draw_serial` | Draw a serial number that is not present in ``used_serials``. |

## `ls.pharma.stability.schedule.wizard`

- Python class: `LsPharmaStabilityScheduleWizard`
- Source: `wizards/ls_pharma_stability_schedule_wizard.py`
- Description: Stability Schedule Generation Wizard
- Purpose: Propose and create the time points of a stability study.

### Fields

| Field | Type | Label | Attributes | |
|---|---|---|---|---|
| `study_id` | Many2one &rarr; `ls.pharma.stability_study` | Study | required, readonly |  |
| `duration_months` | Integer | Duration (Months) | required |  |
| `condition_ids` | Many2many &rarr; `ls.pharma.stability.condition` | Storage Conditions | required |  |
| `preview` | Text | Proposed Schedule | compute=_compute_preview |  |

### Public methods

| Method | Purpose |
|---|---|
| `default_get` | Pre-fill the wizard from the study it was opened on. |
| `action_generate` | Apply the duration and the conditions, then generate the schedule. |

### Internal methods

| Method | Purpose |
|---|---|
| `_compute_preview` | Build a textual preview of the schedule that would be created. |

