import os

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"

for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".py"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "lss.foundation.step.template.dependencies" in content or "step.template.dependencies" in content:
                print(f"Found in: {filepath}")
                for i, line in enumerate(content.split('\n'), 1):
                    if "dependencies" in line and "Many2many" in line:
                        print(f"  Line {i}: {line.strip()}")
                        # Print context
                        lines = content.split('\n')
                        for j in range(max(0, i-3), min(len(lines), i+3)):
                            print(f"    {j}: {lines[j-1]}")
        except:
            pass
