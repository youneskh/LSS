# Installation Guide

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 **Community** Edition |
| Database | PostgreSQL, as required by the Odoo release in use |
| Python | The interpreter shipped with or required by that Odoo release |
| Odoo modules | `base`, `mail`, `product`, `stock` — all Community, all installed automatically as dependencies |
| Extra Python packages | None |
| Enterprise modules | None, and none may be required |

## 2. Before you install

Read `docs/00_verification_and_limitations.md`. This module was never installed
or executed by its author. Install it first on a scratch database, never
directly on a production or validated instance.

## 3. Deployment

```bash
# 1. Place the module in an addons path
cp -r ls_complaint /opt/odoo/custom-addons/

# 2. Confirm the addons path is declared
grep addons_path /etc/odoo/odoo.conf

# 3. Restart the service and update the apps list
sudo systemctl restart odoo
```

Then, in the web client: activate the developer mode, open *Apps*, click
*Update Apps List*, search for `Complaint Management` and install it.

Command line alternative:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_complaint --stop-after-init
```

To install with the demonstration records:

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> -i ls_complaint \
         --without-demo=False --stop-after-init
```

## 4. Post-installation verification

| # | Check | Expected |
|---|---|---|
| 1 | The `Complaints` root menu is visible | Present for any user in a complaint group |
| 2 | Settings → Users → a user shows the *Life Sciences Complaint Management* section | Four selectable levels |
| 3 | Settings → Technical → Sequences | `Complaint`, `Complaint Investigation`, `Complaint Adverse Event` present |
| 4 | Settings → Technical → Scheduled Actions | Two actions, both active, daily |
| 5 | Settings → Technical → Email Templates | Two templates on model `ls.complaint` |
| 6 | Create a complaint | A reference `CMP/<year>/00001` is assigned |
| 7 | Print the complaint | A PDF titled `Complaint - CMP/<year>/00001` is produced |

Record these seven checks as the Installation Qualification evidence.

## 5. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| Loading fails on a view with an unknown tag or attribute | Version-sensitive view API | Consult the risk register R-01, R-02, R-15 in `docs/00_verification_and_limitations.md` and apply the stated fallback |
| Loading fails on `_sql_constraints` | Declarative constraint API changed | Risk register R-03 |
| Loading fails on the scheduled actions | A required `ir.cron` field has no default | Risk register R-06 |
| `_read_group` raises on the category form | Signature changed | Risk register R-04 |
| The report does not render | wkhtmltopdf is absent or misconfigured | Odoo infrastructure matter, independent of this module |
| A user sees the menu but no record | Multi-company rule, or the ownership record rule | See `docs/administrator_manual.md` section 4 |

## 6. Uninstallation

Uninstalling removes every complaint, investigation, adverse event, resolution
and category created by the module. In a regulated environment this destroys
quality records. Export first, and record the decision.

```bash
odoo-bin -c /etc/odoo/odoo.conf -d <database> --uninstall ls_complaint \
         --stop-after-init
```
