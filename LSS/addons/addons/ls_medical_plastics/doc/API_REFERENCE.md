# API Reference

**Module:** `ls_medical_plastics`  
**Target platform:** Odoo 19.0 Community Edition  
**Licence:** AGPL-3.0-or-later

This reference is generated directly from the module source using the Python
`ast` module. It therefore reflects exactly what is shipped rather than a
hand-maintained description that could drift from the code.

---

## Model index

| Model | Kind | Source | Fields | Methods |
|---|---|---|---|---|
| `ls.mp.component` | New model | `models/mp_component.py` | 29 | 14 |
| `ls.mp.injection_molding` | New model | `models/mp_injection_molding.py` | 44 | 29 |
| `ls.mp.injection_molding.material` | New model | `models/mp_injection_molding_material.py` | 10 | 5 |
| `ls.mp.injection_molding.reading` | New model | `models/mp_injection_molding_reading.py` | 23 | 11 |
| `ls.mp.injection_molding.scrap` | New model | `models/mp_injection_molding_scrap.py` | 10 | 2 |
| `ls.mp.material.grade` | New model | `models/mp_material_grade.py` | 26 | 11 |
| `ls.mp.molding_parameter` | New model | `models/mp_molding_parameter.py` | 25 | 22 |
| `ls.mp.molding_parameter.line` | New model | `models/mp_molding_parameter_line.py` | 16 | 6 |
| `ls.mp.scrap.reason` | New model | `models/mp_scrap_reason.py` | 9 | 1 |
| `ls.mp.tool` | New model | `models/mp_tool.py` | 37 | 22 |
| `ls.mp.tool.cavity` | New model | `models/mp_tool_cavity.py` | 8 | 5 |
| `ls.mp.tool.maintenance` | New model | `models/mp_tool_maintenance.py` | 16 | 9 |
| extends `mrp.production` | Extension | `models/mrp_production.py` | 3 | 2 |
| `ls.mp.reading.wizard` | New model | `wizards/mp_reading_wizard.py` | 4 | 3 |
| `ls.mp.reading.wizard.line` | New model | `wizards/mp_reading_wizard.py` | 15 | 2 |
| `ls.mp.tool.service.wizard` | New model | `wizards/mp_tool_service_wizard.py` | 8 | 2 |
| `ls.mp.traceability.wizard` | New model | `wizards/mp_traceability_wizard.py` | 10 | 6 |

---

## `ls.mp.component`

Moulded component master record.

Defined in `models/mp_component.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `code` | Char | - | yes | - | - | - |
| `product_id` | Many2one | `product.product` | yes | - | - | - |
| `category` | Selection | - | yes | - | - | - |
| `is_primary_packaging` | Boolean | - | - | `_compute_is_primary_packaging` | - | yes |
| `criticality` | Selection | - | yes | - | - | - |
| `drug_contact` | Boolean | - | - | - | - | - |
| `sterile_supply` | Boolean | - | - | - | - | - |
| `sterilization_method` | Selection | - | - | - | - | - |
| `material_grade_ids` | Many2many | `ls.mp.material.grade` | - | - | - | - |
| `primary_material_grade_id` | Many2one | `ls.mp.material.grade` | - | - | - | - |
| `nominal_part_weight` | Float | - | - | - | - | - |
| `part_weight_tolerance` | Float | - | - | - | - | - |
| `part_weight_uom` | Char | - | - | - | - | - |
| `customer_id` | Many2one | `res.partner` | - | - | - | - |
| `drawing_reference` | Char | - | - | - | - | - |
| `drawing_revision` | Char | - | - | - | - | - |
| `specification_reference` | Char | - | - | - | - | - |
| `tool_ids` | Many2many | `ls.mp.tool` | - | - | - | - |
| `tool_count` | Integer | - | - | `_compute_counts` | - | - |
| `parameter_spec_ids` | One2many | `ls.mp.molding_parameter` | - | - | - | - |
| `parameter_spec_count` | Integer | - | - | `_compute_counts` | - | - |
| `approved_spec_count` | Integer | - | - | `_compute_counts` | - | - |
| `run_ids` | One2many | `ls.mp.injection_molding` | - | - | - | - |
| `run_count` | Integer | - | - | `_compute_counts` | - | - |
| `state` | Selection | - | yes | - | - | - |
| `company_id` | Many2one | `res.company` | yes | - | - | - |
| `active` | Boolean | - | - | - | - | - |
| `note` | Text | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_code_company_unique` | `UNIQUE(code, company_id)` |
| `_part_weight_positive` | `CHECK(nominal_part_weight >= 0 AND part_weight_tolerance >= 0)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_is_primary_packaging` | Flag components whose category belongs to the container closure system. |
| `_compute_counts` | Compute the smart-button counters shown on the component form. |
| `_compute_display_name` | Show the component code together with its name. |
| `_check_primary_grade_is_approved` | The primary grade must also appear among the approved grades. |
| `_check_sterilization_method` | A component supplied sterile must declare a sterilisation method. |
| `_check_product_company` | The linked product must belong to the same company, when restricted. |
| `_onchange_sterile_supply` | Clear the sterilisation method when the component is not sterile. |
| `action_release` | Release the component for production use. |
| `action_hold` | Place a released component on hold. |
| `action_set_obsolete` | Mark the component obsolete. |
| `action_reset_to_draft` | Return an obsolete or held component to draft. |
| `action_view_tools` | Open the tools able to produce this component. |
| `action_view_parameter_specs` | Open the moulding parameter specifications of this component. |
| `action_view_runs` | Open the moulding runs recorded for this component. |

---

## `ls.mp.injection_molding`

Execution record of an injection moulding run.

Defined in `models/mp_injection_molding.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `state` | Selection | - | yes | - | - | - |
| `component_id` | Many2one | `ls.mp.component` | yes | - | - | - |
| `tool_id` | Many2one | `ls.mp.tool` | yes | - | - | - |
| `workcenter_id` | Many2one | `mrp.workcenter` | - | - | - | - |
| `production_id` | Many2one | `mrp.production` | - | - | - | - |
| `parameter_spec_id` | Many2one | `ls.mp.molding_parameter` | - | - | - | - |
| `parameter_spec_version` | Integer | - | - | - | - | - |
| `lot_id` | Many2one | `stock.lot` | - | - | - | - |
| `date_start` | Datetime | - | - | - | - | - |
| `date_end` | Datetime | - | - | - | - | - |
| `shift` | Selection | - | - | - | - | - |
| `operator_id` | Many2one | `res.users` | yes | - | - | - |
| `setter_id` | Many2one | `res.users` | - | - | - | - |
| `shot_count_start` | Integer | - | - | - | - | - |
| `shot_count_end` | Integer | - | - | - | - | - |
| `shot_count` | Integer | - | - | `_compute_shot_count` | - | yes |
| `qty_produced` | Float | - | - | - | - | - |
| `qty_rejected` | Float | - | - | `_compute_quantities` | - | yes |
| `qty_startup_scrap` | Float | - | - | `_compute_quantities` | - | yes |
| `qty_good` | Float | - | - | `_compute_quantities` | - | yes |
| `reject_rate` | Float | - | - | `_compute_quantities` | - | yes |
| `material_line_ids` | One2many | `ls.mp.injection_molding.material` | - | - | - | - |
| `reading_ids` | One2many | `ls.mp.injection_molding.reading` | - | - | - | - |
| `scrap_line_ids` | One2many | `ls.mp.injection_molding.scrap` | - | - | - | - |
| `blocked_cavity_ids` | Many2many | `ls.mp.tool.cavity` | - | - | - | - |
| `active_cavity_count` | Integer | - | - | `_compute_active_cavity_count` | - | yes |
| `reading_count` | Integer | - | - | `_compute_reading_statistics` | - | yes |
| `out_of_tolerance_count` | Integer | - | - | `_compute_reading_statistics` | - | yes |
| `critical_out_of_tolerance_count` | Integer | - | - | `_compute_reading_statistics` | - | yes |
| `has_deviation` | Boolean | - | - | `_compute_reading_statistics` | - | yes |
| `deviation_reference` | Char | - | - | - | - | - |
| `setup_by_id` | Many2one | `res.users` | - | - | - | - |
| `setup_date` | Datetime | - | - | - | - | - |
| `startup_verified_by_id` | Many2one | `res.users` | - | - | - | - |
| `startup_verification_date` | Datetime | - | - | - | - | - |
| `reviewed_by_id` | Many2one | `res.users` | - | - | - | - |
| `review_date` | Datetime | - | - | - | - | - |
| `review_comment` | Text | - | - | - | - | - |
| `closed_by_id` | Many2one | `res.users` | - | - | - | - |
| `close_date` | Datetime | - | - | - | - | - |
| `cancellation_reason` | Text | - | - | - | - | - |
| `company_id` | Many2one | `res.company` | yes | - | - | - |
| `note` | Text | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_shot_counters_non_negative` | `CHECK(shot_count_start >= 0 AND shot_count_end >= 0)` |
| `_quantities_non_negative` | `CHECK(qty_produced >= 0)` |
| `_dates_consistent` | `CHECK(date_end IS NULL OR date_start IS NULL OR date_end >= date_start)` |

### Methods

| Method | Purpose |
|---|---|
| `create` | Assign the run reference from the sequence. |
| `_compute_shot_count` | Derive the shots produced from the machine counter readings. |
| `_compute_quantities` | Split produced parts into accepted, rejected and start-up scrap. |
| `_compute_reading_statistics` | Count effective readings and out-of-tolerance results. |
| `_compute_active_cavity_count` | Cavities producing parts during the run. |
| `_compute_display_name` | Render the run as ``REFERENCE - COMPONENT``. |
| `_onchange_component_id` | Restrict the tool selection to tools declared for the component. |
| `_onchange_tool_id` | Default the work centre and preselect the approved specification. |
| `_find_effective_specification` | Return the approved specification applicable to this run context. |
| `_check_tool_produces_component` | The tool must be declared as producing the component. |
| `_check_specification_matches_context` | The specification must belong to the same component and tool. |
| `_check_shot_counter_progression` | The end counter cannot be lower than the start counter. |
| `_check_scrap_not_exceeding_production` | Rejected parts cannot exceed the parts produced. |
| `_check_company_consistency` | Component and tool must belong to the run company. |
| `action_start_setup` | Move the run into setup and freeze the applicable specification. |
| `action_start_startup_check` | Move the run from setup into start-up verification. |
| `action_confirm_startup` | Confirm start-up verification and release the run to production. |
| `_missing_startup_parameters` | Return the names of parameters still awaiting a start-up reading. |
| `_failing_critical_startup_readings` | Return critical parameters that are out of tolerance at start-up. |
| `action_complete` | Complete the run and stop production. |
| `action_review` | Record the quality review of a completed run. |
| `action_close` | Close and freeze the run, advancing the tool shot counter. |
| `action_return_to_draft` | Return a run in setup or start-up verification to draft. |
| `action_reject_review` | Send a completed run back for correction instead of reviewing it. |
| `action_cancel` | Cancel a run that has not yet produced parts. |
| `action_open_reading_wizard` | Open the wizard used to capture a set of parameter readings. |
| `action_view_readings` | Open the readings captured for this run. |
| `write` | Freeze closed runs against any further modification. |
| `unlink` | Allow deletion only for runs that never produced a record of value. |

---

## `ls.mp.injection_molding.material`

One material grade and lot consumed by a moulding run.

Defined in `models/mp_injection_molding_material.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `run_id` | Many2one | `ls.mp.injection_molding` | yes | - | - | - |
| `material_grade_id` | Many2one | `ls.mp.material.grade` | yes | - | - | - |
| `product_id` | Many2one | `product.product` | - | - | - | - |
| `lot_id` | Many2one | `stock.lot` | - | - | - | - |
| `supplier_lot_reference` | Char | - | - | - | - | - |
| `quantity` | Float | - | yes | - | - | - |
| `quantity_uom` | Char | - | yes | - | - | - |
| `is_regrind` | Boolean | - | - | - | - | - |
| `drug_contact` | Boolean | - | - | - | `material_grade_id.drug_contact` | yes |
| `company_id` | Many2one | `res.company` | - | - | `run_id.company_id` | yes |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_quantity_positive` | `CHECK(quantity > 0)` |

### Methods

| Method | Purpose |
|---|---|
| `_onchange_material_grade_id` | Default the product and consumption unit from the selected grade. |
| `_compute_display_name` | Render the line as ``GRADE / LOT``. |
| `_check_grade_is_usable` | Only qualified grades may be consumed. |
| `_check_grade_approved_for_component` | The grade must be approved for the component being moulded. |
| `_check_lot_recorded_for_drug_contact` | Grades in direct drug contact must be traceable to a lot. |

---

## `ls.mp.injection_molding.reading`

One captured value of one moulding parameter.

Defined in `models/mp_injection_molding_reading.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `run_id` | Many2one | `ls.mp.injection_molding` | yes | - | - | - |
| `parameter_line_id` | Many2one | `ls.mp.molding_parameter.line` | yes | - | - | - |
| `reading_type` | Selection | - | yes | - | - | - |
| `capture_date` | Datetime | - | yes | - | - | - |
| `recorded_by_id` | Many2one | `res.users` | yes | - | - | - |
| `value_numeric` | Float | - | - | - | - | - |
| `value_text` | Char | - | - | - | - | - |
| `parameter_name` | Char | - | yes | - | - | - |
| `parameter_code` | Char | - | yes | - | - | - |
| `parameter_uom` | Char | - | - | - | - | - |
| `value_type` | Selection | - | yes | - | - | - |
| `target_value` | Float | - | - | - | - | - |
| `min_value` | Float | - | - | - | - | - |
| `max_value` | Float | - | - | - | - | - |
| `expected_text` | Char | - | - | - | - | - |
| `is_critical` | Boolean | - | - | - | - | - |
| `in_tolerance` | Boolean | - | - | `_compute_in_tolerance` | - | yes |
| `supersedes_id` | Many2one | `ls.mp.injection_molding.reading` | - | - | - | - |
| `superseded_by_ids` | One2many | `ls.mp.injection_molding.reading` | - | - | - | - |
| `is_superseded` | Boolean | - | - | `_compute_is_superseded` | - | - |
| `correction_reason` | Char | - | - | - | - | - |
| `comment` | Char | - | - | - | - | - |
| `company_id` | Many2one | `res.company` | - | - | `run_id.company_id` | yes |

### Methods

| Method | Purpose |
|---|---|
| `_compute_in_tolerance` | Evaluate the captured value against the frozen acceptance criteria. |
| `_compute_is_superseded` | Flag readings that have been corrected by a later entry. |
| `_search_is_superseded` | Translate a search on ``is_superseded`` into one on the inverse field. |
| `_compute_display_name` | Render the reading as ``Parameter @ timestamp``. |
| `_check_correction_reason` | A correcting reading must record why the earlier value was wrong. |
| `_check_correction_consistency` | A correction must target the same run and parameter. |
| `_check_qualitative_value` | A qualitative reading must carry an observed value. |
| `create` | Freeze the acceptance criteria and validate the run state. |
| `_check_run_accepts_readings` | Reject readings captured against a closed or cancelled run. |
| `write` | Block modification of captured readings. |
| `unlink` | Block deletion of captured readings. |

---

## `ls.mp.injection_molding.scrap`

Quantity of parts rejected for one reason during a moulding run.

Defined in `models/mp_injection_molding_scrap.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `run_id` | Many2one | `ls.mp.injection_molding` | yes | - | - | - |
| `reason_id` | Many2one | `ls.mp.scrap.reason` | yes | - | - | - |
| `cavity_id` | Many2one | `ls.mp.tool.cavity` | - | - | - | - |
| `quantity` | Float | - | yes | - | - | - |
| `detected_by_id` | Many2one | `res.users` | - | - | - | - |
| `detection_date` | Datetime | - | yes | - | - | - |
| `is_startup` | Boolean | - | - | - | `reason_id.is_startup` | yes |
| `requires_investigation` | Boolean | - | - | - | `reason_id.requires_investigation` | yes |
| `comment` | Char | - | - | - | - | - |
| `company_id` | Many2one | `res.company` | - | - | `run_id.company_id` | yes |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_quantity_positive` | `CHECK(quantity > 0)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Render the line as ``Reason: quantity``. |
| `_check_cavity_belongs_to_tool` | A cavity may only be cited if it belongs to the tool used. |

---

## `ls.mp.material.grade`

Qualified polymer or masterbatch grade.

Defined in `models/mp_material_grade.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `code` | Char | - | yes | - | - | - |
| `polymer_type` | Selection | - | yes | - | - | - |
| `manufacturer_id` | Many2one | `res.partner` | - | - | - | - |
| `supplier_ids` | Many2many | `res.partner` | - | - | - | - |
| `product_id` | Many2one | `product.product` | - | - | - | - |
| `drug_contact` | Boolean | - | - | - | - | - |
| `food_contact` | Boolean | - | - | - | - | - |
| `regulatory_reference` | Text | - | - | - | - | - |
| `master_file_reference` | Char | - | - | - | - | - |
| `change_notification_agreement` | Boolean | - | - | - | - | - |
| `melt_flow_index` | Float | - | - | - | - | - |
| `melt_flow_index_uom` | Char | - | - | - | - | - |
| `density` | Float | - | - | - | - | - |
| `density_uom` | Char | - | - | - | - | - |
| `recycled_content` | Float | - | - | - | - | - |
| `default_quantity_uom` | Char | - | yes | - | - | - |
| `qualification_state` | Selection | - | yes | - | - | - |
| `qualification_date` | Date | - | - | - | - | - |
| `requalification_date` | Date | - | - | - | - | - |
| `qualification_note` | Text | - | - | - | - | - |
| `component_ids` | Many2many | `ls.mp.component` | - | - | - | - |
| `component_count` | Integer | - | - | `_compute_component_count` | - | - |
| `company_id` | Many2one | `res.company` | yes | - | - | - |
| `active` | Boolean | - | - | - | - | - |
| `note` | Text | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_code_company_unique` | `UNIQUE(code, company_id)` |
| `_recycled_content_range` | `CHECK(recycled_content >= 0 AND recycled_content <= 100)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_component_count` | Count the components declaring this grade. |
| `_compute_display_name` | Show the internal code together with the commercial name. |
| `_check_qualification_date` | A qualified grade must carry the date on which it was qualified. |
| `_check_requalification_after_qualification` | Requalification cannot be scheduled before qualification. |
| `action_set_under_evaluation` | Move draft grades into evaluation. |
| `action_qualify` | Qualify the grade, stamping today's date when none is set. |
| `action_qualify_conditionally` | Qualify the grade subject to conditions recorded in the notes. |
| `action_reject` | Reject the grade. |
| `action_set_obsolete` | Mark the grade obsolete so that it can no longer be consumed. |
| `action_reset_to_draft` | Return a rejected or obsolete grade to draft for rework. |
| `_assert_state_transition` | Raise when any record is not in one of ``allowed_states``. |

---

## `ls.mp.molding_parameter`

Approved moulding process window for a component and tool.

Defined in `models/mp_molding_parameter.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `component_id` | Many2one | `ls.mp.component` | yes | - | - | - |
| `tool_id` | Many2one | `ls.mp.tool` | yes | - | - | - |
| `workcenter_id` | Many2one | `mrp.workcenter` | - | - | - | - |
| `version` | Integer | - | yes | - | - | - |
| `state` | Selection | - | yes | - | - | - |
| `line_ids` | One2many | `ls.mp.molding_parameter.line` | - | - | - | - |
| `parameter_count` | Integer | - | - | `_compute_parameter_counts` | - | yes |
| `critical_parameter_count` | Integer | - | - | `_compute_parameter_counts` | - | yes |
| `author_id` | Many2one | `res.users` | yes | - | - | - |
| `reviewer_id` | Many2one | `res.users` | - | - | - | - |
| `review_date` | Datetime | - | - | - | - | - |
| `approver_id` | Many2one | `res.users` | - | - | - | - |
| `approval_date` | Datetime | - | - | - | - | - |
| `effective_date` | Date | - | - | - | - | - |
| `change_reason` | Text | - | - | - | - | - |
| `previous_version_id` | Many2one | `ls.mp.molding_parameter` | - | - | - | - |
| `review_interval_months` | Integer | - | - | - | - | - |
| `next_review_date` | Date | - | - | `_compute_next_review_date` | - | yes |
| `review_overdue` | Boolean | - | - | `_compute_next_review_date` | - | yes |
| `run_ids` | One2many | `ls.mp.injection_molding` | - | - | - | - |
| `run_count` | Integer | - | - | `_compute_run_count` | - | - |
| `company_id` | Many2one | `res.company` | yes | - | - | - |
| `active` | Boolean | - | - | - | - | - |
| `note` | Text | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_version_positive` | `CHECK(version > 0)` |
| `_review_interval_non_negative` | `CHECK(review_interval_months >= 0)` |

### Methods

| Method | Purpose |
|---|---|
| `create` | Assign the specification reference from the sequence. |
| `_compute_parameter_counts` | Count total and critical parameters. |
| `_compute_run_count` | Count the runs executed against this specification. |
| `_compute_next_review_date` | Derive the periodic review due date for approved specifications. |
| `_compute_display_name` | Render the specification as ``REF - COMPONENT/TOOL v N``. |
| `_check_single_approved_specification` | Only one approved specification may exist per production context. |
| `_check_tool_produces_component` | The tool must be declared as producing the component. |
| `_check_change_reason` | Any version after the first must justify the change. |
| `_check_segregation_of_duties` | Enforce separation between authoring, reviewing and approving. |
| `_check_company_consistency` | Component and tool must belong to the specification company. |
| `action_submit_for_review` | Send a draft specification for review. |
| `action_review` | Record the review of the specification by the current user. |
| `action_approve` | Approve the specification and supersede the previous version. |
| `_supersede_previous_versions` | Move any other approved specification for the same context aside. |
| `action_reject` | Return a specification under review to draft. |
| `action_cancel` | Cancel a specification that has never been approved. |
| `action_set_obsolete` | Withdraw an approved or superseded specification from use. |
| `_has_open_runs` | Return whether runs referencing this specification are still open. |
| `action_create_new_version` | Create the next draft version of this specification. |
| `action_view_runs` | Open the moulding runs executed against this specification. |
| `unlink` | Prevent deletion of specifications that have been approved or used. |
| `_cron_check_specification_review` | Scheduled action flagging approved specifications due for review. |

---

## `ls.mp.molding_parameter.line`

One process parameter within a moulding parameter specification.

Defined in `models/mp_molding_parameter_line.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `spec_id` | Many2one | `ls.mp.molding_parameter` | yes | - | - | - |
| `sequence` | Integer | - | - | - | - | - |
| `name` | Char | - | yes | - | - | - |
| `code` | Char | - | yes | - | - | - |
| `parameter_uom` | Char | - | yes | - | - | - |
| `value_type` | Selection | - | yes | - | - | - |
| `target_value` | Float | - | - | - | - | - |
| `min_value` | Float | - | - | - | - | - |
| `max_value` | Float | - | - | - | - | - |
| `expected_text` | Char | - | - | - | - | - |
| `is_critical` | Boolean | - | - | - | - | - |
| `monitoring_frequency` | Selection | - | yes | - | - | - |
| `record_required` | Boolean | - | - | - | - | - |
| `note` | Text | - | - | - | - | - |
| `state` | Selection | - | - | - | `spec_id.state` | yes |
| `company_id` | Many2one | `res.company` | - | - | `spec_id.company_id` | yes |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_code_spec_unique` | `UNIQUE(spec_id, code)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Render the parameter as ``Name (unit)``. |
| `_check_numeric_range` | Validate that the numeric range is coherent and contains the target. |
| `_check_qualitative_expected` | A qualitative parameter must declare its expected value. |
| `_check_critical_is_recorded` | A critical parameter must always be recorded. |
| `_evaluate_value` | Return whether a captured value satisfies this parameter. |
| `_snapshot_values` | Return the specification values to freeze onto a reading. |

---

## `ls.mp.scrap.reason`

Configurable reason for rejecting moulded parts.

Defined in `models/mp_scrap_reason.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `code` | Char | - | yes | - | - | - |
| `category` | Selection | - | yes | - | - | - |
| `sequence` | Integer | - | - | - | - | - |
| `is_startup` | Boolean | - | - | - | - | - |
| `requires_investigation` | Boolean | - | - | - | - | - |
| `description` | Text | - | - | - | - | - |
| `company_id` | Many2one | `res.company` | - | - | - | - |
| `active` | Boolean | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_code_company_unique` | `UNIQUE(code, company_id)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Render the reason as ``[CODE] Name``. |

---

## `ls.mp.tool`

Moulding tool master record.

Defined in `models/mp_tool.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `code` | Char | - | yes | - | - | - |
| `tool_type` | Selection | - | yes | - | - | - |
| `state` | Selection | - | yes | - | - | - |
| `manufacturer_id` | Many2one | `res.partner` | - | - | - | - |
| `serial_no` | Char | - | - | - | - | - |
| `acquisition_date` | Date | - | - | - | - | - |
| `steel_grade` | Char | - | - | - | - | - |
| `storage_location` | Char | - | - | - | - | - |
| `workcenter_id` | Many2one | `mrp.workcenter` | - | - | - | - |
| `component_ids` | Many2many | `ls.mp.component` | - | - | - | - |
| `cavity_count` | Integer | - | yes | - | - | - |
| `cavity_ids` | One2many | `ls.mp.tool.cavity` | - | - | - | - |
| `active_cavity_count` | Integer | - | - | `_compute_cavity_statistics` | - | yes |
| `blocked_cavity_count` | Integer | - | - | `_compute_cavity_statistics` | - | yes |
| `opening_shot_count` | Integer | - | - | - | - | - |
| `recorded_shot_count` | Integer | - | - | `_compute_shot_counts` | - | yes |
| `total_shot_count` | Integer | - | - | `_compute_shot_counts` | - | yes |
| `shot_count_at_last_maintenance` | Integer | - | - | - | - | - |
| `shots_since_maintenance` | Integer | - | - | `_compute_maintenance_status` | - | yes |
| `shots_to_next_maintenance` | Integer | - | - | `_compute_maintenance_status` | - | yes |
| `maintenance_interval_shots` | Integer | - | - | - | - | - |
| `maintenance_interval_months` | Integer | - | - | - | - | - |
| `last_maintenance_date` | Date | - | - | - | - | - |
| `next_maintenance_date` | Date | - | - | `_compute_maintenance_status` | - | yes |
| `maintenance_status` | Selection | - | - | `_compute_maintenance_status` | - | yes |
| `qualification_date` | Date | - | - | - | - | - |
| `requalification_interval_months` | Integer | - | - | - | - | - |
| `requalification_due_date` | Date | - | - | `_compute_requalification_due` | - | yes |
| `requalification_overdue` | Boolean | - | - | `_compute_requalification_due` | - | yes |
| `maintenance_ids` | One2many | `ls.mp.tool.maintenance` | - | - | - | - |
| `maintenance_count` | Integer | - | - | `_compute_relation_counts` | - | - |
| `run_ids` | One2many | `ls.mp.injection_molding` | - | - | - | - |
| `run_count` | Integer | - | - | `_compute_relation_counts` | - | - |
| `company_id` | Many2one | `res.company` | yes | - | - | - |
| `active` | Boolean | - | - | - | - | - |
| `note` | Text | - | - | - | - | - |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_code_company_unique` | `UNIQUE(code, company_id)` |
| `_cavity_count_positive` | `CHECK(cavity_count > 0)` |
| `_counters_non_negative` | `CHECK(opening_shot_count >= 0 AND shot_count_at_last_maintenance >= 0)` |
| `_intervals_non_negative` | `CHECK(maintenance_interval_shots >= 0 AND maintenance_interval_months >= 0 AND requalification_interval_months >= 0)` |

### Methods

| Method | Purpose |
|---|---|
| `create` | Assign the tool code from the sequence and build the cavity register. |
| `write` | Keep the cavity register aligned with the declared cavity count. |
| `_synchronise_cavity_register` | Create the missing cavity records up to the declared cavity count. |
| `_check_cavity_count_not_reduced` | Refuse a cavity count lower than the cavities already registered. |
| `_compute_cavity_statistics` | Count active and blocked cavities. |
| `_compute_shot_counts` | Accumulate shots from closed runs only. |
| `_compute_maintenance_status` | Derive maintenance counters, due date and traffic-light status. |
| `_evaluate_maintenance_status` | Return the maintenance traffic-light value for this tool. |
| `_compute_requalification_due` | Derive the requalification due date and overdue flag. |
| `_compute_relation_counts` | Compute smart-button counters. |
| `_compute_display_name` | Show the tool code together with its name. |
| `_check_qualification_recorded` | A tool cannot enter service without a recorded qualification date. |
| `action_qualify` | Record the tool as qualified. |
| `action_place_in_service` | Release the tool for production. |
| `action_send_to_maintenance` | Take the tool out of production for maintenance. |
| `action_quarantine` | Quarantine the tool, blocking any further production. |
| `action_decommission` | Permanently withdraw the tool from service. |
| `action_open_service_wizard` | Open the wizard used to return the tool to service after maintenance. |
| `_has_open_runs` | Return whether the tool has runs that are neither closed nor cancelled. |
| `action_view_runs` | Open the moulding runs executed with this tool. |
| `action_view_maintenance` | Open the maintenance history of this tool. |
| `_cron_check_tool_status` | Scheduled action flagging tools due for maintenance or requalification. |

---

## `ls.mp.tool.cavity`

Individual cavity of a moulding tool.

Defined in `models/mp_tool_cavity.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `tool_id` | Many2one | `ls.mp.tool` | yes | - | - | - |
| `number` | Integer | - | yes | - | - | - |
| `label` | Char | - | - | - | - | - |
| `state` | Selection | - | yes | - | - | - |
| `blocked_reason` | Text | - | - | - | - | - |
| `blocked_date` | Datetime | - | - | - | - | - |
| `blocked_by_id` | Many2one | `res.users` | - | - | - | - |
| `company_id` | Many2one | `res.company` | - | - | `tool_id.company_id` | yes |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_tool_number_unique` | `UNIQUE(tool_id, number)` |
| `_number_positive` | `CHECK(number > 0)` |

### Methods

| Method | Purpose |
|---|---|
| `_compute_display_name` | Render the cavity as ``TOOLCODE/NN``. |
| `_check_blocked_reason` | A blocked or removed cavity must record why. |
| `action_block` | Block the cavity, stamping the acting user and timestamp. |
| `action_unblock` | Return a blocked cavity to active service. |
| `action_remove` | Mark the cavity permanently removed from the tool. |

---

## `ls.mp.tool.maintenance`

Maintenance intervention performed on a moulding tool.

Defined in `models/mp_tool_maintenance.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `name` | Char | - | yes | - | - | - |
| `tool_id` | Many2one | `ls.mp.tool` | yes | - | - | - |
| `maintenance_type` | Selection | - | yes | - | - | - |
| `state` | Selection | - | yes | - | - | - |
| `date_planned` | Date | - | yes | - | - | - |
| `date_start` | Datetime | - | - | - | - | - |
| `date_end` | Datetime | - | - | - | - | - |
| `shot_count_at_event` | Integer | - | - | - | - | - |
| `performed_by_id` | Many2one | `res.users` | - | - | - | - |
| `external_provider_id` | Many2one | `res.partner` | - | - | - | - |
| `findings` | Text | - | - | - | - | - |
| `actions_taken` | Text | - | - | - | - | - |
| `cavity_ids` | Many2many | `ls.mp.tool.cavity` | - | - | - | - |
| `requalification_required` | Boolean | - | - | - | - | - |
| `resets_maintenance_counter` | Boolean | - | - | - | - | - |
| `company_id` | Many2one | `res.company` | - | - | `tool_id.company_id` | yes |

### SQL constraints

Declared with `models.Constraint`, which replaces `_sql_constraints` in Odoo 19.

| Name | Definition |
|---|---|
| `_dates_consistent` | `CHECK(date_end IS NULL OR date_start IS NULL OR date_end >= date_start)` |
| `_shot_count_non_negative` | `CHECK(shot_count_at_event >= 0)` |

### Methods

| Method | Purpose |
|---|---|
| `create` | Assign the maintenance reference from the sequence. |
| `_compute_display_name` | Render the event as ``REFERENCE - TOOLCODE``. |
| `_check_actions_recorded` | A completed intervention must record what was done. |
| `action_start` | Start the intervention and snapshot the current tool shot count. |
| `action_done` | Complete the intervention and update the tool maintenance baseline. |
| `_apply_to_tool` | Push the outcome of a completed intervention onto the tool record. |
| `action_cancel` | Cancel a maintenance event that has not been completed. |
| `action_reset_to_draft` | Return a cancelled event to draft. |
| `unlink` | Prevent deletion of completed maintenance events. |

---

## Extension of `mrp.production`

Add moulding run navigation to manufacturing orders.

Defined in `models/mrp_production.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `mp_run_ids` | One2many | `ls.mp.injection_molding` | - | - | - | - |
| `mp_run_count` | Integer | - | - | `_compute_mp_run_count` | - | - |
| `mp_open_run_count` | Integer | - | - | `_compute_mp_run_count` | - | - |

### Methods

| Method | Purpose |
|---|---|
| `_compute_mp_run_count` | Count attached moulding runs and those not yet closed. |
| `action_view_mp_runs` | Open the moulding runs attached to this manufacturing order. |

---

## `ls.mp.reading.wizard`

Capture several parameter readings for a moulding run at once.

Defined in `wizards/mp_reading_wizard.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `run_id` | Many2one | `ls.mp.injection_molding` | yes | - | - | - |
| `reading_type` | Selection | - | yes | - | - | - |
| `line_ids` | One2many | `ls.mp.reading.wizard.line` | - | - | - | - |
| `comment` | Char | - | - | - | - | - |

### Methods

| Method | Purpose |
|---|---|
| `default_get` | Pre-load the wizard with the parameters of the run specification. |
| `_onchange_run_id` | Default the reading type from the current state of the run. |
| `action_record` | Create the readings selected for capture. |

---

## `ls.mp.reading.wizard.line`

One parameter row of the reading capture wizard.

Defined in `wizards/mp_reading_wizard.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `wizard_id` | Many2one | `ls.mp.reading.wizard` | yes | - | - | - |
| `parameter_line_id` | Many2one | `ls.mp.molding_parameter.line` | yes | - | - | - |
| `sequence` | Integer | - | - | - | `parameter_line_id.sequence` | - |
| `parameter_name` | Char | - | - | - | `parameter_line_id.name` | - |
| `parameter_uom` | Char | - | - | - | `parameter_line_id.parameter_uom` | - |
| `value_type` | Selection | - | - | - | `parameter_line_id.value_type` | - |
| `target_value` | Float | - | - | - | `parameter_line_id.target_value` | - |
| `min_value` | Float | - | - | - | `parameter_line_id.min_value` | - |
| `max_value` | Float | - | - | - | `parameter_line_id.max_value` | - |
| `is_critical` | Boolean | - | - | - | `parameter_line_id.is_critical` | - |
| `capture` | Boolean | - | - | - | - | - |
| `value_numeric` | Float | - | - | - | - | - |
| `value_text` | Char | - | - | - | - | - |
| `supersedes_id` | Many2one | `ls.mp.injection_molding.reading` | - | - | - | - |
| `correction_reason` | Char | - | - | - | - | - |

### Methods

| Method | Purpose |
|---|---|
| `_check_correction_reason` | A correction must always state its reason. |
| `_prepare_reading_values` | Build the values used to create the moulding parameter reading. |

---

## `ls.mp.tool.service.wizard`

Confirm the conditions for returning a tool to production.

Defined in `wizards/mp_tool_service_wizard.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `tool_id` | Many2one | `ls.mp.tool` | yes | - | - | - |
| `tool_state` | Selection | - | - | - | `tool_id.state` | - |
| `cavity_ids` | Many2many | `ls.mp.tool.cavity` | - | - | - | - |
| `blocked_cavity_ids` | Many2many | `ls.mp.tool.cavity` | - | - | - | - |
| `requalification_performed` | Boolean | - | - | - | - | - |
| `qualification_date` | Date | - | - | - | - | - |
| `reset_maintenance_baseline` | Boolean | - | - | - | - | - |
| `confirmation_note` | Text | - | - | - | - | - |

### Methods

| Method | Purpose |
|---|---|
| `_onchange_tool_id` | Pre-select the currently active cavities of the tool. |
| `action_return_to_service` | Return the tool to production after validating the conditions. |

---

## `ls.mp.traceability.wizard`

Resolve the genealogy of moulded components.

Defined in `wizards/mp_traceability_wizard.py`.

### Fields

| Field | Type | Comodel | Required | Computed | Related | Stored |
|---|---|---|---|---|---|---|
| `search_mode` | Selection | - | yes | - | - | - |
| `lot_id` | Many2one | `stock.lot` | - | - | - | - |
| `material_lot_id` | Many2one | `stock.lot` | - | - | - | - |
| `component_id` | Many2one | `ls.mp.component` | - | - | - | - |
| `tool_id` | Many2one | `ls.mp.tool` | - | - | - | - |
| `date_from` | Date | - | - | - | - | - |
| `date_to` | Date | - | - | - | - | - |
| `include_open_runs` | Boolean | - | - | - | - | - |
| `run_ids` | Many2many | `ls.mp.injection_molding` | - | - | - | - |
| `run_count` | Integer | - | - | - | - | - |

### Methods

| Method | Purpose |
|---|---|
| `_check_period` | The period end cannot precede its start. |
| `_build_domain` | Build the search domain matching the selected enquiry mode. |
| `action_search` | Resolve the matching runs and reopen the wizard with the result. |
| `action_open_runs` | Open the matching runs in a list view. |
| `action_print` | Print the moulding run record for every matching run. |
| `_collect_genealogy` | Return the resolved genealogy of the matching runs. |

---

**Totals:** 17 model definitions, 293 fields.

