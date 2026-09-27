# CONFIGURATION GUIDE

Module: `ls_training`

---

## 1. Order of configuration

Configure in this order; each step depends on the one before.

1. Assign user groups
2. Confirm HR master data (departments, job positions, employee/user links)
3. Set the expiry warning window
4. Create competencies
5. Create and approve courses
6. Define training requirements
7. Verify the scheduled actions

## 2. Assign user groups

**Settings → Users & Companies → Users**, open a user, section
**Life Sciences Training**.

| Assign | To |
|--------|-----|
| Learner | Every employee who should see their own training record |
| Viewer | Department managers, QA reviewers, auditors |
| Trainer | Training coordinators, trainers |
| Manager | Quality managers, training system owners |

Groups are cumulative: assigning Trainer automatically grants Viewer and
Learner.

**Critical prerequisite.** The Learner self-service scope works by matching
`employee.user_id` to the logged-in user. An employee record with no linked
user means that person sees nothing. Verify on each employee form that the
**Related User** field is populated.

## 3. HR master data

The training matrix resolves populations from job positions and
departments, so these must be accurate before requirements are useful.

| Object | Where | Note |
|--------|-------|------|
| Departments | Employees → Configuration → Departments | Used for department-based requirements |
| Job Positions | Employees → Configuration → Job Positions | Used for role-based requirements |
| Employees | Employees → Employees | Must have Company, Department, Job Position, Work Email and Related User |

Work Email is required for expiry reminders. Employees without one are
silently skipped by the reminder job.

## 4. Expiry warning window

**Settings → Technical → System Parameters**

| Key | Default | Effect |
|-----|---------|--------|
| `ls_training.expiry_warning_days` | `30` | Number of days before expiry at which a certification becomes "Expiring Soon" and reminders begin |

Set to `60` for a longer planning horizon, or `0` to disable advance
warning entirely (certifications then move straight from Valid to Expired).

A missing, non-numeric or negative value falls back to 30, so a mistyped
parameter cannot silently disable warnings.

The change takes effect on the next daily refresh, or immediately for
newly written records.

## 5. Competencies

**Training → Configuration → Competencies**

| Field | Guidance |
|-------|----------|
| Competency / Code | Code must be unique per company. Keep codes short and stable — they appear on printed records |
| Minimum Acceptable Level | Level at or above which the competency counts as held. Default: Proficient |
| Reassessment Interval (Months) | 0 = no periodic reassessment. Otherwise drives the proposed next-assessment date |
| Description | What the person must be able to do |

## 6. Courses

**Training → Configuration → Courses**

| Field | Guidance |
|-------|----------|
| Course Title | |
| Course Code | Leave blank to generate `TRN/CRS/00001`, or enter your own controlled code |
| Version | Increment when the training material changes. The value in force at issuance is frozen onto each certification |
| Course Type | Induction, GMP/GxP, Procedure/SOP, Technical, Health and Safety, Quality System, Regulatory |
| Delivery Mode | Classroom, On-the-Job, Self-Study, External e-Learning |
| e-Learning URL | Required when the mode is External e-Learning |
| Duration (Hours) | Must be greater than zero. Also used to propose a session end time |
| Certification Validity (Months) | 0 = never expires. 12 = annual requalification |
| Requires Assessment | When enabled, a score is captured and compared to the pass mark |
| Pass Score (%) | 0–100 |
| Granted Competencies | Copied onto each certification issued |

### Approving a course

A course must reach **Approved** before it can be scheduled.

Draft → **Submit for Review** → Under Review → **Approve** → Approved

Both buttons require the Manager group. Note that one Manager can perform
both steps; the module does not enforce two distinct approvers. If your
procedure requires segregated approval, enforce it procedurally or
integrate `ls_electronic_signature`.

### Retiring a course

**Make Obsolete** is blocked while any session is in Draft, Confirmed or
In Progress. Close or cancel those sessions first.

## 7. Training requirements

**Training → Configuration → Training Requirements**

Each requirement states that a population must hold a course.

| Target combination | Population |
|--------------------|-----------|
| Specific Employee set | That employee only |
| Job Position only | Everyone with that job, same company |
| Department only | Everyone in that department, same company |
| Job Position **and** Department | Only employees matching both |

At least one target is mandatory.

| Field | Guidance |
|-------|----------|
| Mandatory | Mandatory requirements count towards the compliance rate. Advisory ones are reported but excluded |
| Grace Period (Days) | Days a newly targeted employee has before being considered overdue |
| Justification | Record why this population needs this training. Useful during audit |

The **Targeted Employees** smart button shows exactly who a requirement
currently resolves to. Use it to verify a rule before relying on it.

Duplicate requirements (same course, job, department, employee and
company) are rejected.

## 8. Scheduled actions

**Settings → Technical → Scheduled Actions**

| Action | Default | Purpose |
|--------|---------|---------|
| Training: Refresh Certification Status | Daily | Detects expiry transitions |
| Training: Send Expiry Reminders | Daily | Emails affected employees |

Both must remain active. If the refresh job is disabled, certification
statuses freeze at their last computed value and expired qualifications
will continue to display as valid — a genuine data-integrity concern.

Schedule the refresh job to run **before** the reminder job.

## 9. Outgoing email

Reminders require a working outgoing mail server:
**Settings → Technical → Outgoing Mail Servers**. Without one, messages
queue indefinitely and no one is notified.

## 10. Multi-company

Every model carries a company, and seven global record rules restrict
visibility to the user's allowed companies.

| Object | Scope |
|--------|-------|
| Courses, competencies, requirements | Per company |
| Sessions, attendance, certifications, assessments | Per company |
| Sequences | Shared across companies by default |

An attendee must belong to the same company as the session; this is
enforced by constraint. Courses are not shared between companies — each
company maintains its own approved course catalogue.

## 11. Configuration checklist

| # | Item | Done |
|---|------|------|
| 1 | Training groups assigned to all relevant users | ☐ |
| 2 | Every employee has a Related User | ☐ |
| 3 | Every employee has a Work Email | ☐ |
| 4 | Departments and job positions accurate | ☐ |
| 5 | Expiry warning window set to your policy | ☐ |
| 6 | Competencies created | ☐ |
| 7 | Courses created and approved | ☐ |
| 8 | Requirements defined and verified via Targeted Employees | ☐ |
| 9 | Both scheduled actions active | ☐ |
| 10 | Outgoing mail server configured and tested | ☐ |
