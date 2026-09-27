#!/usr/bin/env python3
"""Find remaining unfixed W1203/W1201 lines."""
import re
from pathlib import Path

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")

BACKSLASH = chr(92)  # backslash char

for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "W1203" not in line and "W1201" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):", line)
    if not m:
        continue
    fp = m.group(1).replace(BACKSLASH, "/")
    lineno = int(m.group(2))
    full = ROOT / fp
    if not full.exists():
        continue
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    if lineno - 1 >= len(lines):
        continue
    code = "W1203" if "W1203" in line else "W1201"
    content = lines[lineno - 1].rstrip()
    # Show the line and surrounding context
    if 'f"' in content or "f'" in content or ".format(" in content:
        print(f"{fp}:{lineno} [{code}]")
        print(f"  {content[:150]}")
        # Show next line too
        if lineno < len(lines):
            print(f"  {lines[lineno].rstrip()[:150]}")
        print()
