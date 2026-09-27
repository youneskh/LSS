# INSTALLATION GUIDE

Module: `ls_training` · Target: Odoo 19.0 Community Edition

---

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Odoo | 19.0 Community Edition |
| Python | As required by Odoo 19 |
| PostgreSQL | As required by Odoo 19 |
| Odoo modules | `base`, `mail`, `hr` (installed automatically as dependencies) |
| Additional Python packages | **None** |

`python-dateutil` is used by the module but is already a hard dependency of
Odoo itself, so nothing extra is installed.

## 2. Read this first

This module was built without access to a running Odoo 19 instance.
**Installation has never been performed.** Before installing on any system
that matters, read `verification_notes.md`, in particular §2, which
describes the one known API uncertainty that can block installation and the
one-line fix for it.

Install on a scratch database first.

## 3. Installation

### 3.1 Place the module

Copy the `ls_training` directory into a directory listed in your
`addons_path`:

```bash
cp -r ls_training /opt/odoo/custom-addons/
```

Confirm the path is declared in your Odoo configuration file:

```ini
[options]
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
```

### 3.2 Update the apps list

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -u base --stop-after-init
```

Or, in the interface: enable developer mode, then **Apps → Update Apps
List**.

### 3.3 Install

Command line:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_training --stop-after-init
```

Interface: **Apps**, remove the "Apps" filter, search `Training
Management`, click **Install**.

With demo data (scratch databases only):

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_training --without-demo=False --stop-after-init
```

## 4. If installation fails

### 4.1 `Invalid field 'group_ids' on model 'ir.rule'`

This is the anticipated failure described in `verification_notes.md` §2.

Edit `ls_training/__manifest__.py` and change this line:

```python
"security/ls_training_record_rules.xml",
```

to:

```python
"security/ls_training_record_rules_alt_groups.xml",
```

Exactly one of the two must be listed. Retry the installation.

### 4.2 Error mentioning `privilege_id` or `res.groups.privilege`

The target is not Odoo 19. This module uses the Odoo 19 group model and
will not install on Odoo 18 or earlier without modification.

### 4.3 Error mentioning `<chatter/>`

Replace each `<chatter/>` element in `views/` with the legacy block:

```xml
<div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div>
```

Affects `ls_training_course_views.xml`, `ls_training_session_views.xml`,
`ls_training_certification_views.xml` and
`ls_training_competency_assessment_views.xml`.

### 4.4 Error mentioning `_sql_constraints`

See `verification_notes.md` §3. The eight constraints are listed in
`functional_specification.md` §3.4 for translation to a newer syntax.

## 5. Post-installation verification

Perform these checks before declaring the installation successful.

| # | Check | Expected |
|---|-------|----------|
| 1 | Menu **Training** appears | Root menu visible to a user in any training group |
| 2 | Submenus | Operations, Reporting, Configuration present |
| 3 | **Settings → Users & Companies → Groups** | Four groups under "Life Sciences Training": Learner, Viewer, Trainer, Manager |
| 4 | **Settings → Technical → Sequences** | `ls.training.course`, `ls.training.session`, `ls.training.certification` |
| 5 | **Settings → Technical → Scheduled Actions** | Two actions named "Training: …", both active, daily |
| 6 | **Settings → Technical → Record Rules**, filter model `ls.training.*` | 13 rules |
| 7 | **Settings → Technical → System Parameters** | `ls_training.expiry_warning_days` = 30 |
| 8 | **Settings → Technical → Email Templates** | "Training: Certification Expiry Reminder" |
| 9 | Employee form | "Training" tab and "Certifications" smart button |
| 10 | Create a course, approve it, create a session | No error |

## 6. Run the test suite

**The suite has never been executed.** Run it before any further use:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <test_database> \
         -i ls_training --test-enable --stop-after-init \
         --log-level=test
```

To run only this module's tests on an existing database:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <test_database> \
         -u ls_training --test-enable --test-tags /ls_training \
         --stop-after-init
```

Expect failures on the first run. Treat any failure as a defect to be
investigated, not as a reason to skip testing. Record results in your own
copy of `test_report.md`.

## 7. Measure coverage

```bash
coverage run --source=/opt/odoo/custom-addons/ls_training \
    odoo-bin -c /etc/odoo/odoo.conf -d <test_database> \
    -i ls_training --test-enable --stop-after-init
coverage report -m
coverage html
```

The 95% figure in the brief is a target. No coverage measurement has been
made.

## 8. Upgrade

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -u ls_training --stop-after-init
```

Data files carrying `noupdate="1"` (sequences, parameters, cron, mail
template) are not overwritten on upgrade, so local customisation survives.
Demo data uses `noupdate="0"` and is refreshed.

## 9. Uninstallation

Uninstalling **deletes all training data**: courses, sessions, attendance,
certifications, assessments and requirements. In a regulated environment
this destroys quality records.

Export or archive the data first. Then, in **Apps**, open the module and
select **Uninstall**.
