# Run with:  odoo shell -c /etc/odoo/odoo.conf -d <database with the ls_* modules and demo data>  < render_reports.py
# Renders every QWeb report declared by an ls_* module to HTML for up to three
# records of its model. Read only: the transaction is rolled back at the end.
import traceback

reports = env["ir.actions.report"].search([("report_type", "like", "qweb")])  # noqa: F821
data = env["ir.model.data"]  # noqa: F821
checked = failed = without_records = 0
for report in reports:
    xmlid = data.search([("model", "=", "ir.actions.report"), ("res_id", "=", report.id)], limit=1)
    if not xmlid or not xmlid.module.startswith("ls_"):
        continue
    records = env[report.model].search([], limit=3)  # noqa: F821
    if not records:
        without_records += 1
        print(f"RENDER {xmlid.module}.{xmlid.name}: no record of {report.model} to render")
        continue
    checked += 1
    try:
        report._render_qweb_html(report.report_name, records.ids)
        print(f"RENDER {xmlid.module}.{xmlid.name}: OK ({len(records)} record(s))")
    except Exception as error:  # noqa: BLE001
        failed += 1
        print(f"RENDER {xmlid.module}.{xmlid.name}: FAIL {type(error).__name__}: {str(error).splitlines()[0][:200]}")
        traceback.print_exc()
print(f"RENDER summary: rendered={checked}, failed={failed}, no records={without_records}")
env.cr.rollback()  # noqa: F821
