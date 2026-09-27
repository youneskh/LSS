# Odoo 19 CE — Independent Code Review & Release Audit

**System:** `D:\Docker\odoo19Claude_ls-docker` (Life Sciences Suite + OCA (Odoo Community Association) addons)
**Revision 3 — final, 2026-09-25.** Supersedes revisions 1 and 2 (2026-09-24), which remain in the project folder as history.
**Mode:** Phase 1, review only. No source file under `addons/` was modified at any point.
**Runtime:** Odoo **19.0-20260723** (the project's own container), PostgreSQL 16. Reference source for code inspection: `odoo/odoo` branch `19.0`, commit `2e2acfd`.

---

## 0. Evidence basis — read this first

Every finding carries one of these statuses:

| Status | Meaning |
|---|---|
| **Confirmed at runtime** | Reproduced on the project's container by a test or probe. The log is named. |
| **Verified by inspection** | A precise code path traced through the Odoo 19.0 source; not reproduced at runtime. |
| **Withdrawn** | An earlier claim that runtime evidence showed to be wrong. Kept in the register so the correction is visible. |

**Runtime evidence (all on scratch databases; the production database was only read):**

| Campaign | What ran | Logs |
|---|---|---|
| 2026-09-24 module suites | Each module's own tests, 23 modules | `logs/tests/` |
| 2026-09-25 main campaign | Main-database module list; F-05 install; co-installation; install with demo, upgrade, uninstall per module; audit probes; performance and concurrency; coverage | `logs/campaign/` |
| 2026-09-25 rerun | Uninstall, `ls_validation` upgrade retry, probes (fixed collection), performance and concurrency. These steps failed the first time because of defects in the auditor's own scripts, not the product. | `logs/campaign/*_v2.log`, `04_*_3_uninstall.log` |

The probe module (`audit_campaign/addons/ls_audit_probe`) is test code only. It was loaded from the container's `/tmp`, never from `addons/`.

---

## 1. Executive summary

**Decision: RELEASE BLOCKED.**

| Severity | Active findings |
|---|---|
| CRITICAL | 1 |
| HIGH | 9 |
| MEDIUM | 21 |
| LOW | 6 |
| INFO | 5 |
| **Total active** | **42** |
| Withdrawn | 2 (F-33, F-34) |
| Superseded | 1 (F-08) |

**What works (demonstrated at runtime):**
- All 23 `ls_*` modules install individually and together (116 modules loaded in one database).
- Each module upgrades on a database containing its demo data (23 of 23) and uninstalls cleanly (23 of 23).
- The standard stock engine is **not** harmed by the custom code. Receipts with lots and backorders, deliveries with reservation, partial delivery and return, internal transfers, inventory adjustment, serial uniqueness, cancellation, scrap, and sale order to delivery: **16 of 16 probes pass**, both as installed and with the audit trail recording every stock change. The audit chain verifies afterwards.
- `ls_cosmetics` passes its full suite (110 of 110).

**Release blockers (all confirmed at runtime except where noted):**
- **F-01 (critical):** after `ls_supplier_qualification` is installed, any internal user without a supplier-qualification role gets an access error opening a **contact**, which blocks the standard Contacts form for most staff.
- **F-02:** electronic signatures crash (`res.users.groups_id` no longer exists); the module's demo data cannot load.
- **F-03:** inventory users without a recall role cannot open the **Lot/Serial** form.
- **F-04:** 30 uniqueness and value constraints in 4 modules do not exist; duplicates are accepted.
- **F-05:** the Docker build breaks core Odoo: `delivery` cannot be installed (`External ID not found: base.module_list`). `delivery` **is installed in the production database**, so upgrading it or running `-u all` there will fail.
- **F-06:** a lot from a **rejected** batch, and a lot under an **open recall**, are delivered to customers without any block.
- **F-07:** recalling a component lot does not reach the customers of the finished lots made from it.
- **F-10:** with stock models audited, **15 of 30** concurrent validations fail with a duplicate chain position; the per-company lock does not work under Odoo's transaction isolation.
- **F-35:** recall effectiveness checks cannot be generated, so a recall cannot be closed through its workflow.
- **F-42:** expired training certifications and expired validations stay shown as valid; their daily refresh jobs do not save the new status.

**Testing:** Odoo ran 1,988 of the 2,558 written test methods; **422 failed or errored**. About 150 of those failures come from test code never updated for Odoo 19 (F-40). **Line coverage is 65.9%** against the project's own 95% target (F-45).

**Security:** FAIL (F-01, F-03, F-11 clear-text signature passwords, F-14 folder rules ignore implied groups). No public HTTP (Hypertext Transfer Protocol) routes exist in the custom code; SQL is parameterised.

**Corrections to earlier revisions:** F-33 and F-34 (revision 2) are **withdrawn**: they were caused by test users who lacked the Internal User group, which is possible because the role groups do not include it (now F-27, raised to medium). F-01, first flagged by inspection, did not reproduce in the first probe run because of a cached value; with a clean cache it **is** reproduced.

---

## 2. Architecture assessment (discovered)

**Platform:** Docker Compose, with the images `odoo:19` (floating tag) and `postgres:16`. Port 8069 is published on 8071. The addons path is `/mnt/extra-addons,/mnt/found-addons`. The Dockerfile installs `numpy pandas scipy scikit-learn sentry_sdk odoorpc` and runs `patch-delivery.sh`. The container runs Odoo 19.0-20260723 on Python 3.12 (paths `/usr/lib/python3.12/...` in the test tracebacks).

**Addons inventory** (`addons/`, 456 entries):
- 23 custom `ls_*` modules: 21 functional modules, plus `ls_electronic_signature_test` and `ls_import_export`.
- 2 non-OCA helper modules: `base_delivery_patch` and `numpy_data_analysis`.
- About 430 OCA modules. All 444 manifests carry a `19.0.x` version. The Python in all 3,926 files parses; all 1,516 XML files parse.
- `found/` holds `ls_foundation`, a second copy of `ls_import_export` with different content, and `wooden_marketplace_llm` (not a module: it has `manifest.py`, not `__manifest__.py`).
- Loose scripts inside `addons/`: `convert_sql_constraints.py`, `diagnose_views2.py`, `extract_names.py`, `retrofit_scan.py`, `verify_constraints.py` and two `.sql` files.

**Custom code size (live code only):**

| Item | Count |
|---|---|
| Python files | 349 |
| Lines | 70,747 |
| `_name` declarations | 267 |
| ACL (Access Control List) rows | 768 |
| `ir.rule` records | about 230 |
| Lines of tests | 33,084 |

**Module independence:** no `ls_*` module references another `ls_*` model (0 cross-references found). Each module is standalone. The dependency table in `addons/README.md` (for example "ls_capa depends on ls_qms") does not match the manifests.

**Standard models extended:**

| Standard model | Extended by | What changes |
|---|---|---|
| `base` (**every model**) | `ls_audit_trail` | Overrides `create`, `write` and `unlink` |
| `purchase.order` | `ls_supplier_qualification` | Overrides `button_confirm` |
| `res.partner` | `ls_supplier_qualification` | Adds fields |
| `stock.lot` | `ls_recall` | Adds fields |
| `product.template` | `ls_cosmetics` | Adds fields |
| `product.template` | `ls_pharma` | Adds fields |
| `mrp.production` | `ls_medical_plastics` | Adds fields |
| `hr.employee` | `ls_training` | Adds fields |
| `res.company` | 5 modules | Adds fields |
| `res.config.settings` | 3 modules | Adds fields |

No module overrides `action_confirm`, `action_assign`, `button_validate`, `_action_done`, `_action_cancel`, reservation, procurement or valuation logic.

**Production database `odooClaude_ls_DB` (read only):** 239 modules installed, including 22 of the 23 `ls_*` modules (not `ls_electronic_signature_test`), `delivery`, `auditlog`, `database_cleanup`, `base_technical_user`, `quality_control_oca` and `mgmtsystem*`. Not installed: `queue_job*`, `base_import_async`, `base_delivery_patch`, `stock_delivery`, `stock_no_negative`.

**Stock data flows** (all read-only):
- `ls_recall` reads `stock.move.line` to trace distribution.
- `ls_supplier_qualification` reads `stock.move` for delivery counters.
- `ls_pharma`, `ls_lab`, `ls_complaint`, `ls_deviation` and `ls_medical_plastics` hold Many2one links to `stock.lot`, `mrp.production` or `stock.warehouse`.

**Security boundaries:**
- No `http.route` in the custom code.
- Raw SQL appears only in `ls_audit_trail` (advisory lock, chain tail, purge DELETE) and `ls_electronic_signature` (trigger DDL (Data Definition Language), advisory lock, chain tail). All data values are passed as parameters.
- `sudo()` is used 104 times, mostly for guarded workflow writes in `ls_change_control` and for hash-chain writes.

**Scheduled actions:** 20 modules declare crons in data files. `ls_medical_device` creates its crons in a `post_init_hook` instead.

**Custom JavaScript:** none (no assets declared).

---

## 3. Odoo 19 compatibility

| Status | Item |
|---|---|
| **Defect (runtime)** | `res.users.groups_id` is used in 3 Python sites and in demo XML. It does not exist in 19.0 (renamed to `group_ids` / `all_group_ids`, `res_users.py:257-258`). See F-02. |
| **Defect (runtime)** | `_sql_constraints` appears in 29 files. 19.0 logs "no longer supported" and creates nothing (`odoo/orm/model_classes.py:162-164`). See F-04. |
| **Defect (runtime)** | `patch-delivery.sh` renames `stock.view_move_line_tree_detailed` and `base.module_tree`. Both IDs exist unchanged in 19.0; the replacement IDs do not exist, and `delivery` fails to install on the project image. See F-05. |
| **Risk** | 9 form views use `<div class="oe_chatter">`. The 19.0 form compiler only handles `<chatter/>` (`mail/static/src/chatter/web/form_compiler.js:47`). See F-22. |
| **Pass** | 156 search views, 182 list, 22 graph, 18 pivot, 4 calendar and 2 activity views validate against the 19.0 RNG schemas. |
| **Pass** | All 16 inherited-view XPaths resolve against the 19.0 parent architectures. |
| **Pass** | No `name_get`, `read_group` (public), `search_read`, `fields_view_get`, `qty_done`, `quantity_done`, `detailed_type`, `uom.category`, `self._context`, `self._cr`, `numbercall` or `doall` in live code. |
| **Pass** | `res.groups.privilege_id` is used correctly throughout. |
| **Pass** | The `_check_credentials(credential, env)` convention matches 19.0 (`res_users.py:312`). |

---


## 4. Finding register

Status: **RT** = confirmed at runtime · **IN** = verified by inspection · **WD** = withdrawn · **SU** = superseded.

| ID | Severity | Status | Module | Area | Finding | Release impact |
|---|---|---|---|---|---|---|
| F-01 | CRITICAL | RT | ls_supplier_qualification | Security / UI | Contact form raises AccessError for internal users without a qualification role | Blocker |
| F-02 | HIGH | RT | ls_electronic_signature | Odoo 19 compat | `user.groups_id` crashes the signature wizard; demo data fails | Blocker |
| F-03 | HIGH | RT | ls_recall | Stock UI / Security | Lot form raises AccessError for inventory users without a recall role | Blocker |
| F-04 | HIGH | RT | ls_audit, ls_capa, ls_complaint, ls_training | Data integrity | 30 declared DB constraints never created | Blocker |
| F-05 | HIGH | RT | Docker build, base_delivery_patch | Upgradeability | Core files patched with invalid IDs; `delivery` cannot install; it is installed in production | Blocker |
| F-06 | HIGH | RT | ls_pharma, ls_lab, ls_recall | Stock / quality | Rejected-batch and recalled lots are delivered without a block | Blocker for GMP use |
| F-07 | HIGH | RT | ls_recall | Traceability | Component recall does not reach finished-goods customers | Blocker for manufacturers |
| F-08 | — | SU | All | Testing | Replaced by the runtime campaign, F-40 and F-45 | — |
| F-09 | MEDIUM | RT | ls_audit_trail | Audit completeness | Rule chosen by active company; company-B change unaudited when A is active | Fix before release |
| F-10 | HIGH | RT | ls_audit_trail | Concurrency | 50% of concurrent audited validations fail on chain position | Blocker if stock is audited |
| F-11 | MEDIUM | RT | ls_electronic_signature | Security | Signature password stored in clear text | Fix before release |
| F-12 | MEDIUM | IN | ls_electronic_signature | Install integrity | `cr.rollback()` inside `init()` | Fix before release |
| F-13 | MEDIUM | RT | ls_supplier_qualification | Multi-company | PO of company B refused when company A is active; status cached across companies | Fix before release |
| F-14 | MEDIUM | RT | ls_document_management | Security | Folder rules ignore implied groups | Fix before release |
| F-15 | MEDIUM | IN | ls_medical_device | Computed fields | Date-dependent stored fields never refreshed | Fix before release |
| F-16 | MEDIUM | RT | ls_pharma, ls_lab, ls_medical_plastics | Data integrity | Batch accepts another product's lot | Fix before release |
| F-17 | MEDIUM | RT | ls_recall | Traceability | 2 dozen traced as "2"; coordinators need stock rights | Fix before release |
| F-18 | MEDIUM | IN | ls_calibration | Maintainability | Dead parallel implementation | Fix before release |
| F-19 | MEDIUM | IN | Project | Quality evidence | "Zero pylint findings" relies on 50+ disabled checks | Condition |
| F-20 | MEDIUM | IN | OCA addons | Maintainability | Regex edits of OCA code; unported modules relabelled 19.0 | Condition |
| F-21 | MEDIUM | RT | Deployment | Security / operations | `list_db=True`, no `dbfilter`; server runs cron jobs on every database | Fix before production |
| F-22 | LOW | IN | ls_import_export, ls_medical_plastics | UI | Legacy `oe_chatter` markup in 9 forms | Post-release |
| F-23 | INFO | RT | 18 modules | Maintainability | `raise` in `unlink()`: uninstall still succeeds (23/23) | — |
| F-24 | MEDIUM | RT | ls_qms and 3 others | Multi-company | Cross-company links accepted (`check_company` not enforced) | Fix before release |
| F-25 | LOW | IN | Addons path | Maintainability | Duplicate `ls_import_export`; non-module folder | Post-release |
| F-26 | LOW | IN | ls_electronic_signature_test | Security | Test module installable in production (not installed today) | Post-release |
| F-27 | MEDIUM | RT | 16 modules | Security design | Role groups do not include Internal User; role-only users cannot work | Fix before release |
| F-28 | LOW | IN | ls_supplier_qualification | Business logic | Counter method: KeyError without stock; last day excluded | Post-release |
| F-29 | INFO | IN | 9 modules | Code quality | Constraints raise `UserError`; 44 `assertRaises(Exception)` | — |
| F-30 | INFO | IN | Suite | Documentation | README dependency table contradicts manifests | — |
| F-31 | INFO | RT | 11 modules | Security data | `global` written on 86 rules; installs without error | — |
| F-32 | INFO | IN | 3 modules | Dead code | `numbercall` / `doall` hooks | — |
| F-33 | — | WD | — | — | Withdrawn: caused by test users without Internal User (see F-27) | — |
| F-34 | — | WD | — | — | Withdrawn: same cause as F-33 | — |
| F-35 | HIGH | RT | ls_recall | Business logic | Effectiveness checks cannot be generated (NOT NULL `partner_id`) | Blocker |
| F-36 | MEDIUM | RT | ls_supplier_qualification | Data | Programmatic/demo creation fails on `criticality` | Fix before release |
| F-37 | MEDIUM | RT | ls_validation | Business logic | Items cannot be e-signed; protocol state not updated | Fix before release |
| F-38 | LOW | RT | ls_audit_trail | Configuration | Duplicate audit rules accepted | Post-release |
| F-39 | MEDIUM | RT | ls_qms, ls_risk_management, ls_document_management | Business logic | Revision defects (quality plan, FMEA); approval re-submission | Fix before release |
| F-40 | MEDIUM | RT | 12 modules | Testing | ≈150 test failures from test code not ported to Odoo 19 | Fix before release |
| F-41 | MEDIUM | RT | ls_environmental_monitoring | Security design | ACL contradicts the specification (86 test errors) | Decision required |
| F-42 | HIGH | RT | ls_training, ls_validation | Business logic | Expiry refresh jobs do not persist the status | Blocker |
| F-43 | MEDIUM | RT | ls_medical_device | Segregation of duties | Author can approve own PMS report; plain user can submit CE record | Fix before release |
| F-44 | LOW | RT | ls_document_management, ls_training | Upgradeability | Demo data rejected on upgrade by the modules' own guards | Post-release |
| F-45 | MEDIUM | RT | Suite | Testing | Line coverage 65.9% against a 95% target | Condition |

## 5. Detailed findings

### F-01 — CRITICAL — Contact form raises AccessError for users without a qualification role (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F01_contact_form_readable_by_sales_user` and `test_F01c_contact_form_readable_by_plain_internal_user` fail with "Failed to read field res.partner.ls_qualification_ids — You are not allowed to access 'Life Sciences Supplier Qualification Dossier'". The purchase-order field (`test_F01b`) did **not** fail, so the purchase-form part of the original claim is not reproduced. The first probe run passed only because the value had been cached by the superuser in the same transaction; the rerun clears the cache first.
- **Module / files:**
  - `ls_supplier_qualification/views/res_partner_views.xml:32-33`
  - `models/res_partner.py:14-18, 49-71` (`_compute_ls_qualification`)
  - `models/purchase_order.py:21-40` (`_compute_ls_qualification_warning`)
  - `views/purchase_order_views.xml:12`
- **Evidence:** `ls_is_approved_supplier` and `ls_qualification_id` are added to `base.view_partner_form` with no `groups` attribute. Their compute reads the One2many `ls_qualification_ids` as the current user, because `compute_sudo` defaults to False for non-stored computed fields (`odoo/orm/fields.py:448`). In 19.0, `One2many.read()` calls `comodel.search_fetch()` and wraps an AccessError as "Failed to read field" (`fields_relational.py:940-956`). Read access on `ls.supplier.qualification` is granted only to the three qualification groups (`security/ir.model.access.csv:17-19`). `ls_qualification_warning` is also placed on `purchase.order_form` without groups (line 12).
- **Impact:** every internal user without a supplier-qualification group (sales, accounting, inventory) cannot open any contact. The purchase-order form was **not** affected at runtime.
- **Reproduction:**
  1. Install the module.
  2. Create a user with only Sales / User.
  3. Open any contact.
  4. Expected result: AccessError "Failed to read field res.partner.ls_qualification_ids".
- **Recommendation:** compute `_compute_ls_qualification` and `_compute_ls_qualification_warning` through `sudo()` restricted to the fields needed, or set `compute_sudo=True` on the non-stored computed fields. Keep the company filter. Add `groups=` to the invisible fields. **Regression risk:** low. **Test:** open partner and PO forms `with_user()` as a user with no qualification group.

### F-02 — HIGH — E-signature uses the removed `res.users.groups_id` (confirmed at runtime)
- **Runtime:** module suite: `AttributeError: 'res.users' object has no attribute 'groups_id'` at `ls_signature_meaning.py:96`. Demo install (`04_ls_electronic_signature_1_install_demo.log`): "demo data failed to install … Invalid field 'groups_id' in 'res.users'".
- **Files:**
  - `ls_electronic_signature/models/ls_signature_meaning.py:96` (`is_available_to`)
  - `models/ls_signature_mixin.py:253`
  - `wizards/ls_signature_wizard.py:304`
  - `demo/ls_signature_demo.xml:16,25,34,43`
  - `tests/test_attempt.py:90`, `tests/test_meaning.py:76,80`
- **Evidence:** 19.0 `res.users` defines `group_ids` and `all_group_ids` (`res_users.py:257-258`), and no `groups_id` exists anywhere in base. `_compute_available_meaning_ids` (wizard line 113) always calls `is_available_to()`, which reads `user.groups_id`.
- **Impact:** AttributeError whenever the signature wizard computes its meanings, so no electronic signature can be executed. Installing with demo data fails on an invalid field. The module's own tests that write `groups_id` would error.
- **Reproduction:** open the signature wizard on any record that uses the mixin, for example `ls.signature.test.record`.
- **Recommendation:** use `user.all_group_ids`. Implied groups must count for authorization, so `group_ids` is not enough. Fix the demo XML and the tests. **Regression risk:** low. **Test:** a user whose signer group is inherited through `implied_ids` can sign.

### F-03 — HIGH — Lot/Serial form raises AccessError for inventory users (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F03_lot_form_readable_by_inventory_user` (user = Internal User + Inventory / User): "Failed to read field stock.lot.ls_recall_execution_ids — not allowed to access 'Recall Execution'".
- **Files:**
  - `ls_recall/models/stock_lot.py:40-62`
  - `views/stock_lot_views.xml:21-24`
  - `tests/test_security.py:111-122`
- **Evidence:** `ls_recall_open` is displayed on `stock.view_production_lot_form` for everyone. Its compute evaluates `lot.ls_recall_execution_ids` **before** `.sudo()`. `Many2many.read()` runs `comodel._search()`, which calls `check_access('read')` (`fields_relational.py:1377-1391`; `models.py:5364-5366`). `ls.recall.execution` is readable only by the recall groups. The docstring and test `test_lot_indicator_readable_without_a_recall_role` assert the opposite.
- **Impact:** after installation, warehouse users without a recall role cannot open lots, and the stated safeguard (risk R6, "warn warehouse staff") does not work.
- **Reproduction:** as a user with Inventory / User only, open any lot.
- **Recommendation:** read the relation under `sudo()` from the start, for example `lot.sudo().ls_recall_execution_ids`, or set `compute_sudo=True`. **Regression risk:** low. **Test:** keep the existing test and run it.

### F-04 — HIGH — 30 database constraints do not exist (confirmed at runtime)
- **Runtime:** 12 constraint tests fail with "IntegrityError not raised" or "Exception not raised": `ls_audit` 3, `ls_capa` 4, `ls_training` 5 (`logs/tests/`).
- **Files:** 9 in `ls_audit/models`, 5 in `ls_capa/models`, 4 in `ls_complaint/models`, 7 in `ls_training/models` (full list below).
- **Evidence:** `odoo/orm/model_classes.py:162-164` only logs "Model attribute '_sql_constraints' is no longer supported". None of the 30 is backed by a Python `@api.constrains` that enforces the same rule. The CAPA category has a Python check, but it only rejects blank codes (`capa_category.py:82-89`).
- **Impact:** duplicate references become possible for audit findings, CAPA (Corrective and Preventive Action) records, complaints, adverse events, training certifications, sessions and attendance. Negative quantities, capacities and grace days are accepted. For GxP (Good Practice regulations) records these are data-integrity defects.
- **Reproduction:** create two `ls.capa.issue` records with the same `name` and `company_id`; both are saved.
- **Recommendation:** convert to `models.Constraint` (as the other modules already do). Before upgrading, run a duplicate-detection SQL on existing databases, because adding a UNIQUE constraint fails if duplicates exist. **Migration required:** yes (pre-migrate duplicate cleanup). **Test:** duplicate creation raises IntegrityError, one test per constraint.
- **Affected constraints:**
  - **ls_audit:** type, area and finding-category codes; programme, schedule, finding and report references; checklist code+version; auditor user+company; checklist `version > 0`.
  - **ls_capa:** issue, action, root-cause and effectiveness names; category code; `default_due_days > 0`.
  - **ls_complaint:** complaint, adverse event and investigation names; category code; `quantity_complained >= 0`.
  - **ls_training:** attendance session+employee; certification and session names; competency and course codes; assessment employee+competency+date; `grace_days >= 0`; `capacity >= 0`.

### F-05 — HIGH — Core Odoo files patched at build time and at import time (confirmed at runtime)
- **Files:** `patch-delivery.sh`, `Dockerfile:7`, `addons/base_delivery_patch/__init__.py`, `__manifest__.py` (`auto_install: True`, no license).
- **Evidence:**
  - `sed` replaces `view_move_line_tree_detailed` with `view_move_line_list_detailed` in `stock_delivery/views/delivery_view.xml`, and `module_tree` with `module_list` in `delivery/views/ir_module_module_views.xml`.
  - In 19.0 the original IDs exist (`stock/views/stock_move_line_views.xml:40`, `base/views/ir_module_views.xml:128`) and the replacement IDs do not exist anywhere.
  - `sale_manual_delivery` depends on `stock_delivery`, and `sale_order_carrier_auto_assign` depends on `delivery`.
  - `base_delivery_patch` copies `/tmp/delivery_patch/...` over a core file on Python import and wraps everything in `except Exception: pass`.
- **Impact:** confirmed on the project image: installing `delivery` fails with `ValueError: External ID not found in the system: base.module_list` (`logs/campaign/02_f05_delivery_install.log`). The production database has `delivery` **installed** (`01_installed_modules_main_db.txt`), so any upgrade of `delivery`, including `-u all`, will fail to load its views. Core is modified outside version control, and the auto-install module is a latent path to overwrite core code with a file from a world-writable directory; it is blocked today only by file permissions.
- **Recommendation:** remove both mechanisms. Rebuild the image from an unmodified, digest-pinned `odoo:19`. If a real incompatibility existed, fix it in the dependent module, not in core. **Regression risk:** low. **Test:** install `delivery` and `stock_delivery` on a scratch DB.

### F-06 — HIGH — Quality decisions not enforced in inventory operations (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`: `test_F06a` delivers 5 units of a lot whose `ls.pharma.batch` is **rejected**; `test_F06b` delivers a lot named in an **initiated** recall (the lot shows "Under Recall"). Both deliveries reach state `done`.
- **Files:**
  - `ls_pharma/models/ls_pharma_batch.py:67-77`: `lot_id` is informational; no stock hook.
  - `ls_lab/models/ls_lab_oos.py:169`: the "Remain In Quarantine" disposition has no stock effect.
  - `ls_recall/doc/01_business_analysis.md` §8: "module warns; it does not move goods".
- **Evidence:** no custom override of `stock.move`, `stock.move.line`, `stock.picking` or `stock.quant` exists (section 2). Only the recall exclusion is documented; the batch-release and OOS gaps are not declared out of scope.
- **Impact:** a batch with no release decision, a rejected batch, a lot under OOS investigation or a lot under recall can be reserved and delivered through standard Odoo with no warning in the transfer.
- **Recommendation:** block these lots through a standard mechanism: a lot-level blocked flag checked in `stock.move.line` validation / `_action_done`, or a quarantine location with restricted routes. Decide which module owns it. **Regression risk:** high (core stock flow), so it needs a full stock regression suite. **Test:** receipt, reservation, delivery and backorder with blocked and released lots.

### F-07 — HIGH — Recall tracing does not follow lot genealogy (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F07`: component lot consumed by a manufacturing order, finished lot delivered to a pharmacy; the recall on the component lot lists **no** consignee.
- **Files:** `ls_recall/models/ls_recall_execution.py:848-886` (`_scan_move_lines`)
- **Evidence:** the domain is `lot_id in self.lot_ids`, `state = done`, destination usage `customer`. The consumption of a recalled component lot in manufacturing orders (MO) is never followed to the finished lots produced, and this limitation is not listed in §8 "Out of scope".
- **Impact:** recalling a raw-material or intermediate lot finds no consignees of the finished products that contain it, and the chatter summary gives no warning.
- **Recommendation:** add downstream traversal (consumed move lines → produced lots, recursively), or state the limitation in the UI (User Interface) and require manual lot selection. **Test:** component lot → MO → finished lot → delivery; the recall on the component must list the consignee.

### F-08 — SUPERSEDED — Test-execution evidence
- Revision 1 reported that no current test evidence existed. That gap is closed by the runtime campaigns (section 13). The underlying problems are now tracked as F-40 (test code not ported) and F-45 (coverage).

### F-09 — MEDIUM — Audit trail picks rules by the user's active company (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F09`: rule for company B on `res.partner.ref`; the write made with company B active is audited (control), the same write made with company A active is **not**.
- **File:** `ls_audit_trail/models/base_audit.py:65`
- **Evidence:** `_ls_audit_config_for(self._name, self.env.company.id)` searches rules with `company_id in [False, env.company]`. The chain company, by contrast, is the record's company (`_ls_record_company_id`).
- **Impact:** a user working with companies A and B active (current company A) writes a B record. A rule defined only for B is not applied and the change is not audited, or A's rule is applied to B's data.
- **Recommendation:** resolve the configuration per record company (group `self` by `company_id`). **Test:** a multi-company write with rules on only one company.

### F-10 — HIGH — Audit chain lock does not prevent collisions (confirmed at runtime)
- **File:** `ls_audit_trail/models/ls_audit_trail_log.py:579-651` (`_ls_lock_chain`, `_ls_chain_tail`, `_ls_seal`). The same pattern exists in `ls_electronic_signature/models/ls_signature_log.py:363-375`.
- **Runtime** (`06_perf_concurrency_v2.log`): two threads validating 15 deliveries each, with audit rules on `stock.picking`, `stock.move`, `stock.move.line` and `stock.quant`:
  - without audit rules: 30 of 30 validated, 0 errors;
  - with audit rules: **15 of 30 validated, 15 failed** with `UniqueViolation … "ls_audit_trail_log_company_sequence_unique"`.
  - The chain still verifies afterwards: the database constraint rejected the duplicates, so integrity held, but the users' transactions failed.
- **Mechanism (analysis):** Odoo runs transactions in REPEATABLE READ. The advisory lock serialises the two sealers, but the second transaction's snapshot predates the first one's commit, so its SQL read of the chain tail returns the old position. Odoo retries only serialization failures and deadlocks, not unique violations, so the user sees an error.
- **Impact:** in any company where two users perform audited operations at the same time, about half of the operations can fail. The electronic-signature chain is exposed to the same collision (**not** tested at runtime).
- **Recommendation:** allocate chain positions with a PostgreSQL sequence per company, or seal in a separate short transaction / queue; or raise a serialization error so Odoo's retry applies. **Test:** re-run `perf_concurrency.py`; expect 30 of 30.

### F-11 — MEDIUM — Signature password persisted in clear text (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F11`: after creating the signature dialog, `SELECT password FROM ls_signature_wizard` returns the typed password.
- **File:** `ls_electronic_signature/wizards/ls_signature_wizard.py:38,76`
- **Evidence:** `ls.signature.wizard` is a `TransientModel`, and `password = fields.Char()` is a stored column. The web client saves the wizard before calling `action_sign`, and the value is never cleared.
- **Impact:** passwords sit in `ls_signature_wizard.password` until the transient vacuum runs, and also end up in WAL (Write-Ahead Log) files and backups.
- **Recommendation:** keep the field but clear it (`self.password = False`) in a `finally` block before any exception, or pass the password as a method argument from a non-stored field. Purge existing rows. **Migration:** `UPDATE ls_signature_wizard SET password = NULL`.

### F-12 — MEDIUM — Transaction rollback inside `init()`
- **File:** `ls_electronic_signature/models/ls_signature_log.py:202-245`
- **Evidence:** if trigger creation fails, `self.env.cr.rollback()` runs in the middle of module installation.
- **Impact:** it silently discards all work done earlier in the install transaction, including other modules' data, while the loader continues, leaving an inconsistent registry and database.
- **Recommendation:** use `with self.env.cr.savepoint():`.

### F-13 — MEDIUM — Supplier control mixes companies (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`: `test_F13` — a company B order to a supplier approved for company B is refused while company A is active ("has no qualification dossier"); the same order confirms with company B active. `test_F13b` — the approval value computed for company B is reused when company A becomes active, because the compute lacks `@api.depends_context('company')`.
- **Files:** `ls_supplier_qualification/models/res_partner.py:57`, `purchase_order.py:43-75`
- **Evidence:** the dossier is taken from `self.env.company`, while the policy comes from `order.company_id`.
- **Impact:** confirming company B's PO while the active company is A checks A's dossier, so an unqualified supplier can pass or a qualified one can be blocked.
- **Recommendation:** resolve the dossier with `order.company_id` (e.g. `order.partner_id.with_company(order.company_id)`), and add `@api.depends_context('company')` to `_compute_ls_qualification`. **Test:** a multi-company PO confirmation.

### F-14 — MEDIUM — Folder access rules ignore implied groups (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F14`: a user holding the folder's read group through an implied group cannot find the document.
- **File:** `ls_document_management/security/ls_document_record_rules.xml:72,83,101,112`
- **Evidence:** the rules use `user.group_ids.ids`, which holds explicitly assigned groups only (`res_users.py:257`).
- **Impact:** users who get a folder's group through an implied group are denied read or write.
- **Recommendation:** use `user.all_group_ids.ids`.

### F-15 — MEDIUM — Date-dependent stored fields go stale
- **File:** `ls_medical_device/models/device.py:295-311, 394-425, 777-830`
- **Evidence:** `periodic_report_overdue`, `next_periodic_report_due` and `active_ce_marking_id` (CE marking) are stored and computed from today's date, and no job recomputes them. The cron `_cron_check_post_market_obligations` reads the stored `periodic_report_overdue`.
- **Impact:** overdue post-market reports are never flagged or scheduled unless the device record is edited.
- **Recommendation:** recompute in the cron (as `ls_training`, `ls_validation` and `ls_medical_plastics` do) or make the fields non-stored. **Test:** freeze the date past the due date and run the cron.

### F-16 — MEDIUM — No lot / product / company consistency check (confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F16`: `ls.pharma.batch` is created with the lot of a different product.
- **Files:** `ls_pharma/models/ls_pharma_batch.py:67`, plus the lot fields in `ls_lab` and `ls_medical_plastics`
- **Evidence:** there is no constraint that `lot_id.product_id == product_id` or that the lot's company matches, and none of the 21 `ls_pharma` models that carry `company_id` sets `_check_company_auto`. `ls_complaint` and `ls_recall` do have the check.
- **Impact:** a batch release or lab result can reference another product's or another company's lot, which breaks traceability.
- **Recommendation:** add `@api.constrains` for this check, and add `check_company=True` with `_check_company_auto = True`.

### F-17 — MEDIUM — Recall tracing: mixed UoM and access rights (UoM part confirmed at runtime)
- **Runtime:** probe `05_probes_v2.log`, `test_F17`: 2 dozen delivered (24 units left the stock) are traced as `qty_shipped = 2.0`. The access-rights part is verified by inspection only.
- **File:** `ls_recall/models/ls_recall_execution.py:875-882`
- **Evidence:**
  - `move_line.quantity` is expressed in the move-line UoM; `quantity_product_uom` exists for the product UoM (`stock_move_line.py:37-42`).
  - The trace reads `stock.picking` and `stock.lot`, which require `stock.group_stock_user`, and the recall groups imply no stock group.
- **Impact:** shipped quantities are wrong when deliveries use different UoMs, and a recall coordinator without Inventory rights gets AccessError on "Trace distribution".
- **Recommendation:** sum `quantity_product_uom`, and either imply `stock.group_stock_user` or read the stock data under a scoped `sudo()`.

### F-18 — MEDIUM — Dead parallel implementation in `ls_calibration`
- **Evidence:**
  - 13 Python files are not imported: `models/calibration_*.py`, `models/constants.py`, `report/__init__.py`, `wizards/calibration_plan_generate.py`, `wizards/calibration_record_reject.py`.
  - 14 XML files are not in the manifest, including `security/ls_calibration_groups.xml` and `security/ls_calibration_record_rules.xml`.
  - 3 test files target the dead models.
- **Impact:** reviewers and tests work against code that never runs, and the documentation may describe the dead model set (oot, point, reading, standard, instrument category).
- **Recommendation:** delete the dead set or re-integrate it deliberately, then re-run the tests.

### F-19 — MEDIUM — Quality evidence depends on suppressed checks
- **Evidence:** `ODOO_COMPLIANCE_REPORT.md` states "ZERO findings from both flake8 and pylint". `.pylintrc:147` disables more than 50 messages, including E8103 (sql-injection), E8140, W8106, E1101, E0601, W0612 and all R/C messages. An independent run of pylint-odoo 10.0.11 (odoolint only) on the 23 `ls_*` modules gives 1,534 messages (section 9).
- **Impact:** the "zero findings" status cannot be reproduced with default rules and must not be used as validation evidence.
- **Recommendation:** publish the rule set with each report, and justify each disabled message.

### F-20 — MEDIUM — Scripted edits of third-party OCA code
- **Evidence** (`FIXES_SUMMARY.md`):
  - Regex scripts changed 358 manifests and 367 files: 4,161 `string=` removals, and about 200 `print()` calls replaced with `_logger.info`.
  - `base_import_async`, `queue_job_batch`, `queue_job_cron`, `queue_job_cron_jobrunner`, `queue_job_subscribe` and `test_queue_job_batch` were relabelled from 18.0 to 19.0 with no port.
- **Upstream check (OCA/queue, branch 19.0, commit `bc1d885`, 2026-09-14):** the 19.0 branch still carries `base_import_async`, `queue_job_batch`, `queue_job_cron`, `queue_job_cron_jobrunner`, `queue_job_subscribe` and `test_queue_job_batch` at version **18.0** (not ported). Four of them are `installable: False` locally too. `queue_job_batch` and `test_queue_job_batch` are unported 18.0 code labelled 19.0 and installable. The local `queue_job` is 19.0.2.0.3 against 19.0.2.1.3 upstream.
- **Installed in production:** none of the queue-job modules (`01_installed_modules_main_db.txt`), so the current exposure is nil.
- **Recommendation:** restore OCA modules from upstream and remove the relabelled ones until OCA ports them.

### F-21 — MEDIUM — Deployment configuration
- **Files:** `config/odoo.conf`, `docker-compose.yml`, `Dockerfile`
- **Evidence:**
  - `list_db = True` and `proxy_mode = False`.
  - The PostgreSQL password is in clear text in the compose file.
  - Port 8071 is published on all interfaces.
  - The image is `odoo:19` (floating tag).
  - `pg_isready` has no `-h 127.0.0.1` (the healthcheck race condition already documented in the project).
  - `admin_passwd` is PBKDF2-hashed, which is correct.
  - **Runtime:** without a `dbfilter`, the running server executes scheduled jobs on **every** database. During the campaign it updated the scratch database `t_c_demo_ls_validation` at the same moment as an upgrade, which failed with `SerializationFailure` (`04_ls_validation_2_upgrade.log`); the retry passed. In production the same behaviour runs jobs of test or copy databases against their stored data.
- **Recommendation for production:** `list_db = False`, a `dbfilter`, secrets through environment variables or files, a reverse proxy with `proxy_mode = True`, and an image pinned by digest.

### F-24 — MEDIUM — `check_company` not enforced (confirmed at runtime)
- **Evidence:** 13 fields declare `check_company=True` in classes without `_check_company_auto` (`ls_qms` ×7, `ls_document_management` ×4, `ls_medical_device` ×1, `ls_supplier_qualification` ×1). Only the user-interface domain applies.
- **Runtime:** probe `05_probes_v2.log` `test_F24`: an objective of company A is created with a policy of company B.
- **Recommendation:** `_check_company_auto = True` on those models.

### F-27 — MEDIUM — Role groups do not include Internal User (confirmed at runtime)
- **Evidence:** 18 root groups have no `implied_ids` (for example `group_ls_capa_viewer`, `group_ls_recall_viewer`, all 3 `ls_environmental_monitoring` roles, the lab and medical-device roles).
- **Runtime:** probe `05_probes_v2.log` `test_F27`: an Internal User holding the lab analyst role draws an OOS sequence normally; a user given only the role cannot (AccessError). The 48 module-suite errors first reported as F-33/F-34 come from this.
- **Impact:** in normal use Odoo 19 users are created as Internal Users, so production impact is limited to users configured with a role only; the defect mainly corrupts the test evidence.
- **Recommendation:** make each root role imply `base.group_user`.

### F-35 — HIGH — Recall effectiveness checks cannot be generated (confirmed at runtime)
- **File:** `ls_recall/models/ls_recall_execution.py:968` (`action_generate_effectiveness_checks`); model `ls.recall.effectiveness` (`partner_id` computed and required).
- **Root cause:** `partner_id` is a stored, required computed field without `precompute=True`, so the row is inserted before the compute runs.
- **Evidence:** module suite 15 errors, and probe `05_probes_v2.log` `test_F35` (the button path after a real trace): `NotNullViolation: null value in column "partner_id" of relation "ls_recall_effectiveness"`.
- **Impact:** the effectiveness step of a recall cannot be completed, so a recall cannot reach closure through the designed workflow.
- **Recommendation:** pass `partner_id` explicitly in the create values, or make the compute run before insert (`precompute=True`). **Test:** `TestEffectiveness`.

### F-36 — MEDIUM — Supplier qualification creation fails on `criticality` (confirmed at runtime)
- **Root cause:** `criticality` and `requalification_interval_months` (`ls_supplier_qualification.py:71,116`) are stored, required computed fields without `precompute=True`.
- **Runtime:** probe `05_probes_v2.log` `test_F36` (creation by code without the computed value) fails; the module's own **demo data** fails for the same reason (`04_ls_supplier_qualification_1_install_demo.log`); all 14 test classes of the module fail in setup. The web form is not affected, because the form sends the value computed on screen.
- **Impact:** imports, integrations and demo data cannot create dossiers; the module's whole test suite never runs (coverage 44%).
- **Recommendation:** `precompute=True` on both fields (and on the two wizard fields found by the same scan).

### F-37 — MEDIUM — Validation module defects (confirmed at runtime)
- **Evidence:** `ls.validation.item` does not inherit `ls.validation.signature.mixin` (`models/ls_validation_item.py:31`), while the five other validation models do. 10 errors: `'ls.validation.item' object has no attribute '_ls_create_signature'` / `'_ls_verify_credentials'`. The sign wizard therefore refuses items with "does not support electronic signatures". Also failing: approving an execution does not move the protocol to "executed". (The expiry-refresh failure is F-42.)
- **Recommendation:** add the mixin to `ls.validation.item`; fix the cron and the protocol state update; re-run `test_signature`, `test_cron`, `test_execution`.

### F-38 — LOW — Duplicate audit rules accepted (confirmed at runtime)
- **Runtime:** `test_reject_duplicate_rule` fails ("IntegrityError not raised").
- **Revision 2 claimed more; corrected here.** The purge failures come from the test changing `event_datetime` by SQL, which rightly breaks the digest; the tamper test writes `db_datas` while the file lives in the filestore; the binary-capture test uses a corrupt PNG. These are test-design defects (F-40), not product defects.
- **Recommendation:** add a `models.Constraint` on (`model_id`, `company_id`).

### F-39 — MEDIUM — Revision and workflow defects (confirmed by failing tests)
- `ls_qms`: creating a quality-plan revision writes `previous_revision_id`, a field `ls.qms.quality_plan` does not have (`ls_qms_document_mixin.py:323`, called from `create_new_revision` line 658), so quality-plan revisions fail.
- `ls_risk_management`: an FMEA (Failure Mode and Effects Analysis) revision is created with **no** failure modes: `line_ids` is a One2many, which `copy()` does not duplicate by default (`ls_risk_fmea.py:87, 370`).
- `ls_document_management`: re-submitting a document for review violates `ls_document_approval_pending_approver_uniq` (`ls_document_document.py:311, 355`); the previous cycle is not cancelled first.
- Items from revision 2 reclassified after root-cause analysis: training/validation expiry → **F-42**; medical-device approvals → **F-43**; e-signature lockout and deviation stage-log ordering fail because every record in a test transaction carries the same timestamp (test artifact; add an `id` tie-breaker to the ordering), → F-40.

### F-40 — MEDIUM — Test suites not ported to Odoo 19
- **Evidence (test-side errors, not product defects):**

| Cause | Errors | Modules |
|---|---|---|
| `res.groups.users` (renamed `user_ids` in 19) | 56 | ls_change_control, ls_complaint |
| `res.users.groups_id` written in tests | 10 | ls_electronic_signature, ls_electronic_signature_test |
| Audit programme not approved in the fixture | 54 | ls_audit |
| `stock.move.name` (no longer exists) | 5 | ls_recall |
| `assertRaises` given a non-class | 6 | ls_calibration |
| Date fixtures rejected by the module's own date checks | ≈15 | ls_capa, ls_deviation, ls_recall, ls_training, ls_medical_device |
| `ir.rule.global_` | 1 | ls_lab |
| Custom `search=` methods called with a bare boolean, rejected by the Odoo 19 domain parser | 3 | ls_capa, ls_deviation |
| Test design (data changed by SQL, wrong storage, corrupt image, identical timestamps, NewId comparison, folder-cycle exception type) | ≈10 | ls_audit_trail, ls_electronic_signature, ls_deviation, ls_document_management |
| Test users created without Internal User (see F-27) | 48 | ls_lab, ls_pharma, ls_medical_plastics, ls_medical_device, ls_environmental_monitoring |

- **Impact:** about 150 test results say nothing about the product. The code these tests should cover is **NOT VERIFIED** until they are fixed.
- **Recommendation:** port the test code (`user_ids`, `group_ids`, fixtures), then re-run the full campaign.

### F-41 — MEDIUM — Environmental monitoring: ACL contradicts the specification
- **Evidence:** 86 errors "You are not allowed to create 'Environmental Monitoring Limit' / 'Plan'" when the tests act as a technician. `security/ir.model.access.csv` grants create on these models to managers only.
- **Decision required:** either technicians must create plans and limits (fix the ACL) or only managers may (fix the tests and the documentation). Until decided, 86 of 104 tests in this module give no evidence.

### F-42 — HIGH — Expiry statuses never change (confirmed at runtime)
- **Files:** `ls_training/models/ls_training_certification.py:311-319` (`_cron_refresh_certification_state`), `ls_validation/models/ls_validation_item.py:318-339` (`_cron_refresh_validation_status`). The same call pattern is used in `ls_audit/models/ls_audit_auditor.py:180` and `ls_medical_plastics/models/mp_tool.py:572` (not tested at runtime).
- **Evidence:** the jobs call the compute method directly (`records._compute_state()`). For a stored computed field this does not schedule a database write, so the new value is lost. Runtime: `test_refresh_updates_expired_status` ('valid' != 'expired') and `test_status_becomes_expired_after_the_validity` ('validated' != 'expired').
- **Impact:** an operator whose GMP training expired, or equipment whose validation expired, continues to be shown as valid. In a GxP (Good Practice regulations) context this is a compliance-relevant data defect.
- **Recommendation:** recompute through the ORM: `self.env.add_to_compute(field, records)` then `records.flush_recordset()`, or `records._recompute_recordset([fname])`; add `@api.depends_context` where appropriate. **Test:** the two existing tests.

### F-43 — MEDIUM — Medical devices: segregation of duties and locks (confirmed by failing tests)
- **Evidence:** `ls_medical_device/models/pms_report.py:422-452`: `action_approve` checks only the approver's group, not that the approver differs from the author. `test_self_approval_rejected` fails ("UserError not raised"). `ce_marking.py:313`: `action_submit` has no authority check (`test_plain_user_cannot_activate` fails).
- Three "locked after submission" tests fail because the code locks at **approval** while the tests (specification) expect locking at **submission** (`technical_file_section.py:161-172`). This is a specification decision.
- **Recommendation:** add author ≠ approver checks; decide and align the lock point; re-run the tests.

### F-44 — LOW — Demo data rejected on upgrade by the modules' own guards
- **Runtime:** upgrading `ls_document_management` and `ls_training` on databases with demo data logs "demo data failed to install" because the demo records reload onto controlled records (`UserError: A document version is a controlled record…`, `Only a draft course can be submitted…`). The upgrade itself completes.
- **Recommendation:** mark such demo records `noupdate="1"`.

### F-45 — MEDIUM — Test coverage below the project's own target
- **Runtime** (`07_*_coverage.txt`, `coverage` run over each module's own suite, tests excluded): **65.9%** of 25,559 statements (8,713 not executed). Lowest: `ls_calibration` 37%, `ls_supplier_qualification` 44%, `ls_complaint` 45%, `ls_environmental_monitoring` 47%, `ls_change_control` 51%, `ls_medical_plastics` 53%, `ls_electronic_signature` 54%. Highest: `ls_capa` 97%, `ls_training` 96%.
- The low figures follow directly from suites that cannot start or error early (F-36, F-40, F-41, F-27).
- **Recommendation:** fix F-40/F-41/F-27 first, then re-measure; the 95% target in the project's framework is not met by any process yet.

### Other LOW findings

| ID | Evidence | Recommendation |
|---|---|---|
| F-22 | `<div class="oe_chatter">` in 3 `ls_import_export` views and 6 `ls_medical_plastics` views. The 19.0 compiler only transforms `<chatter/>`. Rendering is **UNABLE TO CONFIRM**. | Replace with `<chatter/>`. |
| F-25 | `ls_import_export` exists in both `addons/` and `found/` with 5 differing files; the first path wins. `found/wooden_marketplace_llm` is not a module. | Keep one copy and remove `found/` from the addons path. |
| F-26 | `ls_electronic_signature_test` is installable in production (it is **not** installed in `odooClaude_ls_DB`); `ls.signature.test.record` gives `base.group_user` full CRUD (Create, Read, Update, Delete). | Move it out of the production addons path. |
| F-28 | `ls_supplier_performance.py:446`: `self.env["stock.move"]` raises KeyError when `stock` is absent, before the guard runs. `period_end` is converted to midnight, which excludes that whole day. | Guard with `"stock.move" in self.env`; use end-of-day. |

### INFO findings
- **F-29:** `@api.constrains` methods raise `UserError` instead of `ValidationError` (for example `ls_pharma/models/product_template.py:97-152`). There are 44 `assertRaises(Exception)` in tests (ruff B017), which can hide wrong exception types.
- **F-30:** `addons/README.md` lists inter-module dependencies that the manifests do not declare.
- **F-23:** pylint E8140 ×90, `unlink()` raising directly. Runtime: all 23 modules uninstall cleanly with their demo data, so the uninstall concern raised in revision 1 is not reproduced. `@api.ondelete` remains the recommended form.
- **F-31:** 86 `ir.rule` records write the computed field `global` (`ir_rule.py:53-56, 281`). The values match the compute, and all modules install without error at runtime. Removing the field is harmless.
- **F-32:** hooks write `numbercall` "if present". It is absent in 19.0 (`ir_cron.py`, 0 occurrences), so the code is dead.

---

### F-33, F-34 — WITHDRAWN
- Revision 2 reported that `ir.sequence`, `res.company` and `mail.message` access failed for ordinary users. Odoo 19 grants Internal Users read access to sequences and companies (`base/security/ir.model.access.csv:29, 45`). The failing tests used users created with only an `ls_` role. Cause and remedy are in F-27.

---

## 6. Stock / inventory audit

| Flow | By inspection | Runtime (probe P1, plain and audited) |
|---|---|---|
| Receipt, lot-tracked, partial with backorder | No custom override | **PASS** (both) |
| Delivery with reservation, partial with backorder, return | No custom override | **PASS** (both) |
| Internal transfer | No custom override | **PASS** (both) |
| Inventory adjustment (`action_apply_inventory`) | No custom override | **PASS** (both) |
| Serial-number uniqueness | Standard constraint | **PASS** (both) |
| Cancellation releases reservation | No custom override | **PASS** (both) |
| Scrap | No custom override | **PASS** (both) |
| Sale order → delivery → delivered quantity | No custom override | **PASS** (both) |
| Audit chain after stock operations | — | **Verifies** |
| Negative stock | No custom code writes quants; OCA `stock_no_negative` is **not** installed in production | Standard Odoo behaviour, not re-tested |
| Concurrency with audited stock models | — | **FAIL** (F-10) |
| Quality ↔ stock coupling | Absent | **FAIL** (F-06) |
| Recall traceability | Direct shipments only | **FAIL** (F-07, F-17) |
| Lot form for inventory users | — | **FAIL** (F-03) |

Conclusion: the custom modules do not corrupt standard inventory. Their own stock-facing functions (quality blocking, recall tracing, lot indicator) are defective.

## 7. Security audit (summary)
- **No public attack surface in the custom code:** no controllers, routes or portal access.
- **SQL injection:** all data values are parameterised. The pylint E8103 hits in `ls_signature_log.init` interpolate module constants only, so they are false positives.
- **`sudo()`:** the 104 uses are guarded. For example, `ls_change_control` checks the requester or manager before every `sudo().write`. No IDOR (Insecure Direct Object Reference) path was found, because record reads before `sudo` still enforce rules.
- **Defects:** F-01, F-03, F-11, F-14 (all confirmed at runtime), F-21, F-26, F-27.
- **Multi-company rules:** present on every custom model with a `company_id` field, except child lines and transient wizards.

## 8. Performance and concurrency audit
Measured on the project container (`06_perf_concurrency_v2.log`), 30 single-line deliveries per run:

| Configuration | Sequential validation | Two concurrent users (2 × 15) |
|---|---|---|
| No audit rule | 60 ms per picking | 30 of 30 validated, 0 errors |
| Audit on `stock.picking`, `stock.move`, `stock.move.line`, `stock.quant` | 103 ms per picking (**×1.70**) | **15 of 30 validated, 15 errors** (F-10) |

- The ×1.70 cost is acceptable for regulated records but should be documented before anyone audits high-volume stock models.
- By inspection: the `base` hooks add one cached lookup per create/write/unlink on unaudited models; `hr.employee` training compliance runs one query per employee when displayed; chain verification is linear in its 7-day window.
- Not measured: production-size data volumes, report rendering, cron duration.

## 9. Static analysis (executed in this audit)

| Tool | Version | Command | Result |
|---|---|---|---|
| Python compile | CPython 3.11.15 | `python3 -m py_compile` on all `ls_*` `.py` files | 0 errors |
| Python parse | CPython 3.10 (device) | `ast.parse` on the whole `addons/` tree | 3,926 files, 0 syntax errors |
| flake8 | 7.3.0 | `flake8 --config .flake8 addons/ls_*`, and `--select=F` | 0 / 0 |
| ruff | 0.15.11 | `ruff check --select F,E9,B,PLE` | 0 real defects. B023 ×12 are false positives (immediate `filtered()`); B017 ×44 are weak tests; F401 are Odoo `__init__` imports |
| pylint + pylint-odoo | 4.0.9 / 10.0.11 | `--load-plugins=pylint_odoo --valid-odoo-versions=19.0 --disable=all --enable=odoolint` | 1,534 messages: W8161 ×1105, E8140 ×90, W8301 ×81, W8120 ×46, W8106 ×21, W8163 ×9, W8164 ×6, E8103 ×3 (false positive), 5 others |
| lxml | — | parse all XML (`ls_*` and whole `addons/`) | 0 errors in 1,516 files |
| RNG | Odoo 19.0 schemas | validate list, search, graph, pivot, calendar and activity archs | 384 archs, 0 failures |
| XPath | Odoo 19.0 source | resolve 16 inherited XPaths against parent archs | 16 of 16 match |
| Odoo install, co-install, demo install, upgrade, uninstall | 19.0-20260723 | see section 13 | 23/23 install; 23/23 co-install; 20/23 load demo data; 23/23 upgrade; 23/23 uninstall |
| coverage.py | installed in the container | `coverage run --source=<module> --omit=*/tests/*` over each suite | 65.9% (section 13) |

W8301 was reviewed: the pattern `_("…%s") % x` translates correctly, so it is not a defect.


## 10. Test assessment

| Item | Result |
|---|---|
| Written | 2,558 test methods in 22 modules; `ls_import_export` has none |
| Executed by Odoo | 1,988 (four suites cannot start: `ls_complaint`, `ls_electronic_signature_test`, `ls_medical_plastics`, `ls_supplier_qualification`) |
| Failed or errored | 422 (35 failures, 387 errors); identical in both runs (2026-09-24 and 2026-09-25) |
| Fully passing | `ls_cosmetics` 110 / 110 |
| Line coverage | 65.9% overall (section 13) against a 95% target |
| Probe tests added by the audit | 34: 16 stock workflows (all pass), 18 finding probes (16 reproduce a finding, 2 pass) |

**Where the 422 failures come from:**

| Origin | ≈ Count | Findings |
|---|---|---|
| Test code not ported to Odoo 19 or badly designed | 150 | F-40 |
| Test users without Internal User | 48 | F-27 |
| ACL versus specification (environmental monitoring) | 86 | F-41 |
| Product defects | ≈138 | F-02, F-04, F-35, F-36, F-37, F-39, F-42, F-43 and others |

**Coverage matrix of the brief (section 14 of the brief)**

| # | Area | Status |
|---|---|---|
| 1 | Installation | PASS: 23/23 alone, 23/23 together |
| 2 | Upgrade | PASS: 23/23 with demo data (one retry, cron collision) |
| 3 | Module dependencies | PASS: every module installs with only its declared dependencies |
| 4 | User permissions | FAIL: F-01, F-03, F-14, F-27 |
| 5 | Multi-company | FAIL: F-09, F-13, F-16, F-24 |
| 6–10 | Receipts, deliveries, internal transfers, returns, backorders | PASS (probe P1) |
| 11–12 | Lots, serial numbers | Standard: PASS; LSS traceability: FAIL (F-07, F-17) |
| 13 | Inventory adjustments | PASS |
| 14 | Cancellation | PASS |
| 15 | Partial operations | PASS |
| 16 | Concurrent operations | FAIL with audit on stock (F-10); PASS without |
| 17 | Custom business workflows | FAIL: 422 suite failures; F-35, F-37, F-39, F-42, F-43 |
| 18 | Security boundaries | FAIL: F-01, F-03, F-11, F-14 |
| 19 | Error conditions | Partly covered by module suites |
| 20 | Data integrity | FAIL: F-04, F-16, F-36 |

## 11. Remediation plan

| Priority | Findings | Action | Owner type | Test required | Release blocker |
|---|---|---|---|---|---|
| P1 | F-05 | Remove `patch-delivery.sh` and `base_delivery_patch`; rebuild from a digest-pinned `odoo:19`; then `-u delivery` on a copy of production | DevOps | Install `delivery`; upgrade a production copy | Yes |
| P1 | F-01, F-03 | Compute the partner and lot indicators under `sudo()` (or `compute_sudo=True`) | Odoo developer | Probes F-01, F-01c, F-03 pass | Yes |
| P1 | F-02 | `groups_id` → `all_group_ids` in code, demo and tests | Odoo developer | Suite + demo install | Yes |
| P1 | F-04 | `models.Constraint`, with a duplicate-cleanup pre-migration | Odoo developer + DBA (Database Administrator) | 12 constraint tests + upgrade of a production copy | Yes |
| P1 | F-35, F-36 | `precompute=True` on the required stored computed fields | Odoo developer | Probes F-35, F-36; suites | Yes |
| P1 | F-42 | Persist recomputed statuses in the refresh jobs | Odoo developer | Two cron tests | Yes |
| P1 | F-10 | Chain positions from a per-company sequence (audit trail and e-signature) | Odoo developer | `perf_concurrency.py`: 30/30 | Yes, if any busy model is audited |
| P2 | F-06, F-07 | Design lot blocking and downstream genealogy; decide ownership | Architect + stock developer | Probes F-06, F-07 + P1 stock suite | Yes for GMP use |
| P2 | F-09, F-11, F-13, F-14, F-16, F-17, F-24, F-27, F-37, F-39, F-43 | Code fixes per finding | Odoo developer | Matching probes and suites | Yes |
| P2 | F-40, F-41 | Port the test code; decide the environmental-monitoring ACL | QA (Quality Assurance) + process owner | Suites green | Yes |
| P3 | F-45 | Re-measure coverage after P1–P2; raise towards 95% | QA | Coverage report | Condition |
| P3 | F-12, F-15, F-18, F-19, F-20, F-21 | Clean-up and hardening | Developer / DevOps | Targeted | Condition / production |
| P4 | LOW and INFO | Clean-up | Developer | Targeted | No |

After P1 and P2, re-run `audit_campaign/run_campaign.ps1` (fixed version) and the module suites. The expected outcome is all probes passing and 0 suite failures.

## 12. Release gate

| Area | Result | Basis |
|---|---|---|
| Odoo 19 compatibility | **FAIL** | F-02, F-04, F-05 (runtime) |
| Stock integrity | **FAIL** | Standard engine PASS (16/16); LSS stock functions FAIL: F-03, F-06, F-07, F-17 |
| Security | **FAIL** | F-01, F-03, F-11, F-14 (runtime) |
| Data integrity | **FAIL** | F-04, F-16, F-24, F-36, F-42 (runtime) |
| Performance | **FAIL** | F-10 (50% concurrent failures with audited stock); ×1.70 cost otherwise acceptable |
| Testing | **FAIL** | 422 of 1,988 fail; 4 suites cannot start; coverage 65.9% |
| Maintainability | **PASS WITH CONDITIONS** | F-18, F-19, F-20 |
| Upgradeability | **FAIL** | Module install/upgrade/uninstall PASS 23/23, but F-05 blocks upgrading `delivery` in production |

## 13. Runtime results per module

**Environment:** container `odoo19Claude_ls`, image Odoo 19.0-20260723, PostgreSQL 16; one scratch database per module and step. Module suites: `logs/tests/` (2026-09-24) and `logs/campaign/07_*_tests.log` (2026-09-25, identical results). Demo install, upgrade and uninstall: `logs/campaign/04_*`. Coverage: `logs/campaign/07_*_coverage.txt`.

| Module | Suite: run | Failed | Errors | Demo data loads | Upgrade | Uninstall | Coverage | Main cause of failures |
|---|---|---|---|---|---|---|---|---|
| ls_audit | 135 | 4 | 55 | Yes | Yes | OK | 73% | Fixture (programme not approved); **F-04** |
| ls_audit_trail | 97 | 2 | 4 | Yes | Yes | OK | 89% | F-40 (test design); **F-38** |
| ls_calibration | 101 | 0 | 6 | Yes | Yes | OK | 37% | Test code (`assertRaises`) |
| ls_capa | 112 | 5 | 7 | Yes | Yes | OK | 97% | **F-04**; date fixtures; `search=` methods |
| ls_change_control | 121 | 0 | 76 | Yes | Yes | OK | 51% | Test code (`res.groups.users`) |
| ls_complaint | **0** | 0 | 9 | Yes | Yes | OK | 45% | Test code (`res.groups.users`) blocks every class |
| ls_cosmetics | 110 | 0 | 0 | Yes | Yes | OK | 77% | **All pass** |
| ls_deviation | 92 | 1 | 2 | Yes | Yes | OK | 94% | F-40 (fixtures, timestamps) |
| ls_document_management | 101 | 1 | 4 | Yes | Yes, demo reload rejected (F-44) | OK | 94% | **F-39** (approval re-submission); F-40 (exception type, NewId comparison) |
| ls_electronic_signature | 56 | 1 | 3 | **No** (F-02) | Yes | OK | 54% | **F-02**; test code (F-40) |
| ls_electronic_signature_test | **0** | 0 | 8 | **No** (F-02) | Yes | OK | 93% | Test code (`groups_id`) |
| ls_environmental_monitoring | 104 | 0 | 88 | Yes | Yes | OK | 47% | **F-41** (86); F-27 (2) |
| ls_import_export | 0 | 0 | 0 | Yes | Yes | OK | 77% | No tests exist |
| ls_lab | 91 | 0 | 18 | Yes | Yes | OK | 82% | F-27 (17) |
| ls_medical_device | 137 | 6 | 24 | Yes | Yes | OK | 74% | F-27 (10); **F-43** (5); fixtures |
| ls_medical_plastics | **0** | 0 | 11 | Yes | Yes | OK | 53% | F-27 blocks every class |
| ls_pharma | 121 | 2 | 12 | Yes | Yes | OK | 65% | test users without Internal User (8, F-27); mixin model without ACL; fixtures |
| ls_qms | 115 | 0 | 3 | Yes | Yes | OK | 94% | F-39 |
| ls_recall | 99 | 0 | 27 | Yes | Yes | OK | 78% | **F-35** (15); **F-03**; test code |
| ls_risk_management | 161 | 2 | 3 | Yes | Yes | OK | 56% | F-39 |
| ls_supplier_qualification | **0** | 0 | 14 | **No** (F-36) | Yes | OK | 44% | **F-36** blocks every class |
| ls_training | 146 | 8 | 2 | Yes | Yes, demo reload rejected (F-44) | OK | 96% | **F-04**; **F-42** |
| ls_validation | 89 | 3 | 11 | Yes | Yes (retry) | OK | 82% | **F-37**; **F-42** |
| **Total** | **1,988** | **35** | **387** | **20 / 23** | **23 / 23** | **23 / 23** | **65.9%** | 422 failing results |

**Other runtime results:**

| Check | Result | Log |
|---|---|---|
| Co-installation of the 23 modules | PASS: 116 modules loaded, no error | `03_coinstall_all.log` |
| F-05: install `delivery` + `stock_delivery` | **FAIL**: `External ID not found: base.module_list` | `02_f05_delivery_install.log` |
| Modules installed in production (read only) | 239; includes `delivery` | `01_installed_modules_main_db.txt` |
| Probes (34) | 16/16 stock workflows pass; 16 of 18 finding probes reproduce the finding (F-01, F-01c, F-03, F-06a, F-06b, F-07, F-09, F-11, F-13, F-13b, F-14, F-16, F-17, F-24, F-35, F-36); 2 pass (F-01b purchase form, F-27 internal-user control) | `05_probes_v2.log` |
| Performance and concurrency | ×1.70 with audited stock; 15/30 concurrent failures (F-10) | `06_perf_concurrency_v2.log` |

## 14. Final release decision

# RELEASE BLOCKED

| Category | Items |
|---|---|
| **Defects demonstrated at runtime** | F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-09, F-10, F-11, F-13, F-14, F-16, F-17 (UoM), F-21 (cron on all databases), F-24, F-27, F-35, F-36, F-37, F-38, F-39, F-41, F-42, F-43, F-44, F-45 |
| **Risks identified by inspection only** | F-12, F-15, F-17 (access part), F-18, F-19, F-20, F-22, F-25, F-26, F-28, F-29 to F-32; the same chain collision in the e-signature log (F-10) |
| **Areas successfully tested** | Installation (23/23), co-installation, upgrade with data (23/23), uninstall (23/23), 16 standard stock workflows with and without auditing, audit-chain integrity after stock operations, `ls_cosmetics` (110/110), static analysis |
| **Withdrawn after runtime evidence** | F-33, F-34 |
| **Areas NOT VERIFIED** | Line-by-line review of the ≈430 third-party OCA modules (out of the custom scope; 239 modules are installed in production); F-12 (would require breaking a live install); F-15 at runtime; rendering of the F-22 forms in a browser; production-size performance; behaviour of scheduled jobs over time |

The release can be reconsidered when the P1 and P2 actions in section 11 are done and a re-run of the campaign and the module suites shows the probes passing and no suite failure.

A code review and a test campaign cannot prove the absence of defects. This report certifies nothing, and makes no claim of regulatory compliance.
