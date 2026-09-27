# PHASE 2 — REGULATORY ANALYSIS

Module: `ls_training` — Life Sciences Training Management

---

## 1. Mandatory statement

**This module does not make any organisation compliant with any regulation.**

Software cannot deliver compliance. Compliance is produced by an
organisation's procedures, its trained personnel, its quality system and
its own validation of the tools it uses. This module is one such tool. It
is designed so that an organisation implementing training processes can
record and retrieve evidence of those processes.

No statement in this document should be read as a claim of certification,
conformity assessment, or approval by any regulatory authority.

Where a requirement is quoted or summarised below, it is described from
published standard descriptions and published regulatory texts. **Clause
numbers and their exact wording could not be verified from the official
paid standard texts**, which are not freely available. Organisations must
read the applicable standard themselves and reach their own conclusion.

## 2. Frameworks considered, and their relevance to *this* module

The Life Sciences Suite specification lists thirteen frameworks. Only those
with a direct bearing on personnel training and competence are analysed
here. Frameworks with no training-specific bearing on this module are
listed in §4 and explicitly excluded, rather than being padded into the
analysis.

| Framework | Relevant to `ls_training`? | Basis |
|-----------|---------------------------|-------|
| ISO 9001:2015 | **Yes** | Contains requirements on competence, awareness and documented information as evidence of competence |
| ISO 13485:2016 | **Yes** | Contains requirements on human resources, competence and training effectiveness for medical device QMS |
| GMP (WHO, EU, national) | **Yes** | GMP guidance consistently requires trained personnel and records of that training |
| ANPP requirements (Algeria) | **Partly — unverified** | See §3.4 |
| ISO 22716:2007 (cosmetics GMP) | **Yes** | Contains personnel training provisions |
| ISO 15378:2017 (primary packaging GMP) | **Yes** | Applies GMP principles including personnel competence to packaging material manufacture |
| FDA 21 CFR Part 11 | **Partly — see §3.5** | Applies to electronic records and signatures; this module produces electronic records but does **not** implement Part 11 controls |
| FDA 21 CFR Part 211 | **Yes** | US drug GMP contains explicit personnel training provisions |
| ISO 14971:2019 | **No** | Risk management for devices; no training-record requirement addressed by this module |
| EU MDR 2017/745 | **Marginal** | Personnel competence is referenced but the module implements nothing MDR-specific |
| EU Cosmetics Regulation 1223/2009 | **No** | No training-record requirement addressed by this module |
| GS1 standards | **No** | Barcoding and serialisation; not applicable |
| ICH guidelines | **No** | Quality/safety/efficacy guidance; no training-record requirement addressed here |

## 3. How the module supports implementation

### 3.1 Competence and training records (ISO 9001, ISO 13485, GMP)

These frameworks broadly expect an organisation to determine the
competence needed, provide training where there is a gap, evaluate the
result, and retain evidence.

| Expectation | Module capability | Where |
|-------------|-------------------|-------|
| Determine required competence per role | Training requirements target a job position, department or individual | `ls.training.requirement` |
| Identify the gap | Training matrix reports every employee/course cell as trained, expiring, expired or not trained | `ls.training.matrix.wizard` |
| Provide training | Session scheduling and delivery lifecycle | `ls.training.session` |
| Evaluate the result | Attendance with derived pass/fail from presence and assessment score | `ls.training.attendance.result` |
| Retain evidence | Certification records that cannot be deleted, plus printable individual training record | `ls.training.certification`, training record report |
| Retain competence evidence distinct from attendance | Assessment records with named assessor, level and written evidence | `ls.training.competency.assessment` |

**What the module does not do here.** It does not evaluate *effectiveness*
of training in the sense some standards intend — that is, whether the
training changed behaviour on the job. A passing score evidences knowledge
at a point in time. Organisations requiring effectiveness checks should
use competency assessments performed after a delay, and should define that
practice in their own procedure. The module supports it; it does not
enforce it.

### 3.2 Training against approved material (GMP)

GMP expects training to be delivered against controlled, current material.

The course model carries an explicit four-state lifecycle
(Draft → Under Review → Approved → Obsolete) and a version field. Sessions
can only reference courses in the Approved state, enforced by the
`course_id` domain and by the state machine. When a certification is
issued, the course version in force at that moment is copied onto the
certification and never changes afterwards, so a later revision of the
course does not retroactively alter what an employee was trained on.

**Limitation.** The course record is not a controlled document in the sense
of a document management system. It has no attachment control, no review
periodicity and no independent approver enforcement — one user holding the
Manager group can move a course from Draft to Approved alone. Organisations
requiring segregated document control should integrate
`ls_document_management` and `ls_electronic_signature` from the suite.

### 3.3 Periodic requalification (GMP, ISO 13485)

Time-limited qualification is modelled through `validity_months` on the
course, which derives an expiry date on each certification. A daily
scheduled action re-evaluates status so that expiry is detected without
human intervention, and a second action notifies affected employees within
a configurable warning window.

**Limitation.** Notification is by email to the employee's work email
address. Employees without a work email receive nothing, and the module
does not escalate to a manager. This is a documented gap, not a hidden one.

### 3.4 ANPP requirements (Algeria)

**This information could not be verified from official documentation.**

The suite specification lists the Agence Nationale des Produits
Pharmaceutiques as an applicable authority for pharmaceutical
manufacturing in Algeria. Specific ANPP requirements concerning personnel
training records — their required content, retention period, language or
format — **could not be verified from official ANPP publications** during
the preparation of this module.

Consequently:

- No ANPP-specific field, report or workflow has been implemented.
- No claim is made that this module satisfies any ANPP expectation.
- Organisations subject to ANPP oversight must obtain the applicable
  requirements directly from the authority and assess whether this module,
  as configured in their environment, supports them.

Inventing plausible-looking ANPP requirements would have been worse than
useless, so none were invented.

### 3.5 FDA 21 CFR Part 11 — explicit non-claim

Part 11 concerns electronic records and electronic signatures. This module
creates electronic records. **It does not implement Part 11 controls.**

| Part 11 subject area | Status in this module |
|----------------------|----------------------|
| Electronic signatures | **Not implemented.** No signature manifestation, no signature meaning, no re-authentication at point of signing. Approval actions are ordinary button clicks governed by group membership. |
| Audit trail (secure, computer-generated, time-stamped, recording operator, old and new values, not obscuring prior entries) | **Not implemented as such.** The module uses Odoo's `mail.thread` change tracking on selected fields of four models. This is not a complete field-level audit trail and does not cover all models or all fields. |
| Record retention and retrieval | **Partly supported.** Certifications cannot be deleted; closed attendance cannot be modified; training records are printable. Retention policy enforcement is not implemented. |
| Copy generation for inspection | **Supported.** Two QWeb PDF reports plus standard Odoo export. |
| Limiting system access to authorised individuals | **Supported** through the four-group model, access-control lists and record rules. |
| Operational system checks enforcing sequencing | **Supported.** The session and course state machines refuse out-of-order transitions. |
| Authority checks | **Supported** at group level. |
| Device checks, training of persons who develop the system, written policies on signature accountability | **Organisational, not software.** Out of scope for any module. |

An organisation requiring Part 11 must implement `ls_electronic_signature`
and `ls_audit_trail` from the suite, and must validate the resulting
combined system. This module alone is not sufficient and does not claim to
be.

### 3.6 Data integrity (ALCOA+)

| Principle | How the module supports it | Gap |
|-----------|---------------------------|-----|
| **A**ttributable | Odoo records create/write user on every record; assessments name the assessor explicitly | Attribution relies on Odoo core, not on a module-level audit trail |
| **L**egible | Structured fields, printable reports | — |
| **C**ontemporaneous | Session dates, assessment dates and grant dates are recorded; the grant date is taken from the session end | Nothing prevents back-dating a manual certification |
| **O**riginal | Course version frozen at issuance; attendance frozen at closure | — |
| **A**ccurate | Outcome derived from evidence rather than typed; range constraints on scores and dates | — |
| **C**omplete | Failed attendances are retained; renewals add records rather than replacing them; certifications cannot be deleted | — |
| **C**onsistent | Single state machine per model; deterministic derivation | — |
| **E**nduring | Deletion blocked on certifications, confirmed assessments and closed-session attendance | Retention scheduling not implemented |
| **A**vailable | Search, filters, matrix and reports | — |

## 4. Frameworks explicitly excluded from this module

| Framework | Why nothing was implemented |
|-----------|----------------------------|
| ISO 14971:2019 | Device risk management. No training-record requirement is addressed by this module. Implemented in `ls_risk_management`. |
| EU Cosmetics Regulation 1223/2009 | Product-level obligations (safety assessment, PIF, labelling). Nothing training-specific implemented here. |
| GS1 | Identification and serialisation. Not applicable. |
| ICH Q7/Q9/Q10 etc. | Referenced by the suite for pharmaceutical quality; this module implements no ICH-specific artefact. |
| EU MDR 2017/745 | Personnel competence is expected, but the module contains no MDR-specific field, code or report, so no support is claimed beyond the generic competence capability in §3.1. |

## 5. Regulatory support matrix for this module

Using the suite convention: **S** = supports implementation of processes
aligned with the framework; **—** = no direct support implemented;
**N/C** = not claimed.

| Capability | ISO 9001 | ISO 13485 | GMP | ISO 22716 | ISO 15378 | 21 CFR 211 | 21 CFR 11 |
|-----------|----------|-----------|-----|-----------|-----------|------------|-----------|
| Role-based training requirements | S | S | S | S | S | S | — |
| Training gap identification | S | S | S | S | S | S | — |
| Delivery against approved material | S | S | S | S | S | S | — |
| Attendance and assessment evidence | S | S | S | S | S | S | — |
| Certification with frozen course version | S | S | S | S | S | S | — |
| Periodic requalification and expiry alerting | S | S | S | S | S | S | — |
| Competency assessment by named assessor | S | S | S | S | S | S | — |
| Individual training record output | S | S | S | S | S | S | — |
| Access control by role | S | S | S | S | S | S | S |
| Enforced operational sequencing | S | S | S | S | S | S | S |
| Electronic signature | — | — | — | — | — | — | **N/C** |
| Field-level audit trail | — | — | — | — | — | — | **N/C** |
| Record retention enforcement | — | — | — | — | — | — | **N/C** |

## 6. Conclusion

The module supports implementation of training and competence processes of
the kind expected by ISO 9001, ISO 13485, GMP guidance, ISO 22716 and
ISO 15378, and by the personnel provisions of FDA 21 CFR Part 211.

It does **not** implement FDA 21 CFR Part 11 controls, and does not claim
to. It implements nothing ANPP-specific, because ANPP training-record
requirements could not be verified from official sources.

Any organisation intending to rely on this module in a regulated context
must validate it in its own environment, against its own user requirements,
under its own quality system. Nothing in this module substitutes for that.
