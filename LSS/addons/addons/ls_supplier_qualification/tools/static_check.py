#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Offline consistency checks for the ls_supplier_qualification module.

This script performs the checks that do not need a running Odoo server or a
PostgreSQL database. It is a complement to flake8, pylint-odoo and the Odoo
test suite, not a replacement for them: see doc/13_static_analysis_report.md
for what it does and does not cover.

Usage::

    python3 tools/static_check.py [module_path]
"""
import ast
import csv
import os
import re
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


MAX_LINE_LENGTH = 88
FORBIDDEN_MARKERS = ("TODO", "FIXME", "XXX", "HACK")
VAGUE_TERMS = (" etc.", " and more", "miscellaneous", "similar features")


class Checker:
    """Collect and report the findings of every offline check."""

    def __init__(self, root):
        """Store the module root and prepare the finding list."""
        self.root = root
        self.findings = []

    # ------------------------------------------------------------------
    def error(self, path, message):
        """Record one finding."""
        self.findings.append("%s: %s" % (os.path.relpath(path, self.root), message))

    def walk(self, extension, skip_tools=True):
        """Yield every file of the module with the given extension.

        :param str extension: file suffix to select.
        :param bool skip_tools: exclude the ``tools`` directory, which holds
            this script and therefore contains the marker strings it looks
            for.
        """
        skipped = {"__pycache__"}
        if skip_tools:
            skipped.add("tools")
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in skipped]
            for filename in sorted(filenames):
                if filename.endswith(extension):
                    yield os.path.join(dirpath, filename)

    # ------------------------------------------------------------------
    def check_python_style(self):
        """Check line length, whitespace, markers and vague wording."""
        for path in self.walk(".py"):
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, start=1):
                    stripped = line.rstrip("\n")
                    if len(stripped) > MAX_LINE_LENGTH:
                        self.error(path, "line %s exceeds %s characters"
                                   % (number, MAX_LINE_LENGTH))
                    if stripped != stripped.rstrip():
                        self.error(path, "line %s has trailing whitespace" % number)
                    if "\t" in stripped:
                        self.error(path, "line %s contains a tab" % number)
                    for marker in FORBIDDEN_MARKERS:
                        if marker in stripped:
                            self.error(path, "line %s contains %s" % (number, marker))
                    for term in VAGUE_TERMS:
                        if term in stripped.lower():
                            self.error(path, "line %s uses vague wording '%s'"
                                       % (number, term.strip()))

    def check_python_ast(self):
        """Check docstrings, bare excepts and model descriptions."""
        for path in self.walk(".py"):
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            tree = ast.parse(source, filename=path)
            basename = os.path.basename(path)
            if not ast.get_docstring(tree) and basename not in (
                "__init__.py", "__manifest__.py",
            ):
                self.error(path, "module has no docstring")
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.error(path, "bare except at line %s" % node.lineno)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        self.error(path, "function %s at line %s has no docstring"
                                   % (node.name, node.lineno))
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        self.error(path, "class %s at line %s has no docstring"
                                   % (node.name, node.lineno))
                    self._check_model_class(path, node)

    def _check_model_class(self, path, node):
        """Require _description on every class that declares _name."""
        assignments = {
            target.id: child
            for child in node.body
            if isinstance(child, ast.Assign)
            for target in child.targets
            if isinstance(target, ast.Name)
        }
        if "_name" in assignments and "_description" not in assignments:
            self.error(path, "class %s declares _name without _description"
                       % node.name)

    def check_xml(self):
        """Check that every XML file is well formed."""
        for path in self.walk(".xml"):
            try:
                etree.parse(path)
            except etree.XMLSyntaxError as error:
                self.error(path, "invalid XML: %s" % error)

    # ------------------------------------------------------------------
    def collect_model_technical_names(self):
        """Return the set of _name values declared by the module."""
        names = set()
        for path in self.walk(".py"):
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                for child in node.body:
                    if not isinstance(child, ast.Assign):
                        continue
                    for target in child.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "_name"
                            and isinstance(child.value, ast.Constant)
                        ):
                            names.add(child.value.value)
        return names

    def collect_xml_ids(self):
        """Return every external identifier defined by the module data."""
        xml_ids = set()
        for path in self.walk(".xml"):
            tree = etree.parse(path)
            for element in tree.iter():
                identifier = element.get("id")
                if identifier:
                    xml_ids.add(identifier)
        return xml_ids

    def check_access_csv(self):
        """Check the access rights file against the declared models."""
        path = os.path.join(self.root, "security", "ir.model.access.csv")
        if not os.path.exists(path):
            self.error(path, "ir.model.access.csv is missing")
            return
        declared = self.collect_model_technical_names()
        expected_model_ids = {
            "model_" + name.replace(".", "_") for name in declared
        }
        covered = set()
        with open(path, encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                model_id = row["model_id:id"]
                if model_id.startswith("model_"):
                    covered.add(model_id)
                    if model_id not in expected_model_ids:
                        self.error(path, "unknown model reference %s" % model_id)
                for column in (
                    "perm_read", "perm_write", "perm_create", "perm_unlink"
                ):
                    if row[column] not in ("0", "1"):
                        self.error(path, "invalid %s value in row %s"
                                   % (column, row["id"]))
        for model_id in sorted(expected_model_ids - covered):
            self.error(path, "no access line for %s" % model_id)

    def check_manifest_files_exist(self):
        """Check that every file listed in the manifest is present."""
        path = os.path.join(self.root, "__manifest__.py")
        with open(path, encoding="utf-8") as handle:
            manifest = ast.literal_eval(handle.read())
        for key in ("data", "demo"):
            for relative in manifest.get(key, []):
                target = os.path.join(self.root, relative)
                if not os.path.exists(target):
                    self.error(path, "%s file not found: %s" % (key, relative))
        for relative in manifest.get("images", []):
            if not os.path.exists(os.path.join(self.root, relative)):
                self.error(path, "image not found: %s" % relative)
        return manifest

    def check_python_xml_id_references(self):
        """Check the module-local external identifiers used from Python."""
        module_name = os.path.basename(self.root.rstrip("/"))
        defined = self.collect_xml_ids()
        pattern = re.compile(r'"%s\.([a-zA-Z0-9_]+)"' % re.escape(module_name))
        for path in self.walk(".py"):
            if os.sep + "tests" + os.sep in path:
                continue
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            for match in pattern.finditer(content):
                if match.group(1) not in defined:
                    self.error(path, "unknown external identifier %s.%s"
                               % (module_name, match.group(1)))

    def check_view_tags(self):
        """Check that no deprecated <tree> tag remains in the views."""
        for path in self.walk(".xml"):
            tree = etree.parse(path)
            if tree.getroot().findall(".//tree"):
                self.error(path, "deprecated <tree> tag, use <list> from Odoo 18")
            for record in tree.getroot().findall(".//record"):
                if record.get("model") != "ir.actions.act_window":
                    continue
                for field in record.findall("field[@name='view_mode']"):
                    if "tree" in (field.text or ""):
                        self.error(path, "view_mode uses 'tree', use 'list'")

    # ------------------------------------------------------------------
    def run(self):
        """Run every check and return the process exit code."""
        self.check_python_style()
        self.check_python_ast()
        self.check_xml()
        self.check_access_csv()
        self.check_manifest_files_exist()
        self.check_python_xml_id_references()
        self.check_view_tags()
        if self.findings:
            _logger.info("STATIC CHECK: FAIL (%s finding(s))", len(self.findings))
            for finding in self.findings:
                _logger.info("  - %s", finding)
            return 1
        _logger.info("STATIC CHECK: PASS")
        return 0


def main():
    """Entry point of the command-line script."""
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    return Checker(root).run()


if __name__ == "__main__":
    sys.exit(main())
