#!/usr/bin/env python3
"""Fix F821: Add missing imports (base64, EVAL_NO_LIMIT)."""
from pathlib import Path

fixes = []

# Fix 1: wooden_marketplace/controllers/main.py - missing base64 import
f1 = Path("addons/wooden_marketplace/controllers/main.py")
if f1.exists():
    with open(f1, "r", encoding="utf-8") as f:
        content = f.read()
    if "import base64" not in content:
        # Add after first import block
        lines = content.splitlines()
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                import_idx = i + 1
        lines.insert(import_idx, "import base64")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        fixes.append(f"{f1}: added 'import base64'")

# Fix 2: ls_environmental_monitoring/models/ls_env_result.py - EVAL_NO_LIMIT
f2 = Path("addons/ls_environmental_monitoring/models/ls_env_result.py")
if f2.exists():
    with open(f2, "r", encoding="utf-8") as f:
        content = f.read()
    if "EVAL_NO_LIMIT" not in content.split("#")[0] and "EVAL_NO_LIMIT" in content:
        # Check context - likely a domain eval context
        lines = content.splitlines()
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                import_idx = i + 1
        # EVAL_NO_LIMIT might be from odoo.tools.safe_eval
        lines.insert(import_idx, "from odoo.tools.safe_eval import EVAL_NO_LIMIT")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        fixes.append(f"{f2}: added 'from odoo.tools.safe_eval import EVAL_NO_LIMIT'")

print(f"Fixed {len(fixes)} files:")
for f in fixes:
    print(f"  {f}")
