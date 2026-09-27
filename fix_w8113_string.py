#!/usr/bin/env python3
"""Fix W8113: Remove redundant string= attributes from Odoo field definitions.

Example: name = fields.Char(string="Name")  ->  name = fields.Char()
"""
import re
from pathlib import Path

ADDONS_DIR = Path("addons")
fixes = []
errors = []

# Match: varname = fields.Something(..., string="SameName", ...)
# We handle both single-line and some multi-line cases.
# Pattern breakdown:
#   (\w+)\s*=\s*fields\.\w+\(       -> capture var name
#   [^)]*?                          -> any args before string
#   string\s*=\s*["']([^"']+)["']   -> capture string value
#   [^)]*?\)                       -> any args after string

# For single-line cases
SINGLE_LINE_RE = re.compile(
    r'^(\s*)(\w+)\s*=\s*(fields\.\w+\()([^)]*?)'
    r'string\s*=\s*["\']([^"\']+)["\']'
    r'([^)]*?)\)',
    re.MULTILINE
)

def names_match(varname: str, string_val: str) -> bool:
    """Check if string value is redundant given the variable name.
    
    Examples:
      name -> "Name"          yes
      partner_id -> "Partner" yes (strip _id)
      sale_order -> "Sale Order"  yes
      date_start -> "Date Start"  yes
    """
    # Normalize: replace _ with space, title case
    expected = varname.replace("_", " ").title()
    # Also handle without _id, _ids suffixes
    base = varname
    for suffix in ("_id", "_ids", "_line", "_lines"):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
    expected_base = base.replace("_", " ").title()
    
    string_norm = string_val.strip()
    return (
        string_norm == expected or
        string_norm == expected_base or
        string_norm.lower() == varname.lower().replace("_", " ") or
        string_norm == varname.replace("_", " ").title()
    )

def remove_string_param(match) -> str:
    """Rebuild the line without the redundant string= parameter."""
    indent = match.group(1)
    varname = match.group(2)
    field_call_start = match.group(3)  # e.g. "fields.Char("
    before = match.group(4)           # args before string=
    string_val = match.group(5)       # the string value
    after = match.group(6)            # args after string=
    
    if not names_match(varname, string_val):
        return match.group(0)  # don't change
    
    # Clean up leading/trailing commas and spaces
    before = before.rstrip().rstrip(",")
    after = after.lstrip().lstrip(",")
    
    args = []
    if before.strip():
        args.append(before.strip())
    if after.strip():
        args.append(after.strip())
    
    if args:
        return f"{indent}{varname} = {field_call_start}{', '.join(args)})"
    else:
        return f"{indent}{varname} = {field_call_start})"

for pyfile in sorted(ADDONS_DIR.rglob("*.py")):
    if "__manifest__" in str(pyfile):
        continue
    try:
        with open(pyfile, "r", encoding="utf-8") as f:
            original = f.read()
        
        modified, count = SINGLE_LINE_RE.subn(remove_string_param, original)
        if count > 0 and modified != original:
            with open(pyfile, "w", encoding="utf-8") as f:
                f.write(modified)
            rel = str(pyfile.relative_to(ADDONS_DIR))
            fixes.append(f"{rel}: {count} redundant string= removed")
    except Exception as e:
        errors.append(f"{pyfile}: {e}")

print(f"Fixed {len(fixes)} files, total instances removed: {sum(int(f.split(': ')[1].split()[0]) for f in fixes)}")
if fixes:
    print("\nAll fixes:")
    for f in fixes:
        print(f"  {f}")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors[:5]:
        print(f"  {e}")
