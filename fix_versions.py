#!/usr/bin/env python3
"""Bump version strings from 18.0 to 19.0 for targeted modules."""
from pathlib import Path

ADDONS_DIR = Path("addons")

MODULES_TO_BUMP = {
    "base_import_async": ("18.0.1.0.0", "19.0.1.0.0"),
    "queue_job_batch": ("18.0.1.0.0", "19.0.1.0.0"),
    "queue_job_cron": ("18.0.1.1.1", "19.0.1.1.1"),
    "queue_job_cron_jobrunner": ("18.0.1.0.1", "19.0.1.0.1"),
    "queue_job_subscribe": ("18.0.1.0.0", "19.0.1.0.0"),
    "test_queue_job_batch": ("18.0.1.0.0", "19.0.1.0.0"),
    "wooden_marketplace_llm": (None, "19.0.1.0.0"),  # was "1.0.0" or unversioned
}

fixes = []

for module, (old, new) in MODULES_TO_BUMP.items():
    manifest = ADDONS_DIR / module / "__manifest__.py"
    if not manifest.exists():
        print(f"SKIP: {module} not found")
        continue
    with open(manifest, "r", encoding="utf-8") as f:
        content = f.read()
    
    if old and old in content:
        content = content.replace(old, new)
        fixes.append(f"{module}: {old} → {new}")
    elif "'version'" in content or '"version"' in content:
        # Replace any version value
        import re
        content = re.sub(
            r"(['\"]version['\"]\s*:\s*['\"])[^'\"]+(['\"])",
            rf"\g<1>{new}\g<2>",
            content
        )
        fixes.append(f"{module}: version → {new}")
    else:
        print(f"SKIP: {module} has no version key")
        continue
    
    with open(manifest, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Bumped {len(fixes)} modules:")
for f in fixes:
    print(f"  {f}")
