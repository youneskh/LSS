# Phase 4 — Technical Specification

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS**

---

## 4.1 Module architecture

```
ls_supplier_qualification/
├── __init__.py                 imports models and wizards
├── __manifest__.py             version 19.0.1.0.0, licence AGPL-3
├── README.rst
├── models/                     14 python modules, 18 model classes
├── wizards/                    2 transient models and their form views
├── security/                   groups, ACL matrix, record rules
├── data/                       sequences, standards, categories, criteria,
│                               templates, mail templates, scheduled actions
├── demo/                       fictitious demonstration data
├── views/                      14 view files, one per model plus menus
├── report/                     report actions and three QWeb templates
├── tests/                      common fixtures and 13 test modules
├── tools/                      offline static check and .pot extraction
├── i18n/                       translation template
├── static/description/         icon and banner
└── doc/                        the ten phase documents and the manuals
```

## 4.2 Dependencies

| Dependency | Why |
|------------|-----|
| `base` | Companies, users, partners, sequences, scheduled actions. |
| `mail` | `mail.thread` and `mail.activity.mixin` for chatter, tracking, activities and mail templates. |
| `product` | `product.product` on scope lines and on the purchase scope check. |
| `purchase` | `purchase.order.button_confirm` override. |

**Not declared, on purpose:**

* `purchase_stock` — only the optional delivery-counter button touches the
  bridge fields, and it verifies their presence at run time instead of forcing
  the dependency on every installation.
* `ls_qms`, `ls_audit`, `ls_capa` — see the deviation recorded in Phase 5, §5.5.

No external Python or binary dependency is declared, and none is used: the
module imports only `hashlib`, `json` and `dateutil.relativedelta`, all of
which ship with Odoo's own requirements.

## 4.3 Model inventory


#### `ls.supplier.assessment` — `LsSupplierAssessment`

Source: `models/ls_supplier_assessment.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, readonly, index |
| `qualification_id` | Many2one | required, index, tracking |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `template_id` | Many2one | required, tracking, check_company |
| `assessment_type` | Selection | required, tracking |
| `date` | Date | required, tracking |
| `assessor_id` | Many2one | required, tracking |
| `reviewer_id` | Many2one | readonly, tracking |
| `review_date` | Date | readonly |
| `line_ids` | One2many | - |
| `state` | Selection | required, index, tracking |
| `max_score_per_criterion` | Integer | required, readonly |
| `mandatory_min_score` | Integer | required, readonly |
| `pass_threshold` | Float | required, readonly |
| `conditional_threshold` | Float | required, readonly |
| `total_weighted_score` | Float | store, compute |
| `total_max_weighted_score` | Float | store, compute |
| `score_percent` | Float | store, tracking, compute |
| `mandatory_failed_count` | Integer | store, compute |
| `finding_count` | Integer | store, compute |
| `result` | Selection | store, tracking, compute |
| `conclusion` | Text | tracking |

#### `ls.supplier.assessment.line` — `LsSupplierAssessmentLine`

Source: `models/ls_supplier_assessment.py`

| Field | Type | Attributes |
|-------|------|------------|
| `assessment_id` | Many2one | required, index |
| `company_id` | Many2one | store, index, related |
| `criterion_id` | Many2one | required, check_company |
| `criterion_domain` | Selection | store, related |
| `sequence` | Integer | - |
| `weight` | Float | required |
| `is_mandatory` | Boolean | - |
| `score` | Integer | - |
| `max_score` | Integer | store, related |
| `weighted_score` | Float | store, compute |
| `max_weighted_score` | Float | store, compute |
| `is_conform` | Boolean | store, compute |
| `evidence` | Text | - |
| `comment` | Text | - |
| `is_finding` | Boolean | - |

#### `ls.supplier.assessment.template` — `LsSupplierAssessmentTemplate`

Source: `models/ls_supplier_assessment_template.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required |
| `code` | Char | required |
| `sequence` | Integer | - |
| `active` | Boolean | - |
| `description` | Text | - |
| `category_ids` | Many2many | - |
| `line_ids` | One2many | - |
| `max_score_per_criterion` | Integer | required |
| `mandatory_min_score` | Integer | required |
| `pass_threshold` | Float | required |
| `conditional_threshold` | Float | required |
| `company_id` | Many2one | required, index |
| `line_count` | Integer | compute |

#### `ls.supplier.assessment.template.line` — `LsSupplierAssessmentTemplateLine`

Source: `models/ls_supplier_assessment_template.py`

| Field | Type | Attributes |
|-------|------|------------|
| `template_id` | Many2one | required, index |
| `criterion_id` | Many2one | required, check_company |
| `sequence` | Integer | - |
| `weight` | Float | required |
| `is_mandatory` | Boolean | - |
| `company_id` | Many2one | store, index, related |

#### `ls.supplier.audit` — `LsSupplierAudit`

Source: `models/ls_supplier_audit.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, readonly, index |
| `qualification_id` | Many2one | required, index, tracking |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `audit_type` | Selection | required, tracking |
| `audit_scope` | Text | required |
| `standard_ids` | Many2many | - |
| `planned_date` | Date | required, index, tracking |
| `date_start` | Date | tracking |
| `date_stop` | Date | tracking |
| `lead_auditor_id` | Many2one | required, tracking |
| `auditor_ids` | Many2many | - |
| `auditee_contact_id` | Many2one | - |
| `finding_ids` | One2many | - |
| `state` | Selection | required, index, tracking |
| `outcome` | Selection | tracking |
| `conclusion` | Text | tracking |
| `report_date` | Date | readonly, tracking |
| `response_due_date` | Date | tracking |
| `response_received_date` | Date | readonly |
| `critical_count` | Integer | store, compute |
| `major_count` | Integer | store, compute |
| `minor_count` | Integer | store, compute |
| `observation_count` | Integer | store, compute |
| `open_finding_count` | Integer | store, compute |
| `finding_count` | Integer | store, compute |

#### `ls.supplier.audit.finding` — `LsSupplierAuditFinding`

Source: `models/ls_supplier_audit.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required |
| `sequence` | Integer | - |
| `audit_id` | Many2one | required, index |
| `qualification_id` | Many2one | store, index, related |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `severity` | Selection | required, index, tracking |
| `description` | Text | required |
| `requirement_reference` | Char | - |
| `supplier_response` | Text | - |
| `root_cause` | Text | - |
| `corrective_action` | Text | - |
| `action_due_date` | Date | tracking |
| `implementation_date` | Date | - |
| `verification_method` | Text | - |
| `verified_by_id` | Many2one | readonly |
| `closure_date` | Date | readonly, tracking |
| `closure_comment` | Text | - |
| `state` | Selection | required, index, tracking |

#### `ls.supplier.category` — `LsSupplierCategory`

Source: `models/ls_supplier_category.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required |
| `code` | Char | required |
| `sequence` | Integer | - |
| `active` | Boolean | - |
| `description` | Text | - |
| `criticality` | Selection | required |
| `requires_assessment` | Boolean | - |
| `requires_initial_audit` | Boolean | - |
| `requires_periodic_audit` | Boolean | - |
| `audit_interval_months` | Integer | - |
| `requalification_interval_months` | Integer | required |
| `review_interval_months` | Integer | required |
| `standard_ids` | Many2many | - |
| `company_id` | Many2one | required, index |
| `qualification_ids` | One2many | - |
| `qualification_count` | Integer | compute |

#### `ls.supplier.criterion` — `LsSupplierCriterion`

Source: `models/ls_supplier_criterion.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required |
| `code` | Char | required |
| `sequence` | Integer | - |
| `active` | Boolean | - |
| `domain` | Selection | required |
| `description` | Text | - |
| `default_weight` | Float | required |
| `is_mandatory` | Boolean | - |
| `standard_ids` | Many2many | - |
| `internal_reference` | Char | - |
| `company_id` | Many2one | required, index |

#### `ls.supplier.material` — `LsSupplierMaterial`

Source: `models/ls_supplier_material.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, tracking |
| `sequence` | Integer | - |
| `qualification_id` | Many2one | required, index |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `product_id` | Many2one | tracking, check_company |
| `material_type` | Selection | required, tracking |
| `specification_reference` | Char | - |
| `manufacturing_site` | Char | - |
| `evaluated_batches` | Char | - |
| `state` | Selection | required, index, tracking |
| `qualification_date` | Date | tracking |
| `expiry_date` | Date | tracking |
| `is_expired` | Boolean | compute |
| `suspension_reason` | Text | readonly |
| `notes` | Text | - |

#### `ls.supplier.performance` — `LsSupplierPerformance`

Source: `models/ls_supplier_performance.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, readonly, index |
| `qualification_id` | Many2one | required, index, tracking |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `period_start` | Date | required, tracking |
| `period_end` | Date | required, index, tracking |
| `evaluation_date` | Date | required, tracking |
| `evaluator_id` | Many2one | required, tracking |
| `state` | Selection | required, index, tracking |
| `delivery_total_count` | Integer | - |
| `delivery_late_count` | Integer | - |
| `lot_total_count` | Integer | - |
| `lot_rejected_count` | Integer | - |
| `nonconformity_count` | Integer | - |
| `complaint_count` | Integer | - |
| `otd_percent` | Float | store, compute |
| `quality_percent` | Float | store, compute |
| `documentation_percent` | Float | - |
| `responsiveness_percent` | Float | - |
| `weight_otd` | Float | required |
| `weight_quality` | Float | required |
| `weight_documentation` | Float | required |
| `weight_responsiveness` | Float | required |
| `threshold_a` | Float | required |
| `threshold_b` | Float | required |
| `threshold_c` | Float | required |
| `overall_score` | Float | store, tracking, compute |
| `rating` | Selection | store, tracking, compute |
| `action_required` | Boolean | store, compute |
| `comments` | Text | - |

#### `ls.supplier.qualification` — `LsSupplierQualification`

Source: `models/ls_supplier_qualification.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, readonly, index |
| `partner_id` | Many2one | required, index, tracking, check_company |
| `category_id` | Many2one | required, tracking, check_company |
| `criticality` | Selection | required, store, tracking, compute |
| `responsible_id` | Many2one | required, tracking |
| `company_id` | Many2one | required, index |
| `active` | Boolean | - |
| `color` | Integer | - |
| `notes` | Html | - |
| `state` | Selection | required, index, tracking |
| `registration_date` | Date | required, tracking |
| `approval_date` | Date | readonly, tracking |
| `approved_by_id` | Many2one | readonly, tracking |
| `requalification_interval_months` | Integer | required, store, tracking, compute |
| `expiry_date` | Date | readonly, index, tracking |
| `approval_conditions` | Text | - |
| `suspension_reason` | Text | readonly |
| `disqualification_reason` | Text | readonly |
| `assessment_ids` | One2many | - |
| `audit_ids` | One2many | - |
| `material_ids` | One2many | - |
| `performance_ids` | One2many | - |
| `review_ids` | One2many | - |
| `signature_ids` | One2many | - |
| `assessment_count` | Integer | compute |
| `audit_count` | Integer | compute |
| `material_count` | Integer | compute |
| `performance_count` | Integer | compute |
| `review_count` | Integer | compute |
| `signature_count` | Integer | compute |
| `latest_assessment_id` | Many2one | store, compute |
| `latest_assessment_score` | Float | store, compute |
| `latest_assessment_result` | Selection | store, compute |
| `latest_performance_rating` | Selection | store, compute |
| `latest_performance_score` | Float | store, compute |
| `open_critical_finding_count` | Integer | store, compute |
| `open_major_finding_count` | Integer | store, compute |
| `risk_level` | Selection | store, compute |
| `next_audit_date` | Date | store, index, compute |
| `next_review_date` | Date | store, index, compute |
| `days_to_expiry` | Integer | compute |
| `expiry_status` | Selection | compute |
| `blocking_reasons` | Text | compute |
| `is_ready_for_approval` | Boolean | compute |

#### `ls.supplier.review` — `LsSupplierReview`

Source: `models/ls_supplier_review.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required, readonly, index |
| `qualification_id` | Many2one | required, index, tracking |
| `partner_id` | Many2one | store, index, related |
| `company_id` | Many2one | store, index, related |
| `review_type` | Selection | required, tracking |
| `review_date` | Date | required, index, tracking |
| `reviewer_id` | Many2one | required, tracking |
| `period_start` | Date | required |
| `period_end` | Date | required |
| `assessment_ids` | Many2many | check_company |
| `audit_ids` | Many2many | check_company |
| `performance_ids` | Many2many | check_company |
| `summary` | Text | required |
| `decision` | Selection | required, tracking |
| `decision_justification` | Text | - |
| `new_expiry_date` | Date | - |
| `new_conditions` | Text | - |
| `state` | Selection | required, index, tracking |

#### `ls.supplier.signature` — `LsSupplierSignature`

Source: `models/ls_supplier_signature.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | store, compute |
| `qualification_id` | Many2one | index |
| `res_model` | Char | required, readonly, index |
| `res_id` | Integer | required, readonly, index |
| `signed_record_name` | Char | readonly |
| `user_id` | Many2one | required, readonly, index |
| `login_used` | Char | readonly |
| `signed_on` | Datetime | required, readonly |
| `meaning` | Selection | required, readonly |
| `reason` | Text | readonly |
| `payload` | Text | readonly |
| `sequence_number` | Integer | required, readonly, index |
| `previous_hash` | Char | readonly |
| `record_hash` | Char | required, readonly |
| `company_id` | Many2one | required, readonly, index |

#### `ls.supplier.standard` — `LsSupplierStandard`

Source: `models/ls_supplier_standard.py`

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required |
| `code` | Char | required |
| `issuing_body` | Char | - |
| `scope_note` | Text | - |
| `sequence` | Integer | - |
| `active` | Boolean | - |

#### `inherit purchase.order` — `PurchaseOrder`

Source: `models/purchase_order.py`

| Field | Type | Attributes |
|-------|------|------------|
| `ls_qualification_id` | Many2one | related |
| `ls_qualification_state` | Selection | related |
| `ls_qualification_warning` | Text | compute |

#### `inherit res.company` — `ResCompany`

Source: `models/res_company.py`

| Field | Type | Attributes |
|-------|------|------------|
| `ls_enforce_sod` | Boolean | - |
| `ls_expiry_reminder_days` | Integer | - |
| `ls_audit_response_days` | Integer | - |
| `ls_po_control_level` | Selection | required |
| `ls_po_check_scope` | Boolean | - |
| `ls_perf_weight_otd` | Float | - |
| `ls_perf_weight_quality` | Float | - |
| `ls_perf_weight_documentation` | Float | - |
| `ls_perf_weight_responsiveness` | Float | - |
| `ls_perf_threshold_a` | Float | - |
| `ls_perf_threshold_b` | Float | - |
| `ls_perf_threshold_c` | Float | - |

#### `inherit res.config.settings` — `ResConfigSettings`

Source: `models/res_config_settings.py`

| Field | Type | Attributes |
|-------|------|------------|
| `ls_enforce_sod` | Boolean | related |
| `ls_expiry_reminder_days` | Integer | related |
| `ls_audit_response_days` | Integer | related |
| `ls_po_control_level` | Selection | related |
| `ls_po_check_scope` | Boolean | related |
| `ls_perf_weight_otd` | Float | related |
| `ls_perf_weight_quality` | Float | related |
| `ls_perf_weight_documentation` | Float | related |
| `ls_perf_weight_responsiveness` | Float | related |
| `ls_perf_threshold_a` | Float | related |
| `ls_perf_threshold_b` | Float | related |
| `ls_perf_threshold_c` | Float | related |

#### `inherit res.partner` — `ResPartner`

Source: `models/res_partner.py`

| Field | Type | Attributes |
|-------|------|------------|
| `ls_qualification_ids` | One2many | - |
| `ls_qualification_id` | Many2one | compute |
| `ls_qualification_state` | Selection | compute |
| `ls_qualification_expiry_date` | Date | compute |
| `ls_is_approved_supplier` | Boolean | compute, search |
| `ls_qualification_count` | Integer | compute |

#### `ls.supplier.approve.wizard` — `LsSupplierApproveWizard`

Source: `wizards/ls_supplier_approve_wizard.py`

| Field | Type | Attributes |
|-------|------|------------|
| `qualification_id` | Many2one | required, readonly |
| `partner_id` | Many2one | readonly, related |
| `blocking_reasons` | Text | readonly, related |
| `latest_assessment_score` | Float | readonly, related |
| `open_critical_finding_count` | Integer | readonly, related |
| `decision` | Selection | required |
| `conditions` | Text | - |
| `requalification_interval_months` | Integer | required, store, compute |
| `expiry_date` | Date | required, store, compute |
| `reason` | Text | required |
| `signature_login` | Char | required |

#### `ls.supplier.status.wizard` — `LsSupplierStatusWizard`

Source: `wizards/ls_supplier_status_wizard.py`

| Field | Type | Attributes |
|-------|------|------------|
| `qualification_id` | Many2one | required, readonly |
| `partner_id` | Many2one | readonly, related |
| `current_state` | Selection | readonly, related |
| `action_type` | Selection | required, store, compute |
| `reason` | Text | required |
| `signature_login` | Char | required |

_Total field declarations: 308 across 20 classes._

## 4.4 Constraints

### 4.4.1 SQL constraints

| Model | Name | Definition |
|-------|------|------------|
| `ls.supplier.standard` | `code_uniq` | `UNIQUE(code)` |
| `ls.supplier.category` | `code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.supplier.criterion` | `code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.supplier.criterion` | `weight_positive` | `CHECK(default_weight > 0)` |
| `ls.supplier.assessment.template` | `code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.supplier.assessment.template.line` | `criterion_template_uniq` | `UNIQUE(template_id, criterion_id)` |
| `ls.supplier.assessment.template.line` | `weight_positive` | `CHECK(weight > 0)` |
| `ls.supplier.qualification` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.supplier.qualification` | `requalification_interval_positive` | `CHECK(requalification_interval_months > 0)` |
| `ls.supplier.material` | `product_qualification_uniq` | `UNIQUE(qualification_id, product_id)` |
| `ls.supplier.assessment` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.supplier.assessment.line` | `criterion_assessment_uniq` | `UNIQUE(assessment_id, criterion_id)` |
| `ls.supplier.assessment.line` | `weight_positive` | `CHECK(weight > 0)` |
| `ls.supplier.assessment.line` | `score_positive` | `CHECK(score >= 0)` |
| `ls.supplier.audit` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.supplier.audit.finding` | `name_audit_uniq` | `UNIQUE(audit_id, name)` |
| `ls.supplier.performance` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.supplier.review` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.supplier.signature` | `sequence_company_uniq` | `UNIQUE(company_id, sequence_number)` |

### 4.4.2 Python constraints

| Model | Method | Checks |
|-------|--------|--------|
| `ls.supplier.standard` | `_check_code` | Non-blank code. |
| `ls.supplier.category` | `_check_intervals` | Requalification, review and audit intervals strictly positive. |
| `ls.supplier.criterion` | `_check_default_weight` | Weight strictly positive. |
| `ls.supplier.assessment.template` | `_check_scoring_rules` | Scale positive, minimum inside the scale, thresholds in 0–100 and ordered. |
| `ls.supplier.qualification` | `_check_unique_active_dossier` | One live dossier per supplier and company. |
| `ls.supplier.qualification` | `_check_validity_dates` | Expiry strictly after approval. |
| `ls.supplier.qualification` | `_check_approval_completeness` | Approved state carries date, approver and expiry. |
| `ls.supplier.qualification` | `_check_conditional_approval` | Conditional state carries conditions. |
| `ls.supplier.material` | `_check_dates`, `_check_qualification_date` | Scope validity chronology and mandatory qualification date. |
| `ls.supplier.assessment` | `_check_frozen_rules` | Frozen scale and thresholds coherent. |
| `ls.supplier.assessment` | `_check_reviewer_segregation` | Reviewer differs from assessor when the rule is on. |
| `ls.supplier.assessment.line` | `_check_score_range` | Score inside the frozen scale. |
| `ls.supplier.audit` | `_check_dates`, `_check_report_dates` | Audit and reporting chronology. |
| `ls.supplier.audit` | `_check_outcome_consistency` | No Acceptable outcome with a critical finding. |
| `ls.supplier.audit.finding` | `_check_dates` | Closure after report issue and after implementation. |
| `ls.supplier.audit.finding` | `_check_corrective_action` | Documented action for critical and major findings. |
| `ls.supplier.performance` | `_check_period`, `_check_no_overlap` | Positive period, no overlap between confirmed evaluations. |
| `ls.supplier.performance` | `_check_percentages`, `_check_counters` | Indicators in 0–100, counters non-negative and consistent. |
| `ls.supplier.review` | `_check_period`, `_check_decision_documentation` | Positive period; conditions and justifications where required. |
| `res.company` | `_check_ls_lead_times`, `_check_ls_perf_weights`, `_check_ls_perf_thresholds` | Non-negative lead times, at least one positive weight, ordered thresholds. |

## 4.5 Compute and onchange methods

| Model | Compute | Stored | Depends on |
|-------|---------|--------|------------|
| `ls.supplier.category` | `_compute_qualification_count` | no | `qualification_ids` |
| `ls.supplier.assessment.template` | `_compute_line_count` | no | `line_ids` |
| `ls.supplier.qualification` | `_compute_criticality` | yes, editable | `category_id` |
| `ls.supplier.qualification` | `_compute_requalification_interval_months` | yes, editable | `category_id` |
| `ls.supplier.qualification` | `_compute_counts` | no | six one2many fields |
| `ls.supplier.qualification` | `_compute_latest_assessment` | yes | assessment state, date, score, result |
| `ls.supplier.qualification` | `_compute_latest_performance` | yes | evaluation state, period end, score, rating |
| `ls.supplier.qualification` | `_compute_finding_counts` | yes | finding severity and state |
| `ls.supplier.qualification` | `_compute_risk_level` | yes | criticality, latest result, latest rating, finding counts |
| `ls.supplier.qualification` | `_compute_next_dates` | yes | approval date, category intervals, closed audits, done reviews |
| `ls.supplier.qualification` | `_compute_days_to_expiry` | no | expiry date, state |
| `ls.supplier.qualification` | `_compute_blocking_reasons` | no | state, category rules, evidence |
| `ls.supplier.material` | `_compute_is_expired` | no | expiry date, state |
| `ls.supplier.assessment` | `_compute_scores` | yes | line scores, weights, mandatory flags, frozen rules |
| `ls.supplier.assessment.line` | `_compute_weighted` | yes | score, weight, max score, minimum |
| `ls.supplier.audit` | `_compute_finding_counts` | yes | finding severity and state |
| `ls.supplier.performance` | `_compute_otd_percent` | yes, editable | delivery counters |
| `ls.supplier.performance` | `_compute_quality_percent` | yes, editable | lot counters |
| `ls.supplier.performance` | `_compute_overall_score` | yes | four indicators, four weights, three thresholds |
| `ls.supplier.signature` | `_compute_name` | yes | meaning, record name, sequence number |
| `res.partner` | `_compute_ls_qualification` | **no, deliberately** | dossier state, expiry, active, company |
| `res.partner` | `_compute_ls_qualification_count` | no | `ls_qualification_ids` |
| `purchase.order` | `_compute_ls_qualification_warning` | no | partner status, order lines, state |
| wizards | `_compute_interval`, `_compute_expiry_date`, `_compute_action_type` | yes, editable | wizard inputs |

| Model | Onchange | Effect |
|-------|----------|--------|
| `ls.supplier.assessment.template.line` | `_onchange_criterion_id` | Proposes the criterion weight and mandatory flag. |
| `ls.supplier.assessment` | `_onchange_template_id` | Refreshes the frozen rules while the record is a draft. |
| `ls.supplier.assessment.line` | `_onchange_criterion_id` | Proposes the criterion weight and mandatory flag. |
| `ls.supplier.material` | `_onchange_product_id` | Proposes the product name as the scope designation. |

## 4.6 Security model

### 4.6.1 Groups

| XML id | Name | Implies |
|--------|------|---------|
| `group_ls_supplier_viewer` | Supplier Viewer | — |
| `group_ls_supplier_assessor` | Supplier Assessor | Viewer |
| `group_ls_supplier_manager` | Supplier Manager | Assessor |

No group is granted to new users automatically. Assignment is an explicit
administrative act.

### 4.6.2 Access rights

44 lines in `security/ir.model.access.csv`, three per model plus the two
wizards. The pattern is: Viewer read-only; Assessor read, write, create on
operational models and read-only on configuration models; Manager full.

Two deliberate departures from the pattern:

* `ls.supplier.assessment.line` grants unlink to the Assessor, because removing
  a criterion row from a draft questionnaire is part of conducting the
  assessment.
* `ls.supplier.signature` grants **no** write, create or unlink to any group.
  Entries are written by the application through `sudo()`. A user cannot create
  a signature by hand, and no user interface offers it.

### 4.6.3 Record rules

| Rule | Groups | Operations | Domain |
|------|--------|-----------|--------|
| Multi-company (13 rules, one per company-scoped model) | none, therefore global | all | `[('company_id', 'in', company_ids)]` |
| `ls_supplier_assessment_rule_assessor` | Assessor | write, create | `[('assessor_id', '=', user.id)]` |
| `ls_supplier_assessment_rule_manager` | Manager | write, create, unlink | `[(1, '=', 1)]` |
| `ls_supplier_audit_rule_auditor` | Assessor | write, create | lead auditor or team member |
| `ls_supplier_audit_rule_manager` | Manager | write, create, unlink | `[(1, '=', 1)]` |

Rules attached to different groups combine with OR, so a manager keeps
unrestricted access through the manager rule while an assessor is limited to
their own work.

## 4.7 XML structure

| File | Records |
|------|---------|
| `security/ls_supplier_qualification_groups.xml` | 1 module category, 3 groups |
| `security/ls_supplier_qualification_security.xml` | 17 record rules |
| `data/ir_sequence_data.xml` | 5 sequences, company-independent |
| `data/ls_supplier_standard_data.xml` | 13 framework designations |
| `data/ls_supplier_category_data.xml` | 10 starter categories |
| `data/ls_supplier_criterion_data.xml` | 32 starter criteria |
| `data/ls_supplier_assessment_template_data.xml` | 2 templates, 44 template lines |
| `data/mail_template_data.xml` | 3 mail templates |
| `data/ir_cron_data.xml` | 3 scheduled actions |
| `views/*.xml` | List, form, search, kanban, calendar, graph and pivot views, 16 window actions, 1 server action, 17 menu items |
| `report/*.xml` | 3 report actions, 6 QWeb templates (document plus wrapper) |
| `demo/ls_supplier_demo.xml` | 2 partners, 2 dossiers, 2 scope lines, 1 assessment |

All data files that must survive a module upgrade without being reset carry
`noupdate="1"`: sequences, security rules, starter configuration, mail
templates and scheduled actions. View files do not, so that view fixes are
delivered by an upgrade.

**View syntax note.** All list views use the `<list>` tag and all window
actions use `list` in `view_mode`, following the rename introduced in Odoo 18.
The chatter uses the `<chatter/>` element.

## 4.8 Controllers, services and external API

The module declares **no HTTP controller and no web service**. Everything is
reachable through the standard Odoo external API, because every operation is a
public ORM method on a model. The methods intended for external callers are
listed in `doc/11_api_documentation.md`.

There is no JavaScript and no asset bundle: the module adds no client-side
component, so nothing has to be re-tested against a future OWL change.

## 4.9 Data, demo data and translations

* **Data** is split between configuration that an organisation is expected to
  adapt (categories, criteria, templates) and infrastructure it is not
  (sequences, crons, security). Both are `noupdate`.
* **Demo data** uses `.invalid` e-mail addresses so that no message can ever
  leave a demonstration database, and fictitious company names.
* **Translations**: `i18n/ls_supplier_qualification.pot` contains 511 entries
  extracted offline by `tools/extract_pot.py`. Every user-facing string in
  Python passes through `_()`, and every view label is a translatable
  attribute. Translatable model fields are marked `translate=True`: category
  and criterion names and descriptions, template names and descriptions,
  standard designations and scope notes.

---

**Phase 4 gate: PASS.** No open issue. Phase 5 may start.
