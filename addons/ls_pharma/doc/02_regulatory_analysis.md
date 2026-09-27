# Phase 2 — Regulatory Analysis

## 2.1 How to read this document

Every provision listed below was read in the source named in section 2.2. A
provision is cited only where the module actually implements a control that
supports it. Where a framework applies to this domain but the module was not
built against a text that was read, the row says so plainly rather than
implying coverage.

**The module supports the implementation of processes. It does not confer
compliance, and no statement here should be read as a claim of compliance or
of certification.**

## 2.2 Sources consulted

| Source | Access | Used for |
|---|---|---|
| 21 CFR Part 211, Electronic Code of Federal Regulations, `ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211` | Full text of 211.188 fetched and read; the other sections read in the same source | The batch record, the yield rules, the release gate |
| ICH Q1A(R2), reproduced by the FDA, `fda.gov/media/71707/download` | Fetched and read | Storage conditions and testing frequencies |
| ICH M4(R4), reproduced by the FDA, `fda.gov/files/drugs/published/M4-Organization-...pdf` | Fetched and read | The five modules and the top-level dossier sections |
| ICH M4Q, reproduced by the FDA, `fda.gov/media/71581/download` | Fetched and read | The sub-sections of 2.3 and of 3.2 |
| GS1 General Specifications, Section 3 and GS1 US "How to Calculate a Check Digit" | Application identifier definitions and the check digit algorithm read | Element strings and the modulo-10 check digit |
| Commission Delegated Regulation (EU) 2016/161, Article 4 | Read | The composition of the unique identifier and the unpredictability of the serial number |

## 2.3 Provisions implemented, with the artefact that implements them

| Provision | What it requires | Where the module implements it |
|---|---|---|
| 21 CFR 211.188(a) | An accurate reproduction of the master production or control record, checked for accuracy, dated and signed | `ls.pharma.batch_record`: `master_record_reference`, `master_record_version`, `master_checked_by_user_id`, `master_checked_date`; execution is refused until the last two are set |
| 21 CFR 211.188(b)(1) | Dates | `date_executed`, and the dates on every line model |
| 21 CFR 211.188(b)(2) | Identity of individual major equipment and lines | `ls.pharma.batch.equipment` |
| 21 CFR 211.188(b)(3) | Identification of each batch of component or in-process material used | `ls.pharma.batch.component`, fields `component_lot_id` and `component_lot_reference` |
| 21 CFR 211.188(b)(4) | Weights and measures of components | `quantity`, `uom_id`, `assay_percentage`, `compensated_quantity` |
| 21 CFR 211.188(b)(5) | In-process and laboratory control results | `ls.pharma.batch_record.control` |
| 21 CFR 211.188(b)(6) | Inspection of the packaging and labelling area before and after use | `ls.pharma.batch_record.clearance`, with the two moments `before` and `after` |
| 21 CFR 211.188(b)(7) | A statement of the actual yield and the percentage of theoretical yield | `ls.pharma.batch`: `actual_yield_qty`, `theoretical_yield_qty`, `yield_percentage` |
| 21 CFR 211.188(b)(8) | Complete labelling control records | `ls.pharma.batch_record.labeling` with the reconciliation difference |
| 21 CFR 211.188(b)(9) | A description of drug product containers and closures | `container_closure_description`, `examination_result` |
| 21 CFR 211.188(b)(10) | Sampling performed | `ls.pharma.batch_record.sample` |
| 21 CFR 211.188(b)(11) | Identification of the persons performing and directly supervising or checking each significant step | `ls.pharma.batch_record.step`: `is_significant`, `performed_by_user_id`, `checked_by_user_id` |
| 21 CFR 211.188(b)(12) | Any investigation made | `ls.pharma.batch_record.discrepancy` |
| 21 CFR 211.188(b)(13) | Results of examinations made | `examination_result`, and the control results |
| 21 CFR 211.101(c) | Verification by a second person of the weight or measure of each component | `charged_by_user_id` and `verified_by_user_id`, with a constraint refusing the same user for both |
| 21 CFR 211.101(d) | The exemption where an automated system performs the charge | `is_automated_charge`, which suspends the second-person constraint |
| 21 CFR 211.103 | Determination of actual yields and percentages of theoretical yield | `yield_percentage`, computed and stored |
| 21 CFR 211.125 | Labelling issuance and reconciliation | `quantity_issued`, `quantity_used`, `quantity_returned`, `quantity_destroyed`, `quantity_difference`, `is_reconciled` |
| 21 CFR 211.134 | Examination of packaged and labelled products | `examination_result` |
| 21 CFR 211.165 | Testing and release for distribution against acceptance criteria | The `check_qc_conform` entry of the release checklist, and the conformity of every control |
| 21 CFR 211.166 | A written stability testing programme | `ls.pharma.stability_study` and the `check_stability_programme` entry |
| 21 CFR 211.170 | Reserve samples | The `reserve` sample type and `reserve_sample_count` |
| 21 CFR 211.182 | An equipment cleaning and use log | `cleaning_record_reference`, `cleaning_verified_by_user_id`, `date_used_start`, `date_used_end` |
| 21 CFR 211.186(b)(6) | The theoretical yield and its maximum and minimum percentages in the master record | `pharma_theoretical_yield_qty`, `pharma_yield_min_percentage`, `pharma_yield_max_percentage` on the product, proposed onto the batch |
| 21 CFR 211.192 | Review and approval of production and control records by the quality control unit before release, and thorough investigation of any unexplained discrepancy, extended to other batches, with a written record | The approval guard, the open-discrepancy guard, `extended_to_other_batches`, `extension_scope`, `conclusion`, `follow_up`, and the release gate |
| ICH Q1A(R2), general case | Long term at 25 °C / 60 % RH or 30 °C / 65 % RH; intermediate at 30 °C / 65 % RH; accelerated at 40 °C / 75 % RH | The four shipped `ls.pharma.stability.condition` records |
| ICH Q1A(R2), frequencies | Long term every 3 months in year one, every 6 months in year two, annually thereafter; accelerated a minimum of three points; intermediate a minimum of four | `_ich_timepoint_months` and the constants it reads |
| ICH M4(R4) | The five modules and the top-level organisation of the dossier | The 108 shipped template sections |
| ICH M4Q | The sub-sections of 2.3 and of 3.2 | The same template |
| GS1 General Specifications | Application identifiers (00), (01), (10), (17), (21) and the modulo-10 check digit | `gs1.py`, with a test that reproduces the worked example published by GS1 |
| Commission Delegated Regulation (EU) 2016/161, Article 4 | The unique identifier carries the product code, the serial number, the national reimbursement number where required, the batch number and the expiry date; the serial number must not be possible to deduce | `build_unique_identifier`, `national_number`, and serial numbers drawn from `secrets` |

## 2.4 Frameworks named in the suite specification but not implemented here

| Framework | Position taken |
|---|---|
| FDA 21 CFR Part 11 | **Not implemented.** The release digest detects modification of a stored decision. It is not a signature manifestation and the module carries none of the identification, authentication or signature controls of Part 11. Stated on the release form, on the printed certificate and in the model docstring. |
| WHO GMP | No WHO text was read while writing this module. No claim is made. |
| ISO 9001, ISO 13485 | Not applicable to this Layer 4 module; the suite places quality-system processes in the Layer 3 modules. |
| ANPP and Algerian BPF | See section 2.5. |

## 2.5 Algeria — reference-level only

The following Algerian instruments were **located by reference** during this
work. Their full texts were **not read**. They are recorded here so that the
receiving team can obtain them, and for no other purpose. **No requirement of
this module is derived from them, and no conformity with them is claimed.**

| Instrument | Date | Status here |
|---|---|---|
| Décret exécutif n° 22-247 (rules of good manufacturing practice) | 30 June 2022 | Reference only, text not read |
| Arrêté n° 21 (issuance of the BPF certificate) | 30 September 2025 | Reference only, text not read |
| Arrêté n° 18 (batch release of vaccines) | 25 September 2025 | Reference only, text not read |
| Arrêté n° 17 (Site Master File made mandatory) | 22 September 2025 | Reference only, text not read |
| ANPP note n° 42/MIP/ANPP/DG/NOTE/2026 (labelling particulars) | 11 May 2026 | Reference only, secondary source, text not read |
| ANPP inspection guideline | notified 31 May 2026 | Reference only, secondary source, text not read |

A deployment in Algeria must have these texts read by its regulatory affairs
function and must map their requirements onto the module itself. This module
was not built against them.

## 2.6 What this analysis does not establish

- It does not establish that the controls implemented are sufficient for any
  particular inspection.
- It does not establish that the citations are complete for any framework;
  they are complete only for the controls that the module implements.
- It does not substitute for the manufacturer's own gap analysis.

## Gate verdict

**PASS with a declared limitation.** Every provision that the module relies
upon was read in a primary source, and every provision read is mapped to an
artefact. The limitation is the Algerian corpus, which is carried as
reference-level only and is excluded from every claim.
