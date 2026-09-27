# 07 — Static Analysis Report

**Phase gate: FAIL — the three required tools were not run.**

The master prompt requires the module to pass `flake8`, `pylint`,
`pylint-odoo` and XML validation with no blocking issues. Recorded honestly:

| Required tool | Status |
|---|---|
| `flake8` | **Not run.** Not installed; network disabled so it could not be installed |
| `pylint` | **Not run.** Same reason |
| `pylint-odoo` | **Not run.** Same reason |
| XML validation | **Partially performed.** Well-formedness verified with `xmllint --noout` on all 24 XML files. Validation against Odoo's RelaxNG view schema requires Odoo and was not performed |

## 7.1 What was run instead

A purpose-written AST and XML checker (`check_module.py`, delivered alongside
the module). It performs the following, all of which passed:

| Check | Result |
|---|---|
| Python syntax on all 25 `.py` files (`compileall`) | Pass |
| XML well-formedness on all 24 `.xml` files (`xmllint`) | Pass |
| Longest Python line: 85 characters against an 88 limit | Pass |
| Unused imports | None found |
| Every model and field extracted from the AST | 14 models |
| Every `<field name="">` in every view resolves against the target model, descending into one2many/many2many sub-views via the comodel | Pass |
| Every intra-module `ref=` resolves to a declared record or an auto-generated `ir.model` id | 66 references checked, all resolved |
| Every file in the manifest exists | Pass |
| Every XML file in the tree is loaded by the manifest | Pass |
| Every model in `ir.model.access.csv` is declared in Python | 29 rows, 12 models, all resolved |
| ACL CSV structure and ID uniqueness | Pass |

## 7.2 Negative control

A static checker that reports success is worthless unless it can report
failure. The checker was therefore validated by injecting two defects:

1. `<field name="days_open"/>` renamed to `days_open_typo`
2. `ref="view_ls_deviation_search"` renamed to a non-existent id

The checker reported 5 errors (2 field errors, 3 reference errors). After
reverting, it returned to a clean pass. The checker demonstrably detects the
defect classes it claims to detect.

## 7.3 What the substitute does NOT cover

`flake8` and `pylint-odoo` catch classes of issue this checker does not:

- Cyclomatic complexity and function length
- PEP 8 issues other than line length (whitespace, blank lines, naming)
- Odoo-specific lints: missing `@api.model_create_multi`, translation of field strings, `sql-injection` heuristics, missing manifest keys, deprecated method usage, `print` statements, unreachable code
- Shadowed builtins and redefined names
- Docstring conventions

Running these three tools is a mandatory action before release. The clean
result above must not be represented as equivalent to a clean `pylint-odoo`
run.

## 7.4 Deliberate design choices a linter may flag

Recorded so a reviewer does not "fix" them:

1. **`ls.deviation.stage.log.write` raises unconditionally and ignores `vals`.** This is the append-only enforcement, not a stub.
2. **`_group_expand_state` ignores both arguments.** That is the required Odoo signature.
3. **Disposition approval is checked by both ACL and `has_group`.** Intentional defence in depth, explained in `05_architecture_review.md` section 5.5.
4. **`_compute_product_uom_id` is duplicated** on two models. Accepted; see section 5.3.
