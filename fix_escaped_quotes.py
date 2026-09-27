import os
import re

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"

for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            
            # Fix escaped quotes in invisible/readonly attributes
            # invisible="status != \'answered\'" → invisible="status != 'answered'"
            content = content.replace(r"\'", "'")
            
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print("Fixed: " + filepath)
        except Exception as e:
            print("Error: " + str(e))
