# Odoo 19 CE — Independent Code Review & Release Audit

**System:** `D:\Docker\odoo19Claude_ls-docker` (Life Sciences Suite + OCA (Odoo Community Association) addons)
**Audit date:** 2026-09-24 · **Mode:** Phase 1, review only. No source file was modified.
**Revision 2 (same day):** adds the results of a runtime test campaign executed by the project owner on the project's own container (section 13). Every finding confirmed or contradicted by that run is marked accordingly.
**Reference source:** `odoo/odoo` branch `19.0`, commit `2e2acfd6d2725d1a4a95b1a6056334e1ac34163f` (2026-09-24). The exact build of the `odoo:19` Docker image used by the project is **NOT VERIFIED**. Findings that depend on Odoo internals were checked against this commit.

---

## 0. Evidence basis — read this first

| Category | What it covers |
|---|---|
| **Demonstrated (runtime)** | **Revision 2:** full install and test run of all 23 `ls_*` modules on 2026-09-24, image **Odoo 19.0-20260723**, one scratch database per module (`t_<module>`), logs in `logs/tests/`. Also the older logs `addons/install.log` and `addons/test.log` (2026-08-06). |
| **Verified by inspection** | Custom code read and cross-checked against the Odoo 19.0 source (the ORM (Object-Relational Mapping) field access path, `res.users` / `res.groups` / `ir.rule` / `ir.cron` definitions, view RNG (RELAX NG) schemas, XML IDs). |
| **Executed in this audit** | Static tools only (section 9). |
| **NOT VERIFIED** | Upgrade, uninstall, installation with demo data, the standard stock workflows, multi-company at runtime, performance. The auditor could not reach the containers directly; the test campaign in section 13 was run by the project owner using the auditor's commands, and the auditor read the logs. |

Findings marked "verified by inspection" trace a precise code path through the Odoo 19.0 source. Findings marked **"confirmed at runtime"** were reproduced by the 2026-09-24 test run.

---

## 1. Executive summary

**Overall technical status:** not releasable.

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH | 10 |
| MEDIUM | 19 |
| LOW | 7 |
| INFO | 4 |
| **Total** | **41** |

**Runtime test result (2026-09-24, revision 2):** all 23 modules **install** on Odoo 19.0-20260723. Odoo ran **1,988 tests**; **422 failed or errored**. Only `ls_cosmetics` passes completely (110 of 110). In 4 modules no test could start at all (`ls_complaint`, `ls_electronic_signature_test`, `ls_medical_plastics`, `ls_supplier_qualification`), and `ls_import_export` has no tests. About half of the failures come from test code that was never ported to Odoo 19. The rest confirm real defects, including F-02, F-03 and F-04 and nine new findings (F-33 to F-41). See section 13.

**Critical blockers**
- **F-01:** after `ls_supplier_qualification` is installed, the standard **Contacts form and Purchase Order form** raise AccessError for every user who lacks a supplier-qualification group.
- **F-02:** the `ls_electronic_signature` signing wizard calls `res.users.groups_id`, a field that does not exist in Odoo 19. Every signature attempt fails with AttributeError. **Confirmed at runtime.**
- **F-03:** after `ls_recall` is installed, the standard **Lot/Serial form** raises AccessError for inventory users who lack a recall role. **Confirmed at runtime:** the module's own test fails at exactly the line identified.
- **F-04:** 30 database constraints (24 UNIQUE, 6 CHECK) in `ls_audit`, `ls_capa`, `ls_complaint` and `ls_training` use `_sql_constraints`. Odoo 19 ignores that attribute, so none of these constraints exists. **Confirmed at runtime** in `ls_audit`, `ls_capa` and `ls_training` ("IntegrityError not raised").
- **F-33 (new, runtime):** records in `ls_lab`, `ls_pharma`, `ls_medical_plastics`, `ls_medical_device` and `ls_environmental_monitoring` take their reference from `ir.sequence` without `sudo()`. On Odoo 19 ordinary users are refused, so they cannot create OOS investigations, batch release decisions, moulding parameters, devices or samples.
- **F-34 / F-35 (new, runtime):** medical-device state changes fail for non-administrators, and recall effectiveness checks cannot be generated at all.
- **F-05:** the Docker build rewrites Odoo core files with `sed`, replacing valid XML IDs with IDs that do not exist in 19.0. An auto-installed module also tries to overwrite core files at import time and swallows every exception.

**Major risks**
- Quality decisions are not enforced in inventory: batch release, OOS (Out of Specification) and recall status do not stop a lot from being reserved or shipped (F-06).
- Recall tracing does not follow lot genealogy from component to finished product (F-07).
- There is no current test-execution evidence (F-08).

**Test coverage status:** 2,558 test methods are written; Odoo executed 1,988 of them on 2026-09-24 and 422 failed or errored (section 13). Coverage was never measured.

**Security status:** FAIL. Record-access design breaks standard forms (F-01, F-03). The e-signature password is persisted in clear text (F-11). Folder rules ignore implied groups (F-14). No HTTP (Hypertext Transfer Protocol) controllers and no public routes exist in the custom modules.

**Stock integrity status:** the custom code never writes stock records: it defines no override of `stock.*` business methods and only reads stock data. No path to stock-quantity corruption was found by inspection. However, stock-related functions are broken or incomplete (F-03, F-06, F-07, F-16, F-17), and the standard stock workflows were **NOT VERIFIED** at runtime.

---

## 2. Architecture assessment (discovered)

**Platform:** Docker Compose, with the images `odoo:19` (floating tag) and `postgres:16`. Port 8069 is published on 8071. The addons path is `/mnt/extra-addons,/mnt/found-addons`. The Dockerfile installs `numpy pandas scipy scikit-learn sentry_sdk odoorpc` and runs `patch-delivery.sh`. The container's Python version is **NOT VERIFIED**; the image layout seen in `test.log` is `/usr/lib/python3/dist-packages/odoo/orm/...`.

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
| **Defect** | `res.users.groups_id` is used in 3 Python sites and in demo XML. It does not exist in 19.0 (renamed to `group_ids` / `all_group_ids`, `res_users.py:257-258`). See F-02. |
| **Defect** | `_sql_constraints` appears in 29 files. 19.0 logs "no longer supported" and creates nothing (`odoo/orm/model_classes.py:162-164`). See F-04. |
| **Defect** | `patch-delivery.sh` renames `stock.view_move_line_tree_detailed` and `base.module_tree`. Both IDs exist unchanged in 19.0 (`stock/views/stock_move_line_views.xml:40`, `base/views/ir_module_views.xml:128`); the replacement IDs do not exist. See F-05. |
| **Risk** | 9 form views use `<div class="oe_chatter">`. The 19.0 form compiler only handles `<chatter/>` (`mail/static/src/chatter/web/form_compiler.js:47`). See F-22. |
| **Pass** | 156 search views, 182 list, 22 graph, 18 pivot, 4 calendar and 2 activity views validate against the 19.0 RNG schemas. |
| **Pass** | All 16 inherited-view XPaths resolve against the 19.0 parent architectures. |
| **Pass** | No `name_get`, `read_group` (public), `search_read`, `fields_view_get`, `qty_done`, `quantity_done`, `detailed_type`, `uom.category`, `self._context`, `self._cr`, `numbercall` or `doall` in live code. |
| **Pass** | `res.groups.privilege_id` is used correctly throughout. |
| **Pass** | The `_check_credentials(credential, env)` convention matches 19.0 (`res_users.py:312`). |

---

## 4. Finding register

| ID | Severity | Module | Area | Finding | Release impact |
|---|---|---|---|---|---|
| F-01 | CRITICAL | ls_supplier_qualification | Security / UI | Contacts and PO (Purchase Order) forms raise AccessError for users without a qualification group | Blocker |
| F-02 | HIGH | ls_electronic_signature | Odoo 19 compat | `user.groups_id` makes the signature wizard fail every time; demo data cannot load | Blocker |
| F-03 | HIGH | ls_recall | Stock UI / Security | Lot form raises AccessError for stock users without a recall role | Blocker |
| F-04 | HIGH | ls_audit, ls_capa, ls_complaint, ls_training | Data integrity | 30 declared DB constraints are never created | Blocker |
| F-05 | HIGH | Docker build, base_delivery_patch | Upgradeability / Security | Core files patched with invalid IDs; import-time core overwrite attempt | Blocker |
| F-06 | HIGH | ls_pharma, ls_lab, ls_recall | Stock / business logic | Release, OOS and recall decisions do not block reservation or delivery | Blocker for GMP (Good Manufacturing Practice) use |
| F-07 | HIGH | ls_recall | Stock traceability | Trace ignores component → finished-lot genealogy | Blocker for manufacturers |
| F-08 | HIGH | All | Testing | Test evidence absent at first review; now superseded by the run in section 13 (422 of 1,988 fail) | Blocker |
| F-09 | MEDIUM | ls_audit_trail | Business logic | Audit rule chosen by the user's active company, not the record's company | Fix before release |
| F-10 | MEDIUM | ls_audit_trail | Concurrency | Per-company advisory lock serializes every audited transaction; deadlock path | Condition |
| F-11 | MEDIUM | ls_electronic_signature | Security | Signing password stored in clear text in the wizard table | Fix before release |
| F-12 | MEDIUM | ls_electronic_signature | Install integrity | `cr.rollback()` inside `init()` | Fix before release |
| F-13 | MEDIUM | ls_supplier_qualification | Multi-company | Dossier from `env.company` checked against a PO of another company | Fix before release |
| F-14 | MEDIUM | ls_document_management | Security | Folder rules use explicit groups only (`group_ids`) | Fix before release |
| F-15 | MEDIUM | ls_medical_device | Computed fields | Date-dependent stored fields never refreshed | Fix before release |
| F-16 | MEDIUM | ls_pharma, ls_lab, ls_medical_plastics | Data integrity | No lot / product / company consistency check | Fix before release |
| F-17 | MEDIUM | ls_recall | Stock / Security | Quantities summed in mixed UoM (Unit of Measure); coordinators need stock rights | Fix before release |
| F-18 | MEDIUM | ls_calibration | Maintainability | Second, dead implementation alongside the live one | Fix before release |
| F-19 | MEDIUM | Project | Quality evidence | "Zero pylint findings" relies on disabling 50+ checks | Condition |
| F-20 | MEDIUM | OCA addons | Maintainability | Regex bulk edits of third-party code; 18.0 modules relabelled 19.0 | Condition |
| F-21 | MEDIUM | Deployment | Security | `list_db=True`, clear-text DB (database) credentials, floating image tag | Fix before production |
| F-22 | LOW | ls_import_export, ls_medical_plastics | UI | Legacy `oe_chatter` markup in 9 forms | Post-release |
| F-23 | LOW | 18 modules | Maintainability | 90 `raise` in `unlink()` instead of `@api.ondelete` | Post-release |
| F-24 | LOW | ls_qms, ls_document_management, ls_medical_device, ls_supplier_qualification | Multi-company | 13 `check_company=True` fields not enforced on the server | Post-release |
| F-25 | LOW | Addons path | Maintainability | Duplicate `ls_import_export`; non-module folder in `found/` | Post-release |
| F-26 | LOW | ls_electronic_signature_test | Security | Test-only module installable in production | Post-release |
| F-27 | LOW | 16 modules | Security | 18 root groups do not imply `base.group_user` | Post-release |
| F-28 | LOW | ls_supplier_qualification | Business logic | Counter method: KeyError without stock; last day excluded | Post-release |
| F-33 | HIGH | ls_lab, ls_pharma, ls_medical_plastics, ls_medical_device, ls_environmental_monitoring | Security / Odoo 19 | `ir.sequence.next_by_code()` without `sudo()`: ordinary users cannot create records (runtime) | Blocker |
| F-34 | HIGH | ls_medical_device, ls_lab | Security / workflow | State changes and revisions raise AccessError on `res.company` / `mail.message` for non-admin users (runtime) | Blocker |
| F-35 | HIGH | ls_recall | Business logic | "Generate effectiveness checks" fails: NOT NULL violation on `partner_id` (runtime) | Blocker |
| F-36 | MEDIUM | ls_supplier_qualification | Data / tests | Creating a qualification violates NOT NULL on `criticality`; whole suite cannot start (runtime) | Fix before release |
| F-37 | MEDIUM | ls_validation | Business logic | Validation items cannot be e-signed (mixin missing); expiry cron and protocol state wrong (runtime) | Fix before release |
| F-38 | MEDIUM | ls_audit_trail | Data integrity | Binary-field audit crashes writes; tamper check misses tampering; purge refuses a valid chain; duplicate rules accepted (runtime) | Fix before release |
| F-39 | MEDIUM | ls_qms, ls_risk_management, ls_electronic_signature, ls_deviation, ls_training | Business logic | Revision and state defects confirmed by failing tests (runtime) | Fix before release |
| F-40 | MEDIUM | 11 modules | Testing | Test code not ported to Odoo 19 (`res.groups.users`, `res.users.groups_id`, `stock.move.name`, `ir.rule.global_`) and broken fixtures (runtime) | Fix before release |
| F-41 | MEDIUM | ls_environmental_monitoring | Security design | ACL lets only managers create plans and limits; the tests (specification) expect technicians to (runtime) | Decision required |
| F-29 | INFO | 9 modules | Code quality | Constraints raise `UserError`; 44 `assertRaises(Exception)` | — |
| F-30 | INFO | Suite | Documentation | README dependency table contradicts manifests | — |
| F-31 | INFO | 11 modules | Security data | `global` written explicitly on 86 `ir.rule` records | — |
| F-32 | INFO | ls_validation, ls_cosmetics, ls_medical_device | Dead code | `numbercall` / `doall` compatibility hooks | — |

---

## 5. Detailed findings

### F-01 — CRITICAL — Standard Contacts and Purchase forms raise AccessError
- **Module / files:**
  - `ls_supplier_qualification/views/res_partner_views.xml:32-33`
  - `models/res_partner.py:14-18, 49-71` (`_compute_ls_qualification`)
  - `models/purchase_order.py:21-40` (`_compute_ls_qualification_warning`)
  - `views/purchase_order_views.xml:12`
- **Evidence:** `ls_is_approved_supplier` and `ls_qualification_id` are added to `base.view_partner_form` with no `groups` attribute. Their compute reads the One2many `ls_qualification_ids` as the current user, because `compute_sudo` defaults to False for non-stored computed fields (`odoo/orm/fields.py:448`). In 19.0, `One2many.read()` calls `comodel.search_fetch()` and wraps an AccessError as "Failed to read field" (`fields_relational.py:940-956`). Read access on `ls.supplier.qualification` is granted only to the three qualification groups (`security/ir.model.access.csv:17-19`). `ls_qualification_warning` is also placed on `purchase.order_form` without groups (line 12).
- **Impact:** every internal user without a supplier-qualification group (sales, accounting, inventory) cannot open any contact, and purchase users cannot open a PO.
- **Reproduction:**
  1. Install the module.
  2. Create a user with only Sales / User.
  3. Open any contact.
  4. Expected result: AccessError "Failed to read field res.partner.ls_qualification_ids".
- **Recommendation:** compute `_compute_ls_qualification` and `_compute_ls_qualification_warning` through `sudo()` restricted to the fields needed, or set `compute_sudo=True` on the non-stored computed fields. Keep the company filter. Add `groups=` to the invisible fields. **Regression risk:** low. **Test:** open partner and PO forms `with_user()` as a user with no qualification group.

### F-02 — HIGH — E-signature uses the removed `res.users.groups_id`
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

### F-03 — HIGH — Lot/Serial form raises AccessError for inventory users
- **Files:**
  - `ls_recall/models/stock_lot.py:40-62`
  - `views/stock_lot_views.xml:21-24`
  - `tests/test_security.py:111-122`
- **Evidence:** `ls_recall_open` is displayed on `stock.view_production_lot_form` for everyone. Its compute evaluates `lot.ls_recall_execution_ids` **before** `.sudo()`. `Many2many.read()` runs `comodel._search()`, which calls `check_access('read')` (`fields_relational.py:1377-1391`; `models.py:5364-5366`). `ls.recall.execution` is readable only by the recall groups. The docstring and test `test_lot_indicator_readable_without_a_recall_role` assert the opposite.
- **Impact:** after installation, warehouse users without a recall role cannot open lots, and the stated safeguard (risk R6, "warn warehouse staff") does not work.
- **Reproduction:** as a user with Inventory / User only, open any lot.
- **Recommendation:** read the relation under `sudo()` from the start, for example `lot.sudo().ls_recall_execution_ids`, or set `compute_sudo=True`. **Regression risk:** low. **Test:** keep the existing test and run it.

### F-04 — HIGH — 30 database constraints do not exist
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

### F-05 — HIGH — Core Odoo files patched at build time and at import time
- **Files:** `patch-delivery.sh`, `Dockerfile:7`, `addons/base_delivery_patch/__init__.py`, `__manifest__.py` (`auto_install: True`, no license).
- **Evidence:**
  - `sed` replaces `view_move_line_tree_detailed` with `view_move_line_list_detailed` in `stock_delivery/views/delivery_view.xml`, and `module_tree` with `module_list` in `delivery/views/ir_module_module_views.xml`.
  - In 19.0 the original IDs exist (`stock/views/stock_move_line_views.xml:40`, `base/views/ir_module_views.xml:128`) and the replacement IDs do not exist anywhere.
  - `sale_manual_delivery` depends on `stock_delivery`, and `sale_order_carrier_auto_assign` depends on `delivery`.
  - `base_delivery_patch` copies `/tmp/delivery_patch/...` over a core file on Python import and wraps everything in `except Exception: pass`.
- **Impact:** installing `delivery` or `stock_delivery` should fail with "External ID not found". This is verified against 19.0 HEAD only; the image build is NOT VERIFIED. Core is modified outside version control, and the auto-install module is a latent path to overwrite core code with a file from a world-writable directory; it is blocked today only by file permissions.
- **Recommendation:** remove both mechanisms. Rebuild the image from an unmodified, digest-pinned `odoo:19`. If a real incompatibility existed, fix it in the dependent module, not in core. **Regression risk:** low. **Test:** install `delivery` and `stock_delivery` on a scratch DB.

### F-06 — HIGH — Quality decisions not enforced in inventory operations
- **Files:**
  - `ls_pharma/models/ls_pharma_batch.py:67-77`: `lot_id` is informational; no stock hook.
  - `ls_lab/models/ls_lab_oos.py:169`: the "Remain In Quarantine" disposition has no stock effect.
  - `ls_recall/doc/01_business_analysis.md` §8: "module warns; it does not move goods".
- **Evidence:** no custom override of `stock.move`, `stock.move.line`, `stock.picking` or `stock.quant` exists (section 2). Only the recall exclusion is documented; the batch-release and OOS gaps are not declared out of scope.
- **Impact:** a batch with no release decision, a rejected batch, a lot under OOS investigation or a lot under recall can be reserved and delivered through standard Odoo with no warning in the transfer.
- **Recommendation:** block these lots through a standard mechanism: a lot-level blocked flag checked in `stock.move.line` validation / `_action_done`, or a quarantine location with restricted routes. Decide which module owns it. **Regression risk:** high (core stock flow), so it needs a full stock regression suite. **Test:** receipt, reservation, delivery and backorder with blocked and released lots.

### F-07 — HIGH — Recall tracing does not follow lot genealogy
- **Files:** `ls_recall/models/ls_recall_execution.py:848-886` (`_scan_move_lines`)
- **Evidence:** the domain is `lot_id in self.lot_ids`, `state = done`, destination usage `customer`. The consumption of a recalled component lot in manufacturing orders (MO) is never followed to the finished lots produced, and this limitation is not listed in §8 "Out of scope".
- **Impact:** recalling a raw-material or intermediate lot finds no consignees of the finished products that contain it, and the chatter summary gives no warning.
- **Recommendation:** add downstream traversal (consumed move lines → produced lots, recursively), or state the limitation in the UI (User Interface) and require manual lot selection. **Test:** component lot → MO → finished lot → delivery; the recall on the component must list the consignee.

### F-08 — HIGH — No current test-execution evidence; tests inconsistent with code
- **Evidence:**
  - The only run on record is `addons/test.log`: `ls_cosmetics`, 2026-08-06, "0 failed, 5 error(s) of 108 tests". The errors are `test_label`, `test_pif`, 2× `test_security` (inside `mail_thread._message_log_batch`) and `test_wizards`. The code was then mass-edited on 2026-08-08 to 2026-08-10 (`FIXES_SUMMARY.md`).
  - Three `ls_calibration` test files are not imported and never run (`test_plan_and_oot`, `test_security_and_integration`, `test_tolerance`). They reference models that exist only in dead code (F-18).
  - `ls_import_export` has no tests.
  - Tests exist that should fail on the current code: `ls_recall/tests/test_security.py:111` (F-03), and `ls_electronic_signature` tests writing `groups_id` (F-02).
- **Impact:** no module's behaviour on Odoo 19 is currently demonstrated.
- **Recommendation:** run `odoo -d ls_test -i <module> --test-enable --stop-after-init` per module on a scratch DB, with coverage measured. Resolve every error before release.

### F-09 — MEDIUM — Audit trail picks rules by the user's active company
- **File:** `ls_audit_trail/models/base_audit.py:65`
- **Evidence:** `_ls_audit_config_for(self._name, self.env.company.id)` searches rules with `company_id in [False, env.company]`. The chain company, by contrast, is the record's company (`_ls_record_company_id`).
- **Impact:** a user working with companies A and B active (current company A) writes a B record. A rule defined only for B is not applied and the change is not audited, or A's rule is applied to B's data.
- **Recommendation:** resolve the configuration per record company (group `self` by `company_id`). **Test:** a multi-company write with rules on only one company.

### F-10 — MEDIUM — Audit chain lock serializes all audited writes per company
- **File:** `ls_audit_trail/models/ls_audit_trail_log.py:579-591, 617-651`
- **Evidence:** `pg_advisory_xact_lock(namespace, company)` is taken **after** the audited row is written and held until commit.
- **Impact:** if high-volume models such as `stock.move`, `stock.quant` or `mrp.production` are audited, all such transactions in a company run one at a time. The row-lock → advisory-lock ordering creates a deadlock path (T1 locks row X then waits on the chain; T2 holds the chain and then needs X).
- **Recommendation:** document that stock-engine models are not supported for auditing, or move sealing to an asynchronous sequencer. **Test:** concurrent validation of two pickings with `stock.move` audited. **NOT VERIFIED** at runtime.

### F-11 — MEDIUM — Signature password persisted in clear text
- **File:** `ls_electronic_signature/wizards/ls_signature_wizard.py:38,76`
- **Evidence:** `ls.signature.wizard` is a `TransientModel`, and `password = fields.Char()` is a stored column. The web client saves the wizard before calling `action_sign`, and the value is never cleared.
- **Impact:** passwords sit in `ls_signature_wizard.password` until the transient vacuum runs, and also end up in WAL (Write-Ahead Log) files and backups.
- **Recommendation:** keep the field but clear it (`self.password = False`) in a `finally` block before any exception, or pass the password as a method argument from a non-stored field. Purge existing rows. **Migration:** `UPDATE ls_signature_wizard SET password = NULL`.

### F-12 — MEDIUM — Transaction rollback inside `init()`
- **File:** `ls_electronic_signature/models/ls_signature_log.py:202-245`
- **Evidence:** if trigger creation fails, `self.env.cr.rollback()` runs in the middle of module installation.
- **Impact:** it silently discards all work done earlier in the install transaction, including other modules' data, while the loader continues, leaving an inconsistent registry and database.
- **Recommendation:** use `with self.env.cr.savepoint():`.

### F-13 — MEDIUM — Supplier control mixes companies
- **Files:** `ls_supplier_qualification/models/res_partner.py:57`, `purchase_order.py:43-75`
- **Evidence:** the dossier is taken from `self.env.company`, while the policy comes from `order.company_id`.
- **Impact:** confirming company B's PO while the active company is A checks A's dossier, so an unqualified supplier can pass or a qualified one can be blocked.
- **Recommendation:** resolve the dossier with `order.company_id`, for example by passing it as the company context. **Test:** a multi-company PO confirmation.

### F-14 — MEDIUM — Folder access rules ignore implied groups
- **File:** `ls_document_management/security/ls_document_record_rules.xml:72,83,101,112`
- **Evidence:** the rules use `user.group_ids.ids`, which holds explicitly assigned groups only (`res_users.py:257`).
- **Impact:** users who get a folder's group through an implied group are denied read or write.
- **Recommendation:** use `user.all_group_ids.ids`.

### F-15 — MEDIUM — Date-dependent stored fields go stale
- **File:** `ls_medical_device/models/device.py:295-311, 394-425, 777-830`
- **Evidence:** `periodic_report_overdue`, `next_periodic_report_due` and `active_ce_marking_id` (CE marking) are stored and computed from today's date, and no job recomputes them. The cron `_cron_check_post_market_obligations` reads the stored `periodic_report_overdue`.
- **Impact:** overdue post-market reports are never flagged or scheduled unless the device record is edited.
- **Recommendation:** recompute in the cron (as `ls_training`, `ls_validation` and `ls_medical_plastics` do) or make the fields non-stored. **Test:** freeze the date past the due date and run the cron.

### F-16 — MEDIUM — No lot / product / company consistency check
- **Files:** `ls_pharma/models/ls_pharma_batch.py:67`, plus the lot fields in `ls_lab` and `ls_medical_plastics`
- **Evidence:** there is no constraint that `lot_id.product_id == product_id` or that the lot's company matches, and none of the 21 `ls_pharma` models that carry `company_id` sets `_check_company_auto`. `ls_complaint` and `ls_recall` do have the check.
- **Impact:** a batch release or lab result can reference another product's or another company's lot, which breaks traceability.
- **Recommendation:** add `@api.constrains` for this check, and add `check_company=True` with `_check_company_auto = True`.

### F-17 — MEDIUM — Recall tracing: mixed UoM and access rights
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
- **Impact:** the local OCA copies no longer match upstream, and modules labelled 19.0 may contain unported 18.0 code. Which of these modules are installed in `odooClaude_ls_DB` is **NOT VERIFIED**.
- **Recommendation:** restore OCA modules from the upstream 19.0 branches and remove unported modules. **UNABLE TO CONFIRM** whether upstream 19.0 ports exist for each relabelled module.

### F-21 — MEDIUM — Deployment configuration
- **Files:** `config/odoo.conf`, `docker-compose.yml`, `Dockerfile`
- **Evidence:**
  - `list_db = True` and `proxy_mode = False`.
  - The PostgreSQL password is in clear text in the compose file.
  - Port 8071 is published on all interfaces.
  - The image is `odoo:19` (floating tag).
  - `pg_isready` has no `-h 127.0.0.1` (the healthcheck race condition already documented in the project).
  - `admin_passwd` is PBKDF2-hashed, which is correct.
- **Recommendation for production:** `list_db = False`, a `dbfilter`, secrets through environment variables or files, a reverse proxy with `proxy_mode = True`, and an image pinned by digest.

### F-33 — HIGH — Reference sequences read without `sudo()` (confirmed at runtime)
- **Files:** `ls_lab/models/ls_lab_oos.py:237`, `ls_lab/models/ls_lab_mixin.py:59`, `ls_lab/models/ls_lab_coa.py:143`, `ls_pharma/models/ls_pharma_batch_release.py:276`, `ls_medical_plastics/models/mp_molding_parameter.py:169`, `ls_medical_device/models/device.py:525`, `ls_environmental_monitoring/models/ls_env_sample.py:273`.
- **Evidence:** 38 test errors read "You are not allowed to access 'Sequence' (ir.sequence) records." The stack traces point to the `create()` lines above, all calling `self.env["ir.sequence"].next_by_code(...)` as the current user.
- **Impact:** a lab analyst cannot record an out-of-specification result (the OOS investigation is created automatically), a QP (Qualified Person) cannot record a batch release decision, and users cannot create moulding parameters, devices or environmental samples. `ls_medical_plastics` cannot even start its test suite.
- **Recommendation:** `self.env["ir.sequence"].sudo().next_by_code(...)`, which is the standard Odoo pattern. **Regression risk:** low. **Test:** the existing tests.

### F-34 — HIGH — Workflow actions fail for non-administrators (confirmed at runtime)
- **Files:** `ls_medical_device/models/device.py:572` (`_set_state`), `ls_lab/models/ls_lab_coa.py:146`, `ls_lab/models/ls_lab_specification.py:217`, `ls_lab/models/ls_lab_test_method.py:233`.
- **Evidence:** 10 errors: "You are not allowed to access 'Companies' (res.company) records" and "You are not allowed to create 'Message' (mail.message) records" when a role user changes a device state or revises a CoA (Certificate of Analysis), specification or test method.
- **Impact:** device lifecycle transitions (development, market placement, withdrawal) and lab document revisions only work for administrators.
- **Recommendation:** read company settings through `self.env.company.sudo()` or a stored related field; post chatter messages on records the user can write, or make the role groups imply `base.group_user` (see F-27). Re-run the listed tests.

### F-35 — HIGH — Recall effectiveness checks cannot be generated (confirmed at runtime)
- **File:** `ls_recall/models/ls_recall_execution.py:968` (`action_generate_effectiveness_checks`); model `ls.recall.effectiveness` (`partner_id` computed and required).
- **Evidence:** 15 errors: `NotNullViolation: null value in column "partner_id" of relation "ls_recall_effectiveness"`.
- **Impact:** the effectiveness step of a recall cannot be completed, so a recall cannot reach closure through the designed workflow.
- **Recommendation:** pass `partner_id` explicitly in the create values, or make the compute run before insert (`precompute=True`). **Test:** `TestEffectiveness`.

### F-36 — MEDIUM — Supplier qualification creation fails on `criticality`
- **Evidence:** all 14 test classes of `ls_supplier_qualification` fail in `setUpClass` with `NotNullViolation` on `ls_supplier_qualification.criticality`. The field is computed from the category and stored as required. **UNABLE TO CONFIRM** whether the defect is in the compute or only in the test fixture; either way the module's behaviour, including the purchase control and F-01, is not exercised at runtime.
- **Recommendation:** give `criticality` a default, or precompute it; fix the fixture; re-run.

### F-37 — MEDIUM — Validation module defects (confirmed at runtime)
- **Evidence:** `ls.validation.item` does not inherit `ls.validation.signature.mixin` (`models/ls_validation_item.py:31`), while the five other validation models do. 10 errors: `'ls.validation.item' object has no attribute '_ls_create_signature'` / `'_ls_verify_credentials'`. The sign wizard therefore refuses items with "does not support electronic signatures". Also failing: the expiry cron leaves an item "validated" after its validity ends, and approving an execution does not move the protocol to "executed".
- **Recommendation:** add the mixin to `ls.validation.item`; fix the cron and the protocol state update; re-run `test_signature`, `test_cron`, `test_execution`.

### F-38 — MEDIUM — Audit-trail integrity defects (confirmed at runtime)
- **Evidence:**
  - `OSError: Truncated File Read` raised from `ls_audit_trail/models/base_audit.py:106` (`write`) when a binary field is audited: **auditing a model with a binary field makes its writes fail.**
  - `test_archive_digest_self_check_detects_tampering`: "UserError not raised", so a tampered evidence pack is **not** detected.
  - 3 purge tests: the retention wizard refuses a chain that should verify (`ls_audit_trail_purge_wizard.py:191`).
  - `test_reject_duplicate_rule`: duplicate audit rules are accepted.
- **Recommendation:** read binary values as fingerprints without decoding; fix the evidence-pack self-check; debug `_ls_verify_chain` on the purge scenario; add a `models.Constraint` on rules.

### F-39 — MEDIUM — Further business-logic defects shown by failing tests
- `ls_qms`: creating a quality-plan revision writes a field that does not exist (`previous_revision_id`, `ls_qms_document_mixin.py:323`), so quality-plan revisions fail.
- `ls_risk_management`: an FMEA (Failure Mode and Effects Analysis) revision creates no copy; the assessment wizard hits a NOT NULL on `severity_level_id`.
- `ls_electronic_signature`: a successful signature does not clear the lockout counter (`test_success_clears_the_lockout`).
- `ls_training`: the refresh cron leaves an expired certification "valid"; capacity and duplicate-registration rules are not enforced (together with the F-04 constraints).
- `ls_deviation`: stage-log ordering is not reverse chronological.
- Each item is a failing test; the exact root cause of each was **not** analysed line by line.

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

- **Impact:** about 150 test results say nothing about the product. The code these tests should cover is **NOT VERIFIED** until they are fixed.
- **Recommendation:** port the test code (`user_ids`, `group_ids`, fixtures), then re-run the full campaign.

### F-41 — MEDIUM — Environmental monitoring: ACL contradicts the specification
- **Evidence:** 86 errors "You are not allowed to create 'Environmental Monitoring Limit' / 'Plan'" when the tests act as a technician. `security/ir.model.access.csv` grants create on these models to managers only.
- **Decision required:** either technicians must create plans and limits (fix the ACL) or only managers may (fix the tests and the documentation). Until decided, 86 of 104 tests in this module give no evidence.

### F-22 to F-28 — LOW

| ID | Evidence | Recommendation |
|---|---|---|
| F-22 | `<div class="oe_chatter">` in 3 `ls_import_export` views and 6 `ls_medical_plastics` views. The 19.0 compiler only transforms `<chatter/>`. Rendering is **UNABLE TO CONFIRM**. | Replace with `<chatter/>`. |
| F-23 | pylint E8140 ×90: `unlink()` raising directly (the immutable logs are intentional). Blocks cleanup of XML-ID records at uninstall. | Use `@api.ondelete(at_uninstall=False)`. |
| F-24 | 13 fields declare `check_company=True` in classes without `_check_company_auto` (`ls_qms` ×7, `ls_document_management` ×4, `ls_medical_device` ×1, `ls_supplier_qualification` ×1). Only the UI domain applies. | Set `_check_company_auto = True`. |
| F-25 | `ls_import_export` exists in both `addons/` and `found/` with 5 differing files; the first path wins. `found/wooden_marketplace_llm` is not a module. | Keep one copy and remove `found/` from the addons path. |
| F-26 | `ls_electronic_signature_test` is installable in production; `ls.signature.test.record` gives `base.group_user` full CRUD (Create, Read, Update, Delete). | Move it out of the production addons path. |
| F-27 | 18 root groups have no `implied_ids` (for example `group_ls_capa_viewer`, `group_ls_recall_viewer`, all 3 `ls_environmental_monitoring` roles). | Imply `base.group_user`. |
| F-28 | `ls_supplier_performance.py:446`: `self.env["stock.move"]` raises KeyError when `stock` is absent, before the guard runs. `period_end` is converted to midnight, which excludes that whole day. | Guard with `"stock.move" in self.env`; use end-of-day. |

### F-29 to F-32 — INFO
- **F-29:** `@api.constrains` methods raise `UserError` instead of `ValidationError` (for example `ls_pharma/models/product_template.py:97-152`). There are 44 `assertRaises(Exception)` in tests (ruff B017), which can hide wrong exception types.
- **F-30:** `addons/README.md` lists inter-module dependencies that the manifests do not declare.
- **F-31:** 86 `ir.rule` records write the computed field `global` (`ir_rule.py:53-56, 281`). The values match the compute. Project notes record this as an install failure, but that is **UNABLE TO CONFIRM**. Removing the field is harmless.
- **F-32:** hooks write `numbercall` "if present". It is absent in 19.0 (`ir_cron.py`, 0 occurrences), so the code is dead.

---

## 6. Stock / inventory audit

| Flow | By inspection | Runtime |
|---|---|---|
| Receipts, deliveries, internal transfers, returns, backorders, inventory adjustments, scrap | No custom code alters them; no override of stock business methods | NOT VERIFIED |
| Lots / serial numbers | Uniqueness left to standard `stock.lot`. Consistency gaps in F-16; lot form broken in F-03 | NOT VERIFIED |
| Negative stock | No custom quant writes. The OCA `stock_no_negative` is present, installed state NOT VERIFIED | NOT VERIFIED |
| Concurrency | Custom risk only through F-10, if stock models are audited | NOT VERIFIED |
| Multi-company | Custom stock reads filter by `company_id` in `ls_recall`; F-13 and F-16 apply | NOT VERIFIED |
| Quality ↔ stock coupling | Absent (F-06) | — |
| Traceability | Direct shipments only (F-07); UoM defect (F-17) | NOT VERIFIED |

About 60 OCA stock, sale and purchase modules are in the addons path. They were not reviewed line by line, because they are third-party code and their installed state is unknown.

## 7. Security audit (summary)
- **No public attack surface in the custom code:** no controllers, routes or portal access.
- **SQL injection:** all data values are parameterised. The pylint E8103 hits in `ls_signature_log.init` interpolate module constants only, so they are false positives.
- **`sudo()`:** the 104 uses are guarded. For example, `ls_change_control` checks the requester or manager before every `sudo().write`. No IDOR (Insecure Direct Object Reference) path was found, because record reads before `sudo` still enforce rules.
- **Defects:** F-01, F-03, F-11, F-14, F-21, F-26, F-27.
- **Multi-company rules:** present on every custom model with a `company_id` field, except child lines and transient wizards.

## 8. Performance audit
- **`ls_audit_trail` `base` hooks:** they add an ormcache lookup to every create/write/unlink, O(1) per call. Audited models add snapshot reads plus a chain seal, O(n) in the records written, under a per-company lock (F-10).
- **Non-stored computes on standard models:** `hr.employee` training compliance runs a per-employee requirement search (N+1 queries) but only when displayed. The other computes are counts on already-loaded relations.
- **`_ls_cron_verify_chain`:** linear in the verification window (7 days by default).
- No measurements were taken; everything in this section is **NOT VERIFIED**.

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
| Odoo install/upgrade | — | — | NOT EXECUTED |

W8301 was reviewed: the pattern `_("…%s") % x` translates correctly, so it is not a defect.

## 10. Test assessment

| Item | Status |
|---|---|
| Framework | `odoo.tests` `TransactionCase`, tagged `post_install -at_install`. `ls_qms` and `ls_document_management` carry no tag |
| Written | 2,558 test methods in 22 modules; `ls_import_export` has none |
| Executed (evidence) | 108 (`ls_cosmetics`, 2026-08-06): 0 failed, 5 errors |
| Multi-company tests | Present in 13 modules; absent in `ls_calibration`, `ls_complaint`, `ls_electronic_signature`, `ls_lab`, `ls_pharma`, `ls_qms`, `ls_recall`, `ls_supplier_qualification` |
| Permission tests | `with_user` used in 21 modules; `ls_electronic_signature` has 0 |
| Standard-form access with non-role users | Missing, which is why F-01 and F-03 went unnoticed |
| Stock workflow tests | `ls_recall` delivery tests only; no MO genealogy, returns, backorders, UoM or blocked lots |
| Concurrency / performance / upgrade / uninstall | None |

**Minimum matrix to add**

| # | Area | What to test |
|---|---|---|
| 1 | Installation | Each module alone and all together, with and without demo data |
| 2 | Upgrade | `-u` on a database with data, including the F-04 migration |
| 3 | Uninstall | Every module |
| 4 | Dependencies | Each module installs with only its declared dependencies |
| 5 | Permissions | Standard partner, PO, lot, employee, product and MO forms opened by users without any `ls_` role |
| 6 | Multi-company | Covers F-09, F-13, F-16 and F-24 |
| 7–10 | Receipts, deliveries, returns, backorders | With lots under release, OOS and recall states (F-06) |
| 11–12 | Lots and serials | Genealogy recall (F-07), UoM mix (F-17) |
| 13 | Inventory adjustments | Audited `stock.quant` |
| 14 | Cancellation | Picking and MO cancel with audit enabled |
| 15 | Partial operations | Partial delivery with trace re-run |
| 16 | Concurrency | Two pickings validated concurrently with audit on (F-10) |
| 17 | Custom workflows | Each module's full state machine |
| 18 | Security boundaries | ACL and record rules per role |
| 19 | Error conditions | Signature lockout, credential API modes |
| 20 | Data integrity | One test per constraint (F-04) |

## 11. Remediation plan

| Priority | Finding | Action | Owner type | Test required | Release blocker |
|---|---|---|---|---|---|
| P1 | F-01 | sudo-scoped computes, `groups=` on fields | Odoo developer | Non-role user opens partner and PO | Yes |
| P1 | F-02 | `groups_id` → `all_group_ids` (code, demo, tests) | Odoo developer | Signature with an implied signer group | Yes |
| P1 | F-03 | sudo before the relation read | Odoo developer | Existing test passes | Yes |
| P1 | F-04 | `models.Constraint` plus duplicate pre-migration | Odoo developer + DBA (Database Administrator) | Constraint tests, upgrade test | Yes |
| P1 | F-05 | Remove patches, pin the image | DevOps | Install `delivery` and `stock_delivery` | Yes |
| P1 | F-33, F-34, F-35 | `sudo()` on sequences, company/message access, effectiveness `partner_id` | Odoo developer | Re-run the affected suites | Yes |
| P1 | F-40, F-08 | Port test code to Odoo 19, fix fixtures, re-run all suites with coverage | QA (Quality Assurance) | All green; coverage recorded | Yes |
| P2 | F-36 to F-39, F-41 | Fix per finding; decide the F-41 ACL | Developer + process owner | Re-run the affected suites | Yes |
| P2 | F-06 | Design and implement lot blocking | Architect + stock developer | Stock regression suite | Yes for GMP use |
| P2 | F-07 | Downstream genealogy trace | Stock developer | Component → finished-lot recall | Yes for manufacturers |
| P2 | F-09 to F-17 | Code fixes listed per finding | Odoo developer | Per finding | Yes |
| P3 | F-18, F-20 | Remove dead code; restore upstream OCA | Maintainer | Re-run suites | Condition |
| P3 | F-19 | Publish lint rule set, justify disables | QA | — | Condition |
| P3 | F-21 | Harden production config | DevOps / security | Configuration review | Production only |
| P4 | F-22 to F-32 | Clean-up | Developer | Targeted | No |

After fixing, re-audit with a runtime pass: install, the full test suite and the stock matrix.

## 12. Release gate

| Area | Result | Basis |
|---|---|---|
| Odoo 19 compatibility | **FAIL** | F-02, F-04, F-05, F-33 (all confirmed at runtime except F-05). Installation itself: **PASS** for all 23 modules without demo data |
| Stock integrity | **FAIL** | F-03, F-06, F-07; runtime NOT VERIFIED |
| Security | **FAIL** | F-01, F-11, F-14 |
| Data integrity | **FAIL** | F-04, F-16 |
| Performance | **NOT VERIFIED** | No measurements |
| Testing | **FAIL** | F-08, F-40: 422 of 1,988 tests fail or error; 4 modules run no test |
| Maintainability | **PASS WITH CONDITIONS** | F-18, F-20 |
| Upgradeability | **FAIL** | F-05, F-04 migration |

## 13. Runtime test campaign (2026-09-24)

**Environment:** container `odoo19Claude_ls`, image **Odoo 19.0-20260723**, PostgreSQL 16. Command per module: `odoo -d t_<module> -i <module> --test-enable --test-tags /<module> --stop-after-init --http-port=8099 --gevent-port=8098 --log-level=test`, run by the project owner; logs in `logs/tests/`. Demo data not loaded (Odoo 19 default).

| Module | Installed | Tests run | Failed | Errors | Main cause |
|---|---|---|---|---|---|
| ls_audit | Yes | 135 | 4 | 55 | Fixture (programme not approved); **F-04** |
| ls_audit_trail | Yes | 97 | 2 | 4 | **F-38** |
| ls_calibration | Yes | 101 | 0 | 6 | Test code (`assertRaises`) |
| ls_capa | Yes | 112 | 5 | 7 | **F-04**; date fixtures; `search=` methods |
| ls_change_control | Yes | 121 | 0 | 76 | Test code (`res.groups.users`) |
| ls_complaint | Yes | **0** | 0 | 9 | Test code (`res.groups.users`) blocks every class |
| ls_cosmetics | Yes | 110 | 0 | 0 | **All pass** |
| ls_deviation | Yes | 92 | 1 | 2 | F-39; fixtures |
| ls_document_management | Yes | 101 | 1 | 4 | Folder-cycle checks; approval re-submission; default approvers |
| ls_electronic_signature | Yes | 56 | 1 | 3 | **F-02**; lockout (F-39); test code |
| ls_electronic_signature_test | Yes | **0** | 0 | 8 | Test code (`groups_id`) |
| ls_environmental_monitoring | Yes | 104 | 0 | 88 | **F-41** (86); **F-33** (2) |
| ls_import_export | Yes | 0 | 0 | 0 | No tests exist |
| ls_lab | Yes | 91 | 0 | 18 | **F-33** (14); **F-34** (3) |
| ls_medical_device | Yes | 137 | 6 | 24 | **F-34**; **F-33**; locks not enforced (5 × "UserError not raised"); fixtures |
| ls_medical_plastics | Yes | **0** | 0 | 11 | **F-33** blocks every class |
| ls_pharma | Yes | 121 | 2 | 12 | **F-33** (8); mixin model without ACL; fixtures |
| ls_qms | Yes | 115 | 0 | 3 | F-39 |
| ls_recall | Yes | 99 | 0 | 27 | **F-35** (15); **F-03**; test code |
| ls_risk_management | Yes | 161 | 2 | 3 | F-39 |
| ls_supplier_qualification | Yes | **0** | 0 | 14 | **F-36** blocks every class |
| ls_training | Yes | 146 | 8 | 2 | **F-04**; F-39 |
| ls_validation | Yes | 89 | 3 | 11 | **F-37** |
| **Total** | **23 / 23** | **1,988** | **35** | **387** | **422 failing results** |

**Earlier findings, re-checked at runtime:**
- **F-02 confirmed:** `AttributeError: 'res.users' object has no attribute 'groups_id'` at `ls_signature_meaning.py:96`.
- **F-03 confirmed:** `test_lot_indicator_readable_without_a_recall_role` fails at `stock_lot.py:56`, the line identified. The test user had no Inventory rights, so the refused model was `stock.lot`; the same compute-as-user mechanism applies to `ls.recall.execution` for inventory users.
- **F-04 confirmed:** 12 constraint tests fail with "IntegrityError not raised" or "Exception not raised": `ls_audit` 3, `ls_capa` 4, `ls_training` 5.
- **F-01 not exercised:** blocked by F-36. To check it directly: log in as a user who has only Sales / User and open any contact.
- **F-08 superseded:** replaced by the results in this section and by F-40.

## 14. Final release decision

# RELEASE BLOCKED

| Category | Items |
|---|---|
| **Defects demonstrated at runtime** | F-02, F-03, F-04, F-33, F-34, F-35, F-37, F-38, F-39 (2026-09-24 run, section 13) |
| **Defects verified by code inspection against Odoo 19.0 source** | F-01, F-02, F-03, F-04, F-05, F-11, F-12, F-14, F-15 |
| **Risks identified by inspection** | F-06, F-07, F-09, F-10, F-13, F-16, F-17, F-19, F-20, F-21, and the LOW/INFO items |
| **Areas successfully tested** | Static analysis (section 9); installation of all 23 modules; the `ls_cosmetics` suite (110/110 pass) |
| **Areas NOT VERIFIED** | Upgrade, uninstall, installation with demo data, F-01 at runtime (its test suite cannot start), standard stock workflows, multi-company at runtime, performance, the installed module set of `odooClaude_ls_DB` |

A code review cannot prove the absence of defects. This report certifies nothing, and makes no claim of regulatory compliance.
