# API Reference — `ls_medical_device`

This document is generated from the module source with the Python
`ast` module. It is not maintained by hand, so it cannot drift from
the code it describes.

Generated: 2026-08-01

---

## Model index

| Model | Description | Source |
|---|---|---|
| `ls.md.ce_marking` | CE Marking and Declaration of Conformity | `ce_marking.py` |
| `ls.md.clinical_evaluation` | Medical Device Clinical Evaluation | `clinical_evaluation.py` |
| `ls.md.clinical_evidence_source` | Clinical Evidence Source | `clinical_evaluation.py` |
| `ls.md.device` | Medical Device | `device.py` |
| `ls.md.device_class` | Medical Device Risk Class | `device_class.py` |
| `ls.md.notified_body` | Notified Body | `notified_body.py` |
| `ls.md.pmcf_evaluation` | PMCF Evaluation Report | `pmcf_evaluation.py` |
| `ls.md.pms` | Post-Market Surveillance Plan | `pms.py` |
| `ls.md.pms_report` | Periodic Post-Market Report | `pms_report.py` |
| `ls.md.risk_assessment` | Medical Device Risk Management File | `risk_assessment.py` |
| `ls.md.risk_item` | Medical Device Risk | `risk_item.py` |
| `ls.md.technical_file` | Medical Device Technical Documentation | `technical_file.py` |
| `ls.md.technical_file_section_template` | Technical Documentation Section Template | `technical_file_section.py` |
| `ls.md.technical_file_section` | Technical Documentation Section | `technical_file_section.py` |
| `ls.md.udi` | Unique Device Identification Assignment | `udi.py` |
| `ls.md.device.state.wizard` | Medical Device Status Change Wizard | `device_state_wizard.py` |
| `ls.md.pms.report.wizard` | Periodic Post-Market Report Wizard | `pms_report_wizard.py` |

---

## `ls.md.ce_marking`

**Class:** `LsMdCeMarking` — **Source:** `ce_marking.py`

**Description:** CE Marking and Declaration of Conformity

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, issue_date desc, id desc`

### Fields (22)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `state` | Selection | Status | required, tracked |
| `conformity_route` | Selection | Conformity Assessment Route | required, tracked |
| `notified_body_id` | Many2one | Notified Body | tracked, -> `ls.md.notified_body` |
| `certificate_number` | Char | Certificate Number | tracked |
| `declaration_number` | Char | Declaration of Conformity Number | tracked |
| `declaration_date` | Date | Declaration Date | tracked |
| `basic_udi_di` | Char | Basic UDI-DI | related `device_id.basic_udi_di`, stored |
| `issue_date` | Date | Certificate Issue Date | tracked |
| `expiry_date` | Date | Certificate Expiry Date | tracked |
| `days_to_expiry` | Integer | Days to Expiry | compute `_compute_expiry_status` |
| `is_expired` | Boolean | Expired | compute `_compute_expiry_status` |
| `ce_marking_affixed` | Boolean | CE Marking Affixed | tracked |
| `ce_marking_date` | Date | CE Marking Date |  |
| `scope` | Text | Scope |  |
| `conditions` | Text | Conditions and Restrictions |  |
| `suspension_reason` | Text | Suspension or Withdrawal Reason | tracked |
| `suspension_date` | Date | Suspension or Withdrawal Date | tracked |
| `surveillance_audit_due` | Date | Next Surveillance Audit Due |  |
| `notes` | Text | Notes |  |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_certificate_number_unique` | `UNIQUE(certificate_number, company_id)` | The certificate number must be unique within a company. |
| `_validity_order` | `CHECK(expiry_date IS NULL OR issue_date IS NULL OR expiry_date >= issue_date)` | The certificate expiry date cannot precede its issue date. |

### Methods (17)

- **`_compute_expiry_status`** — Derive the remaining validity of the certificate.
- **`_search_is_expired`** — Allow searching on the computed expiry flag.
- **`_compute_display_name`** — Show the certificate number when available.
- **`_check_notified_body_required`** — Require a notified body for routes that involve one.
- **`_check_issued_certificate_details`** — Require certificate details once the certificate is issued.
- **`_check_ce_marking_date`** — Require a date whenever the CE marking is declared affixed.
- **`create`** — Allocate the record reference from the dedicated sequence.
- **`write`** — Freeze the certificate identity once it has been issued.
- **`unlink`** — Prevent deletion of records that left the draft status.
- **`copy_data`** — Reset identifiers and status when duplicating a certificate record.
- **`_check_regulatory_authority`** — Raise unless the current user holds regulatory authority.
- **`action_submit`** — Record submission of the application to the notified body.
- **`action_mark_issued`** — Record issuance of the certificate.
- **`action_activate`** — Move an issued certificate into the valid status.
- **`action_suspend`** — Suspend a valid certificate.
- **`action_withdraw`** — Withdraw a certificate.
- **`_cron_expire_certificates`** — Move certificates past their expiry date into the expired status.

---

## `ls.md.clinical_evaluation`

**Class:** `LsMdClinicalEvaluation` — **Source:** `clinical_evaluation.py`

**Description:** Medical Device Clinical Evaluation

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, version desc, id desc`

### Fields (34)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `title` | Char | Title | required, tracked |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `version` | Integer | Version | required, tracked |
| `state` | Selection | Status | required, tracked |
| `evaluator_id` | Many2one | Evaluator | tracked, -> `res.users` |
| `evaluator_qualification` | Text | Evaluator Qualification |  |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `plan_scope` | Text | Plan Scope |  |
| `gspr_requiring_clinical_data` | Text | Requirements Supported by Clinical Data |  |
| `intended_clinical_benefits` | Text | Intended Clinical Benefits |  |
| `target_population` | Text | Target Population |  |
| `acceptance_criteria` | Text | Acceptance Criteria |  |
| `literature_search_protocol` | Text | Literature Search Protocol |  |
| `evidence_source_ids` | Many2many | Clinical Evidence Sources | -> `ls.md.clinical_evidence_source` |
| `equivalence_claimed` | Boolean | Equivalence Claimed | tracked |
| `equivalent_device_description` | Text | Equivalent Device |  |
| `equivalence_demonstration` | Text | Equivalence Demonstration |  |
| `clinical_investigation_performed` | Boolean | Clinical Investigation Performed | tracked |
| `clinical_investigation_reference` | Char | Clinical Investigation Reference |  |
| `clinical_investigation_justification` | Text | Justification for Not Performing an Investigation |  |
| `data_appraisal` | Text | Appraisal of Clinical Data |  |
| `data_analysis` | Text | Analysis of Clinical Data |  |
| `benefit_risk_conclusion` | Text | Benefit-Risk Conclusion | tracked |
| `conformity_confirmed` | Boolean | Conformity With Requirements Confirmed | tracked |
| `residual_gaps` | Text | Residual Gaps in Clinical Evidence |  |
| `pmcf_applicable` | Boolean | PMCF Applicable | tracked |
| `pmcf_plan_summary` | Text | PMCF Plan Summary |  |
| `pmcf_justification` | Text | Justification for Not Applying PMCF |  |
| `next_review_date` | Date | Next Review Due | tracked |
| `pmcf_evaluation_ids` | One2many | PMCF Evaluation Reports | -> `ls.md.pmcf_evaluation` |
| `notes` | Text | Notes |  |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_version_positive` | `CHECK(version > 0)` | The clinical evaluation version must be strictly positive. |
| `_device_version_unique` | `UNIQUE(device_id, version)` | A device cannot have two clinical evaluations with the same version. |

### Methods (14)

- **`_compute_display_name`** — Show the reference, the title and the version.
- **`_check_equivalence_demonstration`** — Require a demonstration whenever equivalence is claimed.
- **`_check_pmcf_documentation`** — Require either a PMCF plan summary or a justification.
- **`_check_clinical_investigation`** — Require a reference or a justification for the investigation status.
- **`create`** — Allocate the evaluation reference from the dedicated sequence.
- **`write`** — Freeze the technical content of an approved evaluation.
- **`unlink`** — Prevent deletion of approved or superseded evaluations.
- **`copy_data`** — Create the next version of the evaluation when duplicating.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft evaluation to review.
- **`action_approve`** — Approve the clinical evaluation.
- **`action_supersede`** — Mark an approved evaluation as superseded.
- **`action_cancel`** — Cancel an evaluation that will not be completed.
- **`action_reset_to_draft`** — Return an evaluation under review to draft.

---

## `ls.md.clinical_evidence_source`

**Class:** `LsMdClinicalEvidenceSource` — **Source:** `clinical_evaluation.py`

**Description:** Clinical Evidence Source

**Default order:** `sequence, name`

### Fields (5)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Name | required |
| `code` | Char | Code | required |
| `sequence` | Integer | Sequence |  |
| `active` | Boolean | Active |  |
| `description` | Text | Description |  |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_code_unique` | `UNIQUE(code)` | The clinical evidence source code must be unique. |

---

## `ls.md.device`

**Class:** `LsMdDevice` — **Source:** `device.py`

**Description:** Medical Device

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `reference desc, id desc`

### Fields (50)

| Field | Type | Label | Notes |
|---|---|---|---|
| `reference` | Char | Reference | required, readonly, tracked |
| `name` | Char | Device Name | required, tracked |
| `model_reference` | Char | Model or Catalogue Reference | tracked |
| `basic_udi_di` | Char | Basic UDI-DI | tracked |
| `gmdn_code` | Char | Nomenclature Code |  |
| `product_id` | Many2one | Product | tracked, -> `product.product` |
| `manufacturer_id` | Many2one | Legal Manufacturer | tracked, -> `res.partner` |
| `authorised_representative_id` | Many2one | Authorised Representative | -> `res.partner` |
| `company_id` | Many2one | Company | required, -> `res.company` |
| `active` | Boolean | Active |  |
| `device_class_id` | Many2one | Risk Class | required, tracked, -> `ls.md.device_class` |
| `classification_rule` | Char | Classification Rule | tracked |
| `classification_rationale` | Text | Classification Rationale |  |
| `intended_purpose` | Text | Intended Purpose | tracked |
| `is_implantable` | Boolean | Implantable | tracked |
| `is_sterile` | Boolean | Placed on the Market Sterile |  |
| `is_measuring` | Boolean | Has a Measuring Function |  |
| `is_reusable_surgical` | Boolean | Reusable Surgical Instrument |  |
| `is_software` | Boolean | Software |  |
| `is_custom_made` | Boolean | Custom-Made | tracked |
| `requires_direct_marking` | Boolean | Requires Direct Marking | compute `_compute_requires_direct_marking`, stored |
| `state` | Selection | Status | required, tracked |
| `state_change_reason` | Text | Last Status Change Reason | readonly |
| `market_placement_date` | Date | First Placed on the Market | tracked |
| `market_withdrawal_date` | Date | Withdrawn From the Market | tracked |
| `documentation_retention_years` | Integer | Documentation Retention (Years) | compute `_compute_documentation_retention`, stored |
| `documentation_retention_until` | Date | Retain Documentation Until | compute `_compute_documentation_retention`, stored |
| `udi_ids` | One2many | UDI Assignments | -> `ls.md.udi` |
| `risk_assessment_ids` | One2many | Risk Management Files | -> `ls.md.risk_assessment` |
| `clinical_evaluation_ids` | One2many | Clinical Evaluations | -> `ls.md.clinical_evaluation` |
| `pmcf_evaluation_ids` | One2many | PMCF Evaluation Reports | -> `ls.md.pmcf_evaluation` |
| `technical_file_ids` | One2many | Technical Documentation | -> `ls.md.technical_file` |
| `ce_marking_ids` | One2many | CE Marking Records | -> `ls.md.ce_marking` |
| `pms_ids` | One2many | Post-Market Surveillance Plans | -> `ls.md.pms` |
| `pms_report_ids` | One2many | Periodic Post-Market Reports | -> `ls.md.pms_report` |
| `udi_count` | Integer | UDI Count | compute `_compute_related_counts` |
| `risk_assessment_count` | Integer | Risk File Count | compute `_compute_related_counts` |
| `clinical_evaluation_count` | Integer | Clinical Evaluation Count | compute `_compute_related_counts` |
| `technical_file_count` | Integer | Technical File Count | compute `_compute_related_counts` |
| `ce_marking_count` | Integer | CE Marking Count | compute `_compute_related_counts` |
| `pms_report_count` | Integer | Periodic Report Count | compute `_compute_related_counts` |
| `periodic_report_type` | Selection | Periodic Report Type | compute `_compute_periodic_report_obligation`, stored |
| `periodic_report_interval_months` | Integer | Report Interval (Months) | compute `_compute_periodic_report_obligation`, stored |
| `annual_pmcf_update_required` | Boolean | Annual PMCF Update Required | compute `_compute_periodic_report_obligation`, stored |
| `notified_body_required` | Boolean | Notified Body Required | related `device_class_id.notified_body_required`, stored |
| `last_periodic_report_date` | Date | Last Periodic Report | compute `_compute_periodic_report_status`, stored |
| `next_periodic_report_due` | Date | Next Periodic Report Due | compute `_compute_periodic_report_status`, stored |
| `periodic_report_overdue` | Boolean | Periodic Report Overdue | compute `_compute_periodic_report_status`, stored |
| `active_ce_marking_id` | Many2one | Active Certificate | compute `_compute_active_ce_marking`, stored, -> `ls.md.ce_marking` |
| `ce_certificate_expiry_date` | Date | Certificate Expiry | related `active_ce_marking_id.expiry_date`, stored |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_reference_unique` | `UNIQUE(reference, company_id)` | The device reference must be unique within a company. |
| `_basic_udi_di_unique` | `UNIQUE(basic_udi_di, company_id)` | The Basic UDI-DI must be unique within a company. |

### Methods (29)

- **`_compute_requires_direct_marking`** — Propose direct marking for reusable surgical instruments.
- **`_compute_documentation_retention`** — Derive the documentation retention period and its end date.
- **`_compute_periodic_report_obligation`** — Derive the post-market reporting obligations of the device.
- **`_compute_periodic_report_status`** — Derive the last and next periodic post-market report dates.
- **`_compute_active_ce_marking`** — Select the most recent certificate in an issued or valid state.
- **`_compute_related_counts`** — Count the regulatory records attached to each device.
- **`_compute_display_name`** — Combine the reference and the device name.
- **`_check_market_dates`** — Reject a withdrawal date preceding the placement date.
- **`_check_on_market_requires_placement_date`** — Require a placement date once the device is declared on the market.
- **`_check_custom_made_combination`** — Record a combination that requires documented justification.
- **`create`** — Allocate the device reference from the dedicated sequence.
- **`copy_data`** — Reset identifiers and lifecycle data when duplicating a device.
- **`_check_regulatory_authority`** — Raise unless the current user holds regulatory authority.
- **`_set_state`** — Apply a lifecycle transition and record its justification.
- **`action_start_development`** — Move a device into development.
- **`action_start_conformity_assessment`** — Move a device under development into conformity assessment.
- **`action_place_on_market`** — Declare the device placed on the market.
- **`action_suspend`** — Suspend a device that is on the market.
- **`action_resume`** — Return a suspended device to the market.
- **`action_withdraw`** — Withdraw the device from the market.
- **`action_open_state_wizard`** — Open the wizard used to record a justified status change.
- **`_action_open_related`** — Return an action listing the related records of one device.
- **`action_view_udi`** — Open the UDI assignments of the device.
- **`action_view_risk_assessments`** — Open the risk management files of the device.
- **`action_view_clinical_evaluations`** — Open the clinical evaluations of the device.
- **`action_view_technical_files`** — Open the technical documentation records of the device.
- **`action_view_ce_markings`** — Open the CE marking records of the device.
- **`action_view_pms_reports`** — Open the periodic post-market reports of the device.
- **`_cron_check_post_market_obligations`** — Raise activities for overdue post-market obligations.

---

## `ls.md.device_class`

**Class:** `LsMdDeviceClass` — **Source:** `device_class.py`

**Description:** Medical Device Risk Class

**Default order:** `sequence, code`

### Fields (13)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Name | required |
| `code` | Char | Code | required |
| `sequence` | Integer | Sequence |  |
| `active` | Boolean | Active |  |
| `description` | Text | Description |  |
| `regulatory_framework` | Char | Regulatory Framework | required |
| `notified_body_required` | Boolean | Notified Body Involvement Required |  |
| `notified_body_scope_note` | Text | Notified Body Scope Note |  |
| `periodic_report_type` | Selection | Periodic Post-Market Report | required |
| `periodic_report_interval_months` | Integer | Maximum Report Interval (Months) |  |
| `annual_pmcf_update_required` | Boolean | Annual PMCF Evaluation Update Required |  |
| `device_ids` | One2many | Devices | -> `ls.md.device` |
| `device_count` | Integer | Device Count | compute `_compute_device_count` |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_code_unique` | `UNIQUE(code, regulatory_framework)` | The risk class code must be unique within a regulatory framework. |
| `_interval_non_negative` | `CHECK(periodic_report_interval_months >= 0)` | The maximum report interval cannot be negative. |

### Methods (3)

- **`_compute_device_count`** — Count the devices attached to each risk class.
- **`_compute_display_name`** — Show the code alongside the name to disambiguate similar classes.
- **`action_view_devices`** — Open the devices registered under the selected risk class.

---

## `ls.md.notified_body`

**Class:** `LsMdNotifiedBody` — **Source:** `notified_body.py`

**Description:** Notified Body

**Default order:** `name`

### Fields (11)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Name | required |
| `identification_number` | Char | Identification Number | required |
| `partner_id` | Many2one | Contact | -> `res.partner` |
| `country_id` | Many2one | Country | -> `res.country` |
| `designation_scope` | Text | Designation Scope |  |
| `designation_reference` | Char | Designation Reference |  |
| `designation_verified_date` | Date | Designation Verified On |  |
| `active` | Boolean | Active |  |
| `notes` | Text | Notes |  |
| `ce_marking_ids` | One2many | Certificates | -> `ls.md.ce_marking` |
| `ce_marking_count` | Integer | Certificate Count | compute `_compute_ce_marking_count` |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_identification_number_unique` | `UNIQUE(identification_number)` | The notified body identification number must be unique. |

### Methods (4)

- **`_compute_ce_marking_count`** — Count the certificates issued by each notified body.
- **`_compute_display_name`** — Prefix the notified body name with its identification number.
- **`_check_designation_verified_date`** — Reject a verification date in the future.
- **`action_view_certificates`** — Open the certificates issued by the selected notified body.

---

## `ls.md.pmcf_evaluation`

**Class:** `LsMdPmcfEvaluation` — **Source:** `pmcf_evaluation.py`

**Description:** PMCF Evaluation Report

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, period_end desc, id desc`

### Fields (26)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `clinical_evaluation_id` | Many2one | Clinical Evaluation | tracked, -> `ls.md.clinical_evaluation` |
| `state` | Selection | Status | required, tracked |
| `period_start` | Date | Period Start | required, tracked |
| `period_end` | Date | Period End | required, tracked |
| `annual_update_required` | Boolean | Annual Update Required | related `device_id.annual_pmcf_update_required`, stored |
| `next_update_due` | Date | Next Update Due | compute `_compute_next_update_due`, stored |
| `activities_performed` | Text | PMCF Activities Performed |  |
| `data_collected` | Text | Clinical Data Collected |  |
| `findings` | Text | Main Findings | tracked |
| `new_risks_identified` | Boolean | New or Emerging Risks Identified | tracked |
| `new_risks_description` | Text | New or Emerging Risks |  |
| `off_label_use_observed` | Boolean | Off-Label Use or Misuse Observed |  |
| `off_label_use_description` | Text | Off-Label Use or Misuse |  |
| `benefit_risk_conclusion` | Text | Benefit-Risk Conclusion | tracked |
| `benefit_risk_remains_acceptable` | Boolean | Benefit-Risk Remains Acceptable | tracked |
| `actions_required` | Boolean | Preventive or Corrective Action Required | tracked |
| `actions_description` | Text | Actions |  |
| `clinical_evaluation_update_required` | Boolean | Clinical Evaluation Update Required | tracked |
| `risk_file_update_required` | Boolean | Risk Management File Update Required | tracked |
| `author_id` | Many2one | Author | tracked, -> `res.users` |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `notes` | Text | Notes |  |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_period_order` | `CHECK(period_end >= period_start)` | The period end cannot precede the period start. |

### Methods (15)

- **`_compute_next_update_due`** — Derive the due date of the next annual update.
- **`_compute_display_name`** — Show the reference together with the covered period end.
- **`_check_new_risks_description`** — Require a description when new risks are flagged.
- **`_check_actions_description`** — Require a description when actions are flagged as required.
- **`_check_clinical_evaluation_device`** — Reject a clinical evaluation belonging to another device.
- **`create`** — Allocate the report reference from the dedicated sequence.
- **`write`** — Freeze the content of an approved report.
- **`unlink`** — Prevent deletion of approved or superseded reports.
- **`copy_data`** — Reset the identity and approval of a duplicated report.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft report to review.
- **`action_approve`** — Approve the report and record the approver.
- **`action_supersede`** — Mark an approved report as superseded by a later one.
- **`action_cancel`** — Cancel a report that will not be completed.
- **`action_reset_to_draft`** — Return a report under review to draft.

---

## `ls.md.pms`

**Class:** `LsMdPms` — **Source:** `pms.py`

**Description:** Post-Market Surveillance Plan

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, version desc, id desc`

### Fields (28)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `title` | Char | Title | required, tracked |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `version` | Integer | Version | required, tracked |
| `state` | Selection | Status | required, tracked |
| `effective_date` | Date | Effective From | tracked |
| `responsible_id` | Many2one | Responsible | tracked, -> `res.users` |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `information_sources` | Text | Information Sources |  |
| `collection_process` | Text | Proactive Collection Process |  |
| `indicators_and_thresholds` | Text | Indicators and Thresholds |  |
| `analysis_methods` | Text | Analysis Methods |  |
| `communication_methods` | Text | Communication Methods |  |
| `referenced_procedures` | Text | Referenced Procedures |  |
| `corrective_action_process` | Text | Corrective Action Process |  |
| `traceability_tools` | Text | Traceability Tools |  |
| `pmcf_plan_included` | Boolean | PMCF Plan Included | tracked |
| `pmcf_plan_reference` | Char | PMCF Plan Reference |  |
| `pmcf_not_applicable_justification` | Text | Justification for PMCF Not Applicable |  |
| `periodic_report_type` | Selection | Periodic Report Type | related `device_id.periodic_report_type`, stored |
| `periodic_report_interval_months` | Integer | Report Interval (Months) | related `device_id.periodic_report_interval_months`, stored |
| `report_ids` | One2many | Periodic Reports | -> `ls.md.pms_report` |
| `report_count` | Integer | Report Count | compute `_compute_report_count` |
| `review_frequency_months` | Integer | Plan Review Frequency (Months) |  |
| `next_review_date` | Date | Next Plan Review | tracked |
| `notes` | Text | Notes |  |

### Constraints (3)

| Name | Definition | Message |
|---|---|---|
| `_version_positive` | `CHECK(version > 0)` | The post-market surveillance plan version must be strictly positive. |
| `_device_version_unique` | `UNIQUE(device_id, version)` | A device cannot have two surveillance plans with the same version. |
| `_review_frequency_non_negative` | `CHECK(review_frequency_months >= 0)` | The plan review frequency cannot be negative. |

### Methods (14)

- **`_compute_report_count`** — Count the periodic reports issued under each plan.
- **`_compute_display_name`** — Show the reference, the title and the version.
- **`_check_pmcf_element`** — Require either a PMCF plan reference or a justification.
- **`create`** — Allocate the plan reference from the dedicated sequence.
- **`write`** — Freeze the content of an approved plan.
- **`unlink`** — Prevent deletion of approved or superseded plans.
- **`copy_data`** — Create the next version of the plan when duplicating.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft plan to review.
- **`action_approve`** — Approve the plan once its mandatory elements are recorded.
- **`action_supersede`** — Mark an approved plan as superseded.
- **`action_cancel`** — Cancel a plan that will not be completed.
- **`action_reset_to_draft`** — Return a plan under review to draft.
- **`action_view_reports`** — Open the periodic reports issued under the plan.

---

## `ls.md.pms_report`

**Class:** `LsMdPmsReport` — **Source:** `pms_report.py`

**Description:** Periodic Post-Market Report

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, period_end desc, id desc`

### Fields (32)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `pms_id` | Many2one | Surveillance Plan | tracked, -> `ls.md.pms` |
| `report_type` | Selection | Report Type | required, tracked |
| `state` | Selection | Status | required, tracked |
| `period_start` | Date | Period Start | required, tracked |
| `period_end` | Date | Period End | required, tracked |
| `next_report_due` | Date | Next Report Due | compute `_compute_next_report_due`, stored |
| `benefit_risk_conclusion` | Text | Benefit-Risk Determination Conclusion | tracked |
| `conclusion` | Selection | Conclusion | tracked |
| `pmcf_main_findings` | Text | Main PMCF Findings |  |
| `sales_volume` | Float | Volume of Sales |  |
| `population_estimate` | Text | User Population Estimate |  |
| `complaint_count` | Integer | Complaints Received |  |
| `serious_incident_count` | Integer | Serious Incidents Reported |  |
| `non_serious_incident_count` | Integer | Non-Serious Incidents Recorded |  |
| `fsca_count` | Integer | Field Safety Corrective Actions |  |
| `trend_signal_identified` | Boolean | Trend Signal Identified | tracked |
| `trend_signal_description` | Text | Trend Signal Description |  |
| `data_analysis_summary` | Text | Analysis Summary |  |
| `capa_summary` | Text | Preventive and Corrective Actions |  |
| `risk_file_update_required` | Boolean | Risk Management File Update Required | tracked |
| `clinical_evaluation_update_required` | Boolean | Clinical Evaluation Update Required | tracked |
| `labelling_update_required` | Boolean | Labelling or IFU Update Required | tracked |
| `author_id` | Many2one | Author | tracked, -> `res.users` |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `notified_body_submission_required` | Boolean | Notified Body Submission Required |  |
| `notified_body_submission_date` | Date | Submitted to Notified Body | tracked |
| `notified_body_reference` | Char | Notified Body Submission Reference |  |
| `notes` | Text | Notes |  |

### Constraints (3)

| Name | Definition | Message |
|---|---|---|
| `_period_order` | `CHECK(period_end >= period_start)` | The reporting period end cannot precede its start. |
| `_device_period_unique` | `UNIQUE(device_id, period_start, period_end)` | A device cannot have two reports covering exactly the same period. |
| `_counts_non_negative` | `CHECK(complaint_count >= 0 AND serious_incident_count >= 0 AND non_serious_incident_count >= 0 AND fsca_count >= 0)` | Incident and complaint counts cannot be negative. |

### Methods (17)

- **`_compute_next_report_due`** — Derive the due date of the following periodic report.
- **`_onchange_device_id`** — Propose the report type and the submission obligation.
- **`_compute_display_name`** — Show the reference together with the covered period.
- **`_check_trend_signal_description`** — Require a description when a trend signal is flagged.
- **`_check_plan_device`** — Reject a surveillance plan belonging to another device.
- **`_check_periods_do_not_overlap`** — Reject a reporting period overlapping another report of the device.
- **`create`** — Allocate the report reference and default the report type.
- **`write`** — Freeze the content of an approved report.
- **`unlink`** — Prevent deletion of approved or superseded reports.
- **`copy_data`** — Reset the identity and approval of a duplicated report.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft report to review.
- **`action_approve`** — Approve the report once its regulatory content is recorded.
- **`action_supersede`** — Mark an approved report as superseded by a later revision.
- **`action_cancel`** — Cancel a report that will not be completed.
- **`action_reset_to_draft`** — Return a report under review to draft.
- **`action_record_notified_body_submission`** — Record that the report was submitted to the notified body.

---

## `ls.md.risk_assessment`

**Class:** `LsMdRiskAssessment` — **Source:** `risk_assessment.py`

**Description:** Medical Device Risk Management File

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, version desc, id desc`

### Fields (22)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `title` | Char | Title | required, tracked |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `version` | Integer | Version | required, tracked |
| `state` | Selection | Status | required, tracked |
| `scope` | Text | Scope |  |
| `risk_policy` | Text | Risk Acceptability Policy |  |
| `standard_reference` | Char | Standard Reference |  |
| `assessment_date` | Date | Assessment Date | tracked |
| `responsible_id` | Many2one | Responsible | tracked, -> `res.users` |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `risk_item_ids` | One2many | Risks | -> `ls.md.risk_item` |
| `risk_item_count` | Integer | Risk Count | compute `_compute_risk_statistics`, stored |
| `unacceptable_risk_count` | Integer | Unacceptable Residual Risks | compute `_compute_risk_statistics`, stored |
| `uncontrolled_risk_count` | Integer | Risks Without Control Measure | compute `_compute_risk_statistics`, stored |
| `max_residual_index` | Integer | Highest Residual Risk Index | compute `_compute_risk_statistics`, stored |
| `overall_benefit_risk_conclusion` | Text | Overall Benefit-Risk Conclusion | tracked |
| `overall_risk_acceptable` | Boolean | Overall Residual Risk Acceptable | tracked |
| `production_information_summary` | Text | Production and Post-Production Information |  |
| `notes` | Text | Notes |  |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_version_positive` | `CHECK(version > 0)` | The risk management file version must be strictly positive. |
| `_device_version_unique` | `UNIQUE(device_id, version)` | A device cannot have two risk management files with the same version. |

### Methods (13)

- **`_compute_risk_statistics`** — Aggregate the risk lines into file-level indicators.
- **`_compute_display_name`** — Show the reference, the title and the version.
- **`_check_conclusion_recorded`** — Require an overall conclusion before approval.
- **`create`** — Allocate the file reference from the dedicated sequence.
- **`write`** — Freeze the technical content of an approved file.
- **`unlink`** — Prevent deletion of approved or superseded files.
- **`copy_data`** — Create the next version of the file when duplicating.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft file to review.
- **`action_approve`** — Approve the risk management file.
- **`action_supersede`** — Mark an approved file as superseded by a later version.
- **`action_cancel`** — Cancel a file that will not be completed.
- **`action_reset_to_draft`** — Return a file under review to draft.

---

## `ls.md.risk_item`

**Class:** `LsMdRiskItem` — **Source:** `risk_item.py`

**Description:** Medical Device Risk

**Default order:** `risk_assessment_id, sequence, id`

### Fields (29)

| Field | Type | Label | Notes |
|---|---|---|---|
| `sequence` | Integer | Sequence |  |
| `risk_assessment_id` | Many2one | Risk Management File | required, -> `ls.md.risk_assessment` |
| `device_id` | Many2one | Device | related `risk_assessment_id.device_id`, stored, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `risk_assessment_id.company_id`, stored, -> `res.company` |
| `reference` | Char | Risk Identifier | required |
| `hazard` | Text | Hazard | required |
| `hazard_category` | Char | Hazard Category |  |
| `sequence_of_events` | Text | Foreseeable Sequence of Events |  |
| `hazardous_situation` | Text | Hazardous Situation | required |
| `harm` | Text | Harm | required |
| `affected_party` | Char | Affected Party |  |
| `initial_severity` | Selection | Initial Severity | required |
| `initial_probability` | Selection | Initial Probability | required |
| `initial_index` | Integer | Initial Risk Index | compute `_compute_initial_index`, stored |
| `control_option` | Selection | Control Option |  |
| `control_measure` | Text | Risk Control Measure |  |
| `control_implementation_reference` | Char | Implementation Evidence |  |
| `control_verification_reference` | Char | Effectiveness Evidence |  |
| `control_verified` | Boolean | Effectiveness Verified |  |
| `introduces_new_hazard` | Boolean | Introduces a New Hazard |  |
| `new_hazard_description` | Text | New Hazard Description |  |
| `residual_severity` | Selection | Residual Severity | required |
| `residual_probability` | Selection | Residual Probability | required |
| `residual_index` | Integer | Residual Risk Index | compute `_compute_residual_index`, stored |
| `proposed_acceptability` | Selection | Proposed Acceptability | compute `_compute_proposed_acceptability`, stored |
| `residual_acceptability` | Selection | Residual Acceptability | required |
| `acceptability_justification` | Text | Acceptability Justification |  |
| `disclosed_to_user` | Boolean | Residual Risk Disclosed |  |
| `notes` | Text | Notes |  |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_reference_unique` | `UNIQUE(risk_assessment_id, reference)` | The risk identifier must be unique within a risk management file. |

### Methods (12)

- **`_compute_initial_index`** — Multiply the initial severity by the initial probability.
- **`_compute_residual_index`** — Multiply the residual severity by the residual probability.
- **`_compute_proposed_acceptability`** — Propose an acceptability band from the shipped default matrix.
- **`_compute_display_name`** — Show the risk identifier and the beginning of the hazard text.
- **`_check_residual_not_worse_than_initial`** — Reject a residual risk estimate above the initial estimate.
- **`_check_new_hazard_description`** — Require a description when a new hazard is flagged.
- **`_check_acceptability_justification`** — Require a justification when the decision differs from the proposal.
- **`_check_control_measure_present`** — Require a control measure whenever risk reduction was applied.
- **`_check_parent_editable`** — Raise when the parent risk management file is no longer editable.
- **`create`** — Reject the creation of a risk in a closed file.
- **`write`** — Reject changes to a risk held in a closed file.
- **`unlink`** — Reject deletion of a risk held in a closed file.

---

## `ls.md.technical_file`

**Class:** `LsMdTechnicalFile` — **Source:** `technical_file.py`

**Description:** Medical Device Technical Documentation

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Default order:** `device_id, version desc, id desc`

### Fields (19)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `title` | Char | Title | required, tracked |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `annex_reference` | Selection | Annex | required, tracked |
| `version` | Integer | Version | required, tracked |
| `state` | Selection | Status | required, tracked |
| `compilation_date` | Date | Compilation Date | tracked |
| `responsible_id` | Many2one | Responsible | tracked, -> `res.users` |
| `approver_id` | Many2one | Approved By | readonly, tracked, -> `res.users` |
| `approval_date` | Datetime | Approval Date | readonly, tracked |
| `section_ids` | One2many | Sections | -> `ls.md.technical_file_section` |
| `section_count` | Integer | Section Count | compute `_compute_completeness`, stored |
| `complete_section_count` | Integer | Complete Sections | compute `_compute_completeness`, stored |
| `missing_mandatory_count` | Integer | Missing Mandatory Sections | compute `_compute_completeness`, stored |
| `completeness_ratio` | Float | Completeness | compute `_compute_completeness`, stored |
| `retention_until` | Date | Retain Until | related `device_id.documentation_retention_until`, stored |
| `storage_location` | Char | Storage Location |  |
| `notes` | Text | Notes |  |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_version_positive` | `CHECK(version > 0)` | The technical documentation version must be strictly positive. |
| `_device_annex_version_unique` | `UNIQUE(device_id, annex_reference, version)` | A device cannot have two technical documentation sets with the same annex and version. |

### Methods (14)

- **`_compute_completeness`** — Derive the completeness indicators of the documentation set.
- **`_compute_display_name`** — Show the reference, the title and the version.
- **`_check_custom_made_annex`** — Match the annex to the custom-made status of the device.
- **`create`** — Allocate the reference and seed the section template.
- **`_seed_sections_from_template`** — Copy the shipped section template into a new documentation set.
- **`write`** — Freeze the identity of an approved documentation set.
- **`unlink`** — Prevent deletion of approved or superseded documentation sets.
- **`copy_data`** — Create the next version of the documentation set when duplicating.
- **`_check_approval_authority`** — Raise unless the current user may approve regulatory records.
- **`action_submit_for_review`** — Move a draft documentation set to review.
- **`action_approve`** — Approve the documentation set once all mandatory sections are complete.
- **`action_supersede`** — Mark an approved documentation set as superseded.
- **`action_cancel`** — Cancel a documentation set that will not be completed.
- **`action_reset_to_draft`** — Return a documentation set under review to draft.

---

## `ls.md.technical_file_section_template`

**Class:** `LsMdTechnicalFileSectionTemplate` — **Source:** `technical_file_section.py`

**Description:** Technical Documentation Section Template

**Default order:** `annex_reference, sequence, section_number`

### Fields (7)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Section Title | required |
| `section_number` | Char | Section Number | required |
| `annex_reference` | Selection | Annex | required |
| `sequence` | Integer | Sequence |  |
| `is_mandatory` | Boolean | Mandatory |  |
| `description` | Text | Description |  |
| `active` | Boolean | Active |  |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_annex_section_unique` | `UNIQUE(annex_reference, section_number)` | A section number can appear only once per annex in the template. |

### Methods (1)

- **`_compute_display_name`** — Show the section number followed by its title.

---

## `ls.md.technical_file_section`

**Class:** `LsMdTechnicalFileSection` — **Source:** `technical_file_section.py`

**Description:** Technical Documentation Section

**Default order:** `technical_file_id, sequence, section_number`

### Fields (16)

| Field | Type | Label | Notes |
|---|---|---|---|
| `technical_file_id` | Many2one | Technical Documentation | required, -> `ls.md.technical_file` |
| `device_id` | Many2one | Device | related `technical_file_id.device_id`, stored, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `technical_file_id.company_id`, stored, -> `res.company` |
| `sequence` | Integer | Sequence |  |
| `section_number` | Char | Section Number | required |
| `name` | Char | Section Title | required |
| `description` | Text | Description |  |
| `is_mandatory` | Boolean | Mandatory |  |
| `is_complete` | Boolean | Complete |  |
| `not_applicable` | Boolean | Not Applicable |  |
| `not_applicable_justification` | Text | Justification |  |
| `evidence_reference` | Char | Evidence Reference |  |
| `evidence_location` | Char | Evidence Location |  |
| `responsible_id` | Many2one | Responsible | -> `res.users` |
| `review_date` | Date | Last Reviewed |  |
| `notes` | Text | Notes |  |

### Constraints (1)

| Name | Definition | Message |
|---|---|---|
| `_file_section_unique` | `UNIQUE(technical_file_id, section_number)` | A section number can appear only once in a documentation set. |

### Methods (8)

- **`_compute_display_name`** — Show the section number followed by its title.
- **`_onchange_not_applicable`** — Mark a section that does not apply as complete.
- **`_check_not_applicable_justification`** — Require a justification whenever a section is declared not applicable.
- **`_check_evidence_reference`** — Require an evidence reference before a section can be complete.
- **`_check_parent_editable`** — Raise when the parent documentation set is closed for editing.
- **`create`** — Reject the creation of a section in a closed documentation set.
- **`write`** — Reject changes to a section of a closed documentation set.
- **`unlink`** — Reject deletion of a section of a closed documentation set.

---

## `ls.md.udi`

**Class:** `LsMdUdi` — **Source:** `udi.py`

**Description:** Unique Device Identification Assignment

**Inherits:** `mail.thread`

**Default order:** `device_id, packaging_level, id`

### Fields (26)

| Field | Type | Label | Notes |
|---|---|---|---|
| `name` | Char | Reference | required, readonly |
| `device_id` | Many2one | Device | required, tracked, -> `ls.md.device` |
| `company_id` | Many2one | Company | related `device_id.company_id`, stored, -> `res.company` |
| `udi_kind` | Selection | Identifier Kind | required, tracked |
| `udi_di` | Char | Device Identifier | required, tracked |
| `issuing_entity` | Selection | Issuing Entity | required |
| `issuing_entity_note` | Char | Issuing Entity Note |  |
| `packaging_level` | Selection | Packaging Level | required |
| `quantity_per_package` | Integer | Quantity per Package |  |
| `carrier_type` | Selection | Carrier Type |  |
| `is_direct_marking` | Boolean | Direct Marking |  |
| `direct_marking_identical` | Boolean | Direct Marking Identical to Label |  |
| `pi_lot_number` | Boolean | PI Includes Lot Number |  |
| `pi_serial_number` | Boolean | PI Includes Serial Number |  |
| `pi_manufacturing_date` | Boolean | PI Includes Manufacturing Date |  |
| `pi_expiry_date` | Boolean | PI Includes Expiry Date |  |
| `pi_software_version` | Boolean | PI Includes Software Version |  |
| `pi_component_summary` | Char | Production Identifier Components | compute `_compute_pi_component_summary`, stored |
| `state` | Selection | Status | required, tracked |
| `assignment_date` | Date | Assignment Date | tracked |
| `database_name` | Char | UDI Database |  |
| `database_submission_date` | Date | Submitted On | tracked |
| `database_reference` | Char | Database Reference |  |
| `obsolete_date` | Date | Obsolete Since |  |
| `obsolete_reason` | Text | Obsolescence Reason |  |
| `notes` | Text | Notes |  |

### Constraints (2)

| Name | Definition | Message |
|---|---|---|
| `_udi_di_unique` | `UNIQUE(udi_di, packaging_level, company_id)` | The device identifier must be unique per packaging level and company. |
| `_quantity_positive` | `CHECK(quantity_per_package > 0)` | The quantity per package must be strictly positive. |

### Methods (14)

- **`_compute_pi_component_summary`** — Build a readable list of the selected production identifiers.
- **`_compute_display_name`** — Show the identifier together with its kind.
- **`_check_basic_udi_di_uniqueness_per_device`** — Allow at most one Basic UDI-DI record per device.
- **`_check_issuing_entity_note`** — Require a note when the issuing entity is recorded as 'Other'.
- **`_check_assignment_date`** — Require an assignment date once the identifier leaves draft.
- **`_check_publication_details`** — Require submission details once the identifier is published.
- **`create`** — Allocate the record reference from the dedicated sequence.
- **`write`** — Block edits to the identifier once it has been published.
- **`unlink`** — Prevent deletion of identifiers that left the draft status.
- **`copy_data`** — Reset the identifier and its lifecycle when duplicating.
- **`action_assign`** — Mark the identifier as assigned to the device.
- **`action_publish`** — Mark the identifier as submitted to a UDI database.
- **`action_mark_obsolete`** — Retire the identifier from use.
- **`action_reset_to_draft`** — Return an assigned identifier to draft.

---

## `ls.md.device.state.wizard`

**Class:** `LsMdDeviceStateWizard` — **Source:** `device_state_wizard.py`

**Description:** Medical Device Status Change Wizard

### Fields (5)

| Field | Type | Label | Notes |
|---|---|---|---|
| `device_id` | Many2one | Device | required, -> `ls.md.device` |
| `current_state` | Selection | Current Status | readonly, related `device_id.state` |
| `target_state` | Selection | New Status | required |
| `reason` | Text | Justification | required |
| `effective_date` | Date | Effective Date | required |

### Methods (2)

- **`_onchange_device_id`** — Reset the target status when it is not reachable from the current one.
- **`action_apply`** — Apply the requested transition through the device business methods.

---

## `ls.md.pms.report.wizard`

**Class:** `LsMdPmsReportWizard` — **Source:** `pms_report_wizard.py`

**Description:** Periodic Post-Market Report Wizard

### Fields (5)

| Field | Type | Label | Notes |
|---|---|---|---|
| `device_ids` | Many2many | Devices | required, -> `ls.md.device` |
| `period_start` | Date | Period Start |  |
| `period_end` | Date | Period End | required |
| `use_device_interval` | Boolean | Derive Start From Report Interval |  |
| `created_report_ids` | Many2many | Created Reports | readonly, -> `ls.md.pms_report` |

### Methods (3)

- **`_check_period`** — Reject a period whose end precedes its start.
- **`_compute_period_start_for`** — Return the period start to use for one device.
- **`action_create_reports`** — Create one draft periodic report per selected device.

---
