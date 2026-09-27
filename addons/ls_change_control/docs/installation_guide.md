# Installation Guide

Module: `ls_change_control` | Target: Odoo 19.0 Community Edition

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by the Odoo release in use |
| Python | The version supported by the Odoo release in use |
| Odoo modules | `base`, `mail`, `hr`. `mail` and `hr` are part of Odoo Community |
| Additional Python packages | None |
| Outgoing mail server | Required only if the three mail notifications are to be delivered |

The module does not require, and must not be installed alongside, any Odoo
Enterprise module.

## 2. Installation

### 2.1 Place the module on the addons path

```bash
cd /opt/odoo/addons
git clone <repository-url> ls_change_control
chown -R odoo:odoo ls_change_control
```

Confirm that the directory containing `ls_change_control` appears in
`addons_path` in the Odoo configuration file.

### 2.2 Install

```bash
sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf \
    -d <database> -i ls_change_control --stop-after-init
```

Or, from the interface: Apps, Update Apps List, search for
"Life Sciences - Change Control", Install.

### 2.3 Verify the installation

After installation, confirm each of the following.

| Check | Expected result |
|-------|-----------------|
| A `Change Control` application appears in the main menu | Present |
| Configuration, Impact Areas | 14 records |
| Configuration, Change Categories | 10 records, each with at least one approval role |
| Settings, Technical, Sequences, search `Change Control Request` | One sequence, prefix `CC/%(year)s/` |
| Settings, Technical, Scheduled Actions, search `Change Control` | Three active actions, daily |
| Settings, Technical, Email Templates, search `Change Control` | Three templates |
| Settings, Users and Companies, Groups, category `Change Control` | Four groups |

If any item is missing, the installation did not complete. Consult the server
log before proceeding.

## 3. Installation with demo data

Demo data creates three change requests in Draft and three implementation
actions. It is intended for a training or evaluation database only, never for
production.

```bash
sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf \
    -d <demo-database> -i ls_change_control --stop-after-init
```

Note that from Odoo 19, demo data is no longer loaded by default; the database
must have been created with demo data enabled.

## 4. Running the automated tests

The tests require a database that can be written to. Never run them against a
production database.

```bash
sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf \
    -d <test-database> -i ls_change_control \
    --test-enable --test-tags /ls_change_control \
    --log-level=test --stop-after-init
```

The suite is tagged `post_install`, so it runs after the module and its
dependencies are fully loaded.

## 5. Upgrade

```bash
sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf \
    -d <database> -u ls_change_control --stop-after-init
```

An upgrade never overwrites the change control configuration: all data files
are declared with `noupdate="1"`. Categories, impact areas, approval
templates, mail templates and scheduled actions modified on the site are
preserved.

Before any upgrade on a validated system:

1. Take a full backup of the database and of the filestore.
2. Perform the upgrade on a copy first.
3. Execute the automated test suite on the copy.
4. Execute the operational qualification tests defined by the organisation.
5. Record the outcome under the change control procedure of the organisation. An upgrade of a validated system is itself a change.

## 6. Uninstallation

```bash
sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf \
    -d <database> --stop-after-init
```

then Apps, Life Sciences - Change Control, Uninstall.

**Uninstalling deletes every change control record.** In a regulated
environment, change control records are subject to a retention period.
Export the records and confirm the retention obligation with the quality unit
before uninstalling.

## 7. Post-installation configuration

Installation alone does not make the module usable. Proceed to
`docs/configuration_guide.md` and perform at minimum:

1. Assign the four security groups to the users.
2. Review and approve the categories, the impact areas and the approval matrices.
3. Set the company parameters.
4. Assign a default approver to each approval template line, or accept that approvers are assigned request by request.
