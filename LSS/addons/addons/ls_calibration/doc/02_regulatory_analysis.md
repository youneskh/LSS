# Phase 2 — Regulatory Analysis

Module: `ls_calibration`.

## 2.0 Statement of verification

This section distinguishes three levels of evidence. The distinction is
mandatory: a validation deliverable must not present an unverified reference
as a verified one.

| Level | Meaning |
|-------|---------|
| **V** | Verified during the preparation of this document against a primary source, cited below. |
| **P** | Based on the published structure of the standard or regulation. The clause numbering is stated as commonly published, but the text of the standard was **not** consulted during the preparation of this document, because ISO standards are not freely distributable. It must be confirmed against the licensed copy held by the organisation. |
| **N** | **This information could not be verified from official documentation.** |

Primary sources consulted during the preparation of this document:

* U.S. Food and Drug Administration, *Quality Management System Regulation
  (QMSR)*, and *Quality Management System Regulation — Frequently Asked
  Questions*, fda.gov.
* U.S. Federal Register, *Medical Devices; Quality Management System
  Regulation Technical Amendments*, federalregister.gov.

## 2.1 Frameworks applicable to this module

Only the frameworks that impose requirements on the control of measuring
equipment are listed. Frameworks of the suite that do not apply to this
module are excluded and the exclusion is justified.

| Framework | Level | Applicability to the calibration of measuring equipment |
|-----------|-------|--------------------------------------------------------|
| ISO 9001:2015 | P | Clause 7.1.5 *Monitoring and measuring resources*, including 7.1.5.2 *Measurement traceability*, requires that measuring equipment be verified or calibrated at defined intervals against traceable standards, be identified, be safeguarded, and that the validity of previous results be assessed when equipment is found unfit. |
| ISO 13485:2016 | P | Clause 7.6 *Control of monitoring and measuring equipment* imposes calibration or verification at specified intervals against traceable standards, identification of the calibration status, protection from adjustments that would invalidate the result, and assessment of the validity of previous measurements when the equipment is found not to conform. |
| FDA 21 CFR Part 820 (QMSR) | V | The revised Part 820, titled *Quality Management System Regulation*, became effective on **2 February 2026** and incorporates ISO 13485:2016 by reference. The former § 820.72 *Inspection, measuring, and test equipment* is therefore no longer the operative text; the requirement for the control of measuring equipment is the one of ISO 13485:2016 Clause 7.6, as incorporated. |
| FDA 21 CFR Part 210 and 211 | N | The pharmaceutical current good manufacturing practice regulations require the routine calibration of instruments, apparatus, gauges and recording devices according to a written programme. The exact section numbers commonly cited are § 211.68 and § 211.160(b)(4); **this information could not be verified from official documentation during the preparation of this document** and must be confirmed against the current text of the eCFR before use in a validation deliverable. |
| FDA 21 CFR Part 11 | N | Applies to the electronic calibration records and to the approval signatures. The requirements for audit trails, record protection and signature manifestation are widely published; **the specific paragraph references could not be verified from official documentation during the preparation of this document.** See section 2.4 for the resulting gap. |
| EU GMP | N | The European good manufacturing practice guidelines require the calibration of measuring equipment used in production and control. **The applicable chapter and annex references could not be verified from official documentation during the preparation of this document.** |
| WHO GMP | N | The WHO good manufacturing practices for pharmaceutical products address the calibration of measuring equipment. **The applicable technical report series and annex could not be verified from official documentation during the preparation of this document.** |
| ISO 15378:2017 | P | Good manufacturing practice for primary packaging materials for medicinal products, structured on ISO 9001 with GMP requirements. The control of measuring equipment follows the ISO 9001 clause identified above. |
| ISO 22716:2007 | P | Cosmetics good manufacturing practices. The equipment requirements, including calibration of measuring equipment, are published as Clause 5 *Equipment*. **The exact sub-clause number could not be verified** and must be confirmed against the licensed copy of the standard. |
| ISO/IEC 17025 | P | Applies to the external laboratory that issues a calibration certificate, not to this module. The module records the accreditation reference of that laboratory. |
| ANPP requirements, Algeria | N | **This information could not be verified from official documentation.** No publication of the Agence Nationale des Produits Pharmaceutiques specifying calibration requirements was consulted during the preparation of this document. The organisation must map its national obligations itself before using this module in an Algerian regulated context. |

## 2.2 Frameworks deliberately excluded

| Framework | Reason for exclusion |
|-----------|----------------------|
| ISO 14971:2019 | Risk management for medical devices. It informs the criticality classification of an instrument but imposes no requirement on the calibration process itself. The module provides the criticality and GxP impact fields to carry the output of that process. |
| EU MDR 2017/745 | Imposes a quality management system, whose measuring equipment requirements are those of ISO 13485:2016 already covered. |
| EU Cosmetics Regulation 1223/2009 | Product safety and notification requirements. No requirement on the calibration of measuring equipment. |
| GS1 standards | Identification and serialisation. No requirement on calibration. |

## 2.3 How the module supports the implementation of these requirements

The module **supports the implementation of** processes aligned with these
requirements. It does not establish compliance.

| Requirement theme | Supporting design element |
|-------------------|---------------------------|
| Calibration at defined intervals | `ls.calibration.plan` with `interval_number` and `interval_uom`; `next_due_date` computed from the last approved record. |
| Traceability to recognised standards | `standard_ids` on the record, with a blocking refusal of an overdue standard; `external_standard_reference` and `accreditation_reference` for externally traceable standards. |
| Identification of the calibration status | `calibration_status` computed at read time; dedicated view; badge in the list views. |
| Records of the results of calibration | `ls.calibration.record` and its lines; PDF report. |
| Assessment of the validity of previous results when equipment is found unfit | `as_found_status` computed before any adjustment; mandatory `oot_impact_assessment`; `oot_action_reference` pointing to the quality system event. |
| Protection against adjustments that invalidate results | Separation of the as-found and as-left readings; locking of the record after approval. |
| Written procedure | `procedure_reference` and `method_description` on the plan. |
| Attributable and contemporaneous records | `performed_by_id`, `calibration_date`, `submitted_by_id`, `submission_date`, `approved_by_id`, `approval_date`; message thread on every model. |
| Segregation of duties | Approval refused when the approver is the performer; approval restricted to the manager group. |
| Record protection | `write` and `unlink` refused on approved records and on their lines; deletion restricted to draft records. |
| Personnel competence | Out of scope of this module; carried by the training module of the suite. |

## 2.4 Regulatory gaps of this module

These gaps are stated explicitly so that they cannot be discovered during an
inspection.

| # | Gap | Consequence |
|---|-----|-------------|
| RG-01 | The approval does not re-authenticate the user. The signature manifestation is recorded in the message thread, but a compliant electronic signature under FDA 21 CFR Part 11 additionally requires the signer to be authenticated at the moment of signing. | The module alone must not be presented as providing Part 11 electronic signatures. A dedicated module is required. |
| RG-02 | The audit trail is the standard Odoo change tracking on the tracked fields. It is not a complete field level audit trail and it is not tamper evident. | A dedicated audit trail module is required for a Part 11 or Annex 11 claim. |
| RG-03 | The out-of-tolerance action reference is a free text field, not a link to a controlled deviation record. | The link to the deviation must be maintained procedurally until the deviation module of the suite is available. |
| RG-04 | The calibration procedures are referenced by their identifier, not managed under document control inside this module. | Document control remains the responsibility of the document management system. |
| RG-05 | The national requirements applicable in Algeria were not verified. | The organisation must perform that mapping before use in that jurisdiction. |

## Gate

**Phase 2: PASS with documented reservations.** The applicable frameworks are
identified, the level of verification of each reference is stated, the
supporting design elements are mapped, and five regulatory gaps are declared.
No claim of compliance or certification is made anywhere in the module or in
its documentation.
