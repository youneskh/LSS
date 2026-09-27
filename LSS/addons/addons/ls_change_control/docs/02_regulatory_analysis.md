# Phase 2 - Regulatory Analysis

Module: `ls_change_control`

## 1. Statement of principle

**This module does not achieve, guarantee or certify compliance with any
regulatory framework.**

What follows describes how the module **supports** an organisation that is
implementing a change control process. The organisation remains responsible
for its procedures, for the validation of the system in its intended use, for
the training of its personnel and for the operation of its quality management
system.

Where a requirement of a framework could not be verified from an official
publication, this document states so explicitly rather than paraphrasing from
memory.

## 2. Applicable frameworks

The frameworks below are those listed in section 3.1 of the functional
specification of the Life Sciences Suite that are relevant to change control.

| Framework | Relevance to this module |
|-----------|--------------------------|
| Good manufacturing practices, including the practices recognised by the ANPP in Algeria and the WHO GMP guidance | Change control is a core element of a pharmaceutical quality system |
| ISO 9001:2015 | Contains requirements on the control of changes and on documented information |
| ISO 13485:2016 | Contains requirements on the control of changes in a medical device quality management system |
| ISO 15378:2017 | Applies GMP principles to primary packaging materials for medicinal products |
| ISO 22716:2007 | Provides GMP guidelines for cosmetics |
| FDA 21 CFR Part 11 | Applies to electronic records and electronic signatures used in regulated activities |
| EU Regulation 2017/745 on medical devices | Contains obligations relating to changes to devices and to the quality management system |
| ICH quality guidelines | Address change management within a pharmaceutical quality system |

**Verification note.** The exact clause numbers of ISO standards are not
reproduced in this document. ISO standards are copyrighted works that are not
freely available, and the precise clause numbering could not be verified
against an official publication in the environment where this module was
built. Section 14 of the suite specification maps modules to frameworks at
framework level; this document does the same. An organisation must map the
module to the specific clauses of the standards it holds under licence.

## 3. How the module supports each requirement family

The table below states, for each requirement family that a change control
process is generally expected to address, the mechanism the module provides.
The left column describes a process expectation, not a quotation from a
regulation.

| Process expectation | Mechanism in the module |
|---------------------|-------------------------|
| Changes are formally requested before being made | `ls.change_control.request`, Draft state, mandatory description of the situation before, the situation after and the justification |
| Changes are classified | `category_id` and `classification` fields; the category drives the whole workflow |
| The impact of a change is evaluated before approval | `ls.change_control.assessment`, one record per impact area, with a mandatory written rationale |
| Evaluation covers quality, regulatory and validation aspects | 14 seeded impact areas covering facilities, utilities, equipment, process, product, materials, analytical methods, cleaning, packaging, documentation, computerised systems, personnel, regulatory dossier and environmental monitoring |
| Changes are approved by the appropriate functions before implementation | `ls.change_control.approval`, generated from the approval template of the category, 11 named approval roles |
| Approval is attributable to a person | `decided_by_id`, `date_decision` in UTC, `signature_meaning`, all read only and written only by the workflow |
| Decisions cannot be altered afterwards | `write` and `unlink` on a decided approval raise an error, in every state and for every group |
| The regulatory consequence of a change is determined | `regulatory_impact` field with four explicit values, plus the Regulatory Dossier impact area |
| Implementation is planned and tracked | `ls.change_control.implementation` with a responsible person, a planned date and twelve explicit action types |
| Implementation is evidenced | `evidence_reference` mandatory before an action can be closed |
| Effectiveness of the change is verified | `ls.change_control.verification`, acceptance criteria recorded, result Effective or Not Effective |
| An ineffective change triggers a follow-up | A Not Effective result requires `follow_up_required` and blocks the transition to Verified |
| The change is formally closed | `action_close` with a mandatory closure statement, reserved to change control managers |
| Records are retained | Deletion refused for any request that is not in Draft; completed sub-records are never deletable |
| Records are available for inspection | Change control record report in PDF, containing every section of the record |
| Access to the process is controlled | Four security groups, access rights per model, record rules per company and per ownership |

## 4. Support for electronic records and electronic signatures

The suite architecture assigns electronic signatures to `ls_electronic_signature`
and audit trails to `ls_audit_trail`. This module therefore provides the
following, and nothing more.

| Element | Provided by this module | Not provided by this module |
|---------|------------------------|----------------------------|
| Identity of the person taking a decision | Yes, `decided_by_id` | |
| Date and time of the decision | Yes, `date_decision`, stored in UTC | |
| Meaning of the signature | Yes, `signature_meaning` | |
| Immutability of the signed record | Yes, enforced in `write` and `unlink` | |
| Attribution of every field change in the chatter | Yes, through Odoo message tracking on tracked fields | Field level audit trail on untracked fields |
| Re-authentication of the signer at the moment of signing | **No** | Assigned to `ls_electronic_signature`; the extension point is `_apply_signature` |
| Cryptographic sealing or hash chaining of records | **No** | Assigned to `ls_audit_trail` |

**This is an explicit limitation.** An organisation that must satisfy the
electronic signature requirements of FDA 21 CFR Part 11 cannot do so with this
module alone.

## 5. Support for data integrity principles

| Principle | Mechanism |
|-----------|-----------|
| Attributable | Every decision stores its author. Workflow writes use `sudo()`, which in Odoo keeps the real user on the environment, so chatter tracking names the person who acted, not a technical account |
| Legible | Records are stored as structured fields, not as free text blobs; the report renders every section |
| Contemporaneous | Decision dates are stamped by the server at the moment of the decision and cannot be supplied by the client |
| Original | The original record is the database record; the printed report carries a notice that it is uncontrolled when printed |
| Accurate | Python and SQL constraints reject incoherent data such as a temporary change without an end date |
| Complete | Blocking guards prevent a transition while a mandatory assessment or approval is outstanding |
| Consistent | The category template imposes the same assessment and approval matrix on every change of the same type |
| Enduring | Submitted requests cannot be deleted or archived |
| Available | Records are searchable, groupable and printable |

## 6. Points requiring organisational procedures

The module cannot, by construction, satisfy the following. They must be
covered by the procedures of the organisation.

1. Definition of who holds each security group, and the periodic review of that assignment.
2. Definition of the categories, impact areas and approval matrices applicable to the site, and their approval by the quality unit.
3. Validation of the system in its intended use, including installation, operational and performance qualification.
4. Training of the personnel on the change control procedure and on the system.
5. Backup, restoration and disaster recovery of the database.
6. Retention period of the records and the archival strategy.
7. Periodic review of the change control process and of its metrics.
8. Determination, for each market, of the regulatory action a given change triggers.
