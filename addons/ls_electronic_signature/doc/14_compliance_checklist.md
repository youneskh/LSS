# Phase 10 — Final Validation and Compliance Checklist

## 1 Phase gates

| Phase | Gate | Basis |
|---|---|---|
| 1 Business Analysis | **PASS** | Objectives, requirements, roles, stories, use cases, scope, exclusions with reasons, 7 risks with mitigations, 8 measurable success criteria. |
| 2 Regulatory Analysis | **PASS** | Requirements verified against eCFR and the printed CFR; each mapped to a mechanism; unverifiable frameworks declared as such; non-implemented paragraphs stated with reasons. |
| 3 Functional Specification | **PASS** | Menus, workflows, state machines, 14 business rules, notifications, 3 scheduled actions, reports, KPIs, search facilities, wizards. |
| 4 Technical Specification | **PASS** | Architecture, dependencies, 11 models, fields, constraints, 4-layer immutability, concurrency, security, injection handling, performance. |
| 5 Architecture Review | **PASS**, 2 open mitigated | 12 findings; AR-1…AR-10 closed in code with regression tests; AR-11, AR-12 carried to qualification. |
| 6 Development | **PASS** | No placeholder, no dead code, no commented-out code, no `TODO`; verified mechanically. |
| 7 Testing | **CONDITIONAL** | 140 tests written and fully traced; **not executed** — no Odoo or PostgreSQL in the build environment. |
| 8 Static Analysis | **CONDITIONAL** | 13 stdlib-based checks pass with 0 findings; flake8/pylint-odoo not installable offline. |
| 9 Documentation | **PASS** | 14 documents plus README and changelog; `.pot` generation documented rather than mis-authored. |
| 10 Final Validation | **CONDITIONAL** | Gates 7 and 8 are open; qualification in the target environment outstanding. |

**The overall gate is CONDITIONAL, not PASS.** Phases 7 and 8 cannot be closed
from an environment with no Odoo installation and no network. Reporting them as
PASS would be a false statement of exactly the kind this module is built to
prevent.

## 2 Coding requirements

| Requirement | Status | Evidence |
|---|---|---|
| Installs successfully | **To verify** | `test_install.py`; requires an Odoo instance |
| Upgrades successfully | **To verify** | All data `noupdate="1"`; requires an instance |
| Official Odoo module architecture | **Met** | Phase 5 §5.1 |
| OCA practice where applicable | **Met** | Phase 5 §5.2 |
| Odoo core not modified | **Met** | Only `res.config.settings` extended by `_inherit` |
| Inheritance used wherever possible | **Met** | `AbstractModel` mixin |
| MVC | **Met** | Rules in models, no logic in views, pure functions in `tools/` |
| ORM best practice | **Met** | `@api.model_create_multi`; batched search; no query per record |
| SQL optimised | **Met** | 9 indexes; chain head read is one indexed `LIMIT 1` |
| SQL injection prevented | **Met** | Parameter binding throughout; only module constants interpolated |
| XSS prevented | **Met** | `t-out` only; no `t-raw` |
| Input validated | **Met** | 7 Python constraints, 8 SQL constraints, `ast.literal_eval` never `eval` |
| Access rights respected | **Met** | 20 ACL rows; no write or unlink on evidence anywhere |
| Record rules respected | **Met** | 7 global company rules, 6 group rules |
| PEP 8 | **Met** for what was checked | Line length, whitespace, imports, docstrings: 0 findings. flake8 outstanding |
| Complete docstrings | **Met** | 0 missing, verified by AST |
| No duplicated code | **Met** | Canonicalisation, manifestation block and parameter reading each exist once |
| No dead or commented-out code | **Met** | Verified mechanically |
| No `TODO`/`FIXME` | **Met** | 0 occurrences |

## 3 Deliverables

| Deliverable | Status |
|---|---|
| Directory tree | Delivered |
| Python source (30 files) | Delivered |
| XML (22 files) | Delivered |
| Security (2 XML + 2 CSV) | Delivered |
| Data and demo (5 files) | Delivered |
| Reports (3 files) | Delivered |
| Tests (14 files, 140 tests) | Delivered, not executed |
| Documentation (14 documents + README + CHANGELOG) | Delivered |
| Application icon | Delivered, generated deterministically |
| JavaScript | **None** — architectural decision, Phase 4 §4.10 |
| `.pot` translation template | **Not shipped** — generation command documented; hand-authoring would produce false source references |

## 4 Regulatory support summary

Supported, with a specific implementing mechanism: §11.50(a), §11.50(b),
§11.70, §11.100(a), §11.100(c) partially, §11.200(a)(1), §11.200(a)(1)(i),
§11.200(a)(1)(ii), §11.200(a)(2), §11.300(a) via the platform, §11.300(d).

Not supported, each with a stated reason: §11.100(b) and the §11.100(c)
certification itself (organisational); §11.200(a)(3) (predominantly
organisational; partially supported only); §11.300(b), (c) (platform and
procedure); §11.300(e) (no devices used); §11.10 (system-wide, and partly the
subject of sibling modules).

**No compliance with, or certification against, any framework is claimed.**

## 5 Release gate — must be closed before production use

| # | Action | Owner |
|---|---|---|
| 1 | Install on a clean Odoo 19.0 Community database; confirm IQ-1…IQ-4 | IT |
| 2 | Execute the automated suite; attach the output | Validation |
| 3 | Measure coverage; close or justify any shortfall below 95 % | Validation |
| 4 | Run flake8 and pylint-odoo; attach the output | Development |
| 5 | Execute OQ-CRED-001 | Validation |
| 6 | Execute OQ-VIEW-001 | Validation |
| 7 | Execute MT-1, MT-2, MT-3 | Validation |
| 8 | Execute PT-1, PT-2; record the figures | Validation |
| 9 | Configure the binding statement to match the §11.100(c) certification | Quality Assurance |
| 10 | Populate the Security Unit group with at least one e-mail address | IT |
| 11 | Confirm `attempt_isolated_cursor = 1` | IT |
| 12 | Write the SOPs listed in `13_validation_report.md` §3.2 | Quality Assurance |
| 13 | Train and record training for every signer | Quality Assurance |
| 14 | Replace `LICENSE` with the verbatim AGPL-3.0 text from gnu.org | Development |
| 15 | Approve the validation file | Quality Assurance |

Until every line is closed, the module is **not** released for production use in
a regulated environment.
