"""Scan module .py files for Odoo 19 patterns of interest."""
import os
import re
import collections

ADDONS = r"D:\Docker\odoo19Claude_ls-docker\addons"
SEP = os.sep
pat_string = re.compile(r'string\s*=\s*(["\'])([A-Za-z0-9 _]+)\1')

stats = collections.Counter()
w8113_samples = []

for root, dirs, files in os.walk(ADDONS):
    norm = root.replace(SEP, "/")
    if "/tools/" in norm or "/static" in norm or norm.endswith("/i18n"):
        continue
    # only model-ish files
    for fn in files:
        if not fn.endswith(".py"):
            continue
        if fn in ("static_check.py", "retrofit_scan.py", "negative_control.py",
                  "convert_sql_constraints.py", "verify_constraints.py",
                  "extract_names.py", "diagnose_views2.py"):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    for m in pat_string.finditer(line):
                        stats["total_string="] += 1
        except Exception:
            pass

print("Total string= occurrences (fields/views):", stats["total_string="])
