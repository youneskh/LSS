# Installation Guide

Module: `ls_supplier_qualification` · Odoo 19 Community Edition

---

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Odoo | 19.0 Community Edition |
| Database | PostgreSQL, as required by the Odoo version in use |
| Python | The interpreter shipped with your Odoo installation |
| Odoo modules | `base`, `mail`, `product`, `purchase` — all Community, all installed automatically as dependencies |
| External Python packages | None. The module imports only `hashlib`, `json` and `dateutil`, all already required by Odoo |
| Optional | `purchase_stock`, only if you want the automatic delivery counters |

The module is licensed AGPL-3. It contains no Enterprise code and no
proprietary dependency.

## 2. Install the files

Place the `ls_supplier_qualification` directory inside a path listed in
`addons_path`:

```bash
cp -r ls_supplier_qualification /opt/odoo/custom-addons/
chown -R odoo:odoo /opt/odoo/custom-addons/ls_supplier_qualification
```

Confirm the path is declared in your configuration file:

```ini
[options]
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
```

## 3. Install the module

**From the interface.** Restart the Odoo service, go to **Apps**, click
**Update Apps List**, search for *Supplier Qualification* and press **Activate**.
Remove the default *Apps* filter if the module does not appear: it is declared
`application: False`, so it is listed under modules rather than apps.

**From the command line.**

```bash
odoo-bin -d <database> -i ls_supplier_qualification --stop-after-init
```

**With demonstration data**, on a scratch database only:

```bash
odoo-bin -d <scratch_database> -i ls_supplier_qualification --without-demo=False
```

## 4. Verify the installation

Run these checks before declaring the installation successful. They are the
same checks the automated installation test performs.

| # | Check | Expected result |
|---|-------|-----------------|
| 1 | The **Supplier Qualification** menu appears. | Four sections: Qualification, Evaluation, Monitoring, Configuration. |
| 2 | **Configuration → Supplier Categories** | 10 starter categories. |
| 3 | **Configuration → Assessment Criteria** | 32 starter criteria, grouped by domain. |
| 4 | **Configuration → Assessment Templates** | 2 templates; the full one carries 32 criteria, the short one 12. |
| 5 | **Configuration → Reference Standards** | 13 framework designations. |
| 6 | **Settings → Technical → Scheduled Actions**, filter on "Supplier Qualification" | 3 active daily actions. |
| 7 | **Settings → Technical → Sequences**, filter on "Supplier" | 5 sequences: SQ, SA, SAU, SP, SR. |
| 8 | **Settings → Users & Companies → Groups** | Supplier Viewer, Supplier Assessor, Supplier Manager. |
| 9 | **Settings → Supplier Qualification** | The settings block renders with governance, purchase control and scorecard sections. |

## 5. Post-installation verification points

Three items could not be verified in the environment where this module was
built. Check them once, on a scratch database, before using the module in
production. The reasoning is in `doc/05_architecture_review.md`, §5.8.

**V-01 — Record rules load.**
If the module installs without error, this is satisfied: a rename of the
`ir.rule` groups field in Odoo 19 would surface as a load failure on
`security/ls_supplier_qualification_security.xml`. Should that happen, edit
that file and rename the `groups` field in the four ownership rules
(`ls_supplier_assessment_rule_assessor`, `ls_supplier_assessment_rule_manager`,
`ls_supplier_audit_rule_auditor`, `ls_supplier_audit_rule_manager`). The
thirteen multi-company rules do not use that field and are unaffected.

**V-02 — Group assignment.**
Open a user, add the Supplier Manager group, save. The module ships no data
record that writes user groups, so no failure is expected here.

**V-03 — Automatic delivery counters.**
Only relevant if `purchase_stock` is installed. Create a draft performance
evaluation and press **Recompute Delivery Counters**. Either the counters fill,
or a message names `purchase_stock` as missing. Both outcomes are correct
behaviour; an unhandled traceback is not.

## 6. Run the test suite

```bash
odoo-bin -d <test_database> \
    -i ls_supplier_qualification \
    --test-enable \
    --test-tags /ls_supplier_qualification \
    --stop-after-init \
    --log-level=test
```

The suite contains 13 test modules, all tagged `post_install`. Expect no
failure and no error. See `doc/12_test_report.md` for what is covered and for
the honest statement of what was and was not executed before delivery.

## 7. Upgrade

```bash
odoo-bin -d <database> -u ls_supplier_qualification --stop-after-init
```

Configuration data (categories, criteria, templates, standards), security
rules, sequences, mail templates and scheduled actions carry `noupdate="1"`, so
an upgrade does not overwrite anything an organisation has changed. Views are
refreshed by an upgrade, which is how layout corrections are delivered.

Take a database backup before upgrading a production system.

## 8. Uninstall

Uninstalling removes every model of the module and all data stored in them,
including the signature log. In a regulated environment this is a records
destruction event. Export what you need first:

1. Print the dossier report for every dossier you must retain.
2. Export the signature log to XLSX from the list view.
3. Take a full database backup.

Then remove the module from **Apps**.

## 9. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| The module does not appear in Apps. | Apps list not refreshed, or `addons_path` wrong. | Update Apps List; check the path; check file ownership. |
| Load error on the security XML. | Verification point V-01. | See §5 above. |
| The menu is invisible after installation. | No group assigned. | Add the user to Supplier Viewer or above. |
| A user sees no dossier although records exist. | Multi-company rule, or the dossiers belong to another company. | Check the user's allowed companies. |
| **Recompute Delivery Counters** raises an error naming `purchase_stock`. | Expected behaviour when the bridge module is absent. | Install `purchase_stock` or enter the counters manually. |
| Purchase orders are refused at confirmation. | Control level set to *Block* and the supplier is not approved. | Approve the supplier, or lower the level to *Warn* in the settings. |
| Scheduled actions do not run. | Cron disabled at server level. | Check that the Odoo cron worker is running. |
