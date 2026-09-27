# Release Notes — `ls_audit_trail` 19.0.1.0.0

## Summary

First release of the Audit Trail module for the Life Sciences Suite on Odoo 19
Community Edition. It provides tamper-evident, field-level change capture with a
per-company SHA-256 hash chain, integrity verification, sealed evidence packs and
a controlled retention mechanism.

## Highlights

- **Configure what matters.** Audit any model down to the field, with a recorded
  justification and both an allow-list and an exclusion list.
- **Detect tampering.** Every entry is chained; verification recomputes and
  compares digests and reconciles the head of each chain against retention
  anchors. Altered values, altered attribution, removed entries and undocumented
  truncations are all detected.
- **Hand an inspector a sealed pack.** JSON + CSV + a digest manifest in one ZIP,
  with the archive's own SHA-256 recorded and re-checkable, plus a PDF cover
  sheet.
- **Remove aged records safely, or not at all.** Retention runs require an
  approved period and procedure, an exact-count confirmation and a justification,
  verify the chain first, and leave an anchor behind. With retention disabled,
  nothing is ever removable.

## Upgrade notes

Not applicable; this is the initial release.

## Compatibility

Odoo 19.0 Community Edition. PostgreSQL. No third-party Python dependency.

## Delivery status

CONDITIONAL PASS. Static validation is complete and clean; execution against a
live Odoo 19 instance and formal qualification (IQ/OQ/PQ) remain for the
receiving team. See `doc/test_report.md` for the precise honesty statement.
