# Changelog — `ls_medical_device`

Format based on Keep a Changelog. Versioning follows the Odoo convention
`19.0.major.minor.patch`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-15: the post-market job recomputes the date-dependent periodic report status before using it.
- F-43: authors and responsible persons cannot approve their own PMS report, clinical evaluation, PMCF report, risk file, technical documentation or PMS plan; submitting a CE certificate requires the regulatory authority; author content is frozen at submission and conclusions at approval.
- The notified-body rule is checked at submission (state trigger); the PMCF documentation and the justification for not performing a clinical investigation are required from the submission.
- F-24: `_check_company_auto` on devices. F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards.
- Tests ported (F-40): fixtures completed, certificate expiry job run with `freezegun`, specific exceptions (F-29).

## [19.0.1.0.0] — 2026-08-02

Initial release. Not yet installed against a running Odoo 19 instance; see
`validation_report.md`.

### Added

- Device register (`ls.md.device`) with a six-state life cycle, gated
  transitions and a justification wizard.
- Risk class configuration (`ls.md.device_class`) carrying the post-market
  reporting obligation per class, seeded with the seven MDR classes.
- Notified body register (`ls.md.notified_body`) with designation verification
  tracking. No designation data shipped.
- UDI assignments (`ls.md.udi`) covering Basic UDI-DI, UDI-DI, packaging
  levels, carrier types and UDI-PI components.
- Risk management (`ls.md.risk_assessment`, `ls.md.risk_item`) following the
  ISO 14971:2019 process, with index computation and residual risk evaluation.
- Clinical evaluation (`ls.md.clinical_evaluation`) with equivalence,
  investigation and PMCF justification constraints.
- PMCF evaluation reports (`ls.md.pmcf_evaluation`) with the annual update
  obligation for class III and implantable devices.
- Technical documentation (`ls.md.technical_file`, `ls.md.technical_file_section`,
  `ls.md.technical_file_section_template`) with template seeding and
  completeness control.
- CE marking and declarations of conformity (`ls.md.ce_marking`) with validity
  tracking and automatic expiry.
- Post-market surveillance plans (`ls.md.pms`) with the Annex III 1.1 elements
  enforced at approval.
- Periodic post-market reports (`ls.md.pms_report`) covering both the
  Article 85 PMSR and the Article 86 PSUR.
- Four access levels with segregation of duties enforced in Python, including
  refusal of self-approval.
- Two daily scheduled actions, created through a registry-aware post-install
  hook.
- Three QWeb PDF reports.
- 137 tests across ten modules.
- Ten documentation files, including an API reference generated from source.

### Known limitations

- Vigilance case management (MDR Article 87) not implemented.
- No EUDAMED integration.
- No electronic signatures.
- Annex VIII classification rules not implemented.
- Record rules are global only; access differentiation is via ACL and Python.
- No kanban views and no custom JavaScript.
- MDR Annex II section titles unconfirmed against the Official Journal.
