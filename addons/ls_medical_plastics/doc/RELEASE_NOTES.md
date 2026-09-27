# Release Notes — 19.0.1.0.0

**Module:** Life Sciences — Medical Plastics (`ls_medical_plastics`)
**Platform:** Odoo 19.0 Community Edition
**Date:** August 2026

---

## Summary

First release. The module records injection moulding production for medical
plastics and pharmaceutical primary packaging: a mould and cavity register with
shot-based maintenance scheduling, versioned and approved moulding parameter
specifications, moulding run execution records with append-only process
readings, and material traceability from a produced lot back to the resin lots,
tool, cavities and specification version used.

## What to know before installing

**This release has never been installed on a live Odoo 19 instance, and its 139
automated tests have never been executed.** It is delivered as a
**CONDITIONAL PASS**: statically clean, dynamically unproven. Read
`doc/VALIDATION_REPORT.md` before deploying anywhere near production.

The single highest-risk item at installation is the inherited
`mrp.production` form view. If installation fails with an xpath error, remove
`views/mrp_production_views.xml` from the manifest; the module loses only a
navigation button. This is documented in `doc/INSTALLATION.md` section 4.

## Highlights

- **Readings cannot be altered.** Not by an operator, not by a manager. A wrong
  value is corrected by a new reading that supersedes it and states why; both
  values appear on the printed record. Enforced in the model *and* in the access
  rights.
- **Criteria are frozen at capture.** Revising a specification cannot change
  whether a historical reading was in tolerance.
- **Production cannot start out of specification.** A critical parameter out of
  tolerance at start-up blocks the run.
- **Duties are separated in code.** Three distinct users are needed to approve a
  specification. The operator and setter cannot review their own run. These are
  ORM-level checks, not hidden buttons.
- **Cavity-level traceability.** A defect can be attributed to one cavity, and
  that cavity blocked without taking the mould out of service.

## Upgrade notes

None; this is the first release.

## Compatibility

Requires `base`, `mail`, `product`, `stock` and `mrp`. It does **not** depend on
any other Life Sciences Suite module, so it installs standalone. Integration
points for deviation management, document control and validation are provided as
reference fields ready to be bridged. See `doc/DEVELOPER_MANUAL.md` section 4.

## Not included

Electronic signatures, comprehensive audit trail, instrument calibration and
machine data acquisition are outside this module's scope. Where a predicate rule
requires them, they must be supplied by dedicated modules and procedures.
