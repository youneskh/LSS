# Life Sciences - Import & Export Compliance (`ls_import_export`)

A foreign-trade compliance platform for the regulated life-sciences
sectors (pharmaceutical, medical devices, cosmetics) operating in or
from Algeria. Part of the **Regulatory Affairs** domain of the Life
Sciences Suite for Odoo 19 Community Edition.

> **Premium module.** This is intended as one of the Premium modules of
> the Life Sciences Suite: a compliance platform for foreign trade,
> not a simple import/export extension of Purchase.

## What this module does

It provides two layers:

1. A **cited regulatory provision registry** that records, source by
   source, the Algerian and international texts that govern regulated
   imports and exports (ANPP, Ministry of Pharmaceutical Industry,
   Customs, Bank of Algeria, commerce extérieur, PPI when applicable).
2. A **generic compliance engine** (country-agnostic) that the registry
   configures: requirement evaluation, expiry alerts, configurable
   landed-cost calculation, dossier preparation, shipment and customs
   tracking.

## The Truth Protocol — read this first

**This module asserts no regulatory requirement that is not first
recorded as a cited provision with a source, an effective date and a
status of *in force*.** The registry ships **empty**. Every provision
is entered by a human who has read the source, cited it and dated it.
Where a rule is expected but not yet verified, the expectation is
recorded as an open **regulatory question** to be answered by a
qualified adviser — never guessed by the module.

This means a freshly installed module is **inert by design**. It
becomes active only as the registry is populated with verified
provisions. Inertness here is the guarantee that the module will never
enforce a rule that has not been read and cited.

This module is a **tool**, not a source of law and not legal advice.
An organisation's compliance depends on its procedures, its validation,
the competence of its staff and the way it actually uses the system.

See `doc/02_regulatory_analysis.md` for the full regulatory statement
and the list of open questions.

## Status

**Phase 1 (foundation):** registry data model
(`ls.import_export.provision`, `.citation`,
`.regulatory.question`, `.compliance.requirement`), engine contract,
architecture and regulatory analysis. **Non-behavioural by design.**

Later phases add: authorisations, operations, shipments, containers,
dossiers, customs declarations, banking files, KPI, cost calculation.

See `doc/00_foundation_architecture.md` §9 for the phasing.

## Documentation

The `doc/` folder follows the suite's numbered scheme. The Phase 1
documents are:

| File | Content |
|------|---------|
| `doc/00_foundation_architecture.md` | Architecture, data model, engine contract, integrations, security, menu, phasing. |
| `doc/02_regulatory_analysis.md` | Regulatory statement, Truth Protocol, 25 open questions. |
| `doc/05_architecture_review.md` | Convention compliance, consolidation of the 17 domains, assumptions, deviations, risks. |
| `CHANGELOG.md` | Release history. |

## License

AGPL-3.0 or later.
