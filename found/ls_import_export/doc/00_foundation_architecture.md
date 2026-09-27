# Phase 0 — Foundation Architecture

Module: `ls_import_export` — Life Sciences - Import & Export Compliance

---

## 0. Document status and Truth Protocol

**Status:** Phase 1 deliverable (foundation). This document fixes the
architecture for all subsequent phases. It is reviewable and must be
approved before model implementation begins in Phase 2.

**Truth Protocol (suite-wide).** Every claim about the existing
codebase is tagged against the actual code under `addons/`. Every
claim about regulation is tagged against an official source. The
tags are:

| Tag | Meaning |
|-----|---------|
| **VERIFIED** | Checked against the code under `addons/` or against a cited official source in this module's `02_regulatory_analysis.md`. |
| **CUSTOM DEVELOPMENT** | Code to be written in this module; does not yet exist. |
| **ASSUMPTION** | A design choice that has not been validated against code or text and is flagged for verification. |
| **NOT ASSERTED** | A regulatory requirement that the module deliberately does not claim, because it could not be verified from official documentation. The open question is recorded in `02_regulatory_analysis.md` §3 and in `ls.import_export.regulatory.question`. |

**Core rule of this module.** No regulatory requirement, document
requirement, cost component, threshold or deadline is asserted by the
module's behaviour unless it is first recorded as a **cited provision**
in `ls.import_export.provision` with a source, an effective date and a
status of *in force*. Behaviour that has no backing provision is, by
construction, impossible. This is the operational form of the Truth
Protocol.

---

## 1. What this module is, and what it is not

### 1.1 What it is

A **foreign-trade compliance platform** for the regulated
life-sciences sectors (pharmaceutical, medical devices, cosmetics)
operating in or from Algeria. It is structured as two layers:

1. A **generic compliance engine** (agnostic of country) that performs
   verifications, expiry alerts, configurable cost calculation, dossier
   preparation and tracking.
2. A **cited regulatory provision registry** that *configures* the
   engine for Algeria, and that could configure it for another
   jurisdiction later.

It is a **Premium module** of the Life Sciences Suite and sits in the
**Regulatory Affairs** domain.

### 1.2 What it is not

* It is **not** a purchase module, a sales module, an inventory module,
  an accounting module or a landed-cost engine. Those exist in Odoo and
  in the suite; this module *integrates* with them, it does not replace
  them. **CUSTOM DEVELOPMENT**
* It is **not** a regulatory oracle. It does not certify compliance
  with ANPP, the Customs administration, the Bank of Algeria or any
  ministry. An organisation's compliance depends on its procedures, its
  validation, the competence of its staff and the way it actually uses
  the system. **NOT ASSERTED** for any specific regulatory regime —
  see `02_regulatory_analysis.md`.
* It is **not** a source of law. The registry records provisions the
  organisation has entered and cited; it does not assert that a
  provision is currently in force unless a human has recorded that fact
  with a source and a date.

---

## 2. Functional perimeter

The full perimeter requested for this module. Phase 1 does not deliver
all of it; it delivers the registry and the engine contract. The table
records, for each domain, the cluster it belongs to, whether it is new
or an extension, and the phase in which it is built.

| # | Domain | Cluster | Build mode | Phase |
|---|--------|---------|------------|-------|
| 1 | Import Management | Operations | Extension + new | 4 |
| 2 | Export Management | Operations | Extension + new | 4 |
| 3 | Supplier Compliance | Compliance core | New | 3 |
| 4 | Customer Export Compliance | Compliance core | New | 3 |
| 5 | Regulatory Authorization | Compliance core | New | 3 |
| 6 | Customs Management | Compliance core | New | 3 |
| 7 | Banking & Foreign Trade | Compliance core | New | 3 |
| 8 | Shipment Management | Operations | New | 4 |
| 9 | Freight Forwarder Management | Operations | Categorisation of partners | 3 |
| 10 | Customs Broker Management | Operations | Categorisation of partners | 3 |
| 11 | Document Management | Reuse Odoo | Use `ls.document.link` from document side | — |
| 12 | Cost Management | Reuse Odoo | Build on `account` + Landed Costs | 5 |
| 13 | Incoterms Management | Reuse Odoo | Native Odoo `sale`/`purchase` | — |
| 14 | Currency Management | Reuse Odoo | Native Odoo; contextual only | — |
| 15 | Import KPI | Intelligence | New | 5 |
| 16 | Export KPI | Intelligence | New | 5 |
| 17 | Audit Trail | Intelligence | Use `ls_audit_trail` engine, no dependency | — |

### 2.1 The four clusters

**Cluster A — Compliance core (the module's real value).** Regulatory
Authorization, Customs Management, Banking & Foreign Trade, Supplier
Compliance, Customer Export Compliance. This is where the cited
provision registry lives and where compliance is enforced.

**Cluster B — Operations.** Import Management, Export Management,
Shipment & Container Tracking, Freight Forwarder and Customs Broker
partner categorisation. These are the day-to-day flows that the
compliance core governs.

**Cluster C — Reuse Odoo.** Currency, Incoterms, Cost (via Landed
Costs) and Document Management. These are deliberately *not*
rebuilt; the module uses Odoo's native objects and the suite's
`ls.document.link` loose-coupling pattern. Building them here would
duplicate Odoo and violate the suite's loose-coupling convention
(see `05_architecture_review.md`).

**Cluster D — Intelligence.** Import/Export KPI, dashboards, audit.
Built last, on top of the operational data.

---

## 3. Architectural principle: regulation as cited data, not hardcoded logic

This is the single most important design decision in the module, and it
is the technical form of the Truth Protocol.

### 3.1 The rule

Every enforceable behaviour of the module — a required document, a
mandatory authorisation, a cost component, a threshold, a deadline — is
expressed as a **compliance requirement** that references one or more
**cited provisions**. A cited provision is a record of a regulatory
text, with:

* a **reference** (law, decree, order, instruction, tariff heading…)
* an **official source** (URL or archived attachment)
* an **effective date**, and where relevant an end date
* a **scope of application** (product category, operation type,
  origin/destination country)
* explicit **applicability conditions**
* a **status**: *in force* / *repealed* / *amended* / *under review*

No behaviour is asserted from a provision whose status is not
*in force*. When the regulation changes, the registry is updated; the
code does not change. This is what makes the module auditable and
durable.

### 3.2 Two layers

```
+-------------------------------------------------------------+
|  Algerian regulatory provisions (registry content)          |
|  ANPP · Ministry · Customs · Bank of Algeria · Foreign trade|
|  Each one CITED, with source + effective date + status.     |
+-------------------------------------------------------------+
                        | configures
                        v
+-------------------------------------------------------------+
|  Generic compliance engine (country-agnostic)               |
|  - requirement evaluation                                   |
|  - expiry alerts                                            |
|  - configurable cost calculation                            |
|  - dossier preparation                                      |
|  - tracking                                                 |
+-------------------------------------------------------------+
                        | drives
                        v
+-------------------------------------------------------------+
|  Operations: imports, exports, shipments                    |
+-------------------------------------------------------------+
```

The engine never reads "Algeria" or "ANPP" in its code. It reads the
registry. A future Tunisia or Morocco configuration would be a second
set of registry entries, not a fork.

### 3.3 The honest limit

The registry is **empty by default**. It ships with **no asserted
provision**. Every entry is created by a human who has read the source,
cited it and dated it. The module makes it structurally impossible to
enforce a rule that has not been recorded and cited; it also makes it
structurally impossible for the engine to invent a rule. Where a rule
is expected but not yet verified, the expectation is recorded as a
**regulatory question** (`ls.import_export.regulatory.question`) to be
answered by a qualified adviser, not guessed by the module.

---

## 4. Data model (Phase 1 ships the registry; later phases add the rest)

### 4.1 Models shipped in Phase 1

| Model | `_name` | Role |
|-------|---------|------|
| Provision | `ls.import_export.provision` | A cited regulatory text. The atomic unit of the registry. |
| Citation | `ls.import_export.provision.citation` | A verbatim quote or paraphrase of a passage of a provision, with its exact location (article, page). Multiple citations per provision. |
| Regulatory question | `ls.import_export.regulatory.question` | An open question about a requirement that has not yet been verified; to be answered by a qualified adviser. |
| Compliance requirement | `ls.import_export.compliance.requirement` | An enforceable requirement (document, authorisation, cost component, threshold, deadline) backed by one or more cited provisions. This is what the engine evaluates. No backing provision => no requirement. |

### 4.2 Models added in later phases (contract fixed now, code later)

| Model | `_name` | Phase | Role |
|-------|---------|-------|------|
| Authorization | `ls.import_export.authorization` | 3 | A licence / authorisation / registration held by the organisation (e.g. import licence, ANPP authorisation, banking domiciliation). Has validity dates that drive expiry alerts. |
| Operation | `ls.import_export.operation` | 4 | An import or export operation. Links to purchase/sales orders, shipments, authorisations, dossiers. |
| Shipment | `ls.import_export.shipment` | 4 | A physical shipment with containers, Incoterm, freight forwarder, customs broker, tracking events. |
| Container | `ls.import_export.container` | 4 | A container / consignment within a shipment. |
| Dossier | `ls.import_export.dossier` | 4 | The set of documents required for an operation, checked against requirements. |
| Dossier line | `ls.import_export.dossier.line` | 4 | One required document in a dossier, with status. |
| Customs declaration | `ls.import_export.customs.declaration` | 3 | A customs declaration linked to an operation. |
| Banking file | `ls.import_export.banking.file` | 3 | A banking domiciliation / foreign-trade banking file. |
| Cost estimate | `ls.import_export.cost.estimate` | 5 | A configurable landed-cost estimate (transport, insurance, duties, taxes, configurable fees). |
| Cost line | `ls.import_export.cost.line` | 5 | One line of a cost estimate, each line backed by a cited provision where the cost is regulated. |

### 4.3 Provision registry schema (Phase 1, detailed)

`ls.import_export.provision` — a cited regulatory text.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | Short human title. |
| `code` | Char | Sequence `IEP/####`, unique, allocated on creation. |
| `authority` | Selection | Issuing body: ANPP, Ministry of Pharmaceutical Industry, Customs (DGD), Bank of Algeria, Ministry of Trade, other. **CUSTOM DEVELOPMENT**; the list is editable master data, not a claim that any of these bodies has issued a specific provision. |
| `instrument_type` | Selection | Law, decree, order, instruction, circular, tariff schedule, regulation, other. |
| `reference` | Char | The official reference number / citation of the text. |
| `source_url` | Char | Official URL. |
| `source_attachment_id` | Many2one `ir.attachment` | Archived copy of the source (PDF). |
| `effective_date` | Date | Date of entry into force. |
| `end_date` | Date | Date of abrogation / replacement, if any. |
| `status` | Selection | `in_force`, `repealed`, `amended`, `under_review`. |
| `jurisdiction` | Char | Country / jurisdiction (e.g. "Algeria"). |
| `product_category_scope` | Many2many `product.category` | Product categories the provision applies to, if scoped. |
| `operation_type_scope` | Selection | `import`, `export`, `both`, `none`. |
| `summary` | Text | Neutral paraphrase of what the provision requires. **Never** a claim that it is currently in force unless `status = in_force`. |
| `citation_ids` | One2many → `ls.import_export.provision.citation` | Verbatim / paraphrased passages with their location. |
| `requirement_ids` | One2many → `ls.import_export.compliance.requirement` | The requirements that cite this provision. |
| `company_id` | Many2one `res.company` | Multi-company; required. |
| `active` | Boolean | Archive. |
| State / chatter | — | `mail.thread` + `mail.activity.mixin`. |

`ls.import_export.provision.citation` — a located quote.

| Field | Type | Notes |
|-------|------|-------|
| `provision_id` | Many2one → `ls.import_export.provision` | Parent. |
| `locator` | Char | Article / paragraph / page, e.g. "Art. 12". |
| `quote_type` | Selection | `verbatim`, `paraphrase`. |
| `text` | Text | The quote or paraphrase. |
| `language` | Selection | Language of the source passage. |

`ls.import_export.compliance.requirement` — an enforceable requirement.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | Short human title. |
| `code` | Char | Sequence `IEC/####`. |
| `requirement_type` | Selection | `document`, `authorization`, `cost_component`, `threshold`, `deadline`, `procedure`. |
| `provision_ids` | Many2many → `ls.import_export.provision` | **Required, non-empty.** A requirement with no backing provision is refused by a constraint. This is the Truth-Protocol guard at data level. |
| `product_category_scope` | Many2many `product.category` | |
| `operation_type_scope` | Selection | `import`, `export`, `both`. |
| `config` | Json / Text | Engine-specific configuration (e.g. for a cost component, the configurable parameters). Kept opaque in Phase 1; typed in later phases. |
| `active` | Boolean | |
| `company_id` | Many2one `res.company` | |
| State / chatter | — | |

`ls.import_export.regulatory.question` — an open question.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | The question. |
| `question_type` | Selection | `document_required`, `authorization_required`, `threshold`, `deadline`, `procedure`, `cost_component`, `other`. |
| `context` | Text | Why the question is open and what depends on the answer. |
| `expected_provision_ref` | Char | The reference the answer is expected to cite, if known. |
| `status` | Selection | `open`, `answered`, `wont_answer`. When `answered`, links to the provision that answers it. |
| `answer_provision_id` | Many2one → `ls.import_export.provision` | Filled when answered. |
| `company_id` | Many2one `res.company` | |
| State / chatter | — | |

### 4.4 Constraints (the Truth-Protocol guards)

* `ls.import_export.compliance.requirement`: a SQL/constraint rejecting
  any requirement whose `provision_ids` is empty. A requirement without
  a cited provision cannot exist. **CUSTOM DEVELOPMENT.**
* `ls.import_export.provision`: a requirement cannot reference a
  provision whose `status` is not `in_force` at evaluation time; the
  engine refuses to evaluate such a requirement and surfaces it as a
  *registry gap* instead of enforcing or waiving it.
* Provision `effective_date` must be present; `end_date`, if set, must
  be on or after `effective_date`.

---

## 5. Generic compliance engine (contract fixed in Phase 1)

The engine is the country-agnostic layer. In Phase 1 its **contract**
is fixed; its behaviours are implemented as the operational models
arrive in later phases. The contract has four parts.

### 5.1 Requirement evaluation

```
evaluate(requirement, operation_context) -> EvaluationResult
```

Given a compliance requirement and an operation context (product
categories, operation type, origin/destination, dates), the engine
returns one of: *satisfied*, *not satisfied*, *not applicable*, or
*registry gap* (the backing provision is not in force or is missing).
The engine **never** returns *satisfied* or *not satisfied* on the
basis of an uncited or out-of-force provision: in that case it returns
*registry gap* and records a regulatory question.

### 5.2 Expiry alerts

Authorisations and provisions carry validity/effective dates. A
scheduled action (cron) scans for records nearing expiry and creates
activities on the responsible user. The lead time is configurable
through an `ir.config_parameter`. **CUSTOM DEVELOPMENT.**

### 5.3 Configurable cost calculation

Cost lines are configurable; where a cost is regulated (a duty rate, a
tax), the cost line must reference a cited provision that establishes
it. Unregulated costs (a negotiated freight rate) need no provision.
The calculator sums configured lines and never invents a regulated
rate. Builds on Odoo `account` and on **Landed Costs** (Enterprise)
where available; falls back to its own journal posting otherwise.
**CUSTOM DEVELOPMENT; Landed Costs integration is an ASSUMPTION pending
Phase 5 verification of the Enterprise availability in this instance.**

### 5.4 Dossier preparation

Given an operation, the engine builds the set of required documents by
selecting every `document`-type requirement whose scope matches, each
backed by cited provisions. Missing requirements (no backing provision
in force) are surfaced as *registry gaps*, not silently dropped.

---

## 6. Integrations

Integrations follow the suite's **loose-coupling convention**: the
module hard-depends only on Odoo core; it integrates with other `ls_*`
modules either through their public abstract mixins or through the
loose-coupling models, **without adding them to `depends`**. This is
verified convention (see `05_architecture_review.md` §1).

| Integration | How | Dependency? |
|-------------|-----|-------------|
| Purchase | `purchase.order`/`purchase.order.line` extension fields + smart-buttons | `purchase` in `depends` (core) |
| Sales | `sale.order` extension fields + smart-buttons | `sale` in `depends` (core) |
| Inventory / Stock | `stock.picking`, `stock.move`, `stock.quant` links to operations/shipments | `stock` in `depends` (core) |
| MRP | Link production orders to import operations for raw materials | runtime check, **not** in `depends` |
| Quality | Link quality control points to incoming shipments | runtime check, **not** in `depends` |
| Accounting | `account.move` for cost postings | `account` in `depends` (core) |
| Landed Costs | `stock.landed.cost` when Enterprise available | runtime check, **not** in `depends` (**ASSUMPTION**) |
| Maintenance | Link imported spare parts / equipment to maintenance equipment | runtime check, **not** in `depends` |
| QMS (`ls_qms`) | Shared Regulatory Affairs domain; no hard dependency | **not** in `depends` |
| Documents (`ls_document_management`) | `ls.document.link` from the document side | **not** in `depends` |
| Audit Trail (`ls_audit_trail`) | Admin creates `ls.audit_trail.rule` for this module's models | **not** in `depends` |
| Supplier Qualification (`ls_supplier_qualification`) | Supplier compliance references qualification records by `res_id`/`res_model`, no dependency | **not** in `depends` |
| Batch Traceability (`ls_pharma`) | Operation lines reference lots by `res_id`/`res_model` | **not** in `depends` |
| Recall (`ls_recall`) | A recall may reference an affected import/export operation by `res_id`/`res_model` | **not** in `depends` |

### 6.1 Why no hard dependency on `ls_*` modules

Verified convention: no `ls_*` module in the suite depends on another
`ls_*` module for cross-cutting concerns. Audit is intercepted globally
by `ls_audit_trail` through `base` inheritance; documents are linked
through `ls.document.link`; supplier qualification, batch traceability
and recall are referenced by `res_model`/`res_id`. Hard-dependencies
would force an install order the suite deliberately avoids, and would
make this Premium module uninstallable on a minimal Odoo. This module
follows the same convention. **VERIFIED** against `addons/`.

---

## 7. Security model (Odoo 19 privilege pattern)

Follows the verified suite pattern (`ir.module.category` ->
`res.groups.privilege` -> `res.groups` with `privilege_id`), as in
`ls_qms` and `ls_recall`. **CUSTOM DEVELOPMENT** here, modelled on
**VERIFIED** convention.

* Category: `module_category_ls_import_export` ("Life Sciences").
* Privilege: `res_groups_privilege_ls_import_export` ("Import & Export
  Compliance").
* Groups (XML IDs):
  - `group_ls_import_export_viewer` — read-only.
  - `group_ls_import_export_user` — operates imports/exports; implies
    viewer.
  - `group_ls_import_export_officer` — manages authorisations, customs,
    banking files; implies user.
  - `group_ls_import_export_manager` — full, including registry edits;
    implies officer.
* Record rule: global multi-company isolation on `company_id`.
* `ir.model.access.csv`: three rows per model (viewer read; user
  read+write+create; manager full).

A deliberate restriction: **only the manager group may create or edit
`ls.import_export.provision` records**, because the registry is the
trusted root of the whole module. Editing a provision is a regulated
act and must be controlled. Officers and users may *read* provisions
and *create* requirements that cite them.

---

## 8. Menu structure (own root menu, per suite convention)

The module defines its own top-level root menu
`menu_ls_import_export_root` with a `web_icon`, restricted to the
viewer group, per the verified convention (no shared parent menu
exists in the suite). **CUSTOM DEVELOPMENT.**

```
Import & Export Compliance (root, sequence ~80)
 |
 +-- Operations                 (Phase 4)
 |   +-- Imports
 |   +-- Exports
 |   +-- Shipments
 |   +-- Containers
 |
 +-- Compliance                 (Phase 3)
 |   +-- Authorisations
 |   +-- Customs Declarations
 |   +-- Banking Files
 |   +-- Supplier Compliance
 |   +-- Customer Export Compliance
 |
 +-- Registry                   (Phase 1)   <-- shipped now
 |   +-- Provisions
 |   +-- Compliance Requirements
 |   +-- Regulatory Questions
 |
 +-- Intelligence               (Phase 5)
 |   +-- Import KPI
 |   +-- Export KPI
 |   +-- Dashboards
 |
 +-- Configuration (sequence 90, base.group_system / manager)
     +-- Authorities
     +-- Sequences
     +-- Cron jobs
```

In Phase 1, only the **Registry** section and the **Configuration**
section are populated. The other sections are placeholders so the menu
shape is stable as phases land.

---

## 9. Phasing

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **Phase 1** | Registry (`provision`, `citation`, `regulatory.question`, `compliance.requirement`), engine contract, architecture, regulatory analysis with open questions. | **This deliverable.** |
| Phase 2 | Full data model implementation of Cluster A + B entities (authorisation, operation, shipment, container, dossier, customs declaration, banking file). | Planned |
| Phase 3 | Compliance core behaviours (requirement evaluation, expiry alerts, supplier/customer compliance). | Planned |
| Phase 4 | Operations (import/export flows, shipment tracking, dossier preparation). | Planned |
| Phase 5 | Intelligence (KPI, cost calculation, dashboards, reports). | Planned |

Phase 1 is deliberately **non-behavioural**: it ships the registry that
all later behaviour depends on, and it ships *no asserted regulatory
content*. Filling the registry with cited Algerian provisions is a
separate, source-by-source effort documented in
`02_regulatory_analysis.md`.

---

## 10. Open items requiring a decision before Phase 2

These are recorded here so they are visible; they are also mirrored as
regulatory questions in the module's registry on first install.

1. **Landed Costs availability.** Is Odoo **Enterprise** (and therefore
   `stock_landed.cost`) available in this instance, or is this Community
   Edition only? Determines whether Phase 5 cost posting reuses
   `stock.landed.cost` or posts its own `account.move`. **ASSUMPTION:
   Community Edition only; own posting.** To confirm.
2. **Multi-company.** Is the module expected to serve one Algerian
   company, or several companies (e.g. a holding with pharma + device
   + cosmetics subsidiaries)? Affects default scopes and record rules.
3. **Languages.** Regulatory texts and citations are entered in their
   source language; should the UI ship French + Arabic + English, or
   French + English only? Affects `i18n` effort.
4. **Registry authority.** Reviewing and approving provisions is a
   regulated act. Should it require an electronic signature (suite's
   `ls.signature.mixin`) or is manager-group approval sufficient for
   Phase 1? Current design: manager-group approval; signature deferred.
