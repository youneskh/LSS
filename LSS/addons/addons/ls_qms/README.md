# Life Sciences QMS (`ls_qms`)

Controlled quality documentation, quality objectives and quality records for
regulated Life Sciences organisations, on **Odoo 19 Community Edition**.

* **Version:** 19.0.1.0.0
* **License:** AGPL-3.0-or-later
* **Development status:** Alpha
* **Depends on:** `base`, `mail`, `hr`
* **Odoo Enterprise code used:** none

---

## 1. What the module does

`ls_qms` implements Layer 3 of the Life Sciences Suite for the Quality
Management System scope defined in section 7.2 of the Functional
Specification. It provides:

| Capability | Model |
|---|---|
| Quality policy under revision control | `ls.qms.policy` |
| Standard operating procedures | `ls.qms.sop` |
| Work instructions subordinate to a procedure | `ls.qms.work_instruction` |
| Quality plans with a table of control lines | `ls.qms.quality_plan` |
| Control line of a quality plan | `ls.qms.quality_plan.line` |
| Quality objectives with measured achievement | `ls.qms.objective` |
| Dated measurement of an objective | `ls.qms.objective.measurement` |
| Quality records with retention control | `ls.qms.quality_record` |

Two abstract models carry the shared behaviour:

| Abstract model | Responsibility |
|---|---|
| `ls.qms.document.mixin` | Lifecycle, revisions, periodic review, freezing of published content |
| `ls.qms.parameter.mixin` | Validated reading of the system parameters |

## 2. Document lifecycle

```
draft ──submit──► under_review ──approve──► approved ──publish──► published
  ▲                    │                                             │
  │                    │ reject                          create new revision
  └────────────────────┘                                             │
                                                                     ▼
published (previous revision) ──automatically──► obsolete    under_revision
```

Rules enforced by the code:

1. Only the transitions drawn above are accepted. Any other transition raises
   a user error naming the source and the target state.
2. The author of a document cannot approve it while the system parameter
   `ls_qms.enforce_segregation_of_duties` is true.
3. Approval and publication require the group **Approver**.
4. Withdrawal and reopening require the group **Manager**.
5. Content fields of a published or obsolete revision cannot be written.
6. Only a draft revision can be deleted.
7. Publishing revision *n* sets revision *n-1* to obsolete and stamps its
   withdrawal date.
8. A work instruction cannot be published before its parent procedure.

## 3. Roles

| Group | Reads | Creates and edits | Approves and publishes | Withdraws and deletes |
|---|---|---|---|---|
| Viewer | published revisions only | no | no | no |
| User | every state | yes | no | no |
| Approver | every state | yes | yes | no |
| Manager | every state | yes | yes | yes |

Each group implies the previous one.

## 4. Installation

```bash
odoo-bin -d <database> -i ls_qms --stop-after-init
```

The full procedure, including the prerequisites and the verification steps,
is in `docs/06_installation_guide.md`.

## 5. Documentation

| File | Content |
|---|---|
| `docs/01_business_analysis.md` | Objectives, stakeholders, user stories, scope |
| `docs/02_regulatory_analysis.md` | Frameworks supported, and what is **not** covered |
| `docs/03_functional_specification.md` | Menus, workflows, business rules, reports |
| `docs/04_technical_specification.md` | Models, fields, constraints, security, data |
| `docs/05_architecture_review.md` | Review against Odoo, OCA and design principles |
| `docs/06_installation_guide.md` | Installation and post-installation checks |
| `docs/07_configuration_guide.md` | System parameters, groups, sequences |
| `docs/08_user_manual.md` | Day-to-day operation for each role |
| `docs/09_administrator_manual.md` | Scheduled actions, backup, monitoring |
| `docs/10_developer_manual.md` | Extension points and coding conventions |
| `docs/11_api_documentation.md` | Public methods, signatures and return values |
| `docs/12_test_report.md` | Test inventory and **execution status** |
| `docs/13_validation_report.md` | Validation position and residual risks |
| `docs/14_verification_and_deviation_register.md` | Verified facts, unverified points, deviations |

## 6. Statement on regulatory compliance

This module **supports** the implementation of quality processes. It does
**not** certify compliance with any regulatory framework. It does not replace
an organisational quality system, staff training, or computerised system
validation performed by the operating organisation.

Two functions frequently expected in a regulated environment are
**deliberately outside** this module and are delegated to separate modules of
the Life Sciences Suite:

| Function | Delegated to | State of the extension point |
|---|---|---|
| Authenticated electronic signature per 21 CFR 11.100 and 11.200 | `ls_electronic_signature` | `_ls_qms_signature_hook` is called at approval and returns `True` in this module |
| Field level audit trail with hash chain | `ls_audit_trail` | Not implemented here; `mail.thread` tracking only |

Read `docs/13_validation_report.md` before deploying in a regulated
environment.
