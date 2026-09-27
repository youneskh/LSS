# Phase 2 — Regulatory Analysis

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS**

---

## 2.1 Statement of limits — read this first

This module **does not certify compliance with anything**. It is a record-keeping
and workflow tool. Whether an organisation meets a regulatory requirement
depends on its procedures, its people, its validation activities and its
decisions, not on the software that stores the records.

Three further limits apply to this document specifically, and they are stated
plainly because the alternative would be to imply knowledge that is not held:

1. **No normative text is reproduced, paraphrased or interpreted anywhere in
   the module.** The `ls.supplier.standard` model stores a designation and an
   issuing body. The criteria shipped in `data/ls_supplier_criterion_data.xml`
   are wording written for this module; they are not extracted from any
   standard. Where a criterion is linked to a framework, that link expresses an
   association the organisation chooses to make, and nothing more.

2. **The mapping in §2.3 is an architectural recommendation, not a verified
   clause-by-clause mapping.** Producing a real traceability matrix requires the
   purchased text of each standard and a competent reviewer. That work belongs
   to the implementing organisation.

3. **The specific published requirements of the ANPP (Agence Nationale des
   Produits Pharmaceutiques, Algeria) regarding supplier qualification could not
   be verified from official documentation** in the preparation of this module.
   The module therefore provides an `ANPP` entry in the standards library so
   that an organisation can attach its own verified requirements to it, and
   makes no statement about their content. The same caution applies to the
   Algerian GMP (BPF) text.

## 2.2 Frameworks the module is designed to support

The list below is the set of frameworks named in the Life Sciences Suite
functional specification that plausibly touch supplier qualification. Each is
shipped as a record in the standards library so that an organisation can
reference it. Their designations are stated; their content is not.

| Code | Designation | Issuing body |
|------|-------------|--------------|
| `ISO9001` | ISO 9001:2015 | ISO |
| `ISO13485` | ISO 13485:2016 | ISO |
| `ISO14971` | ISO 14971:2019 | ISO |
| `ISO15378` | ISO 15378:2017 | ISO |
| `ISO22716` | ISO 22716:2007 | ISO |
| `21CFR11` | 21 CFR Part 11 | FDA |
| `21CFR211` | 21 CFR Part 211 | FDA |
| `21CFR820` | 21 CFR Part 820 | FDA |
| `EUMDR` | Regulation (EU) 2017/745 | EU Parliament and Council |
| `EU1223` | Regulation (EC) 1223/2009 | EU Parliament and Council |
| `WHOGMP` | WHO Good Manufacturing Practices | WHO |
| `ANPP` | ANPP requirements (Algeria) | ANPP |
| `GS1` | GS1 General Specifications | GS1 |

## 2.3 How the module supports the process, by theme

The table describes **what the module does**, in the module's own terms. It
deliberately avoids asserting that doing so satisfies any clause of any text.

| Theme common to the frameworks above | What this module provides |
|--------------------------------------|---------------------------|
| Evaluating and selecting a supplier before use | Dossier with a documented evaluation stage; category-driven prerequisites; weighted assessment producing a reproducible result. |
| Defining criteria for evaluation | Configurable criterion library with weights and a mandatory flag; questionnaire templates with an explicit scale and thresholds. |
| Recording the evaluation result | Assessment record with per-criterion score, evidence, comment, weighted total, percentage and Pass / Conditional / Fail outcome; PDF report. |
| Defining what the supplier is approved for | Explicit scope lines with material type, specification reference, manufacturing site, evaluated batches, and their own validity date. |
| Approving the supplier | Approval wizard with a decision, an end of validity, a written justification and a login confirmation; approval fields on the dossier; e-mail notification. |
| Keeping approval decisions attributable | Append-only signature log with user, timestamp, stated meaning, justification, a JSON snapshot of the signed values and a SHA-256 chain. |
| Re-evaluating suppliers periodically | Category-driven requalification interval; expiry state and daily job; periodic review record whose decision is written onto the dossier. |
| Auditing suppliers | Audit record with type, scope, framework basis, team, dates; findings with four severities; response deadline derived from a company setting. |
| Following up findings | Six-step finding workflow ending in verification and closure; audit closure blocked while any finding is open; corrective action mandatory for critical and major findings. |
| Monitoring performance | Scorecard combining on-time delivery, quality acceptance, documentation compliance and responsiveness with frozen weights; A–D rating; automatic follow-up activity when the rating is C or D. |
| Controlling purchases from unapproved sources | Purchase order check at confirmation with three levels and an optional scope check. |
| Retaining records | Deletion refused on dossiers past draft, on started assessments, on planned audits, on confirmed evaluations, on completed reviews, and on every signature entry. |
| Producing evidence for an inspection | Three QWeb PDF reports, including a dossier report that consolidates scope, assessments, audits, performance, reviews and the signature log. |

## 2.4 Electronic records and signatures — precise statement

21 CFR Part 11 is commonly described as requiring, for a signature that is not
based on biometrics, at least two distinct identification components, and
requiring signed records to carry the printed name of the signer, the date and
time, and the meaning of the signature.

What this module implements:

* **Printed name of the signer** — `user_id`, resolved to the user's name in
  the log view and in the dossier report.
* **Date and time** — `signed_on`, a UTC datetime written by the server.
* **Meaning of the signature** — `meaning`, a closed selection list
  (authored, reviewed, approved, conditionally approved, rejected, suspended,
  reinstated, disqualified, verified).
* **Justification** — `reason`, free text, mandatory in both wizards.
* **Link to what was signed** — `res_model`, `res_id`, `signed_record_name`
  and a JSON snapshot of the signed values.
* **Detection of alteration** — an ORM guard that refuses `write` and `unlink`
  on the log, plus a SHA-256 chain over the whole company log and a
  verification action that recomputes it.

What this module **does not** implement, stated so that it is not assumed:

* **Re-authentication at the moment of signing.** The wizard asks the signer to
  retype their own login and rejects a mismatch. That confirms intent; it is
  not a second identification component, because the session is already open.
  Password or second-factor re-authentication is delegated to
  `ls_electronic_signature`, which does not exist yet in the suite.
* **Session controls, password ageing and account lockout.** These are Odoo
  platform and infrastructure concerns.
* **A general audit trail on every field of every model.** The module tracks a
  chosen set of fields through `mail.thread`, and logs decisions. Field-level
  tracking across the suite is the scope of `ls_audit_trail`.

Until `ls_electronic_signature` is deployed, an organisation that needs the
second identification component must cover it by other documented means — for
example a short session timeout combined with a procedural control — and must
say so in its own validation documentation. The module makes this visible to
the signer in the approval dialog rather than hiding it.

## 2.5 Data integrity (ALCOA+) — what the module contributes

| Principle | Contribution of this module |
|-----------|-----------------------------|
| Attributable | Every decision carries a user; the signature log names the signer and the meaning. |
| Legible | Records are structured fields, not free text; reports render them in a fixed layout. |
| Contemporaneous | Dates are stamped by the server at the moment of the action (`approval_date`, `report_date`, `closure_date`, `signed_on`). |
| Original | Signature entries cannot be modified; the JSON snapshot freezes the signed values. |
| Accurate | SQL and Python constraints reject impossible values; scoring rules are frozen so a result cannot change retroactively. |
| Complete | Prerequisite checks refuse an approval on incomplete evidence; audit closure refuses open findings. |
| Consistent | The state machines allow only defined transitions; the scoring formula is single-sourced. |
| Enduring | Deletion is refused on records past their draft stage. |
| Available | Three PDF reports plus standard Odoo export. |

The module contributes to these principles. It does not deliver them on its
own: backup, restoration, access control and infrastructure integrity are
outside it.

## 2.6 Regulatory items deliberately left to the organisation

| Item | Why it is not in the module |
|------|-----------------------------|
| Deciding which frameworks apply | A regulatory determination, not a software setting. |
| Deciding criticality levels and intervals | The shipped values are proposals; they must be reviewed and approved before use. |
| Writing the criteria | Criteria carry the organisation's own expectations; the shipped set is a starting point. |
| Quality agreements | A contractual document; the module records that a criterion covering it was assessed. |
| Computer system validation of this module | See Phase 11 approach in `doc/14_validation_report.md`. The module is designed to support validation; it is not validated by being installed. |

---

**Phase 2 gate: PASS**, with three limits recorded above (§2.1) and carried
forward into the compliance checklist. No claim of compliance is made anywhere
in the module. Phase 3 may start.
