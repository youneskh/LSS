# Regulatory Traceability Matrix

Each row maps one provision to the artefact that supports it and to the test
that exercises that artefact. A row exists only where the module implements
something; no row is written to fill a gap.

**Support is not compliance.** These rows say what the software records and
enforces, not that an organisation using it meets the provision.

## 14.1 21 CFR Part 211

| Provision | Artefact | Test |
|---|---|---|
| 211.101(c) | `ls.pharma.batch.component`: `charged_by_user_id`, `verified_by_user_id`; constraint `_check_second_person_verification` | `test_batch.test_component_verifier_must_differ_from_the_charger` |
| 211.101(d) | `is_automated_charge` suspends the constraint | `test_batch.test_components_carry_the_second_person_verification` |
| 211.103 | `ls.pharma.batch`: `yield_percentage`; guard in `action_complete` | `test_batch.test_yield_percentage`, `test_completion_requires_an_actual_yield` |
| 211.125 | `ls.pharma.batch_record.labeling`: reconciliation fields | `test_batch_record.test_labeling_reconciliation` |
| 211.134 | `examination_result` on the batch record | Covered by the printed record; no dedicated test |
| 211.165 | Release checklist entry `check_qc_conform`; control conformity | `test_batch_record.test_numeric_control_conformity`, `test_batch_release.*` |
| 211.166 | `ls.pharma.stability_study`; checklist entry `check_stability_programme`; conclusion required to complete | `test_stability.test_completion_requires_settled_time_points_and_a_conclusion` |
| 211.170 | Sample type `reserve`; `reserve_sample_count` | `test_batch_record.test_reserve_sample_count` |
| 211.182 | `ls.pharma.batch.equipment`: cleaning record fields | `test_batch.test_related_record_counts` (structural); no dedicated behavioural test |
| 211.186(b)(6) | Product fields for theoretical yield and its limits, proposed onto the batch | `test_batch.test_yield_below_the_lower_limit_requires_an_investigation` |
| 211.188(a) | Master record reference, version, checker and date; guard in `action_start_execution` | `test_batch_record.test_execution_requires_a_checked_master_record` |
| 211.188(b)(1) | Dates on the record and on every line | Structural |
| 211.188(b)(2) | `ls.pharma.batch.equipment` | Structural |
| 211.188(b)(3) | `component_lot_id`, `component_lot_reference` | Structural |
| 211.188(b)(4) | `quantity`, `uom_id`, `assay_percentage`, `compensated_quantity` | `test_batch.test_components_carry_the_second_person_verification` |
| 211.188(b)(5) | `ls.pharma.batch_record.control` | `test_batch_record.test_numeric_control_conformity` |
| 211.188(b)(6) | `ls.pharma.batch_record.clearance`, moments before and after | `test_batch_record.test_line_clearance_before_and_after` |
| 211.188(b)(7) | Actual yield and percentage of theoretical yield | `test_batch.test_yield_percentage` |
| 211.188(b)(8) | `ls.pharma.batch_record.labeling` | `test_batch_record.test_labeling_reconciliation` |
| 211.188(b)(9) | `container_closure_description` | Structural |
| 211.188(b)(10) | `ls.pharma.batch_record.sample` | `test_batch_record.test_reserve_sample_count` |
| 211.188(b)(11) | `is_significant`, `performed_by_user_id`, `checked_by_user_id` | `test_batch_record.test_completion_percentage` |
| 211.188(b)(12) | `ls.pharma.batch_record.discrepancy` | `test_batch_record.test_open_discrepancy_blocks_approval` |
| 211.188(b)(13) | `examination_result`, control results | Structural |
| 211.192 (review and approval) | Guards in `action_approve` and in the release gate | `test_batch_record.test_reviewer_cannot_be_the_executor`, `test_batch_release.test_release_requires_every_record_to_be_approved` |
| 211.192 (investigation) | Open-discrepancy guard; required conclusion and follow-up | `test_batch_record.test_open_discrepancy_blocks_approval`, `test_discrepancy_cannot_be_closed_without_a_conclusion` |
| 211.192 (extension to other batches) | `extended_to_other_batches`, `extension_scope` | Structural, enforced by the closure guard in `action_close` |
| 211.192 (yield discrepancy) | `yield_investigation_required`, `yield_investigation_reference`; release gate | `test_batch_release.test_yield_outside_limits_requires_an_investigation_reference` |
| 211.22 (independence of the quality unit) | Group model; manufacturer and executor separations | `test_security.test_quality_assurance_does_not_imply_production`, `test_batch_release.test_manufacturer_cannot_decide_on_the_batch` |

## 14.2 ICH Q1A(R2)

| Provision | Artefact | Test |
|---|---|---|
| General case storage conditions | Four shipped `ls.pharma.stability.condition` records | `test_stability.test_shipped_conditions_match_the_guideline` |
| Long term frequency | `_ich_timepoint_months`, long term branch | `test_stability.test_long_term_months`, `test_long_term_months_over_thirty_six` |
| Accelerated, minimum three points | `ICH_ACCELERATED_TIMEPOINTS` | `test_stability.test_accelerated_months` |
| Intermediate, minimum four points | `ICH_INTERMEDIATE_TIMEPOINTS` | `test_stability.test_intermediate_months` |
| Significant change | `is_significant_change` on a result, raised to the study | `test_stability.test_significant_change_is_carried_to_the_study` |

## 14.3 ICH M4(R4) and M4Q

| Provision | Artefact | Test |
|---|---|---|
| The five modules | `CTD_MODULES` | `test_ctd.test_template_sections_are_installed` |
| Top-level organisation | Template sections 1.1 to 5.4 | Same |
| Sub-structure of 2.3 and 3.2 | Template sections down to the fourth level | Same |
| Sub-structure of 2.6, 2.7, 4.2, 5.3 | **Not shipped**, and the reason is recorded in the data file | — |

## 14.4 GS1

| Provision | Artefact | Test |
|---|---|---|
| Modulo-10 check digit | `gs1.compute_check_digit` | `test_gs1.test_check_digit_published_example` |
| GTIN-14 validation | `gs1.is_valid_gtin14` | `test_gs1.test_valid_gtin14`, `test_invalid_gtin14_wrong_check_digit` |
| SSCC-18 construction | `gs1.build_sscc` | `test_gs1.test_build_sscc` |
| AI (01), (21), (10), (17) | `gs1.build_unique_identifier` | `test_gs1.test_unique_identifier_element_string` |
| AI (00) | `gs1.build_sscc_element_string` | `test_gs1.test_sscc_element_string` |
| Twenty-character limit on variable fields | `gs1.validate_variable_field` | `test_gs1.test_variable_field_length_limit` |

## 14.5 Commission Delegated Regulation (EU) 2016/161

| Provision | Artefact | Test |
|---|---|---|
| Article 4, composition of the unique identifier | `gtin`, `serial_number`, `national_number`, `batch_number`, `expiry_date` | `test_serialization.test_element_string_carries_the_four_data_fields` |
| Article 4, the serial number must not be possible to deduce | `secrets`-based generation | `test_gs1.test_generated_serials_are_not_sequential` |

## 14.6 Frameworks with no rows

| Framework | Why there are no rows |
|---|---|
| FDA 21 CFR Part 11 | Not implemented. The digest is not a signature and the identification and authentication controls of the Part are absent. |
| WHO GMP | No WHO text was read during this work. |
| ISO 9001, ISO 13485, ISO 14971 | Quality-system standards addressed by the Layer 3 modules of the suite, not by this Layer 4 module. |
| ANPP, Algerian BPF | Located by reference only; the texts were never read. Nothing here derives from them. |
