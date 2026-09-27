# Phase 2 — Regulatory Analysis

Module: `ls_import_export` — Life Sciences - Import & Export Compliance

---

## 1. Statement of what this document is and is not

This module **supports** an organisation in implementing the
foreign-trade compliance processes that several Algerian and
international frameworks require. It does **not** make an organisation
compliant, and nothing in it is certified against any framework.
Compliance depends on the organisation's procedures, the validation it
performs, the competence of its staff and the way it actually uses the
system.

Each requirement the module enforces is backed by a **cited provision**
recorded in the registry (`ls.import_export.provision`) with a source
and an effective date. Where a provision is paraphrased, it is
paraphrased; the module does not reproduce regulatory text.

**This Phase 1 document asserts no specific Algerian regulatory
provision as currently in force.** The reason is given in §2 and the
consequence in §3. This is the operational form of the suite's Truth
Protocol: rather than invent mappings from training-data knowledge of
Algerian law — which is unverifiable, dated and therefore unsafe in a
regulated domain — the module ships a **structured, empty registry**
and a **list of open questions** to be answered source by source.

## 2. Frameworks considered, and the verification status of each

The table below lists the frameworks the module is *designed to
accommodate*. "Designed to accommodate" means the registry and the
engine can hold and evaluate provisions from that framework. It does
**not** mean the module asserts that any specific provision of that
framework exists, is currently in force, or applies to a given
operation. That determination is made per provision, with a cited
source, by the organisation.

| Framework | Verification status | Position in this Phase 1 document |
|-----------|---------------------|------------------------------------|
| ANPP (Agence Nationale des Produits Pharmaceutiques, Algeria) — authorisations, licensing, import/export of pharmaceutical products | **NOT VERIFIED** | No provision asserted. Open questions in §3. |
| Ministère de l'Industrie Pharmaceutique (Algeria) | **NOT VERIFIED** | No provision asserted. Open questions in §3. |
| Douanes algériennes / Direction Générale des Douanes (DGD) — customs procedures, tariff, declarations | **NOT VERIFIED** | No provision asserted. Open questions in §3. |
| Réglementation du commerce extérieur (Algeria) — licensing of imports/exports, lists of goods | **NOT VERIFIED** | No provision asserted. Open questions in §3. |
| Banque d'Algérie — foreign exchange, domiciliation, repatriation of export proceeds | **NOT VERIFIED** | No provision asserted. Open questions in §3. |
| PPI (Programme Prix à l'Importation / Produits à l'Importation) — when applicable | **NOT VERIFIED** | No provision asserted. Open questions in §3. The very scope and current name of the mechanism are treated as open. |
| Incoterms® (ICC) | **VERIFIED as a published standard** | The module uses Odoo's native Incoterms; no behavioural assertion beyond recording the Incoterm chosen on an operation. |
| WTO / HS Convention (tariff nomenclature) | **VERIFIED as a published standard** | The module accommodates HS codes as data; it does not assert any specific heading or rate. |
| ICH / EudraLex / ISO (life-sciences quality) | **VERIFIED as published standards** | Relevant where the *product* is regulated (quality, traceability). These are quality frameworks, not foreign-trade frameworks; they are supported through integration with the suite's QMS modules, not asserted here. |

**Why every Algerian framework is NOT VERIFIED.** Algerian regulatory
texts governing pharmaceutical and medical-device foreign trade
(ANPP authorisations, ministry licensing, customs procedures, banking
domiciliation, the commerce-extérieur regime) change over time, are
published across multiple official journals and ministry sites, and
include instruments whose current applicability must be read against
the latest text. Asserting a specific provision as in force, from
unverifiable training-data knowledge, would violate the Truth Protocol
and could mislead an implementing organisation in a regulated domain.
The module therefore asserts none until each is recorded with a cited
source and a verified effective date.

## 3. Open regulatory questions

These are the questions the registry must answer, source by source,
before the corresponding behaviour is enabled. Each is mirrored on
first install as an `ls.import_export.regulatory.question` record
(status `open`). Until answered and backed by a cited provision, the
engine returns *registry gap* for the related requirement rather than
enforcing or waiving anything.

### 3.1 ANPP and pharmaceutical authorisations

| # | Question |
|---|----------|
| Q-01 | Which pharmaceutical product categories require an ANPP authorisation prior to import? What is the current instrument that establishes this, and what is its effective date? |
| Q-02 | Is a separate import licence required for active pharmaceutical ingredients (API), and under which current text? |
| Q-03 | Is a separate authorisation required for imported primary packaging materials in contact with pharmaceutical products, and under which text? |
| Q-04 | Which documents must accompany an ANPP import authorisation file (pro forma invoice, certificate of analysis, GMP certificate, etc.), as established by the current applicable text? |
| Q-05 | What are the validity, renewal and amendment rules for an ANPP authorisation, per the current text? |
| Q-06 | What are the current ANPP notification/reporting obligations on import (batch-level, quantity-level), and under which text? |

### 3.2 Medical devices and cosmetics

| # | Question |
|---|----------|
| Q-07 | Which medical-device import authorisations or registrations are currently required, and by which authority under which text? |
| Q-08 | Are cosmetic raw materials / finished cosmetics subject to a specific import authorisation, and under which current text? |
| Q-09 | Do medical-device and cosmetic imports require conformity certificates, and under which text? |

### 3.3 Customs

| # | Question |
|---|----------|
| Q-10 | Which customs regimes apply to life-sciences imports (e.g. consumption, temporary admission, warehouse), and what is the current procedural text for each? |
| Q-11 | What is the current tariff treatment (HS headings and applicable duties/taxes) for the product categories in scope? (To be entered per heading, with the tariff schedule as source.) |
| Q-12 | What are the current document requirements for customs clearance of the in-scope product categories (commercial invoice, packing list, bill of lading / air waybill, certificate of origin, etc.), per the customs procedural text? |
| Q-13 | Are there current exemptions or suspensions of duty/tax applicable to pharmaceutical / device / cosmetic imports, and under which text? |
| Q-14 | What is the current declaration procedure (electronic system, forms), and under which text? |

### 3.4 Banking and foreign trade

| # | Question |
|---|----------|
| Q-15 | What is the current domiciliation requirement for imports and exports, and under which text (Bank of Algeria / currency regulation)? |
| Q-16 | What are the current rules on repatriation of export proceeds, and under which text? |
| Q-17 | What are the current foreign-exchange rules affecting payment for imports, and under which text? |
| Q-18 | What are the current time limits and procedural steps of the domiciliation file, and under which text? |

### 3.5 Commerce extérieur and licensing

| # | Question |
|---|----------|
| Q-19 | Which goods are currently subject to an import licence or a prior authorisation under the commerce-extérieur regime, and under which current text/list? |
| Q-20 | Are there current temporary or permanent import bans/restrictions affecting the in-scope categories, and under which text? |
| Q-21 | What are the current export licensing requirements for pharmaceutical / device / cosmetic finished products, and under which text? |

### 3.6 PPI and pricing

| # | Question |
|---|----------|
| Q-22 | What is the current scope and name of the import-pricing / PPI mechanism, and which text establishes it? (The mechanism's current applicability and name are treated as open and must not be assumed.) |
| Q-23 | Where PPI applies, what are the current procedural steps, documents and deadlines, and under which text? |

### 3.7 Documentation and traceability

| # | Question |
|---|----------|
| Q-24 | What are the current mandatory documents per operation type (import vs export) and per product category, aggregating the answers above into the dossier engine? |
| Q-25 | What are the current record-retention requirements for foreign-trade documents, and under which text? |

**How these get answered.** Each question is closed by recording a
cited provision (`ls.import_export.provision`) with source, effective
date and status, then linking it to the question's
`answer_provision_id`. The corresponding compliance requirement is
then created against that provision. Until then, the related behaviour
is not enabled. This is the mechanism that keeps the module honest as
texts evolve.

## 4. What the module does *before* the questions are answered

Phase 1 ships the **registry and the engine contract** only. It does
not enforce any of the requirements above, because none of them is yet
backed by a cited provision. Concretely:

* The operator can create provisions, citations, requirements and
  questions.
* The engine evaluates a requirement only against its backing
  provisions; a requirement with no in-force backing provision returns
  *registry gap*.
* Expiry alerts fire only on authorisations whose validity dates the
  operator has entered (Phase 3 onwards).
* Cost calculation (Phase 5) never invents a regulated rate: a
  regulated cost line requires a cited provision establishing the rate;
  an unregulated cost line (e.g. a negotiated freight rate) does not.

This means a freshly installed module is, by design, **inert**. It
becomes active only as the registry is populated with verified
provisions. Inertness here is a feature, not a gap: it is the
guarantee that the module will never enforce a rule that has not been
read and cited.

## 5. Data integrity (ALCOA+) — honest position

| Principle | Position |
|-----------|----------|
| Attributable | Supported. Every workflow action records the acting user; Odoo's chatter records field changes on tracked fields. |
| Legible | Supported. |
| Contemporaneous | Partly. The system timestamps when an entry is *made*, which is not necessarily when the event occurred. |
| Original | Partly. The module holds the record of the action; it is not the original of a paper customs or banking document. |
| Accurate | Supported by constraints, not guaranteed. |
| Complete, Consistent, Enduring, Available | Supported at application level; depends on the organisation's backup, retention and archival arrangements, which are outside the module. |

A full audit trail over every field of every model is **not** provided
by this module. Odoo's chatter tracks the fields marked `tracking=True`.
A general field-level audit trail is the concern of the suite's
`ls_audit_trail` module, which is **not** a dependency here; the
administrator creates audit rules (`ls.audit_trail.rule`) for this
module's models at runtime, per the suite's loose-coupling convention.

## 6. Place reserved for verified provisions

Section 6 of `13_validation_report.md` (to be produced in a later
phase) will reserve a place for each provision as it is verified and
entered — authority, reference, source, effective date, status, and
the requirements it backs. Until a provision appears there with a
verified source, the module asserts nothing about it.
