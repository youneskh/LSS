# Phase 8 — Static Analysis Report

## 1. Required tools versus available tools

The assignment requires the module to pass `flake8`, `pylint`, `pylint-odoo`
and XML validation.

| Tool | Available | Executed |
|---|---|---|
| `flake8` | **No** — not installed, network disabled, cannot be installed | No |
| `pylint` | **No** — same | No |
| `pylint-odoo` | **No** — same | No |
| XML validation | Yes (`xml.dom.minidom`, `ElementTree`, `xmllint`) | **Yes** |
| Python compilation | Yes (`compileall`) | **Yes** |

**Three of the four required tools could not be executed.** Rather than claim a
pass that was never obtained, a substitute checker was written and run. Both
scripts are delivered in `tools/`, so that the result below can be reproduced.

## 2. Substitute checker

Two scripts were executed against the module:

`static_check.py`
- Python compilation of every `.py` file
- line length ≤ 88, no tab characters, no trailing whitespace
- absence of `TODO`, `FIXME`, `XXX`, `pdb.set_trace`
- manifest: every declared file exists, every file is declared, required keys present, version targets Odoo 19
- every `ref=` and `groups=` resolves to an identifier of this module or of a declared dependency
- every ACL row targets a declared model and an existing group; every model has at least one ACL row; no duplicate ACL identifier
- every `<field name="…">` in every view exists on the target model
- every `type="object"` button targets an existing method

`extra_check.py`
- absence of APIs removed in recent Odoo versions: `attrs=`, `states="…"`, `<tree>`, `oe_chatter`, `name_get`, `ir.cron.numbercall`, `stock.production.lot`, `@api.model` on a `create` override
- no duplicate XML identifier across the module
- every `t-field` expression in the report template resolves to a real field

## 3. Result

```
static_check.py
models declared : 7
xml identifiers : 159
errors          : 0
warnings        : 0

extra_check.py
xml ids checked : 69
errors          : 0
```

Three defects were found and fixed during Phase 8:

| # | Defect | Fix |
|---|---|---|
| 1 | Two lines exceeded 88 characters after an edit that inserted a literal `\n` into a help string | Help strings rewritten with implicit string concatenation |
| 2 | Two `write()` overrides had an over-long inline set literal | Extracted to a named `tracked` set |
| 3 | The `group_operator` attribute on the KPI measure is version-sensitive | Removed; documented as R-07 |

## 4. What this does not prove

The substitute checker does not implement: cyclomatic complexity limits,
unused-import and unused-variable detection with full scope analysis, naming
conventions beyond the ones checked, the `pylint-odoo` catalogue of Odoo-specific
messages (manifest key completeness against the OCA list, deprecated field
attributes, missing `_description`, translation function misuse, and others).

The module was written to satisfy those rules — every model has `_description`,
every user-facing string uses `_()`, imports are minimal and used — but **that
is a statement of intent, not a measurement**.

## 5. How to obtain the missing evidence

```bash
pip install flake8 pylint pylint-odoo
flake8 --max-line-length=88 path/to/ls_complaint
pylint --load-plugins=pylint_odoo -d all -e odoolint path/to/ls_complaint
xmllint --noout path/to/ls_complaint/**/*.xml
```

## Phase 8 gate

**CONDITIONAL PASS.**

- XML validation: **PASS**, executed.
- Python compilation and the substitute checks: **PASS**, executed, zero errors,
  zero warnings.
- `flake8`, `pylint`, `pylint-odoo`: **NOT EXECUTED** — unavailable offline.
  This is a genuine gap against the assignment.

The corrective action is section 5.
