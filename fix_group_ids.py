import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
fixed_files = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        
        # Only process security/record rule files
        if "record_rule" not in filepath and "security" not in filepath:
            continue
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            
            # Replace group_ids with groups in ir.rule records
            # Pattern 1: group_ids with eval and Command.link
            content = re.sub(
                r'<field name="group_ids"\s+eval="\[Command\.link\(ref\(\'([^\']+)\'\)\)\]"/>',
                r'<field name="groups" rel="res.groups" eval="[(4, ref(\'\1\'))]"/>',
                content
            )
            
            # Pattern 2: group_ids with simple ref
            content = re.sub(
                r'<field name="group_ids"\s+ref="([^"]+)"/>',
                r'<field name="groups" rel="res.groups" eval="[(4, ref(\'\1\'))]"/>',
                content
            )
            
            # Pattern 3: group_ids with other patterns
            content = re.sub(
                r'<field name="group_ids"',
                r'<field name="groups" rel="res.groups"',
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
