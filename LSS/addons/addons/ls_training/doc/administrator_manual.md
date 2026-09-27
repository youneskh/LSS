# ADMINISTRATOR MANUAL

Module: `ls_training`

---

## 1. Responsibilities

| Area | Task |
|------|------|
| Access | Assign training groups; keep employee/user links current |
| Scheduling | Keep both cron jobs active and correctly ordered |
| Email | Maintain the outgoing mail server; monitor the queue |
| Parameters | Own `ls_training.expiry_warning_days` |
| Data integrity | Monitor for stale certification statuses |
| Backup | Ensure training evidence is included in backup scope |

## 2. Group administration

Four groups, cumulative:

```
Learner  ←  Viewer  ←  Trainer  ←  Manager
```

Assigning Manager implicitly grants the other three. Never assign only
Viewer to someone who must record outcomes — Viewer cannot write.

### The employee/user link

The Learner scope is enforced by a record rule matching
`employee_id.user_id` against the current user. Consequences:

| Situation | Effect |
|-----------|--------|
| Employee has no Related User | That person sees no training records at all |
| One user linked to two employees | The user sees both employees' records |
| Employee's Related User changed | Visibility follows immediately; historical records are unaffected |

Audit this periodically:

**Employees → filter where Related User is not set.**

## 3. Scheduled actions

**Settings → Technical → Scheduled Actions**

| Action | Method | Frequency | Order |
|--------|--------|-----------|-------|
| Training: Refresh Certification Status | `_cron_refresh_certification_state` | Daily | Run first |
| Training: Send Expiry Reminders | `_cron_send_expiry_reminders` | Daily | Run second |

### Why the refresh job matters

Certification status is a **stored** computed field. It depends on today's
date, which no field change triggers. Without the daily refresh, statuses
freeze at their last computed value and **expired qualifications continue
to display as Valid**.

This is a data-integrity concern, not a cosmetic one. If the job has been
disabled, re-enable it and force a refresh:

```python
# Settings → Technical → Scheduled Actions, or an Odoo shell
env["ls.training.certification"]._cron_refresh_certification_state()
```

The method returns the number of records refreshed.

### Reminder job behaviour

Sends one email per certification in `expiring` or `expired` status whose
employee has a work email. Notes:

- It does **not** deduplicate across certifications. An employee with three
  expiring certifications receives three emails.
- It re-sends daily while the status persists. Employees who ignore
  reminders receive them every day until the certification is renewed or
  revoked.
- Employees with no work email are silently skipped.
- Managers are not notified. There is no escalation path in this version.

If daily repetition is unacceptable, reduce the job frequency or extend the
module with a "last reminded" field.

## 4. System parameters

| Key | Default | Notes |
|-----|---------|-------|
| `ls_training.expiry_warning_days` | `30` | Integer. Missing, non-numeric or negative values fall back to 30 |

Changing this affects the boundary between Valid and Expiring Soon.
Existing records adopt the new window at the next refresh.

## 5. Sequences

**Settings → Technical → Sequences**

| Code | Prefix | Padding |
|------|--------|---------|
| `ls.training.course` | `TRN/CRS/` | 5 |
| `ls.training.session` | `TRN/SES/%(year)s/` | 5 |
| `ls.training.certification` | `TRN/CER/%(year)s/` | 5 |

Created without a company, so one sequence serves all companies. The code
calls `next_by_code` with company context, so adding company-specific
sequences later requires no code change.

Changing a prefix affects only new records. Do not change padding
mid-year — it produces inconsistent references within a series.

## 6. Record rules

13 rules. Verify after installation and after any upgrade:

**Settings → Technical → Record Rules**, filter on model `ls.training`.

| Rule type | Count | Groups |
|-----------|-------|--------|
| Multi-company (global) | 7 | none — applies to everyone |
| Learner self-scope | 3 | Learner |
| Viewer full-scope | 3 | Viewer |

Global rules intersect (always restrict). Group rules unify (a Viewer's
broad rule overrides the Learner's narrow one). Because Viewer implies
Learner, Viewers, Trainers and Managers see everything in their allowed
companies while a plain Learner sees only their own.

**Do not delete the Viewer rules.** Removing them would leave Viewers
subject to the Learner restriction alone, and they would see only their
own records.

## 7. Multi-company operation

| Object | Behaviour |
|--------|-----------|
| Courses | Not shared. Each company maintains its own approved catalogue |
| Requirements | Per company |
| Sessions | Attendees must belong to the session's company (enforced by constraint) |
| Certifications | Per company |
| Sequences | Shared |

Users see records of their allowed companies only.

## 8. Email configuration

Reminders need **Settings → Technical → Outgoing Mail Servers** configured
and tested. Without it, messages queue in **Settings → Technical → Emails**
and nobody is notified — silently, from the user's point of view.

Monitor the queue for stuck messages.

## 9. Backup and retention

The module blocks deletion of certifications, confirmed assessments and
closed-session attendance at application level. It does **not** implement
retention scheduling or archival.

Database backups are your retention mechanism. Confirm that:

- backups run at a frequency matching your record-retention policy;
- restores have been tested;
- the retention period of backups meets the requirement applicable to your
  jurisdiction and product type.

Uninstalling the module deletes all training data irreversibly.

## 10. Monitoring checklist

| Frequency | Check |
|-----------|-------|
| Daily | Both cron jobs ran without error (Settings → Technical → Scheduled Actions, check Next Execution) |
| Daily | Email queue is draining |
| Weekly | Certifications with status Expired that nobody has acted on |
| Monthly | Employees without a Related User |
| Monthly | Employees without a Work Email |
| Monthly | Courses stuck in Draft or Under Review |
| Quarterly | Training group assignments still match role |
| After every upgrade | All 13 record rules present; both cron jobs active; menus visible |

## 11. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Expired certifications still show Valid | Refresh cron disabled or failing | Re-enable; run the method manually |
| No reminders sent | Mail server unconfigured, or employees lack work email | Check both |
| A user sees no training data | No Related User on their employee record, or no training group | Set both |
| A Viewer sees only their own records | Viewer record rules deleted | Reinstall or recreate them |
| Matrix refuses to generate | Scope exceeds 20 000 lines, or no requirement applies | Narrow the scope; check requirements exist |
| Course cannot be selected on a session | Course not Approved | Approve it |
| Session will not close | An attendee is Pending | Mark attendance or remove the attendee |
| Certification cannot be deleted | By design | Revoke instead |
