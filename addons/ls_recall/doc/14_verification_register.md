# Verification Register

Module: `ls_recall`

---

## Purpose

Every assumption in this module that could not be verified in the
environment where it was built, and every claim the source specification
asked for that is **not** being made. This is the document to read
before deciding whether to trust anything else in the set.

The rule applied throughout: if it was not run, it is not reported as
having passed.

## A. Not verified — must be checked on a real Odoo 19 instance

| # | Item | Risk if wrong | Effort to fix |
|---|------|---------------|---------------|
| A1 | **The test suite has never run.** 99 tests are written; none executed. | Unknown. Tests may fail for reasons ranging from a typo to a design error. | Unknown until run |
| A2 | **Coverage is unmeasured.** The 95% target in the source specification is **not claimed**. | A coverage claim would be fabricated. | Run under `coverage.py` |
| A3 | **`flake8` and `pylint-odoo` never run.** Neither is installed and the shell has no network. | Style and Odoo-specific findings this analyser does not model. | Run both |
| A4 | **Installation never performed.** | The module may not install. | Install on a clean 19.0 database |
| A5 | `stock.move.line.quantity` is the correct field name on Odoo 19 (renamed from `qty_done` around Odoo 17). | Tracing returns nothing or raises. | One line in `_scan_move_lines` |
| A6 | `is_storable` exists on `product.template`. Used unconditionally in `demo/ls_recall_demo.xml`; the test fixture sets it conditionally. | Demo data fails to load on databases with demo enabled. Production installs unaffected. | One line in the demo file |
| A7 | `<menuitem groups="...">` still maps correctly after the `ir.ui.menu.groups_id` → `group_ids` rename. | Menus visible to the wrong users, or an install error. | Change the attribute |
| A8 | `res.groups.implied_ids` was not renamed. | Role inheritance breaks; security tests fail. | Rename in the security file |
| A9 | `web_ribbon` accepts `bg_color="text-bg-danger"` / `"text-bg-info"` (Bootstrap 5 naming). | Cosmetic only, or a view error. | Change the attribute |
| A10 | `activity_schedule(act_type_xmlid=...)` keeps this signature. | Scheduled actions raise. | Adjust the two call sites |
| A11 | `context_today().strftime('%Y-%m-%d')` is evaluable inside a search-filter domain. | Two saved filters fail. | Rewrite the two domains |
| A12 | `self.env._()` is available (used instead of `from odoo import _`). | Every translated message raises. | Global find and replace |
| A13 | `models.Constraint` is the correct Odoo 19 construct and the attribute name becomes the constraint name. Verified against Odoo 19 documentation, **not** by execution. | Constraints not created. | Revert to `_sql_constraints` |
| A14 | `res.groups.privilege` and `privilege_id` are correct for Odoo 19. Verified against Odoo 19 documentation, **not** by execution. | Install fails on the security file. | Revert to `category_id` |
| A15 | QWeb `web.external_layout` and `web.html_container` are unchanged. | The two PDFs fail to render. | Adjust the templates |
| A16 | The stock flow in `tests/test_traceability.py` (`_update_available_quantity`, `action_assign`, `picked`, `button_validate`) works as written on 19.0. | That file's seven tests fail although the module code is correct. | Adjust the fixture |

**A16 is the single most likely thing to need adjustment.** Run
`test_traceability.py` first, and distinguish a fixture problem from a
module problem before concluding anything about `_scan_move_lines`.

## B. Verified by execution in this environment

| # | Item | Evidence |
|---|------|----------|
| B1 | All 25 Python files compile | `python3 -m compileall` |
| B2 | All 17 XML files are well-formed | `lxml.etree.parse` on each |
| B3 | Every file in the manifest exists, and every XML file on disk is in the manifest | `static_checks.py` |
| B4 | Every view field reference resolves to a declared model field | `static_checks.py` |
| B5 | Every object button resolves to a declared method | `static_checks.py` |
| B6 | Every internal `ref`, `groups`, `parent` and `action` id resolves | `static_checks.py` |
| B7 | The ACL CSV has unique ids, known models, known groups, and covers every model | `static_checks.py` |
| B8 | No Python line exceeds 88 characters; no tabs; no trailing whitespace; no TODO/FIXME/XXX/HACK | `static_checks.py` |
| B9 | Every module, class and function has a docstring | `static_checks.py` |
| B10 | The static analyser detects faults rather than passing blindly | Negative control, 4 injected faults, 4 detections |
| B11 | The shipped icon is a valid 140×140 PNG | Header parsed and image rendered |

## C. Claims deliberately not made

| # | The source specification asks for | Position |
|---|-----------------------------------|----------|
| C1 | 95% test coverage | Not claimed. Unmeasured. |
| C2 | "Passes flake8, pylint, pylint-odoo" | Not claimed. Not run. |
| C3 | "Production ready" | Not claimed. The module is ready to enter qualification, not to be used in a regulated production environment on this evidence alone. |
| C4 | 21 CFR Part 11 electronic signatures | Not claimed and not implemented. Reasoning in `02_regulatory_analysis.md` §4. |
| C5 | ANPP compliance mapping | Not asserted. No ANPP-published recall requirement text could be verified. See `02_regulatory_analysis.md` §5. |
| C6 | Compliance with any framework | Never claimed. The module supports processes; compliance is a property of an organisation. |
| C7 | A complete `.pot` translation template | Not shipped. Must be generated by the extractor; hand-writing one would mean asserting extraction that never happened. |

## D. Regulatory citations: what was checked and how

Citations in `02_regulatory_analysis.md` were taken from the published
regulatory texts during research for this work, principally 21 CFR Part
7 Subpart C, EudraLex Volume 4 Part I Chapter 8, and Regulation (EU)
2017/745.

Two cautions:

1. **Regulations change.** Verify each citation against the current text
   before relying on it. The effectiveness check levels in 21 CFR
   7.42(b)(3) and the communication content elements in 7.49(a) are the
   two that the module's behaviour depends on most directly.
2. **Structure is not interpretation.** The module reproduces the
   *structure* these texts define — the categories, the levels, the
   lists. It does not interpret them for your product, your
   jurisdiction or your situation. That is your regulatory affairs
   function's work.

## E. Placeholders to replace before release

| Item | Current value |
|------|---------------|
| `author` in `__manifest__.py` | "Life Sciences Suite Project" |
| `website` in `__manifest__.py` | Absent |
| `development_status` | "Beta" — raise only after qualification |

## F. Recommended order of first verification

1. Install on a clean Odoo 19.0 Community database without demo data.
2. Install again on a database **with** demo data (exercises item A6).
3. Run the full suite; triage `test_traceability.py` first.
4. Measure coverage and record the real figure.
5. Run `flake8` and `pylint-odoo`; fix findings.
6. Walk one recall end to end by hand, including a closure override.
7. Upgrade the module over itself and confirm sequences did not reset.
8. Only then consider items A5 to A16 closed.
