#!/usr/bin/env python3
"""Generate the translation template and the API reference offline.

Neither artefact can be produced by Odoo's own tooling in this build
environment, because no Odoo runtime is available. Both are therefore derived
from the sources with the standard library and ``lxml``.

The translation template is explicitly marked as offline-generated. It is a
starting point for translators and must be regenerated with Odoo's own export
before release, because only Odoo can resolve strings contributed by inherited
views and by the base model.

Run from the module root::

    python3 tools_generate_docs.py
"""

import ast
import os
from datetime import datetime, timezone

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


MODULE_NAME = "ls_risk_management"

MODEL_ORDER = [
    "ls.risk.category",
    "ls.risk.matrix",
    "ls.risk.matrix.level",
    "ls.risk.matrix.cell",
    "ls.risk.register",
    "ls.risk.assessment",
    "ls.risk.mitigation",
    "ls.risk.fmea",
    "ls.risk.fmea.line",
    "ls.risk.role.mixin",
    "ls.risk.assess.wizard",
    "ls.risk.residual.wizard",
    "ls.risk.close.wizard",
    "ls.risk.cancel.wizard",
    "ls.risk.assessment.cancel.wizard",
    "ls.risk.mitigation.cancel.wizard",
    "ls.risk.fmea.cancel.wizard",
]


def source_files():
    """Yield the Python files that declare models.

    :return: generator of relative paths.
    """
    for directory in ("models", "wizards"):
        for name in sorted(os.listdir(directory)):
            if name.endswith(".py") and name != "__init__.py":
                yield os.path.join(directory, name)


def constant(node):
    """Return the literal value of a node, or ``None``.

    :param node: AST node.
    :return: the literal value when the node is a constant.
    """
    return node.value if isinstance(node, ast.Constant) else None


def parse_models():
    """Build a structured inventory of the models from the sources.

    :return: list of dictionaries describing each model.
    :rtype: list
    """
    inventory = []
    for path in source_files():
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            info = {
                "class": node.name,
                "file": path,
                "name": None,
                "description": None,
                "inherit": [],
                "order": None,
                "transient": any(
                    isinstance(base, ast.Attribute)
                    and base.attr == "TransientModel"
                    for base in node.bases
                ),
                "abstract": any(
                    isinstance(base, ast.Attribute)
                    and base.attr == "AbstractModel"
                    for base in node.bases
                ),
                "docstring": ast.get_docstring(node) or "",
                "fields": [],
                "methods": [],
                "constraints": [],
            }
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1:
                    target = item.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "_name":
                        info["name"] = constant(item.value)
                    elif target.id == "_description":
                        info["description"] = constant(item.value)
                    elif target.id == "_order":
                        info["order"] = constant(item.value)
                    elif target.id == "_inherit":
                        if isinstance(item.value, ast.Constant):
                            info["inherit"] = [item.value.value]
                        elif isinstance(item.value, (ast.List, ast.Tuple)):
                            info["inherit"] = [
                                constant(element) for element in item.value.elts
                            ]
                    elif isinstance(item.value, ast.Call):
                        func = item.value.func
                        if not isinstance(func, ast.Attribute):
                            continue
                        if isinstance(func.value, ast.Name) and func.value.id == "fields":
                            info["fields"].append(_describe_field(target.id, item.value))
                        elif (
                            isinstance(func.value, ast.Name)
                            and func.value.id == "models"
                            and func.attr == "Constraint"
                        ):
                            args = [constant(arg) for arg in item.value.args]
                            info["constraints"].append(
                                {
                                    "name": target.id,
                                    "definition": args[0] if args else "",
                                    "message": args[1] if len(args) > 1 else "",
                                }
                            )
                elif isinstance(item, ast.FunctionDef):
                    if item.name.startswith("__"):
                        continue
                    info["methods"].append(
                        {
                            "name": item.name,
                            "args": [a.arg for a in item.args.args if a.arg != "self"],
                            "doc": (ast.get_docstring(item) or "").split("\n")[0],
                            "public": not item.name.startswith("_"),
                        }
                    )
            if info["name"]:
                inventory.append(info)
    return inventory


def _describe_field(name, call):
    """Describe a field definition node.

    :param str name: field name.
    :param call: the ``fields.X(...)`` call node.
    :return: dictionary describing the field.
    :rtype: dict
    """
    described = {
        "name": name,
        "type": call.func.attr,
        "string": None,
        "comodel": None,
        "required": False,
        "readonly": False,
        "store": None,
        "compute": None,
        "related": None,
        "help": None,
    }
    for keyword in call.keywords:
        value = constant(keyword.value)
        if keyword.arg in ("string", "comodel_name", "compute", "related", "help"):
            key = "comodel" if keyword.arg == "comodel_name" else keyword.arg
            described[key] = value
        elif keyword.arg in ("required", "readonly", "store"):
            described[keyword.arg] = value
    if described["comodel"] is None and call.args:
        described["comodel"] = constant(call.args[0])
    return described


def collect_translatable():
    """Collect translatable strings from the Python and XML sources.

    :return: sorted list of ``(string, occurrences)`` pairs.
    :rtype: list
    """
    strings = {}

    def record(text, location):
        if not text or not isinstance(text, str) or not text.strip():
            return
        strings.setdefault(text, set()).add(location)

    for path in source_files():
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_env_translate = (
                    isinstance(func, ast.Attribute)
                    and func.attr == "_"
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "env"
                )
                if is_env_translate and node.args:
                    record(constant(node.args[0]), f"{path}:{node.lineno}")
                if isinstance(func, ast.Attribute) and func.value.__class__ is ast.Name:
                    if getattr(func.value, "id", None) == "fields":
                        for keyword in node.keywords:
                            if keyword.arg in ("string", "help"):
                                record(
                                    constant(keyword.value), f"{path}:{node.lineno}"
                                )

    for directory in ("views", "wizards", "report", "security"):
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".xml"):
                continue
            path = os.path.join(directory, name)
            tree = etree.parse(path)
            for element in tree.iter():
                if not isinstance(element.tag, str):
                    continue
                for attribute in ("string", "name", "title", "confirm", "placeholder"):
                    if element.tag in ("menuitem",) and attribute == "name":
                        record(element.get(attribute), f"{path}:{element.sourceline}")
                    elif attribute != "name":
                        record(element.get(attribute), f"{path}:{element.sourceline}")
    return sorted((text, sorted(locations)) for text, locations in strings.items())


def write_pot(entries):
    """Write the translation template.

    :param list entries: output of :func:`collect_translatable`.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M+0000")
    lines = [
        "# Translation template for the Life Sciences Risk Management module.",
        "#",
        "# OFFLINE-GENERATED FILE.",
        "#",
        "# This template was produced by tools_generate_docs.py from the module",
        "# sources, because no Odoo runtime was available in the build",
        "# environment. It covers strings declared directly by this module. It",
        "# does NOT cover strings contributed by inherited views or by the base",
        "# model, which only Odoo's own export can resolve.",
        "#",
        "# Regenerate with Odoo's export before release:",
        "#   odoo-bin -d DATABASE --i18n-export=ls_risk_management.pot \\",
        "#            --modules=ls_risk_management --stop-after-init",
        "#",
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: Odoo Server 19.0\\n"',
        '"Report-Msgid-Bugs-To: \\n"',
        f'"POT-Creation-Date: {stamp}\\n"',
        f'"PO-Revision-Date: {stamp}\\n"',
        '"Last-Translator: \\n"',
        '"Language-Team: \\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: \\n"',
        '"Plural-Forms: \\n"',
        "",
    ]
    for text, locations in entries:
        for location in locations[:4]:
            lines.append(f"#: {MODULE_NAME}/{location}")
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        lines.append(f'msgid "{escaped}"')
        lines.append('msgstr ""')
        lines.append("")
    with open(os.path.join("i18n", f"{MODULE_NAME}.pot"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    _logger.info("Generated i18n/%s.pot with %s entries", MODULE_NAME, len(entries))


def write_api_reference(inventory):
    """Write the API reference document.

    :param list inventory: output of :func:`parse_models`.
    """
    by_name = {info["name"]: info for info in inventory}
    lines = [
        "# API Reference",
        "",
        "## Life Sciences Suite - Risk Management (`ls_risk_management`)",
        "",
        "This document is generated from the module sources by",
        "`tools_generate_docs.py` using the Python `ast` module. It reflects",
        "what the code actually declares rather than a hand-maintained list.",
        "",
        f"Models declared: **{len(inventory)}**.",
        "",
        "---",
        "",
    ]
    for model_name in MODEL_ORDER:
        info = by_name.get(model_name)
        if not info:
            continue
        kind = "Abstract" if info["abstract"] else (
            "Transient" if info["transient"] else "Persistent"
        )
        lines += [
            f"## `{info['name']}`",
            "",
            f"- **Class**: `{info['class']}` in `{info['file']}`",
            f"- **Kind**: {kind}",
            f"- **Description**: {info['description'] or 'not set'}",
        ]
        if info["inherit"]:
            lines.append(f"- **Inherits**: {', '.join(f'`{i}`' for i in info['inherit'])}")
        if info["order"]:
            lines.append(f"- **Order**: `{info['order']}`")
        lines.append("")
        if info["docstring"]:
            lines += [info["docstring"].split("\n")[0], ""]

        if info["fields"]:
            lines += [
                f"### Fields ({len(info['fields'])})",
                "",
                "| Field | Type | Label | Target | Req. | Stored compute / related |",
                "|---|---|---|---|---|---|",
            ]
            for field in info["fields"]:
                derived = ""
                if field["compute"]:
                    derived = f"compute `{field['compute']}`"
                    if field["store"]:
                        derived += ", stored"
                elif field["related"]:
                    derived = f"related `{field['related']}`"
                lines.append(
                    f"| `{field['name']}` | {field['type']} | "
                    f"{field['string'] or ''} | "
                    f"{'`' + field['comodel'] + '`' if field['comodel'] else ''} | "
                    f"{'yes' if field['required'] else ''} | {derived} |"
                )
            lines.append("")

        if info["constraints"]:
            lines += [
                f"### Database constraints ({len(info['constraints'])})",
                "",
                "| Name | Definition | Message |",
                "|---|---|---|",
            ]
            for constraint in info["constraints"]:
                lines.append(
                    f"| `{constraint['name']}` | `{constraint['definition']}` | "
                    f"{constraint['message']} |"
                )
            lines.append("")

        public = [m for m in info["methods"] if m["public"]]
        private = [m for m in info["methods"] if not m["public"]]
        if public:
            lines += [f"### Public methods ({len(public)})", ""]
            for method in public:
                signature = ", ".join(method["args"])
                lines.append(f"- `{method['name']}({signature})` - {method['doc']}")
            lines.append("")
        if private:
            lines += [f"### Internal methods ({len(private)})", ""]
            for method in private:
                signature = ", ".join(method["args"])
                lines.append(f"- `{method['name']}({signature})` - {method['doc']}")
            lines.append("")
        lines += ["---", ""]

    total_fields = sum(len(info["fields"]) for info in inventory)
    total_methods = sum(len(info["methods"]) for info in inventory)
    total_constraints = sum(len(info["constraints"]) for info in inventory)
    lines += [
        "## Totals",
        "",
        f"- Models: {len(inventory)}",
        f"- Fields: {total_fields}",
        f"- Methods: {total_methods}",
        f"- Database constraints: {total_constraints}",
        "",
    ]
    os.makedirs("doc", exist_ok=True)
    with open(os.path.join("doc", "API_REFERENCE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    _logger.info(
        "Generated doc/API_REFERENCE.md: %d models, %d fields, %d methods, %d constraints",
        len(inventory),
        total_fields,
        total_methods,
        total_constraints,
    )
    return total_fields, total_methods, total_constraints


def main():
    """Generate both artefacts."""
    inventory = parse_models()
    write_api_reference(inventory)
    write_pot(collect_translatable())


if __name__ == "__main__":
    main()
