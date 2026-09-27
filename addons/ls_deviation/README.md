# Life Sciences — Deviation Management (`ls_deviation`)

Record, classify, investigate, disposition and close GxP deviations in
**Odoo 19 Community Edition**.

**Licence:** AGPL-3 · **Version:** 19.0.1.0.0

---

## ⚠ Read first

This module has **never been installed or executed against a running Odoo
instance.** It was built in an environment without Odoo and without network
access to a database.

Static checks pass (Python syntax, XML well-formedness, view-field
cross-validation, manifest and reference integrity). The 92 automated tests
were **written but not run**, and `flake8`/`pylint-odoo` were **not run**
because they could not be installed.

Read [`docs/00_VERIFICATION_STATUS.md`](docs/00_VERIFICATION_STATUS.md) before
doing anything else with this module. Install into a scratch database first.

---

## What it does

A deviation is a departure from an approved procedure, specification or
expected outcome. This module enforces a controlled path from reporting to
closure:

```
Reported → Assessed → Investigation → Disposition → CAPA Required → Closed
                                                  ↘─────────────────↗
```

with `Cancelled` as a traceable terminal state and send-back transitions for
rework.

### Enforced, not merely offered

| Gate | Rule |
|---|---|
| Leaving **Reported** | Severity, impact assessment narrative and assigned investigator required |
| Leaving **Assessed** | At least one investigation record must exist |
| Leaving **Investigation** | All investigations complete; **extension rationale mandatory**; a product disposition required where impact was assessed |
| Completing an investigation | Findings **and** root cause both required |
| Approving a disposition | Manager group only — the proposer cannot self-approve |
| **Closing** | Conclusions **and** follow-up required; blocked by open actions or unapproved dispositions |
| Changing a target date | Only via wizard, only later, justification mandatory |
| Deleting | Blocked past Reported — cancel instead, with a reason |
| Transition log | Append-only; rejects write and unlink for **every** user including the superuser |

### Regulatory basis for the unusual gates

Three design decisions come directly from verified regulation rather than
convention:

- **Mandatory `justification`** — 21 CFR 211.100(b): *any deviation from the
  written procedures shall be recorded and justified.*
- **Mandatory extension rationale and "other batches evaluated"** —
  21 CFR 211.192: the investigation *shall extend to other batches of the same
  drug product and other drug products* that may be associated. The rationale
  is required **even when the conclusion is that no extension was needed**,
  because failure to extend is a recurring inspection finding.
- **Mandatory conclusions and follow-up at closure** — 21 CFR 211.192: a
  written record of the investigation *shall include the conclusions and
  follow-up.*

No claim of compliance or certification is made. See
[`docs/02_regulatory_analysis.md`](docs/02_regulatory_analysis.md).

---

## Installation

```bash
odoo -d <scratch_database> -i ls_deviation --stop-after-init
```

Depends on `base`, `mail`, `hr`, `stock`, `mrp`, `maintenance`.

**No user is granted access at install.** Assign at least one user to
*Deviation Manager* immediately afterwards, or the application is
inaccessible. This is deliberate — see
[`docs/08_installation_and_configuration.md`](docs/08_installation_and_configuration.md).

Run the tests:

```bash
odoo --test-enable --test-tags ls_deviation -d <scratch_db> -i ls_deviation --stop-after-init
```

---

## Roles

| Group | Can |
|---|---|
| Deviation Viewer | Read |
| Deviation Reporter | Create; edit own records while Reported |
| Deviation Investigator | Edit any open record; investigate; propose dispositions |
| Deviation Manager (QA) | Approve dispositions; close; cancel; configure |

Strictly hierarchical — assign only the highest applicable.

---

## What it deliberately does not do

- **No CAPA lifecycle.** A `capa_reference` field and a documented bridge-module hook only. `ls_capa` does not exist.
- **No 21 CFR Part 11 electronic signature.** Approvals are ordinary authenticated writes. The transition log is explicitly documented as *not* a signature record.
- **No stock movement on disposition.** A "Destroy" decision records the decision; scrapping the quant is a separate inventory transaction.
- **No dependency on `ls_qms`.** It does not exist. This module declares its own root menu with a comment explaining how to reparent it later.

---

## Documentation

| Document | Contents |
|---|---|
| [`00_VERIFICATION_STATUS.md`](docs/00_VERIFICATION_STATUS.md) | **Start here.** What is proven, what is not, residual risks |
| [`01_business_analysis.md`](docs/01_business_analysis.md) | Objectives, requirements, roles, stories, scope, risks |
| [`02_regulatory_analysis.md`](docs/02_regulatory_analysis.md) | Verified citations and their design consequences |
| [`03_functional_specification.md`](docs/03_functional_specification.md) | Navigation, state machine, business rules, reports |
| [`04_technical_specification.md`](docs/04_technical_specification.md) | Models, fields, constraints, security, tree |
| [`05_architecture_review.md`](docs/05_architecture_review.md) | SOLID/DRY/KISS review, 9 findings, known weaknesses |
| [`06_test_plan.md`](docs/06_test_plan.md) | 92 tests by area; coverage position |
| [`07_static_analysis_report.md`](docs/07_static_analysis_report.md) | What was run, what was not, negative control |
| [`08_installation_and_configuration.md`](docs/08_installation_and_configuration.md) | Install, roles, configuration, upgrade |
| [`09_user_and_admin_manual.md`](docs/09_user_and_admin_manual.md) | User, administrator and developer manuals |
| [`10_validation_checklist.md`](docs/10_validation_checklist.md) | 20-item pre-release checklist, all open |
| [`CHANGELOG.md`](docs/CHANGELOG.md) | Release notes |

---

## Odoo 19 API notes

Six breaking changes from Odoo ≤18 were verified against official
documentation and applied: `models.Constraint` instead of `_sql_constraints`;
`<list>` instead of `<tree>`; `<chatter/>` instead of `oe_chatter`;
`<t t-name="card">` instead of `kanban-box`; `res.groups.privilege` with
`privilege_id` instead of `category_id`; `_read_group` instead of
`read_group`.
