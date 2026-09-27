# 01 — Business Analysis

**Phase gate: PASS** (analysis complete; no unresolved open questions blocking design)

## 1.1 Business objectives

| # | Objective |
|---|---|
| BO-1 | Ensure every departure from an approved procedure, specification or expected outcome is recorded promptly and cannot be quietly discarded |
| BO-2 | Ensure each deviation is classified for severity and assessed for impact before investigation effort is committed |
| BO-3 | Ensure root cause investigation is evidenced, not asserted |
| BO-4 | Ensure affected material receives an explicit, justified and independently approved disposition before release |
| BO-5 | Ensure the investigation is extended to other potentially associated batches and that the extension decision is recorded either way |
| BO-6 | Ensure closure carries written conclusions and follow-up |
| BO-7 | Make deviation ageing and overdue status visible so that closure targets are managed rather than discovered at audit |
| BO-8 | Produce a single printable record per deviation suitable for presentation during inspection |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|---|---|
| BR-1 | Each deviation carries a unique, gapless, company-scoped reference | BO-1 |
| BR-2 | A deviation record cannot be deleted once it has progressed past initial reporting; it can only be cancelled with a recorded reason | BO-1 |
| BR-3 | Occurrence, detection and recording timestamps are captured and must be chronologically consistent | BO-1 |
| BR-4 | Severity is one of Critical, Major, Minor | BO-2 |
| BR-5 | A planned deviation must carry its justification before execution | BO-2 |
| BR-6 | Impact is assessed across patient safety, product quality, regulatory status, validation status and other batches | BO-2 |
| BR-7 | Investigation records a structured RCA method, findings and root cause; where no definitive root cause exists, the most probable cause and its rationale are recorded instead | BO-3 |
| BR-8 | Where the deviation has an assessed impact, at least one product disposition is required before the disposition stage is reached | BO-4 |
| BR-9 | Disposition approval is segregated from disposition proposal | BO-4 |
| BR-10 | The batches evaluated for association, and the rationale for the extension scope, are recorded even when the conclusion is that no extension was necessary | BO-5 |
| BR-11 | Closure requires written conclusions and follow-up and a CAPA decision rationale | BO-6 |
| BR-12 | Closure is blocked while immediate actions remain open or dispositions remain unapproved | BO-4, BO-6 |
| BR-13 | Target closure dates derive from severity and can only be changed through a justified extension | BO-7 |
| BR-14 | Overdue open deviations notify the assigned investigator and QA reviewer daily | BO-7 |
| BR-15 | Every state transition records who, when and why in an append-only log | BO-1 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|---|---|
| Production and warehouse operators | Report deviations quickly with minimum friction |
| Line supervisors | Ensure containment actions are assigned and completed |
| QA officers | Assess impact, approve dispositions, close deviations |
| QA management | Monitor ageing, overdue counts, recurrence by category |
| Qualified Person / Pharmacien directeur technique | Rely on deviation closure as an input to batch release |
| Regulatory Affairs | Present the deviation record during inspection |
| Validation team | Evidence that the computerised system enforces the procedure |
| IT / ERP administrators | Install, upgrade and maintain the module |

## 1.4 User roles

| Role | Group | Privileges |
|---|---|---|
| Viewer | `group_ls_deviation_viewer` | Read all deviations within their companies |
| Reporter | `group_ls_deviation_reporter` | Create deviations; maintain own records while still Reported |
| Investigator | `group_ls_deviation_investigator` | Maintain any open deviation; record investigations and propose dispositions |
| Manager (QA) | `group_ls_deviation_manager` | Approve or reject dispositions; close; cancel; amend terminal records; configure master data |

Groups are strictly hierarchical: Manager implies Investigator implies
Reporter implies Viewer.

## 1.5 User stories

| # | Story |
|---|---|
| US-1 | As an operator, I record a deviation immediately so that it is captured at the time of the event |
| US-2 | As a supervisor, I assign containment actions with a responsible person and a deadline |
| US-3 | As a QA officer, I classify severity and record an impact assessment before committing investigation effort |
| US-4 | As an investigator, I select an RCA method and record findings and root cause |
| US-5 | As an investigator, I record which other batches I evaluated and why the extension scope was appropriate |
| US-6 | As a QA officer, I propose a disposition for affected material with a justification |
| US-7 | As a QA manager, I approve or reject the proposed disposition |
| US-8 | As a QA manager, I close the deviation with conclusions and follow-up |
| US-9 | As a QA manager, I extend a target closure date only with a justification that is retained |
| US-10 | As a QA manager, I cancel a deviation raised in error without destroying the record |
| US-11 | As a QA manager, I receive notification of overdue deviations |
| US-12 | As a reviewer, I send a deviation back a step when the work is insufficient, recording why |
| US-13 | As Regulatory Affairs, I print the complete deviation record including its transition log |
| US-14 | As QA management, I analyse deviations by category, severity and month |

## 1.6 Use cases

- UC-1 Record deviation
- UC-2 Assign and complete immediate actions
- UC-3 Assess severity and impact
- UC-4 Conduct root cause investigation
- UC-5 Evaluate extension to other batches
- UC-6 Propose product disposition
- UC-7 Approve or reject product disposition
- UC-8 Decide CAPA requirement
- UC-9 Close deviation
- UC-10 Send deviation back for rework
- UC-11 Cancel deviation
- UC-12 Extend target closure date
- UC-13 Notify overdue deviations
- UC-14 Print deviation report
- UC-15 Analyse deviation trends
- UC-16 Configure types, categories, RCA methods, tags and closure targets

## 1.7 Functional scope

In scope: deviation recording, classification, impact assessment, immediate
and containment actions, root cause investigation, extension evaluation,
product disposition with segregated approval, CAPA decision recording,
closure, cancellation, send-back, target date management, overdue
notification, transition logging, PDF reporting, trend analysis, master data
configuration, four-tier role-based access, multi-company isolation.

## 1.8 Out of scope

Explicitly not delivered by this module:

- CAPA lifecycle management. Only a reference field and a documented hook.
- 21 CFR Part 11 electronic signatures. Belongs to `ls_electronic_signature`.
- Field-level regulated audit trail beyond Odoo's native change tracking. Belongs to `ls_audit_trail`.
- Document control of the deviation SOP itself. Belongs to `ls_document_management`.
- Batch release decisioning. Belongs to `ls_pharma`.
- Laboratory OOS/OOT investigation. Belongs to `ls_lab`.
- Environmental monitoring excursion capture. Belongs to `ls_environmental_monitoring`; such excursions are recorded here as deviations of type Environmental Excursion.
- Automatic stock movement on disposition. The disposition records the decision; executing a scrap, rework or return remains a separate inventory transaction.
- Training records, supplier qualification, change control, complaints, recalls.

## 1.9 Risks

| # | Risk | Mitigation |
|---|---|---|
| R-1 | Users record deviations with insufficient factual detail | Description, impact assessment and justification are mandatory at defined gates rather than at creation, so the record is created promptly and enriched under control |
| R-2 | Closure targets are extended repeatedly without scrutiny | Extension only via wizard with mandatory justification posted to the chatter; the original target and each extension remain visible |
| R-3 | Disposition approved by the same person who proposed it | Approval restricted to the Manager group and stamped with approver and timestamp |
| R-4 | The 211.192 extension to other batches is skipped | `extension_rationale` is a hard gate on leaving the investigation stage; the rationale is required even when the conclusion is that no extension was needed |
| R-5 | Records deleted to hide a problem | Deletion blocked beyond the Reported state; cancellation requires a reason and retains the record |
| R-6 | Dependencies `ls_qms` and `ls_capa` do not exist | Dependencies reduced to existing modules; integration hook documented |
| R-7 | Module written against Odoo ≤18 idioms fails on 19 | Six breaking API changes verified against official Odoo 19 documentation before use; residual uncertainties listed in `00_VERIFICATION_STATUS.md` |
| R-8 | Module presented as validated when it has never been installed | Verification status document states plainly that nothing was executed against a running Odoo |

## 1.10 Success criteria

| # | Criterion | How assessed |
|---|---|---|
| SC-1 | Module installs into Odoo 19 Community without error | **Outstanding** — requires a running instance |
| SC-2 | All 92 test methods pass | **Outstanding** — requires a running instance |
| SC-3 | No deviation can be closed without conclusions and follow-up | Enforced by the close wizard; covered by tests |
| SC-4 | No deviation can leave investigation without an extension rationale | Enforced by `action_disposition`; covered by tests |
| SC-5 | No disposition is self-approved | Enforced by group check; covered by tests |
| SC-6 | Every transition is logged and the log cannot be edited | Enforced at model level; covered by tests |
