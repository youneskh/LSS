# Administrator Manual — `ls_medical_device`

## 1. Access levels

| Group | XML ID | Implies |
|---|---|---|
| Viewer | `group_ls_md_viewer` | — |
| User | `group_ls_md_user` | Viewer |
| Regulatory Affairs | `group_ls_md_regulatory` | User |
| Manager | `group_ls_md_manager` | Regulatory Affairs |

The groups are attached to a `res.groups.privilege` record, which replaced the
module category reference on `res.groups` in Odoo 19.0.

## 2. Permission matrix

| Model | Viewer | User | Regulatory | Manager |
|---|---|---|---|---|
| Device | R | RWC | RWC | RWCU |
| Risk class | R | R | R | RWCU |
| Notified body | R | R | RWC | RWCU |
| UDI assignment | R | RWCU | RWCU | RWCU |
| Risk file / risk | R | RWCU | RWCU | RWCU |
| Clinical evaluation | R | RWCU | RWCU | RWCU |
| PMCF evaluation | R | RWCU | RWCU | RWCU |
| Technical documentation | R | RWCU | RWCU | RWCU |
| CE marking | R | RWC | RWCU | RWCU |
| Surveillance plan | R | RWCU | RWCU | RWCU |
| Periodic report | R | RWCU | RWCU | RWCU |

R = read, W = write, C = create, U = unlink.

## 3. How segregation of duties is implemented

Two layers, deliberately:

1. **`ir.model.access` records** control create, read, write and unlink.
2. **Python authority checks** inside the business methods control approval
   and market status changes.

The second layer exists because a restriction implemented only in a view does
not survive programmatic access. `_check_approval_authority` and
`_check_regulatory_authority` call `user.has_group()` and raise `UserError`
when the level is insufficient.

Additionally, an approver may not approve a record they authored. This is
checked against the author or evaluator field on each controlled model.

## 4. Record rules and multi-company

Twelve record rules implement multi-company scoping with the domain:

```
['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
```

**All rules are global — no group is attached to any of them.** The reason is
stated in the data file: the name of the field holding the groups of an
`ir.rule` record in Odoo 19.0 could not be verified from official
documentation. Writing an unverified field name into a data file aborts the
installation. Global rules do not need that field.

The consequence: the record rules implement multi-company scoping only.
Differentiation between the four access levels is implemented through
`ir.model.access` and the Python authority checks described above. This is a
design decision, not an omission.

The computed field `ir.rule.global` is never written in the data files; Odoo
derives it from the presence or absence of groups.

## 5. Scheduled actions

Created by the post-installation hook in `hooks.py`, not by an XML data file.
The hook filters the value dictionary against the fields `ir.cron` actually
declares in the running registry, because the exact field set in Odoo 19.0
could not be verified.

| Action | Model | Method |
|---|---|---|
| Check Post-Market Obligations | `ls.md.device` | `_cron_check_post_market_obligations` |
| Expire Certificates | `ls.md.ce_marking` | `_cron_expire_certificates` |

Both run daily. Each is created with an external identifier so an upgrade
updates rather than duplicates it.

To disable one, archive it in Settings → Technical → Scheduled Actions rather
than deleting it; a module upgrade would recreate a deleted record.

## 6. Data retention

MDR Article 10(8) requires the technical documentation, the EU declaration of
conformity and any relevant certificate to remain available to competent
authorities for at least 10 years after the last device covered by the
declaration was placed on the market, and at least 15 years for implantable
devices.

The device computes `documentation_retention_years` from the implantable flag
and `documentation_retention_until` from the market withdrawal date. The
retention end date is only available once withdrawal has been recorded.

**The module does not enforce retention.** It computes and displays the date.
Preventing deletion of the underlying evidence is the responsibility of the
document management system and the backup policy of the organisation.

Approved regulatory records cannot be deleted through the interface; they are
cancelled instead. Deletion of draft records remains possible for users with
unlink rights.

## 7. Backup and archiving

Devices, notified bodies, risk classes, evidence sources and section templates
carry an `active` flag and are archived rather than deleted.

Controlled records — risk files, clinical evaluations, technical
documentation, plans, reports — do not carry an `active` flag. Their lifecycle
states `superseded` and `cancelled` serve the equivalent purpose while keeping
the record visible in its history.

## 8. Upgrade considerations

- Selection values (risk scales, states, conformity routes) live in
  `models/constants.py`. Changing one after records exist requires a data
  migration; the module ships none.
- The section templates are `noupdate="1"` data. Edits made by the
  organisation survive an upgrade. New template entries added by a future
  version will not be seeded into documentation records that already exist.
- The scheduled action hook is idempotent and safe to re-run.

## 9. Troubleshooting

| Symptom | Cause |
|---|---|
| A user cannot place a device on the market | Missing Regulatory Affairs level, or no approved technical documentation, or no issued certificate where the class requires a notified body |
| Approval is refused for the record's author | Expected: an approver may not approve their own record |
| A record cannot be edited | It has left the draft status. Create a new version |
| No due date appears for a class I device | Expected: Article 85 sets no fixed interval, so the class ships with an interval of zero |
| A periodic report for an implantable is not flagged for submission | Check that the device implantable flag was set before the report was created |
