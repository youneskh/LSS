#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Offline static checker for the ``ls_audit_trail`` module.

The build environment has no network access, so ``flake8``, ``pylint`` and
``pylint-odoo`` cannot be installed. This checker uses only the Python standard
library and ``lxml`` to validate the properties those tools would otherwise
catch. It is intentionally conservative: it reports a finding only when it is
certain, and it excludes its own source directory from the marker string scan so
that it does not flag itself.

The checker is *not* a substitute for installing the module against a live Odoo
19 instance. It cannot execute Odoo, so it cannot confirm that views render or
that constraints fire. Its verdict is therefore reported as a set of static
checks, never as a certification that the module works.

Usage::

    python3 devtools/static_check.py
"""

from __future__ import annotations

import ast
import csv
import os
import re
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


CHECKER_DIR = os.path.abspath(os.path.dirname(__file__))
MODULE_ROOT = os.path.dirname(CHECKER_DIR)

#: Substrings that must never appear in shipped source.
FORBIDDEN_MARKERS = ("TODO", "FIXME", "XXX", "pdb.set_trace", "breakpoint(")

#: Maximum line length enforced (Odoo guideline is 79 for Python).
MAX_PY_LINE = 88


class Findings:
    """Accumulate errors and warnings and render a verdict."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def report(self) -> int:
        """Print the findings and return a process exit code."""
        for warning in self.warnings:
            _logger.info("WARN  %s", warning)
        for error in self.errors:
            _logger.info("ERROR %s", error)
        _logger.info("-" * 60)
        _logger.info("%s error(s), %s warning(s)", len(self.errors), len(self.warnings))
        return 1 if self.errors else 0


def iter_files(extension: str):
    """Yield module files with ``extension``, excluding the checker directory."""
    for root, _dirs, files in os.walk(MODULE_ROOT):
        if os.path.abspath(root) == CHECKER_DIR:
            continue
        for name in files:
            if name.endswith(extension):
                yield os.path.join(root, name)


def check_python_syntax(findings: Findings) -> dict:
    """Parse every Python file and return the parsed trees.

    :param findings: accumulator for errors.
    :return: a mapping of file path to its parsed AST module.
    """
    trees = {}
    for path in iter_files(".py"):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        try:
            trees[path] = ast.parse(source, filename=path)
        except SyntaxError as error:
            findings.error(f"{path}: syntax error: {error}")
    return trees


def check_line_length(findings: Findings) -> None:
    """Warn about Python lines exceeding the configured maximum."""
    for path in iter_files(".py"):
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                stripped = line.rstrip("\n")
                if len(stripped) > MAX_PY_LINE:
                    findings.warning(
                        f"{path}:{number}: line longer than {MAX_PY_LINE} "
                        f"characters ({len(stripped)})"
                    )


def check_markers(findings: Findings) -> None:
    """Report forbidden markers in Python and XML source."""
    for extension in (".py", ".xml"):
        for path in iter_files(extension):
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, start=1):
                    for marker in FORBIDDEN_MARKERS:
                        if marker in line:
                            findings.error(
                                f"{path}:{number}: forbidden marker {marker!r}"
                            )


def check_docstrings(findings: Findings, trees: dict) -> None:
    """Warn about public functions and classes without a docstring."""
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                if ast.get_docstring(node) is None:
                    findings.warning(
                        f"{path}:{node.lineno}: {node.name} has no docstring"
                    )


def check_xml_wellformed(findings: Findings) -> list:
    """Parse every XML file and return the parsed trees.

    :param findings: accumulator for errors.
    :return: a list of ``(path, tree)`` tuples.
    """
    trees = []
    for path in iter_files(".xml"):
        try:
            trees.append((path, etree.parse(path)))
        except etree.XMLSyntaxError as error:
            findings.error(f"{path}: XML not well formed: {error}")
    return trees


def collect_model_names(trees: dict) -> set:
    """Return the set of model names declared with ``_name`` in the module."""
    names = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if "_name" in targets and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        names.add(node.value.value)
    return names


def check_manifest(findings: Findings) -> dict:
    """Validate the manifest and that every data file it lists exists.

    :param findings: accumulator for errors.
    :return: the parsed manifest dictionary, or an empty dictionary on failure.
    """
    manifest_path = os.path.join(MODULE_ROOT, "__manifest__.py")
    if not os.path.isfile(manifest_path):
        findings.error("__manifest__.py is missing")
        return {}
    with open(manifest_path, encoding="utf-8") as handle:
        try:
            manifest = ast.literal_eval(handle.read())
        except (ValueError, SyntaxError) as error:
            findings.error(f"__manifest__.py is not a literal dict: {error}")
            return {}
    for key in ("name", "version", "license", "depends", "data"):
        if key not in manifest:
            findings.error(f"__manifest__.py is missing the {key!r} key")
    version = manifest.get("version", "")
    if not re.match(r"^19\.0\.\d+\.\d+\.\d+$", version):
        findings.warning(
            f"__manifest__.py version {version!r} does not follow "
            "19.0.x.y.z"
        )
    for relative in manifest.get("data", []) + manifest.get("demo", []):
        if not os.path.isfile(os.path.join(MODULE_ROOT, relative)):
            findings.error(f"__manifest__.py lists missing data file {relative!r}")
    return manifest


def check_access_csv(findings: Findings, model_names: set) -> None:
    """Validate that the ACL file references models declared by the module."""
    acl_path = os.path.join(MODULE_ROOT, "security", "ir.model.access.csv")
    if not os.path.isfile(acl_path):
        findings.error("security/ir.model.access.csv is missing")
        return
    declared_refs = {"model_" + name.replace(".", "_") for name in model_names}
    covered = set()
    with open(acl_path, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "id",
            "name",
            "model_id:id",
            "group_id:id",
            "perm_read",
            "perm_write",
            "perm_create",
            "perm_unlink",
        }
        if set(reader.fieldnames or []) != required:
            findings.error(
                "security/ir.model.access.csv has unexpected columns: "
                f"{reader.fieldnames}"
            )
            return
        for row in reader:
            covered.add(row["model_id:id"])
            for permission in ("perm_read", "perm_write", "perm_create", "perm_unlink"):
                if row[permission] not in ("0", "1"):
                    findings.error(
                        f"ACL {row['id']!r}: {permission} must be 0 or 1"
                    )
    missing = declared_refs - covered
    for reference in sorted(missing):
        findings.warning(
            f"model {reference!r} has no entry in ir.model.access.csv"
        )


def check_immutability_guards(findings: Findings, trees: dict) -> None:
    """Confirm that the log and line models override write and unlink.

    This is a module specific invariant: the whole value of the audit trail
    depends on these overrides existing.
    """
    required = {
        "ls_audit_trail_log.py": {"write", "unlink"},
        "ls_audit_trail_log_line.py": {"write", "unlink"},
    }
    for path, tree in trees.items():
        base = os.path.basename(path)
        if base not in required:
            continue
        defined = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        }
        for method in required[base]:
            if method not in defined:
                findings.error(
                    f"{path}: expected an override of {method}() enforcing "
                    "immutability"
                )


def check_no_raw_sql_in_models(findings: Findings, trees: dict) -> None:
    """Warn about ``cr.execute`` outside the files where it is expected.

    Raw SQL is used deliberately in a few places, all documented: the log model
    reads the chain tail and takes the advisory lock, the purge wizard deletes
    rows the ORM refuses to delete, and the res.company compute reads a group
    aggregate. Any other occurrence is flagged for review.
    """
    allowed = {
        "ls_audit_trail_log.py",
        "ls_audit_trail_purge_wizard.py",
    }
    for path, tree in trees.items():
        base = os.path.basename(path)
        if base in allowed or base.startswith("test_"):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "execute":
                findings.warning(
                    f"{path}:{node.lineno}: cr.execute outside the documented "
                    "SQL sites; confirm it is parameterised and necessary"
                )


def check_sql_is_parameterised(findings: Findings, trees: dict) -> None:
    """Report any ``cr.execute`` whose first argument is an f-string or a %.

    Parameterised queries pass a tuple as the second argument. A query built by
    string formatting is a potential SQL injection and is reported as an error.
    """
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                continue
            if not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.JoinedStr):
                findings.error(
                    f"{path}:{node.lineno}: cr.execute called with an f-string"
                )
            if isinstance(first, ast.BinOp) and isinstance(first.op, ast.Mod):
                findings.error(
                    f"{path}:{node.lineno}: cr.execute called with % formatting"
                )


def _harvest_fields() -> dict:
    """Return a mapping of model name to the field names it declares.

    The inventory is built from the AST of the model and wizard packages, so it
    reflects exactly what the module defines, independent of any running Odoo.

    :return: a mapping of model name to a set of field names.
    """
    inventory: dict[str, set] = {}
    for package in ("models", "wizards"):
        directory = os.path.join(MODULE_ROOT, package)
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                model = _class_model_name(cls)
                if not model:
                    continue
                field_set = inventory.setdefault(model, set())
                field_set.update(_class_field_names(cls))
    return inventory


def _class_model_name(cls: ast.ClassDef):
    """Return the ``_name`` or ``_inherit`` string of a model class."""
    name = inherit = None
    for node in cls.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "_name" in targets and isinstance(node.value, ast.Constant):
                name = node.value.value
            if "_inherit" in targets and isinstance(node.value, ast.Constant):
                inherit = node.value.value
    return name or inherit


def _class_field_names(cls: ast.ClassDef) -> set:
    """Return the names of every ``fields.*`` assignment in a model class."""
    names = set()
    for node in cls.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "fields"
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
    return names


#: Fields provided by Odoo that the module uses in views without declaring.
COMMON_FIELDS = frozenset(
    {
        "id",
        "display_name",
        "create_date",
        "write_date",
        "create_uid",
        "write_uid",
        "active",
        "company_id",
        "message_ids",
        "message_follower_ids",
        "activity_ids",
        "message_main_attachment_id",
    }
)


def check_view_fields(findings: Findings, inventory: dict) -> None:
    """Confirm that every top-level view field exists on its model.

    Fields inside a relational subview belong to the comodel and cannot be
    validated from this module's inventory alone, so they are skipped. The arch
    container field itself is also skipped.
    """
    for path in iter_files(".xml"):
        for record in etree.parse(path).iter("record"):
            if record.get("model") != "ir.ui.view":
                continue
            model_field = record.find("./field[@name='model']")
            if model_field is None or not model_field.text:
                continue
            model = model_field.text
            if model not in inventory:
                continue
            known = inventory[model] | COMMON_FIELDS
            arch = record.find("./field[@name='arch']")
            if arch is None:
                continue
            for field in arch.iter("field"):
                if field is arch:
                    continue
                name = field.get("name")
                if not name:
                    continue
                if _is_nested_field(field, arch):
                    continue
                if name not in known:
                    findings.error(
                        f"{path}: view field {name!r} is not defined on {model}"
                    )


def _is_nested_field(field, arch) -> bool:
    """Return whether ``field`` is inside a relational subview under ``arch``."""
    ancestor = field.getparent()
    while ancestor is not None and ancestor is not arch:
        if ancestor.tag == "field":
            return True
        ancestor = ancestor.getparent()
    return False


def check_xml_id_references(findings: Findings, inventory: dict) -> None:
    """Confirm that ``ref``, ``parent`` and ``action`` resolve.

    A reference resolves when it names a record declared in the module, an
    implicit ``model_*`` identifier of a declared model, or one of the external
    identifiers the module legitimately depends on.
    """
    declared = set()
    for path in iter_files(".xml"):
        tree = etree.parse(path)
        for tag in ("record", "menuitem", "template", "report"):
            for element in tree.iter(tag):
                identifier = element.get("id")
                if identifier:
                    declared.add(identifier)
                    declared.add(f"ls_audit_trail.{identifier}")
    for model in inventory:
        implicit = "model_" + model.replace(".", "_")
        declared.add(implicit)
        declared.add(f"ls_audit_trail.{implicit}")

    for path in iter_files(".xml"):
        tree = etree.parse(path)
        for element in tree.iter():
            reference = element.get("ref")
            if reference and reference not in declared and reference not in KNOWN_EXTERNAL_IDS:
                findings.error(f"{path}: ref={reference!r} does not resolve")
        for menu in tree.iter("menuitem"):
            for attribute in ("parent", "action"):
                value = menu.get(attribute)
                if value and value not in declared and value not in KNOWN_EXTERNAL_IDS:
                    findings.error(
                        f"{path}: menuitem {attribute}={value!r} does not resolve"
                    )


#: External identifiers this module depends on. Kept explicit so that a typo in
#: a reference is caught rather than silently assumed to be external.
KNOWN_EXTERNAL_IDS = frozenset(
    {
        "base.model_res_partner",
        "base.field_res_partner__name",
        "base.field_res_partner__vat",
        "base.field_res_partner__email",
        "base.view_company_form",
        "base.group_multi_company",
        "base.be",
        "web.external_layout",
        "web.html_container",
    }
)


def main() -> int:
    """Run every check and print the verdict."""
    findings = Findings()
    trees = check_python_syntax(findings)
    check_line_length(findings)
    check_markers(findings)
    check_docstrings(findings, trees)
    check_xml_wellformed(findings)
    model_names = collect_model_names(trees)
    check_manifest(findings)
    check_access_csv(findings, model_names)
    check_immutability_guards(findings, trees)
    check_no_raw_sql_in_models(findings, trees)
    check_sql_is_parameterised(findings, trees)
    inventory = _harvest_fields()
    check_view_fields(findings, inventory)
    check_xml_id_references(findings, inventory)
    _logger.info("Discovered models: %s", ', '.join(sorted(model_names)))
    return findings.report()


if __name__ == "__main__":
    sys.exit(main())
