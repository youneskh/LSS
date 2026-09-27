# USER MANUAL

Module: `ls_training` — Training Management

---

## 1. Who does what

| Your role | What you can do |
|-----------|-----------------|
| Learner | See your own certifications, attendance and assessments |
| Viewer | See everyone's training records; run the training matrix |
| Trainer | Everything above, plus schedule sessions, register attendees, record outcomes, close sessions, record assessments |
| Manager | Everything above, plus manage courses, requirements and competencies, and revoke certifications |

## 2. Checking your own training (Learner)

Open **Employees**, find yourself, and go to the **Training** tab. You will
see:

- **Mandatory Courses** — how many courses your role requires
- **Compliant Courses** — how many you currently hold valid
- **Training Compliance** — the percentage
- Your certifications, colour-coded: red = expired, orange = expiring soon
- Your competency assessments

Click **Print Training Record** for a one-page PDF of your complete
history.

You can also open **Training → Operations → Certifications** and use the
**My Certifications** filter.

If you see nothing at all, your employee record is probably not linked to
your user account. Ask your administrator to set the **Related User**
field.

## 3. Running a training session (Trainer)

### Step 1 — Create the session

**Training → Operations → Sessions → New**

| Field | Note |
|-------|------|
| Course | Only approved courses appear |
| Start / End | End must be after start. Selecting a course proposes an end time from its duration |
| Internal Trainer *or* External Trainer | Fill exactly one, not both |
| Location | |
| Maximum Attendees | Leave 0 for no limit |

### Step 2 — Register attendees

Either add rows directly in the **Attendees** tab, or click
**Register Employees** for the bulk wizard:

| Select By | Result |
|-----------|--------|
| Selected Employees | The people you pick |
| All Employees of a Department | Everyone in that department |
| All Employees of a Job Position | Everyone with that job |
| All Employees Required to Take the Course | Everyone a training requirement targets for this course |

**Skip Already Certified** (on by default) leaves out anyone who already
holds a valid or expiring certification, so you do not retrain people
unnecessarily.

Running the wizard twice is safe — people already registered are skipped.

### Step 3 — Confirm and start

**Confirm** requires at least one attendee. Then **Start** when delivery
begins.

### Step 4 — Record outcomes

In the **Attendees** tab, tick **Attended** for each person present. If the
course requires an assessment, enter the **Score**.

The **Result** column fills in by itself:

| Situation | Result |
|-----------|--------|
| Not ticked as attended | Pending |
| Attended, course has no assessment | Passed |
| Attended, score ≥ pass mark | Passed |
| Attended, score < pass mark | Failed |

You cannot type the result directly. It is derived from what you recorded,
so anyone reviewing the record later can see exactly why someone passed.

### Step 5 — Close

Click **Close and Issue Certifications**. The system:

1. Refuses if anyone is still **Pending**
2. Issues a certification to every attendee who **Passed**
3. Freezes the attendance evidence permanently

**About absentees.** Someone who did not attend stays Pending, and Pending
blocks closure. This is deliberate — absence is not a failed assessment.
Remove the absent person from the attendee list, then close. They can be
registered on a later session.

**Closure is final.** After closing you cannot change the course, dates,
trainer, attendance or scores. Check before you click.

## 4. Recording external training (Trainer)

For training delivered outside the system:

**Training → Operations → Certifications → New**

| Field | Note |
|-------|------|
| Employee, Course | Required |
| Course Version | Defaults from the course; set it to the version actually delivered |
| Granted On | The real completion date |
| Expires On | Calculated from the course validity — override it if the provider set a different date |
| Score | If applicable |

Leave **Source Session** empty; that is what marks it as external.

## 5. Certifications

### Status meanings

| Status | Meaning |
|--------|---------|
| Valid | In force |
| Expiring Soon | Inside the warning window (30 days by default) |
| Expired | Past its expiry date |
| Revoked | Withdrawn deliberately |

Statuses update automatically overnight.

### Finding what needs attention

**Training → Operations → Expiring and Expired** lists everything requiring
action. Group by Course to plan a refresher session, or by Employee to see
who is affected.

### Printing a certificate

Select one or more certifications, then **Print → Training Certificate**.

### Renewal

Do not edit an old certification. Run a new session, or record a new
certification manually. The old record stays in the history and lapses on
its own date. This is how the full history remains reconstructable.

### Revocation (Manager)

Open the certification, click **Revoke**, and enter a reason. The reason is
mandatory and appears on the printed certificate.

Revocation is permanent and cannot be undone. Certifications can never be
deleted — revocation is the only way to withdraw one.

## 6. Competency assessments

Attendance shows someone sat through the training. An assessment shows they
can actually do the job.

**Training → Operations → Competency Assessments → New**

| Field | Note |
|-------|------|
| Employee | The person assessed |
| Competency | What is being assessed |
| Assessor | Who observed. Cannot be the same person as the employee |
| Assessment Date | |
| Demonstrated Level | Not Demonstrated / Developing / Proficient / Expert |
| Assessment Evidence | What you observed. Required to confirm |

**Competency Acquired** ticks automatically when the level reaches the
minimum defined on the competency.

Click **Confirm** to finalise. Confirmed assessments become read-only and
cannot be deleted.

## 7. The training matrix

**Training → Reporting → Training Matrix**

Choose a scope — leave departments and job positions empty for the whole
company — and click **Generate Matrix**.

One line per employee/course combination:

| Status | Colour | Meaning |
|--------|--------|---------|
| Valid | green | Certified and in force |
| Expiring Soon | orange | Action needed shortly |
| Expired | red | Qualification lapsed |
| Not Trained | red | Never certified |
| Revoked | red | Withdrawn |

Use the **Gaps** filter to see only problems. Switch to the pivot view for
an employee-by-course grid.

If the scope is too large the system refuses and tells you the count — narrow
by department or job position and try again.

## 8. Common questions

**Why can I not select my course on a session?**
It is not approved. Only approved courses can be scheduled.

**Why can I not close the session?**
Someone is still Pending. Tick their attendance or remove them.

**Why did an attendee get no certificate?**
They failed, or they were never marked as attended.

**Why can I not correct a score?**
The session is closed. Closed evidence is permanent. Raise it through your
deviation process.

**Why can I not delete a certification?**
Certifications are quality evidence. Revoke it instead.

**Why is someone's compliance 100% when they have had no training?**
No mandatory requirement targets them. Check the requirements
configuration.

**I did not get an expiry reminder.**
Check that your employee record has a Work Email, that both scheduled
actions are active, and that an outgoing mail server is configured.
