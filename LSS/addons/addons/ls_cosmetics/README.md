# Life Sciences Suite — Cosmetics (`ls_cosmetics`)

Odoo 19.0 Community Edition · AGPL-3.0 · version `19.0.1.0.0`

Cosmetic formulation management, product safety reports, Product Information
Files, claim substantiation, labelling particulars and Algerian prior
authorisation dossiers.

---

## 1. What this module is, and what it is not

This module **supports** the implementation of processes required by
Regulation (EC) No 1223/2009 on cosmetic products. It does not certify
compliance, and installing it does not make an organisation compliant.
Compliance depends on procedures, trained personnel, a functioning quality
system, and the accuracy of the data entered.

Three statements are made explicitly because they are easy to get wrong:

1. **No annex substance data is shipped.** Annexes II to VI of Regulation
   (EC) No 1223/2009 are amended several times a year. An embedded snapshot
   would be stale on arrival and would lend false authority to whatever it
   contained. The `ls.cosmetic.restriction` model is an empty register that
   you populate from the current consolidated text, recording the source and
   consolidation date on every entry. Until an ingredient is linked to an
   annex entry, the module reports its status as **not evaluated** — never as
   compliant.

2. **The module does not verify the safety assessor's qualification.**
   Article 10(2) requires the Part B assessment to be carried out by a person
   holding a university qualification in pharmacy, toxicology, medicine or a
   similar discipline. The module records the assessor's name, address and
   qualification evidence, and requires the approval to be performed by that
   named person's user account. It cannot check a diploma.

3. **The date the last batch was placed on the market is entered manually.**
   The ten-year retention clock of Article 11(1) runs from that date. Odoo
   records commercial stock movements, not the regulatory act of placing a
   batch on the market. Deriving the date from a stock move would put an
   unverifiable value on a regulatory retention period, so the module asks a
   person for it.

---

## 2. Regulatory traceability

Each row maps a specific published provision to the specific field or
constraint that supports it. Provisions were read from the consolidated text
of Regulation (EC) No 1223/2009 and from Commission Regulation (EU)
No 655/2013.

### Regulation (EC) No 1223/2009

| Provision | Requirement | Where it lands |
|---|---|---|
| Art. 2(1)(a) | Definition of a cosmetic product | `product.template.ls_is_cosmetic` (help text carries the definition) |
| Art. 2(1)(k) | Definition of nanomaterial | `ls.cosmetic.ingredient.is_nanomaterial` |
| Art. 4 | A responsible person must exist | `ls.cosmetic.pif.responsible_person_id`, `responsible_person_basis`, `mandate_reference` (all required) |
| Art. 8 | Good manufacturing practice | `ls.cosmetic.pif.gmp_statement`, `gmp_standard`, `gmp_site_id`, `gmp_certificate_reference` |
| Art. 10(1) | A safety report must exist before market placement | `ls.cosmetic.safety_assessment`; `ls.cosmetic.pif._check_safety_assessment_approved` blocks activation without an approved report |
| Art. 10(1)(c) | The report must be kept up to date | `review_date`, `review_overdue`, `_cron_notify_review_due` |
| Art. 10(2) | Assessor qualification | `assessor_partner_id`, `assessor_address`, `assessor_qualification`, `assessor_qualification_attachment_ids`; `action_approve` refuses any user other than `assessor_user_id` |
| Art. 10(3) | Non-clinical studies and GLP | `non_clinical_glp_statement` |
| Art. 11(1) | File kept **10 years** after the last batch was placed on the market | `last_batch_market_date` → `retention_end_date` (`PIF_RETENTION_YEARS = 10`); `action_archive_file` refuses to archive early; `unlink` blocked outside draft |
| Art. 11(2)(a) | Description of the product | `product_description` |
| Art. 11(2)(b) | The safety report | `safety_assessment_id` |
| Art. 11(2)(c) | Manufacturing method + GMP statement | `manufacturing_method`, `gmp_statement` |
| Art. 11(2)(d) | Proof of the effect claimed | `claim_ids`, `no_claims_justification`; unapproved claims block activation |
| Art. 11(2)(e) | Animal testing data | `animal_testing_data` / `no_animal_testing`, enforced by `_check_animal_testing_item` |
| Art. 11(3) | File accessible at the labelled address, in an understandable language | `file_address` (required), `file_language_ids` |
| Art. 19(1)(a) | Responsible person name and address; country of origin if imported | `responsible_person_id`, `responsible_person_address`, `is_imported`, `country_of_origin_id` + `_check_country_of_origin` |
| Art. 19(1)(b) | Nominal content, with the stated exemptions | `nominal_content`, `content_exempt`, `content_exempt_reason` + `_check_nominal_content` |
| Art. 19(1)(c) | Minimum durability, or period after opening above **30 months** | `durability_mode`, `minimum_durability_date`, `pao_months`, `stated_durability_months` + `_check_durability` (`MIN_DURABILITY_THRESHOLD_MONTHS = 30`) |
| Art. 19(1)(d) | Particular precautions, at least those in Annexes III–VI | `precautions`, `annex_wording` (computed from the linked annex entries) |
| Art. 19(1)(e) | Batch number or identification reference | `batch_reference_rule`, `batch_on_packaging_only` |
| Art. 19(1)(f) | Function, unless clear from presentation | `product_function`, `function_clear_from_presentation` + `_check_product_function` |
| Art. 19(1)(g) | List of ingredients, descending order of weight, INCI names, `(nano)` suffix, `parfum`/`aroma`, colorant ordering and `+/-` marker | `ingredient_list`, generated by `formulation.build_ingredient_list()`; `ingredient._label_token()` applies the nano suffix and perfume term |
| Art. 19(1)(g)(i)(ii) | Impurities and processing aids are not ingredients | `ingredient.is_impurity`, `is_processing_aid`; excluded from the generated list |
| Art. 19(2)(3)(5) | Leaflet, adjacent notice, languages | `information_on_leaflet`, `notice_in_proximity`, `language_ids` |
| Art. 20(1) | Claims must not attribute characteristics the product lacks | `ls.cosmetic.claim` state machine; approval blocked until all six criteria are met |
| Art. 20(3) | "Not tested on animals" claims | `is_no_animal_testing_claim`, `animal_testing_declaration` + `_check_animal_testing_declaration` |
| Annex I Part A §1–10 | Safety information | `part_a_1_composition` … `part_a_10_other_information`; Part B cannot start until all ten are documented |
| Annex I Part B §1–4 | Conclusion, warnings, reasoning, assessor credentials | `conclusion`, `conclusion_statement`, `labelled_warnings`, `reasoning`, B4 assessor fields; `_check_part_b_complete` blocks approval on any gap |
| Annex I Part B §3 | Specific assessment for children under 3 and for external intimate hygiene | `reasoning_children`, `reasoning_intimate_hygiene` + `_check_specific_assessments` |

### Commission Regulation (EU) No 655/2013 — common criteria for claims

Each of the six criteria has a boolean **and** a justification field; a claim
cannot be approved unless every criterion is marked as met *and* carries a
written justification.

| Criterion | Field pair |
|---|---|
| Legal compliance | `criterion_legal` / `criterion_legal_note` |
| Truthfulness | `criterion_truth` / `criterion_truth_note` |
| Evidential support | `criterion_evidence` / `criterion_evidence_note` |
| Honesty | `criterion_honesty` / `criterion_honesty_note` |
| Fairness | `criterion_fairness` / `criterion_fairness_note` |
| Informed decision-making | `criterion_informed` / `criterion_informed_note` |

### Algeria

Cosmetic and body hygiene products in Algeria fall under the **Ministère du
Commerce**, not the ANPP. The ANPP is the pharmaceutical authority, and this
module asserts **no ANPP requirement** for cosmetics.

| Provision | Where it lands |
|---|---|
| Décret exécutif n° 97-37 (14 Jan 1997), modified by n° 10-114 (18 Apr 2010) — prior authorisation regime | `ls.cosmetic.dz_authorization` |
| The sixteen dossier items | `doc_rc` … `doc_trademark`, checked by `_compute_dossier_completeness`; submission refused while incomplete |
| Filing with the territorially competent Direction de Wilaya du Commerce | `wilaya_direction`, `submission_mode` |
| Deposit receipt, which is not an authorisation | `receipt_reference`, `receipt_date` |
| Decision notified within **45 days** of the deposit receipt | `decision_due_date` (`DZ_DECISION_DELAY_DAYS = 45`), `decision_overdue`, `_cron_monitor_deadlines` |
| Opinion of the Scientific and Technical Commission of the CACQE | `scientific_commission_opinion` |
| Reasoned refusal | `refusal_reason` + `_check_refusal_reason` |
| Formal notice with **1 month** to comply, then withdrawal | `notice_date`, `notice_deadline` (`DZ_COMPLIANCE_DELAY_DAYS = 30`), `notice_subject`, `action_withdraw` |

**Not verified:** the composition and numbering of the Algerian annexes of
permitted and prohibited substances could not be established from the
ministry's published index. No Algerian annex numbering is encoded anywhere
in this module.

### ISO 22716:2007

The standard is referenced as the GMP standard recorded on the Product
Information File (`gmp_standard`, defaulting to ISO 22716:2007). Whether it
is a harmonised standard conferring the Article 8(2) presumption of
conformity at a given date must be confirmed against the current list of
harmonised standards; the module does not assert it.

---

## 3. Models

13 models, 316 fields. The full generated inventory is in
[`docs/MODEL_INVENTORY.md`](docs/MODEL_INVENTORY.md).

| Model | Purpose |
|---|---|
| `ls.cosmetic.restriction` | Annex II–VI entries, loaded by you, with source and consolidation date |
| `ls.cosmetic.ingredient` | INCI register: identity, nano, CMR, perfume, labelling exclusions |
| `ls.cosmetic.formulation` | Versioned composition; the single source for the label list |
| `ls.cosmetic.formulation.line` | One substance at one concentration, with its annex evaluation |
| `ls.cosmetic.safety_assessment` | The CPSR: Annex I Part A §1–10 and Part B §1–4 |
| `ls.cosmetic.claim` | Claim wording assessed against the six common criteria |
| `ls.cosmetic.claim.evidence` | Experimental studies, consumer perception tests, published information |
| `ls.cosmetic.label` | The seven Article 19(1) particulars |
| `ls.cosmetic.pif` | The Article 11 dossier and its ten-year retention clock |
| `ls.cosmetic.dz_authorization` | Algerian prior authorisation dossier and deadlines |
| `product.template` | Cosmetic flag and dossier links |
| `ls.cosmetic.formulation.revise` | Wizard issuing the next formulation version |
| `ls.cosmetic.label.generate` | Wizard previewing the Article 19(1)(g) list |

---

## 4. Security

Four groups, defined through the Odoo 19 `res.groups.privilege` model:

| Group | Can do |
|---|---|
| Cosmetics: Read Only | Read everything in the module |
| Cosmetics: Formulator | Maintain the ingredient register; create, edit and submit formulations, claims and labels |
| Cosmetics: Safety Assessor | Prepare and approve safety reports |
| Cosmetics: Regulatory Manager | Approve formulations, claims and labels; manage PIFs, Algerian dossiers and annex data |

Segregation of duties is enforced **at ORM level**, not only in the user
interface:

- the user who submits a formulation cannot approve it;
- the user who starts a claim's substantiation cannot approve it;
- a safety report can only be approved by the user account named as the
  assessor in section B4.

Approved formulations, safety reports and labels are frozen: `write` refuses
changes to the regulated fields, and `unlink` is blocked outside the draft
state. A change is made by issuing a new version, which supersedes its
predecessor only when the new version is itself approved.

---

## 5. Installation

```bash
# 1. place the module on the addons path
cp -r ls_cosmetics /path/to/odoo/addons/

# 2. update the app list, then install
odoo-bin -d <database> -u base --stop-after-init
odoo-bin -d <database> -i ls_cosmetics --stop-after-init
```

Dependencies: `base`, `mail`, `product`, `stock`, `mrp` — all Odoo 19
Community. The module declares **no dependency on any other `ls_*` suite
module**, so it installs standalone.

After installation, load your annex data before relying on any composition
check: **Cosmetics → Ingredients → Annex Restrictions**.

---

## 6. Delivery status — CONDITIONAL PASS

Stated plainly, because a delivery gate that always reads PASS is worthless.

**Verified in this environment:**

- Every Python file parses (`ast.parse`, `py_compile`) — 13 models, 316 fields.
- Every XML file is well formed, under two independent parsers (`lxml`, `xmllint`).
- Custom static checker reports **zero findings** across 12 check categories:
  view field cross-references, object button targets, `ref=` resolution, ACL
  model coverage, manifest reconciliation, placeholder tokens, raw SQL,
  a PEP 8 subset, licence headers and docstring coverage.
- The checker itself was validated against **13 deliberately injected faults**
  before its output was trusted; all 13 were detected.

**Not verified, and required before production use:**

- Tests are **written but never executed.** There is no Odoo runtime and no
  PostgreSQL in the build environment. ~100 test methods exist across 9 files;
  none has been run. **No pass rate is claimed.**
- **No coverage was measured.** No coverage percentage is claimed.
- `flake8`, `pylint` and `pylint-odoo` were **not run** (no network access to
  install them). The custom checker covers a subset of what they would.
- The module has **never been installed against a live Odoo 19 server.**
- IQ / OQ / PQ have not been performed.

See [`docs/OUTSTANDING_QUALIFICATION.md`](docs/OUTSTANDING_QUALIFICATION.md)
for the tasks the receiving team must complete, and
[`docs/DEVIATIONS.md`](docs/DEVIATIONS.md) for every deviation from the suite
specification with its rationale.

---

## 7. Documentation

| Document | Contents |
|---|---|
| `docs/MODEL_INVENTORY.md` | Every model and field, generated from the AST |
| `docs/USER_GUIDE.md` | The seven workflows, end to end |
| `docs/ADMIN_GUIDE.md` | Groups, crons, annex data loading, residual risks and their one-line fixes |
| `docs/DEVIATIONS.md` | Deviations from the suite specification, with rationale |
| `docs/OUTSTANDING_QUALIFICATION.md` | What must be done before production use |
| `docs/CHANGELOG.md` | Release history |

---

## Licence

AGPL-3.0 or later. Copyright 2026 Life Sciences Suite Architecture Team.
