# 09 — Administrator Manual

## 1. Daily operation

| Task | Where |
|---|---|
| Confirm the three scheduled actions ran | Settings, Technical, Scheduled Actions, column Next Execution Date |
| Watch documents overdue for review | Quality Management, Reporting, Procedures Due for Review |
| Watch records past their retention | Quality Management, Reporting, Records Past Retention |

## 2. Scheduled actions

Each action is implemented as a model method and can be run manually from the
scheduled action form. The three methods return the number of activities
created, which is written to the Odoo log.

| Action | Method | Model bearing the method |
|---|---|---|
| Document Review Reminder | `_cron_document_review_reminder` | `ls.qms.document.mixin` |
| Objective Monitoring | `_cron_objective_monitoring` | `ls.qms.objective` |
| Record Retention Review | `_cron_retention_review` | `ls.qms.quality_record` |

If an action is disabled, no data is lost: the review dates and retention
dates remain correct, only the prompting stops.

## 3. Multi company

Every stored model carries `company_id` and a record rule isolating the
records of the companies active for the user. Sequences are shared unless a
company specific sequence with the same code is created.

A work instruction must belong to a procedure of the same company; this is
enforced by a Python constraint and by `check_company` on the relational
field.

## 4. Backup and retention

The module stores quality evidence. Align the database backup policy with the
longest retention period configured, which is 60 months by default. Attached
files are stored by Odoo either in the filestore or in the database depending
on the deployment; both must be included in the backup.

## 5. What is written to the chatter

| Event | Trace |
|---|---|
| Submission, approval, publication, withdrawal | Tracked state change |
| Rejection | Message containing the reason |
| New revision | Message on the previous revision naming the new one |
| Correction of a confirmed record by a manager | Tracked field change |

This tracking is the standard `mail.thread` mechanism. It is **not** a
protected audit trail in the sense of 21 CFR 11.10(e). See
`02_regulatory_analysis.md`, section 3.

## 6. Troubleshooting

| Symptom | Cause to check |
|---|---|
| A user sees no document | The user holds Viewer only and no document is published |
| Approve raises an error naming segregation of duties | The acting user is the author; either another approver acts, or the parameter is changed under change control |
| Publish raises an error on a work instruction | The parent procedure is not published |
| The reference reads `/` | The sequence for the model has been deleted; recreate it with the code listed in `07_configuration_guide.md` |
| No review reminder is raised | The review period is zero, the document is not published, or the scheduled action is inactive |
