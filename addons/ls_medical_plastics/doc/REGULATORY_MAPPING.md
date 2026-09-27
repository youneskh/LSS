# Regulatory Mapping

**Module:** `ls_medical_plastics` · **Version:** 19.0.1.0.0

---

## 1. Statement of limitation

This document maps specific regulatory provisions to specific implemented
features. It is written under a strict evidence rule:

- Where a provision is cited, it is cited because the standard or regulation is
  published and its subject matter is a matter of public record.
- Where the exact clause text or numbering **could not be verified from official
  documentation** in the preparation environment, this is stated explicitly
  rather than approximated.
- **No claim of compliance or certification is made anywhere in this document.**
  A software feature can support a process; only an organisation operating a
  validated system under adequate procedures can be compliant.

**Verification note applying to the whole document:** the preparation
environment had no access to paid standards texts (ISO, and the compendial
chapters of pharmacopoeias are not freely redistributable). Clause *numbering*
for ISO standards is therefore given only where it is widely published in
official ISO catalogue descriptions and scope statements. Where numbering could
not be verified it is omitted and the requirement is described by subject
instead. Readers must confirm every citation against the controlled copy of the
standard held by their organisation.

---

## 2. ISO 15378 — primary packaging materials for medicinal products

ISO 15378 is the standard covering good manufacturing practice requirements for
primary packaging materials for medicinal products, applying ISO 9001 together
with GMP principles. This is the standard of primary relevance to a medical
plastics operation producing container closure components.

**This information could not be verified from official documentation:** the
clause numbering of ISO 15378:2017 could not be confirmed from a primary
source in the preparation environment. The subject areas below are therefore
mapped by subject, not by clause number. Organisations must map to their own
controlled copy.

| Subject area | Implemented by | Enforcement |
|---|---|---|
| Identification and traceability of product | `ls.mp.injection_molding.lot_id`, `ls.mp.injection_molding.material.lot_id` | Traceability wizard resolves lot genealogy in both directions |
| Control of production process parameters | `ls.mp.molding_parameter` with versioned approval; `ls.mp.injection_molding.parameter_spec_version` frozen on the run | `action_start_setup` refuses to proceed without an approved specification |
| Verification at start-up before routine production | Run state `startup_check`; `_missing_startup_parameters`, `_failing_critical_startup_readings` | `action_confirm_startup` raises if readings are missing or a critical parameter is out of tolerance |
| Records of production conditions | `ls.mp.injection_molding.reading` with frozen acceptance criteria | Append-only: `write` and `unlink` overridden; no role holds write/delete in the ACL |
| Control of nonconforming product | `ls.mp.injection_molding.scrap` classified by `ls.mp.scrap.reason`, attributable to `cavity_id` | `_check_scrap_not_exceeding_production`; `requires_investigation` flag |
| Control of production equipment (tooling) | `ls.mp.tool` lifecycle, `ls.mp.tool.cavity`, `ls.mp.tool.maintenance` | `action_place_in_service` requires an active cavity and a qualification date |
| Preventive maintenance of equipment | `maintenance_interval_shots`, `maintenance_interval_months`, `maintenance_status` | `_cron_check_tool_status` flags due and overdue tools daily |
| Competence and authority separation | Five-role implication chain; ORM-level duty separation | `_check_segregation_of_duties`; `action_review` rejects operator and setter |
| Contamination control of materials | `ls.mp.material.grade.drug_contact`, `is_regrind` on consumption lines | `_check_lot_recorded_for_drug_contact` requires a lot for drug-contact grades |

---

## 3. ISO 13485 — quality management for medical devices

Where moulded articles are medical device components, ISO 13485 applies to the
manufacturer's quality management system. ISO 13485:2016 is published; its
subject areas relevant to this module are production and service provision,
control of monitoring and measuring equipment, and traceability.

**This information could not be verified from official documentation:** exact
clause numbering of ISO 13485:2016 could not be confirmed from a primary source
here. The specification document for this suite associates ISO 13485 clause 7.5
with production and service provision and clause 7.6 with monitoring and
measuring equipment; those associations originate from the suite specification,
not from the standard text, and must be confirmed by the reader.

| Subject area | Implemented by |
|---|---|
| Control of production | Approved parameter specification frozen onto each run |
| Traceability of components | Produced lot to material lot to tool to cavity |
| Records retained and protected from alteration | Closed runs frozen by `write` override; readings append-only |
| Equipment maintenance records | `ls.mp.tool.maintenance` — completed events cannot be deleted |

Calibration of measuring equipment is **not** implemented here. Parameter units
are recorded as free text and the module does not manage instrument
calibration status. See `doc/DEVIATIONS_AND_LIMITATIONS.md`.

---

## 4. FDA 21 CFR Part 11 — electronic records and signatures

Part 11 sets requirements for electronic records and electronic signatures
where they are used in place of paper records under FDA predicate rules.

### 4.1 What this module does *not* provide

**This module does not implement electronic signatures and must not be
described as Part 11 compliant.** Specifically it does not provide:

- signature manifestations carrying the printed name, date/time and meaning of
  the signing;
- re-authentication at the point of signing;
- signature/record linking that cannot be excised or transferred;
- a comprehensive, secure, computer-generated, time-stamped audit trail of all
  create/modify/delete operations across records.

Where those controls are required, they must be provided by a dedicated module.
The Life Sciences Suite specification allocates them to
`ls_electronic_signature` and `ls_audit_trail`, which this module deliberately
does **not** depend on (see the dependency deviation in
`doc/DEVIATIONS_AND_LIMITATIONS.md`).

### 4.2 What this module does contribute

| Part 11 subject | Contribution of this module |
|---|---|
| Protection of records to enable accurate retrieval throughout the retention period | Closed runs are frozen; readings and completed maintenance events cannot be deleted |
| Limiting system access to authorised individuals | Five-role model with ACL enforcement, plus global multi-company record rules |
| Use of operational system checks to enforce permitted sequencing of steps | State machines on runs, specifications and tools reject out-of-sequence transitions |
| Use of authority checks | Segregation of duties enforced in ORM methods, not only in the interface |
| Record changes shall not obscure previously recorded information | Readings are append-only; corrections supersede rather than overwrite, and both values print on the run record |

The final row is the one control in this list that the module implements
thoroughly, and it is the design centre of the reading model.

---

## 5. EudraLex Volume 4 Annex 1 and data integrity expectations (ALCOA+)

The ALCOA+ attributes are a widely used articulation of data integrity
expectations by regulators including the FDA, EMA and MHRA.

| Attribute | Implementation | Honest gap |
|---|---|---|
| **A**ttributable | `recorded_by_id`, `operator_id`, `setter_id`, `reviewed_by_id`, `closed_by_id` | Identity is an Odoo account, not a signature |
| **L**egible | Structured fields; values print on the run record | — |
| **C**ontemporaneous | `capture_date` defaults to capture time and is readonly | The system does not prevent late entry of an earlier event |
| **O**riginal | Readings store the measured value and frozen criteria | Values are keyed in by a person, not acquired from the machine |
| **A**ccurate | Range checks against frozen criteria; `in_tolerance` computed | Accuracy of the keyed value is not verifiable by the system |
| **C**omplete | Superseded readings are retained and printed | — |
| **C**onsistent | Sequenced references; state machines | — |
| **E**nduring | Deletion blocked on closed runs, readings, completed maintenance | Database backup and retention are the operator's responsibility |
| **A**vailable | List, search, pivot views and PDF reports | — |

---

## 6. Algeria — ANPP and BPF

The suite specification lists ANPP requirements and Algerian GMP (BPF) as
applicable frameworks for pharmaceutical operations.

**This information could not be verified from official documentation.** No
official ANPP publication or Algerian BPF text was accessible in the
preparation environment. Consequently:

- **No ANPP or BPF requirement is claimed to be met by this module.**
- No ANPP-specific field, code list or report has been implemented, because
  implementing one would require inventing requirements.
- The regulatory reference fields (`ls.mp.material.grade.regulatory_reference`,
  `ls.mp.component.specification_reference`) are shipped **empty** and free-text
  precisely so that an organisation can populate them from the authoritative
  national texts it holds.

Any organisation subject to ANPP oversight must perform its own gap assessment
against the current national requirements.

---

## 7. Summary of the honest position

| Framework | Status |
|---|---|
| ISO 15378 | Supports several subject areas; clause numbering unverified |
| ISO 13485 | Supports production control and traceability subjects; calibration not implemented |
| 21 CFR Part 11 | **Not implemented** for signatures and audit trail; contributes access control, sequencing and non-obscuring of prior records |
| ALCOA+ | Substantially supported with the gaps stated in section 5 |
| ANPP / BPF | **Unverified — no claim made** |

The correct summary sentence for a validation file is: *this module implements
production controls that an organisation may use as part of demonstrating
compliance; the module itself demonstrates nothing.*
