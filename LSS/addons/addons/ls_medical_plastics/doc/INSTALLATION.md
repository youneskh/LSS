# Installation Guide

**Module:** `ls_medical_plastics` · **Target:** Odoo 19.0 Community Edition

---

## 1. Prerequisites

| Requirement | Value |
|---|---|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by the Odoo release |
| Python | The version shipped with the Odoo release |
| Required Odoo modules | `base`, `mail`, `product`, `stock`, `mrp` |
| Additional Python packages | None beyond those Odoo already requires |

The module uses `dateutil.relativedelta`, which is already a dependency of Odoo
itself. No package installation is required.

---

## 2. Installation

1. Copy the `ls_medical_plastics` directory into a directory listed in the
   `addons_path` of your Odoo configuration file.
2. Restart the Odoo service so the new directory is scanned.
3. Enable developer mode: **Settings → General Settings → Developer Tools →
   Activate the developer mode**.
4. Open **Apps** and click **Update Apps List**.
5. Search for *Life Sciences - Medical Plastics* and click **Install**.

Installation creates the five security groups, the four sequences, the default
catalogue of 21 scrap reasons and the two scheduled actions.

---

## 3. Verifying the installation

After installation, confirm each of the following.

| Check | Expected result |
|---|---|
| The **Medical Plastics** menu appears | Visible to users holding at least the Viewer role |
| **Configuration → Scrap Reasons** | 21 reasons present, three of them flagged as start-up scrap |
| **Settings → Technical → Sequences** | `TOOL/`, `TM/`, `MPS/` and `IM/` sequences exist |
| **Settings → Technical → Scheduled Actions** | Two actions named *Medical Plastics: ...* exist and are active |
| **Settings → Users & Companies → Groups** | Five groups named *Medical Plastics / ...* exist |

If the menu does not appear, the current user holds no Medical Plastics role.
Assign one as described in `ADMINISTRATOR_MANUAL.md`.

---

## 4. If installation fails

Installation was never performed by the module authors against a live Odoo 19
instance. The two most likely failure points are known and documented.

### 4.1 An xpath error mentioning `button_box`

The module inherits the manufacturing order form to add a navigation button.
The arch of the Odoo 19 `mrp.production` form could not be verified during
development.

**Remedy:** remove the line `"views/mrp_production_views.xml",` from the `data`
list in `__manifest__.py` and install again. The module loses only that
navigation button.

### 4.2 A field error on `res.groups`, `ir.rule`, `ir.ui.view` or `ir.cron`

The module was deliberately engineered to avoid every field name on these
models whose Odoo 19 spelling could not be verified. If such an error
nevertheless occurs, report the exact field name; the mitigation strategy is
described in `DEVIATIONS_AND_LIMITATIONS.md`, Part B.

### 4.3 A chatter rendering problem

If the message history renders as a raw table rather than as a chatter panel,
see `DEVIATIONS_AND_LIMITATIONS.md` section B1 for the one-line substitution to
apply in each form view.

---

## 5. Upgrading

1. Back up the database and the filestore.
2. Replace the `ls_medical_plastics` directory with the new version.
3. Restart Odoo.
4. Either run `odoo -u ls_medical_plastics -d <database> --stop-after-init`, or
   use **Apps → Life Sciences - Medical Plastics → Upgrade**.

Data files carrying `noupdate="1"` — sequences, scrap reasons and scheduled
actions — are **not** overwritten on upgrade, so local modifications to them
survive.

---

## 6. Uninstallation

Uninstalling removes all module tables and therefore **all moulding runs,
readings, tool records and maintenance history**.

In a regulated environment these are production records subject to a retention
period. Export them before uninstalling, and verify the export against the
retention requirement applicable to the organisation.
