# Life Sciences — Environmental Monitoring

Environmental monitoring programme management for regulated manufacturing areas
on **Odoo 19 Community Edition**.

**Version:** 19.0.1.0.0
**Licence:** AGPL-3.0
**Depends on:** `base`, `mail`
**Delivery status:** CONDITIONAL PASS — see [Status](#status) before deploying

---

## What it does

Manages the full cycle of a routine environmental monitoring programme:

1. **Define the programme** — areas, classification grades, parameters,
   methods and sampling points, each carrying the rationale for its selection.
2. **Set acceptance criteria** — alert, action and specification limits per
   sampling point and parameter, versioned and requiring approval by a second
   person.
3. **Schedule** — approved monitoring plans generate the samples that fall due,
   idempotently, by hand or on a daily job.
4. **Execute** — record collection, analysis and results, with each step
   attributed to the user who performed it.
5. **Evaluate** — results are compared automatically against the approved
   limits, and the thresholds applied are copied onto the result.
6. **Handle breaches** — action and specification exceedances open an excursion
   with impact assessment, investigation and controlled closure.
7. **Trend** — descriptive analysis of released results over a period, with
   exceedance rates, summary statistics and a direction indicator.

---

## What it deliberately does not do

Read this before assuming coverage.

- **No numeric limits are shipped.** Every threshold is configured and approved
  by your organisation, which owns the justification for it.
- **No electronic signatures.** Approval records who approved and when. That is
  not a 21 CFR Part 11 compliant signature.
- **No field-level audit trail.** Change history uses Odoo's standard tracking.
- **No corrective action management.** Excursions carry a free-text external
  reference and an overridable hook for a module that provides it.
- **No instrument interface and no continuous monitoring.** Results are entered
  by a person.
- **No product disposition.** Product impact is assessed and recorded; no batch
  is released, rejected or quarantined by this module.
- **No statistical significance testing.** Trend direction is a descriptive
  comparison of two halves of a series, and says so in the interface.

The full list, with reasons, is in
[`doc/regulatory_mapping.md`](doc/regulatory_mapping.md) section 4.

---

## Status

This module has **never been installed against a live Odoo 19 instance**.

| Activity | Result |
|---|---|
| Python syntax | Verified — all files parse |
| XML well-formedness | Verified — all 23 files parse |
| Custom static analysis | PASS, with the checker proven against 19 injected fault classes |
| Pure-logic tests | **38 executed, 38 passed**, 100% measured statement coverage |
| Database-backed tests | **104 written, 0 executed** |
| Installation on Odoo 19 | **Not performed** |
| `flake8` / `pylint-odoo` | **Not performed** — not installed, no network access |

**Highest remaining risk:** the `<chatter/>` element used in seven form views
was carried forward as a suite convention and was not re-verified against
official Odoo 19 documentation. If it is wrong, the module will fail to install.
Check this first. See [`doc/deviations.md`](doc/deviations.md) section B7.

Full detail: [`doc/test_report.md`](doc/test_report.md).

---

## Regulatory position

This module **supports** the implementation of environmental monitoring
processes. It does not certify compliance with any framework.

Provisions whose text was verified during development, and which are mapped to
specific features:

- 21 CFR 211.42(c)(10)(iv), 211.46(b), 211.113(b) — verified via eCFR and FDA
  guidance
- EU GMP Annex 1 (2022), published August 2022, effective 25 August 2023 with
  section 8.123 effective 25 August 2024 — verified via multiple independent
  sources

Frameworks referenced but **not verified**, and therefore not claimed:
ISO 14644, ISO 22716, ISO 13485 clause text, WHO GMP, and ANPP or Algerian BPF
requirements. No numeric limit from any standard is embedded in this module.

Full mapping with per-provision verification status:
[`doc/regulatory_mapping.md`](doc/regulatory_mapping.md).

---

## Roles

| Role | May do |
|---|---|
| **Viewer** | Read everything; change nothing |
| **Technician** | Create samples, record collection, enter results, run sample generation |
| **Manager** | Everything, including approving limits and plans, reviewing and approving samples, closing excursions, reviewing trend analyses |

Segregation of duties is enforced in the model layer, not only in the interface:

- a limit or plan is approved by someone other than its author;
- a sample is reviewed and approved by someone other than the person who
  entered the results, and only by a manager;
- an excursion is closed by someone other than its owner.

---

## Installation

```bash
cp -r ls_environmental_monitoring /path/to/addons/
./odoo-bin -u ls_environmental_monitoring -d <database>
```

Then follow [`doc/installation_guide.md`](doc/installation_guide.md) and
[`doc/configuration_guide.md`](doc/configuration_guide.md). The module ships no
configuration data, so nothing works until areas, parameters, sampling points
and limits have been created.

---

## Documentation

| Document | Contents |
|---|---|
| [`doc/installation_guide.md`](doc/installation_guide.md) | Installation and post-install verification |
| [`doc/configuration_guide.md`](doc/configuration_guide.md) | Setting up a programme from nothing |
| [`doc/user_manual.md`](doc/user_manual.md) | Day-to-day operation |
| [`doc/administrator_manual.md`](doc/administrator_manual.md) | Roles, jobs, multi-company |
| [`doc/developer_manual.md`](doc/developer_manual.md) | Architecture and extension points |
| [`doc/api_reference.md`](doc/api_reference.md) | Generated from source; 18 models, 254 fields |
| [`doc/regulatory_mapping.md`](doc/regulatory_mapping.md) | Provision-by-provision mapping and verification status |
| [`doc/deviations.md`](doc/deviations.md) | Every departure from specification, with rationale |
| [`doc/test_report.md`](doc/test_report.md) | What was run, what was not |
| [`doc/validation_report.md`](doc/validation_report.md) | Delivery gate and outstanding qualification |
| [`doc/CHANGELOG.md`](doc/CHANGELOG.md) | Release history |

---

## Verifying the delivery yourself

```bash
python3 ls_environmental_monitoring/static_check.py   # expect: RESULT: PASS
python3 negative_control.py                           # expect: 19/19 CAUGHT
```

---

## Credits

**Author:** Life Sciences Suite Architecture Team
**Licence:** AGPL-3.0 or later
