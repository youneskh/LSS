import os
import re

# Scan all model files and add search methods for computed fields used in domains
addons_path = r"D:\Docker\odoo19Claude_ls-docker\addons"

# Map of field names to their model files (based on error messages)
unsearchable_fields = {
    "ls_environmental_monitoring": {
        "open_excursion_count": "models/ls_env_area.py",
    },
}

for addon, fields_map in unsearchable_fields.items():
    addon_path = os.path.join(addons_path, addon)
    for field_name, model_file in fields_map.items():
        model_path = os.path.join(addon_path, model_file)
        
        if not os.path.exists(model_path):
            print(f"File not found: {model_path}")
            continue
        
        with open(model_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add search parameter to field definition
        pattern = rf'({field_name}\s*=\s*fields\.Integer\([^)]*compute="[^"]*")'
        replacement = rf'\1, search="_search_{field_name}"'
        content = re.sub(pattern, replacement, content)
        
        # Check if search method already exists
        if f"def _search_{field_name}" in content:
            print(f"Search method already exists for {field_name} in {model_file}")
            continue
        
        # Add search method before the class ends (before first workflow/action method)
        search_method = f'''
    def _search_{field_name}(self, operator, value):
        """Allow filtering on the non-stored {field_name} field.
        
        :param str operator: one of =, !=, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
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
        
        # Find insertion point (before action_* methods or unlink)
        insertion_patterns = [r"    def action_", r"    def unlink\(", r"    def _action_"]
        insertion_point = None
        for pattern in insertion_patterns:
            match = re.search(pattern, content)
            if match:
                insertion_point = match.start()
                break
        
        if insertion_point is None:
            # If no action method found, insert before the end of class
            insertion_point = content.rfind("\nclass ")
            if insertion_point == -1:
                insertion_point = len(content)
        
        content = content[:insertion_point] + search_method + "\n" + content[insertion_point:]
        
        with open(model_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Fixed: {model_file} - added search method for {field_name}")

print("\nCompleted processing unsearchable fields.")
