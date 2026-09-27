# 08 — Installation and Configuration Guide

## 8.1 Prerequisites

- Odoo 19.0 Community Edition
- PostgreSQL
- Modules installed: `base`, `mail`, `hr`, `stock`, `mrp`, `maintenance`

## 8.2 Installation

1. Place `ls_deviation` in the addons path.
2. Restart the Odoo service.
3. Enable developer mode, update the apps list.
4. Search for "Deviation Management" and install.

**Install first into a scratch database, not a validated environment.** This
module has never been executed against a running Odoo instance; see
`00_VERIFICATION_STATUS.md`.

Command line:

```bash
odoo -d <database> -i ls_deviation --stop-after-init
```

With demo data (safe — demo records reference no external master data):

```bash
odoo -d <database> -i ls_deviation --without-demo=False --stop-after-init
```

## 8.3 Post-installation: assign roles

**No user is assigned to any deviation group by installation.** Immediately
after installing, at least one user must be granted Deviation Manager or the
application will be inaccessible.

Settings → Users & Companies → Users → select the user → Quality Management →
Deviation Management → choose one of Viewer, Reporter, Investigator, Manager.

This is deliberate. In a regulated environment, granting system access is an
authorisation activity that must be evidenced per user against a role
description. Automatic assignment at install would create access nobody
approved.

Suggested mapping:

| Site role | Group |
|---|---|
| Operators, warehouse staff | Reporter |
| Line supervisors, QA officers | Investigator |
| QA management, Qualified Person | Manager |
| Regulatory Affairs, auditors, read-only observers | Viewer |

## 8.4 Configuration

**Closure targets.** Settings → Deviation Management. Set the target closure
interval in days for Minor, Major and Critical. Each defaults to 30 days. When
a severity is first chosen on a deviation, the target closure date is proposed
as detection date plus the configured interval. Thereafter it can only be
changed through the justified extension wizard.

**Master data.** Quality Management → Configuration provides Deviation Types
(8 supplied), Deviation Categories (8 supplied), Root Cause Analysis Methods
(5 supplied) and Tags. All supplied records are `noupdate="1"`, so local edits
survive module upgrade. Set *Requires Disposition* on a type where a
disposition is always needed regardless of the impact assessment.

**Scheduled action.** Settings → Technical → Scheduled Actions → "Deviation:
notify overdue records". Runs daily. Adjust interval or deactivate as the site
procedure requires. Outgoing mail must be configured for notifications to be
delivered; the action still subscribes followers if mail is not configured.

**Sequence.** Settings → Technical → Sequences → "GxP Deviation". Default
format `DEV/<year>/00001`. Change the prefix or padding before recording the
first deviation; changing it afterwards creates a discontinuity that must
itself be documented.

## 8.5 Multi-company

Every transactional model carries a global record rule restricting visibility
to the user's allowed companies. Types and categories may be left without a
company to share them across all companies, or assigned to one company for
company-specific master data.

## 8.6 Upgrade

```bash
odoo -d <database> -u ls_deviation --stop-after-init
```

Master data and the sequence carry `noupdate="1"` and are not overwritten.
Perform the upgrade on a restored copy of production before applying it to
production.

## 8.7 Uninstall

Uninstalling removes all deviation records and their transition logs. In a
regulated environment this destroys GxP records. Export first, and treat the
uninstall as a change-controlled activity.
