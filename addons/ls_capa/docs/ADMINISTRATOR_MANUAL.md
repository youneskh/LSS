# ls_capa — Administrator Manual

Audience: Odoo administrators and system owners operating the module in
a regulated environment.

---

## 1. Security model

### Groups

Four groups sit under the `res.groups.privilege` record **CAPA
Management** (Odoo 19 replaced the direct `category_id` on `res.groups`
with this indirection).

```
CAPA Manager  →  CAPA Coordinator  →  CAPA Investigator  →  CAPA Viewer
        (implies)          (implies)            (implies)
```

### Access control matrix

| Model | Viewer | Investigator | Coordinator | Manager |
|---|---|---|---|---|
| `ls.capa.issue` | R | R W C | R W C | R W C D |
| `ls.capa.root_cause` | R | R W C | R W C | R W C D |
| `ls.capa.action` | R | R | R W C | R W C D |
| `ls.capa.effectiveness` | R | R | R W C | R W C D |
| `ls.capa.category` | R | R | R | R W C D |
| `ls.capa.close.wizard` | — | — | R W C D | R W C D |

R read, W write, C create, D delete.

Investigators deliberately cannot create actions or effectiveness
checks: this enforces separation between investigating a cause and
committing the organization to remediation.

### Record rules

Five global `ir.rule` records restrict every model to the user's allowed
companies. They are global, so they apply to CAPA Managers as well.
Child records derive their company from the parent CAPA through a stored
related field, so a CAPA cannot have children in another company.

### Workflow enforcement

Every gate is implemented in the model layer and raises `UserError`.
Gates therefore hold for XML-RPC, JSON-RPC, data import and server
actions, not only for the user interface. Buttons in views control
visibility only and are not a security boundary.

## 2. What this module does and does not provide for compliance

State this clearly to auditors.

**Provided:** attributable state transitions logged in the chatter, field
change tracking on tracked fields, mandatory evidence and justification
at defined gates, segregated duties, multi-company isolation, and a
printable record.

**Not provided:**

| Requirement | Status | Where it belongs |
|---|---|---|
| Electronic signatures (21 CFR Part 11) | **Not implemented** | `ls_electronic_signature` |
| Tamper-evident, hash-chained audit trail | **Not implemented** | `ls_audit_trail` |
| Controlled document management | Not implemented | `ls_document_management` |
| Training and competency records | Not implemented | `ls_training` |

Odoo user tracking is **not** equivalent to a Part 11 compliant
electronic signature. Do not represent it as one.

## 3. Data retention

CAPA records that progressed beyond Identified cannot be deleted through
the ORM; `unlink` raises `UserError`. Records still in Identified **can**
be deleted by a CAPA Manager, and deletion cascades to root causes,
actions and effectiveness checks.

If your retention policy forbids deletion entirely, remove the delete
permission from the CAPA Manager ACL lines in
`security/ir.model.access.csv` and reinstall, or revoke it at runtime via
*Settings > Technical > Access Rights*.

Uninstalling the module drops all CAPA data irreversibly.

## 4. Backup and recovery

The module stores no data outside PostgreSQL and the standard Odoo
filestore (attachments posted to the chatter). Standard Odoo backup
procedures are sufficient. Back up before every module upgrade.

## 5. Scheduled action

*CAPA: Notify Overdue Records* runs `_cron_notify_overdue()` on
`ls.capa.issue` as the root user, daily, and is **shipped inactive**.

It searches open CAPA records past their due date and posts a chatter
message addressed to the CAPA owner. It does not deduplicate, so the
interval sets the reminder frequency. On a database with a large backlog
of overdue records the first run posts one message per record; review
the backlog before activating.

## 6. Performance

Indexed fields: `name`, `state`, `company_id` on `ls.capa.issue`;
`issue_id`, `state`, `company_id` on the child models. The relation
count computation uses `_read_group` rather than per-record searches.

`is_overdue` and `is_late` are computed but not stored; both implement a
`search` method so filtering is executed in SQL rather than in Python.
`progress` is stored and recomputed when action states change.

## 7. Monitoring

Watch for:

- `UserError` volume on workflow transitions, which usually indicates
  users being blocked by a gate they do not understand rather than a
  defect.
- CAPA records sitting in one status beyond your procedural target.
- Effectiveness checks concluded Not Effective without a follow-up CAPA.

The pivot and graph views on `ls.capa.issue` support periodic quality
management review reporting.

## 8. Upgrading

```bash
odoo-bin -d <database> -u ls_capa --stop-after-init
```

Records marked `noupdate="1"` — sequences, the scheduled action, the
five default categories and the record rules — are preserved with any
local edits. Group definitions are updatable so implication changes
apply.

Always test an upgrade against a restored copy of production first, and
re-run the test suite on that copy.

## 9. Validation obligations

Installing this module in a GxP environment triggers computerised system
validation obligations that the software cannot satisfy on its own. See
`VALIDATION_REPORT.md` for the outstanding qualification activities.
