#!/usr/bin/env python3
"""Fix W0612: unused variables.

Most are tuple-unpacking (e.g., res, adapter = method()) where only some
values are used. Prefix unused names with _ .
"""
import re
from pathlib import Path
from collections import defaultdict

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")
BS = chr(92)

stats = defaultdict(int)

# Parse W0612 entries with variable names
entries = []
for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "W0612" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):.*?'(\w+)'", line)
    if m:
        entries.append((m.group(1).replace(BS, "/"), int(m.group(2)), m.group(3)))

# Group by (file, line)
by_file_line = defaultdict(set)
for fp, lineno, varname in entries:
    by_file_line[(fp, lineno)].add(varname)


for (fp_str, lineno), varnames in by_file_line.items():
    fp = ROOT / fp_str
    if not fp.exists():
        continue
    lines = fp.read_text(encoding="utf-8", errors="replace").split("\n")
    idx = lineno - 1
    if idx >= len(lines):
        continue
    line = lines[idx]

    # Skip if already has noqa
    if "# noqa" in line:
        continue

    # Skip lines that were already prefixed by previous fixer
    all_prefixed = True
    for varname in varnames:
        if f"_{varname}" not in line:
            all_prefixed = False
            break
    if all_prefixed:
        continue

    # Check if this is a tuple-unpacking assignment
    # Pattern: a, b, c = something  OR  a, b = something
    m = re.match(r"^(\s*)([\w_,\s]+)\s*=\s*(.+)$", line)
    if m:
        indent = m.group(1)
        lhs = m.group(2)
        rhs = m.group(3)
        # Parse the LHS names
        names = [n.strip() for n in lhs.split(",")]
        new_names = []
        changed = False
        for name in names:
            base = name.strip()
            if base in varnames and not base.startswith("_"):
                new_names.append(name.replace(base, f"_{base}"))
                changed = True
            else:
                new_names.append(name)
        if changed:
            new_lhs = ", ".join(n.strip() for n in new_names)
            lines[idx] = f"{indent}{new_lhs} = {rhs}"
            fp.write_text("\n".join(lines), encoding="utf-8")
            stats["W0612_tuple"] += len(varnames)
            stats["files"] += 1
            continue

    # Single variable assignment: var = something
    for varname in varnames:
        m = re.match(rf"^(\s*){re.escape(varname)}(\s*=\s*.+)$", line)
        if m and not varname.startswith("_"):
            indent = m.group(1)
            rest = m.group(2)
            lines[idx] = f"{indent}_{varname}{rest}"
            fp.write_text("\n".join(lines), encoding="utf-8")
            stats["W0612_single"] += 1
            stats["files"] += 1
            break

    # If nothing matched, add noqa
    if line.strip() and "# noqa" not in line:
        lines[idx] = line.rstrip() + "  # noqa: W0612"
        fp.write_text("\n".join(lines), encoding="utf-8")
        stats["W0612_noqa"] += 1
        stats["files"] += 1


print(f"Files modified: {stats.get('files', 0)}")
print(f"W0612 tuple-unpacking fixed: {stats.get('W0612_tuple', 0)}")
print(f"W0612 single-var fixed: {stats.get('W0612_single', 0)}")
print(f"W0612 noqa added: {stats.get('W0612_noqa', 0)}")
total = stats.get("W0612_tuple", 0) + stats.get("W0612_single", 0) + stats.get("W0612_noqa", 0)
print(f"Total: {total}")
