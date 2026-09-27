import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
files_with_pattern = []

# Scan for remaining <group expand="0" string="Group By"> patterns
for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            if 'expand="0"' in content and 'Group By' in content:
                files_with_pattern.append(filepath)
        except:
            pass

if files_with_pattern:
    print("Files still containing the deprecated pattern:")
    for f in files_with_pattern:
        print(f"  {f}")
else:
    print("No files with deprecated <group expand=\"0\" string=\"Group By\"> pattern found!")
    
# Also check what we just fixed
print("\nChecking ls_medical_device files for the pattern...")
med_device_path = os.path.join(base_path, "ls_medical_device", "views")
if os.path.exists(med_device_path):
    for file in sorted(os.listdir(med_device_path)):
        if file.endswith(".xml"):
            filepath = os.path.join(med_device_path, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if 'group name="group_by"' in content:
                print(f"  ✓ {file} - FIXED (has group name=\"group_by\")")
            elif 'expand="0"' in content:
                print(f"  ✗ {file} - STILL BROKEN (has expand=\"0\")")
            else:
                print(f"  - {file} - no group_by section")
