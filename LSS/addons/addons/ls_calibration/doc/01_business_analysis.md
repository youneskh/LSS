# Phase 1 — Business Analysis

Module: `ls_calibration` — Life Sciences Suite for Odoo 19 Community Edition.

## 1.1 Business objectives

| # | Objective |
|---|-----------|
| BO-01 | Maintain a single, complete and current register of every measuring, monitoring and test instrument whose result is used to accept or reject a product, a process or an environmental condition. |
| BO-02 | Guarantee that no instrument is used in production beyond its calibration due date without the situation being visible and traceable. |
| BO-03 | Produce, for every calibration, evidence that is complete, attributable, contemporaneous and unmodifiable after approval. |
| BO-04 | Detect out-of-tolerance situations at the as-found stage and force a documented assessment of their impact on the products already released. |
| BO-05 | Ensure the metrological traceability of every calibration to a reference standard whose own calibration status is known and valid. |
| BO-06 | Enforce segregation of duties between the person who performs a calibration and the person who approves it. |
| BO-07 | Reduce the manual effort of planning calibrations by generating the due calibration records automatically. |
| BO-08 | Provide, on demand, the calibration history of any instrument for an internal audit or a regulatory inspection. |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|-------------|-----------|
| BR-01 | Each instrument carries a unique identification that is never reused. | BO-01 |
| BR-02 | Each instrument carries its measuring range, its unit and its maximum permissible error. | BO-01 |
| BR-03 | Each instrument is classified by criticality and by GxP impact. | BO-01 |
| BR-04 | Each instrument has a documented calibration interval and a written procedure reference. | BO-02 |
| BR-05 | The next due date is derived from the last approved calibration and from the interval, without manual computation. | BO-02 |
| BR-06 | Instruments that are due within a configurable lead time, or overdue, are reported and their responsible is notified. | BO-02 |
| BR-07 | A calibration record contains one line per test point with the nominal value, the acceptance limits, the as-found reading and the as-left reading. | BO-03 |
| BR-08 | The verdict of each reading and the overall result are derived from the data and cannot be entered manually. | BO-03 |
| BR-09 | An approved calibration record cannot be modified or deleted. | BO-03 |
| BR-10 | An out-of-tolerance as-found result cannot be submitted for approval without an impact assessment. | BO-04 |
| BR-11 | The reference standards used are recorded, and a standard whose calibration is overdue is refused. | BO-05 |
| BR-12 | The approver of a calibration record is not its performer. | BO-06 |
| BR-13 | The calibration records of the plans that fall due are created automatically. | BO-07 |
| BR-14 | The calibration history, the certificates and a printable record are available per instrument. | BO-08 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| Metrology technician | Performs the calibrations and records the readings. |
| Quality assurance | Approves the calibration records, handles out-of-tolerance events. |
| Production supervisor | Needs to know whether an instrument may be used. |
| Quality control laboratory | Depends on the calibration status of the analytical instruments. |
| Maintenance department | Owns the equipment on which the instruments are installed. |
| Regulatory affairs | Provides the calibration evidence during inspections. |
| Internal and external auditors | Verify the completeness and integrity of the evidence. |
| System administrator | Configures the groups, the scheduled actions and the parameters. |

## 1.4 User roles

| Role | Security group | Rights |
|------|----------------|--------|
| Viewer | `group_ls_calibration_viewer` | Reads the register, the plans, the records and the certificates. |
| Technician | `group_ls_calibration_technician` | Creates and completes calibration records and certificates, submits them for approval. Cannot modify the register or the plans, cannot approve. |
| Manager | `group_ls_calibration_manager` | Maintains the register and the plans, approves or rejects the records, issues and supersedes the certificates, deletes draft records. |

## 1.5 User stories

| # | Story |
|---|-------|
| US-01 | As a manager, I register a new instrument with its metrological characteristics so that it can be scheduled for calibration. |
| US-02 | As a manager, I define a calibration plan with its interval and its test points so that the due dates are computed automatically. |
| US-03 | As a technician, I receive the list of the instruments that are due so that I can organise my week. |
| US-04 | As a technician, I record the as-found and as-left readings of every test point so that the verdict is established automatically. |
| US-05 | As a technician, I record which reference standards I used so that the metrological traceability is documented. |
| US-06 | As a technician, I submit the completed record for approval so that quality assurance can review it. |
| US-07 | As a manager, I approve a calibration record so that the instrument is released and the next due date is set. |
| US-08 | As a manager, I reject a calibration record with a justification so that the technician can correct it. |
| US-09 | As a manager, I am prevented from approving a calibration that I performed myself so that segregation of duties is enforced. |
| US-10 | As a manager, I am required to document the impact of an out-of-tolerance result before the record can be approved. |
| US-11 | As a manager, I issue a calibration certificate from an approved record so that it can be provided to an auditor. |
| US-12 | As a manager, I register the certificate received from an external accredited laboratory so that the evidence is centralised. |
| US-13 | As an auditor, I open an instrument and read its complete calibration history so that I can assess its control. |
| US-14 | As an administrator, I let the system create the due calibration records so that nothing is forgotten. |

## 1.6 Use cases

| # | Use case | Primary actor | Trigger | Result |
|---|----------|---------------|---------|--------|
| UC-01 | Register an instrument | Manager | New instrument received | Instrument in service |
| UC-02 | Define a calibration plan | Manager | Instrument in service | Active plan with a due date |
| UC-03 | Generate the due calibration records | System | Daily scheduled action | Draft records |
| UC-04 | Notify the due and overdue instruments | System | Daily scheduled action | Activities for the responsible users |
| UC-05 | Perform a calibration | Technician | Draft record | Record submitted to review |
| UC-06 | Approve a calibration | Manager | Record submitted | Approved and locked record, new due date |
| UC-07 | Reject a calibration | Manager | Record submitted | Rejected record with a documented reason |
| UC-08 | Handle an out-of-tolerance result | Technician and Manager | As-found out of tolerance | Documented impact assessment and action reference |
| UC-09 | Issue a calibration certificate | Manager | Approved record | Issued certificate |
| UC-10 | Register an external certificate | Technician | Certificate received | Certificate with its attached document |
| UC-11 | Withdraw an instrument | Manager | Instrument out of use | Instrument out of service or retired, plans closed |
| UC-12 | Print the calibration evidence | Any role | Audit request | PDF record and certificate |

## 1.7 Functional scope

In scope: instrument register; calibration plans and test points; calibration
records with as-found and as-left readings; automatic verdict and result;
out-of-tolerance handling; reference standard traceability; review and
approval workflow with segregation of duties; locking of approved records;
calibration certificates, internal and external; due date computation and
status classification; notification and generation scheduled actions; PDF
reports; access rights for three roles; multi-company isolation.

## 1.8 Out of scope

The following items are deliberately excluded from this module. Each one is a
conscious decision, not an omission.

| # | Excluded item | Reason |
|---|---------------|--------|
| OS-01 | Re-authentication at the moment of the signature | Belongs to the electronic signature module of the suite. |
| OS-02 | Complete field level audit trail with hash chaining | Belongs to the audit trail module of the suite. |
| OS-03 | Deviation and corrective action management | Belongs to the deviation and CAPA modules of the suite. |
| OS-04 | Document control of the calibration procedures | Belongs to the document management module of the suite. |
| OS-05 | Training and qualification of the technicians | Belongs to the training module of the suite. |
| OS-06 | Direct acquisition of readings from an instrument or a data logger | Requires an instrument interface that is hardware specific. |
| OS-07 | Uncertainty budget computation | Requires a metrological model per method that is site specific. |
| OS-08 | Blocking of a laboratory result produced by an overdue instrument | Requires the laboratory module of the suite. |
| OS-09 | Preventive maintenance planning | Provided by the native Maintenance application. |
| OS-10 | Purchase of external calibration services | Provided by the native Purchase application. |

## 1.9 Risks

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| RI-01 | An instrument is used beyond its due date. | Product decisions based on an uncontrolled measurement. | Status computed at read time, daily notification, dedicated view. |
| RI-02 | Calibration evidence is modified after approval. | Loss of data integrity, inspection finding. | Write and unlink locking of approved records and of their lines. |
| RI-03 | A calibration is approved by its own performer. | Loss of segregation of duties. | Blocking check at approval. |
| RI-04 | A calibration is justified by an uncontrolled standard. | Loss of metrological traceability. | Overdue standards refused at submission and at approval. |
| RI-05 | An out-of-tolerance result is closed without impact assessment. | Released products not reassessed. | Mandatory assessment before submission. |
| RI-06 | The Odoo 19 API differs from the assumptions of the design. | Installation or execution failure. | API items verified against the official Odoo 19 documentation; residual items listed in the validation report. |
| RI-07 | The status search filters instruments in Python. | Degraded response time on a very large register. | Documented; the candidate set is restricted by the access rights and by the register size. |
| RI-08 | The module is mistaken for a Part 11 compliant signature solution. | Regulatory misrepresentation. | Explicit limitation stated in the README, the roadmap and the validation report. |

## 1.10 Success criteria

| # | Criterion | Measure |
|---|-----------|---------|
| SC-01 | The module installs on a clean Odoo 19 Community database. | Installation without error. |
| SC-02 | The module updates without data loss. | Update without error, records preserved. |
| SC-03 | Every business rule of section 1.2 is enforced by code, not by procedure. | One automated test per rule. |
| SC-04 | No approved record can be altered through the user interface or the ORM. | Dedicated automated tests. |
| SC-05 | Static analysis reports no blocking finding. | Analysis report attached. |
| SC-06 | The complete calibration history of an instrument is retrievable in one screen. | Instrument form with its four tabs. |

## Gate

**Phase 1: PASS.** Objectives, requirements, stakeholders, roles, stories,
use cases, scope, exclusions, risks and success criteria are defined and are
traceable to the following phases.
