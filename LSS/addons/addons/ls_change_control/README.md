# Life Sciences - Change Control (`ls_change_control`)

Odoo 19.0 Community Edition module managing the lifecycle of a controlled
change in a regulated life sciences organisation.

## Critical notice on regulatory compliance

This module is designed to **support** the implementation of a change control
process. **Software alone does not achieve regulatory compliance.** Compliance
depends on the procedures of the organisation, the validation of the system in
its intended use, the training of personnel, the quality management system and
the ongoing monitoring of the process.

This module is **not certified** against any regulatory framework. Every
statement in this documentation describing a link with a regulation describes
how the module *supports* an organisation implementing that requirement. It is
never a claim of compliance.

## Verification status of this release

| Item | Status |
|------|--------|
| Python syntax, style, docstrings | Verified by `static_check.py`, 170 checks, 0 error |
| XML well-formedness | Verified with `xmllint` |
| Odoo 19 view syntax (`list`, `chatter`, no `attrs`) | Verified against the official Odoo 19.0 documentation |
| External identifier references | Verified by `static_check.py` |
| Access rights coverage of every model | Verified by `static_check.py` |
| **Module installation** | **Not executed.** No Odoo runtime was available in the build environment |
| **Automated test suite** | **Not executed.** Requires an Odoo 19 instance and a PostgreSQL database |
| **flake8 / pylint-odoo** | **Not executed.** Not installable in the build environment |

See `docs/validation_report.md` for the full statement.

## Scope

The module covers the workflow required by section 7.6 of the Life Sciences
Suite functional specification:

```
Draft -> Under Review -> Impact Assessment -> Approved -> Implementation
      -> Verified -> Closed
```

with `Rejected` and `Cancelled` as final outcomes.

## Features

* **Change categories** driving the impact areas to assess, the approval
  matrix and the deadlines of implementation and verification.
* **Impact assessment**: one record per impact area, with a mandatory written
  rationale and mandatory required actions when an impact is declared.
* **Approval matrix** generated from the category, recording for each decision
  the identity of the approver, the date and time in UTC and the meaning of the
  signature.
* **Implementation actions** that cannot be closed without an evidence
  reference.
* **Effectiveness verification** with acceptance criteria defined before the
  verification is performed.
* **Change control record report** in PDF, printable for an inspection.
* **Three scheduled reminders**: pending approvals, late implementations, due
  verifications.

## Data integrity design

| Mechanism | Effect |
|-----------|--------|
| Frozen content fields | The description of the change cannot be modified once the request is submitted, by anybody |
| Protected workflow fields | State and decision fields are only written by the workflow methods, through `sudo()` which cannot be reached from an RPC context |
| Immutable records | A completed assessment, a recorded decision, a closed action and a completed verification can never be modified or deleted |
| Retention | A submitted change request can never be deleted |
| Attribution | Workflow writes keep the real user on the environment, so the message tracking of the chatter attributes every change to the person who performed it |

## Dependencies

`base`, `mail`, `hr`. Nothing else.

The functional specification of the suite lists `ls_qms` and `ls_validation` as
dependencies of this module. Those modules do not exist: the specification
describes them as architectural recommendations. A dependency on software that
does not exist cannot be declared, so the module ships integration points
instead. See `docs/developer_manual.md`, section "Integration with the rest of
the suite".

## Installation

```bash
git clone <repository> /opt/odoo/addons/ls_change_control
odoo-bin -d <database> -i ls_change_control --stop-after-init
```

Full procedure: `docs/installation_guide.md`.

## Running the tests

```bash
odoo-bin -d <database> -i ls_change_control --test-enable \
         --test-tags /ls_change_control --stop-after-init --log-level=test
```

## Documentation

| Document | Content |
|----------|---------|
| `docs/01_business_analysis.md` | Objectives, stakeholders, user stories, scope, risks |
| `docs/02_regulatory_analysis.md` | Applicable frameworks and how the module supports them |
| `docs/03_functional_specification.md` | Workflows, state machine, business rules, reports |
| `docs/04_technical_specification.md` | Models, fields, constraints, security, files |
| `docs/05_architecture_review.md` | Review against SOLID, DRY, KISS and Odoo conventions |
| `docs/installation_guide.md` | Installation and upgrade |
| `docs/configuration_guide.md` | Categories, impact areas, approval matrix, parameters |
| `docs/user_manual.md` | Day to day use, role by role |
| `docs/administrator_manual.md` | Security, scheduled actions, maintenance |
| `docs/developer_manual.md` | Architecture, extension points, coding rules |
| `docs/api_documentation.md` | Public methods and their contracts |
| `docs/test_report.md` | Test inventory and execution status |
| `docs/validation_report.md` | What was verified and what was not |
| `docs/compliance_checklist.md` | Final checklist against the master requirements |
| `docs/CHANGELOG.md` | Version history |
| `docs/RELEASE_NOTES.md` | Release notes of version 19.0.1.0.0 |

## License

AGPL-3.0 or later.
