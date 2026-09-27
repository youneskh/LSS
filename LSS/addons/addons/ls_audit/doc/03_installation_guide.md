# 03 — Installation Guide

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 **Community Edition** |
| Python | As required by Odoo 19 |
| PostgreSQL | As required by Odoo 19 |
| Odoo modules | `base`, `mail`, `hr` — all in Community |
| Extra Python packages | **None** |

The module uses no Enterprise module and contains no Enterprise source code.

## 2. Installation

```bash
# 1. Copy the module onto an addons path
cp -r ls_audit /opt/odoo/addons/

# 2. Confirm it is on the path Odoo reads
grep addons_path /etc/odoo/odoo.conf

# 3. Update the module list and install
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_audit --stop-after-init
```

Then log in, enable Developer Mode, open **Apps** and confirm
*Life Sciences - Audit Management* shows as Installed.

### 2.1 Installing with demo data

Demo data is loaded only if the **database** was created with demo data
enabled. It creates four users with the logins `demo_ls_lead_auditor`,
`demo_ls_auditor`, `demo_ls_auditee` and `demo_ls_quality_manager`, plus a
worked example: two audit types, three areas, two auditor qualifications, an
approved four-question checklist, a programme and two audits.

**Never load demo data into production.** The demo users are real login
accounts.

## 3. Run the tests before anything else

This suite has **never been executed**. Verification to date was static only.
Run it on a throwaway database, not on your target database:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d test_ls_audit -i ls_audit \
         --test-enable --test-tags /ls_audit \
         --log-level=test --stop-after-init
```

All tests are tagged `post_install` and run after the module is installed.

**Interpreting failures.** A failure here is a defect in this module. Record
it, fix it, and re-run before proceeding. Do not install into a regulated
environment on the strength of the static analysis alone.

To run a single module:

```bash
--test-tags /ls_audit:TestAuditIndependence
```

## 4. Upgrade

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -u ls_audit --stop-after-init
```

### 4.1 What survives an upgrade

- All transactional data: programmes, audits, responses, findings, reports.
- Configuration you created: types, areas, auditors, categories, checklists.
- Your edits to the five shipped finding categories. They are loaded with
  `noupdate="1"` precisely so that an upgrade does not overwrite deadlines or
  CAPA policies you tuned.

### 4.2 What an upgrade will overwrite

- Views, menus, security groups, access rules, record rules, sequences, mail
  templates and scheduled actions. Customise these in a **separate module**
  that inherits, never by editing this one.

### 4.3 Before upgrading in a regulated environment

1. Back up the database and the filestore.
2. Upgrade a copy first.
3. Run the test suite against the upgraded copy.
4. Re-execute whatever qualification tests your validation plan requires.
5. Record the outcome under your change control procedure.

## 5. Uninstall

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> --uninstall ls_audit --stop-after-init
```

**Uninstalling deletes every audit record this module owns.** In a regulated
environment audit records are subject to retention requirements. Export first,
and handle the removal under change control.

## 6. Post-installation configuration

Order matters, because later steps depend on earlier ones.

1. Assign users to groups — see `06_administrator_manual.md` §2.
2. Create audit types.
3. Build the auditable area hierarchy and set an owner on each area. **The
   owner drives the impartiality check.** An area with no owner imposes no
   ownership restriction.
4. Register auditor qualifications. At least one must be flagged lead auditor,
   or no audit can ever be scheduled.
5. Review the five shipped finding categories and adjust deadlines and CAPA
   policy to your procedure.
6. Create and approve at least one checklist.
7. Create a programme.

Full detail in `04_configuration_guide.md`.

## 7. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Module not listed in Apps | Wrong addons path, or list not updated | Check `addons_path`; click Update Apps List in Developer Mode |
| Install fails on a `res.groups` field | Odoo version is older than 19 | This module targets 19.0 only. Odoo 19 replaced `res.groups.category_id` with `privilege_id` |
| Install fails on a view tag | Odoo version is older than 19 | Odoo 19 uses `<list>`; earlier versions use `<tree>` |
| "This audit cannot be scheduled" | No qualified lead auditor, expired qualification, or scope excludes an area | Open Configuration → Auditors; check the lead flag, the expiry date and the qualified scope. An empty scope means no restriction |
| Cannot save an audit — impartiality error | A team member is an auditee or owns an audited area | Change the team, or reconsider the area ownership |
| Cannot complete an audit | A mandatory question is still pending | Open the Questions tab; optional questions do not block |
| Cannot close a finding | Verification method or result is empty, or you are the auditee | Fill both fields; have someone other than the auditee close it |
| Cannot edit a closed record | Working as designed | Closed and issued records are immutable. Use a new record |
| Scheduled action does nothing | Cron disabled, or nothing overdue | Settings → Technical → Scheduled Actions; check Active and Next Execution |
| No app icon | `static/description/icon.png` missing from the deployed copy | Re-copy the module including `static/` |
