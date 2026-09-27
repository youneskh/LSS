# ls_calibration — Analysis and Functional Specification

Phases 1 to 3 of the Life Sciences Suite development framework.

---

## Truth Protocol statement

Every regulatory citation in this document names the instrument, the clause
and what that clause requires. Where a requirement could not be read from an
official publication available to the author, this is stated explicitly rather
than paraphrased from memory. Nothing in this document asserts that the module
achieves compliance with any framework.

**Sources that could not be consulted:** the full normative text of
ISO 9001:2015, ISO 13485:2016, ISO 10012:2003 and ISO/IEC 17025:2017 is sold
under licence and was not available. Clause numbers and subject matter below
are drawn from the publicly published scope descriptions and clause listings of
those standards. **The detailed wording of the requirements could not be
verified from official documentation.** Implementers must read the standards
themselves before relying on any mapping in this document.

**ANPP (Algeria):** no official ANPP publication setting out calibration
requirements was available. **This information could not be verified from
official documentation.** No ANPP-specific behaviour is implemented, and none
is claimed.

---

# PHASE 1 — BUSINESS ANALYSIS

## 1.1 Business objectives

| # | Objective |
|---|---|
| BO-1 | Maintain a single authoritative register of every measuring instrument whose accuracy affects product quality, patient safety or data integrity. |
| BO-2 | Ensure that no such instrument is used beyond its calibration due date without that fact being visible. |
| BO-3 | Record calibration results in a form that survives inspection: attributable, contemporaneous, complete and unalterable after approval. |
| BO-4 | Ensure that a measuring instrument found out of tolerance triggers an assessment of the product and data generated since its last good calibration. |
| BO-5 | Demonstrate metrological traceability by recording which reference standard was used and where that standard's own traceability comes from. |
| BO-6 | Separate the people who perform, review and approve a calibration. |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|---|---|
| BR-1 | Register instruments with identification, location, measuring range and responsible person. | BO-1 |
| BR-2 | Classify each instrument by criticality and by whether it is used for Good Practice purposes. | BO-1, BO-4 |
| BR-3 | Define, per instrument, the points at which it is verified and the tolerance at each point. | BO-3 |
| BR-4 | Define an approved calibration interval per instrument and generate the resulting schedule. | BO-2 |
| BR-5 | Report each instrument as OK, due soon, overdue or never calibrated. | BO-2 |
| BR-6 | Capture as-found and as-left measured values per point and evaluate each against its limits. | BO-3 |
| BR-7 | Record which reference standards were used and their traceability certificates. | BO-5 |
| BR-8 | Route each calibration through review and approval by users distinct from the performer. | BO-6 |
| BR-9 | Prevent modification or deletion of an approved calibration record. | BO-3 |
| BR-10 | Raise an out-of-tolerance event on an as-found failure and withdraw the instrument from use. | BO-4 |
| BR-11 | Drive each out-of-tolerance event through impact assessment, disposition and closure. | BO-4 |
| BR-12 | Issue internal calibration certificates and store external ones. | BO-3, BO-5 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|---|---|
| Metrology / calibration function | Performs calibrations, maintains the instrument register. |
| Quality Assurance | Reviews and approves calibration records, assesses out-of-tolerance events. |
| Quality Control laboratory | Depends on calibrated instruments for valid test results. |
| Production | Depends on calibrated process instrumentation. |
| Engineering / Maintenance | Owns the physical assets and their availability. |
| Regulatory Affairs | Presents calibration evidence during inspection. |
| Validation | Qualifies the system itself; consumes calibration status as an input. |
| External calibration providers | Perform calibrations and issue certificates. |

## 1.4 User roles

| Role | Group | Capability |
|---|---|---|
| Viewer | `group_ls_calibration_viewer` | Reads everything, changes nothing. |
| Technician | `group_ls_calibration_technician` | Creates calibration records, enters readings, marks performed, submits for review. |
| Approver | `group_ls_calibration_approver` | Reviews and approves records, approves plans, assesses out-of-tolerance events. |
| Manager | `group_ls_calibration_manager` | All of the above, plus master data, reference standards, plan closure and deletion of draft data. |

## 1.5 User stories

| # | Story |
|---|---|
| US-1 | As a metrology technician, I register a new balance with its range and calibration points so it can be scheduled. |
| US-2 | As a metrology technician, I see which instruments are overdue so I can prioritise my week. |
| US-3 | As a metrology technician, I enter as-found readings and immediately see which points are out of tolerance. |
| US-4 | As a metrology technician, I adjust an instrument and enter as-left readings so the record shows the correction. |
| US-5 | As a QA reviewer, I review a completed calibration and either approve it or return it with a reason. |
| US-6 | As a QA reviewer, I cannot approve a calibration I performed myself. |
| US-7 | As QA, I am told which product batches fall in the affected period when an instrument is found out of tolerance. |
| US-8 | As QA, I cannot close an out-of-tolerance event with a confirmed product impact until a corrective action is referenced. |
| US-9 | As a manager, I generate next year's calibration schedule from the approved plans in one operation. |
| US-10 | As an auditor, I open an approved record and confirm it cannot have been edited since approval. |
| US-11 | As a manager, I register the traceability certificate of each reference standard and see when it expires. |
| US-12 | As a metrology technician, I print a calibration certificate for an approved calibration. |

## 1.6 Use cases

| # | Use case | Primary actor | Outcome |
|---|---|---|---|
| UC-1 | Register instrument | Technician | Instrument in `draft`, points defined. |
| UC-2 | Place instrument in service | Approver | Instrument in `in_service`; refused if it has no calibration point. |
| UC-3 | Create and approve a calibration plan | Approver | Plan in `approved`; refused if another approved plan overlaps. |
| UC-4 | Generate scheduled calibrations | Technician | Draft records created up to a horizon date. |
| UC-5 | Execute a calibration | Technician | Readings entered; record `performed`. |
| UC-6 | Review and approve | Approver | Record `approved`; instrument due date refreshed. |
| UC-7 | Reject a calibration | Approver | Record `rejected` with a recorded reason; returns to data entry. |
| UC-8 | Handle an out-of-tolerance result | Approver, Manager | Event raised, instrument quarantined, impact assessed, event closed. |
| UC-9 | Issue a certificate | Approver | Certificate created against an approved record. |
| UC-10 | Retire an instrument | Manager | Instrument `retired` and archived; history preserved. |

## 1.7 Functional scope

In scope: instrument register; instrument categories; calibration points and
tolerances; reference standards and their traceability; calibration plans;
schedule generation; calibration execution with as-found and as-left readings;
result aggregation; review and approval with segregation of duties;
immutability after approval; out-of-tolerance events with impact assessment and
disposition; internal and external certificates; calibration status reporting;
three scheduled actions; two QWeb reports; multi-company isolation.

## 1.8 Out of scope

| Item | Why |
|---|---|
| Electronic signatures under 21 CFR Part 11 | Delivered by `ls_electronic_signature`. Approval here is a user, a timestamp and a tracked message, which is **not** an electronic signature. |
| Field-level audit trail with hash chaining | Delivered by `ls_audit_trail`. This module relies on `mail.thread` tracking, which is a change log, not a tamper-evident audit trail. |
| CAPA workflow | Delivered by `ls_capa`. Referenced here as text only. |
| Document control of calibration procedures | Delivered by `ls_document_management`. Referenced here as text only. |
| Batch and lot identification for impact assessment | Requires a manufacturing application. Recorded here as text. |
| Preventive maintenance scheduling | Distinct discipline from calibration. |
| Direct instrument data acquisition | Requires interfacing outside the scope of an ERP module. |
| Measurement uncertainty budget calculation | Requires a metrology engine; the standard's uncertainty is recorded, not propagated. |
| Statistical drift analysis and interval optimisation | Deferred; the data model supports it but no algorithm is shipped. |

## 1.9 Risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R-1 | The Odoo 19 Maintenance application may not exist in Community Edition. | Installation failure. | No dependency declared; instrument register is native to this module. |
| R-2 | The `ir.rule` group field name in Odoo 19 is unverified. | Installation failure on a data file. | All shipped record rules are global; role restriction uses ACLs and ORM checks. |
| R-3 | The `res.users` groups field name in Odoo 19 is unverified. | Runtime failure in code or tests. | `has_group()` used in code; `new_test_user()` used in tests; the token `groups_id` is banned by the static checker. |
| R-4 | Percentage tolerance misread as a 0-to-1 ratio. | Silent 100-fold error in acceptance limits. | Explicit semantics documented, enforced by `test_percent_is_not_a_ratio`. |
| R-5 | A zero measurement mistaken for an absent one. | A valid zero reading ignored, or an absent reading treated as a pass at zero. | Separate `*_recorded` boolean flags; `test_zero_is_a_valid_measurement`. |
| R-6 | Acceptance criteria changed after a calibration was approved. | Retroactive alteration of a pass/fail basis. | `ls.calibration.point.write` freezes acceptance fields once used in a committed record. |
| R-7 | Approval by the same person who performed the work. | Loss of independent verification. | Enforced in `_check_segregation_of_duties` at ORM level, not only in the UI. |
| R-8 | Module never installed against a live Odoo 19. | Unknown runtime defects. | Declared openly in the delivery gate; installation qualification is assigned to the receiving team. |

## 1.10 Success criteria

| # | Criterion | Verified by |
|---|---|---|
| SC-1 | Python compiles, XML is well-formed, static checks are clean. | `tools/static_check.py`, `py_compile`, `lxml` |
| SC-2 | Every model has access-rights coverage for every group. | Static checker rule 6 |
| SC-3 | Segregation of duties cannot be bypassed through the ORM. | `test_segregation_enforced_at_orm_level` |
| SC-4 | An approved record rejects every data write. | `test_approved_record_is_immutable` |
| SC-5 | All three tolerance conventions compute correct limits. | `test_tolerance.py` |
| SC-6 | An as-found failure raises an event and quarantines the instrument. | `test_oot_quarantines_the_instrument` |
| SC-7 | Every deviation from the suite specification is declared. | `docs/DEVIATIONS.md` |

**PHASE 1 GATE: PASS**

---

# PHASE 2 — REGULATORY ANALYSIS

## 2.1 Method and its limits

Each row below names a framework, the clause understood to bear on calibration,
and the module element that supports implementation. **Supports implementation
is not compliance.** Compliance additionally requires written procedures,
trained personnel, a validated system and management oversight, none of which
software supplies.

## 2.2 Frameworks applicable to this module

### FDA 21 CFR Part 211 — Current Good Manufacturing Practice for Finished Pharmaceuticals

`21 CFR 211.68` addresses automatic, mechanical and electronic equipment.
`21 CFR 211.160(b)(4)` addresses the calibration of instruments, apparatus,
gauges and recording devices at suitable intervals in accordance with an
established written programme.

| Provision subject | Module element |
|---|---|
| Established written calibration programme | `ls.calibration.plan` with `procedure_reference` and an approval state |
| Suitable intervals | `calibration_interval_value` / `calibration_interval_uom` on instrument and plan |
| Records of calibration | `ls.calibration.record`, immutable after approval |
| Equipment not meeting specification | `ls.calibration.oot` with impact assessment and disposition |

**Verification status:** the section numbers and their subject matter are as
published in the Code of Federal Regulations. The exact operative wording was
not quoted and **could not be verified from official documentation** in this
build environment. Implementers must read the current CFR text.

### FDA 21 CFR Part 820 — Quality System Regulation (medical devices)

`21 CFR 820.72` addresses inspection, measuring and test equipment, including
calibration, calibration standards and calibration records.

| Provision subject | Module element |
|---|---|
| Calibration procedures with accuracy and precision limits | `ls.calibration.point` tolerance definition |
| Provision for remedial action when limits are not met | `ls.calibration.oot` state machine |
| Calibration standards traceable to national or international standards | `ls.calibration.standard.traceability_reference`, `issuing_body` |
| Where no such standards exist, an independent reproducible basis | `ls.calibration.standard.description` records the basis as text |
| Records identifying equipment, date, person and next due date | `ls.calibration.record` fields; `ls.calibration.certificate` |

**Note on the QMSR transition.** The FDA Quality Management System Regulation,
which aligns Part 820 with ISO 13485:2016, took effect in February 2026. This
is after the author's training-data cutoff and is stated here as a known change
rather than as a verified reading of the final rule. Implementers must confirm
which text applies to them.

### EU GMP — EudraLex Volume 4

Chapter 3 addresses premises and equipment; Chapter 4 addresses documentation.
Annex 15 addresses qualification and validation and is where calibration status
as a prerequisite to qualification arises.

| Subject | Module element |
|---|---|
| Equipment calibrated at defined intervals | Plan and interval fields |
| Calibration status visible to users | `calibration_status`, instrument list decorations, status action |
| Records retained | Immutability and deletion prevention |

**Verification status:** clause subject matter as published by the European
Commission. Operative wording **could not be verified from official
documentation**.

### ISO 13485:2016 — Medical devices, quality management systems

Clause 7.6 addresses the control of monitoring and measuring equipment.

| Subject | Module element |
|---|---|
| Calibrate or verify at specified intervals against traceable standards | Plan, interval, `standard_ids` |
| Record the basis used for calibration where no standard exists | `ls.calibration.standard.description` |
| Assess and record the validity of previous measuring results when equipment is found non-conforming | `ls.calibration.oot`: `affected_period_start`, `affected_period_end`, `impact_assessment`, `affected_batches` |
| Take appropriate action on the equipment and any product affected | `disposition`, automatic quarantine of the instrument |
| Maintain records of calibration results | `ls.calibration.record` |

Clause 7.6's requirement to assess previously recorded results is the single
requirement that shapes the design of `ls.calibration.oot` most directly.

### ISO 9001:2015 — Quality management systems

Clause 7.1.5 addresses monitoring and measuring resources; 7.1.5.2 addresses
measurement traceability.

| Subject | Module element |
|---|---|
| Calibrated or verified against traceable standards at defined intervals | Plan, `standard_ids` |
| Identified in order to determine status | `code`, `calibration_status` |
| Safeguarded from adjustments that invalidate calibration | `state` = `quarantined`; frozen acceptance criteria |
| Determine validity of previous results when found unfit | `ls.calibration.oot` |

### ISO 22716:2007 (cosmetics) and ISO 15378:2017 (primary packaging materials)

Both include equipment calibration provisions within their good manufacturing
practice requirements. **The clause numbering and wording could not be verified
from official documentation.** The module elements that support them are the
same as those listed for ISO 9001 above. No cosmetics-specific or
packaging-specific behaviour is implemented.

### ISO/IEC 17025:2017 — Testing and calibration laboratories

Clause 6.4 addresses equipment; clause 6.5 addresses metrological traceability.
Relevant where the organisation operates a calibration laboratory rather than
merely consuming calibration services.

| Subject | Module element |
|---|---|
| Metrological traceability to the SI through a documented unbroken chain | `ls.calibration.standard` records one link of that chain |
| Equipment records including calibration dates, results and due dates | `ls.calibration.record`, `ls.calibration.standard` |

**Limitation:** this module records one link of the traceability chain. It does
not model the full unbroken chain to a national metrology institute, nor does
it compute measurement uncertainty budgets. An accredited calibration
laboratory needs more than this module provides.

### FDA 21 CFR Part 11 and EU GMP Annex 11 — electronic records

| Requirement subject | Status in this module |
|---|---|
| Limiting system access to authorised individuals | Supported through Odoo access rights and this module's four groups |
| Use of secure, computer-generated, time-stamped audit trails | **Not implemented here.** `mail.thread` field tracking is a change log without tamper evidence. `ls_audit_trail` is the module that addresses this. |
| Signed electronic records containing the printed name, date, time and meaning of the signature | **Not implemented here.** Approval records a user and a timestamp; there is no re-authentication and no signature meaning. `ls_electronic_signature` addresses this. |
| Authority checks | Supported through group-based access rights and ORM-level segregation of duties |
| Protection of records to enable accurate retrieval | Supported through immutability after approval and prevention of deletion |

**This is the most important limitation in this document.** An organisation
that needs 21 CFR Part 11 electronic signatures on calibration approvals must
deploy `ls_electronic_signature` and `ls_audit_trail` alongside this module.
Approving a calibration record here is not signing it.

## 2.3 ALCOA+ mapping

| Principle | Support | Gap |
|---|---|---|
| Attributable | `performed_by_user_id`, `reviewed_by_user_id`, `approved_by_user_id` | External technicians recorded as text |
| Legible | Structured fields, no free-text results | — |
| Contemporaneous | Timestamps on review and approval; future performed dates refused | Data entry timing is not itself enforced |
| Original | Readings stored as entered, immutable after approval | — |
| Accurate | Tolerance evaluation is computed, not typed | Transcription from the instrument is manual |
| Complete | Mandatory reasons for rejection and cancellation; deletion prevented | — |
| Consistent | Single state machine per model, enforced centrally | — |
| Enduring | Records not deletable past draft | Database retention is an infrastructure matter |
| Available | Search, filters, group-by, two QWeb reports | — |

## 2.4 Frameworks examined and found not applicable

| Framework | Reason |
|---|---|
| EU MDR 2017/745 | Concerns device placing on the market, not instrument calibration. Calibration reaches MDR only through ISO 13485 clause 7.6. |
| EU Cosmetics Regulation 1223/2009 | Concerns product safety and notification. No calibration provision. |
| ISO 14971:2019 | Risk management for devices. Instrument criticality here is a business classification, not an ISO 14971 risk analysis. |
| GS1 standards | Concern identification and serialisation of trade items. |
| ICH Q7 | Contains equipment calibration provisions for active substances; the module elements are identical to those listed for EU GMP. |

**PHASE 2 GATE: PASS** — with the explicit qualifications recorded above.

---

# PHASE 3 — FUNCTIONAL SPECIFICATION

## 3.1 Menu structure

```
Calibration
├── Instruments
│   ├── Instrument Register
│   ├── Calibration Status
│   └── Calibration Points
├── Planning
│   ├── Calibration Plans
│   └── Generate Scheduled Calibrations      [Technician+]
├── Calibrations
│   ├── Open Calibrations
│   ├── All Calibration Records
│   └── Certificates
├── Out of Tolerance
│   └── OOT Events
└── Configuration                             [Manager only]
    ├── Instrument Categories
    └── Reference Standards
```

The root menu is visible to `group_ls_calibration_viewer` and above.

## 3.2 State machines

### Instrument

```
draft ──► in_service ──► quarantined ──► in_service
  │            │              │
  │            ▼              ▼
  │      out_of_service ◄─────┘
  │            │
  └────────────┴──────► retired  (terminal)
```

`draft → in_service` is refused when the instrument has no calibration point.
`retired` archives the record and stamps `retirement_date`.

### Calibration plan

```
draft ──► approved ◄──► suspended
  │           │             │
  └───────────┴─────────────┴──► closed  (terminal)
```

`approved` requires the instrument to be non-retired and to have at least one
calibration point. `suspended` and `closed` each require a recorded reason.

### Calibration record

```
draft ──► in_progress ──► performed ──► under_review ──► approved (terminal)
  │           │               │              │
  │           │               │              └──► rejected ──► in_progress
  │           │               │
  └───────────┴───────────────┴──────────────────► cancelled (terminal)
```

`approved` and `cancelled` are locked: data writes are refused.
`rejected` requires a non-blank reason; `cancelled` requires a reason.

### Out-of-tolerance event

```
open ──► under_assessment ──► assessed ──► closed  (terminal)
```

`assessed` requires impact assessment, product impact, disposition and
justification. `closed` requires a CAPA reference when the product impact is
potential or confirmed, and must be performed by a user other than the
assessor.

## 3.3 Business rules

| # | Rule | Enforcement |
|---|---|---|
| BRL-1 | Instrument ID unique per company | Database constraint |
| BRL-2 | Calibration interval strictly positive | Database constraint |
| BRL-3 | Range maximum not below range minimum | Python constraint |
| BRL-4 | Calibration point nominal value inside the instrument range | Python constraint |
| BRL-5 | Percent-of-span tolerance requires a non-zero span | Python constraint |
| BRL-6 | Point name unique within an instrument | Database constraint |
| BRL-7 | Acceptance criteria frozen once used in a committed record | `write` override |
| BRL-8 | A point with readings cannot be deleted | `unlink` override |
| BRL-9 | Only one approved plan may be effective per instrument at a time | Python constraint |
| BRL-10 | An external plan or record must name its provider | Python constraint |
| BRL-11 | A record's plan must belong to the record's instrument | Python constraint |
| BRL-12 | A performed date cannot be in the future | Python constraint |
| BRL-13 | A performed record must cite at least one reference standard | Python constraint |
| BRL-14 | A calibration point may appear at most once per record | Database constraint |
| BRL-15 | Performer, reviewer and approver must be three distinct users | Python constraint plus action guards |
| BRL-16 | Approved and cancelled records reject data writes | `write` override |
| BRL-17 | Readings follow the immutability of their parent record | `create`, `write` and `unlink` overrides |
| BRL-18 | Only draft records may be deleted | `unlink` override |
| BRL-19 | An instrument with calibration history cannot be deleted | `unlink` override |
| BRL-20 | Certificates can never be deleted | `unlink` override |
| BRL-21 | A certificate requires an approved record | Python constraint |
| BRL-22 | An external certificate requires its document | Python constraint |
| BRL-23 | A certificate cannot predate the calibration | Python constraint |
| BRL-24 | Relative humidity between 0 and 100 | Database constraint |
| BRL-25 | Raising an OOT quarantines an in-service instrument | `create` override |
| BRL-26 | A reported product impact requires a CAPA reference before closure | Action guard |
| BRL-27 | The OOT assessor cannot close the event | Action guard |
| BRL-28 | Generation is capped at 500 records per plan per run | Action guard |

## 3.4 Result aggregation rules

| As-found | As-left | Overall |
|---|---|---|
| not applicable | not applicable | not applicable |
| pass | pass or not applicable | **pass** |
| fail | pass | **pass after adjustment** |
| fail | fail or not applicable | **fail** |
| pass | fail | **fail** |

A series evaluates to `not_applicable` when no value in it was recorded.
`pass after adjustment` exists as a distinct verdict because it carries a
different consequence: the instrument was out of tolerance during the preceding
period even though it is in tolerance now.

## 3.5 Scheduled actions

| Action | Frequency | Default | Purpose |
|---|---|---|---|
| Refresh instrument status | Daily | Active | Recomputes the stored `calibration_status`, which depends on the current date; posts a message when an instrument newly becomes overdue. |
| Notify upcoming and overdue calibrations | Weekly | **Inactive** | Posts a chatter reminder on due and overdue instruments. Shipped inactive so that a fresh installation does not generate notification traffic before configuration. |
| Refresh reference standard validity | Daily | Active | Recomputes the stored `is_valid` flag. |

## 3.6 Reports

| Report | Model | Content |
|---|---|---|
| Calibration Certificate | `ls.calibration.certificate` | Instrument identification, calibration dates, environmental conditions, reference standards with traceability, full reading table with per-point verdict, three-role authorisation block, and an explicit statement that the certificate is not a statement of regulatory conformity. |
| Calibration Record | `ls.calibration.record` | Record status, results, readings and any linked out-of-tolerance events. |

## 3.7 Search, filters and grouping

Every model ships a search view. The instrument search offers filters for
Overdue, Due Soon, Never Calibrated, GxP Critical, Criticality Critical, In
Service, Quarantined, My Instruments and Archived; and grouping by Category,
Calibration Status, Lifecycle Status, Criticality, Responsible and Next Due
Month. The record search offers Open, Awaiting Approval, Approved, Rejected,
Failed, As-Found Out of Tolerance, Performed by Me and Scheduled This Month;
and grouping by Instrument, Category, Status, Overall Result, Performed By,
Scheduled Month and Performed Month. Plan, certificate, standard, point and
OOT searches are documented in `docs/USER_MANUAL.md`.

## 3.8 Wizards

| Wizard | Model | Purpose |
|---|---|---|
| Generate Scheduled Calibrations | `ls.calibration.plan.generate` | Creates draft records from approved plans up to a horizon date, optionally restricted by plan, category or criticality. Refuses to run when nothing matches or when everything is already scheduled. |
| Reject Calibration Record | `ls.calibration.record.reject` | Captures a mandatory non-blank rejection reason and applies it. |

## 3.9 Dashboards and KPIs

The module ships pivot, graph and calendar views on `ls.calibration.record`,
and a pre-filtered Calibration Status action on instruments. It does **not**
ship a dashboard client action: the Odoo 19 dashboard and kanban template APIs
could not be verified from official documentation, and an unverified template
would risk installation failure. Available measures are: record count by
category and overall result (pivot), records by performed month and result
(graph), and scheduled calibrations by month (calendar).

**PHASE 3 GATE: PASS**
