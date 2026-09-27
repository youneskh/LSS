# Installation Guide

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, version supported by Odoo 19 |
| Python | The version required by Odoo 19 |
| Python library | `python-dateutil`, already required by Odoo |
| Odoo modules | `base`, `web`, `mail`, `maintenance`, all Community |

No Odoo Enterprise module, no OCA module and no third-party module is
required. If `maintenance` is not yet installed, Odoo installs it
automatically as a dependency.

## 2. Installation

1. Copy the `ls_calibration` directory into a directory listed in the
   `addons_path` of the instance. Do not rename the directory: the module
   technical name is derived from it and is referenced by every XML
   identifier.
2. Check the file ownership and permissions so that the Odoo service can read
   the directory.
3. Restart the Odoo service.
4. Log in as an administrator, open **Apps**, click **Update Apps List**.
5. Remove the *Apps* filter if necessary, search for `ls_calibration` or for
   *Calibration*, and click **Install**.

Command line equivalent:

```
odoo-bin -d <database> -i ls_calibration --stop-after-init
```

To install with the demonstration data, create the database with
demonstration data enabled; the module then loads three instruments, two
plans, one approved calibration record and one issued certificate.

## 3. What the installation creates

| Object | Quantity |
|--------|----------|
| Models | 8 |
| Security groups | 3 |
| Access rules | 21 |
| Record rules | 6 |
| Sequences | 4 |
| System parameters | 1 |
| Scheduled actions | 2 |
| Window actions | 8 |
| Report actions | 2 |
| Menu items | 9 |

## 4. Verification of the installation

Perform these checks before declaring the installation successful.

| # | Check | Expected result |
|---|-------|-----------------|
| IV-01 | The module appears as installed in **Apps**. | State *Installed*, version `19.0.1.0.0`. |
| IV-02 | The **Calibration** menu is present. | Root menu with five entries. |
| IV-03 | The three groups exist in **Settings → Users & Companies → Groups**. | *Calibration / Viewer*, *Technician*, *Manager*. |
| IV-04 | The four sequences exist in **Settings → Technical → Sequences**. | Prefixes `INS/`, `CP/`, `CAL/`, `CERT/`. |
| IV-05 | The two scheduled actions exist and are active. | Daily interval. |
| IV-06 | The system parameter exists. | `ls_calibration.generation_horizon_days` = `30`. |
| IV-07 | An instrument can be created and receives a reference. | Reference of the form `INS/00001`. |
| IV-08 | The two reports are available from the print menu. | *Calibration Record*, *Calibration Certificate*. |

## 5. Update

```
odoo-bin -d <database> -u ls_calibration --stop-after-init
```

The update preserves every record. The data files are marked `noupdate="1"`,
therefore the sequences, the system parameter and the scheduled actions keep
the values set by the customer. Increase the last segment of the version
string in the manifest before deploying a change, so that platforms that
watch the version trigger the update.

## 6. Uninstallation

Uninstalling deletes the eight models and all their data, including the
approved calibration records and the issued certificates. In a regulated
environment this destroys retained evidence. Export the data first and follow
the change control procedure of the organisation.

## 7. Running the tests

```
odoo-bin -d <test_database> -i ls_calibration --test-enable --test-tags ls_calibration --stop-after-init
```

Run the tests on a disposable database, never on production.

## 8. Troubleshooting

| Symptom | Probable cause | Action |
|---------|----------------|--------|
| The module does not appear in the list | The directory is not in the `addons_path`, or the apps list was not updated | Check the configuration file, restart, update the apps list |
| Installation error mentioning `maintenance` | The Maintenance application is unavailable in the instance | Check that the standard `addons` directory is in the `addons_path` |
| The **Calibration** menu is invisible | The user belongs to none of the three groups | Assign at least the *Viewer* group |
| The reports produce an empty PDF | `wkhtmltopdf` is not installed or is not the version supported by Odoo | Install the version recommended by the Odoo documentation |
| No calibration record is generated | The plan is not active, its due date is beyond the horizon, or an open record already exists | Check the state of the plan, the parameter and the existing records |
