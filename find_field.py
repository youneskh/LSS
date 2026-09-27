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
            
            if "ls_signature_binding_statement" in content:
                print(f"Found in: {filepath}")
                # Show the line
                for i, line in enumerate(content.split('\n'), 1):
                    if "ls_signature_binding_statement" in line:
                        print(f"  Line {i}: {line.strip()}")
        except:
            pass
