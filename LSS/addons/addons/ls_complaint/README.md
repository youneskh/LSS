# Life Sciences — Complaint Management (`ls_complaint`)

Complaint, investigation and adverse event handling for regulated life sciences
organisations, on **Odoo 19 Community Edition**.

**Version** 19.0.1.0.0 · **Licence** AGPL-3 · **Status** Beta

---

## ⚠ Read this first

This module was **written, statically analysed and documented, but never
installed, never executed and never tested.** The environment in which it was
produced has no Odoo runtime and no network access.

- It is **not validated software** and is **not compliant** with any regulation
  on its own.
- **No coverage figure is claimed**; the delivered tests were never run.
- **`flake8`, `pylint` and `pylint-odoo` were never run**; they could not be
  installed offline.
- Fifteen version-sensitive Odoo API points are listed, each with a fallback, in
  [`docs/00_verification_and_limitations.md`](docs/00_verification_and_limitations.md).
  **Read that document before installing.**

## What it does

| Capability | Detail |
|---|---|
| Intake | Any channel, complainant, product and lot traceability, returned sample tracking |
| Classification | Configurable categories, three severities, nine complaint types |
| Assessment | Documented impact assessment with safety and regulatory flags |
| Vigilance | Adverse event records with seriousness, outcome, causality, pseudonymised subject data, reportability decision with a mandatory rationale, configurable deadline and submission tracking |
| Investigation | Eight methodologies, nine root cause categories, batch impact assessment, approval refused to the investigator of the record |
| Resolution | Nine resolution types, mandatory completion evidence |
| Closure | Reviewer distinct from the responsible user, effectiveness confirmation, record frozen afterwards |
| Cancellation | Possible with a documented reason instead of deletion, reversible by a manager |
| Notification | Two daily scheduled actions for overdue complaints and overdue reports |
| Analysis | List, graph and pivot views, eleven filters, eight group-by axes |
| Output | QWeb PDF complaint record, two mail templates |
| Security | Four cumulative levels, 21 access rules, multi-company isolation, per-record segregation of duties |

## What it deliberately does NOT do

**It encodes no regulatory value.** Every time target and the adverse event
reporting deadline are configuration fields defaulting to `0`, meaning *not
configured*. No due date is produced until the deploying organisation sets them
from its own approved procedure. Encoding a value such as "15 days" would assert
a regulatory requirement that was not verified here.

**It does not provide electronic signatures or a tamper-evident audit trail.**
Odoo field tracking plus server-side record freezing is not equivalent to
FDA 21 CFR Part 11 controls. See
[`docs/02_regulatory_analysis.md`](docs/02_regulatory_analysis.md) section 4 for
exactly what is missing.

Also out of scope: CAPA management (a reference field and a documented bridge
contract only), recall execution, document management, automatic transmission to
authority portals, signal detection, LIMS and MES integration, complainant
portal access, translations.

## Installation

```bash
cp -r ls_complaint /opt/odoo/custom-addons/
sudo systemctl restart odoo
odoo-bin -d <database> -i ls_complaint --stop-after-init
```

Full procedure and post-installation checks:
[`docs/installation_guide.md`](docs/installation_guide.md).

**Nothing works until at least one complaint category exists**, because the
category carries the classification and the targets. See
[`docs/configuration_guide.md`](docs/configuration_guide.md).

## Dependencies

`base`, `mail`, `product`, `stock` — all Community. No Enterprise module, no
third-party Python package, no dependency on `ls_qms` or `ls_capa`.

## Access levels

| Level | Can |
|---|---|
| Complaint Viewer | Read everything |
| Complaint Investigator | Create complaints, write the ones he owns or received, investigate, resolve, record adverse events |
| Complaint Reviewer | The above on any complaint, plus approve investigations, waive them and close complaints |
| Complaint Manager | The above, plus cancel, reset, delete and configure |

Segregation of duties is enforced per record: no one approves the investigation
he performed, and no one reviews the closure of a complaint he is responsible
for.

## Documentation

| Document | Content |
|---|---|
| [`docs/00_verification_and_limitations.md`](docs/00_verification_and_limitations.md) | What was verified, what was not, the risk register, the deviations |
| [`docs/01_business_analysis.md`](docs/01_business_analysis.md) | Phase 1 |
| [`docs/02_regulatory_analysis.md`](docs/02_regulatory_analysis.md) | Phase 2 |
| [`docs/03_functional_specification.md`](docs/03_functional_specification.md) | Phase 3 |
| [`docs/04_technical_specification.md`](docs/04_technical_specification.md) | Phase 4, full field reference |
| [`docs/05_architecture_review.md`](docs/05_architecture_review.md) | Phase 5 |
| [`docs/06_test_report.md`](docs/06_test_report.md) | Phase 7 |
| [`docs/07_static_analysis_report.md`](docs/07_static_analysis_report.md) | Phase 8 |
| [`docs/08_validation_report.md`](docs/08_validation_report.md) | Phase 10 and the compliance checklist |
| [`docs/installation_guide.md`](docs/installation_guide.md) | Deployment and troubleshooting |
| [`docs/configuration_guide.md`](docs/configuration_guide.md) | Categories, targets, access, automation |
| [`docs/user_manual.md`](docs/user_manual.md) | Daily use |
| [`docs/administrator_manual.md`](docs/administrator_manual.md) | Operation, monitoring, limitations |
| [`docs/developer_manual.md`](docs/developer_manual.md) | Extension points, the CAPA bridge, pitfalls |
| [`docs/api_documentation.md`](docs/api_documentation.md) | External API and error catalogue |

## Before production use

1. Install on a controlled instance and confirm it loads.
2. Run the test suite under `coverage` and record the result.
3. Run `flake8`, `pylint` and `pylint-odoo`.
4. Perform your own computer system validation, and decide whether the audit
   trail and signature gaps are acceptable for your intended use.

Until those four are done, this is a written deliverable, not validated
software.
