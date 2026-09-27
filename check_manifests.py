#!/usr/bin/env python3
"""Check Odoo manifest compliance for Odoo 19 CE standards."""
import os
import json
import ast
from pathlib import Path

ADDONS_DIR = Path("addons")

REQUIRED_KEYS = {"name", "version"}
RECOMMENDED_KEYS = {"summary", "category", "author", "license", "depends", "data", "installable"}
VALID_LICENSES = {
    "AGPL-3", "GPL-2", "GPL-2 or any later version",
    "GPL-3", "GPL-3 or any later version", "LGPL-3",
    "LGPL-2.1", "MIT", "Other OSI approved licence", "OEEL-1", "OPL-1"
}
VALID_CATEGORIES = {
    "Accounting", "Accounting/Accounting", "Accounting/Localizations",
    "Accounting/Invoicing", "Human Resources", "Sales", "Sales/CRM",
    "Sales/Sales", "Purchases", "Inventory", "Manufacturing", "Services",
    "Project", "Helpdesk", "Marketing", "Website", "Administration",
    "Localization", "Technical", "Tools", "Other", "Uncategorized",
    "Human Resources/Contracts", "Human Resources/Employees",
    "Warehouse", "Warehouse/Stock", "Operations", "Discuss",
    "Extra Rights", "Hidden", "Social", "Productivity",
    "Productivity/Discuss", "Productivity/Project",
    "Human Resources/Fleet", "Manufacturing/Manufacturing",
    "Invoicing & Payments", "Supply Chain", "Specific Industry Applications",
}

issues = []
manifest_count = 0

for manifest_path in sorted(ADDONS_DIR.glob("*/__manifest__.py")):
    manifest_count += 1
    module_name = manifest_path.parent.name
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        manifest = ast.literal_eval(content)
    except SyntaxError as e:
        issues.append({"module": module_name, "severity": "CRITICAL", "issue": f"SyntaxError in manifest: {e}"})
        continue
    except Exception as e:
        issues.append({"module": module_name, "severity": "CRITICAL", "issue": f"Cannot parse manifest: {e}"})
        continue

    if not isinstance(manifest, dict):
        issues.append({"module": module_name, "severity": "CRITICAL", "issue": "Manifest is not a dict"})
        continue

    # Required keys
    missing = REQUIRED_KEYS - set(manifest.keys())
    if missing:
        issues.append({"module": module_name, "severity": "HIGH", "issue": f"Missing required keys: {missing}"})

    # Version check
    version = manifest.get("version", "")
    if version:
        parts = version.split(".")
        if len(parts) < 2:
            issues.append({"module": module_name, "severity": "MEDIUM", "issue": f"Invalid version format: {version}"})
        elif parts[0] != "19":
            issues.append({"module": module_name, "severity": "MEDIUM", "issue": f"Version not targeting Odoo 19: {version}"})

    # License check
    license_ = manifest.get("license", "")
    if license_ and license_ not in VALID_LICENSES:
        issues.append({"module": module_name, "severity": "LOW", "issue": f"Unusual license: {license_}"})

    # Application without category
    if manifest.get("application") and not manifest.get("category"):
        issues.append({"module": module_name, "severity": "LOW", "issue": "Application=True but no category set"})

    # Superfluous installable
    if manifest.get("installable") is True:
        issues.append({"module": module_name, "severity": "LOW", "issue": "Superfluous 'installable': True (default)"})

    # Superfluous application
    if manifest.get("application") is False:
        issues.append({"module": module_name, "severity": "INFO", "issue": "Superfluous 'application': False (default)"})

    # Check for website
    if not manifest.get("website"):
        issues.append({"module": module_name, "severity": "INFO", "issue": "No 'website' key in manifest"})

    # Check for author
    if not manifest.get("author"):
        issues.append({"module": module_name, "severity": "LOW", "issue": "No 'author' key in manifest"})

    # Check depends
    depends = manifest.get("depends", [])
    if not isinstance(depends, list):
        issues.append({"module": module_name, "severity": "HIGH", "issue": f"'depends' is not a list: {type(depends).__name__}"})

    # Check data/demo
    for key in ("data", "demo"):
        val = manifest.get(key)
        if val is not None and not isinstance(val, list):
            issues.append({"module": module_name, "severity": "HIGH", "issue": f"'{key}' is not a list: {type(val).__name__}"})

    # Check images/icon exists
    icon_path = manifest_path.parent / "static" / "description" / "icon.png"
    if not icon_path.exists():
        issues.append({"module": module_name, "severity": "INFO", "issue": "Missing static/description/icon.png"})

    # Check README
    readme_path = manifest_path.parent / "README.rst"
    readme_md = manifest_path.parent / "README.md"
    if not readme_path.exists() and not readme_md.exists():
        issues.append({"module": module_name, "severity": "LOW", "issue": "Missing README.rst or README.md"})

    # Check for __init__.py
    init_path = manifest_path.parent / "__init__.py"
    if not init_path.exists():
        issues.append({"module": module_name, "severity": "HIGH", "issue": "Missing __init__.py"})

    # Check for models/__init__.py if models/ exists
    models_init = manifest_path.parent / "models" / "__init__.py"
    models_dir = manifest_path.parent / "models"
    if models_dir.exists() and not models_init.exists():
        issues.append({"module": module_name, "severity": "HIGH", "issue": "models/ directory exists but no models/__init__.py"})

    # Check for tests/__init__.py if tests/ exists
    tests_init = manifest_path.parent / "tests" / "__init__.py"
    tests_dir = manifest_path.parent / "tests"
    if tests_dir.exists() and not tests_init.exists():
        issues.append({"module": module_name, "severity": "MEDIUM", "issue": "tests/ directory exists but no tests/__init__.py"})

# Summary
print(f"=" * 70)
print(f"ODOO MANIFEST COMPLIANCE REPORT")
print(f"=" * 70)
print(f"Total modules checked: {manifest_count}")
print(f"Total issues found:    {len(issues)}")
print()

severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
issues.sort(key=lambda x: (severity_order.get(x["severity"], 99), x["module"]))

current_severity = None
for issue in issues:
    if issue["severity"] != current_severity:
        current_severity = issue["severity"]
        print(f"\n--- {current_severity} ---")
    print(f"  [{issue['module']}] {issue['issue']}")

# Per-severity counts
print(f"\n{'=' * 70}")
print("SUMMARY BY SEVERITY:")
for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
    count = sum(1 for i in issues if i["severity"] == sev)
    print(f"  {sev:10s}: {count:4d}")
