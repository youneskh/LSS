# Release Notes — `ls_medical_device` 19.0.1.0.0

Released 2 August 2026 for Odoo 19.0 Community Edition.

## Summary

First release of the Medical Devices module of the Life Sciences Suite. It
manages the regulatory record set of a medical device: register, UDI,
ISO 14971 risk management, clinical evaluation and PMCF, technical
documentation, CE marking, and post-market surveillance with periodic
reporting under MDR Articles 85 and 86.

## Before you install

**This release has never been installed against a running Odoo 19 instance,
and its 137 tests have never been executed.** It is delivered as a
CONDITIONAL PASS. `doc/validation_report.md` section 5 lists the nineteen
qualification activities the receiving organisation must complete before
regulated use.

## Configuration required before use

Four items ship as defaults that must be reviewed, not adopted:

1. **Annex II section titles** — confirmed only against secondary renderings.
   Confirm against the Official Journal; the title of section 6 is
   unconfirmed.
2. **ISO 14971 severity and probability scales** — the standard requires the
   manufacturer to define its own in the risk management plan.
3. **Risk matrix boundaries** — informative defaults; the recorded decision
   governs.
4. **Notified body scope notes** for classes Is, Im and Ir.

The notified body register ships empty by design.

## EUDAMED

Commission Decision (EU) 2025/2371 made four EUDAMED modules mandatory from
28 May 2026. The Vigilance and Post-Market Surveillance module was not among
them. This release records report submission as a channel, date and reference
rather than asserting a EUDAMED route that is not in force. Confirm the
obligations currently applicable to your organisation.

## Not included

Vigilance case management (Article 87), EUDAMED submission, electronic
signatures, Annex VIII classification rules, UDI carrier generation, kanban
views, custom JavaScript.

## Dependencies

`base`, `mail`, `product`, `stock`, and the `python-dateutil` package. No
dependency on other Life Sciences Suite modules; integrate by inheritance as
described in `doc/developer_manual.md`.
