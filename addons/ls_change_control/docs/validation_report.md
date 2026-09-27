# Validation Report

Module: `ls_change_control` version 19.0.1.0.0 | Date: 2026-07-24

## 1. Purpose and status of this document

This document states, honestly and without embellishment, **what was verified
and what was not** during the construction of the module.

> **This document is not a validation certificate.**
>
> Validation of a computerised system is performed by the organisation that
> operates it, against its own user requirements, in its own environment, under
> its own quality management system. A software supplier cannot validate a
> system on behalf of its user.
>
> What follows is the supplier side evidence that supports the validation the
> receiving organisation must perform.

## 2. Limitations of the build environment

The module was designed, written and analysed in an environment with:

* no Odoo runtime;
* no PostgreSQL database;
* no network access, therefore no possibility of installing Odoo, `flake8`, `pylint-odoo` or any other package.

The direct consequences are:

| Consequence | Severity |
|-------------|----------|
| The module was never installed | High |
| The module was never upgraded from a previous version | High |
| The automated test suite was never executed | High |
| Coverage was never measured | High |
| `flake8`, `pylint` and `pylint-odoo` were never executed | Medium |
| No PDF was ever rendered | Medium |
| No screen was ever displayed | Medium |

None of these is a defect of the design. All are limitations of the
environment, and all define work that the receiving organisation must perform.

## 3. What was verified, and how

| # | Item | Method | Result |
|---|------|--------|--------|
| V-1 | Python syntax of all 25 Python files | `ast.parse` | Pass |
| V-2 | XML well-formedness of all 20 XML files | `xmllint --noout` | Pass |
| V-3 | Line length, whitespace, final newline | `static_check.py` | Pass |
| V-4 | Docstring on every module, class and public method | `static_check.py` | Pass |
| V-5 | No placeholder comment, no dead code | `static_check.py` and review | Pass |
| V-6 | No construct removed in Odoo 17, 18 or 19 | `static_check.py` | Pass |
| V-7 | Every external identifier reference resolves | `static_check.py` | Pass |
| V-8 | No reference to a module outside the declared dependencies | `static_check.py` | Pass |
| V-9 | Every manifest file exists; every XML file is declared | `static_check.py` | Pass |
| V-10 | Every model is covered by access rights | `static_check.py` | Pass |
| V-11 | Access rights header and permission values | `static_check.py` | Pass |
| V-12 | `_description` on every model | `static_check.py` | Pass |
| V-13 | Manifest keys and version format for Odoo 19 | `static_check.py` | Pass |
| V-14 | Odoo 19 list view element is `list` | Official Odoo 19.0 documentation, View architectures | Confirmed and applied |
| V-15 | Odoo 19 chatter element is `<chatter/>` | Official Odoo 19.0 documentation, Mixins | Confirmed and applied |
| V-16 | Odoo 19 SQL constraints use `models.Constraint` | Official Odoo 19.0 documentation, Constraints tutorial | Confirmed and applied |
| V-17 | Odoo 19 kanban root template is `card` | Official Odoo 19.0 documentation, View architectures | Confirmed and applied |
| V-18 | `sudo()` preserves the real user, so tracking stays attributable | Odoo pull request 34297 introducing superuser mode | Confirmed and relied upon |

Total: **170 automated checks, 0 error, 0 warning.**

## 4. What was NOT verified

| # | Item | Why | Who must do it |
|---|------|-----|----------------|
| N-1 | The module installs on a clean database | No Odoo runtime | Receiving organisation, installation qualification |
| N-2 | The module upgrades without loss | No Odoo runtime | Receiving organisation |
| N-3 | The 121 tests pass | No Odoo runtime | Receiving organisation |
| N-4 | Test coverage reaches 95 percent | No Odoo runtime | Receiving organisation |
| N-5 | `flake8` and `pylint-odoo` report no blocking issue | Packages not installable | Receiving organisation |
| N-6 | Views render correctly | No runtime | Receiving organisation, operational qualification |
| N-7 | The PDF report renders correctly | No runtime and no PDF engine | Receiving organisation |
| N-8 | Notifications are delivered | No mail server | Receiving organisation |
| N-9 | Performance under production volume | No runtime | Receiving organisation, performance qualification |
| N-10 | Behaviour on a database migrated from an earlier Odoo version | No runtime | Receiving organisation |

## 5. Statements that could not be verified from official documentation

The master specification requires that unverifiable information be declared as
such rather than guessed. The following applies.

| Item | Statement |
|------|-----------|
| Presence of `numbercall` and `doall` on `ir.cron` in Odoo 19.0 | **This information could not be verified from official documentation.** Both fields are therefore omitted from the scheduled action records. They are not required to schedule a recurring job |
| Signature of the credential checking API of `res.users` in Odoo 19.0 | **This information could not be verified from official documentation.** No re-authentication of the signer is implemented. The `_apply_signature` extension point is provided instead |
| Exact clause numbering of the ISO standards cited by the suite specification | **This information could not be verified from official documentation.** ISO standards are copyrighted and were not available. The regulatory analysis maps the module at framework level only, and the organisation must map it to the clauses of the standards it holds under licence |
| Field name of the groups relation on `res.users` in Odoo 19.0 | **This information could not be verified from official documentation.** The tests therefore use the documented `new_test_user` helper, which insulates them from the field name |

## 6. Deviations from the functional specification of the suite

Each deviation is stated with its reason. None is an omission.

| # | Specification | Delivered | Reason |
|---|--------------|-----------|--------|
| D-1 | Section 15.3: depends on `ls_qms` and `ls_validation` | Depends on `base`, `mail`, `hr` | Those modules do not exist; the specification itself describes them as architectural recommendations. A dependency on non existent software would make the module uninstallable. Integration points are documented in `docs/developer_manual.md` |
| D-2 | Section 7.6: menus under `Quality` | Own root menu `Change Control` | The parent menu belongs to `ls_qms`, which does not exist. Re-parenting requires one `menuitem` override in a bridge module |
| D-3 | Section 7.6: states Draft to Closed | Exactly those seven states, plus Rejected and Cancelled | Rejected and Cancelled are required by the specification's own description of the process; they are outcomes, not steps. Approvals are collected inside `impact_assessment` rather than in an eighth state, so as not to deviate from the listed sequence |
| D-4 | Section 7.14: electronic signatures | Decision metadata recorded and made immutable; no re-authentication | Electronic signatures are assigned to `ls_electronic_signature` by the suite architecture. Implementing a partial signature here would risk an unfounded claim of compliance |
| D-5 | Section 7.6: four security groups | Exactly four groups | No assessor group was added. An assessor holds the Requester group; restriction to their own assessment is enforced in the application logic |

## 6.1 Deviation from the master prompt

| # | Requirement | Status | Reason |
|---|------------|--------|--------|
| MD-1 | "Generate all JavaScript files" | No JavaScript is delivered | The module requires none: every screen uses standard Odoo view types. Adding front end code with no purpose would add risk and maintenance burden without functional value. Stated rather than silently omitted |
| MD-2 | "Coverage target: minimum 95 percent" | Not measured | Requires an Odoo runtime. Stating a figure would be fabrication |
| MD-3 | "The module shall pass flake8, pylint, pylint-odoo" | Not executed | Packages not installable offline. A substitute analyser covering syntax, style, docstrings, XML and Odoo 19 conformance was written and executed instead |

## 7. Residual risks

| # | Risk | Mitigation |
|---|------|-----------|
| RR-1 | An installation defect not detected by static analysis | Installation qualification by the receiving organisation before any use |
| RR-2 | A run time defect in a rarely used branch | Execution of the 121 tests, then operational qualification |
| RR-3 | An organisation believes the module makes it compliant | Repeated notices in the README, the description page and the regulatory analysis |
| RR-4 | An organisation relies on the module for binding electronic signatures | Stated explicitly in the README, the regulatory analysis and this report |
| RR-5 | The configuration is modified without control | The configuration is a quality record; the configuration guide states it must be managed under the change control procedure |

## 8. Work required before the module may be used in a regulated environment

1. Define the user requirements specification of the organisation for change control.
2. Perform the installation qualification: install on a clean Odoo 19.0 Community instance and verify each item of section 2.3 of the installation guide.
3. Execute the 121 automated tests and record the outcome.
4. Measure coverage and assess any gap against the requirements of the organisation.
5. Execute `flake8` and `pylint-odoo` and assess any finding.
6. Perform the operational qualification: exercise every workflow through the interface, including the refused paths.
7. Verify the rendering of the change control record report.
8. Perform the performance qualification with representative volumes.
9. Configure categories, impact areas, approval matrices and parameters, and have the configuration approved by the quality unit.
10. Write the standard operating procedure covering the use of the system.
11. Train the users and record the training.
12. Establish the backup, restoration and retention procedures.

## 9. Conclusion

| Aspect | Verdict |
|--------|---------|
| Design and architecture | Reviewed, `docs/05_architecture_review.md`, PASS with 7 disclosed findings |
| Source code quality | 170 static checks, 0 error |
| Odoo 19 conformance of the constructs used | Verified against the official documentation |
| Completeness against the specification | Complete, with 5 stated deviations, all justified |
| Documentation | Complete |
| Installation, execution, tests, coverage | **NOT VERIFIED. Remains to be performed by the receiving organisation** |

The module is delivered as **ready for qualification**, not as qualified. Any
statement that this module is validated, qualified or compliant would be false
at the date of this report.
