import os
import re

# Add search method for failed_count in ls_validation_execution.py
validation_exec_path = r"D:\Docker\odoo19Claude_ls-docker\addons\ls_validation\models\ls_validation_execution.py"

with open(validation_exec_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the end of _compute_result_summary and add search method
search_method = '''
    def _search_failed_count(self, operator, value):
        """Allow filtering on the non-stored failed_count field.
        
        :param str operator: one of =, !=, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.failed_count, operator, value)
        ]
        return [("id", "in", matching_ids)]
    
    def _search_open_discrepancy_count(self, operator, value):
        """Allow filtering on the non-stored open_discrepancy_count field.
        
        :param str operator: one of =, !=, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.open_discrepancy_count, operator, value)
        ]
        return [("id", "in", matching_ids)]
    
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

# Add search parameter to failed_count field definition
content = re.sub(
    r'(failed_count = fields\.Integer\(string="Failed", compute="_compute_result_summary")',
    r'\1, search="_search_failed_count"',
    content
)

# Add search parameter to open_discrepancy_count field definition
content = re.sub(
    r'(open_discrepancy_count = fields\.Integer\(\s*string="Open Discrepancies", compute="_compute_discrepancy_count")',
    r'\1, search="_search_open_discrepancy_count"',
    content
)

# Add search methods before the class ends (before the last action method or before unlink)
if "def unlink(self):" in content:
    insertion_point = content.rfind("    def unlink(self):")
    content = content[:insertion_point] + search_method + "\n\n    " + content[insertion_point:]

with open(validation_exec_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed: ls_validation_execution.py - added search methods for failed_count and open_discrepancy_count")
