#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Regenerate ``docs/API_REFERENCE.md`` from the module sources.

Run from the module root::

    python3 docs/gen_api_reference.py

The reference is derived from the abstract syntax tree of the model and
wizard modules, so it cannot drift from the implementation. Nothing is
transcribed by hand.
"""

import ast
import glob
import io
import os
import logging

_logger = logging.getLogger(__name__)


INTERESTING_ATTRS = (
    "comodel_name",
    "required",
    "readonly",
    "store",
    "compute",
    "related",
    "tracking",
    "default",
    "index",
)

META_KEYS = ("_description", "_inherit", "_order", "_rec_name")


def render_value(node):
    """Render an AST value node as a short display string.

    :param node: the AST node to render.
    :return: a compact textual representation.
    :rtype: str
    """
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.List):
        return "[...]"
    if isinstance(node, ast.Lambda):
        return "lambda"
    if isinstance(node, ast.Call):
        func = node.func
        name = getattr(func, "attr", None) or getattr(func, "id", "?")
        return "%s(...)" % name
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive only
        return "?"


def collect(path):
    """Extract model metadata, fields and methods from one source file.

    :param str path: path to the Python source file.
    :return: list of ``(meta, fields, methods, class_name, docstring)``.
    :rtype: list
    """
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    results = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        meta = {}
        fields = []
        methods = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and isinstance(
                stmt.targets[0], ast.Name
            ):
                target = stmt.targets[0].id
                if target.startswith("_"):
                    meta[target] = render_value(stmt.value)
                elif (
                    isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and getattr(stmt.value.func.value, "id", "") == "fields"
                ):
                    keywords = {
                        kw.arg: render_value(kw.value)
                        for kw in stmt.value.keywords
                        if kw.arg
                    }
                    fields.append(
                        (target, stmt.value.func.attr, keywords)
                    )
            elif isinstance(stmt, ast.FunctionDef):
                methods.append(
                    (
                        stmt.name,
                        [a.arg for a in stmt.args.args],
                        [ast.unparse(d) for d in stmt.decorator_list],
                        (ast.get_docstring(stmt) or "").split("\n")[0],
                    )
                )
        if "_name" in meta:
            results.append(
                (meta, fields, methods, node.name,
                 (ast.get_docstring(node) or "").strip())
            )
    return results


def main():
    """Write the API reference document to ``docs/API_REFERENCE.md``."""
    out = io.StringIO()
    out.write("# ls_capa — API Reference\n\n")
    out.write("**Generated from source.** This document is produced by "
              "parsing the\nmodule's Python sources with `ast`, so field "
              "lists and signatures\ncannot drift from the code. Regenerate "
              "with `docs/gen_api_reference.py`.\n\n")
    out.write("Odoo target: 19.0 Community. Module version: "
              "19.0.1.0.1.\n\n---\n\n")

    paths = sorted(glob.glob("models/*.py")) + sorted(
        glob.glob("wizards/*.py")
    )
    for path in paths:
        if path.endswith("__init__.py"):
            continue
        for meta, fields, methods, cls, doc in collect(path):
            model = meta["_name"].strip("'")
            out.write("## `%s`\n\n" % model)
            out.write("*Class* `%s` — `%s`\n\n" % (cls, path))
            if doc:
                out.write(doc.split("\n\n")[0].replace("\n", " ") + "\n\n")
            for key in META_KEYS:
                if key in meta:
                    out.write("- `%s` = %s\n" % (key, meta[key]))
            out.write("\n### Fields\n\n| Field | Type | Key attributes |\n")
            out.write("|---|---|---|\n")
            for name, ftype, keywords in fields:
                attrs = [
                    "%s=%s" % (a, keywords[a])
                    for a in INTERESTING_ATTRS
                    if a in keywords
                ]
                out.write(
                    "| `%s` | %s | %s |\n"
                    % (name, ftype, ", ".join(attrs) or "—")
                )
            public = [m for m in methods if not m[0].startswith("_")]
            internal = [m for m in methods if m[0].startswith("_")]
            for title, group in (
                ("Public methods", public),
                ("Internal methods", internal),
            ):
                if not group:
                    continue
                out.write("\n### %s\n\n" % title)
                for name, args, decorators, summary in group:
                    decos = " ".join("`@%s`" % d for d in decorators)
                    bullet = "- **`%s(%s)`** %s\n  %s\n" if title.startswith(
                        "Public"
                    ) else "- `%s(%s)` %s\n  %s\n"
                    out.write(bullet % (name, ", ".join(args), decos, summary))
            out.write("\n---\n\n")

    os.makedirs("docs", exist_ok=True)
    with open("docs/API_REFERENCE.md", "w", encoding="utf-8") as handle:
        handle.write(out.getvalue())
    _logger.info("docs/API_REFERENCE.md regenerated (%d chars)", len(out.getvalue()))


if __name__ == "__main__":
    main()
