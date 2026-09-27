"""Additional Odoo-version and consistency checks for ls_complaint."""

import ast
import os
import re
import xml.etree.ElementTree as ET
import logging

_logger = logging.getLogger(__name__)


MODULE = "/home/claude/ls_complaint"
LEGACY = {
    r'\battrs\s*=': "attrs= was removed in Odoo 17",
    r'\bstates\s*=\s*"': 'states= view attribute was removed in Odoo 17',
    r"<tree[\s>]": "<tree> was renamed <list> in Odoo 18",
    r"</tree>": "</tree> was renamed </list> in Odoo 18",
    r"oe_chatter": "the oe_chatter div was replaced by <chatter/> in Odoo 18",
    r"name_get": "name_get was replaced by _compute_display_name in Odoo 17",
    r"\bnumbercall\b": "ir.cron.numbercall was removed in Odoo 17",
    r"stock\.production\.lot": "renamed stock.lot in Odoo 16",
    r"@api\.model\b(?!_create_multi)[\s\S]{0,80}def create\(":
        "create must use @api.model_create_multi",
}

errors = []
seen_ids = {}


def files(ext):
    """Yield every module file with the given extension, excluding tools."""
    for root, _dirs, names in os.walk(MODULE):
        if "/tools" in root:
            continue
        for name in sorted(names):
            if name.endswith(ext):
                yield os.path.join(root, name)


for path in list(files(".py")) + list(files(".xml")):
    content = open(path, encoding="utf-8").read()
    for pattern, message in LEGACY.items():
        for match in re.finditer(pattern, content):
            line = content[: match.start()].count("\n") + 1
            errors.append(f"{path}:{line}: {message}")

for path in files(".xml"):
    for element in ET.parse(path).iter():
        identifier = element.get("id")
        if identifier and element.tag in ("record", "template", "menuitem"):
            if identifier in seen_ids:
                errors.append(
                    f"{path}: duplicate XML id '{identifier}' "
                    f"(already in {seen_ids[identifier]})"
                )
            seen_ids[identifier] = path

model_fields = {}
for path in files(".py"):
    if "/tests/" in path:
        continue
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        name = None
        collected = set()
        for item in node.body:
            if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name):
                target = item.targets[0].id
                if target == "_name" and isinstance(item.value, ast.Constant):
                    name = item.value.value
                elif (
                    isinstance(item.value, ast.Call)
                    and isinstance(item.value.func, ast.Attribute)
                    and getattr(item.value.func.value, "id", "") == "fields"
                ):
                    collected.add(target)
        if name:
            model_fields[name] = collected

report = os.path.join(MODULE, "report/ls_complaint_report_templates.xml")
content = open(report, encoding="utf-8").read()
alias_model = {
    "doc": "ls.complaint",
    "investigation": "ls.complaint.investigation",
    "event": "ls.complaint.adverse_event",
    "resolution": "ls.complaint.resolution",
}
for alias, expression in re.findall(r't-field="(\w+)\.([\w.]+)"', content):
    model = alias_model.get(alias)
    if model is None:
        errors.append(f"{report}: unknown alias '{alias}'")
        continue
    root_field = expression.split(".")[0]
    if root_field not in model_fields.get(model, set()):
        errors.append(f"{report}: t-field {alias}.{expression} unknown on {model}")

_logger.info("xml ids checked : %s", len(seen_ids))
_logger.info("errors          : %s", len(errors))
for item in errors:
    _logger.info("ERROR  ", item)
raise SystemExit(1 if errors else 0)
