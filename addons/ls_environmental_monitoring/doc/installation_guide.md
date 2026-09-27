# Installation Guide — `ls_environmental_monitoring`

## 1. Prerequisites

| Requirement | Value |
|---|---|
| Odoo | 19.0 Community Edition |
| Python | 3.10 or later |
| Database | PostgreSQL, as required by Odoo |
| Odoo modules | `base` and `mail`, both part of the standard distribution |
| Python packages | `python-dateutil`, already an Odoo dependency |

No module outside the standard Odoo distribution is required.

## 2. Install

```bash
cp -r ls_environmental_monitoring /path/to/odoo/addons/
./odoo-bin -c odoo.conf -d <database> -u ls_environmental_monitoring --stop-after-init
```

Then activate the module from Apps, or install directly:

```bash
./odoo-bin -c odoo.conf -d <database> -i ls_environmental_monitoring --stop-after-init
```

## 3. Post-installation verification

This module has never been installed against a live Odoo 19 instance. The
checks below are therefore **installation qualification steps, not a
confirmation of previously observed behaviour.** Record the outcome of each.

### 3.1 Check the highest-risk item first

The form views use the `<chatter/>` element. Its exact form in Odoo 19 could not
be verified during development.

1. Open **Environmental Monitoring → Configuration → Areas** and open any record.
2. If the form loads, the element is correct.
3. If installation failed with a view parsing error mentioning `chatter`, remove
   the seven `<chatter/>` lines from the files under `views/` and reinstall.
   Field tracking continues to work; only the inline message log is lost.

### 3.2 Check that the security groups were created

1. Enable developer mode.
2. Go to **Settings → Users & Companies → Groups**.
3. Confirm that three groups exist whose names begin
   `Environmental Monitoring /`.
4. They will appear without a category heading. This is expected and explained
   in `doc/deviations.md` section B1.
5. If installation failed with an error about a required field on `res.groups`,
   consult `doc/deviations.md` section B1 for the remedy.

### 3.3 Check the menus

Confirm that the **Environmental Monitoring** application appears with these
sections: Operations, Results, Trending, Programme, Configuration.

### 3.4 Check the sequences

Go to **Settings → Technical → Sequences** and confirm two records exist with
the codes `ls.env.sample` and `ls.env.excursion`.

### 3.5 Check the scheduled jobs

Go to **Settings → Technical → Scheduled Actions** and confirm two records:

- Environmental Monitoring: Generate Scheduled Samples
- Environmental Monitoring: Notify Overdue Samples

Both are created active and run daily. Deactivate the generation job if you
intend to generate samples manually only.

### 3.6 Run the supplied test suite

```bash
./odoo-bin -c odoo.conf -d <test_database> \
    -i ls_environmental_monitoring \
    --test-enable --test-tags /ls_environmental_monitoring \
    --stop-after-init
```

104 database-backed tests have been written and **have never been executed**.
Expect to spend time on failures caused by the unverified Odoo 19 API points
listed in `doc/deviations.md` section B. Record actual pass and fail counts;
do not carry forward any figure from `doc/test_report.md`, which reports only
the 38 pure-logic tests that were executed during development.

### 3.7 Run the static checker

```bash
python3 ls_environmental_monitoring/static_check.py
```

Expect `RESULT: PASS (no errors)`.

## 4. Upgrading

This is the first release, so there is no upgrade path to test. Future upgrades
should be rehearsed on a copy of production before being applied.

## 5. Uninstalling

Uninstalling removes all environmental monitoring records, including samples,
results and excursions. In a regulated environment these are retained records.
**Export or archive the data before uninstalling, and follow your change control
procedure.**
