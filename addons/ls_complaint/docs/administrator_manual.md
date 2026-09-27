# Administrator Manual

## 1. Responsibilities of the administrator

| Area | Task |
|---|---|
| Access | Assign the four levels, review them periodically |
| Master data | Create and maintain the complaint categories and their targets |
| Automation | Monitor the two scheduled actions |
| Communication | Maintain the two mail templates |
| Records | Monitor archived and cancelled complaints |
| Integration | Maintain the CAPA reference discipline until a CAPA module exists |
| Change control | Record every configuration change under the organisation's change control procedure |

## 2. Security model in practice

Four cumulative groups: Viewer ⊂ Investigator ⊂ Reviewer ⊂ Manager.

Segregation of duties is enforced **per record**, server-side:

- an investigation cannot be approved by its own investigator;
- a complaint cannot be closed with a reviewer equal to its responsible user;
- both are also expressed as ORM constraints, so they cannot be bypassed by the
  external API.

Only the Manager can delete, and deletion is additionally blocked by the ORM for
any record past its initial state. In practice **no record that carries evidence
can be deleted from the user interface or from the API**.

## 3. What this module does not protect against

Stated plainly, because the opposite assumption is dangerous:

1. A PostgreSQL superuser can modify or delete anything, including the message
   history. The freezing described above is enforced by the ORM, not by the
   database.
2. Odoo field tracking is not a 21 CFR Part 11 audit trail: there is no hash
   chain, no independent verification and no signature meaning. See
   `docs/02_regulatory_analysis.md` section 4.
3. There is no re-authentication on approval or closure. The recorded identity
   is the session identity.
4. Attachments are standard Odoo attachments, with no version control and no
   retention enforcement.

If the organisation is subject to electronic record and signature requirements,
these are gaps to be closed by other means before the module is used for
regulated records.

## 4. Diagnosing "a user cannot see or edit a record"

| Question | Where to look |
|---|---|
| Does the user have a complaint level? | Settings → Users → the user |
| Is the record in the user's allowed company? | The global multi-company rule uses `company_ids` |
| Is the user an investigator trying to write someone else's complaint? | Record rule *Complaint: investigator writes own complaints* — expected behaviour |
| Is the record closed or cancelled? | Freezing is server-side and applies to everyone |
| Is the record archived? | Filter *Archived* |

## 5. Monitoring

| Signal | Where |
|---|---|
| Overdue complaints | Filter *Overdue* on the complaint list; red rows |
| Overdue adverse event reports | Filter *Reporting Overdue*; red rows |
| Scheduled actions running | Settings → Technical → Scheduled Actions → last execution |
| Activities created by the crons | The server log records `ls_complaint: N overdue activities created` |
| Categories without targets | Category list; the four target columns are visible |

A category left at `0` produces no due date, no overdue flag and no
notification. That is intended, but it must be a decision, not an oversight.

## 6. Re-parenting the menu under a future Quality menu

The module creates its own `Complaints` root menu because the `Quality` root
menu belongs to `ls_qms`, which does not exist. When it does, create a small
bridge module that depends on both and contains:

```xml
<record id="ls_complaint.menu_ls_complaint_root" model="ir.ui.menu">
    <field name="parent_id" ref="ls_qms.menu_ls_qms_root"/>
    <field name="web_icon"></field>
</record>
```

Do not edit `ls_complaint` itself: the change would be lost on update and would
create a dependency that cannot be satisfied.

## 7. Backup and retention

Complaint records are quality records. Their retention period is set by the
organisation's procedure and by the applicable regulation, not by this module,
which implements **no** retention policy and **no** automatic archival. Include
the Odoo database and its filestore in the backup plan, and verify restoration
periodically.

## 8. Before every module update

1. Back up the database and the filestore.
2. Update on a copy first and run the test suite there.
3. Confirm the two scheduled actions kept their interval and active state — they
   are `noupdate`, so they should.
4. Confirm the categories kept their targets — they are user data and are never
   overwritten.
5. Record the update under change control.

## 9. Known operational limitations

| # | Limitation |
|---|---|
| 1 | No automatic acknowledgement to the complainant; the template exists but sending is manual |
| 2 | No escalation beyond the daily to-do activity |
| 3 | No CAPA verification; the reference is free text |
| 4 | No automatic transmission of any report to any authority |
| 5 | No kanban view; list, graph and pivot only |
| 6 | No translation file delivered |
| 7 | No dashboard model; analysis relies on the standard views |
