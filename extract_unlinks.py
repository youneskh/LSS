"""Extract every E8140 unlink method body for review."""
import re
from pathlib import Path

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_all.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")

# Parse pylint log for E8140 lines: path:line: [..]
locations = []
for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "E8140" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):", line)
    if m:
        locations.append((m.group(1).replace("\\", "/"), int(m.group(2))))

locations.sort()
print(f"Total E8140 locations: {len(locations)}")
print("=" * 70)

for idx, (relpath, lineno) in enumerate(locations, 1):
    full = ROOT / relpath
    if not full.exists():
        print(f"\n[{idx}] MISSING: {relpath}:{lineno}")
        continue
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    # find the enclosing 'def unlink' by scanning backwards from lineno
    start = None
    for i in range(lineno - 1, -1, -1):
        if re.match(r"\s*def unlink\(self", lines[i]):
            start = i
            break
    if start is None:
        print(f"\n[{idx}] {relpath}:{lineno} (no def unlink found above)")
        continue
    # collect method body until next def at same-or-less indent or EOF
    header = lines[start]
    body_indent = len(header) - len(header.lstrip())
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j]
        if stripped.strip() == "":
            continue
        cur_indent = len(stripped) - len(stripped.lstrip())
        # a new method/class/decorator at indent <= body_indent ends this method
        if cur_indent <= body_indent and re.match(r"\s*(def |class |@|\w)", stripped):
            end = j
            break
    print(f"\n[{idx}] {relpath}:{lineno}")
    print("-" * 70)
    for k in range(start, min(end, len(lines))):
        print(lines[k])
