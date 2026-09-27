# ls_capa — Installation Guide

**Module:** `ls_capa` 19.0.1.0.0
**Target:** Odoo 19.0 Community Edition

---

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 Community Edition |
| Python | 3.12 (the version Odoo 19 targets) |
| PostgreSQL | Version supported by your Odoo 19 build |
| Odoo modules | `base`, `mail`, `project` — all shipped with Community |
| External Python packages | None |
| Enterprise modules | None. This module uses no Enterprise code. |

`project` is a standard Community application. If it is not yet
installed, Odoo installs it automatically as a dependency.

## 2. Obtain the module

Place the `ls_capa` directory inside a directory listed in your
`addons_path`. A conventional layout:

```
/opt/odoo/
├── odoo/                 # Odoo 19.0 source
└── custom-addons/
    └── ls_capa/          # this module
```

From the archive:

```bash
tar -xzf ls_capa-19.0.1.0.0.tar.gz -C /opt/odoo/custom-addons/
```

## 3. Configure the addons path

In `odoo.conf`:

```ini
[options]
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
```

Restart the Odoo service after editing the file.

## 4. Install

### Command line (recommended for a controlled environment)

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_capa --stop-after-init
```

To include the demonstration data set:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_capa \
    --without-demo=False --stop-after-init
```

### User interface

1. Log in as an administrator.
2. Activate developer mode (*Settings > General Settings > Developer
   Tools*).
3. Go to *Apps* and click **Update Apps List**.
4. Remove the default *Apps* filter, search for `ls_capa`, and click
   **Install**.

## 5. Post-installation verification

Confirm each of the following before declaring the installation
successful.

| # | Check | Expected result |
|---|---|---|
| 1 | Server log during install | No `ERROR` or `WARNING` lines mentioning `ls_capa` |
| 2 | Menu *Quality > CAPA* | Present for a user in a CAPA group |
| 3 | *Settings > Users & Companies > Groups* | Four groups under privilege **CAPA Management** |
| 4 | *Settings > Technical > Sequences* | Four sequences: `ls.capa.issue`, `ls.capa.root_cause`, `ls.capa.action`, `ls.capa.effectiveness` |
| 5 | *Quality > Configuration > CAPA Categories* | Five categories preloaded |
| 6 | *Settings > Technical > Scheduled Actions* | *CAPA: Notify Overdue Records* present and **inactive** |
| 7 | Create a test CAPA | Reference allocated as `CAPA/<year>/00001` |
| 8 | Print a CAPA | PDF report renders |

## 6. Run the test suite

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <test-database> \
    -i ls_capa --test-enable --stop-after-init --log-level=test
```

Use a disposable database. Never enable tests against production.

## 7. Upgrade an existing installation

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -u ls_capa --stop-after-init
```

Data files carrying `noupdate="1"` (sequences, scheduled action, default
categories, record rules) are **not** overwritten, so local edits to
those records survive the upgrade. Security group definitions are
updatable so that changes to the implication chain propagate.

Take a database backup before any upgrade.

## 8. Uninstallation

Uninstalling removes all CAPA records, root cause analyses, actions and
effectiveness checks permanently. In a regulated environment this
destroys GxP records. Export the data first, and obtain quality approval
before uninstalling.

## 9. Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| Module not listed in Apps | Addons path wrong, or list not refreshed | Check `addons_path`, restart, click *Update Apps List* |
| `Invalid field 'privilege_id' on res.groups` | Target is Odoo 18 or earlier | This module requires Odoo 19.0 |
| Kanban view renders empty | Target is Odoo 18 or earlier | The `<t t-name="card">` template requires Odoo 19 |
| `project.task` errors on *Create Task* | `project` not installed | Install the Project application |
| Menu absent for a user | User has no CAPA group | Assign a group under *Users > Access Rights* |
