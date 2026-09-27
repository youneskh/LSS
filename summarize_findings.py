"""Summarize pylint-odoo and flake8 findings by module, excluding tooling scripts."""
import re
import collections
from pathlib import Path

ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")
SCRIPT_PREFIXES = (
    "convert_sql_constraints", "retrofit_scan", "static_check",
    "verify_constraints", "extract_names", "diagnose_views2",
    "negative_control", "tools_generate_docs",
)

# Pattern: addons\<module>\... or addons/<module>/...
MOD_RE = re.compile(r'addons[\\/]+([^\\/:\s]+)')


def by_module(logfile, msg_ids):
    """Return {module: count} for lines matching any of msg_ids, excluding scripts/tools."""
    want = tuple("(%s)" % m for m in msg_ids)
    counts = collections.Counter()
    for line in logfile.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("addons"):
            continue
        if not any(w in line for w in want):
            continue
        if "/tools/" in line or "\\tools\\" in line:
            continue
        # exclude standalone scripts at addons root (addons\<name>.py)
        m = MOD_RE.match(line)
        if not m:
            continue
        mod = m.group(1)
        if mod.endswith(".py") or mod in SCRIPT_PREFIXES:
            continue
        counts[mod] += 1
    return counts


pylint_log = ROOT / "logs" / "pylint_odoo_all.txt"
flake_log = ROOT / "logs" / "flake8_report.txt"

print("=" * 70)
print("E8140 (raise in unlink) by module")
print("=" * 70)
e8140 = by_module(pylint_log, ["E8140"])
print("Unique modules:", len(e8140), " Total instances:", sum(e8140.values()))
for mod, n in e8140.most_common(15):
    print("  %3d  %s" % (n, mod))

print()
print("=" * 70)
print("W8161 (use self.env._ instead of _) by module - top 15")
print("=" * 70)
w8161 = by_module(pylint_log, ["W8161"])
print("Unique modules:", len(w8161), " Total instances:", sum(w8161.values()))
for mod, n in w8161.most_common(15):
    print("  %3d  %s" % (n, mod))

print()
print("=" * 70)
print("W8301 + W8120 (lazy/named translation placeholders) by module - top 15")
print("=" * 70)
w83 = by_module(pylint_log, ["W8301", "W8120"])
print("Unique modules:", len(w83), " Total instances:", sum(w83.values()))
for mod, n in w83.most_common(15):
    print("  %3d  %s" % (n, mod))

print()
print("=" * 70)
print("W8113 (redundant string=) by module - top 15")
print("=" * 70)
w8113 = by_module(pylint_log, ["W8113"])
print("Unique modules:", len(w8113), " Total instances:", sum(w8113.values()))
for mod, n in w8113.most_common(15):
    print("  %3d  %s" % (n, mod))

print()
print("=" * 70)
print("C8116 (superfluous manifest key) by module - top 10")
print("=" * 70)
c8116 = by_module(pylint_log, ["C8116"])
print("Unique modules:", len(c8116), " Total instances:", sum(c8116.values()))
for mod, n in c8116.most_common(10):
    print("  %3d  %s" % (n, mod))

print()
print("=" * 70)
print("flake8 E128/E124 (continuation indent) by module - top 15")
print("=" * 70)
e128 = by_module(flake_log, ["E128", "E124"])
print("Unique modules:", len(e128), " Total instances:", sum(e128.values()))
for mod, n in e128.most_common(15):
    print("  %3d  %s" % (n, mod))
