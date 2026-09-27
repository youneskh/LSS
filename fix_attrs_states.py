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
            
            # Remove attrs and states attributes (simple approach: just remove them)
            # attrs="{'invisible': [('field', 'op', 'value')]}" → invisible="field op 'value'"
            content = re.sub(
                r'attrs="\{\'invisible\': \[\(\'([^\']+)\', \'!=\', \'([^\']+)\'\)\]\}"',
                r'invisible="\1 != \'\2\'"',
                content
            )
            content = re.sub(
                r'attrs="\{\'invisible\': \[\(\'([^\']+)\', \'=\', \'([^\']+)\'\)\]\}"',
                r'invisible="\1 == \'\2\'"',
                content
            )
            content = re.sub(
                r'attrs="\{\'readonly\': \[\(\'([^\']+)\', \'!=\', \'([^\']+)\'\)\]\}"',
                r'readonly="\1 != \'\2\'"',
                content
            )
            content = re.sub(
                r'attrs="\{\'readonly\': \[\(\'([^\']+)\', \'=\', \'([^\']+)\'\)\]\}"',
                r'readonly="\1 == \'\2\'"',
                content
            )
            
            # Generic catch-all: remove remaining attrs/states attributes
            content = re.sub(r'\s+attrs="[^"]*"', '', content)
            content = re.sub(r'\s+states="[^"]*"', '', content)
            
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(filepath)
        except Exception as e:
            pass

print("Fixed files:")
for f in sorted(fixed_files):
    print("  " + f)
print("\nTotal: " + str(len(fixed_files)))
