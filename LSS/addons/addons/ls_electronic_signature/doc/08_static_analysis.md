# Phase 8 — Static Analysis

## 8.1 What was run, and what was not

**Constraint disclosed in full.** The build environment used to produce this
delivery has **no network access**. `pip install flake8 pylint pylint-odoo`
failed with "No matching distribution found". Those tools were therefore **not
executed**, and this document does not claim that they were.

What was executed:

| Check | Tool | Result |
|---|---|---|
| Python syntax and bytecode compilation | `python3 -m compileall` (stdlib) | **Pass**, 0 errors, all 30 Python files |
| XML well-formedness | `xml.etree.ElementTree` (stdlib) | **Pass**, 22 files, 0 malformed |
| CSV structure and permission values | `csv` (stdlib) | **Pass**, 21 rows, all 8 columns present, all permissions 0/1 |
| Line length ≤ 100 | `static_check.py` | **Pass**, 0 findings |
| Tabs, trailing whitespace, final newline | `static_check.py` | **Pass**, 0 findings |
| Unused imports (AST) | `static_check.py` | **Pass**, 0 findings |
| Missing docstrings, module/class/function (AST) | `static_check.py` | **Pass**, 0 findings |
| Use of `eval` | `static_check.py` | **Pass**, 0 occurrences |
| `TODO`/`FIXME`/`XXX`/`HACK` markers | `static_check.py` | **Pass**, 0 occurrences |
| Manifest data and demo files exist | `static_check.py` | **Pass** |
| Manifest mandatory keys and version format | `static_check.py` | **Pass** |
| `ir.model.access.csv` references known models | `static_check.py` | **Pass** |
| Unresolved XML external identifiers | `static_check.py` | **Pass**, 99 ids declared, 0 unresolved |

Final run: **0 findings.**

`static_check.py` is delivered at the root of the package, alongside both modules, so the result is reproducible:

```bash
python3 static_check.py
```

## 8.2 Mandatory before release

The canonical toolchain must be run in an environment that has it, and the
output attached to the validation file. This is a **release gate**, not a
recommendation.

```bash
flake8 --max-line-length=100 ls_electronic_signature ls_electronic_signature_test
pylint --load-plugins=pylint_odoo -d all -e odoolint ls_electronic_signature
xmllint --noout ls_electronic_signature/**/*.xml
```

Expected: no error-level finding. `static_check.py` covers a substantial subset
of what flake8 and pylint-odoo detect, but it is not equivalent — in particular
it does not perform type inference, cyclic import detection, or the Odoo-
specific manifest and view checks that `pylint-odoo` contributes.

## Gate

**CONDITIONAL PASS.** Every check that could be executed in this environment
passes with zero findings. The canonical toolchain could not be installed and
must be run before release. Stating this plainly is required: reporting a
flake8 pass that never happened would itself be a data integrity failure of
exactly the kind this module exists to prevent.
