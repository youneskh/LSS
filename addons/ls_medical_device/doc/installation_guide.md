# Installation Guide — `ls_medical_device`

## 1. Prerequisites

| Component | Requirement |
|---|---|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by the Odoo release in use |
| Python | The interpreter version shipped with the Odoo release |
| Python package | `python-dateutil` (used for month and year arithmetic) |

Odoo module dependencies, all part of the Community Edition: `base`, `mail`,
`product`, `stock`.

The module declares no dependency on any other Life Sciences Suite module.
This is deliberate: declaring a dependency on a module that is not present in
the addons path prevents installation. Integration points are provided instead
and are described in `developer_manual.md`.

## 2. Deployment

Copy the module into an addons directory declared in the Odoo configuration:

```bash
cp -r ls_medical_device /path/to/odoo/addons/
```

Update the module list and install:

```bash
odoo -d <database> -u base --stop-after-init
odoo -d <database> -i ls_medical_device --stop-after-init
```

To upgrade an existing installation:

```bash
odoo -d <database> -u ls_medical_device --stop-after-init
```

## 3. What installation creates

| Artefact | Count | Source |
|---|---|---|
| Models | 17 | `models/`, `wizards/` |
| Security groups | 4 | `security/ls_medical_device_groups.xml` |
| Access rules | 45 | `security/ir.model.access.csv` |
| Record rules | 12 | `security/ls_medical_device_rules.xml` |
| Number sequences | 9 | `data/ir_sequence_data.xml` |
| Risk classes | 7 | `data/device_class_data.xml` |
| Clinical evidence sources | 5 | `data/clinical_evidence_source_data.xml` |
| Documentation section templates | see file | `data/technical_file_section_template_data.xml` |
| Scheduled actions | 2 | `hooks.py` (post-installation hook) |
| Report actions | 3 | `report/report_actions.xml` |

### Why the scheduled actions are created in Python

The exact field set of `ir.cron` in Odoo 19.0 could not be verified from
official documentation during preparation of this module. An XML record that
writes a field which no longer exists aborts the installation. The
post-installation hook in `hooks.py` filters the value dictionary against the
fields the running registry actually declares, so the module installs on any
field set that still provides the core scheduling attributes.

Each scheduled action is created with an external identifier, so an upgrade
updates the existing record rather than creating a duplicate.

## 4. Verifying the installation

After installation, confirm:

1. The **Medical Devices** application appears in the main menu.
2. Settings → Technical → Scheduled Actions contains:
   - *Medical Devices: Check Post-Market Obligations*
   - *Medical Devices: Expire Certificates Past Their Expiry Date*
3. Configuration → Risk Classes lists seven classes: I, Is, Im, Ir, IIa, IIb, III.
4. Settings → Users shows the four Medical Devices access levels.

The test module `tests/test_install.py` asserts each of these. Running it is
the recommended verification step:

```bash
odoo -d <database> --test-enable --test-tags /ls_medical_device --stop-after-init
```

## 5. Demo data

Demo data installs only when the database was created with demonstration data
enabled. Every demo record is fictitious. The demo notified body uses the
identification number `DEMO-0000`, deliberately outside the format used for
real designations, so that a demonstration record cannot be mistaken for a
designated body.

**Do not install demo data on a production database.**

## 6. Uninstallation

Uninstalling removes the models and their data. In a regulated environment,
export the records first: the retention obligations of MDR Article 10(8) apply
to the technical documentation regardless of the system holding it.
