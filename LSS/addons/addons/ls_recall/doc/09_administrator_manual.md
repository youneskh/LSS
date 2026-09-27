# Administrator Manual

Module: `ls_recall`

---

## 1. Scope

For the Odoo administrator and the system owner: what the module holds,
what it enforces, what it does not enforce, and what an inspector will
ask for.

## 2. Data held

| Table | Contents | Retention consequence |
|-------|----------|----------------------|
| `ls_recall_plan` | Approved arrangements, all versions | Superseded versions stay as evidence of what was approved when |
| `ls_recall_execution` | The field actions | Closed records are immutable at application level |
| `ls_recall_line` | Consignee, lot, quantities | Contains customer identities |
| `ls_recall_communication` | Issued notices, full text | Sent records are immutable at application level |
| `ls_recall_effectiveness` | Contact attempts and outcomes | |
| `ls_recall_report` | Status and final reports, frozen figures | |
| `mail_message` | Chatter: transitions, quantity changes, tracked field changes | The de facto change history |

Deleting a plan, a recall, a communication or a report through the ORM is
blocked once it has left draft. It is **not** blocked at database level:
a direct SQL `DELETE` will succeed. If your retention policy must be
enforceable against a database administrator, it has to be enforced by
database permissions and backup integrity, not by this module.

## 3. What is immutable, and how

"Immutable" here means the application refuses the write, in `write()`,
so the refusal applies to RPC and to the user interface alike.

| Record | From | What stays writable |
|--------|------|--------------------|
| Plan | approved | state, active, approval stamps, mail fields |
| Field action | closed or cancelled | active, mail fields |
| Field action decision fields | initiated | nothing (action type, classification, depth, product, company, plan) |
| Consignee line | parent closed or cancelled | nothing |
| Communication | sent | acknowledgement fields, mail fields |
| Effectiveness check | parent closed or cancelled | nothing |
| Report | approved | submission fields, mail fields |

## 4. Roles and segregation of duties

Two controls depend on there being more than one person:

* a report cannot be approved by the person who reviewed it;
* only a Manager may close a field action whose checks failed.

Assign at least two Managers. A single-Manager configuration makes the
first control a deadlock during absence and the second unreviewable.

Do not put the same user in Coordinator and Manager: Manager already
implies Coordinator, and the duplicate makes the user list misleading
when someone audits role assignment.

## 5. Multi-company

Six global record rules restrict every persistent model to the user's
allowed companies. They are global rather than group-scoped, so they
intersect with any other rule and cannot be escaped by adding the user
to a further group.

A field action belongs to one company. Tracing only reads movements of
that company. A recall spanning legal entities needs one record per
entity, cross-referenced in the reason text.

## 6. The one privilege escalation

`stock.lot._compute_ls_recall_state` reads recall records through
`sudo`, limited to `action_type` and `state`, so that a warehouse
operator with no recall role still sees the "Under Recall" ribbon.

If the existence of a recall is confidential from warehouse staff in
your organisation, override the compute or restrict the field, and
record the change under change control. The rationale for the default is
in `05_architecture_review.md` §4.1.

## 7. Scheduled actions

Both raise activities only; neither changes a state. Monitor them like
any other cron. If they stop, you lose reminders, not data.

## 8. Backup and archival

The module holds regulatory records. Standard obligations follow:

* verify restores, do not merely take backups;
* retain for the period your framework requires for the product type;
* record any deletion or archival as a controlled event;
* remember that uninstalling the module removes all of the above.

## 9. Change control on the system itself

Changes an administrator can make that alter regulated behaviour:

| Change | Effect |
|--------|--------|
| Sequence prefix or number | Breaks reference continuity |
| Disabling a scheduled action | Reminders stop |
| Role assignment | Alters who can approve and close |
| Overriding the lot compute | Alters who is warned |
| Editing a plan's target reconciliation rate | Alters a closure gate |
| Module upgrade | Alters behaviour; requalify |

Each belongs in your change control system.

## 10. What an inspector is likely to ask for, and where it is

| Question | Where |
|----------|-------|
| Show me your recall procedure and its approval | Recall plan, Approval tab, with version history |
| Who can start a recall out of hours? | Plan: coordinator and deputy |
| When did you last rehearse? | Plan: last and next mock recall dates |
| Show me a recall from decision to closure | The field action; chatter holds the sequence |
| How did you know who received it? | Consignees tab, source transfers column |
| What did you send, and when? | Communications tab, sent date and user |
| How do you know they acted? | Effectiveness checks, outcomes, escalations |
| How much did you get back? | Reconciliation footer |
| When did you tell the authority? | Recall header: notified flag and date |
| Why did you close it? | Closure justification, plus the gate results in the chatter |
| Who closed it? | Closed-by user and closure date |

## 11. Known gaps to disclose during qualification

1. No field-level audit trail beyond tracked fields; chatter only.
2. No electronic signature.
3. Application-level immutability, not database-level.
4. Tracing depends on lot movements being recorded in Odoo.
5. The test suite has never been executed in the environment where the
   module was produced — see `12_test_plan_and_report.md`.
