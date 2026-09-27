# Release Notes — ls_calibration 19.0.1.0.0

## What this release is

The calibration management module of the Life Sciences Suite for Odoo 19
Community Edition. It manages the instruments, their calibration plans, the
calibration records with their as-found and as-left readings, the handling of
out-of-tolerance situations, and the calibration certificates.

## What is new

Everything: this is the first release.

The four capabilities that distinguish it from a generic maintenance
schedule:

1. **The as-found reading is recorded before any adjustment**, so that the
   validity of the measurements taken during the elapsed period can be
   assessed. An out-of-tolerance as-found result cannot be closed without a
   documented impact assessment.
2. **Metrological traceability is enforced**, not merely documented. A
   reference standard whose own calibration is overdue is refused at the
   moment of submission.
3. **Segregation of duties is enforced by the server.** The user who
   performed a calibration cannot approve it, whatever the interface used.
4. **Approved evidence is immutable.** Neither the record nor its test points
   can be modified or deleted afterwards, through the interface or through
   the external API.

## Compatibility

Odoo 19.0 Community Edition only. The module uses `models.Constraint`, the
`<list>` element, the `<chatter/>` element and the `self.env._` translation
API, none of which work on Odoo 18 or earlier.

Dependencies: `base`, `web`, `mail`, `maintenance`, all Community. No
Enterprise module, no OCA module, no third-party module.

## Upgrade path

Not applicable, first release.

## Maturity

`Beta`. The module is complete and internally consistent, its static analysis
reports zero finding, and its 101 tests are written. **It has not been
executed against a live Odoo 19 instance**, because the environment in which
it was produced has neither Odoo nor network access. The nine actions
required to promote it to `Production/Stable` are listed in
`doc/15_final_validation_checklist.md`, section 5.

## Regulatory statement

This module supports the implementation of processes aligned with the
control-of-measuring-equipment requirements of ISO 9001:2015, ISO 13485:2016
and, through the incorporation by reference effective 2 February 2026, the
FDA Quality Management System Regulation. It does not establish compliance
with any framework, and it is not certified against any of them.

It does **not** provide FDA 21 CFR Part 11 electronic signatures: the
approval records the signer, the time and the meaning of the signature, but
does not re-authenticate the signer. Do not present it as a Part 11 signature
solution.
