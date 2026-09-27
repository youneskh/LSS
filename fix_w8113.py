"""Remove W8113 redundant string= attributes from multi-line field definitions.

A string= is redundant when its value matches the auto-derived Odoo label
(field name with underscores replaced by spaces and title-cased).
"""
import re
import os

ADDONS = r"D:\Docker\odoo19Claude_ls-docker\addons"


def humanize(name):
    return name.replace("_", " ").title()


# Match field assignment start:  res_id = fields.Integer(
FIELD_DEF = re.compile(r"^(\s*)(\w+)\s*=\s*fields\.\w+\s*\($")

# Match string= on its own line inside a field def
QUOTED_STR = r'"[^"]*"'
APOS_STR = r"'[^']*'"
STRING_LINE = re.compile(
    r"^(\s*)string\s*=\s*(?:" + QUOTED_STR + r"|" + APOS_STR + r")\s*,?\s*$"
)


count = 0
files = 0

for root, dirs, fnames in os.walk(ADDONS):
    if "/tools" in root.replace(os.sep, "/"):
        continue
    for fn in fnames:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        with open(fp, encoding="utf-8") as f:
            lines = f.readlines()

        changed = False
        i = 0
        while i < len(lines):
            m = FIELD_DEF.match(lines[i])
            if m:
                indent = m.group(1)
                field_name = m.group(2)
                # Look ahead for string=
                for j in range(i + 1, min(i + 20, len(lines))):
                    sm = STRING_LINE.match(lines[j])
                    if sm and sm.group(1).startswith(indent):
                        # Extract the string value
                        val_match = re.search(
                            r"string\s*=\s*[\"']([^\"']+)[\"']", lines[j]
                        )
                        if val_match:
                            sval = val_match.group(1)
                            if sval.lower() == humanize(field_name).lower():
                                lines[j] = ""  # remove the line
                                count += 1
                                changed = True
                        break
                    # Stop at closing paren
                    stripped = lines[j].strip()
                    if stripped.startswith(")") and not stripped.startswith(")#"):
                        break
            i += 1

        if changed:
            with open(fp, "w", encoding="utf-8") as f:
                f.writelines(lines)
            files += 1

print(f"W8113: Removed {count} redundant string= in {files} files")
