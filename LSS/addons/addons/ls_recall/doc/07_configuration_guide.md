# Configuration Guide

Module: `ls_recall`

---

## 1. Order of configuration

1. Assign roles to users.
2. Review the two scheduled actions.
3. Create and approve at least one recall plan.
4. Confirm that products subject to recall are lot-tracked.

## 2. Roles

**Settings → Users & Companies → Users**, "Recall Management" privilege.

| Role | Give it to |
|------|-----------|
| Viewer | Auditors, management, anyone who must read but not act |
| Coordinator | The people who actually run a recall |
| Manager | The quality unit: plan approval, report approval, closure |

The roles are cumulative. Do not assign a user both Coordinator and
Manager; Manager already implies Coordinator.

**Segregation of duties.** Two rules in the module depend on there being
more than one person: a report cannot be approved by the person who
reviewed it, and only a Manager may override a failed closure check.
Assign at least two Managers so that neither rule becomes a deadlock
when one person is absent.

## 3. Scheduled actions

**Settings → Technical → Automation → Scheduled Actions**

| Action | Default | Notes |
|--------|---------|-------|
| Recall: monitor open field actions | Daily | Raises an activity on an overdue or silent real action |
| Recall: monitor mock recall due dates | Weekly | Raises an activity on a plan whose rehearsal is due |

Neither changes a workflow state. If your validation approach requires
scheduled actions to be disabled, disabling them costs only the
reminders.

## 4. Sequences

**Settings → Technical → Sequences & Identifiers → Sequences**

| Code | Default prefix |
|------|----------------|
| `ls.recall.plan` | `RCP/%(year)s/` |
| `ls.recall.execution` | `RCL/%(year)s/` |
| `ls.recall.communication` | `RCC/%(year)s/` |
| `ls.recall.report` | `RCR/%(year)s/` |

All four use the `no_gap` implementation, so references are contiguous.
This is intentional: a gap in a regulated reference series invites the
question of what occupied the missing number.

Change prefixes before the first record is created. Changing them later
produces a discontinuity that must itself be explained.

## 5. Recall plan

**Recalls → Configuration → Recall Plans**

| Field | Guidance |
|-------|----------|
| Title | Name the population it covers, e.g. "sterile injectables" |
| Recall Coordinator | The person accountable for execution |
| Deputy | Mandatory for approval. This is the out-of-hours answer. |
| Decision Team | Those consulted on whether to act |
| Competent Authorities | Partners to notify. Create them as contacts first. |
| Scope | All products, or a named list of products or categories |
| Procedure | The decision route, communication route, disposition rules and out-of-hours arrangements. Approval is refused if this is empty. |
| Default Effectiveness Check Level | Level A unless you have a documented basis for a lower level |
| Target Reconciliation Rate | The closure gate for real actions. 100% is the default; set it lower only with a documented rationale. |
| Initiation Target (hours) | Your internal target from decision to first notice |
| Mock Recall Interval (months) | 12 is a common interval. Set 0 to disable the reminder. |

Approve the plan: Submit for Review, then Approve. Approval is refused
without a procedure and a deputy.

**Revising an approved plan.** Use New Revision. The current version
becomes obsolete and inactive, and a draft at version n+1 is created
with the same reference. Approved plans cannot be edited in place.

## 6. Products and lots

Distribution tracing reads lot movements. A product that is not
lot-tracked cannot be traced.

For each product in scope: set tracking to **By Lots** (or **By Unique
Serial Number**), and confirm that deliveries record the lot. Tracing
matches completed movements whose destination is a customer location.

## 7. What to configure outside this module

| Concern | Where |
|---------|-------|
| Retention and archival of recall records | Database backup and retention policy |
| Electronic signatures | Not provided; see `02_regulatory_analysis.md` §4 |
| Field-level audit trail | A dedicated audit trail module |
| Blocking recalled stock from picking | Warehouse procedure; this module warns but does not move goods |
