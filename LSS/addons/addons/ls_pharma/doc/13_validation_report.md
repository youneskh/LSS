# Validation Report

## 13.1 Delivery verdict

**CONDITIONAL PASS.**

The module is complete against its specification and internally consistent.
It has not been executed, installed or measured. It is delivered as an
engineering artefact ready for qualification, not as a qualified system.

## 13.2 Evidence

| Claim | Evidence | Status |
|---|---|---|
| Every Python file is syntactically valid | `python3 -m py_compile` over every file | Verified |
| Every XML file is well formed | `lxml.etree.parse` over every file | Verified |
| Every field named in a view exists on its model | `static_check.py`, check 1 | Verified |
| Every button names a method that exists | `static_check.py`, check 2 | Verified |
| Every internal reference resolves | `static_check.py`, check 3 | Verified |
| Every external reference names a declared dependency | `static_check.py`, check 3 | Verified |
| Every model has access rules | `static_check.py`, check 6 | Verified |
| The manifest and the file tree agree | `static_check.py`, check 5 | Verified |
| The checker itself detects faults | 15 injected faults, all detected | Verified |
| The module installs on Odoo 19 | — | **Not verified** |
| The tests pass | — | **Not verified** |
| Coverage reaches any figure | — | **Not measured** |
| `flake8`, `pylint`, `pylint-odoo` are clean | — | **Not run** |
| The reports render | — | **Not verified** |

## 13.3 Why the unverified items are unverified

The build environment carries Python 3.12 and `lxml`. It has no Odoo runtime,
no PostgreSQL server and no network access, so packages could not be
installed and no server could be started. This is a limitation of the
environment, not a decision about what should be verified.

## 13.4 Residual risks

| # | Risk | Likelihood | Consequence | Detection |
|---|---|---|---|---|
| RR-1 | `res.groups.privilege` and `privilege_id` behave differently in the target Odoo 19 build | Low | Installation fails on the security file | First installation attempt |
| RR-2 | `web.external_layout` or `web.html_container` differs in the target build | Low | Both reports fail to render; nothing else is affected | First print |
| RR-3 | A field or method behaves differently at runtime from the reading of the source | Unknown | A test fails | Running the suite |
| RR-4 | A view expression is syntactically valid but semantically wrong | Low | The view misbehaves for the user | Installation and manual review |
| RR-5 | The serial generator behaves poorly for very large quantities | Unknown | Slow generation | Performance testing |
| RR-6 | The multi-company rules do not isolate as intended | Low | Cross-company visibility | Multi-company testing |
| RR-7 | An Algerian requirement is unmet | Certain to be unknown | The site is not ready for an ANPP inspection | Regulatory affairs reading the decrees |

RR-7 deserves emphasis. The Algerian instruments were located by reference
only; their texts were never read. **No requirement of this module derives
from them and no conformity with them is claimed.** A deployment in Algeria
must have those texts read and mapped independently.

## 13.5 Outstanding qualification activities

The following must be performed by the receiving organisation. This module
performs none of them and claims none of them.

### Installation Qualification

| # | Activity |
|---|---|
| IQ-1 | Record the Odoo 19 Community version, the PostgreSQL version and the Python version of the target environment |
| IQ-2 | Install the module and record the result, including any error |
| IQ-3 | Confirm the 26 models, the six groups, the 143 access rules and the 22 record rules exist after installation |
| IQ-4 | Confirm the five sequences, the four storage conditions, the 108 template sections and the two scheduled actions exist |
| IQ-5 | Confirm the root menu and every submenu appears for a user in each group |
| IQ-6 | Record the checksum of the delivered archive |

### Operational Qualification

| # | Activity |
|---|---|
| OQ-1 | Execute the test suite and record the full output, including every failure |
| OQ-2 | Measure coverage and record the figure |
| OQ-3 | Run `flake8`, `pylint` and `pylint-odoo` and record the findings |
| OQ-4 | Render both reports and inspect the output |
| OQ-5 | Test each of the four release gate refusals manually and evidence each refusal |
| OQ-6 | Test the two separations of duty manually with two real users |
| OQ-7 | Attempt to modify and to delete a release decision, as an administrator, and evidence both refusals |
| OQ-8 | Verify a decision digest, then alter a covered value directly in the database and confirm the verification then fails |
| OQ-9 | Test multi-company isolation with two companies and a user in one of them |
| OQ-10 | Execute both scheduled actions manually and inspect the effect |
| OQ-11 | Confirm the generated schedule against ICH Q1A(R2) for at least one twelve-month and one twenty-four-month study |
| OQ-12 | Confirm the check digit implementation against a key issued to your own company |

### Performance Qualification

| # | Activity |
|---|---|
| PQ-1 | Run a real batch through the full lifecycle with the real users who will operate it |
| PQ-2 | Have the quality unit review the printed batch record against your written procedure and record the gap, if any |
| PQ-3 | Have regulatory affairs review the dossier template against your authority's requirements |
| PQ-4 | Generate serial numbers at the volume of a real packaging run and record the elapsed time |
| PQ-5 | Confirm that the printed record together with your other records constitutes a complete batch record under your procedures |
| PQ-6 | Train each role and record the training |

## 13.6 Statement of limitations

- This module does not confer compliance with any regulation.
- It is not a 21 CFR Part 11 electronic signature system, and the SHA-256
  digest on a release decision is not an electronic signature.
- The printed batch record is not a complete batch record; its closing note
  names what it omits.
- No coverage percentage and no test pass rate is claimed anywhere in this
  documentation, because none was measured.
- The Algerian corpus is reference-level only.

## 13.7 Sign-off

This report is issued by the developing party. It is not a validation
certificate. Validation is performed by the receiving organisation, on its
own environment, against its own user requirements, and is evidenced by the
records produced under section 13.5.

| Role | Name | Date | Signature |
|---|---|---|---|
| Prepared by | Life Sciences Suite Architecture Team | 2026 | — |
| Reviewed by | *to be completed by the receiving organisation* | | |
| Approved by | *to be completed by the receiving organisation* | | |
