# Administrator Manual

Module: `ls_calibration` `19.0.1.0.0`. Audience: Odoo administrators and IT.

## 1. Technical objects created by the module

| Type | Identifier | Purpose |
|------|-----------|---------|
| Group | `group_ls_calibration_viewer` | Read-only |
| Group | `group_ls_calibration_technician` | Execution |
| Group | `group_ls_calibration_manager` | Administration and approval |
| Rule | `ls_calibration_*_company_rule` | Multi-company isolation, six rules |
| Sequence | `ls_calibration_*_sequence` | Four numbering sequences |
| Parameter | `ls_calibration.generation_horizon_days` | Generation horizon |
| Cron | `ls_calibration_cron_notify_due` | Daily notification |
| Cron | `ls_calibration_cron_generate_records` | Daily generation |
| Report | `action_report_ls_calibration_record` | PDF record |
| Report | `action_report_ls_calibration_certificate` | PDF certificate |

## 2. Routine administration

| Task | Frequency | Action |
|------|-----------|--------|
| Check the scheduled actions | Weekly | Open each action and check the last execution date and the absence of error. Odoo 19 disables a scheduled action that fails repeatedly. |
| Check the volume of open draft records | Monthly | An accumulation means calibrations are generated but not performed. |
| Check the overdue instruments | Weekly | *Calibration Status → Due and Overdue*. |
| Check the expired certificates | Quarterly | *Certificates*, filter *Expired*. |
| Review the group assignments | On personnel change | At least two distinct people must hold the manager role, otherwise no approval is possible when one is absent. |

## 3. Multi-company

Each business record carries a `company_id`. On the plan, the record, the
line and the certificate, it is derived from the instrument, so it can never
diverge. Six global record rules restrict the visibility to the companies
active in the session. Relational fields carry `check_company=True` and the
models declare `_check_company_auto = True`, so the ORM refuses a link
between records of different companies.

An instrument, its plans, its records and its certificates therefore always
belong to a single company.

## 4. Backup and retention

The calibration records and the certificates are regulated evidence. They are
stored in the PostgreSQL database. The certificate documents are stored as
attachments, that is, in the file store directory of the instance, not in the
database. **A backup that covers only the database does not cover the
certificate documents.** The backup procedure must include the file store.

The module does not implement an automatic purge. Nothing is ever deleted by
the system. Retention is a business decision, applied manually and under
change control.

## 5. Monitoring

Both scheduled actions return a count, visible in the Odoo log at the end of
the execution. Points to watch:

| Symptom | Interpretation |
|---------|----------------|
| The notification action returns 0 every day for a long period | Either nothing is due, or no instrument is *In Service*, or the plans are not active. |
| The generation action returns 0 while records are due | Every due plan already has an open record. |
| A scheduled action becomes inactive | Odoo 19 disables a job that fails repeatedly. Read the log, correct the cause, reactivate. |

## 6. Performance

Indexes are declared on the fields used by the searches and the scheduled
actions. One operation is not delegated to PostgreSQL: filtering on the
calibration status, which is resolved in Python because it depends on the
current date and on the per-instrument lead time. On a register of a few
thousand instruments the cost is negligible. If the register grows by an
order of magnitude, replace the per-instrument lead time by a single global
parameter, which makes the filter expressible in SQL.

## 7. Update procedure

1. Restore a copy of production on a test instance.
2. Apply the update there: `odoo-bin -d <copy> -u ls_calibration --stop-after-init`.
3. Run the module tests on that copy.
4. Verify the checks IV-01 to IV-08 of the installation guide.
5. Verify that an approved record is still locked and still prints.
6. Apply the update to production during a change window, after a full backup
   including the file store.

The data files are `noupdate="1"`, therefore an update never overwrites the
sequences, the parameter or the scheduled actions.

## 8. Security administration

| Point | Rule |
|-------|------|
| Do not grant the manager group by default | Approval is a quality responsibility. |
| Do not use a shared account | Attributability of the signatures depends on individual accounts. |
| Do not deactivate the record rules | They are the multi-company isolation. |
| Do not grant delete rights beyond the manager group | Only draft records are deletable, but the rights must remain restricted. |
| Server actions and automation | Adding an automation that writes on approved records will be refused by the ORM overrides. This is intended. |

## 9. Known administrative limitations

| # | Limitation | Consequence |
|---|------------|-------------|
| AL-01 | The security groups carry no category | They appear in the uncategorised section of the user form. Assign them to a privilege in the target database if a grouped presentation is required. |
| AL-02 | The approval does not re-authenticate the signer | The module alone does not provide FDA 21 CFR Part 11 electronic signatures. |
| AL-03 | The audit trail is the standard Odoo change tracking | A complete, tamper-evident audit trail requires a dedicated module. |
| AL-04 | Uninstalling deletes all the data | Uninstallation destroys regulated evidence and must go through change control. |
