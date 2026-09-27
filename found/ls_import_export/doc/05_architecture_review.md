# Phase 5 — Architecture Review

Module: `ls_import_export` — Life Sciences - Import & Export Compliance

---

## 1. Convention compliance (verified against the codebase)

This module follows every load-bearing convention of the Life Sciences
Suite, as verified against `addons/` at the time of writing.

| Convention | This module | Match |
|------------|-------------|-------|
| Version `"19.0.1.0.0"` | `"19.0.1.0.0"` | ✓ |
| License `"AGPL-3"` + header | `"AGPL-3"` + header | ✓ |
| Author `"Life Sciences Suite Architecture Team"` | same | ✓ |
| Category `"Life Sciences/Quality"` | same | ✓ |
| `application: True`, `installable: True`, `auto_install: False` | same | ✓ |
| Folders: `models/ views/ security/ data/ demo/ report/ wizards/ tests/ static/description/ doc/ i18n/` | same | ✓ |
| Model `_name = "ls.<entity>"` | `ls.import_export.<entity>` | ✓ |
| Primary model `_inherit = ["mail.thread", "mail.activity.mixin"]` | same | ✓ |
| `company_id` (required, indexed, default `env.company`) | same | ✓ |
| Odoo 19 security: `ir.module.category` → `res.groups.privilege` → `res.groups` | same | ✓ |
| Group IDs `group_ls_<module>_<role>` | `group_ls_import_export_<role>` | ✓ |
| Own root menu `menu_ls_<module>_root` with `web_icon`, viewer group | same | ✓ |
| `security/ir.model.access.csv`, 3 rows per model | same | ✓ |
| Data load order: groups → access → sequences → cron → … → menus last | same | ✓ |
| `doc/` numbered scheme `01_… 15_…` + `CHANGELOG.md` + `RELEASE_NOTES.md` | same | ✓ |

Verification tag: **VERIFIED** against `ls_qms`, `ls_recall`,
`ls_supplier_qualification`, `ls_document_management`, `ls_audit_trail`.

## 2. Loose coupling to other `ls_*` modules

Verified finding: **no `ls_*` module in the suite depends on another
`ls_*` module** for cross-cutting concerns. Cross-module integration is
done by:

* global `base` interception for audit (`ls_audit_trail`);
* a loose-coupling link model for documents (`ls.document.link`);
* `res_model`/`res_id` references for qualification, traceability and
  recall.

This module follows the same pattern. It hard-depends only on Odoo core
(`mail`, `product`, `stock`, `uom`, `account`, `purchase`, `sale`).
Integration with every `ls_*` module is by loose coupling, not by
`depends`. Verification tag: **VERIFIED**.

| `ls_*` module | Integration mechanism | In `depends`? |
|---------------|------------------------|---------------|
| `ls_audit_trail` | admin creates `ls.audit_trail.rule` for this module's models at runtime | No |
| `ls_document_management` | `ls.document.link` from the document side | No |
| `ls_qms` | shared Regulatory Affairs domain, no code dependency | No |
| `ls_supplier_qualification` | supplier compliance references qualification by `res_model`/`res_id` | No |
| `ls_pharma` (batch traceability) | operation lines reference lots by `res_model`/`res_id` | No |
| `ls_recall` | a recall may reference an affected operation by `res_model`/`res_id` | No |
| `ls_electronic_signature` | optional; if present, provision approval may use the signature mixin | No |

## 3. Consolidation of the original 17 domains

The source brief listed 17 sub-modules. This review consolidates them
into **four clusters** (see `00_foundation_architecture.md` §2.1) and
marks explicit reuse decisions, to avoid rebuilding Odoo native
capabilities.

| Original domain | Decision | Rationale |
|-----------------|----------|-----------|
| Currency Management | **Reuse Odoo native** | Odoo `res.currency` + multi-currency; only contextual use here. Rebuilding would duplicate core. |
| Incoterms Management | **Reuse Odoo native** | Odoo `account.incoterms` on `sale`/`purchase`. Only contextual use. |
| Cost Management | **Build on `account` + Landed Costs** | Regulated cost lines require a cited provision; posting reuses Odoo accounting. Enterprise Landed Costs used if available (ASSUMPTION, see §4). |
| Document Management | **Use `ls.document.link`** | Loose-coupling model of the suite; no dependency. |
| Audit Trail | **Use `ls_audit_trail` engine** | Global interception; no dependency. |
| Freight Forwarder / Customs Broker Management | **Partner categorisation** | These are `res.partner` categories/flags, not standalone modules. |
| All other domains | **New, in scope** | Import/Export Management, Authorizations, Customs, Banking, Shipments, Containers, Dossiers, KPI. |

Net effect: the module concentrates effort on its real value
(compliance core) and does not reinvent the Odoo layer. The functional
perimeter of the brief is fully covered; only the *implementation
boundary* moves.

## 4. Assumptions registered

Each assumption is flagged for verification before the phase that
depends on it.

| ID | Assumption | Affects | Verification needed before |
|----|------------|---------|----------------------------|
| A-01 | This Odoo instance is **Community Edition**; Landed Costs (`stock.landed.cost`) may be unavailable. | Phase 5 cost posting | Phase 5 (confirm edition; choose posting strategy) |
| A-02 | Manager-group approval is sufficient for registry edits in Phase 1; electronic signature deferred. | Phase 1 security model | Phase 2 (decision on `ls.signature.mixin`) |
| A-03 | Registry authorities (ANPP, DGD, Bank of Algeria, etc.) are exposed as editable master data, not as a fixed claim. | Phase 1 data | Confirmed safe; list is data, not assertion |
| A-04 | Multi-company default is a single Algerian company; record rules still enforce isolation. | Phase 1 security | Phase 2 (confirm multi-company scope) |

## 5. Deviations registered

Following the suite convention (deviations recorded in
`05_architecture_review.md`; cf. `ls_recall` deviation D-01).

### D-01 — Registry is shipped empty

**Deviation.** Unlike most suite modules that ship demo data showing
the intended behaviour, this module ships its registry **empty** and
asserts **no** regulatory provision.

**Reason.** Truth Protocol: asserting an Algerian regulatory provision
from unverifiable training-data knowledge is unsafe in a regulated
domain. The registry is filled source by source; each entry is cited
and dated by a human.

**Mitigation.** The 25 open regulatory questions in
`02_regulatory_analysis.md` §3 are seeded as `regulatory.question`
records (status `open`) so the work to populate the registry is
explicit and trackable. The engine returns *registry gap* rather than
silently enforcing or waiving anything.

**Consequence.** A freshly installed module is inert by design. This is
intended.

### D-02 — Own root menu, no shared parent

**Deviation.** The module defines its own top-level root menu
`menu_ls_import_export_root` rather than sitting under a shared
"Life Sciences" or "Regulatory Affairs" parent.

**Reason.** Verified: no shared parent menu exists in the suite. Each
`ls_*` module defines its own root. A shared parent would require a
core dependency the suite deliberately avoids. Same rationale as
`ls_recall` deviation D-01.

### D-03 — Provision editing restricted to the manager group

**Deviation.** `ls.import_export.provision` create/write is restricted
to `group_ls_import_export_manager`, more restrictive than the usual
"officer can create" pattern.

**Reason.** The registry is the trusted root of the entire module:
every enforced requirement depends on it. Editing a provision is
therefore a regulated act and must be tightly controlled.

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Registry stays empty; module remains inert | High by default | Medium (module is installed but unused) | The 25 seeded questions and the Phase-1 non-behavioural contract make this an explicit, managed state, not a hidden gap. |
| A cited provision is entered incorrectly (wrong status, wrong scope) | Medium | High (wrong requirement enforced) | Manager-only edit; citations record locator + quote type; the engine surfaces *registry gap* on any out-of-force provision. |
| Algerian texts change after a provision is entered | Certain over time | Medium (stale rule) | Provisions carry `end_date`/`status`; expiry alerts (Phase 3) cover authorisations; provision review is a documented periodic activity. |
| Organisation treats the registry as legal advice | Medium | High (misplaced reliance) | Stated plainly in `02_regulatory_analysis.md` §1 and in the README: the module is a tool, not a source of law. |

## 7. Open architecture decisions for Phase 2

These are technical, not regulatory (the regulatory open questions are
in `02_regulatory_analysis.md` §3).

1. **Cost posting strategy** (own `account.move` vs `stock.landed.cost`)
   — blocked on A-01.
2. **Signature on provision approval** — blocked on A-02.
3. **Dossier engine storage** — store dossier lines as records vs
   compute on demand from requirements. Lean towards stored, for
   auditability.
4. **Shipment tracking integration** — carrier APIs (Phase 4) are out
   of scope for Phase 1; tracking events are manual until then.
