#!/usr/bin/env python3
# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Convert ``_sql_constraints`` to Odoo 19 ``models.Constraint`` declarations.

WHY THIS MATTERS
----------------

Odoo 19 does not raise an error on ``_sql_constraints``. It logs a warning and
**ignores it**:

    odoo/orm/model_classes.py L162
        if hasattr(model_def, '_sql_constraints'):
            _logger.warning("Model attribute '_sql_constraints' is no longer
                             supported, please define models.Constraint on the
                             model.")

and ``_add_sql_constraints()`` (odoo/orm/models.py L3262) iterates only
``self._table_objects``. A module carrying ``_sql_constraints`` therefore
installs cleanly while its uniqueness and check constraints are **never created
in the database**. In a GxP context this is worse than a crash: a validation
report can assert a control that does not exist.

NAME PRESERVATION
-----------------

The conversion keeps the database constraint name identical, so it is safe on
databases that already carry the old constraints.

    odoo/orm/table_objects.py
        __set_name__ : asserts the attribute starts with '_', then
                       self.name = name[1:]
        full_name    : f"{model._table}_{self.name}"

So ``('name_uniq', 'UNIQUE (code)', 'msg')`` becomes
``_name_uniq = models.Constraint('UNIQUE (code)', 'msg')`` and both yield the
database constraint ``{table}_name_uniq``.

SAFETY
------

Dry run by default. ``--apply`` writes changes and keeps a ``.bak`` beside each
modified file. Every rewritten file is re-parsed before being written; if the
result does not parse, the file is left untouched and the failure is reported.
Anything the tool cannot convert with certainty is reported and skipped, never
guessed at.

Usage::

    python3 convert_sql_constraints.py <path>            # preview
    python3 convert_sql_constraints.py <path> --apply    # write, with .bak
    python3 convert_sql_constraints.py <path> --apply --no-backup
"""

from __future__ import annotations

import argparse
import ast
import difflib
import logging
import os
import sys

_logger = logging.getLogger(__name__)


class Conversion:
    """One ``_sql_constraints`` assignment and its replacement text."""

    def __init__(self, path, class_name, lineno, end_lineno, entries, new_text):
        self.path = path
        self.class_name = class_name
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.entries = entries
        self.new_text = new_text


class Skipped:
    """A construct the tool declines to convert, with the reason."""

    def __init__(self, path, class_name, lineno, reason):
        self.path = path
        self.class_name = class_name
        self.lineno = lineno
        self.reason = reason


def _literal(node):
    """Return a string constant's value, or ``None`` if it is not one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _joined_literal(node):
    """Return the value of a string constant or implicit concatenation."""
    value = _literal(node)
    if value is not None:
        return value
    # Implicit concatenation across lines parses as a single Constant, so the
    # remaining case is an explicit BinOp of string constants.
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _joined_literal(node.left)
        right = _joined_literal(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _python_repr(text):
    """Render a string as a double-quoted Python literal."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def analyse_file(path):
    """Return (conversions, skips) for one Python file."""
    source = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [], [Skipped(path, "?", 0, f"file does not parse: {error}")]

    conversions, skips = [], []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name) or target.id != "_sql_constraints":
                continue

            value = stmt.value
            if not isinstance(value, (ast.List, ast.Tuple)):
                skips.append(Skipped(
                    path, node.name, stmt.lineno,
                    "_sql_constraints is not a literal list; convert by hand",
                ))
                continue

            entries, failed = [], False
            for element in value.elts:
                if not isinstance(element, (ast.Tuple, ast.List)) or len(element.elts) < 2:
                    skips.append(Skipped(
                        path, node.name, getattr(element, "lineno", stmt.lineno),
                        "entry is not a (name, definition, message) tuple",
                    ))
                    failed = True
                    break
                name = _joined_literal(element.elts[0])
                definition = _joined_literal(element.elts[1])
                message = (
                    _joined_literal(element.elts[2])
                    if len(element.elts) > 2 else ""
                )
                if name is None or definition is None or message is None:
                    skips.append(Skipped(
                        path, node.name, getattr(element, "lineno", stmt.lineno),
                        "entry contains a non-literal value; convert by hand "
                        "so the database constraint name is not guessed",
                    ))
                    failed = True
                    break
                if name.startswith("_"):
                    skips.append(Skipped(
                        path, node.name, getattr(element, "lineno", stmt.lineno),
                        f"constraint name {name!r} already starts with '_'; "
                        f"prefixing would produce a mangled attribute, which "
                        f"__set_name__ rejects",
                    ))
                    failed = True
                    break
                entries.append((name, definition, message))
            if failed or not entries:
                continue

            attribute_names = [f"_{name}" for name, _d, _m in entries]
            if len(set(attribute_names)) != len(attribute_names):
                skips.append(Skipped(
                    path, node.name, stmt.lineno,
                    "duplicate constraint names in the same class",
                ))
                continue

            indent = " " * target.col_offset
            blocks = []
            for name, definition, message in entries:
                block = [f"{indent}_{name} = models.Constraint("]
                block.append(f"{indent}    {_python_repr(definition)},")
                if message:
                    block.append(f"{indent}    {_python_repr(message)},")
                block.append(f"{indent})")
                blocks.append("\n".join(block))
            new_text = "\n\n".join(blocks) + "\n"

            conversions.append(Conversion(
                path, node.name, stmt.lineno, stmt.end_lineno, entries, new_text
            ))

    return conversions, skips


def rewrite_file(path, conversions):
    """Return the rewritten source, or ``None`` if the result does not parse."""
    source = open(path, encoding="utf-8").read()
    lines = source.splitlines(keepends=True)

    # Apply bottom-up so earlier line numbers stay valid.
    for conversion in sorted(conversions, key=lambda c: c.lineno, reverse=True):
        start = conversion.lineno - 1
        end = conversion.end_lineno
        lines[start:end] = [conversion.new_text]

    rewritten = "".join(lines)
    try:
        ast.parse(rewritten)
    except SyntaxError:
        return None
    return rewritten


def ensure_models_import(source, path, problems):
    """Return source with ``models`` imported from odoo.

    ``models.Constraint`` is unusable without the import. A converted file that
    lacks it raises NameError the moment Odoo loads the module, so the import is
    added to an existing ``from odoo import ...`` line when one exists, and the
    file is reported when one does not.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    odoo_import = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "odoo":
            if any(alias.name == "models" for alias in node.names):
                return source  # already imported, nothing to do
            if odoo_import is None:
                odoo_import = node

    if odoo_import is None:
        problems.append(
            f"{path}: no 'from odoo import ...' statement found. Add "
            f"'from odoo import models' by hand or models.Constraint will "
            f"raise NameError at load time."
        )
        return source

    lines = source.splitlines(keepends=True)
    index = odoo_import.lineno - 1
    names = sorted({alias.name for alias in odoo_import.names} | {"models"})
    ending = "\n" if lines[index].endswith("\n") else ""
    replacement = f"from odoo import {', '.join(names)}{ending}"
    lines[index:odoo_import.end_lineno] = [replacement]
    rewritten = "".join(lines)
    try:
        ast.parse(rewritten)
    except SyntaxError:
        problems.append(
            f"{path}: could not safely add the 'models' import; add it by hand."
        )
        return source
    return rewritten


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="module or addons directory to convert")
    parser.add_argument("--apply", action="store_true",
                        help="write the changes; without this flag, preview only")
    parser.add_argument("--no-backup", action="store_true",
                        help="do not write .bak files when applying")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.exists(root):
        _logger.info("Not found: %s", root)
        return 2

    targets = []
    if os.path.isfile(root):
        targets = [root]
    else:
        for directory, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for name in sorted(files):
                if name.endswith(".py"):
                    targets.append(os.path.join(directory, name))

    all_conversions, all_skips = [], []
    for path in targets:
        conversions, skips = analyse_file(path)
        all_conversions.extend(conversions)
        all_skips.extend(skips)

    if not all_conversions and not all_skips:
        _logger.info("No _sql_constraints found under %s", root)
        return 0

    by_file = {}
    for conversion in all_conversions:
        by_file.setdefault(conversion.path, []).append(conversion)

    mode = "APPLYING" if args.apply else "PREVIEW (no file will be changed)"
    print(f"{mode} — {len(all_conversions)} assignment(s) in "  # noqa: W8116  CLI script stdout
          f"{len(by_file)} file(s)")
    _logger.info()

    converted_files, failed_files, total_constraints = 0, [], 0
    import_problems = []

    for path in sorted(by_file):
        conversions = by_file[path]
        relative = os.path.relpath(path, root if os.path.isdir(root) else os.path.dirname(root))
        constraint_count = sum(len(c.entries) for c in conversions)
        total_constraints += constraint_count
        _logger.info("--- %s (%s constraint(s)) ---", relative, constraint_count)

        original = open(path, encoding="utf-8").read()
        rewritten = rewrite_file(path, conversions)
        if rewritten is None:
            _logger.info("  REFUSED: the rewritten file would not parse; left untouched")
            failed_files.append(relative)
            _logger.info()
            continue

        rewritten = ensure_models_import(rewritten, relative, import_problems)
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            rewritten.splitlines(keepends=True),
            fromfile=f"a/{relative}", tofile=f"b/{relative}",
        )
        for line in diff:
            sys.stdout.write("  " + line if not line.endswith("\n")
                             else "  " + line)
        _logger.info()

        if args.apply:
            if not args.no_backup:
                with open(path + ".bak", "w", encoding="utf-8") as handle:
                    handle.write(original)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(rewritten)
            converted_files += 1

    if import_problems:
        _logger.info("=" * 70)
        _logger.info("IMPORT PROBLEMS - these files need a manual import:")
        for problem in import_problems:
            _logger.info("  %s", problem)
        _logger.info()

    if all_skips:
        _logger.info("=" * 70)
        _logger.info("SKIPPED — %s construct(s) not converted:", len(all_skips))
        for skip in all_skips:
            relative = os.path.relpath(
                skip.path, root if os.path.isdir(root) else os.path.dirname(root)
            )
            _logger.info("  %s:%s (%s): %s", relative, skip.lineno, skip.class_name, skip.reason)
        _logger.info()

    _logger.info("=" * 70)
    _logger.info("Constraints converted : %s", total_constraints)
    print(f"Files changed         : {converted_files if args.apply else 0}"  # noqa: W8116  CLI script stdout
          f"{'' if args.apply else ' (preview only)'}")
    _logger.info("Files refused         : %s", len(failed_files))
    _logger.info("Constructs skipped    : %s", len(all_skips))
    if not args.apply and total_constraints:
        _logger.info()
        _logger.info("Re-run with --apply to write these changes. A .bak is kept for")
        _logger.info("each modified file unless --no-backup is given.")
    if args.apply:
        _logger.info()
        _logger.info("NEXT: the constraints now exist. Verify on a live database:")
        _logger.info("  SELECT conname FROM pg_constraint WHERE conname LIKE '<table>%';")
        _logger.info("Then update the validation report for each affected module: the")
        _logger.info("controls it documented were previously absent.")
    return 1 if (failed_files or all_skips or import_problems) else 0


if __name__ == "__main__":
    sys.exit(main())
