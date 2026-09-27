# Phase 8 — Static Analysis Report

## 8.1 What was and was not run

| Tool | Status | Reason |
|---|---|---|
| `python3 -m py_compile` | Run on every Python file | — |
| `lxml.etree.parse` | Run on every XML file | — |
| `ls_pharma/static_check.py` | Run, 0 findings | Written for this module |
| `flake8` | **Not run** | No network access to install it |
| `pylint` | **Not run** | Same |
| `pylint-odoo` | **Not run** | Same |
| `xmllint` | Not run separately | `lxml` performs the same well-formedness parse |

The framework requires that the module pass `flake8`, `pylint` and
`pylint-odoo`. **That requirement is not met and is not represented as met.**
The custom checker covers part of what those tools cover and some things they
do not, but it is not a substitute for them.

## 8.2 What the custom checker verifies

| # | Check |
|---|---|
| 1 | Every `<field name="...">` in a view names a field that exists on the model it belongs to, following one-to-many and many-to-many fields into their target model |
| 2 | Every `<button type="object" name="...">` names a method that exists on the model |
| 3 | Every `ref=`, every `ref()` inside `eval=`, and every `groups=` resolves inside the module or names a declared dependency |
| 4 | Every XML identifier is declared exactly once |
| 5 | Every file declared in the manifest exists, and every XML and CSV file in the module is declared |
| 6 | Every model named in the access file exists, and every persistent model of the module appears there |
| 7 | The first term of every domain, every `group_by` and every date filter names a real field |
| 8 | No source file contains a placeholder token |
| 9 | No shipped file executes raw SQL |
| 10 | Line length, trailing whitespace, tab indentation and final newline |
| 11 | The manifest declares a name, a version, a licence, an author, dependencies and data, and the version is an Odoo 19 version |
| 12 | The icon named by the root menu exists |

## 8.3 Negative controls

A checker that has never failed proves nothing. Before its output was
trusted, fifteen faults were injected into a copy of the module and the
checker was required to detect each one.

| # | Injected fault | Detected |
|---|---|---|
| 1 | A field name misspelt in a list view | Yes |
| 2 | A field name misspelt inside a nested one-to-many sub-view | Yes |
| 3 | A button naming a method that does not exist | Yes |
| 4 | A menu pointing at an action that does not exist | Yes |
| 5 | Two records sharing one XML identifier | Yes |
| 6 | A `groups=` attribute naming a module that is not a dependency | Yes, after the checker was extended |
| 7 | A domain naming a field that does not exist | Yes |
| 8 | A `group_by` naming a field that does not exist | Yes |
| 9 | An access rule row removed for one model | Yes |
| 10 | A data file removed from the manifest | Yes |
| 11 | A `TODO` comment | Yes |
| 12 | A raw SQL call | Yes |
| 13 | A line over the length limit | Yes |
| 14 | Trailing whitespace | Yes |
| 15 | A missing menu icon | Yes, after the checker was extended |

The first run detected fourteen of fifteen. The undetected fault, number 6,
led to a `groups=` scan being added, and the icon check was added at the same
time. The suite was then re-run and all fifteen were detected. Two false
positives were also found and corrected: the checker had been flagging the
legitimate `placeholder="..."` view attribute as a placeholder token, and had
been flagging citation URLs that cannot be wrapped as over-length lines.

## 8.4 Findings on the module itself

Final run: **0 findings.**

Findings raised and fixed during the phase:

| Finding | Fix |
|---|---|
| A double hyphen inside an XML comment made `security/ls_pharma_record_rules.xml` unparseable, which would have aborted installation | The comment was rewritten |
| Three code lines exceeded the length limit | Reformatted |
| `demo/ls_pharma_demo.xml` was declared in the manifest but did not exist | The file was written |

The first of these is the clearest justification for the checker: an
unparseable security file is an installation failure, and it was invisible to
`py_compile`.

## 8.5 What the checker cannot verify

- That an external identifier such as `web.external_layout` exists in the
  target Odoo build. It can only confirm that the module naming it declares
  the owning module as a dependency.
- That a selection value used in a view expression is valid.
- That a Python expression inside `invisible`, `readonly` or `required`
  evaluates correctly.
- Anything that depends on the runtime: SQL performance, migration behaviour,
  view inheritance resolution or report rendering.

## 8.6 Re-running

```bash
python3 ls_pharma/static_check.py ls_pharma
```

The checker ships inside the module so that it can be re-run after any local
modification. It excludes its own source from the placeholder and raw SQL
scans, because it necessarily contains those tokens.

## Gate verdict

**CONDITIONAL PASS.** The custom analysis is clean and is itself validated.
The gate is conditional because the three tools named by the framework were
not run, which the receiving team must do before qualification.
