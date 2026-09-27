# Life Sciences Suite — Complete Module Collection

**Odoo 19 Community Edition — Layer 3 & Layer 4 Custom Modules**
**Versions and licences:** see each module's `__manifest__.py`.
**Total modules:** 23 (`ls_electronic_signature_test` is a test fixture
and must not be installed in production).

---

## Overview

This archive contains the installable Odoo 19 Community Edition custom modules
of the Life Sciences Suite for organisations operating in pharmaceutical
manufacturing, medical devices, cosmetics, medical plastics and laboratory
environments.

All modules are custom `ls_*` modules. **Every module is standalone:** no
`ls_*` module depends on another `ls_*` module, except the test fixture
`ls_electronic_signature_test`, which depends on `ls_electronic_signature`.

---

## Module List

The dependencies below are the `depends` keys of the manifests (generated from
the manifests on 2026-09-25; the previous table listed inter-module
dependencies that the manifests do not declare — audit finding F-30).

| # | Technical Name | Name | Depends On | Licence |
|---|----------------|------|------------|---------|
| 1 | `ls_audit` | Life Sciences - Audit Management | base, mail, hr | AGPL-3 |
| 2 | `ls_audit_trail` | Life Sciences - Audit Trail | base, mail | AGPL-3 |
| 3 | `ls_calibration` | Life Sciences - Calibration Management | base, web, mail, maintenance | AGPL-3 |
| 4 | `ls_capa` | Life Sciences - CAPA Management | base, mail, project | AGPL-3 |
| 5 | `ls_change_control` | Life Sciences - Change Control | base, mail, hr | AGPL-3 |
| 6 | `ls_complaint` | Life Sciences - Complaint Management | base, mail, product, stock | AGPL-3 |
| 7 | `ls_cosmetics` | Life Sciences - Cosmetics Manufacturing | base, mail, product, stock, mrp | AGPL-3 |
| 8 | `ls_deviation` | Life Sciences - Deviation Management | base, mail, hr, stock, mrp, maintenance | AGPL-3 |
| 9 | `ls_document_management` | Life Sciences - Document Management | base, mail | AGPL-3 |
| 10 | `ls_electronic_signature` | Life Sciences - Electronic Signatures | base, mail | AGPL-3 |
| 11 | `ls_electronic_signature_test` | Life Sciences - Electronic Signatures (test fixture) | ls_electronic_signature | AGPL-3 |
| 12 | `ls_environmental_monitoring` | Life Sciences - Environmental Monitoring | base, mail | AGPL-3 |
| 13 | `ls_import_export` | Life Sciences - Import & Export Compliance | mail, product, stock, uom, account, purchase, sale | AGPL-3 |
| 14 | `ls_lab` | Life Sciences — Laboratory Management | base, mail, product, stock, uom | LGPL-3 |
| 15 | `ls_medical_device` | Life Sciences Suite - Medical Devices | base, mail, product, stock | AGPL-3 |
| 16 | `ls_medical_plastics` | Life Sciences - Medical Plastics | base, mail, product, stock, mrp | AGPL-3 |
| 17 | `ls_pharma` | Life Sciences - Pharmaceutical Manufacturing | base, mail, product, stock, mrp | AGPL-3 |
| 18 | `ls_qms` | Life Sciences QMS | base, mail, hr | AGPL-3 |
| 19 | `ls_recall` | Life Sciences - Recall and Field Action Management | mail, stock | AGPL-3 |
| 20 | `ls_risk_management` | Life Sciences - Risk Management | base, mail | AGPL-3 |
| 21 | `ls_supplier_qualification` | Life Sciences - Supplier Qualification | base, mail, product, purchase | AGPL-3 |
| 22 | `ls_training` | Life Sciences - Training Management | base, mail, hr | AGPL-3 |
| 23 | `ls_validation` | Life Sciences - Validation Management | mail | AGPL-3 |

---

## Installation

### Prerequisites
- Odoo 19 Community Edition
- PostgreSQL database

### Install Order (respecting dependencies)

```bash
# 1. Copy all module folders into your Odoo addons path
# 2. Restart Odoo
# 3. Update Apps List
# 4. Install the full suite in dependency order:

odoo-bin -d mydb -i \
  ls_document_management,\
  ls_qms,\
  ls_capa,\
  ls_audit,\
  ls_deviation,\
  ls_validation,\
  ls_change_control,\
  ls_training,\
  ls_calibration,\
  ls_supplier_qualification,\
  ls_complaint,\
  ls_recall,\
  ls_electronic_signature,\
  ls_audit_trail,\
  ls_risk_management,\
  ls_environmental_monitoring,\
  ls_pharma,\
  ls_medical_device,\
  ls_medical_plastics,\
  ls_cosmetics \
  --test-enable --stop-after-init
```

Or install the entire suite at once (Odoo resolves dependencies automatically):

```bash
odoo-bin -d mydb -i ls_document_management,ls_qms,ls_capa,ls_audit,ls_deviation,ls_change_control,ls_training,ls_validation,ls_calibration,ls_supplier_qualification,ls_complaint,ls_recall,ls_electronic_signature,ls_audit_trail,ls_risk_management,ls_environmental_monitoring,ls_pharma,ls_medical_device,ls_medical_plastics,ls_cosmetics --stop-after-init
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: INDUSTRY MODULES                                  │
│  ls_pharma │ ls_medical_device │ ls_medical_plastics │      │
│  ls_cosmetics                                               │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: LIFE SCIENCES CORE                                │
│  ls_document_management (foundation)                        │
│  ls_qms │ ls_capa │ ls_audit │ ls_deviation                │
│  ls_change_control │ ls_training │ ls_validation           │
│  ls_calibration │ ls_supplier_qualification                │
│  ls_complaint │ ls_recall │ ls_electronic_signature        │
│  ls_audit_trail │ ls_risk_management                       │
│  ls_environmental_monitoring                                │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: NATIVE ODOO 19 CE (base, mail)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Shared Engineering Patterns

All modules follow consistent architecture:
- **Declarative state machines** (`TRANSITIONS` dict as single source of truth)
- **Reusable audit mixin** (`LsAuditMixin` from `ls_document_management`)
- **4-tier RBAC** (viewer → user → approver/coordinator → manager)
- **Multi-company record rules**
- **Mail thread integration** (chatter, activities, followers)
- **Sequences** for automatic reference numbering
- **Demo data** for evaluation
- **Unit tests** for workflow validation
- **QWeb reports** where applicable

---

## Regulatory Alignment

This suite is designed to support implementation of processes aligned with:

- **ISO 9001:2015** — Quality Management Systems
- **ISO 13485:2016** — Medical Devices QMS
- **ISO 14971:2019** — Risk Management for Medical Devices
- **ISO 15378:2017** — GMP for Primary Packaging Materials
- **ISO 22716:2007** — Cosmetics GMP
- **FDA 21 CFR Part 11** — Electronic Records & Signatures
- **FDA 21 CFR Part 820** — Medical Device QSR
- **EU MDR 2017/745** — Medical Device Regulation
- **EU GMP Annex 11** — Computerised Systems
- **ICH Guidelines** — Quality, Safety, Efficacy
- **ANPP (Algeria)** — Pharmaceutical regulatory requirements
- **WHO GMP** — Good Manufacturing Practices

### Absolute Truth Protocol

**Implementation provided. Regulatory compliance requires independent
validation in a real Odoo environment.** No compliance is claimed without
demonstrable evidence. Organizations must conduct their own validation
activities and maintain appropriate documentation.
