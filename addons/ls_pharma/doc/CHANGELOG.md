# Changelog

All notable changes to `ls_pharma` are recorded here. The format follows
Keep a Changelog, and the versioning follows the Odoo convention
`19.0.<major>.<minor>.<patch>`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-06: a customer delivery of a lot whose batch is not released (including rejected batches) is refused.
- Recording a batch release decision no longer fails: the integrity digest is stamped through the parent `write`.
- F-16: batches, components and co-products refuse the lot of another product and check company consistency.
- F-29: `@api.constrains` methods raise `ValidationError`. Reports: `t-field` moved out of table cells.
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

## [19.0.1.0.0] — 2026-08-01

First release.

### Added

- Manufacturing batches with components, major equipment, co-products, yield
  computation against established limits, and an eight-state lifecycle.
- Batch production and control records covering the thirteen items of
  21 CFR 211.188(b): processing steps, in-process and laboratory controls,
  line clearances before and after use, labelling reconciliation, samples,
  discrepancies, containers and closures.
- An append-only batch release decision with an eight-point checklist bound
  to its regulatory basis and a SHA-256 integrity digest.
- Segregation of duties enforced in the models: a component charged by one
  person is verified by another, a record is not approved by its executor, a
  batch is not released by the person who manufactured it.
- Active pharmaceutical ingredient and excipient master data on a shared
  abstract mixin, with a four-state qualification lifecycle.
- Stability studies with the four general-case storage conditions of
  ICH Q1A(R2), schedule generation on the published frequencies, samples,
  time points, results and significant-change tracking.
- GS1 serialisation: modulo-10 check digit, GTIN-14 and SSCC-18 validation,
  element strings, unpredictable serial numbers drawn from `secrets`, and
  aggregation into containers.
- Common Technical Document dossiers with 108 template sections derived from
  ICH M4(R4) and ICH M4Q.
- Six security groups, 143 access rules and 22 multi-company record rules.
- Two printable reports: the batch production and control record and the
  batch release certificate.
- Two daily scheduled actions: overdue stability time points and batches
  approaching expiry.
- An offline static checker, shipped inside the module, validated against
  fifteen injected faults.
- 121 tests across ten test modules.
- A nineteen-document set in `doc/`, plus the README, covering the ten
  development phases.

### Known limitations

- Not a 21 CFR Part 11 electronic signature system.
- No barcode symbol rendering; element strings only.
- No electronic submission packaging.
- The tests have never been executed and no coverage has been measured.
- The module has never been installed against a live Odoo 19 instance.
- The Algerian regulatory corpus is carried as reference-level only.

See `doc/15_deviation_register.md` for the fourteen recorded deviations and
`doc/13_validation_report.md` for the delivery gate.
