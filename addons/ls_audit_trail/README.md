# Life Sciences — Audit Trail (`ls_audit_trail`)

Tamper-evident, field-level audit trail for GxP-regulated data held in Odoo 19
Community Edition.

## What this module does

It records who changed what, when, and from where, for the models and fields you
choose. Each recorded change becomes an immutable entry in a per-company hash
chain, so that removing, inserting or altering an entry after the fact is
detectable. It provides on-demand and scheduled integrity verification, sealed
evidence packs for inspectors, and a controlled, fully documented retention
mechanism for removing aged entries without breaking the chain's verifiability.

## What this module does *not* do

- **It is not an electronic signature.** Capturing a change is not the same as a
  person signing for it. Electronic signatures are a separate concern; see
  `ls_electronic_signature` in the Life Sciences Suite. The evidence pack cover
  sheet carries handwritten (paper) signature lines only.
- **It does not make you compliant.** It supports processes aligned with
  FDA 21 CFR Part 11 §11.10(e), EU GMP Annex 11 §9 and the ALCOA+ data-integrity
  expectations. Compliance additionally depends on your procedures, your system
  validation, your training and your quality system. No certification is claimed.
- **It does not audit unstored data.** One-to-many and many-to-many relations,
  and non-stored computed fields, are never captured directly. Audit the model
  on the other side of a relation, or the fields a computed value depends on.

## Requirements

- Odoo 19.0 Community Edition
- Python 3 (standard library only; no third-party Python dependency)
- PostgreSQL (the chain serialisation uses PostgreSQL transaction advisory locks)

## Installation

Copy the `ls_audit_trail` directory into your Odoo addons path, update the app
list, and install the module. No external Python package is required.

## First configuration

1. Open **Audit Trail ▸ Configuration ▸ Audit Rules** (Administrator role).
2. Create a rule naming the model to audit, the operations (create / write /
   delete) and, optionally, the exact fields. An empty field list audits every
   stored field except the technical ones.
3. Record a justification for the scope. Nothing is audited until a rule exists.

## Roles

| Group | Can |
|-------|-----|
| Audit Trail / Viewer | Read the trail of their own companies |
| Audit Trail / Auditor | Also verify integrity and produce evidence packs |
| Audit Trail / Administrator | Also configure rules and run approved retention |

Segregation of duties is enforced at the ORM level, not only in the interface:
an auditor cannot change what is audited, and only an administrator can remove
entries — and only through the retention wizard, under explicit preconditions.

## Integrity model

Each company owns an independent chain. Every entry stores the SHA-256 digest of
its own canonical content (`payload_digest`) and a `hash_current` that binds that
payload to the `hash_current` of the preceding entry. Verification recomputes
both and compares them to the stored values, and reconciles the head of the
chain against retention anchors. Chain positions are assigned under a PostgreSQL
advisory lock so concurrent transactions cannot claim the same position.

See `doc/` for the full functional, technical, administrator and validation
documentation, and for the honest delivery-gate statement describing exactly
what has and has not been verified.

## Licence

AGPL-3.0-or-later. Authored by the Life Sciences Suite Architecture Team.
