import os
import re
import xml.etree.ElementTree as ET

base_path = r"D:\Docker\odoo19Claude_ls-docker\addons"
unsearchable_fields = {}

# Scan all XML view files for unsearchable fields in domains
for root, dirs, files in os.walk(base_path):
    for file in files:
        if not file.endswith("_views.xml"):
            continue
        filepath = os.path.join(root, file)
        
        try:
            tree = ET.parse(filepath)
            for filter_elem in tree.iter("filter"):
                domain = filter_elem.get("domain", "")
                if not domain:
                    continue
                # Extract field names from domain patterns like ('fieldname', ...)
                fields = re.findall(r"\('([a-z_][a-z0-9_]*)'", domain)
                for field in fields:
                    if field not in unsearchable_fields:
                        unsearchable_fields[field] = []
                    unsearchable_fields[field].append({
                        "file": filepath,
                        "module": os.path.basename(root),
                        "filter": filter_elem.get("name", "unknown")
                    })
        except Exception as e:
            pass

print(f"Found {len(unsearchable_fields)} unique fields used in filters:")
for field, locations in sorted(unsearchable_fields.items()):
    if len(locations) <= 2:  # Skip common fields
        continue
    print(f"\n{field}:")
    for loc in locations[:3]:  # Show first 3 occurrences
        print(f"  - {loc['module']}: {loc['file'].split(os.sep)[-1]}")

# Now scan model files for these fields
print("\n\nScanning model files for these fields...")
fields_to_fix = [
    ("ls_environmental_monitoring", "approved_limit_count", "models/ls_env_sampling_point.py"),
]

for addon, field_name, model_file in fields_to_fix:
    addon_path = os.path.join(base_path, addon)
    model_path = os.path.join(addon_path, model_file)
    
    if not os.path.exists(model_path):
        print(f"File not found: {model_path}")
        continue
    
    with open(model_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    
    # Add search parameter to field definition
    pattern = rf'({field_name}\s*=\s*fields\.Integer\([^)]*compute="[^"]*")'
    replacement = rf'\1, search="_search_{field_name}"'
    content = re.sub(pattern, replacement, content)
    
    # Check if search method already exists
    if f"def _search_{field_name}" not in content:
        # Add search method before action methods or unlink
        search_method = f'''
    def _search_{field_name}(self, operator, value):
        """Allow filtering on the non-stored {field_name} field."""
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.{field_name}, operator, value)
        ]
        return [("id", "in", matching_ids)]
'''
        
        # Add helper method if not present
        if "_evaluate_operator" not in content:
            evaluate_method = '''
    @staticmethod
    def _evaluate_operator(actual, operator, expected):
        """Evaluate a comparison operator between two values."""
        ops = {
            "=": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        return ops.get(operator, lambda a, b: False)(actual, expected)
'''
            search_method += evaluate_method
        
        # Find insertion point
        insertion_patterns = [r"    def action_", r"    def unlink\(", r"    def _action_"]
        insertion_point = None
        for pattern in insertion_patterns:
            match = re.search(pattern, content)
            if match:
                insertion_point = match.start()
                break
        
        if insertion_point is None:
            insertion_point = content.rfind("\nclass ")
            if insertion_point == -1:
                insertion_point = len(content)
        
        content = content[:insertion_point] + search_method + "\n" + content[insertion_point:]
    
    if content != original:
        with open(model_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {model_file} - added search method for {field_name}")

print("\nCompleted.")
