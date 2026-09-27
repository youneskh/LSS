# 06 — Administrator Manual

Audience: Odoo system administrator and system owner.

---

## 1. What this module adds

| Object | Count | Location |
|---|---|---|
| Models | 14 (11 persistent, 3 transient) | `models/`, `wizards/` |
| Security groups | 4 | `security/ls_audit_groups.xml` |
| Access rules | 37 | `security/ir.model.access.csv` |
| Record rules | 10 global + role rules | `security/ls_audit_record_rules.xml` |
| Sequences | 4 | `data/ir_sequence_data.xml` |
| Mail templates | 4 | `data/mail_template_data.xml` |
| Scheduled actions | 3 | `data/ir_cron_data.xml` |
| PDF reports | 2 | `report/` |

No Odoo core model is modified. Everything is additive.

---

## 2. Security groups

Hierarchical — each implies the one below, so assign **one** group per user.

| Group | Assign to |
|---|---|
| `group_ls_audit_auditee` | Process owners who answer findings |
| `group_ls_audit_auditor` | Qualified auditors |
| `group_ls_audit_lead_auditor` | Auditors who lead engagements |
| `group_ls_audit_manager` | Quality management |

Assigning Manager also grants the three below it. Assigning several audit
groups to one user is harmless but pointless.

> **Odoo 19 note.** The user-to-group field is `group_ids`. It was named
> `groups_id` up to Odoo 18. Scripts written for earlier versions will fail.

### 2.1 Permissions summary

| Capability | Auditee | Auditor | Lead | Manager |
|---|---|---|---|---|
| See own findings | Yes | Yes | Yes | Yes |
| See all findings | No | Yes | Yes | Yes |
| Answer findings | Yes | Yes | Yes | Yes |
| Record assessments | No | Yes | Yes | Yes |
| Raise findings | No | Yes | Yes | Yes |
| Create audits | No | No | Yes | Yes |
| Drive audit lifecycle | No | No | Yes | Yes |
| Verify and close findings | No | No | Yes | Yes |
| Prepare reports | No | Yes | Yes | Yes |
| Review / approve / issue reports | No | No | No | Yes |
| Approve checklists | No | No | No | Yes |
| Maintain configuration | No | No | No | Yes |
| Delete records | No | No | No | Yes |

### 2.2 Segregation of duties still applies inside a group

A Manager holds every group, but **cannot** review or approve a report they
prepared themselves. Group membership does not defeat the segregation checks,
which compare user identity, not privilege.

---

## 3. Record rules

### 3.1 Company isolation — global

Ten global rules restrict every transactional model to
`company_id in company_ids`. Global rules carry **no group** and therefore
cannot be bypassed by adding a group to a user.

> `ir.rule.global` is a **computed, stored** field derived from `groups`: a
> rule with no groups is global. Never write it directly.

### 3.2 Row-level restriction for auditees

| Model | An auditee sees |
|---|---|
| `ls.audit.finding` | Findings where they are the auditee |
| `ls.audit.schedule` | Audits where they appear as an auditee |
| `ls.audit.response` | Questions of audits they take part in |
| `ls.audit.report` | **Issued** reports naming them as a recipient |

Auditor and above see everything within their company.

Draft, under-review and approved reports are invisible to auditees by design:
a report is a communication, and it communicates when it is issued.

---

## 4. Scheduled actions

**Settings → Technical → Automation → Scheduled Actions** (Developer Mode).

| Action | Interval | Behaviour |
|---|---|---|
| Overdue audits | Daily | One `mail.activity` for the lead auditor per audit past its planned date and not started. **Idempotent** — re-running does not duplicate |
| Overdue findings | Daily | Notifies on findings past `response_due_date` and not closed |
| Auditor qualifications | Weekly | Recomputes qualification status, then reports expiring (≤60 days) and expired |

The qualification cron recomputes before filtering because the stored status
depends on the current date and would otherwise go stale between runs.

`numbercall` and `doall` are **deliberately not set**. Their behaviour in
Odoo 19 could not be verified; omitting them leaves the framework default,
which is an indefinitely recurring job with no missed-run replay.

To disable a notification, untick **Active**. Do not delete the record — an
upgrade will recreate it.

---

## 5. Data model reference

### 5.1 Persistent models

| Model | Purpose |
|---|---|
| `ls.audit.type` | Audit classification |
| `ls.audit.area` | Hierarchical auditable area with owner |
| `ls.audit.auditor` | Qualification register |
| `ls.audit.finding.category` | Severity, deadline, root cause and CAPA policy |
| `ls.audit.checklist` | Versioned template |
| `ls.audit.checklist.line` | Template question |
| `ls.audit.program` | Programme |
| `ls.audit.schedule` | The audit engagement |
| `ls.audit.response` | One assessed question |
| `ls.audit.finding` | One departure from criteria |
| `ls.audit.report` | Report concluding an audit |

### 5.2 Transient models

`ls.audit.checklist.load`, `ls.audit.finding.response`, `ls.audit.cancel`.
Vacuumed automatically by Odoo.

### 5.3 Master data loaded `noupdate="1"`

The five finding categories. Your edits to deadlines and CAPA policy survive
upgrades. To reset one, delete it and reinstall the module.

---

## 6. Backup and retention

Standard Odoo backup covers this module: PostgreSQL database plus filestore.
Evidence attachments live in the **filestore**, not the database — a
database-only backup loses them.

In a regulated environment, audit records are subject to retention
requirements that usually outlive the software. Retention is **not**
implemented here. Plan for archival export independently.

Uninstalling deletes every record this module owns. Treat uninstall as a
change-controlled activity.

---

## 7. Performance

Indexed fields: `reference`, `state`, `company_id`, `date_planned`,
`response_due_date`, plus the many-to-one keys.

`is_overdue` on audits and findings is a non-stored computed field with a
**search method**, so filtering on it produces a real SQL domain rather than
loading every record into memory.

Expected volumes are modest — hundreds of audits and thousands of findings
per year at a large site. No partitioning or archival strategy is needed at
that scale.

---

## 8. Monitoring

| Check | Where |
|---|---|
| Cron failures | Server log; `ir.cron` last-run values |
| Expiring qualifications | Configuration → Auditors, filter Expiring or Expired |
| Overdue audits | Audits list, Overdue filter |
| Overdue findings | Findings list, Overdue filter |
| Programme completion | Programme form, completion rate |

---

## 9. Customisation policy

**Never edit this module in place.** Create a separate module depending on
`ls_audit` and use inheritance:

- `_inherit` on models to add fields or extend methods.
- `xpath` in inheriting views to modify the UI.
- New `ir.rule` records for extra restriction.

Editing this module means every upgrade overwrites your work, and it destroys
the traceability between the module version and its validation evidence.

---

## 10. Upgrade checklist for a regulated environment

- [ ] Database and **filestore** backed up
- [ ] Upgrade rehearsed on a copy
- [ ] Test suite run against the upgraded copy
- [ ] Customisations in separate modules, still installing
- [ ] Qualification tests re-executed per your validation plan
- [ ] Change control record raised, reviewed and approved
- [ ] Users informed of behaviour changes
