"""Remove C8116 superfluous manifest keys and W8113 redundant string= attributes.

C8116: Removes lines like 'auto_install': False, 'external_dependencies': {},
       'test': [], 'images': [], 'summary': '' from __manifest__.py files.
       These are all equal to the Odoo default values.

W8113: Removes string= parameters from field definitions where the string
       value equals the auto-derived field name (Odoo capitalizes the
       Python attribute name as the default label).
"""
import re
import os

ADDONS = r"D:\Docker\odoo19Claude_ls-docker\addons"

# ── C8116: superfluous manifest keys ──────────────────────────────────────
# Keys where value==default is a no-op. Match both 'key': Value and "key": Value.
SUPERFLUOUS_PATTERNS = [
    # auto_install: False
    (re.compile(r'^(\s*)["\']auto_install["\']\s*:\s*False\s*,?\s*\n', re.M),
     None),
    # external_dependencies: {}
    (re.compile(r'^(\s*)["\']external_dependencies["\']\s*:\s*\{\}\s*,?\s*\n', re.M),
     None),
    # test: []
    (re.compile(r'^(\s*)["\']test["\']\s*:\s*\[\]\s*,?\s*\n', re.M),
     None),
    # images: []
    (re.compile(r'^(\s*)["\']images["\']\s*:\s*\[\]\s*,?\s*\n', re.M),
     None),
    # summary: ''  or  summary: ""  or  summary: .
    (re.compile(r'^(\s*)["\']summary["\']\s*:\s*["\']\.?["\']\s*,?\s*\n', re.M),
     None),
]

manifests_fixed = 0
for root, _dirs, files in os.walk(ADDONS):
    if "__manifest__.py" not in files:
        continue
    mf = os.path.join(root, "__manifest__.py")
    with open(mf, encoding="utf-8") as f:
        original = f.read()
    content = original
    for pat, _repl in SUPERFLUOUS_PATTERNS:
        content = pat.sub("", content)
    if content != original:
        with open(mf, "w", encoding="utf-8") as f:
            f.write(content)
        manifests_fixed += 1

print(f"C8116: Fixed {manifests_fixed} manifests")

# ── W8113: redundant string= on field definitions ─────────────────────────
# Matches  string="field_name"  or  string='field_name'  inside a fields.xxx()
# call where the string value (lowercased, underscores→spaces→title) equals
# the auto-derived Odoo label.
#
# The Odoo convention: field named  is_valid  gets label "Is Valid".
# So string="Is Valid" is redundant.
#
# We match lines like:  is_valid = fields.Boolean(string="Is Valid")
# where string value == humanized field name.

# Build the humanized form: "some_field_name" → "Some Field Name"
def humanize(field_name: str) -> str:
    return field_name.replace("_", " ").title()


# Pattern: capture field name on LHS and string value on RHS
# e.g.:  is_valid = fields.Boolean(string="Is Valid")
FIELD_STR_PAT = re.compile(
    r'^(\s*)(\w+)\s*=\s*fields\.\w+\([^)]*string\s*=\s*["\']([^"\']+)["\'][^)]*\)',
    re.M,
)

fields_fixed = 0
files_touched = set()

for root, _dirs, files in os.walk(ADDONS):
    if "/tools" in root.replace(os.sep, "/"):
        continue
    if "/static" in root.replace(os.sep, "/"):
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        with open(fp, encoding="utf-8") as f:
            original = f.read()

        lines = original.splitlines(True)
        changed = False
        for i, line in enumerate(lines):
            m = FIELD_STR_PAT.match(line)
            if not m:
                continue
            indent, field_name, string_val = m.group(1), m.group(2), m.group(3)
            if string_val.lower() == humanize(field_name).lower():
                # Remove string="..." parameter
                # Handle both comma-separated and trailing forms
                new_line = re.sub(r',?\s*string\s*=\s*["\'][^"\']*["\']', '', line)
                # Clean up double commas
                new_line = new_line.replace(",,", ",").replace("(,", "(")
                lines[i] = new_line
                changed = True
                fields_fixed += 1

        if changed:
            with open(fp, "w", encoding="utf-8") as f:
                f.writelines(lines)
            files_touched.add(fp)

print(f"W8113: Removed {fields_fixed} redundant string= in {len(files_touched)} files")
print("Done.")
