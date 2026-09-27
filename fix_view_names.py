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
            
            # Fix view record IDs and names from .tree to .list
            content = re.sub(r'id="view_([^"]*_)?tree"', lambda m: f'id="view_{m.group(1) if m.group(1) else ""}list"', content)
            content = re.sub(r'<field name="name">([^<]*\.tree)</field>', lambda m: f'<field name="name">{m.group(1)[:-5]}.list</field>', content)
            
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(filepath)
                print("Fixed: " + filepath)
        except Exception as e:
            pass

print("\nTotal files fixed: " + str(len(fixed_files)))
