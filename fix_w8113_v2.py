"""Remove all remaining W8113 redundant string= attributes.

Pylint reports the line of the field assignment start for multi-line defs.
We parse each flagged location, find the string= parameter within the
field definition, and remove it if it equals the auto-derived label.
"""
import re
from pathlib import Path

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")


def humanize(name: str) -> str:
    return name.replace("_", " ").title()


# Parse pylint log
locations = []
for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "W8113" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):", line)
    if m:
        locations.append((m.group(1).replace("\\", "/"), int(m.group(2))))

# Group by file
from collections import defaultdict

by_file = defaultdict(list)
for relpath, lineno in locations:
    by_file[relpath].append(lineno)


def find_string_param(lines, start_idx, indent):
    """Find the string= line within a field def starting at start_idx."""
    for j in range(start_idx, min(start_idx + 30, len(lines))):
        stripped = lines[j]
        if stripped.strip() == "":
            continue
        cur_indent = len(stripped) - len(stripped.lstrip())
        # Match string= at deeper indent than the field assignment
        sm = re.search(r'string\s*=\s*["\']([^"\']+)["\']', stripped)
        if sm and cur_indent > indent:
            return j, sm.group(1), stripped
        # Stop at closing paren at field indent
        if cur_indent <= indent and stripped.strip().startswith(")"):
            return None, None, None
    return None, None, None


total_fixed = 0
files_fixed = 0

for relpath, linenos in by_file.items():
    full = ROOT / relpath
    if not full.exists():
        continue
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    changed = False

    for lineno in linenos:
        # pylint line numbers are 1-based; the flagged line is the field start
        idx = lineno - 1
        if idx >= len(lines):
            continue
        # Find the field name: pattern  name = fields.XXX(
        # The flagged line might be the LHS or the first line of the def.
        # Search backward up to 3 lines for the field assignment.
        field_name = None
        field_indent = None
        assign_line = idx
        for back in range(min(3, idx), -1, -1):
            m = re.match(r"^(\s*)(\w+)\s*=\s*fields\.\w+", lines[idx - back])
            if m:
                field_indent = len(m.group(1))
                field_name = m.group(2)
                assign_line = idx - back
                break
        if not field_name:
            continue

        # Find string= within this field def
        sidx, sval, sline = find_string_param(lines, assign_line, field_indent)
        if sidx is None:
            continue

        if sval.lower() == humanize(field_name).lower():
            # Remove the string= parameter from the line
            new_line = re.sub(r',?\s*string\s*=\s*["\'][^"\']*["\']', "", sline)
            # Clean up: leading comma removed if string was first param
            new_line = re.sub(r"^\s*,\s*", "    ", new_line) if new_line.strip().startswith(",") else new_line
            # If line becomes whitespace-only, remove it entirely
            if new_line.strip() == "":
                lines[sidx] = ""
            else:
                lines[sidx] = new_line
            total_fixed += 1
            changed = True

    if changed:
        full.write_text("".join(lines), encoding="utf-8")
        files_fixed += 1

print(f"W8113: Removed {total_fixed} redundant string= in {files_fixed} files")
