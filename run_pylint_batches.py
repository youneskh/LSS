#!/usr/bin/env python3
"""Run pylint-odoo on all modules in small batches and save incremental results."""
import subprocess
import os
import sys
from pathlib import Path

ADDONS_DIR = Path("addons")
modules = sorted([d.name for d in ADDONS_DIR.iterdir() if d.is_dir() and (d / "__manifest__.py").exists()])

OUT_FILE = Path("logs/pylint_odoo_all.txt")
BATCH_SIZE = 20

# Collect all issues
counts = {}
modules_with_issues = set()
all_lines = []

for i in range(0, len(modules), BATCH_SIZE):
    batch = modules[i:i+BATCH_SIZE]
    paths = [str(ADDONS_DIR / m) for m in batch]
    cmd = [
        sys.executable, "-m", "pylint",
        "--load-plugins=pylint_odoo",
        "--disable=all",
        "--enable=odoolint",
        "--score=no",
        "--persistent=no",
    ] + paths
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        for line in result.stdout.splitlines():
            if "Module" in line or (":" in line and line.startswith("addons")):
                all_lines.append(line)
                if line.startswith("addons"):
                    parts = line.split(":", 1)
                    mod_part = parts[0].replace("addons\\", "").replace("addons/", "")
                    mod_name = mod_part.split(os.sep)[0]
                    modules_with_issues.add(mod_name)
                    # Extract code like W8113
                    code = None
                    for part in line.split():
                        if len(part) == 5 and part[0].isalpha() and part[1:].isdigit():
                            code = part
                            break
                    if code:
                        counts[code] = counts.get(code, 0) + 1
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT batch {i//BATCH_SIZE + 1}: {batch[0]}...{batch[-1]}")
    except Exception as e:
        print(f"ERROR batch {i//BATCH_SIZE + 1}: {e}")

# Write report
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(f"PYLINT-ODOO REPORT\n{'='*60}\n")
    f.write(f"Modules checked: {len(modules)}\n")
    f.write(f"Modules with issues: {len(modules_with_issues)}\n")
    f.write(f"Total issue lines: {len(all_lines)}\n\n")
    f.write("ISSUE COUNTS:\n")
    for code, count in sorted(counts.items(), key=lambda x: -x[1]):
        f.write(f"  {code}: {count}\n")
    f.write(f"\n{'='*60}\nDETAILS:\n")
    for line in all_lines:
        f.write(line + "\n")

print(f"Done. Checked {len(modules)} modules.")
print(f"Modules with issues: {len(modules_with_issues)}")
print(f"Total lines: {len(all_lines)}")
print(f"Top issues: {sorted(counts.items(), key=lambda x: -x[1])[:10]}")
print(f"Report saved to {OUT_FILE}")
