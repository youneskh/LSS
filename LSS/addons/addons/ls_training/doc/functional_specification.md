# PHASE 3 — FUNCTIONAL SPECIFICATION

Module: `ls_training` — Life Sciences Training Management

---

## 1. Navigation

Root menu **Training** (visible to `group_ls_training_learner` and above).

```
Training
├── Operations
│   ├── Sessions                     ls.training.session
│   ├── Attendance                   ls.training.attendance
│   ├── Certifications               ls.training.certification
│   ├── Expiring and Expired         ls.training.certification (filtered)
│   └── Competency Assessments       ls.training.competency.assessment
├── Reporting                        [Viewer and above]
│   └── Training Matrix              ls.training.matrix.wizard
└── Configuration                    [Manager only]
    ├── Courses                      ls.training.course
    ├── Training Requirements        ls.training.requirement
    └── Competencies                 ls.training.competency
```

Additional entry points:

- **Employees → employee form → Training tab** — compliance figures,
  certification list, assessment list, print button (Learner and above).
- **Employees → employee form → smart button "Certifications"**.
- **Certification list → Print → Training Certificate** (report binding).

## 2. State machines

### 2.1 Course — `ls.training.course.state`

```
        action_submit_review        action_approve
draft ──────────────────────► review ──────────────► approved
  ▲                              │                      │
  │      action_reset_to_draft   │                      │ action_set_obsolete
  └──────────────────────────────┴──────────────────────┤
                                                        ▼
                                                    obsolete
```

| Transition | Method | Guard |
|-----------|--------|-------|
| draft → review | `action_submit_review` | state must be `draft` |
| review → approved | `action_approve` | state must be `review` |
| approved → obsolete | `action_set_obsolete` | state must be `approved` **and** no session in draft/confirmed/in_progress |
| any → draft | `action_reset_to_draft` | state must not already be `draft` |

Only `approved` courses appear in the session `course_id` domain.

### 2.2 Session — `ls.training.session.state`

```
         action_confirm      action_start       action_close
draft ─────────────────► confirmed ─────────► in_progress ─────────► done
  ▲                          │                     │                (terminal)
  │                          │                     │
  │  action_reset_to_draft   ▼   action_cancel     ▼
  └──────────────────── cancelled ◄────────────────┘
```

| Transition | Method | Guard |
|-----------|--------|-------|
| draft → confirmed | `action_confirm` | at least one attendance line |
| confirmed → in_progress | `action_start` | state must be `confirmed` |
| in_progress → done | `action_close` | no attendance with `result = pending` |
| any except done → cancelled | `action_cancel` | state must not be `done` |
| cancelled → draft | `action_reset_to_draft` | state must be `cancelled` |

`done` is terminal. On entry to `done` the system issues certifications
(§3.2) and freezes attendance.

### 2.3 Certification — `ls.training.certification.state`

Computed, not user-driven:

| Condition (evaluated in order) | Status |
|-------------------------------|--------|
| `revoked` is true | `revoked` |
| `date_expiry` is empty | `valid` |
| `date_expiry` < today | `expired` |
| `date_expiry` − today ≤ warning window | `expiring` |
| otherwise | `valid` |

Stored, and refreshed daily by a scheduled action so that the passage of
time is reflected without a user action.

### 2.4 Competency assessment — `ls.training.competency.assessment.state`

`draft → confirmed` via `action_confirm`. Confirmation requires non-empty
`evidence`. Confirmed records are read-only and undeletable.

## 3. Business rules

### 3.1 Attendance outcome derivation

`result` is computed, never typed:

| Attended | Course requires assessment | Score vs pass mark | Result |
|----------|---------------------------|--------------------|--------|
| No | any | any | `pending` |
| Yes | No | — | `passed` |
| Yes | Yes | score ≥ pass_score | `passed` |
| Yes | Yes | score < pass_score | `failed` |

**Absence yields `pending`, not `failed`**, because non-attendance is not a
failed assessment. Consequence: a session cannot be closed while an absent
attendee remains registered. The coordinator must remove the attendee or
mark them attended. This is deliberate and is documented in the user
manual.

### 3.2 Certification issuance on session closure

For each attendance with `result = passed`, one certification is created:

| Certification field | Source |
|--------------------|--------|
| `employee_id` | attendance employee |
| `course_id` | session course |
| `session_id` | the session |
| `company_id` | session company |
| `course_version` | course version **at that moment**, frozen |
| `date_granted` | session `date_end`, converted to a date |
| `score` | attendance score |
| `competency_ids` | course competencies, copied |
| `name` | sequence `ls.training.certification` |
| `date_expiry` | computed from `course.validity_months` |

Failing attendees receive nothing; their failure remains on the attendance
record.

### 3.3 Immutability rules

| Object | Frozen when | Blocked operations |
|--------|-------------|--------------------|
| Session header (course, dates, trainer) | state = `done` | write |
| Session | state not in (draft, cancelled) | unlink |
| Attendance (attended, score, employee) | session state = `done` | write |
| Attendance | session state = `done` | unlink |
| Certification | always | unlink (raises; revoke instead) |
| Competency assessment content | state = `confirmed` | write, unlink |

### 3.4 Validation constraints

**SQL constraints (8)**

| Model | Constraint | Rule |
|-------|-----------|------|
| competency | `code_company_uniq` | unique (code, company) |
| course | `code_company_uniq` | unique (code, company) |
| session | `name_company_uniq` | unique (name, company) |
| session | `capacity_positive` | capacity ≥ 0 |
| attendance | `session_employee_uniq` | unique (session, employee) |
| certification | `name_company_uniq` | unique (name, company) |
| assessment | `employee_competency_date_uniq` | unique (employee, competency, date) |
| requirement | `grace_days_positive` | grace_days ≥ 0 |

**Python constraints (18)**

| Model | Constraint | Rule |
|-------|-----------|------|
| competency | `_check_reassessment_months` | ≥ 0 |
| course | `_check_duration_hours` | > 0 |
| course | `_check_pass_score` | 0…100 |
| course | `_check_validity_months` | ≥ 0 |
| course | `_check_elearning_url` | external e-Learning requires a URL |
| session | `_check_dates` | end > start |
| session | `_check_capacity` | attendees ≤ capacity when capacity > 0 |
| session | `_check_trainer` | not both internal and external trainer |
| attendance | `_check_score` | 0…100 |
| attendance | `_check_employee_company` | attendee company = session company |
| certification | `_check_dates` | expiry ≥ grant |
| certification | `_check_score` | 0…100 |
| certification | `_check_revocation_reason` | revocation requires a reason |
| assessment | `_check_assessor_not_employee` | assessor ≠ subject |
| assessment | `_check_dates` | next assessment ≥ assessment |
| requirement | `_check_target_defined` | at least one of employee/job/department |
| requirement | `_check_unique_requirement` | no duplicate (course, job, dept, employee, company) |
| requirement | `_check_target_company` | targeted employee belongs to the company |

The requirement uniqueness rule is a Python constraint rather than a SQL
one because PostgreSQL treats NULLs as distinct, which would permit
duplicates whenever the optional target columns are empty.

### 3.5 Requirement resolution

A requirement targets:

| employee_id | job_id | department_id | Population |
|-------------|--------|---------------|-----------|
| set | ignored | ignored | that employee |
| empty | set | empty | all employees with that job, same company |
| empty | empty | set | all employees in that department, same company |
| empty | set | set | employees matching **both** (intersection) |
| empty | empty | empty | rejected by constraint |

## 4. Wizards

### 4.1 Register Employees — `ls.training.session.register.wizard`

| Field | Purpose |
|-------|---------|
| `selection_mode` | employees / department / job / requirement |
| `employee_ids`, `department_id`, `job_id` | criteria for the chosen mode |
| `exclude_certified` | skip employees already holding a valid or expiring certification for the course |

Behaviour: resolves candidates, subtracts already-registered employees,
optionally subtracts already-certified employees, checks free seats, then
creates the attendance lines and returns to the session form.

Errors raised: no criterion supplied; session closed or cancelled; nobody
left to register; insufficient free seats.

### 4.2 Training Matrix — `ls.training.matrix.wizard`

| Field | Purpose |
|-------|---------|
| `company_id` | scope company |
| `department_ids` | optional department filter (empty = all) |
| `job_ids` | optional job filter (empty = all) |
| `mandatory_only` | exclude advisory requirements |

Behaviour: resolves employees in scope, resolves the applicable
requirements per employee, finds the latest certification per
employee/course, produces one transient line per cell, then opens the
result in list and pivot views.

Guard: refuses above 20 000 lines with a message naming the count and the
limit.

## 5. Reports

| Report | Model | Content |
|--------|-------|---------|
| Training Certificate | `ls.training.certification` | Employee, course, code, frozen version, duration, session, trainer, grant and expiry dates, score against pass mark, status, competencies granted, revocation notice if applicable, two signature blocks |
| Training Record | `hr.employee` | Employee identity, compliance figures, full certification table, full assessment table |

Both are QWeb PDF using `web.external_layout`. The certificate is bound to
the certification model so it appears in the Print menu.

## 6. Scheduled actions

| Action | Frequency | Method | Effect |
|--------|-----------|--------|--------|
| Training: Refresh Certification Status | daily | `_cron_refresh_certification_state` | Recomputes stored status on all non-revoked certifications so expiry transitions are detected |
| Training: Send Expiry Reminders | daily | `_cron_send_expiry_reminders` | Queues one email per certification in `expiring` or `expired` status whose employee has a work email |

## 7. Notifications

One email template, `ls_training_certification_expiry_mail_template`,
addressed to the employee's work email, in the employee's language where
available, stating the course, the reference, whether the certification has
expired or is about to, and the date. `auto_delete` is enabled.

## 8. KPIs

| KPI | Where | Definition |
|-----|-------|-----------|
| Training compliance rate | employee form, Training tab | valid-or-expiring certifications ÷ distinct mandatory required courses × 100; 100% when no mandatory requirement applies |
| Mandatory courses | employee form | count of distinct courses from mandatory requirements |
| Compliant courses | employee form | count of those covered by a valid or expiring certification |
| Registered / Passed / Failed | session form and list | stored counters per session |
| Session count / Certification count | course form | smart buttons |
| Assessment count | competency form | smart button |
| Matrix gap count | matrix, "Gaps" filter | lines in not_trained, expired or revoked |

## 9. Search, filters and grouping

| Model | Filters | Group by |
|-------|---------|----------|
| Course | Approved, Draft, Under Review, With Expiring Certification, Archived | Status, Course Type, Delivery Mode |
| Session | Open, Closed, Upcoming, This Month | Course, Status, Trainer, Start Month |
| Attendance | Passed, Failed, Pending, My Attendance | Employee, Course, Result, Session Month |
| Certification | Valid, Expiring Soon, Expired, Revoked, Action Required, My Certifications, Granted (date) | Employee, Course, Status, Expiry Month |
| Assessment | Acquired, Not Acquired, Draft, Confirmed, Reassessment Due, My Assessments | Employee, Competency, Level |
| Requirement | Mandatory, Role Based, Individual, Archived | Course, Job Position, Department |
| Competency | Periodic Reassessment, Archived | Minimum Level |
| Matrix line | Gaps, Expiring Soon, Valid | Employee, Course, Department, Job Position, Status |

## 10. Views by model

| Model | Views |
|-------|-------|
| `ls.training.course` | list, form (statusbar, 2 smart buttons, obsolete ribbon, 3 pages), search |
| `ls.training.session` | list, form (statusbar, 6 header buttons, editable attendance page), calendar, search |
| `ls.training.attendance` | list, form, search |
| `ls.training.certification` | list, form, revocation dialog form, search |
| `ls.training.competency` | list, form (smart button, archived ribbon), search |
| `ls.training.competency.assessment` | list, form (statusbar), search |
| `ls.training.requirement` | list (editable), form (smart button), search |
| `ls.training.matrix.line` | list (colour-coded), pivot, search |
| `ls.training.matrix.wizard` | form (dialog) |
| `ls.training.session.register.wizard` | form (dialog) |
| `hr.employee` | inherited form: smart button + Training page |

## 11. Access rights summary

| Model | Learner | Viewer | Trainer | Manager |
|-------|---------|--------|---------|---------|
| Course | R | R | R | RWCD |
| Competency | R | R | R | RWCD |
| Requirement | R | R | R | RWCD |
| Session | R | R | RWC | RWCD |
| Attendance | R | R | RWCD | RWCD |
| Certification | R | R | RWC | RWC |
| Assessment | R | R | RWC | RWCD |
| Register wizard | — | — | RWCD | RWCD |
| Matrix wizard and lines | — | RWCD | RWCD | RWCD |

R = read, W = write, C = create, D = delete. Certifications are never
deletable at model level, including for Managers.

Record rules restrict Learners to records whose
`employee_id.user_id` is the current user; Viewers and above see all
records within their allowed companies. Seven global multi-company rules
apply to every user.
