# PHASE 1 — BUSINESS ANALYSIS

Module: `ls_training` — Life Sciences Training Management
Platform: Odoo 19.0 Community Edition

---

## 1. Business objectives

| # | Objective | Measurable outcome |
|---|-----------|--------------------|
| BO-1 | Maintain a complete, reconstructable training record for every employee | Any employee's full training history can be printed from one screen |
| BO-2 | Make training gaps visible before they become findings | A named person can list every mandatory course an employee lacks, at any time |
| BO-3 | Prevent silent expiry of time-limited qualifications | Every certification approaching expiry triggers a notification before the expiry date |
| BO-4 | Ensure training is delivered only against approved material | No session can be scheduled against unapproved course content |
| BO-5 | Separate "was trained" from "is competent" | Competency can be evidenced independently of classroom attendance |
| BO-6 | Preserve training evidence against retroactive alteration | Closed attendance and issued certifications cannot be edited or deleted |

## 2. Business requirements

### 2.1 Course and material control

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-01 | Courses carry a unique code, an explicit version, a duration and a type | Must |
| BR-02 | Courses follow an approval lifecycle before use | Must |
| BR-03 | A course states how long its certification remains valid | Must |
| BR-04 | A course states whether an assessment is required and at what pass mark | Must |
| BR-05 | A course may grant one or more competencies | Should |
| BR-06 | Retired courses remain readable but cannot be scheduled | Must |

### 2.2 Delivery

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-07 | Sessions schedule an approved course for a defined population | Must |
| BR-08 | Employees can be registered individually or in bulk by department, job or requirement | Must |
| BR-09 | Session capacity is enforced | Should |
| BR-10 | Each session names exactly one responsible trainer, internal or external | Must |
| BR-11 | Attendance and assessment score are recorded per attendee | Must |
| BR-12 | A session cannot be closed while any attendee outcome is undetermined | Must |

### 2.3 Certification

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-13 | Closing a session issues certifications to passing attendees automatically | Must |
| BR-14 | Externally delivered training can be recorded manually | Must |
| BR-15 | The course version is frozen on the certification at issuance | Must |
| BR-16 | Expiry is derived from course validity but can be overridden for external training | Must |
| BR-17 | Renewal creates a new record; history is never overwritten | Must |
| BR-18 | Certifications can be revoked with a documented reason, never deleted | Must |
| BR-19 | A printable certificate can be produced per certification | Should |

### 2.4 Requirements and the training matrix

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-20 | Training requirements target a job position, a department, or a named employee | Must |
| BR-21 | Requirements are flagged mandatory or advisory | Must |
| BR-22 | A matrix reports every employee/course cell with its status | Must |
| BR-23 | Each employee carries a computed training compliance rate | Must |
| BR-24 | An individual training record can be printed per employee | Must |

### 2.5 Competency

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-25 | Competencies are defined master data with a minimum acceptable level | Must |
| BR-26 | A named assessor records the demonstrated level with written evidence | Must |
| BR-27 | An employee cannot assess their own competency | Must |
| BR-28 | Confirmed assessments become read-only | Must |
| BR-29 | Competencies may require periodic reassessment | Should |

### 2.6 Notification

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-30 | Certifications entering the warning window are notified to the employee | Must |
| BR-31 | The warning window is configurable | Must |
| BR-32 | Certification status refreshes automatically as time passes | Must |

## 3. Stakeholders

| Stakeholder | Interest in this module | Primary concern |
|-------------|------------------------|-----------------|
| Training Coordinator | Daily operator: schedules sessions, records outcomes | Speed of bulk registration and outcome capture |
| Quality Assurance | Reviews evidence, responds to audit questions | Completeness and immutability of records |
| Department Manager | Accountable for their team's qualification | Visibility of gaps before they block work |
| Employee (Learner) | Subject of the records | Access to own record; advance notice of expiry |
| Human Resources | Owns employee master data | Consistency with job positions and departments |
| Regulatory Affairs | Prepares for inspection | Traceability from requirement to evidence |
| Auditor (internal or external) | Samples and challenges records | Ability to reconstruct any outcome from its inputs |
| System Administrator | Operates the instance | Scheduled actions, parameters, access rights |
| Validation Engineer | Qualifies the system | Testability and documented design intent |

## 4. User roles

| Role | Group | Capability |
|------|-------|------------|
| Learner | `group_ls_training_learner` | Read own attendance, certifications and assessments only |
| Viewer | `group_ls_training_viewer` | Read all training records within allowed companies |
| Trainer | `group_ls_training_trainer` | Create and run sessions, register attendees, record outcomes, close sessions, record assessments |
| Manager | `group_ls_training_manager` | All of the above, plus course approval, requirements, competency master data, revocation and deletion where permitted |

Each group implies the one below it.

## 5. User stories

| ID | As a… | I want to… | So that… |
|----|-------|-----------|----------|
| US-01 | Training Coordinator | schedule a session for an approved course | delivery is planned against controlled material |
| US-02 | Training Coordinator | register a whole department in one action | I do not add thirty attendees by hand |
| US-03 | Training Coordinator | skip employees who are already certified | I do not retrain people unnecessarily |
| US-04 | Trainer | record presence and score per attendee | the outcome follows from recorded evidence |
| US-05 | Trainer | close the session in one action | certificates are issued without manual transcription |
| US-06 | QA Reviewer | see that a closed session can no longer be edited | I can rely on the record |
| US-07 | QA Reviewer | revoke a certification with a written reason | an invalidated qualification is withdrawn traceably |
| US-08 | Department Manager | see which of my staff lack a mandatory course | I can act before it blocks production |
| US-09 | Department Manager | see a compliance percentage per employee | I can prioritise |
| US-10 | Employee | see my own certifications and their expiry dates | I know what I must renew |
| US-11 | Employee | receive a reminder before my qualification lapses | I am not stopped at the door |
| US-12 | Quality Manager | define that every Production Operator must hold GMP Fundamentals | the requirement is a rule, not a habit |
| US-13 | Quality Manager | approve course material before it is used | delivery follows document control |
| US-14 | Assessor | record that I observed an employee performing a task competently | competence is evidenced separately from attendance |
| US-15 | Regulatory Affairs | print an individual training record | I can answer an inspector in one page |
| US-16 | Auditor | reconstruct why an attendee passed | the derivation is transparent |
| US-17 | Administrator | change the expiry warning window | notification timing suits our planning cycle |
| US-18 | Training Coordinator | record externally delivered training | the record is complete regardless of provider |

## 6. Use cases

### UC-01 Deliver a training session

**Actor:** Trainer · **Precondition:** an approved course exists

1. Trainer creates a session for the course, sets dates, location and trainer.
2. Trainer registers attendees (individually or via the bulk wizard).
3. Trainer confirms the session; the system requires at least one attendee.
4. Trainer starts the session.
5. Trainer records presence and, where required, the assessment score.
6. Trainer closes the session.
7. System verifies no outcome is pending, issues certifications to passing attendees, and freezes the attendance evidence.

**Alternate 6a:** an outcome is still pending — the system refuses to close and names the count.
**Alternate 7a:** an attendee failed — no certification is issued for them; the attendance record retains the failure.

### UC-02 Identify a training gap

**Actor:** Department Manager

1. Manager opens the Training Matrix and scopes it to their department.
2. System resolves the applicable requirements per employee, finds the latest certification per employee/course, and reports a status.
3. Manager filters on "Gaps".
4. Manager groups by course to size the remediation.

### UC-03 Handle an approaching expiry

**Actor:** System, then Employee

1. The daily scheduled action refreshes certification statuses.
2. Certifications entering the warning window become "Expiring Soon".
3. The reminder action emails the affected employees.
4. Employee or coordinator schedules a refresher session.
5. On closure, a new certification is issued; the previous one remains in the history and lapses on its own date.

### UC-04 Revoke a certification

**Actor:** Quality Manager

1. Manager opens the certification and selects Revoke.
2. System requires a written reason.
3. Manager confirms; status becomes Revoked, terminally.
4. The record remains in the employee's history and on the printed training record.

### UC-05 Qualify a course for use

**Actor:** Quality Manager

1. Manager creates the course in Draft.
2. Manager submits it for review.
3. Manager approves it.
4. The course becomes selectable on sessions. Retiring it later is blocked while open sessions exist.

## 7. Functional scope

**In scope**

- Course master data with a four-state approval lifecycle
- Session scheduling and a five-state delivery lifecycle
- Attendance capture with derived pass/fail outcome
- Automatic certification issuance on session closure
- Manual certification entry for external training
- Certification expiry, warning window and revocation
- Competency master data and assessment records
- Training requirements by job, department or individual
- ORM-based training matrix with list and pivot views
- Per-employee compliance rate and printable training record
- Printable certificate
- Two daily scheduled actions and one email template
- Four-level role model with record-rule scoping and multi-company isolation

**Out of scope (with rationale)**

| Excluded | Rationale |
|----------|-----------|
| Integration with `website_slides` (Odoo eLearning) | Would impose a hard dependency on the whole website stack on every installation. The module instead models external e-Learning as a delivery mode with a URL. A separate bridge module `ls_training_website_slides` is the correct home for this. |
| Part 11 electronic signature on training records | Belongs to `ls_electronic_signature` in the suite specification. This module deliberately does not implement a second, divergent signature mechanism. Integration point documented in the developer manual. |
| Field-level audit trail | Belongs to `ls_audit_trail`. This module uses Odoo's `mail.thread` tracking on key fields as an interim measure and does not claim to satisfy audit-trail requirements. |
| Linking training to controlled SOP documents | Requires `ls_document_management`. Left to a bridge module so `ls_training` remains installable standalone on `base`, `mail` and `hr`. |
| Training cost, budget and supplier invoicing | Financial scope; no business requirement raised. |
| Trainer qualification and trainer-of-trainers workflow | Deferred; the module records who trained, not whether they were qualified to. Noted as a known limitation. |
| Survey-based online examination | Would require the `survey` dependency; scores are entered by the trainer instead. |

## 8. Risks

| ID | Risk | Impact | Likelihood | Mitigation |
|----|------|--------|-----------|------------|
| R-01 | `ir.rule` group field name differs in Odoo 19 | Installation fails | Medium | Both variants shipped; one-line manifest swap; see `verification_notes.md` §2 |
| R-02 | `hr.employee` field layout changed in Odoo 19 | Matrix returns wrong population | Low–Medium | ORM-only resolution instead of raw SQL; documented in `verification_notes.md` §6 |
| R-03 | Matrix generation is slow on large populations | Poor usability | Medium | Hard limit of 20 000 lines with an actionable error message directing the user to narrow scope |
| R-04 | Compliance rate is computed, not stored, so it cannot be searched or grouped | Reporting limitation | High (accepted) | Documented limitation; the matrix wizard covers the reporting need |
| R-05 | Employees without a linked user cannot use the Learner self-service scope | Some staff see nothing | Medium | Documented in the administrator manual; `employee.user_id` must be populated |
| R-06 | Trainer can close a session and issue certifications without independent review | Weak segregation of duties | Medium | Documented as a known limitation; organisations requiring QA counter-approval should extend the workflow |
| R-07 | Absent attendees remain "pending" indefinitely, blocking closure | Operational friction | Medium | Intended behaviour; coordinator must mark absence explicitly by removing the attendee or the session cannot close. Documented in the user manual |
| R-08 | Test suite has never been executed | Unknown defects | High | Stated plainly in `test_report.md`; execution is a precondition of release |

## 9. Success criteria

| ID | Criterion | Verification method |
|----|-----------|--------------------|
| SC-01 | Module installs on a clean Odoo 19 Community database | Installation test — **not yet performed** |
| SC-02 | Module upgrades without data loss | Upgrade test — **not yet performed** |
| SC-03 | Every business requirement BR-01…BR-32 maps to at least one implemented behaviour and one test | Traceability table in `validation_report.md` |
| SC-04 | Closed sessions and issued certifications cannot be altered | `test_session_workflow.py`, `test_certification.py` |
| SC-05 | A Learner sees only their own records | `test_security.py` |
| SC-06 | Records of one company are invisible from another | `test_security.py` |
| SC-07 | No placeholder, dead code or vague wording in the source | Static check — PASS |
| SC-08 | Every module, class and function documented | Static check — PASS, 264/264 |
