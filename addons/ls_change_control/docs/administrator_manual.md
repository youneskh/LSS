# Administrator Manual

Module: `ls_change_control`

## 1. Security model

### 1.1 Groups

Four groups in the `Change Control` category, cumulative:

```
base.group_user -> Viewer -> Requester -> Approver -> Change Control Manager
```

A user holds exactly one value of the selection; the implied groups give the
lower rights automatically.

### 1.2 Access rights

`security/ir.model.access.csv`, 23 lines. Every model of the module is covered.

| Model | Viewer | Requester | Approver | Manager |
|-------|--------|-----------|----------|---------|
| request | r | r w c | r w c | r w c u |
| assessment | r | r w | r w | r w c u |
| approval | r | r | r w | r w c u |
| implementation | r | r w | r w | r w c u |
| verification | r | r w | r w | r w c u |
| category, impact area, approval template | r | r | r | r w c u |
| decision wizard | - | - | r w c | r w c u |

r read, w write, c create, u unlink.

### 1.3 Record rules

| Rule | Type | Effect |
|------|------|--------|
| Five multi-company rules | Global | A user only sees the records of their allowed companies |
| Change request: own requests only | Requester group, write and create | A requester only modifies the requests they raised or manage |
| Change request: manager full write | Manager group, write, create, delete | Unrestricted within the allowed companies |

Record rules of different groups combine with a logical OR. Because a manager
is also a member of the requester group by implication, the permissive manager
rule neutralises the ownership restriction for managers. This is the intended
and standard Odoo behaviour.

### 1.4 Protections that no group can bypass

These are enforced in the model code and apply to every user, including a
change control manager and the Odoo administrator.

| Protection | Scope |
|------------|-------|
| Content fields frozen after Draft | Title, category, change type, temporary end date, current situation, proposed change, justification |
| Workflow fields not writable from a session | State, reference, decision dates, decision reasons, closure statement |
| Completed assessment immutable | Business fields and deletion |
| Decided approval immutable | Every field and deletion |
| Closed action immutable | Every field and deletion |
| Completed verification immutable | Every field and deletion |
| Submitted request undeletable | Any state other than Draft |

A user with database level access can of course alter the data directly. That
risk is addressed by the database access controls of the organisation, not by
the application.

## 2. Scheduled actions

Settings, Technical, Scheduled Actions.

| Action | Method | Frequency |
|--------|--------|-----------|
| Change Control: remind pending approvals | `_cron_remind_pending_approvals` | Daily |
| Change Control: remind overdue implementations | `_cron_remind_overdue_implementations` | Daily |
| Change Control: remind due effectiveness verifications | `_cron_remind_due_verifications` | Daily |

All three run as the root user, so that they see every company. Each avoids
creating a duplicate activity for the same user and the same summary, so
running them more than once a day is harmless.

Approval reminders are governed per company by the Approval Reminder Delay
parameter; setting it to 0 disables them for that company.

To troubleshoot, run a method manually from Settings, Technical, Scheduled
Actions, Run Manually, and consult the server log.

## 3. Mail

Three templates are delivered. Notifications are queued with
`force_send=False`, so they leave with the standard Odoo mail queue.

If notifications are not delivered:

1. Check that an outgoing mail server is configured and reachable.
2. Check Settings, Technical, Email, Emails for messages in the Failed state.
3. Check that the approvers and requesters have an email address.

The absence of a mail template does not block the workflow: the module logs a
warning and continues. This is deliberate, so that a deleted template cannot
stop a regulated process.

## 4. Multi-company operation

Every transactional model carries a `company_id`, and five global record rules
isolate the companies.

The four configuration parameters are held on `res.company` and must be set
for each company. Categories, impact areas and approval templates are shared
across companies; if a site requires its own categories, create them with
distinct codes and train the users to select the right one.

The sequence is global by default. To obtain a distinct series per site,
create an additional sequence with the code `ls.change_control.request` and a
company; the module resolves the sequence of the company of the request first.

## 5. Backup and retention

Change control records are quality records subject to a retention period
defined by the organisation.

* Back up the database and the filestore together; chatter attachments live in the filestore.
* Never delete a change request from the database to free space. Deletion of submitted requests is refused by the application, and a direct database deletion destroys a quality record.
* Before uninstalling the module, export the records and confirm the retention obligation with the quality unit. Uninstalling drops the tables.

## 6. Monitoring

| What to monitor | How |
|-----------------|-----|
| The three scheduled actions are running | `Next Execution Date` moves forward daily |
| Late changes | Change requests, filter Implementation Late |
| Due verifications | Change requests, filter Verification Due |
| Approvals blocking the process | Approvals, filter Awaiting Decision, group by Approver |
| Failed notifications | Settings, Technical, Email, Emails, state Failed |

## 7. Upgrading the module

An upgrade of a validated system is itself a change and must be managed under
the change control procedure of the organisation.

1. Back up the database and the filestore.
2. Upgrade a copy first: `odoo-bin -d <copy> -u ls_change_control --stop-after-init`.
3. Run the automated test suite on the copy.
4. Run the operational qualification tests of the organisation.
5. Verify that the configuration was preserved: all data files are `noupdate`, so categories, areas, templates, mail templates and scheduled actions modified on the site are not overwritten.
6. Record the outcome, then upgrade production.

## 8. Common administrative situations

| Situation | Action |
|-----------|--------|
| An approver has left the organisation | The approval is immutable only once decided. While it is Pending, a change control manager may reassign `user_id` on the approval |
| An approver is absent and blocks a change | Reassign the pending approval, or clear its Mandatory flag if the procedure allows it. Both actions are traced in the chatter |
| An assessor cannot edit their assessment | They must hold at least the Requester group |
| A category must be withdrawn | Archive it. Never delete it: existing records reference it |
| A wrong approval matrix was applied to a live request | The generated approvals of a request are records of the request. A pending approval may be deleted by a manager; a decided one may not |
| A request was raised in the wrong company | It cannot be moved after submission. Cancel it with a justification and raise a new one |
