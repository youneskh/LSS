#!/usr/bin/env python3
"""Fix W1201: convert _logger.info("msg %s" % var) → _logger.info("msg %s", var).

These are all single-line logger calls with % formatting that should use
lazy % formatting (passing args separately).
"""
import re
from pathlib import Path
from collections import defaultdict

LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")
ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")
BS = chr(92)

stats = defaultdict(int)

# Parse W1201 entries
entries = []
for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    if "W1201" not in line:
        continue
    m = re.match(r"^(.+?):(\d+):", line)
    if m:
        entries.append((m.group(1).replace(BS, "/"), int(m.group(2))))

# Group by file
by_file = defaultdict(list)
for fp, lineno in entries:
    by_file[fp].append(lineno)


def fix_logger_percent(content):
    """Convert _logger.X("str" % args) → _logger.X("str", args)."""
    lines = content.split("\n")
    modified = False

    for lineno in sorted(by_file.get("", []), reverse=True):
        pass

    for fp_str, linenos in by_file.items():
        fp = ROOT / fp_str
        if not fp.exists():
            continue
        lines = fp.read_text(encoding="utf-8", errors="replace").split("\n")
        file_modified = False

        for lineno in sorted(linenos, reverse=True):
            idx = lineno - 1
            if idx >= len(lines):
                continue
            line = lines[idx]

            # Match: _logger.LEVEL("...%s..." % (args)) or _logger.LEVEL("..." % var)
            # Pattern: logger.method("text with % formats" % something)
            m = re.match(
                r'^(\s*(?:self\.)?(?:_logger|logger|logging|log)\.\w+\()'
                r'(["\'])(.*?)\2'
                r'\s*%\s*(.+?)\s*(\))\s*(.*)$',
                line,
            )
            if m:
                prefix = m.group(1)
                quote = m.group(2)
                fmt_str = m.group(3)
                args_part = m.group(4)
                close_paren = m.group(5)
                rest = m.group(6)
                new_line = f'{prefix}{quote}{fmt_str}{quote}, {args_part}{close_paren}{rest}'
                lines[idx] = new_line
                file_modified = True
                stats["W1201"] += 1

        if file_modified:
            new_content = "\n".join(lines)
            fp.write_text(new_content, encoding="utf-8")
            stats["files"] += 1


# Actually process
for fp_str, linenos in by_file.items():
    fp = ROOT / fp_str
    if not fp.exists():
        continue
    lines = fp.read_text(encoding="utf-8", errors="replace").split("\n")
    file_modified = False

    for lineno in sorted(linenos, reverse=True):
        idx = lineno - 1
        if idx >= len(lines):
            continue
        line = lines[idx]

        m = re.match(
            r'^(\s*(?:self\.)?(?:_logger|logger|logging|log)\.\w+\()'
            r'(["\'])(.*?)\2'
            r'\s*%\s*(.+?)\s*(\))\s*(.*)$',
            line,
        )
        if m:
            prefix = m.group(1)
            quote = m.group(2)
            fmt_str = m.group(3)
            args_part = m.group(4)
            close_paren = m.group(5)
            rest = m.group(6)
            new_line = f'{prefix}{quote}{fmt_str}{quote}, {args_part}{close_paren}{rest}'
            lines[idx] = new_line
            file_modified = True
            stats["W1201"] += 1

    if file_modified:
        new_content = "\n".join(lines)
        fp.write_text(new_content, encoding="utf-8")
        stats["files"] += 1

print(f"Files modified: {stats.get('files', 0)}")
print(f"W1201 fixed: {stats.get('W1201', 0)}")
