#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Offline extraction of the translatable strings of the module.

The file produced by this script is a best-effort extraction performed without
a running Odoo server. Before a release, regenerate it with the official
exporter, which resolves inherited views, selection labels and model
descriptions that a static reader cannot see::

    odoo-bin -d <database> --i18n-export=i18n/ls_supplier_qualification.pot \\
        --modules=ls_supplier_qualification --stop-after-init

Usage::

    python3 tools/extract_pot.py [module_path]
"""
import ast
import os
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


XML_ATTRIBUTES = ("string", "help", "placeholder", "title", "confirm", "sum")


def python_strings(root):
    """Yield (path, line, text) for every translatable Python literal."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tools")]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            relative = os.path.relpath(path, root)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    yield from _from_call(node, relative)


def _from_call(node, relative):
    """Yield the translatable literals carried by one call node."""
    func = node.func
    if isinstance(func, ast.Name) and func.id == "_" and node.args:
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            yield relative, node.lineno, first.value
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.value.id != "fields":
            return
        for keyword in node.keywords:
            if keyword.arg not in ("string", "help"):
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(
                keyword.value.value, str
            ):
                yield relative, node.lineno, keyword.value.value


def xml_strings(root):
    """Yield (path, line, text) for every translatable XML attribute."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tools")]
        for filename in sorted(filenames):
            if not filename.endswith(".xml"):
                continue
            path = os.path.join(dirpath, filename)
            relative = os.path.relpath(path, root)
            tree = etree.parse(path)
            for element in tree.iter():
                if not isinstance(element.tag, str):
                    continue
                for attribute in XML_ATTRIBUTES:
                    value = element.get(attribute)
                    if value and not value.startswith("{{"):
                        yield relative, element.sourceline, value


def escape(text):
    """Escape one string for the PO format."""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def main():
    """Write the template file and report how many entries were written."""
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    entries = {}
    for source in (python_strings(root), xml_strings(root)):
        for relative, line, text in source:
            if not text.strip():
                continue
            entries.setdefault(text, []).append("%s:%s" % (relative, line))

    target = os.path.join(root, "i18n", "ls_supplier_qualification.pot")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(
            '# Translation template of ls_supplier_qualification.\n'
            '# This file is distributed under the same licence as the module.\n'
            '# Generated offline by tools/extract_pot.py. Regenerate it with\n'
            '# odoo-bin --i18n-export before a release.\n'
            '#\n'
            'msgid ""\n'
            'msgstr ""\n'
            '"Project-Id-Version: Odoo Server 19.0\\n"\n'
            '"Report-Msgid-Bugs-To: \\n"\n'
            '"Last-Translator: \\n"\n'
            '"Language-Team: \\n"\n'
            '"MIME-Version: 1.0\\n"\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Content-Transfer-Encoding: 8bit\\n"\n'
            '"Plural-Forms: \\n"\n'
        )
        for text in sorted(entries):
            handle.write("\n")
            for reference in sorted(set(entries[text]))[:8]:
                handle.write("#: %s\n" % reference)
            handle.write('msgid "%s"\n' % escape(text))
            handle.write('msgstr ""\n')
    _logger.info("Wrote %s entries to %s", len(entries), target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
