# Life Sciences Suite — Medical Devices (`ls_medical_device`)

Medical device regulatory management for **Odoo 19 Community Edition**.

License: AGPL-3.0 or later. Author: Life Sciences Suite Architecture Team.

---

## What this module does

It manages the regulatory record set of a medical device across its life
cycle: the device register, UDI assignments, ISO 14971 risk management,
clinical evaluation and post-market clinical follow-up, technical
documentation, CE marking and declarations of conformity, and post-market
surveillance with its periodic reports.

## What this module does not do

Stated plainly, because the omissions matter more than the inclusions in a
regulated context:

- **It does not certify compliance** with any regulatory framework. It records
  and structures information; conformity is established by the organisation
  through its quality system, its validation activities and, where required,
  a notified body.
- **It does not implement a vigilance case model.** Serious incident and field
  safety corrective action reporting under MDR Article 87 is out of scope.
  The reporting deadlines are published in `models/constants.py` for reuse by
  an integrating module, and the periodic report records incident *counts*
  only.
- **It does not submit anything to EUDAMED.** Submission is recorded as a
  date, a channel and a reference. See the EUDAMED note below.
- **It does not implement electronic signatures** under 21 CFR Part 11. The
  approval workflow records who approved what and when, which is not the same
  thing. Electronic signature is the scope of `ls_electronic_signature`.
- **It does not classify devices.** The risk class is selected by the user and
  the classification rationale is recorded as text. The module does not
  implement the Annex VIII classification rules.

## Regulatory basis

Every regulatory value in the code carries a source reference in the comment
that declares it. The provisions relied upon are:

| Provision | Applied to |
|---|---|
| MDR Article 10(8) | Technical documentation retention: 10 years, 15 for implantables |
| MDR Article 27 | UDI system: Basic UDI-DI, UDI-DI, UDI-PI, packaging levels |
| MDR Article 56(2) | Certificate validity not exceeding five years |
| MDR Article 61(11) | Annual PMCF evaluation report update for class III and implantables |
| MDR Article 83 | Post-market surveillance system |
| MDR Article 84 | Post-market surveillance plan, part of Annex III documentation |
| MDR Article 85 | Post-market surveillance report for class I devices |
| MDR Article 86(1) | PSUR for class IIa, IIb, III; IIa at least biennial, IIb and III at least annual |
| MDR Article 86(2) | Submission of the report to the notified body for class III and implantables |
| MDR Article 88 | Trend reporting, recorded as a trend signal on the periodic report |
| MDR Annex I | General safety and performance requirements |
| MDR Annex II | Technical documentation structure |
| MDR Annex III | Technical documentation on post-market surveillance |
| MDR Annex XIII Section 2 | Custom-made device documentation |
| ISO 14971:2019 | Risk management process, control option hierarchy, residual risk evaluation |

**Values that could not be verified** are not asserted. The severity and
probability scales, the risk matrix boundaries and the Annex II section titles
are shipped as **editable configuration data**, not as constants, precisely
because ISO 14971 requires the manufacturer to define its own scales and
because the Annex II section titles were confirmed only against secondary
renderings rather than the Official Journal text. Confirm them before use.

## EUDAMED note

Commission Decision (EU) 2025/2371, published in the Official Journal on
27 November 2025, declared four EUDAMED modules functional and, under the
transitional provisions of Regulation (EU) 2024/1860, triggered a six-month
transition. From **28 May 2026** the Actor Registration, UDI/Device
Registration, Notified Bodies and Certificates, and Market Surveillance
modules are mandatory to use.

The **Vigilance and Post-Market Surveillance** module was *not* among the four
declared functional. This module therefore records the submission of a
periodic report as a channel, a date and a reference, rather than asserting a
mandatory EUDAMED route that is not in force. Published sources differ on the
deadline for registering devices already on the market before 28 May 2026
(27 versus 28 November 2026); this module asserts neither date and records no
deadline of its own.

## Installation

Requires Odoo 19.0 Community. Dependencies: `base`, `mail`, `product`,
`stock`. External Python dependency: `python-dateutil`.

```bash
cp -r ls_medical_device /path/to/odoo/addons/
odoo -u ls_medical_device -d <database>
```

The scheduled actions are created by a post-installation hook rather than an
XML data file. See `hooks.py` for the stated reason.

## Access levels

| Level | Grants |
|---|---|
| Viewer | Read-only access to every record |
| User | Create and maintain draft records; cannot approve or change market status |
| Regulatory Affairs | Approve regulatory records, manage certificates, change market status |
| Manager | Full access including configuration and deletion |

Segregation of duties is enforced in Python inside the business methods, not
only in the views, so it also applies to programmatic access. An approver may
not approve a record they authored.

## Documentation

- `doc/installation_guide.md`
- `doc/configuration_guide.md`
- `doc/user_manual.md`
- `doc/administrator_manual.md`
- `doc/developer_manual.md`
- `doc/api_reference.md` — generated from source by `ast`
- `doc/test_report.md`
- `doc/validation_report.md`
- `doc/regulatory_traceability.md`
- `doc/CHANGELOG.md`

## Delivery status

**This module has never been installed against a running Odoo 19 instance.**
The test suite has been written but never executed; no coverage has been
measured; `flake8`, `pylint` and `pylint-odoo` have not been run. The build
environment has no Odoo runtime, no PostgreSQL and no network access.

What *has* been verified is documented in `doc/validation_report.md`, together
with the qualification activities the receiving organisation must complete
before this module is used in a regulated environment.
