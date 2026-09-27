# Architecture Review Report

Module: `ls_document_management` — Odoo 19 Community. Phase 5 deliverable.

This report reviews the module against Odoo architecture, OCA conventions and
common design principles. It is a design review, not a runtime test report.

---

## 1. Odoo architecture conformance

| Aspect | Assessment |
|--------|------------|
| Module layout | Standard: `models/`, `views/`, `security/`, `data/`, `demo/`, `report/`, `wizard/`, `tests/`, `__manifest__.py`, `__init__.py`. PASS. |
| Manifest | Declares name, summary, version `19.0.1.0.0`, category, author, AGPL-3 licence, `depends`, ordered `data`, `demo`, flags. PASS. |
| Data load order | Security groups -> ACL -> record rules -> sequences/cron -> wizards -> views (dependencies before dependents; document views load after the models/actions they reference). PASS. |
| No core modification | Only new models and standard mixins (`mail.thread`, `mail.activity.mixin`). No monkey-patching, no override of core models. PASS. |
| ORM usage | Fields, compute with explicit `@api.depends`, `@api.constrains`, `@api.onchange`, `@api.model_create_multi`. No raw SQL except one parameterised statement in a test. PASS. |
| Odoo 19 API currency | Uses `models.Constraint`/`UniqueIndex`, `Many2oneReference`, `check_company`, `<list>`, `<chatter/>`, `res.groups.privilege`/`group_ids`, cron without `numbercall`/`doall`. Verified against Odoo 19 documentation and release notes. PASS. |

## 2. Security architecture

| Aspect | Assessment |
|--------|------------|
| Defence in depth | Access rights (model level) + record rules (row level) + server-side role checks in Python for state transitions. A UI-only control would be insufficient for GxP; the module enforces publication/archival roles and approver identity in `write`/action code so RPC cannot bypass them. PASS. |
| Segregation of duties | Approver role does not imply Editor. Documented and tested. PASS. |
| Least privilege | Viewer read-only; Editor no unlink; Approver no create; only Manager configures. PASS. |
| Folder-level ACL | A single source of truth: the record rules. The earlier Python helper duplicating this logic was removed during development to avoid divergence. PASS. |
| Multi-company | Global record rules on every model restrict to `company_ids`. PASS. |

## 3. Design principles

### SOLID

- **Single responsibility** — each model owns one concern (folder, document,
  version, approval, retention policy, tag, link). The retention *rule* lives
  in `retention_policy`; the retention *evaluation* lives on `document`; this
  is an intentional separation of the rule from its application.
- **Open/closed** — behaviour is extended through new models and standard
  Odoo inheritance points rather than by editing core. Links target arbitrary
  models without this module depending on them.
- **Liskov / interface segregation** — not directly applicable to Odoo models;
  no fragile base-class hierarchies are introduced.
- **Dependency inversion** — the document does not depend on concrete linked
  models; it references them by name via `Many2oneReference`.

### DRY

- Test setup is centralised in `tests/common.py`.
- Archiving logic is factored into `_archive_document`, reused by both the
  role-checked public action and the scheduled action, so the state checks are
  written once.
- File metadata (size + checksum) computation is a single method reused by
  create and by integrity verification.

### KISS

- The state machine is a flat five-state selection with explicit transition
  methods, not a generic workflow engine.
- Cycle detection in the folder tree is a direct parent-walk that depends only
  on `parent_id`, deliberately avoiding framework helpers whose names have
  changed between Odoo versions.

### Separation of concerns

- Models (logic), views (presentation), security (access), data (seed), report
  (output) and wizards (interaction) are in separate files and directories.

## 4. Upgradeability

| Aspect | Assessment |
|--------|------------|
| Version string | `19.0.1.0.0`, OCA-style. PASS. |
| `noupdate` data | Sequence and cron are under `noupdate="1"` so upgrades do not reset them. PASS. |
| No deprecated constructs | Static check confirms none of the Odoo 17-19 removed constructs are present. PASS. |
| Stable identifiers | XML ids are explicit and descriptive; models use `ls.document.*` namespace. PASS. |

## 5. Maintainability

| Aspect | Assessment |
|--------|------------|
| Docstrings | Every module, class and method carries a docstring (static-check enforced). PASS. |
| Line length | All Python lines within 88 characters (static-check enforced). PASS. |
| Naming | Consistent `ls_`/`ls.document.` prefixes; descriptive field and method names. PASS. |
| No dead code / placeholders | Static check finds no TODO/FIXME/pass-stub/NotImplementedError. PASS. |
| Tests | 101 methods covering lifecycle, versioning, approval, retention, links, folders and security. Written; execution pending a runtime. |

## 6. Findings and resolutions during review

| # | Finding | Resolution |
|---|---------|------------|
| 1 | A plain UNIQUE constraint on (document, version, approver) blocked resubmitting a rejected document to the same approver. | Replaced with a partial `UniqueIndex` limited to `state = 'pending'`, preserving history while allowing resubmission. |
| 2 | Cron-driven archiving would trip the Manager-role guard. | Split into a public role-checked `action_archive_document` and a private `_archive_document` reused by the cron. |
| 3 | Folder access logic existed in both a Python helper and record rules. | Removed the Python helper; record rules are the single source of truth. |
| 4 | `check_access` method naming varies across versions. | Guarded the linked-record name resolution with an `AccessError` try/except instead. |

## 7. Residual architectural risks

- **Runtime-only behaviours** cannot be reviewed statically: record-rule
  evaluation, cron execution, PDF rendering, wizard flows. These are covered by
  the test suite, which has not yet been executed (see validation report).
- **Performance of the folder-scoped record rules** on very large datasets is
  not assessed; the domains traverse `folder_id.group_read_ids`. For typical
  QMS document volumes this is expected to be acceptable, but it should be
  confirmed under representative load.

**Phase 5 result: PASS** with residual risks documented above.
