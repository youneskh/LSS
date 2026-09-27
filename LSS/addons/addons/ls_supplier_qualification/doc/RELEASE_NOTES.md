# Release Notes — 19.0.1.0.0

Module: `ls_supplier_qualification`
Date: 26 July 2026
Licence: AGPL-3
Platform: Odoo 19.0 Community Edition

---

## What this release is

Supplier qualification for regulated life-sciences manufacturing, on Odoo
Community. It holds the evidence that a supplier was evaluated, records who
approved it and for what, makes that approval expire, and stops or warns
purchasing when a supplier is not approved.

## Highlights

**The approval says what it covers.** A dossier cannot be approved without at
least one qualified material or service. "Approved supplier" is never a bare
flag; it always has a scope and an end date.

**Prerequisites are data, not code.** The supplier category decides whether an
assessment is required, whether an audit is required, and how long an approval
lasts. The dossier shows, at all times, the list of what is still missing, and
refuses submission while that list is non-empty.

**Past results do not move.** The scale, the thresholds and the mandatory
minimum are copied onto each assessment when it is created. Editing a
questionnaire afterwards cannot change a result that has already been recorded.
Performance weights behave the same way.

**Decisions are logged and the log is tamper-evident.** Every approval,
suspension, reinstatement, disqualification, assessment completion, review and
audit closure appends an entry carrying the signer, the timestamp, the meaning
of the signature, a written justification and a JSON snapshot of what was
signed. The entries are chained with SHA-256, and a verification action detects
a modification made directly in the database.

**Approvals expire by themselves.** A daily job moves elapsed approvals to
Expired and raises reminders beforehand. A lapsed approval cannot go unnoticed
simply because nobody looked.

**Purchasing is gated, at a level you choose.** No control, a warning in the
order chatter, or a refusal at confirmation — with an optional check that each
ordered product is inside the qualified scope.

**Segregation of duties without a rigid role split.** The approver of a dossier
cannot be an assessor or lead auditor of that same dossier, and an assessment
cannot be reviewed by its own assessor. The rule is per company and can be
disabled as a documented decision, so a small quality department is not blocked.

## Installation

```bash
odoo-bin -d <database> -i ls_supplier_qualification --stop-after-init
```

Dependencies: `base`, `mail`, `product`, `purchase`. All Community. No external
Python package. `purchase_stock` is optional and only enables the automatic
delivery counters.

See `doc/06_installation_guide.md`, and complete §5 of that guide before
production use.

## Before you use it

**Review the shipped configuration.** The 10 categories, 32 criteria, 2
questionnaires, criticality levels, intervals, weights and thresholds are
proposals made by this module. They are not derived from any regulation.
Approve or replace them under your own change control.
See `doc/07_configuration_guide.md` §1.

**Start the purchase control at Warn.** Moving straight to Block on a supplier
base that is not yet qualified stops procurement on day one.

**Read the electronic-signature limitation.** The signature log records who,
when, what and why, and detects tampering. It does not re-authenticate the
signer at the moment of signing. If your quality system needs a second
identification component, cover it by other documented means until
`ls_electronic_signature` is available.
See `doc/02_regulatory_analysis.md` §2.4.

## What this module does not claim

It does not certify compliance with ISO 9001, ISO 13485, ISO 14971, ISO 15378,
ISO 22716, 21 CFR Part 11, 21 CFR Part 211, 21 CFR Part 820, EU MDR, EU
1223/2009, WHO GMP or ANPP requirements. It supports processes an organisation
may use towards those frameworks. Compliance depends on procedures, people,
validation and decisions, not on software.

It reproduces no normative text. The standards library stores designations and
issuing bodies only.

The published ANPP requirements for supplier qualification could not be
verified from official documentation during development. The module provides a
placeholder so an organisation can attach its own verified requirements, and
makes no statement about their content.

## Delivery status

Complete and internally verified. Four items require a live Odoo instance and
are outstanding:

1. Installation on a clean database.
2. Execution of the 141-test suite, with coverage measured.
3. Execution of `flake8`, `pylint` and `pylint-odoo`.
4. Confirmation of the three verification points in
   `doc/05_architecture_review.md` §5.8.

Commands for all four are in `doc/15_compliance_checklist.md` §10.6. No
coverage figure and no lint result is claimed anywhere in this delivery,
because neither was measured.

## Documentation

Fifteen documents in `doc/`: the ten delivery phases, four manuals, the API
reference, plus this file and the changelog. `README.rst` at the module root is
the entry point.

## Planned next

Bridge modules, once the corresponding suite modules exist:
`ls_supplier_qualification_capa`, `ls_supplier_qualification_qms`,
`ls_supplier_qualification_signature`. Interfaces are specified in
`doc/10_developer_manual.md` §5.5.
