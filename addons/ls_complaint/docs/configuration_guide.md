# Configuration Guide

## 1. What must be configured before first use

The module ships with **no complaint category** and therefore **no time
target**. This is deliberate: a target is a commitment made by the organisation,
not a value the software may choose. Until at least one category exists, a
complaint cannot leave the Received state.

## 2. Assign the access levels

Settings → Users & Companies → Users → a user → *Life Sciences Complaint
Management*.

| Level | Give it to |
|---|---|
| Complaint Viewer | Anyone who must read complaints without acting: management, auditors, read-only quality staff |
| Complaint Investigator | Customer service, quality officers, vigilance officers who record and investigate |
| Complaint Reviewer | Quality assurance staff who approve investigations and close complaints |
| Complaint Manager | The process owner and the system administrator |

Segregation of duties is enforced per record, not by the levels: a reviewer may
investigate a complaint, but never approve the investigation he performed, and
never review the closure of a complaint he is responsible for.

## 3. Create the complaint categories

Complaints → Configuration → Complaint Categories.

| Field | Meaning | Guidance |
|---|---|---|
| Name, Code | Identification | The code must be unique per company |
| Default Severity | Severity proposed when the category is chosen | Always overridable by the assessor |
| Investigation Required | Blocks the waiver path | Leave enabled unless the procedure explicitly allows a waiver for that category |
| Acknowledgement Target (days) | Calendar days from receipt | `0` means no target |
| Investigation Target (days) | Calendar days from receipt | `0` means no target |
| Closure Target (days) | Calendar days from receipt; drives the *Overdue* flag and the daily notification | `0` means no target and no overdue detection |
| Adverse Event Reporting Deadline (days) | Calendar days from the awareness date; drives the reporting due date and its notification | `0` means no deadline and no notification |

**The four day values must come from the organisation's own approved procedure**
and, for the reporting deadline, from a Regulatory Affairs determination against
the regulations applicable to the product and the market. The module proposes no
value and validates none.

The only checks applied are arithmetical: no negative value, and the
acknowledgement target must not exceed the closure target.

## 4. Review the scheduled actions

Settings → Technical → Automation → Scheduled Actions.

| Action | Default | Notes |
|---|---|---|
| Life Sciences: Overdue Complaint Notification | daily | Creates one to-do activity per overdue complaint for its responsible user; never duplicates |
| Life Sciences: Adverse Event Reporting Deadline Notification | daily | Same, for reportable events at or past their deadline |

Both are `noupdate`, so a change of interval or an activation change survives a
module update.

## 5. Adapt the mail templates

Settings → Technical → Email → Email Templates.

Two templates are delivered, both on `ls.complaint`, neither sent
automatically:

- *Complaint: Acknowledgement of Receipt*
- *Complaint: Closure Notification*

Adapt the wording, the sender and the language to the organisation's
communication standards. Sending remains a manual decision.

## 6. Multi-company

Each complaint belongs to one company, and every child record inherits it. Five
global record rules restrict every model to the companies active for the user.
The three sequences are company-independent by default; to number complaints
separately per company, duplicate each sequence with a `company_id` and a
distinct prefix — the code assigning the reference already uses `with_company`.

## 7. Optional: relax the ownership rule

By default an investigator may only modify the complaints where he is the
responsible or the receiving user. In a small team this can obstruct work.

Settings → Technical → Security → Record Rules → *Complaint: investigator writes
own complaints* → either deactivate it or widen its domain. Record the change:
it removes a segregation control.

## 8. Configuration checklist

| # | Item | Done |
|---|---|---|
| 1 | Access levels assigned to every user who needs one | ☐ |
| 2 | At least one complaint category created | ☐ |
| 3 | Every category's day targets set from the approved procedure, or deliberately left at 0 | ☐ |
| 4 | Reporting deadline determined by Regulatory Affairs, per category | ☐ |
| 5 | Scheduled actions reviewed and active | ☐ |
| 6 | Mail templates adapted | ☐ |
| 7 | Multi-company behaviour verified, if applicable | ☐ |
| 8 | Ownership record rule decision recorded | ☐ |
