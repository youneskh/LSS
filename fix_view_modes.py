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
            
            # Fix view_mode with tree
            content = re.sub(r'<field name="view_mode">tree,', '<field name="view_mode">list,', content)
            content = re.sub(r'<field name="view_mode">([^<]*),tree(,|<)', r'<field name="view_mode">\1,list\2', content)
            content = re.sub(r'<field name="view_mode">tree</field>', '<field name="view_mode">list</field>', content)
            
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(filepath)
                print("Fixed: " + filepath)
        except Exception as e:
            pass

print("\nTotal files fixed: " + str(len(fixed_files)))
