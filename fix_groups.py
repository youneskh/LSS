import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
fixed_files = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            # Replace both attribute orderings
            content = re.sub(
                r'<group\s+expand="0"\s+string="Group By">',
                '<group name="group_by">',
                content
            )
            content = re.sub(
                r'<group\s+string="Group By"\s+expand="0">',
                '<group name="group_by">',
                content
            )
            
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(filepath)
        except Exception as e:
            print(f"Error: {filepath} - {e}")

for f in sorted(fixed_files):
    print(f"Fixed: {f}")
print(f"\nTotal files fixed: {len(fixed_files)}")
