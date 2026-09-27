# Installation Guide

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by the Odoo version in use |
| Python | The interpreter shipped with your Odoo installation |
| Odoo modules | `base` and `mail`, both part of Odoo Community |
| External Python packages | None beyond those Odoo already requires. `python-dateutil` is used and is already an Odoo dependency. |

This module requires no other module of the Life Sciences Suite. It installs
and runs on a plain Odoo 19 Community database.

## 2. Install

1. Copy the `ls_risk_management` directory into a directory on your
   `addons_path`.
2. Restart the Odoo service so the new module is discovered.
3. Enable developer mode, then open **Apps** and click **Update Apps List**.
4. Search for *Life Sciences - Risk Management* and click **Install**.

Command line equivalent:

```
odoo-bin -d YOUR_DATABASE -i ls_risk_management --stop-after-init
```

To install with demonstration data on a test database:

```
odoo-bin -d YOUR_TEST_DATABASE -i ls_risk_management --without-demo=False \
         --stop-after-init
```

Never load demonstration data on a production or validated database. The
demonstration matrix ships pre-approved so the sample workflow can run; its
acceptability criteria are not suitable for regulated use.

## 3. What installation creates

| Item | Count | Notes |
|---|---|---|
| Models | 17 | 9 persistent, 1 abstract, 6 transient wizards, plus the FMEA line model |
| Access control lines | 35 | Every model is covered |
| Record rules | 9 | All global, multi-company scoped |
| Security groups | 3 | Risk Viewer, Risk Analyst, Risk Manager |
| Sequences | 4 | `RISK/`, `RA/`, `RCM/`, `FMEA/` |
| Scheduled actions | 1 | Daily overdue review notification |
| Risk categories | 10 | Starter taxonomy, editable |
| Risk matrices | 1 | An **unapproved** 5x5 example |
| PDF reports | 2 | Risk record, FMEA worksheet |

## 4. Post-installation check

1. Confirm the menu **Risk Management** appears for a user in the Risk Viewer
   group or above.
2. Open **Risk Management → Configuration → Risk Matrices**. The shipped
   example matrix must be present, in the **Draft** state, and **not** flagged
   as default. If it is approved or default, the installation did not load the
   shipped data as intended; investigate before proceeding.
3. Confirm **Settings → Technical → Automation → Scheduled Actions** contains
   *Life Sciences Risk: notify overdue risk reviews*.

You cannot create an assessable risk until a matrix is approved. This is
deliberate. Continue with `CONFIGURATION.md`.

## 5. Upgrade

```
odoo-bin -d YOUR_DATABASE -u ls_risk_management --stop-after-init
```

Shipped configuration data is marked `noupdate="1"`, so local edits to the
example matrix and the starter taxonomy survive an upgrade.

## 6. Uninstall

Uninstalling **deletes all risk records, assessments, control measures and
FMEA worksheets** created by this module. In a regulated environment, export
the data and record the action under change control first.

## 7. Running the tests

```
odoo-bin -d YOUR_TEST_DATABASE -i ls_risk_management \
         --test-enable --test-tags /ls_risk_management --stop-after-init
```

The test suite has never been executed; see `TEST_REPORT.md`.
