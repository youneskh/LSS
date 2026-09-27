# Run with:  odoo shell -c /etc/odoo/odoo.conf -d <database with the ls_* modules>  < compile_reports.py
# Compiles (without rendering) every QWeb template of the ls_* modules, which
# catches the compile-time errors of Odoo 19 QWeb (for example t-field on a
# table cell) even when no record exists to render a report. Read only.
views = env["ir.ui.view"].search([("type", "=", "qweb")])  # noqa: F821
data = env["ir.model.data"]  # noqa: F821
checked = failed = 0
for view in views:
    xmlid = data.search([("model", "=", "ir.ui.view"), ("res_id", "=", view.id)], limit=1)
    if not xmlid or not xmlid.module.startswith("ls_"):
        continue
    checked += 1
    try:
        env["ir.qweb"]._generate_code(view.id)  # noqa: F821
    except Exception as error:  # noqa: BLE001
        failed += 1
        print(f"COMPILE {xmlid.module}.{xmlid.name}: FAIL {type(error).__name__}: {str(error).splitlines()[0][:200]}")
print(f"COMPILE summary: templates={checked}, failed={failed}")
env.cr.rollback()  # noqa: F821
