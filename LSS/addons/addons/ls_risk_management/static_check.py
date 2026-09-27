#!/usr/bin/env python3
"""Offline static analysis of the ``ls_risk_management`` module.

No network access is available in the build environment, so ``flake8``,
``pylint`` and ``pylint-odoo`` cannot be installed. This checker implements a
subset of their value using only the Python standard library and ``lxml``:

1.  Python files parse, and XML files are well formed.
2.  Every ``<field name="...">`` in a view resolves to a real field of the
    view's model, including fields inside embedded list and form views.
3.  Every ``name="..."`` on a view ``<button type="object">`` resolves to a
    real method.
4.  Every ``ref="..."`` resolves to an external identifier defined by this
    module or by a declared dependency prefix.
5.  Every model declared in Python is covered by at least one ACL line, and
    every ACL line names a real model and a real group.
6.  Every file listed in the manifest exists, and every data file on disk is
    listed in the manifest.
7.  No placeholder tokens, no raw SQL execution, no ``<tree>`` elements, no
    ``_sql_constraints``, and no browser storage calls.
8.  A PEP 8 subset: line length, trailing whitespace, tabs, and a final
    newline. Python files are held to the 100 character limit of the Odoo
    coding guidelines. XML files are held to a wider limit, because an XML
    data line carries human-readable content that cannot be wrapped without
    changing the value stored in the database.

Run from the module root::

    python3 static_check.py

Exit status is 0 when no finding is reported, and 1 otherwise.
"""

import ast
import csv
import os
import re
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


MODULE_NAME = "ls_risk_management"
MAX_PY_LINE_LENGTH = 100
MAX_XML_LINE_LENGTH = 150

#: Directories excluded from the marker-token scan, so that this checker's own
#: source and the generator's source do not trip their own rules.
SELF_EXCLUDED_FILES = {
    "static_check.py",
    "tools_generate_data.py",
    "tools_generate_docs.py",
    "negative_controls.py",
}

#: Tokens that must never appear in shipped source. Each is matched only when
#: it stands alone as an identifier, so that a legitimate name that merely
#: contains a marker word -- such as SEQUENCE_PLACEHOLDER or
#: ACTIVITY_TYPE_TODO_XMLID -- is not reported. Matching is case sensitive.
FORBIDDEN_TOKENS = [
    "TODO",
    "FIXME",
    "XXX",
    "PLACEHOLDER",
    "lorem ipsum",
    "localStorage",
    "sessionStorage",
    "_sql_constraints",
]

#: Compiled identifier-bounded patterns for :data:`FORBIDDEN_TOKENS`.
FORBIDDEN_PATTERNS = [
    (token, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])"))
    for token in FORBIDDEN_TOKENS
]

#: Raw SQL execution patterns that must not appear in shipped Python.
SQL_PATTERNS = [
    re.compile(r"\bself\._?cr\.execute\b"),
    re.compile(r"\benv\.cr\.execute\b"),
    re.compile(r"\bcursor\.execute\b"),
]

#: External identifier prefixes that may be referenced without being defined
#: in this module, because they come from a declared dependency.
ALLOWED_REF_PREFIXES = ("base.", "mail.", "web.")

#: Fields provided by mixins that this module inherits rather than declares.
INHERITED_FIELDS = {
    "display_name",
    "id",
    "create_date",
    "create_uid",
    "write_date",
    "write_uid",
    "message_ids",
    "message_follower_ids",
    "message_partner_ids",
    "message_attachment_count",
    "message_has_error",
    "message_needaction",
    "message_is_follower",
    "message_main_attachment_id",
    "activity_ids",
    "activity_state",
    "activity_user_id",
    "activity_type_id",
    "activity_date_deadline",
    "activity_summary",
    "activity_exception_decoration",
    "activity_exception_icon",
    "rating_ids",
    "website_message_ids",
    "has_message",
}

#: Methods provided by mixins or the base model.
INHERITED_METHODS = {
    "message_post",
    "activity_schedule",
    "toggle_active",
    "action_archive",
    "action_unarchive",
    "copy",
    "create",
    "write",
    "unlink",
    "read",
}

FINDINGS = []


def report(path, message, line=None):
    """Record a finding.

    :param str path: file the finding relates to.
    :param str message: description of the finding.
    :param int line: optional line number.
    """
    location = f"{path}:{line}" if line else path
    FINDINGS.append(f"{location}: {message}")


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------
def python_files():
    """Yield every shipped Python file path.

    :return: generator of relative paths.
    """
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.relpath(os.path.join(root, name), ".")


def xml_files():
    """Yield every shipped XML file path.

    :return: generator of relative paths.
    """
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        for name in sorted(files):
            if name.endswith(".xml"):
                yield os.path.relpath(os.path.join(root, name), ".")


def collect_models():
    """Parse the Python sources and build the model inventory.

    :return: mapping of model name to a dictionary with ``fields``,
        ``methods``, ``inherits`` and ``file`` keys.
    :rtype: dict
    """
    models = {}
    class_to_model = {}
    for path in python_files():
        try:
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        except SyntaxError as error:
            report(path, f"Python syntax error: {error}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            name = None
            inherits = []
            fields = set()
            methods = set()
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1:
                    target = item.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "_name" and isinstance(item.value, ast.Constant):
                        name = item.value.value
                    elif target.id == "_inherit":
                        if isinstance(item.value, ast.Constant):
                            inherits = [item.value.value]
                        elif isinstance(item.value, (ast.List, ast.Tuple)):
                            inherits = [
                                element.value
                                for element in item.value.elts
                                if isinstance(element, ast.Constant)
                            ]
                    elif isinstance(item.value, ast.Call):
                        func = item.value.func
                        if (
                            isinstance(func, ast.Attribute)
                            and isinstance(func.value, ast.Name)
                            and func.value.id == "fields"
                        ):
                            fields.add(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    fields.add(item.target.id)
                elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(item.name)
            if name:
                class_to_model[node.name] = name
                models[name] = {
                    "fields": fields,
                    "methods": methods,
                    "inherits": inherits,
                    "file": path,
                }
    return models


def resolve_fields(model, models):
    """Return every field visible on a model, following module-local mixins.

    :param str model: model name.
    :param dict models: model inventory.
    :return: set of field names.
    :rtype: set
    """
    seen = set(INHERITED_FIELDS)
    pending = [model]
    visited = set()
    while pending:
        current = pending.pop()
        if current in visited or current not in models:
            continue
        visited.add(current)
        seen |= models[current]["fields"]
        pending.extend(models[current]["inherits"])
    return seen


def resolve_methods(model, models):
    """Return every method visible on a model, following module-local mixins.

    :param str model: model name.
    :param dict models: model inventory.
    :return: set of method names.
    :rtype: set
    """
    seen = set(INHERITED_METHODS)
    pending = [model]
    visited = set()
    while pending:
        current = pending.pop()
        if current in visited or current not in models:
            continue
        visited.add(current)
        seen |= models[current]["methods"]
        pending.extend(models[current]["inherits"])
    return seen


def collect_xml_ids():
    """Collect every external identifier defined by this module.

    :return: set of identifiers, both bare and module-qualified.
    :rtype: set
    """
    ids = set()
    for path in xml_files():
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError as error:
            report(path, f"XML syntax error: {error}")
            continue
        for element in tree.iter():
            if element.tag in ("record", "template", "menuitem", "report"):
                value = element.get("id")
                if value:
                    ids.add(value)
                    ids.add(f"{MODULE_NAME}.{value}")
    csv_path = os.path.join("security", "ir.model.access.csv")
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                ids.add(row["id"])
                ids.add(f"{MODULE_NAME}.{row['id']}")
    # Auto-generated model identifiers, created by the ORM for each model.
    for model in collect_models():
        technical = "model_" + model.replace(".", "_")
        ids.add(technical)
        ids.add(f"{MODULE_NAME}.{technical}")
    return ids


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_view_fields(models):
    """Verify that view fields and object buttons resolve on their model."""
    for path in xml_files():
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError:
            continue
        for record in tree.iter("record"):
            if record.get("model") != "ir.ui.view":
                continue
            model_node = record.find("field[@name='model']")
            if model_node is None or not model_node.text:
                continue
            model = model_node.text.strip()
            if model not in models:
                continue
            arch = record.find("field[@name='arch']")
            if arch is None:
                continue
            _walk_arch(arch, model, models, path)


def _walk_arch(node, model, models, path):
    """Recursively validate an arch subtree against a model.

    Descending into a relational field switches the model context, so that
    fields of an embedded list are checked against the related model.

    :param node: XML element to inspect.
    :param str model: model the current context refers to.
    :param dict models: model inventory.
    :param str path: file being checked, used in findings.
    """
    valid_fields = resolve_fields(model, models)
    valid_methods = resolve_methods(model, models)
    for child in node:
        if not isinstance(child.tag, str):
            continue
        if child.tag == "field":
            name = child.get("name")
            if name and name not in valid_fields:
                report(
                    path,
                    f"view field '{name}' does not exist on model '{model}'",
                    child.sourceline,
                )
            nested_model = _relational_target(model, name, models)
            if len(child) and nested_model:
                _walk_arch(child, nested_model, models, path)
            elif len(child):
                _walk_arch(child, model, models, path)
            continue
        if child.tag == "button" and child.get("type") == "object":
            name = child.get("name")
            if name and name not in valid_methods:
                report(
                    path,
                    f"button method '{name}' does not exist on model '{model}'",
                    child.sourceline,
                )
        if child.tag == "tree":
            report(
                path,
                "'<tree>' was renamed to '<list>' in Odoo 18 and must not be used",
                child.sourceline,
            )
        _walk_arch(child, model, models, path)


#: Relational field targets, derived from the model sources at import time.
RELATIONAL_TARGETS = {}


def build_relational_targets():
    """Populate :data:`RELATIONAL_TARGETS` from the Python sources."""
    for path in python_files():
        try:
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            model = None
            for item in node.body:
                if (
                    isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                    and item.targets[0].id == "_name"
                    and isinstance(item.value, ast.Constant)
                ):
                    model = item.value.value
            if not model:
                continue
            for item in node.body:
                if not (
                    isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                    and isinstance(item.value, ast.Call)
                ):
                    continue
                func = item.value.func
                if not (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "fields"
                ):
                    continue
                if func.attr not in ("Many2one", "One2many", "Many2many"):
                    continue
                target = None
                for keyword in item.value.keywords:
                    if keyword.arg == "comodel_name" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        target = keyword.value.value
                if target is None and item.value.args:
                    first = item.value.args[0]
                    if isinstance(first, ast.Constant):
                        target = first.value
                if target:
                    RELATIONAL_TARGETS[(model, item.targets[0].id)] = target


def _relational_target(model, field_name, models):
    """Return the model a relational field points at, if module-local.

    :param str model: owning model.
    :param str field_name: field name.
    :param dict models: model inventory.
    :return: target model name, or ``None``.
    :rtype: str or None
    """
    pending = [model]
    visited = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        target = RELATIONAL_TARGETS.get((current, field_name))
        if target:
            return target if target in models else None
        if current in models:
            pending.extend(models[current]["inherits"])
    return None


def check_xml_refs(known_ids):
    """Verify that every ref and groups attribute resolves."""
    for path in xml_files():
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError:
            continue
        for element in tree.iter():
            if not isinstance(element.tag, str):
                continue
            ref = element.get("ref")
            if ref and ref not in known_ids:
                if not ref.startswith(ALLOWED_REF_PREFIXES):
                    report(path, f"unresolved ref '{ref}'", element.sourceline)
            groups = element.get("groups")
            if groups:
                for group in groups.split(","):
                    group = group.strip()
                    if not group or group.startswith("!"):
                        continue
                    if group not in known_ids and not group.startswith(
                        ALLOWED_REF_PREFIXES
                    ):
                        report(
                            path,
                            f"unresolved group '{group}'",
                            element.sourceline,
                        )
            for attribute in ("parent", "action"):
                value = element.get(attribute)
                if value and value not in known_ids:
                    if not value.startswith(ALLOWED_REF_PREFIXES):
                        report(
                            path,
                            f"unresolved {attribute} '{value}'",
                            element.sourceline,
                        )


def check_acl(models, known_ids):
    """Verify ACL coverage and that each ACL line resolves."""
    csv_path = os.path.join("security", "ir.model.access.csv")
    if not os.path.exists(csv_path):
        report(csv_path, "access control list file is missing")
        return
    covered = set()
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = {
            "id",
            "name",
            "model_id:id",
            "group_id:id",
            "perm_read",
            "perm_write",
            "perm_create",
            "perm_unlink",
        }
        if set(reader.fieldnames or []) != expected:
            report(csv_path, f"unexpected columns: {reader.fieldnames}")
            return
        for index, row in enumerate(reader, start=2):
            technical = row["model_id:id"]
            model = technical.replace("model_", "", 1).replace("_", ".")
            if model not in models:
                report(csv_path, f"ACL references unknown model '{model}'", index)
            else:
                covered.add(model)
            group = row["group_id:id"]
            if group and group not in known_ids:
                report(csv_path, f"ACL references unknown group '{group}'", index)
            for permission in (
                "perm_read",
                "perm_write",
                "perm_create",
                "perm_unlink",
            ):
                if row[permission] not in ("0", "1"):
                    report(
                        csv_path,
                        f"{permission} must be 0 or 1, found '{row[permission]}'",
                        index,
                    )
    for model in sorted(models):
        if model == "ls.risk.role.mixin":
            continue
        if model not in covered:
            report(csv_path, f"model '{model}' has no ACL line")


def check_manifest():
    """Verify that manifest data files exist and that none are missing."""
    manifest_path = "__manifest__.py"
    if not os.path.exists(manifest_path):
        report(manifest_path, "manifest is missing")
        return
    manifest = ast.literal_eval(open(manifest_path, encoding="utf-8").read())
    for key in ("name", "version", "license", "depends", "data", "author"):
        if key not in manifest:
            report(manifest_path, f"manifest is missing the '{key}' key")
    version = manifest.get("version", "")
    if not re.match(r"^19\.0\.\d+\.\d+\.\d+$", version):
        report(manifest_path, f"version '{version}' is not of the form 19.0.x.y.z")
    listed = list(manifest.get("data", [])) + list(manifest.get("demo", []))
    for relative in listed:
        if not os.path.exists(relative):
            report(manifest_path, f"listed file does not exist: {relative}")
    on_disk = set()
    for directory in ("data", "demo", "security", "views", "report", "wizards"):
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if name.endswith((".xml", ".csv")):
                on_disk.add(os.path.join(directory, name))
    for relative in sorted(on_disk - set(listed)):
        report(manifest_path, f"file on disk is not listed in the manifest: {relative}")


def check_tokens_and_style():
    """Check forbidden tokens, raw SQL and the PEP 8 subset."""
    for path in list(python_files()) + list(xml_files()):
        basename = os.path.basename(path)
        content = open(path, encoding="utf-8").read()
        lines = content.splitlines()
        if basename not in SELF_EXCLUDED_FILES:
            for token, pattern in FORBIDDEN_PATTERNS:
                for index, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        report(path, f"forbidden token '{token}'", index)
        if path.endswith(".py") and basename not in SELF_EXCLUDED_FILES:
            for pattern in SQL_PATTERNS:
                for index, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        report(path, "raw SQL execution is not permitted", index)
        limit = MAX_PY_LINE_LENGTH if path.endswith(".py") else MAX_XML_LINE_LENGTH
        for index, line in enumerate(lines, start=1):
            if len(line) > limit:
                report(path, f"line exceeds {limit} characters", index)
            if line != line.rstrip():
                report(path, "trailing whitespace", index)
            if "\t" in line:
                report(path, "tab character", index)
        if content and not content.endswith("\n"):
            report(path, "file does not end with a newline")


def check_translation_calls():
    """Verify that the Odoo 19 translation helper is used consistently."""
    pattern = re.compile(r"(?<![\w.])_\(")
    for path in python_files():
        if os.path.basename(path) in SELF_EXCLUDED_FILES:
            continue
        for index, line in enumerate(
            open(path, encoding="utf-8").read().splitlines(), start=1
        ):
            if pattern.search(line):
                report(
                    path,
                    "use self.env._() rather than the bare _() helper",
                    index,
                )


def main():
    """Run every check and print the findings.

    :return: process exit status.
    :rtype: int
    """
    models = collect_models()
    build_relational_targets()
    known_ids = collect_xml_ids()
    check_view_fields(models)
    check_xml_refs(known_ids)
    check_acl(models, known_ids)
    check_manifest()
    check_tokens_and_style()
    check_translation_calls()

    _logger.info("Models discovered: %s", len(models))
    _logger.info("External identifiers discovered: %s", len(known_ids))
    _logger.info("Relational fields mapped: %s", len(RELATIONAL_TARGETS))
    if FINDINGS:
        _logger.info("\n%s finding(s):", len(FINDINGS))
        for finding in FINDINGS:
            _logger.info("  %s", finding)
        return 1
    _logger.info("\nNo findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
