#!/usr/bin/env python3
"""Run pylint-odoo on all modules and produce a summary report."""
import subprocess
import os
from pathlib import Path
import sys

ADDONS_DIR = Path("addons")
modules = sorted([d.name for d in ADDONS_DIR.iterdir() if d.is_dir() and (d / "__manifest__.py").exists()])

print(f"Running pylint-odoo on {len(modules)} modules...")
print(f"This may take a few minutes.\n")

# Process in batches of 30 to avoid timeouts
BATCH_SIZE = 30
all_issues = []
total_score = 0.0
batch_count = 0

for i in range(0, len(modules), BATCH_SIZE):
    batch = modules[i:i+BATCH_SIZE]
    paths = [str(ADDONS_DIR / m) for m in batch]
    cmd = [
        sys.executable, "-m", "pylint",
        "--load-plugins=pylint_odoo",
        "--disable=all",
        "--enable=C,R,E,F,W,odoolint",
        "--score=no",
        "--persistent=no",
    ] + paths

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        lines = result.stdout.splitlines()
        for line in lines:
            if line.startswith("addons") and ":" in line:
                all_issues.append(line)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT on batch: {batch[0]}...{batch[-1]}")
    except Exception as e:
        print(f"  ERROR on batch {batch[0]}...{batch[-1]}: {e}")

# Categorize issues
from collections import Counter

issue_types = Counter()
modules_with_issues = set()
for line in all_issues:
    # Parse: addons\module\path\file.py:line:col: CODE: message
    parts = line.split(":", 4)
    if len(parts) >= 4:
        code = parts[3].strip()
        if code:
            issue_types[code] += 1
        # Extract module name
        mod_part = parts[0].replace("addons\\", "").replace("addons/", "")
        mod_name = mod_part.split(os.sep)[0]
        modules_with_issues.add(mod_name)

print(f"\n{'=' * 70}")
print(f"PYLINT-ODOO REPORT")
print(f"{'=' * 70}")
print(f"Total modules checked: {len(modules)}")
print(f"Modules with issues:   {len(modules_with_issues)}")
print(f"Total issues found:    {len(all_issues)}")
print(f"\nTOP ISSUE TYPES:")
for code, count in issue_types.most_common(20):
    print(f"  {code:10s}: {count:5d}")

# Save full report
report_path = "logs/pylint_odoo_report.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"PYLINT-ODOO FULL REPORT\n")
    f.write(f"{'=' * 70}\n\n")
    f.write(f"Total modules checked: {len(modules)}\n")
    f.write(f"Modules with issues:   {len(modules_with_issues)}\n")
    f.write(f"Total issues found:    {len(all_issues)}\n\n")
    f.write("TOP ISSUE TYPES:\n")
    for code, count in issue_types.most_common():
        f.write(f"  {code}: {count}\n")
    f.write(f"\n{'=' * 70}\n")
    f.write("FULL ISSUES:\n")
    for line in all_issues:
        f.write(line + "\n")

print(f"\nFull report saved to: {report_path}")
