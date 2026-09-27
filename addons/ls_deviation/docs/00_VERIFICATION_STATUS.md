# 00 — Verification Status

**Read this before the other documents.** It states plainly what has been
verified, what has not, and what remains uncertain. Everything else in this
documentation set should be read against it.

---

## 1. What was actually executed

The module was built in an environment **without Odoo installed and without
network access to a database**. The following checks were genuinely run and
genuinely passed:

| Check | Tool | Result |
|---|---|---|
| Python syntax, all 25 `.py` files | `python3 -m compileall` | Passed |
| XML well-formedness, all 24 `.xml` files | `xmllint --noout` | Passed |
| Manifest data files all exist | custom AST checker | Passed |
| No XML file exists that the manifest fails to load | custom AST checker | Passed |
| Every intra-module `ref=` resolves | custom AST checker | Passed |
| Every `<field name="">` in every view exists on the target model | custom AST checker | Passed |
| Every model in `ir.model.access.csv` is declared in Python | custom AST checker | Passed |
| ACL CSV well-formed, IDs unique, 12 models covered | `csv` module | Passed |
| Longest Python line 85 chars against 88 limit | custom AST checker | Passed |
| Unused imports | custom AST checker | None found |
| Icon is a structurally valid PNG | header/IHDR parse | Passed, 140×140 |

The field cross-validation is the most valuable of these: it descends into
one2many and many2many sub-views and resolves each sub-view against the
comodel, so a typo in any of the 24 XML files would be caught.

**The checker was validated against negative controls.** Injecting a bogus
field name and a bogus `ref` caused it to fail with the expected 5 errors;
reverting restored a clean pass. A checker that cannot fail proves nothing,
so this step was performed deliberately.

---

## 2. What was NOT executed, and therefore is NOT proven

This is the part that matters most for a regulated deliverable.

| Claim the master prompt asks for | Actual status |
|---|---|
| "The module shall install successfully" | **Not demonstrated.** Odoo was never run. No database was created. |
| "The module shall upgrade successfully" | **Not demonstrated.** No upgrade path was executed. |
| "Minimum 95% test coverage" | **Not measured.** 92 test methods were written across 8 test modules, but none were executed and no coverage tool was run. The number 92 is a count of code written, not of tests passed. |
| "Shall pass flake8, pylint, pylint-odoo" | **Not run.** None of the three is installed and the network is disabled, so they could not be installed. The custom AST checker is a partial substitute, not an equivalent. |
| "XML validation" | Well-formedness verified. **Validation against Odoo's RelaxNG view schema was not performed** — that requires Odoo. |

Do not represent this module as installation-tested. The first action of any
implementing team must be to install it into a scratch Odoo 19 Community
database and run the test suite.

---

## 3. Odoo 19 API facts that WERE verified against official documentation

Several Odoo 19 changes would have silently produced a broken module if
written from prior-version habit. Each of the following was checked against
`odoo.com/documentation/19.0` before use:

| Fact | Consequence if assumed from Odoo ≤18 |
|---|---|
| SQL constraints are declared as `models.Constraint` class attributes prefixed with `_`; `_sql_constraints` no longer applies them | Constraints would silently not exist in the database |
| List views use the root element `<list>`, not `<tree>` | View load failure |
| The chatter is the `<chatter/>` element, not `<div class="oe_chatter">` | Chatter would not render |
| Kanban card templates use `<t t-name="card">`, not `kanban-box` | Kanban would render empty |
| `res.groups` references an intermediate `res.groups.privilege` record via `privilege_id`; it can no longer point at `ir.module.category` through `category_id` | Module install failure |
| `read_group` is deprecated in favour of `_read_group`, whose signature returns tuples led by the grouping recordset | Deprecation break in the category counter |

The `res.groups.privilege` change was found **after** the security file had
already been written the old way; the file was rewritten. This is recorded
because it illustrates that the remaining unverified items below are real
risks, not hypothetical ones.

---

## 4. Residual uncertainties — verify these first

These could not be confirmed from official documentation within this session.
They are individually small but each can block installation.

| Item | Where used | Risk |
|---|---|---|
| `ir.rule.groups` field name | `security/ls_deviation_security.xml` | Odoo 19 renamed `groups_id` to `group_ids` on several models. `ir.rule`'s field has historically been `groups` and was not in the published rename list, so `groups` was retained. If group rules fail to load, this is the first thing to check. |
| `groups="..."` XML attribute on `<menuitem>`, `<button>`, `<field>` | menus and views | This is the documented shorthand and is expected to survive the underlying field rename, but it was not explicitly confirmed for 19. |
| `<app>` / `<block>` / `<setting>` in the settings view | `views/res_config_settings_views.xml` | The three components are listed in the Odoo 19 view-architecture reference, so the tags are right. Whether the block renders for a module is a display concern, not an install blocker. |
| `uom.uom` model name and `product.product.uom_id` | `product_uom_id` fields | Odoo 19 changed several UoM fields (`factor` → `relative_factor`, `category_id` → `relative_uom_id`). The model name `uom.uom` and the product's `uom_id` were assumed unchanged and not confirmed. |
| `new_test_user(env, login, groups='...')` signature | `tests/common.py` | Used deliberately so the tests never name the user-to-group field directly, which was the uncertain item. If the helper signature changed, only the test fixture is affected, not the module. |
| `ir.cron` without `numbercall`/`doall` | `data/ir_cron_data.xml` | Those fields were removed in Odoo 17. Omitting them is safe in both cases. Low risk. |

---

## 5. Regulatory citations — verification status

**Verified against primary sources during this session:**

- **21 CFR 211.100(b)** — "Any deviation from the written procedures shall be
  recorded and justified." Confirmed via eCFR and Cornell LII. This is the
  basis for the mandatory `justification` field.
- **21 CFR 211.192** — requires that any unexplained discrepancy or failure to
  meet specifications be thoroughly investigated whether or not the batch has
  been distributed; that the investigation **extend to other batches of the
  same drug product and other drug products** that may be associated; and that
  a written record be made **including the conclusions and follow-up**.
  Confirmed via eCFR and Cornell LII. This is the basis for the
  `other_batches_lot_ids`, `extension_rationale`, `conclusion` and `followup`
  fields, and for making conclusions and follow-up mandatory at closure.
- **Algeria — Décret exécutif n° 22-247 du 30 juin 2022** relating to good
  manufacturing practice rules for pharmaceutical products for human use.
  Confirmed as the legal instrument. The ANPP (Agence nationale des produits
  pharmaceutiques) was confirmed as the competent authority operating BPF
  certification and inspection.

**NOT verified, and therefore not claimed anywhere in this module:**

- The specific articles of Décret exécutif n° 22-247 that address deviation
  handling. The decree was confirmed to exist and to be the Algerian GMP
  instrument, but its text was not read. **No article number is cited
  anywhere in this module**, and no statement is made about what Algerian GMP
  specifically requires of a deviation record. Any ANPP-specific mapping must
  be completed by Regulatory Affairs against the actual text.
- Clause numbers for ISO 9001, ISO 13485 and ISO 14971. ISO standards are
  copyrighted and were not consulted. The Life Sciences Suite specification
  cites ISO 13485 clause 8.3 and ISO 9001 clause 10.2 for this area; those
  citations were **not independently verified** and are consequently not
  repeated as fact in the module source.
- EU GMP Annex and chapter numbers. Not consulted, not cited.

---

## 6. Compliance language

No part of this module claims compliance with or certification against any
regulatory framework. The module **supports** the implementation of processes.
Compliance depends on procedures, validation, training and quality systems
that are outside software. The printed report carries an explicit statement
that it is not an electronic signature record within the meaning of 21 CFR
Part 11.

The `ls.deviation.stage.log` model is documented in its own docstring as
**not** an electronic signature: it records transitions but performs no
identity re-verification at the point of signing and applies no cryptographic
protection. Part 11 signature and audit-trail functionality belongs to the
separate `ls_electronic_signature` and `ls_audit_trail` modules described in
sections 7.14 and 7.15 of the suite specification, which do not yet exist.

---

## 7. Departures from the Life Sciences Suite specification

| Specification says | This module does | Why |
|---|---|---|
| `ls_deviation` depends on `ls_qms` and `ls_capa` | Depends on `base`, `mail`, `hr`, `stock`, `mrp`, `maintenance` only | Neither `ls_qms` nor `ls_capa` exists. A module cannot declare a dependency on a non-existent module and still install. CAPA linkage is provided through a documented `capa_reference` field plus an integration hook. |
| Model `stock.production.lot` | Uses `stock.lot` | `stock.production.lot` was renamed to `stock.lot` in Odoo 16. The specification is out of date on this point. |
| States: Reported → Assessed → Investigation → Disposition → CAPA Required → Closed | Same six, plus `cancelled` and four backward transitions | A deviation raised in error must be voided traceably rather than deleted, and reviewers need to return records for rework. Both extensions are documented in the model docstring. |
| Menus under a `Quality` root | Declares its own `Quality Management` root | The root would belong to `ls_qms`. The menu file carries a comment stating exactly how to reparent it when `ls_qms` arrives. |

---

## 8. Recommended acceptance sequence

1. Install into a **scratch** Odoo 19 Community database. Do not use a
   production or validated environment.
2. Resolve any load errors, checking the residual uncertainties in section 4
   first.
3. Run `odoo --test-enable --test-tags ls_deviation -i ls_deviation`.
4. Install `coverage`, `flake8`, `pylint-odoo` and run them. Only then can the
   coverage and static analysis claims in the master prompt be assessed.
5. Perform an upgrade test from the installed version to itself (`-u`).
6. Only after 1–5 pass should any validation activity (IQ/OQ/PQ) begin.
