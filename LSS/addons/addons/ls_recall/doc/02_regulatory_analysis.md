# Phase 2 — Regulatory Analysis

Module: `ls_recall` — Recall and Field Action Management

---

## 1. Statement of what this document is and is not

This module **supports** an organisation in implementing processes that
several regulatory frameworks require. It does **not** make an
organisation compliant, and nothing in it is certified against any
framework. Compliance depends on the organisation's procedures, the
validation it performs, the competence of its staff and the way it
actually uses the system.

Each mapping below cites the provision it implements structure for.
Where a provision is paraphrased, it is paraphrased; the module does not
reproduce regulatory text.

## 2. Frameworks considered, and why each is or is not in scope

| Framework | In scope | Reason |
|-----------|----------|--------|
| 21 CFR Part 7, Subpart C (Recalls) | Yes | It is the most explicit published description of recall strategy, depth, public warning, effectiveness checks and status reporting. Its structure is used as the module's data model even where an organisation is not FDA-regulated. |
| EudraLex Volume 4, Part I, Chapter 8 | Yes | Governs complaints, quality defects and product recalls for EU GMP, including the expectation of rehearsal. |
| Regulation (EU) 2017/745 (MDR) | Yes | Defines the field safety corrective action and the field safety notice, and the obligation to report them. |
| ISO 13485:2016 | Partly | Clause 8.3 (control of nonconforming product) and 8.2.3 (reporting to regulatory authorities) are supported structurally. The module is not a full QMS. |
| ISO 9001:2015 | Partly | Clause 8.7 (nonconforming outputs) and 10.2 (nonconformity and corrective action) are supported by reference; CAPA itself is out of scope. |
| ICH Q9 | Partly | Risk-based decisions on depth and sampling level are recorded, not calculated. |
| ANPP (Algeria) requirements | **Not mapped** | See §5. |
| ISO 22716, ISO 15378, ISO 14971 | Not mapped | These concern cosmetics GMP, primary packaging GMP and device risk management respectively. None of them defines a recall procedure that this module implements structure for. Claiming a mapping would be padding. |
| 21 CFR Part 11 | Deliberately **not claimed** | See §4. |

## 3. Provision-by-provision mapping

### 3.1 United States — 21 CFR Part 7, Subpart C

| Provision | Substance | Where implemented |
|-----------|-----------|-------------------|
| 7.3(g), (j), (k) | Recall, market withdrawal and stock recovery are three distinct things. | `action_type` selection; `constants.ACTION_TYPE_SELECTION` |
| 7.3(m) | Three health hazard classes, distinguished by the probability and seriousness of the consequence. | `classification` field; the three definitions are paraphrased in `constants.CLASSIFICATION_HELP` and shown as field help |
| 7.41 | A health hazard evaluation informs classification; the classification is assigned by the agency. | `health_hazard_evaluation`, `hhe_user_id`, `hhe_date`. The field help states that the recorded value is the organisation's own assessment and, where applicable, the classification communicated by the authority. |
| 7.42(b)(1) | The strategy specifies the level in the distribution chain to which the recall extends. | `depth` field: wholesale, retail, consumer/user |
| 7.42(b)(2) | A public warning may be given through the general news media or through specialised media. | `public_warning` field with those three options |
| 7.42(b)(3) | Effectiveness checks are made at levels A to E, expressed as a percentage of consignees, and may be made by visit, telephone or letter. | `effectiveness_level`; `EFFECTIVENESS_LEVEL_COVERAGE` (A=100, C=10, D=2, E=0); level B is user-entered and constrained to be strictly between 10 and 100; `method` selection |
| 7.49(a) | A recall communication identifies the product and its codes, explains the reason and the hazard, gives instructions, and asks for a response. | The five `content_*` confirmations, enforced before a notice may be approved or sent; the printed notice template lays the sections out in this order |
| 7.49(b) | Recall communications are marked to convey urgency. | `urgent` boolean, rendered as a banner on the printed notice |
| 7.53 | Recall status reports are made periodically, covering consignees notified, responses, quantities, and effectiveness checks. | `ls.recall.report` with type initial/status/final and the frozen figure set |

**Limits of this mapping.** Part 7 addresses recalls that are voluntary
or requested by the agency, and much of it describes what the *agency*
does. The module implements the firm's side only. It does not classify
recalls: classification under 7.41 is assigned by the authority, and the
field records what the organisation assessed and what it was told.

### 3.2 European Union — EudraLex Volume 4, Part I, Chapter 8

| Expectation | Where implemented |
|-------------|-------------------|
| Written procedures for recall exist in advance and allow a recall to be initiated promptly at any time. | `ls.recall.plan` as an approved, versioned document; approval is refused without a documented procedure |
| A person is designated to execute and coordinate recalls, with sufficient independence and out-of-hours availability. | `responsible_user_id` and mandatory `deputy_user_id` on an approved plan |
| Recall operations are recorded and a final report reconciles delivered and recovered quantities. | The reconciliation fields and the final report with frozen figures |
| Competent authorities are informed. | `authority_notification` communication type; `authority_notified` and its date on the recall; a closure gate for class I and II recalls |
| The effectiveness of the recall arrangements is evaluated periodically. | `mock_recall` action type, `mock_recall_interval_months`, `next_mock_recall_date` and the scheduled reminder |

### 3.3 European Union — Regulation (EU) 2017/745 (MDR)

| Provision | Substance | Where implemented |
|-----------|-----------|-------------------|
| Article 2(68) | Defines a field safety corrective action. | `action_type = fsca` |
| Article 89(8) | A field safety notice informs users of an FSCA. | `communication_type = field_safety_notice`, subject to the same content confirmations as a recall notice |
| Article 87 | Serious incidents and FSCAs are reported to the competent authority. | `authority_notification` communication type and the recall-header notification record |

**Limit.** The module does not submit anything to Eudamed and does not
generate the MDR-prescribed notice format. It records that a notice was
issued, to whom and when.

## 4. Why 21 CFR Part 11 compliance is *not* claimed

Part 11 Subpart C requires, among other things, that an electronic
signature be unique to one individual, that the identity of the
individual be verified before the credential is issued, and that the
signature be linked to its record so it cannot be transferred or
excised. Those requirements are satisfied by an organisation's identity
and credential controls together with system controls — not by a text
field.

Accordingly:

* The closure `attestation` field is a free-text field. It is labelled
  in the view and documented in the model and the manuals as **not** an
  electronic signature. Its intended use is to carry a reference to a
  signed record held elsewhere.
* Approvals record the acting user and the server timestamp
  (`approved_by_user_id` / `approval_date` and equivalents). This is
  attribution, which is useful and auditable, and it is described as
  attribution, not as signature.
* Where the module does something that assists Part 11 objectives —
  attributable and timestamped entries, restricted alteration of
  finalised records, chatter-based change history — it is stated as
  supporting the objective, not as satisfying the rule.

An organisation that needs Part 11 signatures should implement them at
suite level and integrate them here.

## 5. ANPP (Algeria) — why no mapping is asserted

The source specification lists ANPP requirements as a framework.

**This information could not be verified from official documentation.**
No ANPP-published text setting out recall procedure requirements was
available to confirm during this work. Rather than invent a mapping, the
module asserts none.

What the module does instead: the elements ANPP would in practice look
for — a designated coordinator with out-of-hours cover, traceability
from lot to consignee, dated notification of the authority, quantitative
reconciliation, and a final report — are all present and are driven by
the mappings above. An implementing organisation should compare them
against the current ANPP text and record the result of that comparison
in its own validation file. Section 6 of
`13_validation_report.md` reserves a place for it.

## 6. Data integrity (ALCOA+) — honest position

| Principle | Position |
|-----------|----------|
| Attributable | Supported. Every workflow action records the acting user; Odoo's chatter records field changes on tracked fields. |
| Legible | Supported. |
| Contemporaneous | Partly. The system timestamps when an entry is *made*, which is not necessarily when the event occurred. Fields such as `sent_date` are set at the moment the user records the sending. |
| Original | Partly. The module holds the record of the action; it is not the original of a paper notice signed by a consignee. |
| Accurate | Supported by constraints, not guaranteed. |
| Complete, Consistent, Enduring, Available | Supported at application level; depends on the organisation's backup, retention and archival arrangements, which are outside the module. |

A full audit trail over every field of every model is **not** provided by
this module. Odoo's chatter tracks the fields marked `tracking=True`.
A general field-level audit trail is the concern of a dedicated module
(the source specification's `ls_audit_trail`), which is not a dependency
here.
