# 13 — Validation Report

Phase 10 deliverable. Status: **CONDITIONAL**. This document does not declare
the module validated.

## 1. Position on validation

Computerised system validation is an activity of the operating organisation.
It cannot be performed by the supplier of a software package, and it cannot be
performed by the author of this document, who has no access to the intended
use, the process, the infrastructure or the users of any organisation.

This report therefore states what the supplier has done, and what remains for
the operating organisation.

## 2. What the supplier has done

| Activity | Evidence |
|---|---|
| Business analysis | `01_business_analysis.md` |
| Regulatory analysis, including a register of requirements **not** met | `02_regulatory_analysis.md` |
| Functional specification | `03_functional_specification.md` |
| Technical specification | `04_technical_specification.md` |
| Architecture review, with two defects found and corrected | `05_architecture_review.md` |
| Source code with docstrings on every method | `models/`, `wizards/` |
| Written test suite, 115 test methods | `tests/`, inventory in `12_test_report.md` |
| Syntax and XML verification | `12_test_report.md`, section 3 |
| Register of verified facts, unverified points and deviations | `14_verification_and_deviation_register.md` |

## 3. What remains for the operating organisation

| Deliverable | Note |
|---|---|
| Validation plan | Scope and depth set by the risk of the intended use |
| User requirements specification | The functional specification is a supplier document, not a user requirement |
| Risk assessment of the intended use | Including the gaps of section 4 |
| Installation qualification | Version of Odoo, version of the module, checksum, environment |
| Operational qualification | Execution of the test suite, plus tests of any configuration made locally |
| Performance qualification | Execution by the intended users on the intended process |
| Standard operating procedures | Use of the system, change control, backup, access management |
| Training records | Per user and per role |
| Periodic review of the system | Frequency set by the organisation |

## 4. Residual risks

| Identifier | Risk | Severity | Treatment left to the organisation |
|---|---|---|---|
| RR-01 | Approval is not an authenticated electronic signature per 21 CFR 11.100 and 11.200 | High where Part 11 applies | Assess whether Part 11 applies; if it does, do not use this module for signed approvals until `ls_electronic_signature` exists |
| RR-02 | Change tracking is the `mail.thread` mechanism, not a protected audit trail per 21 CFR 11.10(e) | High where Part 11 applies | Same assessment; consider database level auditing meanwhile |
| RR-03 | The module has never been installed or executed | High at first deployment | Execute the installation and the test suite in a qualification environment before any production use |
| RR-04 | No static analysis was run | Medium | Run `flake8` and `pylint-odoo` and review the findings |
| RR-05 | ANPP technical requirements could not be verified | Unknown | Obtain the requirements from the authority and assess the module against them |
| RR-06 | A quality manager can correct a confirmed record | Medium | Procedural control: require a documented justification, and review the chatter during internal audits |
| RR-07 | Setting the segregation parameter to False removes the four eyes principle | High if used | Restrict `base.group_system`, and place the parameter under change control |

## 5. Conclusion

The module is a **syntactically valid, documented, untested source package**
whose design follows the Odoo 19 patterns verified against official
documentation. It is suitable for entry into a qualification environment. It
is **not** suitable for direct production use in a regulated process, and no
statement in this delivery should be read as declaring it compliant, qualified
or validated.
