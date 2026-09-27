# Phase 10 — Final Validation Checklist

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Compliance checklist

| # | Requirement of the framework | Status | Evidence |
|---|------------------------------|--------|----------|
| C-01 | Follows the official Odoo module architecture | Met | Technical specification 4.1 |
| C-02 | Follows the OCA conventions where applicable | Met | Architecture review 5.2 |
| C-03 | Odoo 19 Community only, no Enterprise code | Met | Four Community dependencies; no Enterprise source used |
| C-04 | Does not modify the Odoo core | Met | No core view inheritance, no monkey patch |
| C-05 | Uses inheritance where possible | Met | Two mixins inherited, one core taxonomy reused |
| C-06 | Respects the MVC separation | Met | Architecture review 5.4 |
| C-07 | Respects the ORM best practices | Met | No raw SQL, no query in a loop |
| C-08 | Optimises the SQL queries | Partially met | Indexes declared; one filter resolved in Python, finding PERF-01 |
| C-09 | Prevents SQL injection | Met | No raw SQL |
| C-10 | Prevents XSS | Met | No `t-raw`, sanitising `Html` field |
| C-11 | Validates the user input | Met | 6 database constraints, 4 Python constraints, 20 business rules |
| C-12 | Respects the access rights | Met | 21 access rules, 3 groups |
| C-13 | Respects the record rules | Met | 6 multi-company rules |
| C-14 | Installs successfully | **Not verified** | NV-01 |
| C-15 | Updates successfully | **Not verified** | NV-02 |
| C-16 | Passes the automated quality checks | Partially met | Own analysis passes; flake8 and pylint-odoo not run, NV-05 |
| C-17 | Is fully tested | Partially met | 101 tests written, not executed, NV-03 |
| C-18 | Reaches 95 % coverage | **Not verified** | NV-04 |
| C-19 | Is fully documented | Met | 17 documents, listed below |
| C-20 | Is maintainable | Met | Architecture review 5.7 |
| C-21 | Is upgrade safe | Met | Architecture review 5.5 |
| C-22 | Contains no placeholder | Met | Static analysis, zero finding |
| C-23 | Contains no omitted functionality | Met | Every item of the functional specification is implemented; the exclusions are listed and justified in Phase 1.8 |
| C-24 | Contains no vague wording | Met | Every limitation is quantified and named |
| C-25 | Contains no unexplained assumption | Met | Every unverified item is marked and listed in the validation report |
| C-26 | Makes no false claim of regulatory compliance | Met | Phase 2, README, validation report |

## 2. Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Directory tree | `ls_calibration/` | Complete |
| Python sources | `models/`, `wizards/` | 13 files |
| XML sources | `views/`, `security/`, `data/`, `demo/`, `report/`, `wizards/` | 14 files |
| JavaScript sources | none | **Deliberately none.** No client-side code is required; every screen uses standard view types. This removes the most version-sensitive layer. |
| Security files | `security/` | 2 files, 3 groups, 21 access rules, 6 record rules |
| Data files | `data/` | 3 files |
| Demonstration data | `demo/` | 1 file |
| Reports | `report/` | 2 reports, 4 templates |
| Tests | `tests/` | 9 modules, 101 methods |
| Documentation | `README.rst`, `readme/`, `doc/` | 8 + 9 documents |
| Static analysis tool | `tools/static_analysis.py` | Delivered beside the module |
| Translation template | `i18n/` | Empty; produced by `--i18n-export`, see technical specification 4.15 |
| Application icon | `static/description/icon.png` | Present |

## 3. Documentation set

| Document | Phase |
|----------|-------|
| `01_business_analysis.md` | 1 |
| `02_regulatory_analysis.md` | 2 |
| `03_functional_specification.md` | 3 |
| `04_technical_specification.md` | 4 |
| `05_architecture_review.md` | 5 |
| `06_installation_guide.md` | 9 |
| `07_configuration_guide.md` | 9 |
| `08_user_manual.md` | 9 |
| `09_administrator_manual.md` | 9 |
| `10_developer_manual.md` | 9 |
| `11_api_documentation.md` | 9 |
| `12_test_report.md` | 7 |
| `13_static_analysis_report.md` | 8 |
| `14_validation_report.md` | 9 |
| `15_final_validation_checklist.md` | 10 |
| `CHANGELOG.md` | 9 |
| `RELEASE_NOTES.md` | 9 |

## 4. Phase gates

| Phase | Gate | Reservation |
|-------|------|-------------|
| 1 Business analysis | PASS | none |
| 2 Regulatory analysis | PASS | Five regulatory gaps declared; several references marked as unverified |
| 3 Functional specification | PASS | none |
| 4 Technical specification | PASS | none |
| 5 Architecture review | PASS | Three major findings accepted and declared |
| 6 Development | PASS | Code complete, zero placeholder |
| 7 Testing | CONDITIONAL PASS | Written, not executed |
| 8 Static analysis | CONDITIONAL PASS | Own analysis passes; flake8 and pylint-odoo not run |
| 9 Documentation | PASS | Translation template to be generated from the installed module |
| 10 Final validation | **CONDITIONAL PASS** | See below |

## 5. Phase 10 verdict

**CONDITIONAL PASS.**

The module is complete, internally consistent, documented and free of
placeholders. It cannot be declared production ready, because production
readiness is a statement about observed behaviour, and the module has not
been executed. The manifest therefore declares `development_status: Beta`.

Actions required to close this gate, in order:

1. Install on a clean Odoo 19 Community database. Close NV-01.
2. Run the 101 tests. Close NV-03 and NV-06 to NV-11.
3. Run flake8, pylint and pylint-odoo. Close NV-05.
4. Measure the coverage. Close NV-04.
5. Print both reports. Close NV-12.
6. Install with demonstration data. Close NV-13.
7. Update the module on a copy of production. Close NV-02.
8. Generate `i18n/ls_calibration.pot`.
9. Record the results in documents 12, 13 and 14, then change
   `development_status` to `Production/Stable` and the version to
   `19.0.1.0.1`.

Anyone who signs this checklist as a full pass before those nine actions are
recorded would be signing a statement that has not been demonstrated.
