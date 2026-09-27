# Phase 2 — Regulatory Analysis

## 0. Statement of verification

**This information could not be verified from official documentation.**

No regulatory text was consulted during the production of this module: the
environment has no network access. Every statement below is therefore an
**architectural recommendation** about *what a complaint handling process
generally has to do*, not a citation, a paraphrase or an interpretation of any
regulation. Nothing here should be quoted in a regulatory submission.

Three consequences follow, and they are binding on any user of this module:

1. **The module is not compliant with anything.** Software cannot be compliant
   on its own. Compliance results from procedures, validation, training,
   governance and evidence, of which software is one input.
2. **No deadline, threshold or classification in this module comes from a
   regulation.** Where a regulation would impose a value, the module exposes a
   configuration field defaulting to *not configured*.
3. **The mapping in section 3 is a mapping of intent**, produced by reasoning
   about the process, not by reading the standards. It must be re-derived by the
   organisation's own Regulatory Affairs function against the actual texts.

## 1. Frameworks the deploying organisation is likely to invoke

The source specification (section 3.1) lists the frameworks the Life Sciences
Suite addresses. Those plausibly relevant to complaint handling are listed
below. Their titles are reproduced as given in the source specification; their
content was not verified here.

| Framework | Relevance to complaint handling, as reasoned here |
|---|---|
| ISO 9001:2015 | Customer feedback, non-conformity, corrective action, management review inputs. |
| ISO 13485:2016 | Feedback and complaint handling, and reporting to regulatory authorities, for medical devices. |
| ISO 14971:2019 | Post-production information feeding back into risk management. |
| ISO 22716:2007 | Complaint handling within cosmetics good manufacturing practice. |
| ISO 15378:2017 | Complaint handling for primary packaging materials for medicinal products. |
| GMP (WHO, EU, national — including Algerian BPF recognised by ANPP) | Complaints and product defect handling, decision on recall, record retention. |
| EU MDR 2017/745 | Vigilance and post-market surveillance obligations for devices. |
| EU Cosmetics Regulation 1223/2009 | Undesirable effects and serious undesirable effects. |
| FDA 21 CFR Part 11 | Electronic records and electronic signatures, where records are kept electronically. |
| ANPP requirements (Algeria) | National pharmaceutical requirements applicable to the marketing authorisation holder. |

## 2. How the module supports implementation — and how it does not

| Process expectation | Module support | Honest limitation |
|---|---|---|
| Every complaint is recorded | Unique sequence, mandatory receipt data, no deletion after the initial state, cancellation with a reason instead of deletion | Nothing prevents a complaint from never being entered; that is a procedural and training matter |
| Complaints are evaluated for their consequences | Assessment state with mandatory summary, safety and regulatory impact flags, severity and type | The evaluation criteria themselves are not encoded; they live in the organisation's procedure |
| Complaints that may be reportable are identified | Separate adverse event records with seriousness, outcome, causality and a mandatory reportability rationale | The module does **not** decide reportability and contains no reportability rules |
| Reports reach the authority in time | Configurable deadline, derived due date, daily notification, mandatory acknowledgement reference before submission is recorded | The deadline is `0` (not configured) until Regulatory Affairs sets it; the module cannot transmit anything to any authority |
| Investigations establish root cause | Investigation records with methodology, root cause category and description, conclusion, batch impact assessment | The quality of the analysis is a human matter |
| Investigations are independently reviewed | Approval blocked for the investigator of that record | A user in both groups can still investigate one complaint and approve another, which is the intended design |
| Actions are taken and evidenced | Resolution records with mandatory completion evidence and completion date | The module does not verify the evidence |
| Complaints feed corrective action | `capa_required`, `capa_justification`, mandatory `capa_reference` before resolution when a CAPA was declared | There is **no CAPA module**; the reference is free text and is not verified against anything |
| Complaints feed recall decisions | Resolution types `field_safety_notice` and `recall_initiated`; `other_batches_impacted` on the investigation | Recall execution is out of scope |
| Records are reviewed before closure | Closure wizard requiring a reviewer distinct from the responsible user, a closure summary and an effectiveness confirmation | The effectiveness confirmation is a declaration, not a measurement |
| Records are protected after closure | `write()` refuses any change to closed or cancelled complaints; the same applies to approved investigations, done resolutions and closed adverse events | An administrator with database access can still change anything |
| Complaints are trended | List, graph and pivot views; group by product, category, root cause, severity, month | No automatic signal detection |
| Records can be produced for an inspection | QWeb PDF containing the complaint, its investigations, adverse events, resolutions and closure | Attachments are not embedded in the PDF |

## 3. Traceability of module controls to process expectations

The legend of the source specification's matrix is reused: **S** means *supports
implementation of processes aligned with this framework*. It does not mean
certified, verified or compliant.

| Module control | ISO 9001 | ISO 13485 | ISO 14971 | ISO 22716 | ISO 15378 | GMP | EU MDR | 21 CFR 11 |
|---|---|---|---|---|---|---|---|---|
| Unique reference, no deletion after intake | S | S | — | S | S | S | S | — |
| Classification and severity | S | S | S | S | S | S | S | — |
| Documented assessment with impact flags | S | S | S | S | S | S | S | — |
| Adverse event record with reportability rationale | — | S | S | S | — | S | S | — |
| Configurable reporting deadline and notification | — | S | — | S | — | S | S | — |
| Root cause investigation | S | S | S | S | S | S | S | — |
| Independent approval of the investigation | S | S | — | S | S | S | S | — |
| Resolution with completion evidence | S | S | — | S | S | S | S | — |
| CAPA linkage fields | S | S | — | S | S | S | S | — |
| Closure review by a distinct reviewer | S | S | — | S | S | S | S | — |
| Freezing of final records | S | S | — | S | S | S | S | partial |
| Field-level change history (`mail.thread`) | S | S | — | S | S | S | S | partial |
| Role-based access and record rules | S | S | — | S | S | S | S | partial |
| Printable complaint record | S | S | — | S | S | S | S | — |

## 4. Electronic records and signatures — an explicit warning

The module records who changed a tracked field and when, through the standard
Odoo `mail.thread` mechanism, and it prevents modification of final records
through server-side `write()` guards.

That is **not** an electronic signature, and it is very likely **not** a
sufficient audit trail for FDA 21 CFR Part 11 purposes. In particular the module
does **not** provide:

1. re-authentication at the moment of an approval or a closure;
2. a recorded *meaning* of each signature (author, approver, reviewer);
3. a tamper-evident, independently verifiable audit trail (no hash chaining);
4. protection against modification by a database administrator;
5. a signature manifestation printed on the record.

The source specification allocates these functions to two separate modules,
`ls_electronic_signature` (section 7.14) and `ls_audit_trail` (section 7.15).
Until those exist and are integrated, an organisation subject to 21 CFR Part 11
must not rely on this module alone for signed or audited records. This is stated
here rather than in a footnote because the opposite assumption is the most
likely and most damaging misuse of this module.

## 5. Personal data

Adverse event records concern natural persons. The module deliberately offers
only a pseudonym field, an age range and a sex, with an on-screen warning, and
holds no free-text identity field. Complainant identity is held in `res.partner`
and in three contact fields. The deploying organisation remains responsible for
its own data protection obligations, including retention, access and erasure,
none of which this module implements.

## Phase 2 gate

**PASS** — the applicable frameworks are listed, the support is described
without any claim of compliance, the limitations are stated explicitly, and no
regulatory value is encoded in the software.
