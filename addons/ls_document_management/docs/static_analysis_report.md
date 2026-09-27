# Static Analysis Report

Module: `ls_document_management` — Odoo 19 Community. Phase 8 deliverable.

---

## 1. Honest statement of tooling

The environment in which this module was produced had **no network access and
no Odoo runtime installed**. As a direct consequence:

- `flake8`, `pylint`, `pylint-odoo` and Odoo's own XML schema validation
  **could not be run**, because they are not present offline and could not be
  installed.
- Any claim that the module "passes pylint-odoo with no errors" would be
  **fabricated**. This report does not make that claim.

What was possible was a **custom static self-check** implemented with the
Python standard library and `lxml` (both available offline). Its purpose is to
catch the classes of error that do not require an Odoo runtime. Its output is
reproduced in `static_check_output.txt` and summarised below. This check is a
useful gate but is **not equivalent** to `pylint-odoo` or to installing the
module.

## 2. What the self-check verifies

| # | Check | Method |
|---|-------|--------|
| 1 | Python compiles | `py_compile` on all 22 Python files. |
| 2 | XML well-formed | `lxml.etree.parse` on all 16 XML files. |
| 3 | Manifest/file consistency | Every `data`/`demo` entry exists on disk; version targets `19`. |
| 4 | XML-id inventory | Records, templates, menus and implicit `model_*` ids collected. |
| 5 | XML cross-references | Every `ref`, `parent`, `action`, `groups` and `eval` `ref(...)` resolves to a known id (external `base.`/`web.`/`mail.` prefixes excluded). |
| 6 | Python -> XML references | Every `"ls_document_management.<id>"` string in Python resolves. |
| 7 | Access-rights integrity | No duplicate ACL ids; every model and group referenced exists; every model with a `_name` has an ACL row; permissions are 0/1. |
| 8 | Deprecated constructs | Absence of `<tree>`, `oe_chatter`, `attrs=`, `states={`, `numbercall`, `doall`, `<kanban-box>`, `name_get()`, `groups_id`, `res.groups.category_id`, `tree` view mode (all removed/renamed in Odoo 17-19). XML comments excluded from this scan. |
| 9 | Docstring coverage | Every module (except `__init__`/manifest), class and function has a docstring. |
| 10 | Placeholders | No `TODO`, `FIXME`, `XXX`, `pass  #`, `NotImplementedError`. |
| 11 | Line length | No Python line exceeds 88 characters. |

## 3. Result

```
python_files             22
xml_files                16
declared_data_files      17
xml_ids                  72
models                    9
acl_rows                 26
missing_docstrings        0
long_python_lines         0
------------------------------------------------------------------------
RESULT: PASS - no blocking issue detected by the static checks
```

Additional targeted cross-checks performed manually and passing:

- All 14 object-action buttons in views map to defined methods.
- The `ir.actions.report` `report_name` points at a template that exists.
- No stale `groups_id`; group records use `privilege_id`; user records and
  record rules use `group_ids` / `user.group_ids` (Odoo 19 spelling).
- All four folder-scoped record-rule domains are bracket-balanced.

## 4. What this report does NOT establish

- It does **not** establish that the module installs in Odoo 19. That requires
  running Odoo.
- It does **not** run the 101-method test suite. That requires an Odoo test
  database.
- It does **not** replace `pylint-odoo`, which enforces Odoo-specific lint
  rules (e.g. manifest keys, translatable strings, SQL-injection heuristics)
  beyond what the self-check inspects.

## 5. Recommended commands to close the gap in a real environment

```bash
# Lint
pip install pylint-odoo flake8
flake8 ls_document_management
pylint --load-plugins=pylint_odoo -d all -e odoolint ls_document_management

# Install + tests
odoo -d testdb -i ls_document_management --test-enable --stop-after-init
```

**Phase 8 result: PASS for the checks that are possible offline; the
runtime-dependent checks are explicitly deferred and listed above.**
