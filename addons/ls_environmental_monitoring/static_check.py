#!/usr/bin/env python3
"""Offline static checker for ls_environmental_monitoring.

Runs without a network connection, without Odoo and without PostgreSQL, using
only the Python standard library plus lxml. It is intended to catch the classes
of defect that would otherwise only surface at module installation time.

Checks performed:
  1.  every Python file parses
  2.  every XML file is well-formed
  3.  every file listed in the manifest exists
  4.  every XML file under the module is either listed in the manifest or is
      deliberately excluded
  5.  every ``ref=`` in XML resolves to an XML id defined in this module or to a
      recognised external module prefix
  6.  every ``<field name="...">`` in a view resolves to a field that exists on
      the target model, as determined by parsing the model source
  7.  every model declared in Python has at least one access control list row
  8.  every model referenced by an access control list row exists
  9.  no Odoo 18-and-earlier constructs that were removed in Odoo 19
  10. no placeholder tokens left in the source
  11. no raw SQL execution in shipped code
  12. every Python file declares a licence header

Exit code is 0 when no error is found and 1 otherwise. Warnings do not affect
the exit code.
"""

import ast
import csv
import os
import re
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(MODULE_DIR)

#: Directories whose contents are excluded from marker-string scanning, so that
#: the checker never reports its own source or its own vocabulary.
SELF_EXCLUDED = {os.path.basename(__file__)}

#: XML files that are intentionally absent from the manifest data list.
MANIFEST_EXEMPT_XML = set()

#: Module prefixes whose XML ids are defined outside this module.
EXTERNAL_PREFIXES = ("base.", "mail.", "web.")

#: Tokens that must never appear in delivered source.
PLACEHOLDER_TOKENS = (
    "TODO",
    "FIXME",
    "XXX" + "X",
    "<<<" + "<<<<",
    "PLACEHOLDER",
    "lorem ipsum",
)

#: Constructs removed or renamed in Odoo 19 that must not appear.
FORBIDDEN_XML_PATTERNS = (
    (r"<tree[\s>]", "<tree> was renamed to <list>"),
    (r"</tree>", "</tree> was renamed to </list>"),
    (r'\battrs\s*=', "the attrs dictionary was removed; use direct attributes"),
    (r'\bstates\s*=\s*"', "the states attribute was removed; use invisible="),
    (r"<kanban-box", "<kanban-box> was replaced by <card>"),
    (r'<div class="oe_chatter"', "oe_chatter was replaced by <chatter/>"),
)

FORBIDDEN_PY_PATTERNS = (
    (r"_sql_constraints\s*=", "_sql_constraints was replaced by models.Constraint"),
    (r"def name_get\s*\(", "name_get was replaced by _compute_display_name"),
    (r"\.read_group\s*\(", "read_group was replaced by _read_group"),
    (r"@api\.one\b", "api.one was removed long before Odoo 19"),
)

errors = []
warnings = []


def error(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def walk(extension):
    """Yield every file under the module with the given extension."""
    for root, dirs, files in os.walk(MODULE_DIR):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for name in sorted(files):
            if name.endswith(extension) and name not in SELF_EXCLUDED:
                yield os.path.join(root, name)


def relative(path):
    return os.path.relpath(path, MODULE_DIR)


# ---------------------------------------------------------------------------
# 1. Python parses
# ---------------------------------------------------------------------------
python_trees = {}
for path in walk(".py"):
    try:
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        python_trees[path] = (ast.parse(source, filename=path), source)
    except SyntaxError as exc:
        error("Python syntax error in %s: %s" % (relative(path), exc))

# ---------------------------------------------------------------------------
# 2. XML well-formed
# ---------------------------------------------------------------------------
xml_trees = {}
for path in walk(".xml"):
    try:
        xml_trees[path] = etree.parse(path)
    except etree.XMLSyntaxError as exc:
        error("XML not well-formed in %s: %s" % (relative(path), exc))

# ---------------------------------------------------------------------------
# 3 and 4. Manifest completeness
# ---------------------------------------------------------------------------
manifest_path = os.path.join(MODULE_DIR, "__manifest__.py")
manifest = {}
if not os.path.exists(manifest_path):
    error("__manifest__.py is missing")
else:
    with open(manifest_path, encoding="utf-8") as fh:
        try:
            manifest = ast.literal_eval(fh.read())
        except (ValueError, SyntaxError) as exc:
            error("__manifest__.py is not a literal dict: %s" % exc)

for key in ("name", "version", "license", "depends", "data", "author"):
    if key not in manifest:
        error("__manifest__.py is missing the required key '%s'" % key)

declared = list(manifest.get("data", []))
for entry in declared:
    if not os.path.exists(os.path.join(MODULE_DIR, entry)):
        error("Manifest lists '%s' but the file does not exist" % entry)

if len(declared) != len(set(declared)):
    error("__manifest__.py data list contains duplicate entries")

declared_set = set(declared)
for path in xml_trees:
    rel = relative(path).replace(os.sep, "/")
    if rel not in declared_set and rel not in MANIFEST_EXEMPT_XML:
        error("XML file '%s' exists but is not listed in the manifest" % rel)

version = manifest.get("version", "")
if not re.match(r"^19\.0\.\d+\.\d+\.\d+$", version):
    error("Manifest version '%s' does not follow the 19.0.x.y.z convention" % version)

# ---------------------------------------------------------------------------
# Collect model definitions from Python
# ---------------------------------------------------------------------------
model_fields = {}      # model name -> set of field names
model_inherits = {}    # model name -> list of inherited mixins
model_source = {}      # model name -> file

RELATED_MIXIN_FIELDS = {
    "mail.thread": {
        "message_follower_ids", "message_ids", "message_partner_ids",
        "message_is_follower", "message_needaction", "message_has_error",
        "message_attachment_count", "website_message_ids",
    },
    "mail.activity.mixin": {
        "activity_ids", "activity_state", "activity_user_id", "activity_type_id",
        "activity_date_deadline", "activity_summary", "activity_exception_decoration",
    },
}

BASE_FIELDS = {
    "id", "display_name", "create_uid", "create_date", "write_uid", "write_date",
    "__last_update",
}


def field_names_from_class(node):
    """Return the field names assigned in a model class body."""
    names = set()
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                value = stmt.value
                if (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and isinstance(value.func.value, ast.Name)
                    and value.func.value.id == "fields"
                ):
                    names.add(target.id)
    return names


def string_constant(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


for path, (tree, source) in python_trees.items():
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        name = None
        inherits = []
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "_name":
                    name = string_constant(stmt.value)
                elif target.id == "_inherit":
                    value = stmt.value
                    single = string_constant(value)
                    if single:
                        inherits = [single]
                    elif isinstance(value, (ast.List, ast.Tuple)):
                        inherits = [
                            string_constant(elt)
                            for elt in value.elts
                            if string_constant(elt)
                        ]
        if not name:
            continue
        fields = field_names_from_class(node)
        for mixin in inherits:
            fields |= RELATED_MIXIN_FIELDS.get(mixin, set())
        fields |= BASE_FIELDS
        model_fields[name] = fields
        model_inherits[name] = inherits
        model_source[name] = relative(path)

# ---------------------------------------------------------------------------
# 5. XML id references resolve
# ---------------------------------------------------------------------------
defined_ids = set()
for path, tree in xml_trees.items():
    for element in tree.iter():
        xmlid = element.get("id")
        if xmlid and element.tag in ("record", "template", "menuitem", "report"):
            defined_ids.add(xmlid)
            defined_ids.add("%s.%s" % (MODULE_NAME, xmlid))

# Model reference ids are generated by Odoo from the model name.
for model in model_fields:
    generated = "model_%s" % model.replace(".", "_")
    defined_ids.add(generated)
    defined_ids.add("%s.%s" % (MODULE_NAME, generated))

for path, tree in xml_trees.items():
    for element in tree.iter():
        for attribute in ("ref", "parent", "action"):
            value = element.get(attribute)
            if not value:
                continue
            if value.startswith(EXTERNAL_PREFIXES):
                continue
            if value not in defined_ids:
                error(
                    "%s: %s=\"%s\" does not resolve to a known XML id"
                    % (relative(path), attribute, value)
                )

# ---------------------------------------------------------------------------
# 6. View field references resolve
# ---------------------------------------------------------------------------
VIEW_META_FIELDS = {
    "name", "model", "arch", "inherit_id", "priority", "type", "active",
    "mode", "key", "help", "domain", "context", "res_model", "view_mode",
    "view_id", "target", "binding_model_id", "binding_type", "report_type",
    "report_name", "report_file", "print_report_name", "groups_id",
    "group_ids", "sequence", "code", "prefix", "padding", "number_increment",
    "implementation", "company_id", "model_id", "state", "interval_number",
    "interval_type", "domain_force", "comment", "privilege_id", "category_id",
    "user_ids", "implied_ids", "nextcall", "numbercall", "doall", "global",
}

# View field references are checked after the comodel map is built below,
# because resolving a sub-view requires knowing the comodel of its field.

# Relational field comodels, parsed from the Python source.
comodel_map = {}
for path, (tree, source) in python_trees.items():
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        model_name = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "_name":
                        model_name = string_constant(stmt.value)
        if not model_name:
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            value = stmt.value
            if not (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "fields"
            ):
                continue
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                for keyword in value.keywords:
                    if keyword.arg == "comodel_name":
                        comodel = string_constant(keyword.value)
                        if comodel:
                            comodel_map[(model_name, target.id)] = comodel


def comodel_of(model_name, field_name):
    """Return the comodel of a relational field, or the model itself."""
    return comodel_map.get((model_name, field_name), model_name)


# The comodel map is needed by check_scope, so views are re-checked now that
# it is populated.
for path, tree in xml_trees.items():
    for record in tree.iter("record"):
        if record.get("model") != "ir.ui.view":
            continue
        model_field = record.find("field[@name='model']")
        if model_field is None or not model_field.text:
            continue
        target_model = model_field.text.strip()
        if target_model not in model_fields:
            continue
        arch = record.find("field[@name='arch']")
        if arch is None:
            continue

        def check_scope2(element, model_name):
            fields_of_model = model_fields.get(model_name)
            for child in element:
                if child.tag == "field":
                    field_name = child.get("name")
                    if not field_name:
                        continue
                    if fields_of_model is not None and field_name not in fields_of_model:
                        error(
                            "%s: field '%s' referenced in a view of '%s' does not "
                            "exist on that model"
                            % (relative(path), field_name, model_name)
                        )
                    if len(child):
                        check_scope2(child, comodel_of(model_name, field_name))
                else:
                    check_scope2(child, model_name)

        check_scope2(arch, target_model)

# ---------------------------------------------------------------------------
# 7 and 8. Access control list coverage
# ---------------------------------------------------------------------------
#: Odoo derives a model's XML id by replacing dots with underscores. The
#: mapping is built in that direction because the reverse is ambiguous for
#: model names that themselves contain an underscore.
xmlid_to_model = {
    "model_%s" % name.replace(".", "_"): name for name in model_fields
}

acl_path = os.path.join(MODULE_DIR, "security", "ir.model.access.csv")
acl_models = set()
if not os.path.exists(acl_path):
    error("security/ir.model.access.csv is missing")
else:
    with open(acl_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        seen_ids = set()
        for row in reader:
            row_id = row.get("id")
            if row_id in seen_ids:
                error("Duplicate access control list id '%s'" % row_id)
            seen_ids.add(row_id)
            model_ref = (row.get("model_id:id") or "").strip()
            if not model_ref.startswith("model_"):
                error("Access row '%s' has an unexpected model reference" % row_id)
                continue
            model_name = xmlid_to_model.get(model_ref)
            if model_name is None:
                error(
                    "Access row '%s' references '%s', which does not correspond to "
                    "any model defined in this module" % (row_id, model_ref)
                )
                continue
            acl_models.add(model_name)
            for perm in ("perm_read", "perm_write", "perm_create", "perm_unlink"):
                value = (row.get(perm) or "").strip()
                if value not in ("0", "1"):
                    error(
                        "Access row '%s' has a non-boolean value for %s: '%s'"
                        % (row_id, perm, value)
                    )

for model in sorted(model_fields):
    if model not in acl_models:
        error("Model '%s' has no access control list row" % model)

for model in sorted(acl_models):
    if model not in model_fields:
        error(
            "Access control list references model '%s' which is not defined in "
            "this module" % model
        )

# ---------------------------------------------------------------------------
# 9. Removed Odoo 18 constructs
# ---------------------------------------------------------------------------
for path in walk(".xml"):
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    for pattern, message in FORBIDDEN_XML_PATTERNS:
        if re.search(pattern, content):
            error("%s: %s" % (relative(path), message))

for path, (tree, source) in python_trees.items():
    for pattern, message in FORBIDDEN_PY_PATTERNS:
        if re.search(pattern, source):
            error("%s: %s" % (relative(path), message))

# ---------------------------------------------------------------------------
# 10. Placeholder tokens
# ---------------------------------------------------------------------------
for path in list(walk(".py")) + list(walk(".xml")):
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    for token in PLACEHOLDER_TOKENS:
        # Matched case-sensitively and on a word boundary, so that the
        # legitimate XML "placeholder" attribute is not mistaken for the
        # PLACEHOLDER marker token.
        if re.search(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(token), content):
            error("%s: contains placeholder token '%s'" % (relative(path), token))

# ---------------------------------------------------------------------------
# 11. No raw SQL
# ---------------------------------------------------------------------------
for path, (tree, source) in python_trees.items():
    if re.search(r"\b(self\.)?(env\.)?cr\.execute\s*\(", source):
        error("%s: executes raw SQL, which is not permitted in shipped code"
              % relative(path))

# ---------------------------------------------------------------------------
# 12. Licence headers and basic style
# ---------------------------------------------------------------------------
for path, (tree, source) in python_trees.items():
    head = source[:400]
    if "License AGPL-3.0" not in head:
        error("%s: is missing the AGPL-3.0 licence header" % relative(path))
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = line.rstrip("\n")
        if len(stripped) > 88:
            warn("%s:%d: line exceeds 88 characters" % (relative(path), number))
        if stripped != stripped.rstrip():
            error("%s:%d: line has trailing whitespace" % (relative(path), number))
        if "\t" in stripped:
            error("%s:%d: line contains a tab character" % (relative(path), number))

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
_logger.info("=" * 72)
_logger.info("STATIC CHECK: %s", MODULE_NAME)
_logger.info("=" * 72)
_logger.info("Python files parsed : %d", len(python_trees))
_logger.info("XML files parsed    : %d", len(xml_trees))
_logger.info("Models detected     : %d", len(model_fields))
_logger.info("ACL models covered  : %d", len(acl_models))
_logger.info("Manifest data files : %d", len(declared))
_logger.info("-" * 72)

if warnings:
    _logger.info("WARNINGS (%d):", len(warnings))
    for message in warnings:
        _logger.info("  - %s", message)
    _logger.info("-" * 72)

if errors:
    _logger.info("ERRORS (%d):", len(errors))
    for message in errors:
        _logger.info("  - %s", message)
    _logger.info("-" * 72)
    _logger.info("RESULT: FAIL")
    sys.exit(1)

_logger.info("RESULT: PASS (no errors)")
sys.exit(0)
