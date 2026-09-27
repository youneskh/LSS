# Phase 8 — Static Analysis Report

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Tools that could not be run

The build environment has no network access, therefore `flake8`, `pylint`,
`pylint-odoo`, `black`, `isort` and the OCA pre-commit hooks could not be
installed. **The module has not been passed through those tools.** This must
be done in an environment where they can be installed, before the module is
declared production ready.

Expected command in the target environment:

```
pip install flake8 pylint pylint-odoo
flake8 --max-line-length=88 ls_calibration
pylint --load-plugins=pylint_odoo -e odoolint ls_calibration
```

## 2. Tool that was run

`tools/static_analysis.py`, written for this purpose, reproduces the subset of
those checks that the Python standard library and `lxml` allow.

| Check | Equivalent | Implemented |
|-------|------------|-------------|
| Python syntax | pyflakes | Yes, `ast.parse` |
| Unused imports | F401 | Yes |
| Missing docstring | C0116 | Yes, on every class and method |
| Line length above 88 | E501 | Yes, Python sources only |
| Trailing whitespace | W291 | Yes |
| Tabulation | W191 | Yes |
| Missing newline at end of file | W292 | Yes |
| Commented-out code | pylint-odoo | Yes, heuristic on the common patterns |
| TODO, FIXME, XXX | manifest of the framework | Yes |
| `_sql_constraints` | Odoo 19 removal | Yes |
| `<tree>`, `attrs=`, `states=` | Odoo 17 and 18 removals | Yes |
| `t-esc`, `t-raw` | QWeb deprecation and XSS | Yes |
| `oe_chatter` | Odoo 18 replacement | Yes |
| `tree,form` in `view_mode` | Odoo 18 rename | Yes |
| `from odoo import _` | Odoo 19 translation API | Yes |
| XML well-formedness | xmllint | Yes, `lxml` |
| Files declared in the manifest exist | pylint-odoo | Yes |
| XML identifiers resolve | pylint-odoo | Yes, internal references |
| Access rights consistent with the models | pylint-odoo | Yes, including the detection of a model without access rights |
| Cyclomatic complexity | R0912 | No |
| Naming conventions | C0103 | No |
| Import ordering | isort | No |
| XML formatting | prettier-xml | No |

## 3. Result

```
Module: ls_calibration
Python files: 22
XML files: 14
Models: 8

ERRORS (0)
RESULT: PASS
```

No error and no warning. In particular:

* No file declared in the manifest is missing.
* Every internal XML identifier referenced by `ref`, `parent`, `action` or
  `search_view_id` resolves.
* The 21 access rules reference existing models and existing groups; no model
  of the module is left without access rights.
* No deprecated Odoo construct is present.
* No placeholder, no commented-out code, no method without a docstring.

## 4. Findings corrected during this phase

| # | Finding | Correction |
|---|---------|------------|
| SA-01 | The analysis script itself was inside the module and matched its own forbidden-marker patterns | Moved to `tools/`, outside the module |
| SA-02 | The line-length check flagged the XML and CSV files, where an 88-character limit does not apply | Restricted to the Python sources |
| SA-03 | Six lines of `test_constraints.py` exceeded 88 characters after a refactoring | Extracted into a module level constant |
| SA-04 | `<field name="global" eval="True"/>` on the record rules; in modern Odoo that field is computed from the absence of groups and is not settable | Removed; a rule attached to no group is global by construction |
| SA-05 | `test_cron.py` ended with a malformed conditional expression | Rewritten |
| SA-06 | Unused `fields` import in `test_cron.py` and `test_instrument.py` after refactoring | Removed |

## Gate

**Phase 8: CONDITIONAL PASS.** The implemented analysis reports zero error
and zero warning, and six findings were corrected. The gate cannot be closed
as a full pass because flake8, pylint and pylint-odoo could not be run.
Required action before closure: run those three tools in the target
environment and record their output in this document.
