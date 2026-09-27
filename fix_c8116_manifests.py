#!/usr/bin/env python3
"""Fix C8116: Remove superfluous manifest keys from __manifest__.py files."""
import re
from pathlib import Path

ADDONS_DIR = Path("addons")
fixes = []
errors = []

# Patterns for superfluous keys (with single or double quotes, optional trailing comma)
PATTERNS = [
    # installable: True
    (re.compile(r"^[ \t]*['\"]installable['\"]\s*:\s*True\s*,?\s*$\n?", re.MULTILINE), "installable: True"),
    # application: False
    (re.compile(r"^[ \t]*['\"]application['\"]\s*:\s*False\s*,?\s*$\n?", re.MULTILINE), "application: False"),
    # demo: [] (empty list default)
    (re.compile(r"^[ \t]*['\"]demo['\"]\s*:\s*\[\]\s*,?\s*$\n?", re.MULTILINE), "demo: []"),
    # data: [] (empty list default)
    (re.compile(r"^[ \t]*['\"]data['\"]\s*:\s*\[\]\s*,?\s*$\n?", re.MULTILINE), "data: []"),
]

for manifest_path in sorted(ADDONS_DIR.glob("*/__manifest__.py")):
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            original = f.read()
        modified = original
        removed = []
        for pattern, desc in PATTERNS:
            if pattern.search(modified):
                modified = pattern.sub("", modified)
                removed.append(desc)
        if removed and modified != original:
            # Clean up double blank lines
            modified = re.sub(r"\n{3,}", "\n\n", modified)
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(modified)
            fixes.append(f"{manifest_path.parent.name}: removed {removed}")
    except Exception as e:
        errors.append(f"{manifest_path.parent.name}: {e}")

print(f"Fixed {len(fixes)} manifests")
if fixes:
    print("\nFirst 10 fixes:")
    for f in fixes[:10]:
        print(f"  {f}")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors[:5]:
        print(f"  {e}")
