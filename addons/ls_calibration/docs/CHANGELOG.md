# Changelog

All notable changes to `ls_calibration` are recorded here. The format follows
Keep a Changelog; versions follow the Odoo convention `19.0.MAJOR.MINOR.PATCH`.

---

## [19.0.1.0.0] — 2026-07-30

Initial release. Target platform: Odoo 19.0 Community Edition.

### Added — models

- `ls.calibration.instrument.category` — nested instrument families carrying
  default interval and criticality.
- `ls.calibration.instrument` — instrument register with measuring range,
  criticality, GxP classification, calibration interval, derived calibration
  status and a five-state lifecycle.
- `ls.calibration.point` — per-instrument calibration points with absolute,
  percent-of-reading and percent-of-span tolerances and derived acceptance
  limits.
- `ls.calibration.standard` — reference standards with their own traceability
  certificate, issuing laboratory, expiry and measurement uncertainty.
- `ls.calibration.plan` — approved calibration plans with an effective window
  and schedule generation.
- `ls.calibration.record` — executed calibrations with a seven-state workflow.
- `ls.calibration.reading` — as-found and as-left values per point with derived
  deviation and in-tolerance verdicts.
- `ls.calibration.certificate` — internal and external certificates.
- `ls.calibration.oot` — out-of-tolerance events with a four-state assessment
  and disposition workflow.

### Added — transient models

- `ls.calibration.plan.generate` — bulk generation of scheduled calibrations.
- `ls.calibration.record.reject` — mandatory rejection reason capture.

### Added — controls

- Segregation of duties between performer, reviewer and approver, enforced by
  an ORM constraint and by guards on the approval actions.
- Immutability of approved and cancelled records, enforced by a `write`
  override on the record and by `create`, `write` and `unlink` overrides on
  its readings, so that a closed result cannot be altered by inserting,
  editing or removing a measurement.
- Freezing of a calibration point's acceptance criteria once the point has been
  used in a committed record.
- Prevention of deletion of instruments with history, records past draft,
  plans with generated records, standards in use, points with readings, and of
  certificates under any circumstance.
- Automatic quarantine of an instrument when an out-of-tolerance event is
  raised against it.
- Requirement of a corrective action reference before closing an out-of-
  tolerance event with a reported product impact.
- Requirement of a different user to close an event than the one who assessed
  it.

### Added — security

- Four graduated groups: Viewer, Technician, Approver, Manager, built on the
  Odoo 19 `res.groups.privilege` model.
- 40 access-control lines covering all 11 models.
- 9 global multi-company record rules.

### Added — data and automation

- 4 sequences: instrument, record, certificate, out-of-tolerance event.
- 3 scheduled actions: daily instrument status refresh, weekly due-calibration
  notification (shipped inactive), daily standard validity refresh.

### Added — reporting

- QWeb calibration certificate report with readings, standards, traceability
  and a three-role authorisation block.
- QWeb calibration record report.
- Pivot, graph and calendar views on calibration records.

### Added — quality artefacts

- 112 test methods across 11 test classes in 5 test modules.
- `tools/static_check.py`: an offline static analyser with 12 negative controls
  and 1 positive control.
- `docs/generate_inventory.py`: AST-driven generator for the technical
  specification.
- Translation template with 406 extracted terms.

### Declared deviations from the suite specification

| Ref | Deviation |
|---|---|
| D-1 | Dependencies reduced from `maintenance`, `ls_qms` to `base`, `mail`. |
| D-2 | Five models added beyond the four named in the specification. |
| D-3 | Fourth security group (Approver) added to make segregation of duties assignable. |
| D-4 | Terminal `cancelled`, `closed` and `retired` states added. |
| D-5 | Record rules are global rather than group-scoped. |
| D-6 | No kanban view and no dashboard client action. |
| D-7 | `ir.cron` records omit `numbercall`, `doall` and `nextcall`. |
| D-8 | Electronic signatures and hash-chained audit trail not implemented. |

Full rationale in `docs/03_architecture_review_and_delivery_gate.md`.

### Known limitations

- Never installed against a running Odoo 19 instance.
- Tests written but never executed; no coverage measured.
- `flake8`, `pylint` and `pylint-odoo` never run (no network access).
- Whether the Odoo 19 Maintenance application ships in Community Edition could
  not be verified from official documentation.
- The `ir.rule` and `res.users` group field names in Odoo 19 could not be
  verified; the module is engineered to avoid depending on either.
- Approval is not a 21 CFR Part 11 electronic signature.
- `mail.thread` tracking is a change log, not a tamper-evident audit trail.
- Measurement uncertainty is recorded but not propagated into any calculation.
- Expired reference standards are flagged but their use is not blocked.
- `_compute_calibration_dates` filters records in Python; cost grows with the
  number of calibrations per instrument.

---

## Release notes

### For implementers

Read `docs/03_architecture_review_and_delivery_gate.md` §10.4 before deploying.
It lists 7 installation-qualification, 11 operational-qualification and 4
performance-qualification tasks that have not been performed and cannot be
performed in a build environment without an Odoo runtime.

The first three tasks are: install the module, run the test suite, and measure
coverage. Until those are done, the module's runtime behaviour is unverified.

### For quality and regulatory functions

This module supports calibration process implementation. It does not deliver
electronic signatures or a tamper-evident audit trail. If 21 CFR Part 11
applies to your calibration records, deploy `ls_electronic_signature` and
`ls_audit_trail` alongside this module and validate the combination.

The clause-by-clause regulatory mapping in
`docs/01_analysis_and_functional_spec.md` §2 states, for each framework,
whether the operative wording was verified from an official source. In several
cases it was not, because the standards are sold under licence. Read the
standards yourself before relying on the mapping.

### For developers

The module depends only on `base` and `mail`. Integration with sibling suite
modules is via four documented text extension points which a bridge module can
replace with relational fields by inheriting the model. No change to this
module is required to do so.

Before changing any code, run:

```bash
python3 tools/static_check.py --self-test   # prove the checker works
python3 tools/static_check.py .             # then trust its verdict
python3 docs/generate_inventory.py          # regenerate the technical spec
```
