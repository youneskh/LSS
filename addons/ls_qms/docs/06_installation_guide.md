# 06 — Installation Guide

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, version supported by the Odoo release in use |
| Python | The interpreter shipped with the Odoo release in use |
| Modules | `base`, `mail` and `hr` installable in the target database |

This module uses syntax introduced in Odoo 19, namely `models.Constraint`,
the `<list>` view element, the `<chatter/>` element and `res.groups.privilege`.
**It will not install on Odoo 18 or earlier.**

## 2. Placing the module

Copy the `ls_qms` directory into a directory listed in `addons_path`, then
update the module list:

```bash
odoo-bin -d <database> -u base --stop-after-init
```

## 3. Installing

```bash
odoo-bin -d <database> -i ls_qms --stop-after-init
```

With demonstration data, on a database created with `--without-demo=False`,
the file `demo/ls_qms_demo.xml` is loaded automatically.

## 4. Running the tests

```bash
odoo-bin -d <database> -i ls_qms --test-enable --stop-after-init
```

The suite is described in `12_test_report.md`. **It has not been executed by
the author of the module.** Executing it is part of the acceptance of the
delivery.

## 5. Post-installation verification

Perform these seven checks. `tests/test_installation.py` performs the same
checks programmatically.

| # | Check | Expected result |
|---|---|---|
| 1 | The menu **Quality Management** is present | Eight entries, of which Configuration is visible to an administrator only |
| 2 | Settings, Users and Companies, Groups | The privilege **Quality Management** carries four groups |
| 3 | Settings, Technical, Sequences | Six sequences whose codes start with `ls.qms.` |
| 4 | Settings, Technical, System Parameters | Four parameters whose keys start with `ls_qms.` |
| 5 | Settings, Technical, Scheduled Actions | Three active actions whose names start with `Life Sciences QMS` |
| 6 | Settings, Technical, Activity Types | Three types whose names start with `QMS` |
| 7 | Print a policy | The PDF carries the control block and the uncontrolled copy notice |

## 6. Uninstalling

Uninstalling removes every record of the eight models of the module,
including quality records. In a regulated environment, export the data before
uninstalling and record the operation under change control.
