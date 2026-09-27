# Phase 8 — Static Analysis Report

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS for the checks that could be executed;
three standard linters NOT executed — see §8.1**

---

## 8.1 What could and could not be run

The build environment had Python 3.12 and `lxml`, no network access, and no
Odoo installation. `pip install` was therefore impossible.

| Tool | Executed | Result |
|------|----------|--------|
| `python -m py_compile` | Yes | Pass on all 39 Python files |
| `lxml.etree.parse` | Yes | Pass on all 31 XML files |
| `tools/static_check.py` (written for this module) | Yes | **PASS, 0 findings** |
| `flake8` | **No** — not installed, no network | Not run |
| `pylint` | **No** — same | Not run |
| `pylint-odoo` | **No** — same | Not run |
| Odoo's own XML/view validation at install | **No** — no Odoo instance | Not run |

The module therefore **cannot be declared "lint-clean"**. It can be declared
free of the defect classes listed in §8.3, which were checked mechanically.
§8.5 gives the commands to close the gap.

## 8.2 The offline checker

`tools/static_check.py` was written for this module. It runs in under a second
and needs only Python and `lxml`. It is shipped with the module so that the
same checks can be repeated by anyone.

```bash
python3 tools/static_check.py .
```

Exit code 0 and `STATIC CHECK: PASS` mean no finding. Any finding is printed
with its file, line and description, and the exit code is 1, so the script fits
a CI pipeline directly.

## 8.3 Checks performed and results

| # | Check | Scope | Result |
|---|-------|-------|--------|
| 1 | Line length at most 88 characters | 39 Python files | 0 violations |
| 2 | No trailing whitespace | 39 files | 0 |
| 3 | No tab characters | 39 files | 0 |
| 4 | No `TODO`, `FIXME`, `XXX`, `HACK` | 39 files | 0 |
| 5 | No vague wording (`etc.`, `and more`, `miscellaneous`, `similar features`) | 39 files | 0 |
| 6 | Module docstring present | all except `__init__.py` and `__manifest__.py` | 0 missing |
| 7 | Class docstring present | every class | 0 missing |
| 8 | Function and method docstring present | every function | 0 missing |
| 9 | No bare `except:` | 39 files | 0 |
| 10 | Every class declaring `_name` also declares `_description` | 18 model classes | 0 missing |
| 11 | XML well-formedness | 31 files | 0 errors |
| 12 | Every declared model has an access line | 16 models with `_name` | 0 uncovered |
| 13 | No access line references an undeclared model | 44 CSV rows | 0 |
| 14 | Permission columns are 0 or 1 | 44 rows × 4 columns | 0 invalid |
| 15 | Every file listed in the manifest exists | 32 data entries, 1 demo, 1 image | 0 missing |
| 16 | Every module-local external identifier used from Python is defined in XML | all `ls_supplier_qualification.*` literals | 0 unresolved |
| 17 | No deprecated `<tree>` tag | 31 XML files | 0 |
| 18 | No `view_mode` containing `tree` | 16 window actions | 0 |

Checks 12 to 18 are the ones that catch the errors an ordinary linter does not:
a model shipped without access rights, a smart button pointing at an action
that was renamed, or a view left on pre-Odoo-18 syntax.

## 8.4 Defect classes verified by inspection

These were confirmed by reading the code and by targeted searches rather than
by a tool, and are recorded here so a reviewer can re-check them quickly.

| Class | Finding |
|-------|---------|
| SQL injection | One raw SQL statement in the whole delivery, in `tests/test_signature.py`, and it is parameterised. No `execute` in module code. |
| XSS | No `t-raw` in any QWeb template. The only HTML field is declared `sanitize=True`. |
| Unbounded `sudo()` | Two uses, both in `ls.supplier.signature`, on a model no group can write to. |
| Mutable default arguments | None. Optional dicts default to `None` and are copied. |
| Hard-coded credentials or secrets | None. |
| Print statements and debugger calls | None. |
| Unreachable or dead code | None found; every method is reachable from a view, a cron, a wizard or a test. |
| Circular imports | None. `models/__init__.py` orders imports so that referenced modules load first. |
| Deprecated Odoo API | No `@api.one`, no `@api.multi`, no `@api.returns`, no `fields.Datetime.now()` misuse. `_read_group` uses the current signature. |

## 8.5 Closing the gap

Run these on a machine that has the packages, and attach the output to the
validation package.

```bash
pip install flake8 pylint pylint-odoo

flake8 --max-line-length=88 ls_supplier_qualification/

pylint --load-plugins=pylint_odoo \
       --disable=all \
       --enable=odoolint \
       ls_supplier_qualification/
```

Expected disagreements with the shipped code, and what to do about them:

| Likely message | Assessment |
|----------------|------------|
| `manifest-required-author` | `pylint-odoo` expects an OCA author string. Adjust the manifest if you publish through the OCA. |
| `no-utf8-coding-comment` / `use-vim-comment` | Obsolete checks in some plugin versions. Ignore. |
| `translation-field` on selection labels | Selection labels are translated by Odoo itself. Ignore. |
| Complexity warnings on `_compute_risk_level` or `_apply_decision` | Both are flat sequences of explicit branches, written that way so a validation reviewer can read the rule. Keep, or document the deviation. |

If `flake8` reports anything, it should be whitespace or import ordering, not
logic: line length, tabs and trailing whitespace were already checked here.

## 8.6 Continuous integration

Minimal pipeline that reproduces this phase and closes it:

```yaml
- python3 tools/static_check.py .                 # this phase, no dependencies
- flake8 --max-line-length=88 .                   # §8.5
- pylint --load-plugins=pylint_odoo .             # §8.5
- odoo-bin -d ci -i ls_supplier_qualification \
      --test-enable --test-tags /ls_supplier_qualification \
      --stop-after-init                           # Phase 7
```

The first step needs only Python and `lxml`, so it can run on any runner and
fails fast.

---

**Phase 8 gate: PASS for the executed checks, with a recorded gap.**
18 mechanical checks over 39 Python and 31 XML files, 0 findings. Nine defect
classes verified by inspection. `flake8`, `pylint` and `pylint-odoo` were not
run and no claim is made about them; §8.5 must be executed before release.
Phase 9 may start.
