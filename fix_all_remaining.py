import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
fixed_count = 0

# Scan all XML files for remaining <group expand="0" string="Group By"> patterns
for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            
            # Replace all variations of the deprecated pattern
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
                print("Fixed: " + filepath)
                fixed_count += 1
        except Exception as e:
            pass

print("\nTotal files fixed: " + str(fixed_count))
