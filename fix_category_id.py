import os
import xml.etree.ElementTree as ET

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
fixed_files = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith(".xml"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            tree = ET.parse(filepath)
            root_elem = tree.getroot()
            modified = False
            
            # Find all records for res.groups model with category_id field
            for record in root_elem.findall(".//record[@model='res.groups']"):
                for field in record.findall("field[@name='category_id']"):
                    # Change category_id to category_ids (many2many)
                    field.set('name', 'category_ids')
                    modified = True
            
            if modified:
                tree.write(filepath, encoding='utf-8', xml_declaration=True)
                fixed_files.append(filepath)
                print("Fixed: " + filepath)
        except Exception as e:
            pass

print("\nTotal files fixed: " + str(len(fixed_files)))
