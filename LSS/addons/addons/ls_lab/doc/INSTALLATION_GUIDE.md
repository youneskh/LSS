# INSTALLATION GUIDE — `ls_lab`

## 1. Prerequisites

| Requirement | Value |
|-------------|-------|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by Odoo 19 |
| Python | The interpreter version Odoo 19 requires |
| Module dependencies | `base`, `mail`, `product`, `stock`, `uom` — all present in Community |

No external Python package beyond Odoo's own runtime is required.
`dateutil.relativedelta` is used and is part of Odoo's declared dependencies.

**No Life Sciences Suite module is a dependency.** `ls_lab` installs standalone.

## 2. Verify before installing

Run the offline static checker first. It validates view archs against the real
Odoo 19 RNG schemas shipped in `tools/rng/`, which is the check that catches
install-time schema violations.

```bash
python3 ls_lab/tools/static_check.py ls_lab
```

Expected output ends with `RESULT: 0 finding(s)`. Do not install if it does not.

Optionally re-validate the checker itself:

```bash
python3 ls_lab/tools/negative_control.py ls_lab
```

Expected: `25/25 seeded faults detected`.

## 3. Deploy

### Standard deployment

```bash
cp -r ls_lab /path/to/addons/
```

### Docker deployment

```bash
docker cp ls_lab <container>:/mnt/extra-addons/
```

Confirm the target directory is on `addons_path` in `odoo.conf`.

## 4. Install

Command line:

```bash
odoo -d <database> -i ls_lab --stop-after-init
```

Docker:

```bash
docker exec <container> odoo -d <database> -i ls_lab --stop-after-init
```

User interface: Apps → Update Apps List → search "Laboratory" → Install.

## 5. Verify the installation

| Check | Expected |
|-------|----------|
| Menu | A **Laboratory** root menu appears. |
| Groups | Settings → Users → Groups shows four Laboratory groups under the Laboratory privilege. |
| Sequences | Six sequences with codes `ls.lab.*` exist. |
| Scheduled actions | Three crons named "Laboratory: ..." exist. |
| Reports | Two QWeb PDF report actions exist. |
| Data | **No** storage conditions, methods or specifications exist. This is correct. |

## 6. Run the test suite

The suite is written but was **not executed** during the build. Execute it on a
scratch database and record the outcome in `TEST_REPORT.md`.

```bash
odoo -d <scratch_db> -i ls_lab --test-enable --test-tags /ls_lab --stop-after-init --log-level=test
```

## 7. Upgrade

```bash
odoo -d <database> -u ls_lab --stop-after-init
```

Sequences and scheduled actions are declared `noupdate="1"`, so customer
configuration of those records survives an upgrade.

## 8. Uninstall

Uninstalling removes all laboratory records, including approved specifications,
results, investigations and certificates. In a regulated environment this
destroys records that may be subject to retention requirements. **Export or
archive the data first**, and follow your change control procedure.

## 9. Troubleshooting

| Symptom | Cause | Action |
|---------|-------|--------|
| `Module quality not found` | A sibling module declares `quality`, which is absent from Community. | Run `tools/retrofit_scan.py` on the addons directory. |
| View validation error on install | A search view carries a disallowed `<group>` attribute. | Run `tools/retrofit_scan.py --fix-preview`. |
| `Invalid field groups_id` | Odoo 19 renamed the field to `group_ids`. | Run `tools/retrofit_scan.py`. |
| Users see no menu | The user is in no Laboratory group. | Assign a group; the root menu requires at least Viewer. |
| Sample cannot be registered | No approved specification exists for the product. | Create and approve a specification first. |
