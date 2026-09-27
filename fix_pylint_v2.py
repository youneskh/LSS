#!/usr/bin/env python3
"""Focused pylint fixer v2: fix logging, print, unused-var with broader regex."""
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"D:\Docker\odoo19Claude_ls-docker")
LOG = Path(r"D:\Docker\odoo19Claude_ls-docker\logs\pylint_odoo_final.txt")

stats = defaultdict(int)

# Logger call pattern: matches _logger.info(...), logger.debug(...), logging.warning(...)
LOGGER_RE = re.compile(
    r'^(\s*(?:self\.)?(?:_logger|logger|logging|log)\.\w+\()'
)


def parse_log():
    entries = []
    for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(.+?):(\d+):.*\((\w+)\)", line)
        if m:
            entries.append((m.group(1), int(m.group(2)), m.group(3)))
    return entries


def fstring_to_lazy(match_line):
    """Convert a single line's f-string logger/translate call to lazy % format.

    Returns (new_line, exprs) or (None, []) if no conversion.
    """
    # Find f-string in the line
    m = re.search(r'f(["\'])', match_line)
    if not m:
        return None, []

    quote = m.group(1)
    # Find the full f-string content
    start = m.end()  # right after f"
    # Walk to find matching closing quote (handle escaped quotes)
    i = start
    depth = 0
    end = -1
    while i < len(match_line):
        c = match_line[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == quote and depth == 0:
            end = i
            break
        i += 1
    if end == -1:
        return None, []

    fmt_str = match_line[start:end]

    # Convert {expr} → %s, collecting exprs
    exprs = []

    def replacer(m2):
        inner = m2.group(1)
        # Handle format specs like {var:.2f} or {var!r}
        # Split on : or !
        base_expr = re.split(r"[:!]", inner, 1)[0].strip()
        exprs.append(base_expr)
        # Preserve format spec if present
        fmt_spec_m = re.match(r"[^:!*]+([:!][^}]+)", inner)
        spec = fmt_spec_m.group(1) if fmt_spec_m else ""
        # Convert :.2f → %(.2f)s, !r → %r
        if spec.startswith(":"):
            return f"%({base_expr}){spec[1:]}s" if spec[1:] else "%s"
        elif spec.startswith("!r"):
            return f"%({base_expr})r"
        return "%s"

    new_fmt = re.sub(r"\{([^}]+)\}", replacer, fmt_str)

    if not exprs:
        return None, []

    # Build the new line
    old_str = f"f{quote}{fmt_str}{quote}"
    new_str = f"{quote}{new_fmt}{quote}"
    new_line = match_line.replace(old_str, new_str, 1)

    return new_line, exprs


def fix_file(filepath, file_entries):
    """Apply all fixes to a single file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    modified = False

    # Process codes in reverse line order to preserve line numbers
    all_fixes = []  # (lineno, code)

    for code, locations in file_entries.items():
        for relpath, lineno in locations:
            all_fixes.append((lineno, code))

    # Sort by lineno descending (process bottom-up)
    all_fixes.sort(key=lambda x: -x[0])

    for lineno, code in all_fixes:
        idx = lineno - 1
        if idx >= len(lines):
            continue
        line = lines[idx]

        if code in ("W1203", "W1201"):
            # Logger f-string → lazy % format
            if not LOGGER_RE.match(line):
                continue
            new_line, exprs = fstring_to_lazy(line)
            if new_line is None:
                continue
            # Add the exprs as arguments before the closing )
            # Find the last ) on the line
            last_paren = new_line.rfind(")")
            if last_paren == -1:
                continue
            before = new_line[:last_paren]
            after = new_line[last_paren:]
            # Check if there are existing args (comma after string)
            before_stripped = before.rstrip()
            if before_stripped.endswith((",", "(")):
                # Empty args or trailing comma
                if before_stripped.endswith("("):
                    args_part = ", ".join(exprs)
                else:
                    # trailing comma, just add args
                    args_part = " ".join(exprs)
            else:
                args_part = ", " + ", ".join(exprs)
            new_line = before_stripped + args_part + after
            lines[idx] = new_line
            stats[code] += 1
            modified = True

        elif code == "W8116":
            # print() → _logger.info()
            m = re.match(r"^(\s*)print\((.*)\)\s*$", line)
            if not m:
                continue
            indent = m.group(1)
            args = m.group(2)
            # If file has no _logger, it needs to be added (handle separately)
            lines[idx] = f"{indent}_logger.info({args})"
            stats["W8116"] += 1
            modified = True

        elif code == "W0612":
            # Unused variable: prefix with _
            m = re.match(r"^(\s*)(\w+)(\s*=\s*.*)$", line)
            if not m:
                continue
            indent = m.group(1)
            varname = m.group(2)
            rest = m.group(3)
            if varname.startswith("_"):
                continue
            # Don't rename self, cls, or common names that might be used
            if varname in ("self", "cls", "_"):
                continue
            lines[idx] = f"{indent}_{varname}{rest}"
            stats["W0612"] += 1
            modified = True

    if modified:
        new_content = "\n".join(lines)
        # Ensure file ends with newline if original did
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"
        filepath.write_text(new_content, encoding="utf-8")
        stats["files_modified"] += 1


def add_logger_imports():
    """For files that now use _logger but lack import, add it."""
    for fp in ROOT.rglob("*.py"):
        if ".venv" in str(fp) or "__pycache__" in str(fp):
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "_logger.info(" not in content and "_logger.warning(" not in content:
            continue
        if "_logger = " in content:
            continue
        # Need to add logging import and _logger
        lines = content.split("\n")
        # Find insertion point: after docstring and existing imports
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    insert_idx = i + 1
                    continue
                in_docstring = True
                continue
            if in_docstring:
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = False
                    insert_idx = i + 1
                continue
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i + 1
            elif stripped == "" and insert_idx > 0:
                continue
            elif stripped and not stripped.startswith("#"):
                if insert_idx > 0:
                    break

        if "import logging" not in content:
            lines.insert(insert_idx, "import logging")
            insert_idx += 1
        lines.insert(insert_idx, "_logger = logging.getLogger(__name__)")
        lines.insert(insert_idx, "")
        fp.write_text("\n".join(lines), encoding="utf-8")
        stats["logger_imports_added"] += 1


def main():
    entries = parse_log()

    # Group by file and code
    by_file_code = defaultdict(lambda: defaultdict(list))
    for relpath, lineno, code in entries:
        by_file_code[relpath][code].append((relpath, lineno))

    # Process fixable codes only
    fixable_codes = {"W1203", "W1201", "W8116", "W0612"}

    for relpath, codes in by_file_code.items():
        # Filter to only fixable codes
        relevant = {c: locs for c, locs in codes.items() if c in fixable_codes}
        if not relevant:
            continue
        fp = ROOT / relpath.replace("\\", "/")
        if not fp.exists():
            continue
        fix_file(fp, relevant)

    # Add logger imports for files that need them
    add_logger_imports()

    print(f"Files modified: {stats.get('files_modified', 0)}")
    print(f"Logger imports added: {stats.get('logger_imports_added', 0)}")
    for code in sorted(k for k in stats if k not in ("files_modified", "logger_imports_added")):
        print(f"  {code}: {stats[code]} fixed")
    total = sum(v for k, v in stats.items() if k not in ("files_modified", "logger_imports_added"))
    print(f"Total findings fixed: {total}")


if __name__ == "__main__":
    main()
