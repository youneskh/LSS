#!/usr/bin/env python3
"""Debug W8113: check why fix_w8113_v2.py matched 0 entries."""
import re
from pathlib import Path
from collections import defaultdict

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")


def humanize(name):
    return name.replace("_", " ").title()


# Parse pylint log
locations = []
for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "W8113" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):", line)
    if m:
        locations.append((m.group(1), int(m.group(2))))

mismatches = 0
matches = 0
no_field = 0
no_string = 0

for relpath, lineno in locations:
    fp = ROOT / relpath.replace("\\", "/")
    if not fp.exists():
        print(f"NOT FOUND: {fp}")
        continue
    lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = lineno - 1
    if idx >= len(lines):
        print(f"OUT OF RANGE: {relpath}:{lineno}")
        continue

    # Find field name backward
    field_name = None
    field_indent = None
    assign_line = idx
    for back in range(min(3, idx), -1, -1):
        m2 = re.match(r"^(\s*)(\w+)\s*=\s*fields\.\w+", lines[idx - back])
        if m2:
            field_indent = len(m2.group(1))
            field_name = m2.group(2)
            assign_line = idx - back
            break

    if not field_name:
        no_field += 1
        print(f"NO FIELD: {relpath}:{lineno} -> {lines[idx].strip()[:80]}")
        continue

    # Find string= forward
    sval = None
    for j in range(assign_line, min(assign_line + 30, len(lines))):
        stripped = lines[j]
        cur_indent = len(stripped) - len(stripped.lstrip())
        sm = re.search(r'string\s*=\s*["\']([^"\']+)["\']', stripped)
        if sm and cur_indent > field_indent:
            sval = sm.group(1)
            break
        if cur_indent <= field_indent and stripped.strip().startswith(")"):
            break

    if not sval:
        no_string += 1
        print(f"NO STRING: {relpath}:{lineno} field={field_name}")
        continue

    expected = humanize(field_name)
    if expected.lower() == sval.lower():
        matches += 1
    else:
        mismatches += 1
        if mismatches <= 10:
            print(
                f"MISMATCH: {relpath}:{lineno} field={field_name} "
                f'string="{sval}" expected="{expected}"'
            )

print(f"\nTotal: {len(locations)}, matches={matches}, mismatches={mismatches}, "
      f"no_field={no_field}, no_string={no_string}")
