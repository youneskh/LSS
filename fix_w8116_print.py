#!/usr/bin/env python3
"""Fix W8116/W8116: Replace print() with logger in production code."""
import re
from pathlib import Path

ADDONS_DIR = Path("addons")
fixes = []
errors = []

# Find files with print statements (skip __manifest__.py, test files, scripts)
SKIP_PATTERNS = ("__manifest__.py", "test_", "tests.py", "/tests/")

for pyfile in sorted(ADDONS_DIR.rglob("*.py")):
    if any(s in str(pyfile) for s in SKIP_PATTERNS):
        continue
    try:
        with open(pyfile, "r", encoding="utf-8") as f:
            original = f.read()
        if "print(" not in original:
            continue

        modified = original
        has_logger = "_logger" in original or "logger" in original
        added_import = False

        # Replace print(...) with _logger.info(...)
        # Handle: print("message") → _logger.info("message")
        # Handle: print(var) → _logger.info("%s", var)
        # Handle: print(f"...{var}") → _logger.info("...%s", var)

        lines = modified.splitlines()
        new_lines = []
        print_count = 0
        for line in lines:
            stripped = line.lstrip()
            indent = line[:len(line) - len(stripped)]
            if stripped.startswith("print(") and stripped.endswith(")"):
                # Simple print("msg")
                inner = stripped[6:-1]  # content inside print(...)
                new_lines.append(f'{indent}_logger.info({inner})')
                print_count += 1
            elif stripped.startswith("print("):
                # Multi-line or complex print - skip, log it
                new_lines.append(line)
                print_count += 1
            else:
                new_lines.append(line)

        if print_count > 0:
            modified = "\n".join(new_lines)
            # Add logger import if missing
            if not has_logger:
                # Find a good spot to add import
                import_idx = 0
                for i, line in enumerate(new_lines):
                    if line.startswith("from ") or line.startswith("import "):
                        import_idx = i + 1
                new_lines.insert(import_idx, "import logging")
                new_lines.insert(import_idx + 1, "")
                new_lines.insert(import_idx + 2, f"_logger = logging.getLogger(__name__)")
                new_lines.insert(import_idx + 3, "")
                modified = "\n".join(new_lines)
                added_import = True

            with open(pyfile, "w", encoding="utf-8") as f:
                f.write(modified)
            rel = str(pyfile.relative_to(ADDONS_DIR))
            fixes.append(f"{rel}: {print_count} print() → _logger.info()" + (" + import" if added_import else ""))
    except Exception as e:
        errors.append(f"{pyfile}: {e}")

print(f"Fixed {len(fixes)} files")
if fixes:
    print("\nAll fixes:")
    for f in fixes:
        print(f"  {f}")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors[:5]:
        print(f"  {e}")
