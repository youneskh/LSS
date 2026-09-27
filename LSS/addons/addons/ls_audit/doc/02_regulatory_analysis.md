# 02 — Regulatory Analysis

Phase 2 deliverable. Module: `ls_audit`.

## 0. Standing disclaimer

This module **supports** the implementation of an audit process. It does not
certify compliance with anything. Every statement below describes what a
framework requires and what the software does about it. Whether your
organisation complies depends on your procedures, your validation, your
training and your quality system — not on this software.

Where a requirement is **not** implemented, this document says so plainly.

---

## 1. Frameworks in scope for this module

Only frameworks whose requirements bear directly on *auditing* are analysed.
The wider Life Sciences Suite specification lists others; they are not
relevant to `ls_audit` and are therefore not claimed here.

| Framework | Relevant provision | Applies to |
|---|---|---|
| ISO 13485:2016 | Clause 8.2.4, Internal audit | Medical devices |
| ISO 9001:2015 | Clause 9.2, Internal audit | All industries |
| FDA 21 CFR Part 820 (QMSR) | Internal audit, via incorporation of ISO 13485:2016 | US medical devices |
| EU GMP | Chapter 9, Self inspection | Pharmaceuticals (EU) |
| ISO 19011:2018 | Guidelines for auditing management systems | Guidance, not a requirement |
| FDA 21 CFR Part 11 | Electronic records and signatures | Where records are kept electronically |

---

## 2. A change that postdates most training data: the FDA QMSR

This is important enough to state separately, because it changes what an
audit-management system is for in a US device context.

The FDA's **Quality Management System Regulation (QMSR)** became effective
**2 February 2026**, amending 21 CFR Part 820 and incorporating ISO 13485:2016
by reference. Part 820 still exists; it was retitled and restructured to act
as an overlay on ISO 13485 rather than to state each requirement itself.
Alongside the rule, FDA stopped using the Quality System Inspection Technique
(QSIT) and moved to the inspection process in Compliance Program 7382.850.

**The consequence that matters here:** under the legacy QSR, 21 CFR 820.180(c)
exempted internal audit reports from FDA inspection. Under the QMSR that
exemption is not maintained — management review, internal quality audit and
supplier audit reports are now subject to FDA inspection.

**Design implication.** Audit reports held in this module may be read by an
FDA investigator. They are not internal-only working papers. This is the
reason the report lifecycle enforces separate, separately-attributed
preparation, review, approval and issuance, and the reason issued reports
become immutable.

Sources: FDA, *Quality Management System Regulation (QMSR)* and *QMSR
Frequently Asked Questions*, fda.gov. Corroborated by NSF, BSI and Gardner Law
commentary. **Verify current status before relying on this** — it postdates
this module's construction and regulations change.

---

## 3. ISO 13485:2016 Clause 8.2.4 — requirement-by-requirement mapping

Clause 8.2.4 is the densest source of concrete requirements for this module.
The clause requires internal audits at planned intervals to determine whether
the QMS conforms to planned and documented arrangements, to the standard, to
the organisation's own QMS requirements, and to applicable regulatory
requirements.

| Clause requirement | Module support | Enforcement |
|---|---|---|
| Audits conducted **at planned intervals** | `ls.audit.program` defines a period; each audit's planned date is constrained to fall inside it | Hard constraint |
| Programme planned considering **status and importance of processes** and **results of previous audits** | `ls.audit.area` hierarchy; programme completion statistics; audit history per area | Supported, not enforced — this is a human judgement the software records but cannot make |
| **Audit criteria, scope, interval and methods defined and recorded** | `objective`, `scope` and `criteria` are required fields on every audit | Hard constraint |
| **Selection of auditors ensures objectivity and impartiality** | Team members cannot be auditees; team members cannot own an audited area | Hard constraint |
| **Auditors shall not audit their own work** | Enforced through both rules above, plus: a finding cannot be assigned to the auditor who raised it | Hard constraint |
| Records maintained, including **identification of processes and areas audited** and the **conclusions** | `area_ids` required; report `conclusion` required to issue; records become read-only once closed or issued | Hard constraint |
| Management responsible for the audited area ensures corrections and corrective actions **without undue delay** | `response_deadline_days` per finding category drives a computed `response_due_date`; a daily scheduled action surfaces overdue findings | Enforced deadline, notified breach |
| **Follow-up shall include verification of the actions taken and reporting of verification results** | A finding cannot reach `closed` without a documented `verification_method` **and** `verification_result`; the verifier cannot be the auditee | Hard constraint |
| Documented procedure for planning, conducting, recording and reporting | The state machines encode the procedure; the procedure document itself is your responsibility | Supported |

ISO 13485 clause 8.2.4 carries a note pointing to **ISO 19011** for further
guidance. ISO 19011:2018 informs the design of the auditor qualification
register and the programme concept, but it is guidance, not a requirement, and
no conformity to it is claimed.

**ISO standard text is copyrighted and is not reproduced or shipped with this
module.** Clause references in checklists are free-text fields that you
populate.

---

## 4. FDA 21 CFR Part 11 — what is and is not implemented

This section exists to prevent a specific and serious misunderstanding.

### 4.1 What the module does provide

| Part 11 theme | Implementation |
|---|---|
| Audit trail of changes (§11.10(e)) | Odoo field-level tracking on every workflow model; who, what, old value, new value, timestamp, in the chatter |
| Limiting system access to authorised individuals (§11.10(d)) | Four security groups, 37 access rules, row-level record rules |
| Operational system checks enforcing sequencing (§11.10(f)) | State machines refuse out-of-order transitions |
| Authority checks (§11.10(g)) | Segregation of duties on report review and approval; verifier cannot be the auditee |
| Protection of records (§11.10(c)) | Closed audits, closed findings and issued reports become read-only; issued records cannot be deleted |

### 4.2 What the module does NOT provide

**The approvals in this module are not electronic signatures.**

21 CFR 11.50 requires that a signed electronic record display the printed name
of the signer, the date and time of signing, and the **meaning** of the
signature. 21 CFR 11.200 requires that electronic signatures use at least two
distinct identification components and that, for a series of signings, the
signer re-authenticate.

This module implements **none** of these. It records that a user performed an
action at a time. That is an audit trail entry, not a signature.

Password re-authentication was deliberately **not** implemented rather than
implemented on an unverified API. Shipping a re-authentication step that
silently failed would be worse than shipping none, because it would create the
appearance of a control that does not exist.

The generated PDF audit report states this in its signature block, so a
printed report cannot be mistaken for a signed one.

**If you need Part 11 signatures, you must add a dedicated electronic
signature component and re-validate the system.**

### 4.3 Validation

21 CFR 11.10(a) requires validation of systems to ensure accuracy,
reliability, consistent intended performance, and the ability to discern
invalid or altered records.

**This module is not validated.** It has not even been executed. See
`10_validation_report.md` for exactly what was and was not verified, and
`03_installation_guide.md` for the qualification work you must perform.

---

## 5. Other frameworks — honest, brief

**ISO 9001:2015 clause 9.2** requires internal audits at planned intervals,
an audit programme accounting for the importance of processes and prior audit
results, defined criteria and scope, objective and impartial auditor
selection, reporting to relevant management, and correction without undue
delay. The mapping in §3 satisfies the same structural requirements; ISO 9001
is less prescriptive than ISO 13485 on records.

**EU GMP Chapter 9, Self Inspection**, requires self inspections to be
conducted in a routine manner to monitor implementation and compliance with
GMP principles and to propose corrective measures, with records of self
inspection and any subsequent corrective action. The programme, audit,
finding and report models record exactly this. EU GMP does not prescribe the
impartiality mechanics that ISO 13485 does; the module's constraints are
stricter than Chapter 9 requires, which is not a compliance problem.

**Algerian ANPP requirements.** The parent Life Sciences Suite specification
lists ANPP as a target framework. **I could not verify ANPP's specific
requirements for internal audit from official ANPP publications.** No claim of
ANPP support is made in this module, and no ANPP-specific field or workflow
was built. If ANPP imposes particular audit record requirements, they must be
assessed against this module before use in an ANPP-regulated context.

**ISO 15378, ISO 22716, EU MDR, EU Cosmetics Regulation, GS1.** These appear
in the suite specification but impose no requirement that this module
implements specifically. No support is claimed.

---

## 6. Summary of regulatory claims

| Claim | Status |
|---|---|
| Supports implementation of an ISO 13485:2016 clause 8.2.4 internal audit process | Yes, with the mapping in §3 |
| Supports implementation of an ISO 9001:2015 clause 9.2 internal audit process | Yes |
| Supports implementation of an EU GMP Chapter 9 self-inspection process | Yes |
| Provides 21 CFR Part 11 audit trails | Partially — change tracking yes; see §4.1 |
| Provides 21 CFR Part 11 electronic signatures | **No** |
| Is validated software | **No** |
| Certifies compliance with any framework | **No** |
| Supports ANPP requirements | **Not assessed — could not be verified** |
