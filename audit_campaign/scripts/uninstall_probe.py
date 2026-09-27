# Module name comes from the AUDIT_MOD environment variable.
import os
# Run with:  odoo shell -c /etc/odoo/odoo.conf -d <scratch db>
import traceback

MOD = os.environ["AUDIT_MOD"]

try:
    module = env["ir.module.module"].search([("name", "=", MOD)])  # noqa: F821
    if module.state != "installed":
        print(f"UNINSTALL {MOD}: SKIPPED (state={module.state})")
    else:
        cr = env.cr  # noqa: F821
        module.button_immediate_uninstall()
        cr.commit()
        cr.execute("SELECT state FROM ir_module_module WHERE name = %s", (MOD,))
        state = cr.fetchone()[0]
        print(f"UNINSTALL {MOD}: {'OK' if state == 'uninstalled' else 'STATE=' + state}")
except Exception as error:  # noqa: BLE001
    print(f"UNINSTALL {MOD}: FAILED {type(error).__name__}: {str(error).splitlines()[0][:300]}")
    traceback.print_exc()
