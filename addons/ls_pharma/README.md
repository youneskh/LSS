# Life Sciences Suite — Pharmaceutical Manufacturing (`ls_pharma`)

Odoo 19 Community Edition module for regulated pharmaceutical manufacturing:
manufacturing batches, batch production and control records, batch release,
active ingredient and excipient master data, stability studies, GS1
serialisation and Common Technical Document dossiers.

- **Technical name:** `ls_pharma`
- **Version:** 19.0.1.0.0
- **Licence:** AGPL-3.0 or later
- **Author:** Life Sciences Suite Architecture Team
- **Depends on:** `base`, `mail`, `product`, `stock`, `mrp`

---

## Read this first

**This module does not make an organisation compliant with any regulation.**
It records data and enforces process controls that a manufacturer needs in
order to operate under a quality system. Compliance depends on the
manufacturer's procedures, its validation activities, the training of its
staff and the decisions of its quality unit. Nothing in this module has been
certified by any regulatory authority.

**Delivery status: CONDITIONAL PASS.** What was verified and what was not is
stated in `doc/13_validation_report.md` and repeated in section
"Honest delivery gate" below. The short form: the sources compile, the XML is
well formed and a purpose-built static checker reports no finding, but the
tests shipped with the module **have never been executed**, no coverage has
been measured, `flake8` and `pylint-odoo` have not been run, and the module
has **never been installed against a live Odoo 19 instance**.

---

## What the module does

| Area | What is recorded |
|---|---|
| Batches | Planned, in-process, manufactured, quarantined, reviewed, released or rejected batches, with components, major equipment, co-products, yields and expiry |
| Batch records | Processing steps, in-process and laboratory controls, line clearances, labelling reconciliation, samples, discrepancies, execution and quality review |
| Release | An append-only decision of the quality unit, covered by a SHA-256 integrity digest, with an eight-point checklist bound to its regulatory basis |
| Materials | Active pharmaceutical ingredients and excipients, their pharmacopoeial standard, potency basis, approved manufacturers and qualification state |
| Stability | Studies, storage conditions, a schedule generated from ICH Q1A(R2), samples, time points and results, with significant-change tracking |
| Serialisation | GS1 unique identifiers with a modulo-10 check digit, unpredictable serial numbers, and aggregation under Serial Shipping Container Codes |
| Regulatory | Common Technical Document dossiers with the ICH M4(R4) and M4Q structure shipped as a reusable template |

## What the module deliberately does not do

- It is **not** a 21 CFR Part 11 electronic signature system. The release
  digest detects modification; it does not manifest a signature, and the
  module implements none of the identification, authentication or signature
  controls of that Part.
- It does **not** render barcode symbols. It produces GS1 element strings,
  which a symbology encoder consumes.
- It does **not** generate, validate or transmit an electronic submission
  sequence. It tracks the preparation status of dossier sections.
- It does **not** depend on any other module of the Life Sciences Suite. See
  `doc/15_deviation_register.md` for why.

## Documentation

| Document | Content |
|---|---|
| `doc/01_business_analysis.md` | Objectives, stakeholders, roles, user stories, scope, risks |
| `doc/02_regulatory_analysis.md` | Every provision relied upon, with its source |
| `doc/03_functional_specification.md` | Menus, workflows, state machines, business rules |
| `doc/04_technical_specification.md` | Architecture, models, security, data, jobs |
| `doc/05_architecture_review.md` | Review against SOLID, DRY, KISS and upgrade safety |
| `doc/06_development_report.md` | What was built, and the coding rules applied |
| `doc/07_test_report.md` | The test suite and its honest execution status |
| `doc/08_static_analysis_report.md` | The static checker, its negative controls, its results |
| `doc/09_user_manual.md` | Day-to-day use, by role |
| `doc/10_administrator_manual.md` | Configuration, groups, scheduled actions, backups |
| `doc/11_developer_manual.md` | Extension points and conventions |
| `doc/12_api_reference.md` | Generated inventory of models, fields and methods |
| `doc/13_validation_report.md` | Delivery gate, residual risks, outstanding qualification |
| `doc/14_regulatory_traceability_matrix.md` | Provision to field or constraint |
| `doc/15_deviation_register.md` | Every departure from the suite specification |
| `doc/16_installation_and_configuration_guide.md` | Installation and first configuration |
| `doc/CHANGELOG.md`, `doc/RELEASE_NOTES.md` | History and release notes |
| `doc/00_final_validation_checklist.md` | The ten phase gates and their verdicts |

## Installation in brief

```bash
# 1. place the module on the addons path
cp -r ls_pharma /path/to/addons/

# 2. restart the server and update the module list
odoo-bin -u base -d <database>

# 3. install
odoo-bin -i ls_pharma -d <database>
```

Full instructions, including the first configuration of the GS1 company
prefix, are in `doc/16_installation_and_configuration_guide.md`.

## Re-running the checks

```bash
# offline static analysis, from the directory that contains the module
python3 ls_pharma/static_check.py ls_pharma

# the test suite, against a real server
odoo-bin -d <database> -i ls_pharma --test-enable --stop-after-init
```

## Honest delivery gate

| Item | Status | Evidence |
|---|---|---|
| Python syntax | Verified | `python3 -m py_compile` over every source file |
| XML well-formedness | Verified | `lxml.etree.parse` over every XML file |
| Internal consistency | Verified | `static_check.py`, 0 findings, validated by fault injection |
| Tests written | Yes | 11 test modules under `tests/` |
| Tests executed | **No** | No Odoo runtime and no PostgreSQL in the build environment |
| Coverage measured | **No** | Cannot be measured without executing the tests |
| `flake8` / `pylint-odoo` | **Not run** | No network access to install them |
| Installed on Odoo 19 | **No** | No Odoo runtime in the build environment |
| IQ / OQ / PQ | **Not performed** | Listed as outstanding in `doc/13_validation_report.md` |

No pass rate and no coverage percentage is claimed anywhere in this
documentation, because none was measured.
