import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"

files_to_fix = [
    r"D:\Docker\odoo19Claude_ls-docker\addons\ls_audit\views\ls_audit_finding_views.xml",
    r"D:\Docker\odoo19Claude_ls-docker\addons\ls_deviation\views\ls_deviation_views.xml"
]

for filepath in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove days_open measure from pivot views
    content = re.sub(
        r'<field name="days_open" type="measure"[^>]*/>',
        '',
        content
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")
