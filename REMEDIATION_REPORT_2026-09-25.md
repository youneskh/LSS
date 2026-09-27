# Life Sciences Suite — Remediation Report

**Scope:** corrective actions for the independent audit `AUDIT_REPORT_FINAL_2026-09-25.md` (revision 3, 42 active findings).
**Date:** 2026-09-25.
**Code base:** `addons/ls_*` (23 modules), Docker and Odoo configuration files, audit campaign scripts.
**Backup of the previous state:** `_backup_before_fixes_2026-09-25/before_fixes.tar.gz` (all `ls_*` modules, `base_delivery_patch`, `Dockerfile`, `docker-compose.yml`, `config/`, `patch-delivery.sh`, `requirements.txt`, `found/`, `.pylintrc`, `addons/README.md`). The complete change set is also in `_backup_before_fixes_2026-09-25/REMEDIATION_2026-09-25.patch`.

This report certifies nothing and makes no claim of regulatory compliance. It states what was changed and what was verified, and how.

---

## 1. Verification environment — read this first

The corrections were developed and verified on a separate test installation, not on the project container:

| Item | Value |
|---|---|
| Odoo | 19.0 Community, source branch `19.0`, commit `8d05257d` (2026-09-24) |
| PostgreSQL | 16.13 |
| Python | 3.11 |
| Project container (for comparison) | image `odoo:19` build 19.0-20260723, PostgreSQL 16 |

The Odoo build used for verification is two months newer than the one in the container. **Every result below must be confirmed on the project container** with the audit campaign (section 6). The baseline of the audit was reproduced first on the verification environment: 1,988 tests run, 35 failures and 387 errors, the same figures as the audit, so both environments behave the same way for the defects in scope.

---

## 2. Result summary

| Measure | Audit (before) | After remediation |
|---|---|---|
| Module test suites: tests run | 1,988 (4 suites could not start) | **2,500** (all 23 suites start) |
| Failures + errors | 422 | **0** |
| Audit probe tests (`ls_audit_probe`) | 16 of 18 finding probes reproduced a defect | **34 of 34 pass** (no probe reproduces its finding) |
| Line coverage, module suites, tests excluded | 65.9 % | **81.5 %** (24,604 statements, 4,541 not executed) |
| Cost of auditing the 4 stock models (same database, sequential) | 76 ms per picking (previous code) | 77 ms per picking |
| Concurrent validations, stock models audited (2 × 15), through the Odoo server retry | 15 of 30 fail (`UniqueViolation`, not retried; reproduced) | **30 of 30**, audit chain verifies |
| Concurrent electronic signatures (2 × 15) | 15 of 30 fail (`UniqueViolation`, reproduced) | 30 of 30, chain verifies |
| Co-installation of the 23 modules | 116 modules loaded, no error | 117 modules loaded with demo data, no demo failure |
| QWeb templates of the `ls_*` modules that compile | not checked | 70 of 70 (3 of 6 failed before in `ls_supplier_qualification` alone) |
| Upgrade from the previous code with demo data, then uninstall | 23 / 23 (2 demo reloads rejected) | 23 / 23, no error, no rejected demo reload |
| pylint-odoo, default `odoolint` rules | 1,390 messages (same tool on the previous code) | 1,284 (E8140 90 → 0, E8103 3 → 0, W8106 21 → 7) |
| pylint with the project `.pylintrc` (E8140, E8103 re-enabled) | — | 0 |
| flake8 with the project configuration | 0 | 0 |

---

## 3. Finding register — status

Status: **Fixed** (code changed and verified by a test or probe), **Fixed – deploy** (change delivered; it takes effect when the image is rebuilt or the module upgraded on the project), **Decision** (a choice was made on your behalf; it can be reversed), **Partial**, **Not done**.

| ID | Status | What was done | Verified by |
|---|---|---|---|
| F-01 | Fixed | Qualification status on contacts and purchase orders computed with `compute_sudo=True`; hidden fields carry `groups=` | Probes F-01, F-01b, F-01c; `ls_supplier_qualification/tests/test_audit_fixes.py` |
| F-02 | Fixed | `groups_id` → `all_group_ids` (code), `group_ids` (demo, tests) | Suite `ls_electronic_signature(_test)`; demo loads; test of a signer through an implied group |
| F-03 | Fixed | Lot indicators `compute_sudo=True`; relation read as superuser | Probe F-03; `ls_recall` test |
| F-04 | Fixed – deploy | 29 constraints converted to `models.Constraint` (ls_audit 10, ls_capa 6, ls_complaint 5, ls_training 8). Pre-upgrade duplicate check: `addons/F04_constraint_precheck.sql` | 12 constraint tests; upgrade from the previous code with demo data creates the constraints (section 5) |
| F-05 | Fixed – deploy | `patch-delivery.sh` and `base_delivery_patch` removed from the build and the addons path; image pinned to `odoo:19.0-20260723` (digest command in the `Dockerfile`) | `delivery` and `stock_delivery` install on an unpatched 19.0 (section 5). **The project image must be rebuilt.** |
| F-06 | Fixed / Decision | Customer deliveries refused at `stock.move.line._action_done` for: lots of a batch that is not released or cancelled (`ls_pharma`), lots held by an open OOS/OOT investigation or a reject / quarantine / further-investigation disposition (`ls_lab`), lots of an open recall other than a rehearsal (`ls_recall`). Each module owns its own rule (the modules stay independent). Only destinations of usage `customer` are blocked. | Probes F-06a, F-06b; tests in the three modules; the 16 standard stock probes still pass |
| F-07 | Fixed | Tracing follows `produce_line_ids` from the recalled lots to the lots produced from them, recursively | Probe F-07 (real manufacturing order); `ls_recall` test |
| F-09 | Fixed | Rule chosen per record company; mixed recordsets split by company | Probe F-09 (adapted, section 7); `ls_audit_trail` tests |
| F-10 | Fixed | After the chain lock the tail is also read through a fresh cursor (the REPEATABLE READ snapshot of the transaction may predate the previous commit); same change in the electronic-signature chain | `perf_concurrency.py` with the server retry: 30/30 (previous code 15/30, `UniqueViolation`). `esign_concurrency.py`: previous code 15/30 `UniqueViolation`, now 30/30; both chains verify. See section 8, item 4 |
| F-11 | Fixed – deploy | The password is a non-stored field; it is verified when the dialog is saved and only the outcome is stored (field restricted to Settings, so it cannot be used as an oracle); migration `19.0.1.1.0` drops the old column and its clear-text values | Probe F-11; `ls_electronic_signature_test/tests/test_audit_fixes.py`; upgrade runs the migration |
| F-12 | Fixed | Trigger installed inside a savepoint; DDL composed with `odoo.tools.SQL` identifiers | Install and upgrade; the failure path is not reproducible without removing privileges (as in the audit) |
| F-13 | Fixed | Dossier resolved in the order company; `@api.depends_context("company")` | Probes F-13, F-13b; tests |
| F-14 | Fixed | Folder rules use `user.all_group_ids` | Probe F-14; tests |
| F-15 | Fixed | Periodic-report status recomputed by the job before use | `ls_medical_device` test with `freezegun` |
| F-16 | Fixed | Lot/product constraints and `check_company` on 7 models (pharma batch, component, co-product; lab sample, stability study; plastics run and material line) | Probe F-16; tests |
| F-17 | Fixed / Decision | Quantities summed in the product unit; stock data read as superuser for the recall; recall viewers get read access to lots and transfers | Probe F-17; tests (coordinator without inventory rights) |
| F-18 | Fixed | Dead implementation of `ls_calibration` removed (13 Python, 14 XML, 3 test files) | Suite `ls_calibration` 101/101 |
| F-19 | Fixed | `.pylintrc`: E8140 and E8103 no longer disabled (0 messages each); every remaining suppression kept with its justification; statement that results must be published with the rule set. `ODOO_COMPLIANCE_REPORT.md`: correction notice | pylint-odoo run (section 2) |
| F-20 | Partial | The six unported `queue_job*` / `base_import_async` modules are already `installable: False` in the project folder, and none is installed in production. The OCA modules were **not** restored from upstream (see section 8) | Manifest check |
| F-21 | Fixed – deploy | `list_db = False`, `db_name` and `dbfilter` bound to `odooClaude_ls_DB` (scheduled jobs no longer run on scratch databases), database password moved to `.env`, port published on 127.0.0.1 only, health check on TCP, image pinned. `proxy_mode` stays `False` until a reverse proxy exists | Configuration review; the project must be restarted |
| F-22 | Fixed | `<chatter/>` in 9 forms | Views load; forms not opened in a browser |
| F-23 | Fixed | 86 deletion guards converted to `@api.ondelete(at_uninstall=False)`; the `unlink` override of `ls.audit_trail.rule` is kept (it is not a guard) | Suites; uninstall 23/23 |
| F-24 | Fixed | `_check_company_auto = True` on the 8 models concerned (and on the 7 models of F-16) | Probe F-24; `ls_qms` test |
| F-25 | Fixed – deploy | `/mnt/found-addons` removed from `addons_path` and from `docker-compose.yml`. The `found/` folder is left on disk; nothing in it is installed in production | — |
| F-26 | Fixed – deploy | `ls_electronic_signature_test` moved to `test_addons/`, mounted read-only at `/mnt/test-addons` for command-line test runs, not in `addons_path` | Campaign scripts updated |
| F-27 | Fixed | 19 root role groups imply `base.group_user` | Probe F-27 (adapted); 48 test errors gone |
| F-28 | Fixed | Guard when `stock` is absent; period end inclusive | Test |
| F-29 | Fixed | 66 `raise UserError` inside `@api.constrains` → `ValidationError`; the 42 `assertRaises(Exception)` replaced with the exception actually raised (recorded at runtime) | Suites |
| F-30 | Fixed | Module table of `addons/README.md` regenerated from the manifests | — |
| F-31 | Fixed | `global` removed from 86 `ir.rule` records | Install, upgrade |
| F-32 | Fixed | `numbercall` / `doall` hooks removed (`ls_cosmetics`, `ls_validation`) | Suites |
| F-35 | Fixed | `partner_id` precomputed and passed explicitly | Probe F-35; tests |
| F-36 | Fixed | `precompute=True` on 6 required computed fields; static default of the requalification interval removed (it overrode the category value) | Probe F-36; demo data loads; test |
| F-37 | Fixed | Signature mixin on `ls.validation.item`; protocol marked executed from any creation path | Suite `ls_validation` |
| F-38 | Fixed – deploy | `UNIQUE NULLS NOT DISTINCT (model_id, company_id)` (PostgreSQL 15 or later; the project runs 16) | Test; precheck query added to the SQL file |
| F-39 | Fixed | Quality plan revision fields; FMEA revision copies failure modes; approval re-submission flushes pending state changes first | Tests |
| F-40 | Fixed | Test code ported to Odoo 19 (details in each module CHANGELOG) | 0 failures, 0 errors |
| F-41 | Decision | Access rights kept as the README role table states (technicians do not author limits or plans); tests author them with a second manager; a security test pins the rule | Suite 107/107 |
| F-42 | Fixed | Refresh jobs recompute stored fields through the ORM (`add_to_compute` + `_recompute_recordset`) in `ls_training`, `ls_validation`, `ls_audit`, `ls_medical_plastics` | Tests |
| F-43 | Fixed / Decision | Author ≠ approver on 6 medical-device documents; CE submission requires regulatory authority; author content frozen at **submission**, conclusions frozen at approval (the tests' specification) | Suite `ls_medical_device` 139/139 |
| F-44 | Fixed | Demo data `noupdate="1"` in `ls_document_management` and `ls_training` | Upgrade logs |
| F-45 | Partial | Coverage 65.9 % → 81.5 %. Target 95 % reached by 5 modules (ls_calibration 96, ls_capa 99, ls_complaint 99, ls_qms 95, ls_training 97). Lowest: ls_electronic_signature 54 % alone (88 % with its test fixture module), ls_risk_management 56 %, ls_pharma 68 %, ls_environmental_monitoring 71 %, ls_import_export 77 % (no test) | `coverage.py` |

Withdrawn or superseded in the audit (F-08, F-33, F-34) and INFO items: no action beyond F-23, F-29, F-31, F-32 above.

---

## 4. Additional defects found and fixed during the remediation

These defects were hidden by the errors the audit reported (a suite that crashes in its fixture never reaches them). Each one is now covered by a test.

| # | Module | Defect (Odoo 19 behaviour) | Fix |
|---|---|---|---|
| N-01 | ls_change_control | Submitting any change request for review raised `AttributeError: 'res.groups' object has no attribute 'users'` | `all_user_ids` |
| N-02 | ls_electronic_signature | Recording a refused signature attempt raised the same error while alerting the security unit | `all_user_ids` |
| N-03 | ls_pharma | Every batch release decision failed: the digest was written through the module's own append-only guard | Stamp through the parent `write` |
| N-04 | ls_lab | An analyst entering a failing result got an access error: analysts may not create investigations, which BRU-16 opens automatically | Investigation created as superuser, analyst recorded as investigator |
| N-05 | ls_validation | Password re-authentication failed whenever `auth_totp` is installed (it is installed in production): "authentication API not recognised" | Accept the `credentials` parameter name |
| N-06 | 5 modules | QWeb reports failed to compile: `t-field` on table cells (237 occurrences) and one `t-field` without a field path | Wrapped in `<span>` / `t-out` |
| N-07 | ls_supplier_qualification, ls_environmental_monitoring, ls_validation | Odoo 19 calls field search methods with `in` / `not in`: the approved-supplier filter crashed (`ValueError`), the counter filters silently returned nothing | Operators supported or refused with `UserError` (Odoo then retries with `=`) |
| N-08 | ls_supplier_qualification, ls_complaint, ls_medical_device | Rules checked "when the state changes" did not list `state` as a trigger, so they never ran at the transition (adverse review decision without justification, complaint without product, notified body at submission) | `state` added to `@api.constrains` |
| N-09 | ls_training, ls_medical_plastics | Session capacity and reject totals declared on the parent one2many were not checked when a child line was created; a requirement without target was accepted | Checks from the child side; `course_id` added as a trigger |
| N-10 | ls_recall | A recall plan could never be revised (unique reference across versions) | Unique per version |
| N-11 | ls_supplier_qualification, ls_change_control | Second-person review and approver actions failed on record rules or on chatter/activity access | Controlled actions written with superuser rights after the role and segregation checks |
| N-12 | ls_environmental_monitoring | Monthly schedules drifted (31 Jan → 28 Feb → 28 Mar); a reviewed sample could not be returned to analysis despite the action | Anchored occurrences; transition added |
| N-13 | ls_risk_management | Control completeness could not be confirmed for a risk without control measures | Only pending measures block |
| N-14 | ls_medical_plastics | A draft (not started) run prevented sending its tool to maintenance | Draft runs ignored |
| N-15 | ls_medical_device | A draft clinical evaluation could not be created without its PMCF plan; the evaluator could approve their own evaluation; the justification for not performing a clinical investigation was never required | Rules applied from submission; author ≠ approver |

---

## 5. Installation, upgrade and uninstall

| Check | Result |
|---|---|
| Each module installed with demo data from the **previous** code, upgraded with the new code, then uninstalled | 23 / 23 upgrades without error, warning on constraints or rejected demo reload; 23 / 23 uninstalls OK |
| All 23 modules installed together with demo data (new code) | 117 modules loaded, no demo failure |
| Electronic-signature migration | `Running upgrade [19.0.1.1.0>] post-migrate` logged; the `password` column existed before the upgrade and no longer exists after it |
| Constraints after upgrading ls_audit, ls_capa, ls_complaint, ls_training, ls_audit_trail and ls_recall from the previous code with demo data | 42 of 42 declared constraints present in `pg_constraint` (none of the 29 F-04 constraints existed before); changed definitions recreated (`UNIQUE NULLS NOT DISTINCT (model_id, company_id)`, `UNIQUE (code, version, company_id)`) |
| `delivery` + `stock_delivery` on an unpatched Odoo 19.0 | Both installed without error |

Demo data of `ls_electronic_signature` (F-02) and `ls_supplier_qualification` (F-36) could not load with the previous code; those two upgrades therefore started from databases without their demo data.

---

## 6. Deployment procedure for the project

1. **Rebuild the image** (F-05): `docker compose build --no-cache odoo`. Optionally pin the digest as the `Dockerfile` explains.
2. **Check the `.env` file** (F-21). It holds the current database password so that nothing breaks; change it later with `ALTER ROLE` then in `.env`.
3. **Copy the production database** to a scratch database and, on the copy:
   1. run every query of `addons/F04_constraint_precheck.sql`; each must return 0 rows, otherwise correct the listed records;
   2. upgrade the suite and `delivery`: `odoo -c /etc/odoo/odoo.conf -d <copy> -u delivery,ls_audit,ls_audit_trail,ls_calibration,ls_capa,ls_change_control,ls_complaint,ls_cosmetics,ls_deviation,ls_document_management,ls_electronic_signature,ls_environmental_monitoring,ls_import_export,ls_lab,ls_medical_device,ls_medical_plastics,ls_pharma,ls_qms,ls_recall,ls_risk_management,ls_supplier_qualification,ls_training,ls_validation --stop-after-init`;
   3. check the log for `could not be created` / `Unable to add constraint` and for errors.
4. **Re-run the audit campaign** on scratch databases: `powershell -ExecutionPolicy Bypass -File .\audit_campaign\run_campaign.ps1`. Expected: probes 34/34, suites without failure.
5. Only then upgrade production, in a maintenance window, after a backup.
6. Restart with the new `config/odoo.conf`: the database manager is disabled and the server serves `odooClaude_ls_DB` only. Scratch databases remain usable from the command line with `-d <name>`.

---

## 7. Changes to the audit instruments

The audit probe module and scripts are test code. They were changed only where the old assertion encoded the defective behaviour:

| File | Change | Reason |
|---|---|---|
| `test_p2_permissions.py` F-01 | The "field present in the form" set-up assertion became a diagnostic log; the read that must not fail is unchanged | The fix hides the field from users without a qualification role |
| `test_p2_permissions.py` F-27 | The control now asserts that a role-only user **is** an internal user | That was the defect |
| `test_p3_multicompany.py` F-09 | Only `write` entries are counted | The fix now audits the creation of the company B record as well |
| `test_p5_misc.py` F-11 | Passes when the password column no longer exists | The fix removes the column |
| `perf_concurrency.py` | Adds a run through `odoo.service.model.retrying`, the loop the Odoo server applies to every request; reuses the rules of an earlier run | Shows the effect for users; F-38 forbids a second rule on the same model |
| New scripts | `esign_concurrency.py`, `render_reports.py`, `compile_reports.py` | Evidence for F-10 (second chain) and N-06 |
| `run_campaign.ps1`, `rerun_campaign.ps1` | `/mnt/found-addons` replaced with `/mnt/test-addons` | F-25, F-26 |

---

## 8. Not done, decisions and residual risks

1. **F-45 coverage** — 81.5 % overall; 18 modules remain below 95 %. Raising them requires new tests, mainly in ls_risk_management, ls_pharma, ls_environmental_monitoring, ls_cosmetics, ls_medical_device and ls_import_export.
2. **F-20 OCA code** — the regex edits made to about 430 OCA modules were not reverted. Restoring them from upstream changes code that runs in production (239 installed modules) and needs its own regression campaign. The exposure identified by the audit (unported modules marked 19.0) is nil today: the six modules are `installable: False`.
3. **Decisions taken on your behalf** (each can be reversed):
   - F-06: deliveries are refused for lots of a batch in any state other than released or cancelled, including planned recalls (a recall in the Planned state already holds the lot); only customer destinations are blocked. Moves into production, internal transfers and scrap are not blocked.
   - F-41: technicians do not author environmental limits and plans (README role table); the tests were changed, not the access rights.
   - F-43: content frozen at submission, conclusions at approval; technical documentation sections frozen at submission.
   - Supplier assessments are reviewed by a second assessor through the review action, although the record rules keep editing restricted to the author.
4. **F-10** — without the server retry, two users validating audited stock operations at the same moment still conflict (`SerializationFailure`, 15 of 30); the Odoo server replays such requests transparently (up to 5 attempts), at the cost of latency (2 × 15 validations: 3.9 s with auditing, 2.4 s without, same database). The same kind of conflict exists in standard Odoo stock without any audit rule (1 to 4 of 30 in the runs of this remediation). With the previous code the conflict was a `UniqueViolation`, which the server does not retry: 15 of 30 validations failed even with the retry loop.
5. **Browser checks not done** — the 9 forms converted to `<chatter/>` and the reports were not opened in a browser; the reports were compiled (70/70) and 18 of them rendered with demo data (24 have no demo record).
6. **pylint-odoo** — 1,106 W8161 (use `self.env._` rather than `_`) and 178 other messages remain under the default `odoolint` rules (W8301 and W8120 are analysed as false positives in `.pylintrc`; W8106 marks the append-only `write` guards).
7. **Cosmetic warnings** at load time (duplicate field labels, `unaccent` parameter on `parent_path`, inconsistent `compute_sudo` / `store` in `ls.validation.execution`) predate the audit and were not in its scope.
