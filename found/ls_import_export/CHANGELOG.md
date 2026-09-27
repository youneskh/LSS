# Changelog — ls_import_export

All notable changes to this module are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [19.0.1.0.0] — 2026-08-03 — Phase 1 (foundation)

### Added
- Module scaffold (`__manifest__.py`, `__init__.py`) following the
  verified suite conventions (category `Life Sciences/Quality`,
  version `19.0.1.0.0`, license AGPL-3, author
  "Life Sciences Suite Architecture Team").
- Directory structure: `models/ views/ security/ data/ demo/ report/
  wizards/ tests/ static/description/ doc/ i18n/`.
- Phase 1 foundation documentation:
  - `doc/00_foundation_architecture.md` — architecture, data model,
    generic compliance-engine contract, integrations, security model,
    menu structure, five-phase roadmap.
  - `doc/02_regulatory_analysis.md` — regulatory statement, Truth
    Protocol, 25 open regulatory questions seeded as
    `ls.import_export.regulatory.question` records.
  - `doc/05_architecture_review.md` — convention compliance, loose
    coupling to other `ls_*` modules, consolidation of the original
    17 domains into four clusters, registered assumptions and
    deviations.

### Design decisions
- **Two-layer architecture:** a cited regulatory provision registry
  (Algeria) configures a country-agnostic compliance engine.
- **Registry ships empty.** No regulatory provision is asserted as in
  force. The engine returns *registry gap* for any requirement lacking
  a cited, in-force provision, rather than enforcing or waiving it.
- **Loose coupling.** Hard-depends only on Odoo core
  (`mail`, `product`, `stock`, `uom`, `account`, `purchase`, `sale`).
  Integration with `ls_audit_trail`, `ls_document_management`,
  `ls_qms`, `ls_supplier_qualification`, `ls_pharma`, `ls_recall` is
  by the suite's loose-coupling mechanisms, with no `depends` entries.
- **Provision editing restricted to the manager group** (deviation
  D-03): the registry is the trusted root of the whole module.

### Not included (intentional)
- No operational models (authorisations, operations, shipments,
  dossiers, customs, banking, KPI, cost) — Phases 2–5.
- No asserted regulatory content — by Truth Protocol, the registry is
  filled source by source.
- No views, menus or security XML shipped as loadable data yet in this
  commit — the data files are referenced by the manifest and will be
  populated as the Phase 1 models are implemented. The manifest lists
  them so the load order is fixed.

### Open items
- 25 open regulatory questions (see `doc/02_regulatory_analysis.md` §3).
- 4 open architecture decisions (see `doc/05_architecture_review.md` §7).
