# Installation Guide

Module: `ls_recall` — Odoo 19 Community Edition

---

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Odoo | 19.0 Community Edition |
| Python | 3.12 or later (Odoo 19 minimum) |
| PostgreSQL | As required by Odoo 19 |
| Odoo modules | `mail` and `stock` must be installable; both ship with Community |
| Python packages | None beyond Odoo's own requirements |

`wkhtmltopdf` is needed only to print the two PDF documents, and is an
Odoo prerequisite rather than one of this module's.

## 2. Installation

1. Place the `ls_recall` directory in a path listed in `addons_path`.

2. Confirm the directory is readable by the Odoo system user and that
   `__manifest__.py` is present at its root.

3. Update the module list:

   ```
   odoo-bin -d <database> -u base --stop-after-init
   ```

   Or, in the interface, enable developer mode and use
   **Apps → Update Apps List**.

4. Install:

   ```
   odoo-bin -d <database> -i ls_recall --stop-after-init
   ```

   Or search for "Recall" in **Apps** and press Install.

5. Confirm the result. The **Recalls** menu appears for users in a
   recall group. A user who is in no recall group will not see it; this
   is expected.

## 3. Installing with demonstration data

Demonstration data is loaded only on a database created with demo data
enabled. It creates its own partners, one product, one lot, one recall
plan and one field action left in the Planned state.

The demonstration recall is deliberately **not** advanced through the
workflow. Advancing it would create communications and effectiveness
checks that were never issued or performed — exactly the kind of record
a regulated organisation must not carry.

## 4. Running the tests

```
odoo-bin -d <test-database> -i ls_recall --test-enable \
         --test-tags /ls_recall --stop-after-init --log-level=test
```

The tests are tagged `post_install`, so use `--test-tags /ls_recall`
rather than `at_install`.

**Read `12_test_plan_and_report.md` before relying on a test result.**
The suite has never been executed: the environment in which this module
was produced had no Odoo runtime. Treat the first execution as part of
your own qualification, and run `tests/test_traceability.py` first, as
it is the file most tightly coupled to `stock` internals.

## 5. Upgrading

```
odoo-bin -d <database> -u ls_recall --stop-after-init
```

Sequences and scheduled actions are declared `noupdate="1"`, so an
upgrade will not reset a sequence counter that has already allocated
references, and will not revert a cron interval an administrator has
changed.

## 6. Uninstalling

Uninstalling removes all recall data: plans, field actions, consignee
lines, communications, effectiveness checks and reports. In a regulated
environment this is a records-destruction event. Export or archive the
data first, and record the decision under change control.

The delete guards in the module (`@api.ondelete(at_uninstall=False)`)
are explicitly disabled during uninstall, by design — otherwise the
module could never be removed.

## 7. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Module not listed | Path not in `addons_path`, or app list not updated | Check the configuration file; update the apps list |
| Install fails on `res.groups.privilege` | Running against Odoo 18 or earlier, where the model does not exist | This module targets 19.0 only |
| Install fails on `is_storable` in the demo file | The product field convention differs on your build | Install without demo data, or adjust `demo/ls_recall_demo.xml`; see `14_verification_register.md` item 4 |
| Menu invisible | User holds no recall group | Assign a role under Settings → Users |
| Lot form shows no ribbon | The lot is not named in a real, open field action | Expected; rehearsals do not raise the ribbon |
