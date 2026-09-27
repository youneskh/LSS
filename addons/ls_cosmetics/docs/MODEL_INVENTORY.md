# Model and Field Inventory

This inventory is generated directly from the module source with Python's `ast` module. It is not maintained by hand, so it cannot drift from the code.

**13 models, 316 fields.**

### `ls.cosmetic.claim`

*Cosmetic Product Claim* — defined in `models/ls_cosmetic_claim.py`, 32 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `state` | Selection |
| `product_tmpl_id` | Many2one |
| `formulation_id` | Many2one |
| `medium` | Char |
| `is_no_animal_testing_claim` | Boolean |
| `animal_testing_declaration` | Text |
| `evidence_ids` | One2many |
| `evidence_count` | Integer |
| `criterion_legal` | Boolean |
| `criterion_legal_note` | Text |
| `criterion_truth` | Boolean |
| `criterion_truth_note` | Text |
| `criterion_evidence` | Boolean |
| `criterion_evidence_note` | Text |
| `criterion_honesty` | Boolean |
| `criterion_honesty_note` | Text |
| `criterion_fairness` | Boolean |
| `criterion_fairness_note` | Text |
| `criterion_informed` | Boolean |
| `criterion_informed_note` | Text |
| `criteria_met_count` | Integer |
| `all_criteria_met` | Boolean |
| `assessed_by_id` | Many2one |
| `assessed_date` | Datetime |
| `approved_by_id` | Many2one |
| `approved_date` | Datetime |
| `decision_reason` | Text |
| `note` | Text |

**Database constraints:** `_code_unique`

**Public actions:** `action_start_substantiation`, `action_approve`, `action_reject`, `action_withdraw`, `action_reset_draft`

### `ls.cosmetic.claim.evidence`

*Cosmetic Claim Evidence* — defined in `models/ls_cosmetic_claim_evidence.py`, 11 field(s).

| Field | Type |
|---|---|
| `claim_id` | Many2one |
| `company_id` | Many2one |
| `reference` | Char |
| `evidence_type` | Selection |
| `evidence_date` | Date |
| `performed_by` | Char |
| `summary` | Text |
| `subject_count` | Integer |
| `is_statistically_significant` | Boolean |
| `attachment_ids` | Many2many |
| `note` | Text |

**Database constraints:** `_subject_count_positive`, `_reference_unique`

### `ls.cosmetic.dz_authorization`

*Algerian Prior Authorisation (Cosmetics)* — defined in `models/ls_cosmetic_dz_authorization.py`, 45 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `state` | Selection |
| `authorization_type` | Selection |
| `product_tmpl_id` | Many2one |
| `pif_id` | Many2one |
| `formulation_id` | Many2one |
| `operator_partner_id` | Many2one |
| `wilaya_direction` | Char |
| `submission_mode` | Selection |
| `submission_date` | Date |
| `receipt_reference` | Char |
| `receipt_date` | Date |
| `decision_due_date` | Date |
| `decision_overdue` | Boolean |
| `decision_date` | Date |
| `authorization_reference` | Char |
| `refusal_reason` | Text |
| `notice_date` | Date |
| `notice_deadline` | Date |
| `notice_subject` | Text |
| `withdrawal_date` | Date |
| `scientific_commission_opinion` | Text |
| `doc_rc` | Boolean |
| `doc_fiscal` | Boolean |
| `doc_statutes` | Boolean |
| `doc_accounts` | Boolean |
| `doc_tax_roll` | Boolean |
| `doc_social` | Boolean |
| `doc_denomination` | Boolean |
| `doc_usage` | Boolean |
| `doc_composition` | Boolean |
| `doc_analyses` | Boolean |
| `doc_toxicity` | Boolean |
| `doc_batch_id` | Boolean |
| `doc_precautions` | Boolean |
| `doc_label_model` | Boolean |
| `doc_responsible` | Boolean |
| `doc_trademark` | Boolean |
| `dossier_complete` | Boolean |
| `dossier_item_count` | Integer |
| `attachment_ids` | Many2many |
| `note` | Text |

**Database constraints:** `_code_unique`

**Public actions:** `action_submit`, `action_register_receipt`, `action_grant`, `action_refuse`, `action_register_notice`, `action_resolve_notice`, `action_withdraw`, `action_reset_draft`

### `ls.cosmetic.formulation`

*Cosmetic Formulation* — defined in `models/ls_cosmetic_formulation.py`, 29 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `version` | Integer |
| `state` | Selection |
| `product_tmpl_id` | Many2one |
| `bom_id` | Many2one |
| `predecessor_id` | Many2one |
| `successor_id` | Many2one |
| `line_ids` | One2many |
| `total_percentage` | Float |
| `line_count` | Integer |
| `intended_use` | Text |
| `target_population` | Text |
| `for_children_under_three` | Boolean |
| `for_intimate_hygiene` | Boolean |
| `contains_nanomaterial` | Boolean |
| `contains_cmr` | Boolean |
| `blocking_finding_count` | Integer |
| `unevaluated_line_count` | Integer |
| `safety_assessment_ids` | One2many |
| `safety_assessment_count` | Integer |
| `submitted_by_id` | Many2one |
| `submitted_date` | Datetime |
| `approved_by_id` | Many2one |
| `approved_date` | Datetime |
| `cancel_reason` | Text |
| `note` | Text |

**Database constraints:** `_code_version_unique`, `_version_positive`

**Public actions:** `action_submit_review`, `action_approve`, `action_reset_draft`, `action_cancel`, `action_open_revise_wizard`, `action_view_safety_assessments`

### `ls.cosmetic.formulation.line`

*Cosmetic Formulation Line* — defined in `models/ls_cosmetic_formulation_line.py`, 13 field(s).

| Field | Type |
|---|---|
| `formulation_id` | Many2one |
| `company_id` | Many2one |
| `sequence` | Integer |
| `ingredient_id` | Many2one |
| `concentration` | Float |
| `function_in_product` | Char |
| `is_nanomaterial` | Boolean |
| `is_perfume_component` | Boolean |
| `regulatory_category` | Selection |
| `exclude_from_label` | Boolean |
| `restriction_status` | Selection |
| `restriction_message` | Char |
| `note` | Text |

**Database constraints:** `_concentration_positive`, `_concentration_max`, `_ingredient_unique`

### `ls.cosmetic.ingredient`

*Cosmetic Ingredient* — defined in `models/ls_cosmetic_ingredient.py`, 26 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `inci_name` | Char |
| `chemical_name` | Char |
| `cas_number` | Char |
| `ec_number` | Char |
| `technical_function` | Char |
| `regulatory_category` | Selection |
| `is_nanomaterial` | Boolean |
| `is_perfume_component` | Boolean |
| `perfume_term` | Selection |
| `perfume_composition_code` | Char |
| `perfume_supplier_id` | Many2one |
| `requires_individual_listing` | Boolean |
| `is_impurity` | Boolean |
| `is_processing_aid` | Boolean |
| `is_cmr` | Boolean |
| `cmr_category` | Selection |
| `colour_index` | Char |
| `restriction_ids` | Many2many |
| `prohibited` | Boolean |
| `supplier_ids` | Many2many |
| `product_id` | Many2one |
| `toxicological_profile` | Text |
| `toxicological_reference` | Char |
| `note` | Text |

**Database constraints:** `_inci_name_unique`

### `ls.cosmetic.label`

*Cosmetic Labelling Particulars* — defined in `models/ls_cosmetic_label.py`, 39 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `version` | Integer |
| `state` | Selection |
| `formulation_id` | Many2one |
| `product_tmpl_id` | Many2one |
| `responsible_person_id` | Many2one |
| `responsible_person_address` | Char |
| `is_imported` | Boolean |
| `country_of_origin_id` | Many2one |
| `nominal_content` | Char |
| `content_exempt` | Boolean |
| `content_exempt_reason` | Char |
| `durability_mode` | Selection |
| `minimum_durability_date` | Date |
| `durability_conditions` | Char |
| `stated_durability_months` | Integer |
| `pao_months` | Integer |
| `precautions` | Text |
| `annex_wording` | Text |
| `is_professional_use` | Boolean |
| `batch_reference_rule` | Char |
| `batch_on_packaging_only` | Boolean |
| `product_function` | Char |
| `function_clear_from_presentation` | Boolean |
| `ingredient_list` | Text |
| `ingredient_list_prefix` | Char |
| `colorants_last` | Boolean |
| `may_contain` | Boolean |
| `ingredient_list_generated_on` | Datetime |
| `information_on_leaflet` | Boolean |
| `notice_in_proximity` | Boolean |
| `language_ids` | Many2many |
| `artwork_attachment_ids` | Many2many |
| `approved_by_id` | Many2one |
| `approved_date` | Datetime |
| `note` | Text |

**Database constraints:** `_code_version_unique`, `_pao_months_positive`, `_durability_months_positive`

**Public actions:** `action_generate_ingredient_list`, `action_submit_review`, `action_approve`, `action_reset_draft`, `action_open_generate_wizard`

### `ls.cosmetic.pif`

*Cosmetic Product Information File* — defined in `models/ls_cosmetic_pif.py`, 41 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `state` | Selection |
| `product_tmpl_id` | Many2one |
| `responsible_person_id` | Many2one |
| `responsible_person_basis` | Selection |
| `mandate_reference` | Char |
| `file_address` | Char |
| `file_language_ids` | Many2many |
| `product_description` | Text |
| `safety_assessment_id` | Many2one |
| `formulation_id` | Many2one |
| `label_id` | Many2one |
| `manufacturing_method` | Text |
| `gmp_statement` | Text |
| `gmp_standard` | Char |
| `gmp_site_id` | Many2one |
| `gmp_certificate_reference` | Char |
| `gmp_certificate_date` | Date |
| `claim_ids` | Many2many |
| `claim_count` | Integer |
| `unapproved_claim_count` | Integer |
| `no_claims_justification` | Text |
| `animal_testing_data` | Text |
| `no_animal_testing` | Boolean |
| `notification_reference` | Char |
| `notification_date` | Date |
| `dz_authorization_ids` | One2many |
| `first_placed_date` | Date |
| `last_batch_market_date` | Date |
| `retention_end_date` | Date |
| `retention_elapsed` | Boolean |
| `last_review_date` | Date |
| `attachment_ids` | Many2many |
| `activated_by_id` | Many2one |
| `activated_date` | Datetime |
| `archived_by_id` | Many2one |
| `archived_date` | Datetime |
| `note` | Text |

**Database constraints:** `_code_unique`

**Public actions:** `action_activate`, `action_enter_retention`, `action_archive_file`, `action_reset_draft`

### `ls.cosmetic.restriction`

*Cosmetic Substance Restriction (Annexes II-VI)* — defined in `models/ls_cosmetic_restriction.py`, 19 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `annex` | Selection |
| `reference_number` | Char |
| `substance_name` | Char |
| `inci_name` | Char |
| `cas_number` | Char |
| `ec_number` | Char |
| `product_type_scope` | Text |
| `max_concentration` | Float |
| `has_numeric_limit` | Boolean |
| `conditions_of_use` | Text |
| `label_wording` | Text |
| `other_column` | Text |
| `source_reference` | Char |
| `consolidation_date` | Date |
| `date_from` | Date |
| `date_to` | Date |
| `note` | Text |

**Database constraints:** `_reference_unique`, `_max_concentration_positive`

### `ls.cosmetic.safety_assessment`

*Cosmetic Product Safety Report* — defined in `models/ls_cosmetic_safety_assessment.py`, 41 field(s).

| Field | Type |
|---|---|
| `active` | Boolean |
| `company_id` | Many2one |
| `code` | Char |
| `name` | Char |
| `version` | Integer |
| `state` | Selection |
| `formulation_id` | Many2one |
| `product_tmpl_id` | Many2one |
| `predecessor_id` | Many2one |
| `part_a_1_composition` | Text |
| `part_a_2_physchem` | Text |
| `part_a_3_microbiology` | Text |
| `part_a_4_impurities` | Text |
| `part_a_5_use` | Text |
| `part_a_6_product_exposure` | Text |
| `part_a_7_substance_exposure` | Text |
| `part_a_8_toxicological` | Text |
| `part_a_9_undesirable_effects` | Text |
| `part_a_10_other_information` | Text |
| `margin_of_safety` | Float |
| `margin_of_safety_basis` | Char |
| `conclusion` | Selection |
| `conclusion_statement` | Text |
| `labelled_warnings` | Text |
| `reasoning` | Text |
| `reasoning_children` | Text |
| `reasoning_intimate_hygiene` | Text |
| `reasoning_interactions` | Text |
| `reasoning_stability_impact` | Text |
| `reasoning_toxicological_scope` | Text |
| `assessor_partner_id` | Many2one |
| `assessor_address` | Char |
| `assessor_qualification` | Char |
| `assessor_qualification_attachment_ids` | Many2many |
| `assessor_user_id` | Many2one |
| `approval_date` | Date |
| `approved_by_id` | Many2one |
| `review_date` | Date |
| `review_overdue` | Boolean |
| `non_clinical_glp_statement` | Text |
| `note` | Text |

**Database constraints:** `_code_version_unique`, `_version_positive`, `_margin_of_safety_positive`

**Public actions:** `action_start_part_a`, `action_start_part_b`, `action_approve`, `action_reset_draft`, `action_cancel`

### `product.template`

*extension of product.template* — defined in `models/product_template.py`, 9 field(s).

| Field | Type |
|---|---|
| `ls_is_cosmetic` | Boolean |
| `ls_formulation_ids` | One2many |
| `ls_formulation_count` | Integer |
| `ls_pif_ids` | One2many |
| `ls_pif_count` | Integer |
| `ls_label_ids` | One2many |
| `ls_label_count` | Integer |
| `ls_claim_ids` | One2many |
| `ls_claim_count` | Integer |

**Public actions:** `action_view_ls_formulations`, `action_view_ls_pifs`, `action_view_ls_labels`, `action_view_ls_claims`

### `ls.cosmetic.formulation.revise`

*Revise Cosmetic Formulation* — defined in `wizards/ls_cosmetic_formulation_revise.py`, 5 field(s).

| Field | Type |
|---|---|
| `formulation_id` | Many2one |
| `current_version` | Integer |
| `new_version` | Integer |
| `change_reason` | Text |
| `copy_lines` | Boolean |

**Public actions:** `action_revise`

### `ls.cosmetic.label.generate`

*Generate Cosmetic Ingredient List* — defined in `wizards/ls_cosmetic_label_generate.py`, 6 field(s).

| Field | Type |
|---|---|
| `label_id` | Many2one |
| `formulation_id` | Many2one |
| `colorants_last` | Boolean |
| `may_contain` | Boolean |
| `preview` | Text |
| `excluded_summary` | Text |

**Public actions:** `action_apply`
