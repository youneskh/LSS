# 10 — Validation Report

**Verdict: the module is NOT validated, and is NOT production-ready.**

This document exists to say precisely what was verified, by what method, with
what evidence, and what remains unverified. It is a verification record, not a
validation certificate.

---

## 1. Scope and limits of this report

| | |
|---|---|
| **Module** | `ls_audit` 19.0.1.0.0 |
| **Date** | 24 July 2026 |
| **Environment** | Python 3.12.3, lxml 6.0.2. **No Odoo installation. No network.** |
| **Method** | Static analysis only |
| **Executed** | Nothing. No test has run. The module has never been installed |

### 1.1 Why this is not validation

Computer system validation establishes documented evidence that a system
consistently performs as intended. That requires the system to be **run**.
No part of this module has been run.

What follows is *verification* — evidence that the artefact is internally
consistent and structurally correct. It is a necessary precondition for
validation and no substitute for it.

---

## 2. Verification performed

Tool: `validate_module.py`, shipped alongside the module. Deterministic and
repeatable.

| # | Check | Method | Result | Evidence |
|---|---|---|---|---|
| V1 | Python syntax | `ast.parse` on 30 files | PASS | No syntax error |
| V2 | Docstring coverage | AST walk, all classes and functions | PASS | 254/254 documented |
| V3 | Forbidden markers | Line scan for TODO, FIXME, XXX | PASS | None |
| V4 | XML well-formedness | `lxml.etree.parse` on 24 files | PASS | 130 records parsed |
| V5 | Manifest coherence | Literal eval; two-way file comparison | PASS | 25 declared, none missing, none undeclared |
| V6 | XML id resolution | All `ref=`, `groups=`, `parent=`, `action=`, and `ref()` inside `eval` | PASS | All resolve |
| V7 | ACL integrity | Header, column count, model and group refs, duplicates, coverage | PASS | 37 rules, 14/14 models covered |
| V8 | PEP 8 subset | Length, tabs, trailing space, final newline, CRLF | PASS | 79-char limit |
| V9 | Odoo 19 regressions | `<tree>`, `attrs=`, `states=`, `res.groups.category_id`, `ir.rule.global` writes, `res.users.groups_id` | PASS | None present |

**Overall: PASS**, within the stated limits.

---

## 3. Defects found and corrected

Recorded because a verification report that found nothing would be suspect.

| # | Defect | Severity | Correction |
|---|---|---|---|
| D1 | 18 explicit writes to `ir.rule.global` | **Blocking** — `global` is computed from `groups`; the module would have failed to install | Removed; rules are global by carrying no group. Test asserts `not rule.groups` |
| D2 | 3 lines exceeding 79 characters | Minor | Refactored |
| D3 | `ls.audit.auditor._order` used the non-stored `display_name` | Blocking at query time | Changed to `user_id` |
| D4 | Qualification cron filtered on a stale stored date-dependent field | Functional — expiries would be missed | Recompute before filtering |
| D5 | `_search_is_overdue` carried `@api.model` | Blocking — wrong signature | Decorator removed |
| D6 | Redundant `copy_data` override | Dead code | Removed |
| D7 | Version-uncertain ORM recursion helper | Blocking risk | Replaced with an explicit ancestor walk |
| D8 | 4 dead fields | Dead code | Removed |
| D9 | `_order` on the `severity` Selection sorted alphabetically, not by severity | Functional | Ordered on `category_id`, which resolves through the category's own sequence |

---

## 4. What remains UNVERIFIED

This is the operative section.

| # | Unverified | Risk | Only resolvable by |
|---|---|---|---|
| U1 | **The module installs** | High | Installing it |
| U2 | **Any test passes** | High | Running the suite |
| U3 | Every constraint fires at runtime | High | Running the suite |
| U4 | Record rules isolate as intended | High | Running the suite |
| U5 | Views render | Medium | Opening them |
| U6 | `invisible`/`readonly` expressions evaluate | Medium | Opening them |
| U7 | QWeb PDFs render | Medium | Printing |
| U8 | Mail templates render | Medium | Triggering them |
| U9 | Scheduled actions run under a cron user | Medium | Running them |
| U10 | Demo data loads | Medium | Installing with demo |
| U11 | Sequences allocate correctly | Low | Running the suite |
| U12 | Upgrade preserves data | Medium | A second version |
| U13 | Performance at volume | Low | Load testing |
| U14 | flake8, pylint, pylint-odoo pass | Low | Installing those tools |
| U15 | Multi-company isolation across companies | Medium | Running the suite |

`validate_module.py` reimplements a subset of the flake8 and pylint-odoo
checks that matter most for installability. It is not equivalent to them.

---

## 5. Residual risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RR1 | Runtime defect in an untested path | **High** | High | Execute the suite before any use |
| RR2 | An Odoo 19 API assumption is wrong on a specific point release | Medium | High | Version-sensitive decisions are documented at their call sites; the harness checks known regressions |
| RR3 | Approvals mistaken for Part 11 signatures | Medium | **High — regulatory** | Disclaimer in the PDF signature block, README, and `02_regulatory_analysis.md` §4 |
| RR4 | Module deployed without qualification | Medium | **High — regulatory** | This document; the compliance checklist |
| RR5 | `capa_reference` drifts from the real CAPA system | Medium | Medium | Documented gap; bridge module required |
| RR6 | Second company starts with no configuration | Medium | Low | Documented in the configuration guide |
| RR7 | Impartiality constraints block a small site | Medium | Medium | Area granularity and optional area ownership are documented levers |

---

## 6. Required work before regulated use

Nothing in this section is optional.

### 6.1 Execution

1. Install on a clean Odoo 19 Community database.
2. Run the suite with `coverage`. Fix every failure.
3. Reissue `09_test_report.md` with real numbers.
4. Install flake8, pylint and pylint-odoo and resolve findings.

### 6.2 Qualification

5. Write a Validation Plan defining scope and acceptance criteria.
6. Write a User Requirements Specification. This module's documentation is a
   functional specification, not a URS — a URS states what *your organisation*
   requires.
7. Perform Installation Qualification.
8. Perform Operational Qualification against the controls in
   `02_regulatory_analysis.md` §3.
9. Perform Performance Qualification with your own data and users.
10. Write the SOPs that govern use. **The software encodes a workflow; it does
    not encode your procedure.**
11. Train users and record it.
12. Issue a Validation Summary Report.

### 6.3 Regulatory

13. Decide whether 21 CFR Part 11 electronic signatures are required. If so,
    this module is **not sufficient** — see `02_regulatory_analysis.md` §4.2.
14. Confirm the current status of the FDA QMSR and its effect on the
    inspectability of your audit reports. §2 of that document was verified in
    July 2026 and regulations change.
15. If operating under ANPP, assess ANPP's audit record requirements against
    this module. **They could not be verified during construction and no ANPP
    support is claimed.**

---

## 7. Statement

The `ls_audit` module has been verified as structurally coherent by static
analysis, and nine defects found during that verification have been corrected.
It has **not** been executed, tested, installed or validated.

It must not be used in a regulated environment until at minimum the work in
§6.1 and §6.2 is complete and documented.

No claim of compliance with any regulatory framework is made.
