# Regulatory Traceability Matrix — `ls_medical_device`

Each row maps a specific provision to the specific model field, constraint or
method that supports it. General claims of compliance are deliberately absent;
only provision-to-artefact mappings appear.

**Support means the module provides a place to record and control the
information the provision concerns. It does not mean conformity is achieved.**

## Regulation (EU) 2017/745 (MDR)

| Provision | Subject | Artefact |
|---|---|---|
| Art. 10(4) | Technical documentation drawn up and kept up to date | `ls.md.technical_file`, versioned with approval workflow |
| Art. 10(8) | Retention 10 years, 15 for implantables | `ls.md.device.documentation_retention_years`, `.documentation_retention_until` |
| Art. 15 | Person responsible for regulatory compliance | **Not implemented.** No PRRC model |
| Art. 19 | EU declaration of conformity | `ls.md.ce_marking.declaration_number`, `.declaration_date` |
| Art. 20 | CE marking of conformity | `ls.md.ce_marking.ce_marking_affixed`, `.ce_marking_date` |
| Art. 27(1) | UDI assigned to device and higher packaging levels | `ls.md.udi.packaging_level`, `.udi_kind` |
| Art. 27 | UDI-PI components | `ls.md.udi.pi_lot_number`, `.pi_serial_number`, `.pi_manufacturing_date`, `.pi_expiry_date`, `.pi_software_version` |
| Art. 29 / 31 | Registration obligations | Partially: `ls.md.udi.database_name`, `.database_submission_date`, `.database_reference`. No EUDAMED integration |
| Art. 51 | Classification | `ls.md.device.device_class_id`, `.classification_rule`, `.classification_rationale`. Annex VIII rules **not implemented** |
| Art. 56(2) | Certificate validity not exceeding five years | `ls.md.ce_marking.expiry_date`, `.days_to_expiry`, `_cron_expire_certificates` |
| Art. 61 | Clinical evaluation | `ls.md.clinical_evaluation` |
| Art. 61(11) | Annual PMCF update for class III and implantables | `ls.md.device_class.annual_pmcf_update_required`, `ls.md.pmcf_evaluation.next_update_due` |
| Art. 83 | Post-market surveillance system | `ls.md.pms` |
| Art. 84 | PMS plan within Annex III documentation | `ls.md.pms` linked from `ls.md.technical_file` |
| Art. 85 | PMSR for class I | `ls.md.pms_report.report_type = pmsr` |
| Art. 86(1) | PSUR for IIa, IIb, III; intervals | `ls.md.device_class.periodic_report_interval_months` (24 / 12 / 12) |
| Art. 86(1) | Content: benefit-risk conclusions, PMCF findings, sales volume, user population | `.benefit_risk_conclusion`, `.pmcf_main_findings`, `.sales_volume`, `.population_estimate` |
| Art. 86(2) | Submission to notified body for class III and implantables | `.notified_body_submission_required`, `.notified_body_submission_date`, `.notified_body_reference` |
| Art. 87 | Serious incident and FSCA reporting | **Not implemented.** Deadlines published in `constants.py` only |
| Art. 88 | Trend reporting | `ls.md.pms_report.trend_signal_identified`, `.trend_signal_description` |
| Annex I | General safety and performance requirements | Section entries in `ls.md.technical_file_section` |
| Annex II | Technical documentation structure | `ls.md.technical_file_section_template` (titles **unconfirmed against the Official Journal**) |
| Annex II pt 4 | Explanation where a GSPR does not apply | `.not_applicable` with mandatory `.not_applicable_justification` |
| Annex III | PMS technical documentation | `annex_reference = annex_iii` |
| Annex III 1.1 | Plan elements | Enforced at approval: information sources, collection process, referenced procedures, corrective action process, traceability tools |
| Annex VI Part C | Basic UDI-DI | `ls.md.device.basic_udi_di`, `ls.md.udi.udi_kind = basic_udi_di` |
| Annex XII | Certificate minimum content | Partially: `.certificate_number`, `.scope`, `.conditions`, validity dates |
| Annex XIII s.2 | Custom-made devices | `annex_reference = annex_xiii`, `ls.md.device.is_custom_made` |
| Annex XIV Part A | Clinical evidence kinds | `ls.md.clinical_evidence_source` |
| Annex XIV Part B | PMCF | `ls.md.pmcf_evaluation` |

## ISO 14971:2019

| Concept | Artefact |
|---|---|
| Risk management file | `ls.md.risk_assessment` |
| Risk management plan scope and policy | `.scope`, `.risk_policy` |
| Hazard, sequence of events, hazardous situation, harm | `ls.md.risk_item` fields of the same names |
| Risk estimation | `.initial_severity` × `.initial_probability` = `.initial_index` |
| Risk control option priority | `.control_option` ordered: inherent safety, protective measure, information for safety |
| Risk control verification | `.control_verification_reference`, `.control_verified` |
| New hazards from control measures | `.introduces_new_hazard`, `.new_hazard_description` |
| Residual risk evaluation | `.residual_index`, `.residual_acceptability`, `.acceptability_justification` |
| Residual not worse than initial | `_check_residual_not_worse_than_initial` |
| Disclosure of residual risk | `.disclosed_to_user` |
| Overall residual risk evaluation | `.overall_benefit_risk_conclusion`, `.overall_risk_acceptable` |
| Production and post-production information | `.production_information_summary` |

Severity and probability categories are configuration defaults. The standard
requires the manufacturer to define its own; see the configuration guide.

## ISO 13485:2016

Supported indirectly through document control (versioning, approval,
supersession), competence-bearing approval authority, and the post-market
feedback loop. **No clause-by-clause mapping is asserted**, because the
standard text was not available for verification.

## FDA 21 CFR Part 820 / QMSR

**Not mapped.** The module was designed against the MDR. The February 2026
QMSR transition harmonised the FDA framework with ISO 13485, but no
provision-level verification was performed, so no mapping is claimed.

## ANPP / Algerian BPF

**Not claimed.** No official ANPP publication was available to verify any
requirement. Any mapping would be invention.
