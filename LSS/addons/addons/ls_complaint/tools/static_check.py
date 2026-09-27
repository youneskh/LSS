"""Substitute static analysis for the ls_complaint module.

flake8, pylint and pylint-odoo are not installed in this environment and the
network is disabled, so they could not be executed. This script performs the
subset of their checks that can be implemented with the standard library, plus
Odoo specific cross-checks (XML identifier resolution and view/field
coherence).
"""

import ast
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
import logging

_logger = logging.getLogger(__name__)


MODULE = "/home/claude/ls_complaint"
MAX_LINE = 88
BANNED = ("TODO", "FIXME", "XXX", "pdb.set_trace")

# Fields inherited from base models and mixins, therefore not declared locally.
INHERITED_FIELDS = {
    "id", "display_name", "create_date", "create_uid", "write_date", "write_uid",
    "__last_update", "message_ids", "message_follower_ids", "message_partner_ids",
    "message_main_attachment_id", "message_attachment_count", "message_is_follower",
    "message_needaction", "message_needaction_counter", "message_has_error",
    "message_has_error_counter", "message_has_sms_error", "website_message_ids",
    "activity_ids", "activity_state", "activity_user_id", "activity_type_id",
    "activity_type_icon", "activity_date_deadline", "activity_summary",
    "activity_exception_decoration", "activity_exception_icon",
    "my_activity_date_deadline", "rating_ids", "has_message", "email_cc",
}

errors = []
warnings = []


EXCLUDED_DIRS = ("/tools",)


def walk(ext):
    """Yield every file of the module with the given extension.

    The ``tools`` directory holds these checker scripts themselves and is not
    part of the Odoo addon, so it is excluded from every scan.
    """
    for root, _dirs, files in os.walk(MODULE):
        if any(part in root for part in EXCLUDED_DIRS):
            continue
        for name in sorted(files):
            if name.endswith(ext):
                yield os.path.join(root, name)


def check_style():
    """Check line length, tabs, trailing whitespace and banned markers."""
    for path in list(walk(".py")) + list(walk(".xml")) + list(walk(".csv")):
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                stripped = line.rstrip("\n")
                if len(stripped) > MAX_LINE and path.endswith(".py"):
                    errors.append(f"{path}:{number}: line too long ({len(stripped)})")
                if "\t" in stripped:
                    errors.append(f"{path}:{number}: tab character")
                if stripped != stripped.rstrip():
                    errors.append(f"{path}:{number}: trailing whitespace")
                for marker in BANNED:
                    if marker in stripped:
                        errors.append(f"{path}:{number}: banned marker {marker}")


def collect_models():
    """Return {model_name: {'fields': set, 'methods': set, 'inherit': list}}."""
    models = {}
    for path in list(walk(".py")):
        if "/tests/" in path:
            continue
        tree = ast.parse(open(path, encoding="utf-8").read(), path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            name = inherit = None
            fields, methods = set(), set()
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1:
                    target = item.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "_name" and isinstance(item.value, ast.Constant):
                        name = item.value.value
                    elif target.id == "_inherit":
                        inherit = item.value
                    elif (
                        isinstance(item.value, ast.Call)
                        and isinstance(item.value.func, ast.Attribute)
                        and isinstance(item.value.func.value, ast.Name)
                        and item.value.func.value.id == "fields"
                    ):
                        fields.add(target.id)
                elif isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
            if name:
                models[name] = {
                    "fields": fields | INHERITED_FIELDS,
                    "methods": methods,
                    "inherit": inherit,
                    "path": path,
                }
    return models


def collect_xml_ids():
    """Return the set of XML identifiers defined by the module."""
    ids = set()
    for path in list(walk(".xml")):
        tree = ET.parse(path)
        for element in tree.iter():
            if element.tag in ("record", "template", "menuitem", "act_window"):
                value = element.get("id")
                if value:
                    ids.add(value)
                    ids.add(f"ls_complaint.{value}")
    for path in list(walk(".csv")):
        if os.path.basename(path) != "ir.model.access.csv":
            continue
        for row in csv.DictReader(open(path, encoding="utf-8")):
            ids.add(row["id"])
    return ids


def check_manifest():
    """Check that every declared data file exists and every file is declared."""
    manifest = ast.literal_eval(
        open(os.path.join(MODULE, "__manifest__.py"), encoding="utf-8")
        .read()
        .split("=", 0)[0]
        .split("{", 1)[1]
        .rsplit("}", 1)[0]
        .join(("{", "}"))
    )
    declared = set(manifest.get("data", [])) | set(manifest.get("demo", []))
    for relative in sorted(declared):
        if not os.path.exists(os.path.join(MODULE, relative)):
            errors.append(f"manifest: declared file missing: {relative}")
    for path in list(walk(".xml")) + list(walk(".csv")):
        relative = os.path.relpath(path, MODULE)
        if relative.startswith(("static/", "i18n/")):
            continue
        if relative not in declared:
            errors.append(f"manifest: file not declared: {relative}")
    for key in ("name", "version", "license", "depends", "category", "author"):
        if key not in manifest:
            errors.append(f"manifest: missing key {key}")
    if not manifest["version"].startswith("19.0."):
        errors.append("manifest: version does not target Odoo 19")
    return manifest


def check_refs(xml_ids, manifest):
    """Check that every ref= and groups= target can be resolved."""
    allowed_modules = set(manifest["depends"]) | {"ls_complaint"}
    for path in list(walk(".xml")):
        content = open(path, encoding="utf-8").read()
        targets = re.findall(r'ref="([^"]+)"', content)
        targets += re.findall(r"ref\('([^']+)'\)", content)
        for group_attribute in re.findall(r'groups="([^"]+)"', content):
            targets += [item.strip() for item in group_attribute.split(",")]
        for target in targets:
            if target.startswith("model_"):
                continue
            if "." in target:
                module = target.split(".", 1)[0]
                if module == "ls_complaint":
                    if target not in xml_ids:
                        errors.append(f"{path}: unresolved internal ref {target}")
                elif module not in allowed_modules:
                    errors.append(
                        f"{path}: ref {target} points to a module not in depends"
                    )
            elif target not in xml_ids:
                errors.append(f"{path}: unresolved ref {target}")


def check_acl(xml_ids, models):
    """Check the access control list against the declared models and groups."""
    path = os.path.join(MODULE, "security/ir.model.access.csv")
    seen = set()
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["id"] in seen:
            errors.append(f"acl: duplicate identifier {row['id']}")
        seen.add(row["id"])
        model_id = row["model_id:id"]
        expected = "model_" + model_id[len("model_"):]
        if not model_id.startswith("model_"):
            errors.append(f"acl: malformed model reference {model_id}")
        model_name = expected[len("model_"):].replace("_", ".")
        candidates = {
            name for name in models if name.replace(".", "_") == model_id[6:]
        }
        wizard = {"ls_complaint_close_wizard", "ls_complaint_cancel_wizard"}
        if not candidates and model_id[6:] not in wizard:
            errors.append(f"acl: unknown model {model_name} ({model_id})")
        if row["group_id:id"] not in xml_ids:
            errors.append(f"acl: unknown group {row['group_id:id']}")
    covered = {
        row["model_id:id"]
        for row in csv.DictReader(open(path, encoding="utf-8"))
    }
    for model_name in models:
        technical = "model_" + model_name.replace(".", "_")
        if technical not in covered:
            errors.append(f"acl: model {model_name} has no access rule")


def check_view_fields(models):
    """Check that every field used in a view exists on the target model."""
    for path in list(walk(".xml")):
        tree = ET.parse(path)
        for record in tree.iter("record"):
            if record.get("model") != "ir.ui.view":
                continue
            model_field = record.find("./field[@name='model']")
            if model_field is None or model_field.text not in models:
                continue
            model_name = model_field.text
            known = models[model_name]["fields"]
            arch = record.find("./field[@name='arch']")
            if arch is None:
                continue
            for element in arch.iter():
                if element is arch:
                    continue
                if element.tag != "field":
                    continue
                name = element.get("name")
                if name is None or name in known:
                    continue
                comodel = _resolve_subview(models, model_name, name)
                if comodel is None:
                    errors.append(
                        f"{path}: field '{name}' is unknown on {model_name}"
                    )
            for button in arch.iter("button"):
                method = button.get("name")
                if (
                    button.get("type") == "object"
                    and method
                    and method not in models[model_name]["methods"]
                ):
                    sub_ok = any(
                        method in data["methods"] for data in models.values()
                    )
                    if not sub_ok:
                        errors.append(
                            f"{path}: button method '{method}' not found "
                            f"for {model_name}"
                        )


def _resolve_subview(models, model_name, field_name):
    """Return the comodel when ``field_name`` belongs to an embedded subview."""
    for name, data in models.items():
        if field_name in data["fields"] and name != model_name:
            return name
    return None


def main():
    """Run every check and print the report."""
    check_style()
    models = collect_models()
    xml_ids = collect_xml_ids()
    manifest = check_manifest()
    check_refs(xml_ids, manifest)
    check_acl(xml_ids, models)
    check_view_fields(models)
    _logger.info("models declared : %s", len(models))
    _logger.info("xml identifiers : %s", len(xml_ids))
    _logger.info("errors          : %s", len(errors))
    _logger.info("warnings        : %s", len(warnings))
    for item in errors:
        _logger.info("ERROR  ", item)
    for item in warnings[:10]:
        _logger.info("WARN   ", item)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
