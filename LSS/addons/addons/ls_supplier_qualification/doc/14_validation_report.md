# Phase 9 — Validation Report

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status: **Validation approach defined and supporting evidence prepared.
The module is NOT validated. Validation is performed by the implementing
organisation.**

---

## 9.1 What this document is, and is not

Computer system validation is an activity an organisation performs on its own
installed system, against its own intended use, with its own approvals. It is
not something a supplier can perform on the organisation's behalf by writing a
document.

This report therefore does two things:

1. It states what the module provides **towards** validation: design
   documentation, requirement traceability, an automated test suite, and
   controls that make the system's behaviour verifiable.
2. It states plainly what remains to be done, by whom, and what evidence is
   still missing.

**No part of this document should be read as a statement that the module is
validated, qualified, or compliant.**

## 9.2 Deliverables available as validation input

| Validation deliverable | Where it is, and what it actually is |
|------------------------|--------------------------------------|
| User Requirements Specification | `doc/01_business_analysis.md` covers business objectives, 16 requirements, roles, stories and use cases. It is a **supplier-side** URS. The organisation must review it, accept it, add its own site-specific requirements, and approve it under its own change control. |
| Functional Specification | `doc/03_functional_specification.md`, complete: menus, five state machines, 20 business rules with their enforcement location, notifications, reports, KPIs, filters, wizards. |
| Design Specification | `doc/04_technical_specification.md`, with a model and field inventory generated from the source, plus every SQL and Python constraint. |
| Configuration Specification | `doc/07_configuration_guide.md` describes every configurable value and states which shipped values are proposals requiring approval. |
| Architecture and design review | `doc/05_architecture_review.md`, six findings, two closed in code, three accepted deviations, one open verification point. |
| Test specification | `doc/12_test_report.md`, §7.2 and §7.3: 141 tests with full traceability to the 16 business requirements. |
| Test execution records | **Missing.** The suite was not run. See §9.4. |
| Static analysis records | `doc/13_static_analysis_report.md`: 18 checks executed with 0 findings; three standard linters not run. |
| Traceability matrix | `doc/12_test_report.md`, §7.3. |
| Operating procedures | `doc/08_user_manual.md` and `doc/09_administrator_manual.md` are a basis for SOPs, not SOPs. |
| Validation Plan, Validation Summary Report | **Missing by design.** These are organisation-level documents. |

## 9.3 Suggested risk-based approach

The categorisation below is a recommendation, not a determination. The
organisation decides, based on how it actually uses the module.

**Likely categorisation.** Configurable commercial software with custom code:
the module is an add-on to a commercial platform, delivered configured, and its
categorisation typically follows that of a configurable package with bespoke
elements. Software categorisation frameworks are published by industry bodies
and are not reproduced here.

**Impact on patient safety and product quality.** The module holds the record
of supplier approval and gates purchasing. A failure could allow purchase from
an unqualified source, or could hide that an approval had lapsed. That is a
real, if indirect, quality impact, and it argues for treating the module as
significant rather than peripheral.

**Suggested testing depth by function:**

| Function | Suggested depth | Reason |
|----------|-----------------|--------|
| Approval workflow and its guards | Full OQ and PQ scripts | Directly determines whether a supplier may be used. |
| Expiry handling and the scheduled actions | Full OQ, including a date-shifted PQ | Silent failure is the worst case: nothing happens and nobody notices. |
| Signature log and chain verification | Full OQ, including the tampering-detection test | It is the evidential record. |
| Purchase order control | Full OQ at each of the three levels | It is the operational gate. |
| Assessment scoring | OQ with worked examples reproducing §6 of the configuration guide | Reproducibility of a numeric result. |
| Audit and finding workflow | OQ on the transition guards | Prevents premature closure. |
| Performance scorecard | OQ with one worked calculation | Arithmetic, low risk once verified. |
| Reports | IQ-level check that they render and paginate | Presentation of data verified elsewhere. |
| Configuration models | IQ-level check that starter data loaded | Verified again by use. |

## 9.4 Evidence still required before use

| # | Item | Owner | Status |
|---|------|-------|--------|
| 1 | Installation qualification on the target environment: Odoo version and build, PostgreSQL version, addons path, module version installed | Implementing organisation | Not done |
| 2 | Automated test suite executed, with the count of tests run, passed and failed | Implementing organisation | **Not done** — `doc/12_test_report.md`, §7.1 |
| 3 | Coverage measured and recorded | Implementing organisation | Not done |
| 4 | `flake8`, `pylint`, `pylint-odoo` executed and output attached | Implementing organisation | **Not done** — `doc/13_static_analysis_report.md`, §8.1 |
| 5 | The three verification points of `doc/05_architecture_review.md` §5.8 confirmed | Implementing organisation | Not done |
| 6 | URS reviewed, extended with site requirements, approved | Quality / Validation | Not done |
| 7 | Configuration reviewed and approved; shipped proposals accepted or replaced | Quality | Not done |
| 8 | OQ and PQ scripts written, executed, deviations resolved | Validation | Not done |
| 9 | SOPs written from the manuals and approved | Quality | Not done |
| 10 | Users trained; training records retained | Quality / HR | Not done |
| 11 | The Part 11 gap of `doc/02_regulatory_analysis.md` §2.4 assessed, and the compensating controls documented | Quality / IT | Not done |
| 12 | Periodic review and revalidation triggers defined | Validation | Not done |

## 9.5 Known limitations to carry into the validation file

These are stated in the module documentation and must be reflected in the
organisation's own assessment rather than discovered during an inspection.

| # | Limitation | Reference |
|---|-----------|-----------|
| L-01 | Signing confirms intent by retyping a login; it does **not** re-authenticate the signer. The second identification component must be covered by other documented means. | `doc/02_regulatory_analysis.md` §2.4 |
| L-02 | The framework mapping is an architectural recommendation, not a verified clause-by-clause mapping. | `doc/02_regulatory_analysis.md` §2.1 |
| L-03 | The published ANPP requirements for supplier qualification could not be verified; the module makes no statement about their content. | `doc/02_regulatory_analysis.md` §2.1 |
| L-04 | Field-level change tracking is limited to fields marked `tracking=True`; a general audit trail is a separate module. | `doc/01_business_analysis.md` §1.7 |
| L-05 | Shipped criticality levels, intervals, weights and thresholds are proposals requiring approval. | `doc/07_configuration_guide.md` §1 |
| L-06 | Automatic delivery counters require `purchase_stock`; without it the counters are manual. | `doc/05_architecture_review.md` F-05 |
| L-07 | No upgrade test exists, because this is version 1.0.0. | `doc/12_test_report.md` §7.7 |
| L-08 | Uninstalling the module destroys the signature log along with everything else. | `doc/09_administrator_manual.md` §6 |

## 9.6 Change control after go-live

| Change | Suggested handling |
|--------|--------------------|
| Module version upgrade | Regression test the functions listed in §9.3; verify `noupdate` configuration survived. |
| Odoo platform upgrade | Re-run the full suite; re-verify the three points of §5.8. |
| New category, criterion or template | Configuration change under the organisation's change control. No revalidation of code. |
| Change to weights or thresholds | Configuration change. Note that past evaluations keep their frozen values, which is the intended behaviour and should be stated in the change record. |
| Change to the purchase control level | Configuration change with an operational impact; plan it. |
| Disabling segregation of duties | A documented decision with a quality rationale, not a routine setting change. |

## 9.7 Periodic review

Suggested triggers for reviewing whether the system still performs as intended:
annually; after any Odoo major upgrade; after any module upgrade; after any
finding related to supplier qualification in an internal or external audit;
after any failure of the signature chain verification.

---

**Phase 9 gate: PASS for the preparation of validation support material.**
The module is **not validated**, and this document does not assert that it is.
Twelve evidence items remain outstanding in §9.4, two of which — test execution
and standard linting — are gaps in the supplier's own delivery and are stated as
such. Phase 10 may start.
