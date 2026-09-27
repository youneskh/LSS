# 02 — Regulatory Analysis

Phase 2 deliverable. Status: **CONDITIONAL PASS**. The condition is stated in
section 5.

## 1. Wording convention

Throughout this module the verb **support** means: the software provides a
function that an organisation may use as part of its own compliant process.
It never means that the software is compliant, certified, qualified or
validated. Compliance is a property of an operating organisation, not of a
software package.

## 2. Frameworks addressed

The clause references below follow the published clause structure of the
standards named. They are given so that a reader can locate the requirement
in their own copy of the standard. The full text of the standards is
copyrighted and is not reproduced here.

| Framework | Area addressed | Function of `ls_qms` |
|---|---|---|
| ISO 9001:2015, clause 5.2 | Quality policy | `ls.qms.policy` holds the policy statement, its scope, the commitments and the communication method, under revision control |
| ISO 9001:2015, clause 6.2 | Quality objectives and planning to achieve them | `ls.qms.objective` holds a baseline, a target, a direction, a period and a responsible person; achievement is computed from recorded measurements |
| ISO 9001:2015, clause 7.5 | Documented information: creation, update, control | Revision numbering, approval before issue, control of the current revision, periodic review, withdrawal of superseded revisions |
| ISO 13485:2016, clause 4.2.3 and 4.2.4 | Medical device file and control of documents | Same lifecycle applied to procedures, work instructions and quality plans; review before reissue; identification of the current revision |
| ISO 13485:2016, clause 4.2.5 | Control of records | `ls.qms.quality_record` with a defined retention period, protection against alteration and controlled disposal |
| ISO 13485:2016, clause 5.3 and 5.4.1 | Quality policy and quality objectives | Same models as for ISO 9001:2015 |
| ISO 22716:2007 | Good manufacturing practices for cosmetics: documentation | Controlled procedures and work instructions, retained records |
| ISO 15378:2017 | Good manufacturing practices for primary packaging materials | Quality plans expressing stage, characteristic, specification, method, frequency and sample size |
| WHO good manufacturing practices, documentation chapter | Written procedures, authorised, dated, and kept current | Approval by a second person, effective date, periodic review, withdrawal |
| FDA 21 CFR Part 11, section 11.10(d) | Limiting system access to authorised individuals | Four groups, access control lists and record rules |
| FDA 21 CFR Part 11, section 11.10(k) | Controls over systems documentation, including revision and change control | Revision chain, reason for change recorded on every revision |

## 3. Requirements deliberately **not** met by this module

This section exists so that no reader infers a capability from the table
above. Each line is a gap, not a feature.

| Requirement | Status in `ls_qms` |
|---|---|
| 21 CFR 11.100, 11.200: electronic signature uniquely attributable, requiring two distinct identification components | **Not implemented.** Approval records the acting user and the timestamp only. The method `_ls_qms_signature_hook` is the documented extension point |
| 21 CFR 11.50: signature manifestation printing the printed name, date, time and meaning of the signature | **Not implemented.** The PDF control block prints the approver and the approval date; it is not a signature manifestation |
| 21 CFR 11.70: signature to record linking resistant to excision and transfer | **Not implemented** |
| 21 CFR 11.10(e): computer generated, time stamped audit trail recording operator entries and actions that create, modify or delete records | **Partially covered only.** The module relies on `mail.thread` field tracking, which records tracked field changes in the message thread. This is not a dedicated, protected, exportable audit trail. Delegated to `ls_audit_trail` |
| 21 CFR 11.10(a): validation of the system | **Outside any software package.** Validation is an activity of the operating organisation. See `13_validation_report.md` |
| ISO 9001:2015 clause 9.2, internal audit | Delegated to `ls_audit` |
| ISO 9001:2015 clause 10.2, nonconformity and corrective action | Delegated to `ls_capa` |
| ISO 14971:2019, risk management | Delegated to `ls_risk_management` |
| EU MDR 2017/745, unique device identification and technical documentation | Delegated to `ls_medical_device` |

## 4. Algerian framework

The reference specification names **ANPP** requirements and Algerian good
manufacturing practices.

**This information could not be verified from official documentation.** No
ANPP technical requirement was retrieved from an official ANPP publication
during the development of this module. Consequently:

1. No model, field, view, report or message in `ls_qms` claims conformity
   with an ANPP requirement.
2. No ANPP specific numbering, dossier structure or submission format is
   implemented, because none could be verified.
3. The generic documentation control implemented here is derived from ISO
   9001:2015, ISO 13485:2016 and the WHO good manufacturing practices
   documentation chapter, which are publicly described.

An organisation subject to ANPP oversight must obtain the applicable
requirements from the authority and assess this module against them.

## 5. Condition attached to the PASS

This phase passes on the condition that the operating organisation reads
section 3 and section 4 before treating the module as part of a regulated
process. If authenticated electronic signature or a protected audit trail is
required by the applicable framework, `ls_qms` alone is **not sufficient**.
