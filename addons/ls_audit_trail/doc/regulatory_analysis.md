# Regulatory Analysis — `ls_audit_trail`

**Status of this document.** It maps specific regulatory provisions to specific
implemented mechanisms. It makes no compliance claim. Where a source could not be
verified against an official publication, that is stated in place of a citation.

## Scope of the mapping

This module addresses the *audit trail* and *record protection* requirements of
the frameworks below. It does not address electronic signatures, record
retention policy definition (beyond providing an enforcement mechanism), or
system validation, which are the responsibility of other modules and of the
deploying organisation.

## FDA 21 CFR Part 11

The text of 21 CFR Part 11 is published by the U.S. Government Publishing Office
and the FDA. The provisions most relevant to an audit trail are the following.

- **§11.10(e)** — use of secure, computer-generated, time-stamped audit trails
  to independently record the date and time of operator entries and actions that
  create, modify, or delete electronic records; record changes shall not obscure
  previously recorded information; audit trail documentation shall be retained
  for at least as long as the subject records and be available for review and
  copying.

  *Implemented by:* automatic capture on create, write and delete (`base_audit`);
  a server-side UTC timestamp on every entry (`event_datetime`); preservation of
  the previous value in each field-change line (`old_value_technical`,
  `old_value_display`), which does not obscure prior information; immutability of
  entries and lines enforced in `write` and `unlink` overrides; and the CSV /
  JSON evidence pack for review and copying.

- **§11.10(a)** — validation of systems to ensure accuracy, reliability and the
  ability to discern invalid or altered records.

  *Supported by:* the hash chain and the verification routine, which discern
  altered or removed records. Validation itself (IQ/OQ/PQ) is the deploying
  organisation's responsibility; this module provides the mechanism a validation
  can exercise, not the validation.

- **§11.10(c)** — protection of records to enable their accurate and ready
  retrieval throughout the retention period.

  *Supported by:* immutability, the restrict-on-delete foreign keys to company
  and user, and the controlled retention mechanism that never silently discards
  records.

## EU GMP Annex 11 (Computerised Systems)

Annex 11 is published by the European Commission in EudraLex Volume 4.

- **§9 (Audit Trails)** — consideration, based on a risk assessment, of building
  into the system the creation of a record of all GMP-relevant changes and
  deletions; audit trails need to be available, convertible to a generally
  intelligible form, and regularly reviewed.

  *Implemented by:* per-model, per-field, risk-scoped rules (the risk assessment
  is the organisation's; the rule records its outcome and its justification);
  capture of changes and deletions; and the human-readable display values plus
  the evidence pack, which render the trail in an intelligible form for review.

- **§12 (Security)** — restriction of system access to authorised individuals.

  *Supported by:* the three-tier group model and the multi-company record rules.

## ALCOA+ (data-integrity expectations)

ALCOA+ is described in guidance from several regulators (for example the WHO and
the UK MHRA). The elements an audit trail bears on are mapped as follows.

| Element | Mechanism |
|---------|-----------|
| Attributable | `user_id`, `user_login`, `remote_addr` on every entry |
| Legible | Human-readable `*_display` values and the intelligible evidence pack |
| Contemporaneous | Server UTC `event_datetime` set at capture time |
| Original | Prior value preserved in each field-change line |
| Accurate | Technical values captured verbatim; binary content fingerprinted |
| Complete | Capture of create, write and delete; failed capture fails the transaction |
| Consistent | Deterministic canonical serialisation and a single chain per company |
| Enduring | Immutability and restrict-on-delete foreign keys |
| Available | Search, dashboard, PDF report and downloadable evidence pack |

## FDA QMSR (effective 2 February 2026)

The FDA's Quality Management System Regulation, which incorporates ISO 13485 by
reference, took effect on 2 February 2026. Among other changes, it removed the
prior provision that shielded internal audit reports and certain management
review and supplier records from routine FDA inspection. This is a verified,
post-training-cutoff regulatory change; it strengthens the operational case for
a defensible, tamper-evident audit trail of quality records, but it imposes no
new *technical* requirement that changes this module's design.

## Algeria — ANPP / BPF

The Agence Nationale des Produits Pharmaceutiques (ANPP) administers
pharmaceutical regulation in Algeria, including national Good Manufacturing
Practices (BPF).

**This information could not be verified from official documentation.** Specific
ANPP or BPF provisions governing electronic audit trails were not available from
an official ANPP publication at the time of writing. No ANPP-specific claim is
made. Organisations subject to ANPP oversight must confirm the applicable
requirements against current official ANPP publications and validate the module
accordingly.

## Explicit non-coverage

- Electronic signatures (21 CFR Part 11 Subpart C) — not implemented here.
- Retention *period* determination — the module enforces a period the
  organisation defines and approves; it does not decide the period.
- System validation — not performed by the module.
