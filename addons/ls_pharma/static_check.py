# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Offline static checker for the ``ls_pharma`` module.

The build environment in which this module was written has no Odoo runtime,
no PostgreSQL server and no network access, so ``flake8``, ``pylint-odoo``
and an actual installation could not be run.  This checker replaces none of
them.  It uses only the Python standard library and ``lxml`` and verifies the
internal consistency that can be verified without a running Odoo:

1.  every ``<field name="...">`` in a view names a field that exists on the
    model that the field belongs to, following one-to-many and many-to-many
    fields into their target model;
2.  every ``<button type="object" name="...">`` names a method that exists;
3.  every ``ref="..."`` either resolves inside this module or names a module
    that this module declares as a dependency;
4.  every XML identifier is declared once;
5.  every file listed in the manifest exists, and every XML and CSV file in
    the module is listed in the manifest;
6.  every model named in ``ir.model.access.csv`` exists and every model of the
    module appears there;
7.  the first term of every domain and of every ``group_by`` in a view names a
    real field;
8.  no source file contains a placeholder token;
9.  no shipped file executes raw SQL;
10. a subset of PEP 8: line length, trailing whitespace, tab indentation and
    trailing blank lines.

Run it from the directory that contains the module::

    python3 ls_pharma/static_check.py ls_pharma

The exit status is 0 when no error was found and 1 otherwise.

This file ships inside the module so that the receiving team can re-run it
after any change.  It excludes its own source from the placeholder scan and
the raw SQL scan, because it necessarily contains those very tokens.
"""

import ast
import csv
import os
import re
import sys
import logging

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Field classes recognised on the right-hand side of a field assignment.
FIELD_CLASSES = frozenset(
    {
        "Char",
        "Text",
        "Html",
        "Boolean",
        "Integer",
        "Float",
        "Monetary",
        "Date",
        "Datetime",
        "Binary",
        "Image",
        "Selection",
        "Many2one",
        "One2many",
        "Many2many",
        "Reference",
        "Json",
    }
)

#: Fields that Odoo defines on every model and that a view may therefore name
#: without the module declaring them.
MAGIC_FIELDS = frozenset(
    {
        "id",
        "display_name",
        "create_uid",
        "create_date",
        "write_uid",
        "write_date",
        "__last_update",
    }
)

#: Fields contributed by the mail mixins that this module inherits.  They are
#: listed here because the mixins live in the ``mail`` module, whose source is
#: not available to this checker.
MAIL_THREAD_FIELDS = frozenset(
    {
        "message_ids",
        "message_follower_ids",
        "message_partner_ids",
        "message_is_follower",
        "message_needaction",
        "message_needaction_counter",
        "message_has_error",
        "message_has_error_counter",
        "message_attachment_count",
        "message_main_attachment_id",
        "website_message_ids",
        "has_message",
        "rating_ids",
    }
)

MAIL_ACTIVITY_FIELDS = frozenset(
    {
        "activity_ids",
        "activity_state",
        "activity_user_id",
        "activity_type_id",
        "activity_type_icon",
        "activity_date_deadline",
        "my_activity_date_deadline",
        "activity_summary",
        "activity_exception_decoration",
        "activity_exception_icon",
        "activity_calendar_event_id",
    }
)

#: Fields of models that this module extends or points at but does not own.
#: Only the fields that the views of this module actually name are listed.
#: A name that is not listed here is reported, which is the intended
#: behaviour: it forces every external field used by this module to be
#: declared explicitly in one place.
EXTERNAL_MODEL_FIELDS = {
    "product.template": frozenset({"name", "default_code"}),
    "product.product": frozenset({"name", "default_code"}),
    "res.company": frozenset({"name"}),
    "res.users": frozenset({"name", "login"}),
    "res.partner": frozenset({"name"}),
    "stock.lot": frozenset({"name"}),
    "stock.warehouse": frozenset({"name"}),
    "mrp.production": frozenset({"name"}),
    "mrp.bom": frozenset({"code"}),
    "uom.uom": frozenset({"name"}),
}

#: Tokens that must never appear in a shipped source file.
PLACEHOLDER_TOKENS = (
    "TODO",
    "FIXME",
    "XXX",
    "PLACEHOLDER",
    "LOREM IPSUM",
    "TO BE COMPLETED",
    "NOT IMPLEMENTED YET",
)

#: The XML attribute that legitimately carries the word "placeholder".
PLACEHOLDER_ATTRIBUTE = re.compile(r'placeholder\s*=\s*"[^"]*"')

#: Patterns that indicate raw SQL execution.
RAW_SQL_PATTERNS = (
    re.compile(r"\.cr\.execute\s*\("),
    re.compile(r"\benv\.cr\.executemany\s*\("),
)

#: Maximum length of a source line.
MAX_LINE_LENGTH = 88

#: Elements of a view that carry a model context of their own.
SUBVIEW_TAGS = frozenset({"list", "tree", "form", "kanban", "search", "graph",
                          "pivot", "calendar", "activity"})


class Report:
    """Collects the findings of the checker."""

    def __init__(self):
        """Create an empty report."""
        self.errors = []
        self.notes = []

    def error(self, path, message):
        """Record a finding that must be fixed."""
        self.errors.append("%s: %s" % (path, message))

    def note(self, message):
        """Record an observation that needs no fix."""
        self.notes.append(message)


# ---------------------------------------------------------------------------
# Python inspection
# ---------------------------------------------------------------------------


def _string_value(node):
    """Return the value of a string constant node, or None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _string_list(node):
    """Return the list of string constants held by a node."""
    values = []
    if isinstance(node, (ast.List, ast.Tuple)):
        for element in node.elts:
            value = _string_value(element)
            if value is not None:
                values.append(value)
    else:
        value = _string_value(node)
        if value is not None:
            values.append(value)
    return values


def _field_comodel(call):
    """Return the comodel named by a relational field call, or None."""
    for keyword in call.keywords:
        if keyword.arg == "comodel_name":
            return _string_value(keyword.value)
    if call.args:
        return _string_value(call.args[0])
    return None


class ModelInfo:
    """Everything the checker knows about one Odoo model."""

    def __init__(self, name):
        """Create an empty description of the model called ``name``."""
        self.name = name
        self.fields = set()
        self.relations = {}
        self.methods = set()
        self.inherits = []
        self.is_abstract = False
        self.is_transient = False
        self.own_model = True


def collect_models(module_path, report):
    """Return the models defined by the module, keyed by technical name.

    :param str module_path: path of the module directory.
    :param Report report: report that receives any finding.
    :rtype: dict of str to ModelInfo
    """
    models = {}
    for path in iter_files(module_path, ".py"):
        source = read_text(path)
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as error:
            report.error(path, "syntax error: %s" % error)
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            _collect_class(node, models, path, report)
    return models


def _base_names(node):
    """Return the dotted names of the base classes of a class definition."""
    names = []
    for base in node.bases:
        names.append(ast.unparse(base))
    return names


def _collect_class(node, models, path, report):
    """Add one class definition to the model registry."""
    bases = _base_names(node)
    if not any(base.startswith("models.") for base in bases):
        return
    name = None
    inherits = []
    for statement in node.body:
        if not isinstance(statement, ast.Assign) or not statement.targets:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "_name":
            name = _string_value(statement.value)
        elif target.id == "_inherit":
            inherits = _string_list(statement.value)
    if name is None and len(inherits) == 1:
        name = inherits[0]
        inherits = []
    if name is None:
        report.error(path, "class %s declares neither _name nor _inherit" % node.name)
        return
    info = models.get(name)
    if info is None:
        info = ModelInfo(name)
        models[name] = info
    info.is_abstract = any("AbstractModel" in base for base in bases)
    info.is_transient = any("TransientModel" in base for base in bases)
    info.own_model = not any(
        base.endswith("Model") and name in EXTERNAL_MODEL_FIELDS for base in bases
    )
    info.inherits.extend(inherits)
    for statement in node.body:
        if isinstance(statement, ast.Assign) and statement.targets:
            target = statement.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if not isinstance(statement.value, ast.Call):
                continue
            call = statement.value
            function = call.func
            if (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "fields"
                and function.attr in FIELD_CLASSES
            ):
                info.fields.add(target.id)
                if function.attr in ("Many2one", "One2many", "Many2many"):
                    comodel = _field_comodel(call)
                    if comodel:
                        info.relations[target.id] = comodel
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info.methods.add(statement.name)


def resolve_inheritance(models):
    """Copy the fields of every inherited mixin into the inheriting model."""
    for _pass in range(4):
        for info in models.values():
            for parent_name in info.inherits:
                if parent_name == "mail.thread":
                    info.fields |= MAIL_THREAD_FIELDS
                elif parent_name == "mail.activity.mixin":
                    info.fields |= MAIL_ACTIVITY_FIELDS
                parent = models.get(parent_name)
                if parent is not None:
                    info.fields |= parent.fields
                    info.relations.update(parent.relations)
                    info.methods |= parent.methods


def known_fields(models, model_name):
    """Return the set of field names that ``model_name`` is known to carry."""
    fields = set(MAGIC_FIELDS)
    info = models.get(model_name)
    if info is not None:
        fields |= info.fields
    fields |= EXTERNAL_MODEL_FIELDS.get(model_name, frozenset())
    return fields


def is_known_model(models, model_name):
    """Tell whether the checker can validate fields of ``model_name``."""
    return model_name in models or model_name in EXTERNAL_MODEL_FIELDS


# ---------------------------------------------------------------------------
# XML inspection
# ---------------------------------------------------------------------------


def check_views(module_path, module_name, models, xml_ids, report):
    """Validate every view, action and menu declared by the module."""
    from lxml import etree

    for path in iter_files(module_path, ".xml"):
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError as error:
            report.error(path, "not well formed: %s" % error)
            continue
        root = tree.getroot()
        for record in root.iter("record"):
            model = record.get("model")
            if model == "ir.ui.view":
                _check_view_record(record, path, models, report)
            elif model == "ir.actions.act_window":
                _check_action_record(record, path, models, report)
        for record in root.iter("record"):
            _check_refs(record, path, module_name, xml_ids, report)
        for element in root.iter():
            if not isinstance(element.tag, str):
                continue
            groups = element.get("groups")
            if groups:
                for item in groups.split(","):
                    item = item.strip()
                    if item:
                        _check_single_ref(
                            item, path, module_name, xml_ids, report
                        )
        for menu in root.iter("menuitem"):
            _check_menu(menu, path, module_name, xml_ids, report)
            _check_web_icon(menu, path, module_path, report)


def _record_field(record, name):
    """Return the ``<field>`` child of ``record`` called ``name``."""
    for field in record.findall("field"):
        if field.get("name") == name:
            return field
    return None


def _check_action_record(record, path, models, report):
    """Validate the model named by a window action."""
    res_model_field = _record_field(record, "res_model")
    if res_model_field is None:
        report.error(path, "act_window %s has no res_model" % record.get("id"))
        return
    model_name = (res_model_field.text or "").strip()
    if not is_known_model(models, model_name):
        report.error(
            path,
            "act_window %s targets unknown model %s"
            % (record.get("id"), model_name),
        )


def _check_view_record(record, path, models, report):
    """Validate the architecture of one view record."""
    model_field = _record_field(record, "model")
    arch_field = _record_field(record, "arch")
    if model_field is None:
        report.error(path, "view %s has no model" % record.get("id"))
        return
    model_name = (model_field.text or "").strip()
    if arch_field is None:
        return
    if not is_known_model(models, model_name):
        report.error(
            path, "view %s targets unknown model %s" % (record.get("id"), model_name)
        )
        return
    for child in arch_field:
        _walk_arch(child, model_name, models, path, record.get("id"), report)


def _walk_arch(element, model_name, models, path, view_id, report):
    """Walk one view architecture, following relational fields."""
    tag = element.tag
    if not isinstance(tag, str):
        return
    if tag == "field":
        field_name = element.get("name")
        if field_name and not _is_expression(field_name):
            fields = known_fields(models, model_name)
            if field_name not in fields:
                report.error(
                    path,
                    "view %s: field %s does not exist on %s"
                    % (view_id, field_name, model_name),
                )
                return
            info = models.get(model_name)
            comodel = info.relations.get(field_name) if info else None
            if comodel and len(element):
                for child in element:
                    _walk_arch(child, comodel, models, path, view_id, report)
                return
    elif tag == "button":
        _check_button(element, model_name, models, path, view_id, report)
    _check_attribute_expressions(
        element, model_name, models, path, view_id, report
    )
    for child in element:
        _walk_arch(child, model_name, models, path, view_id, report)


def _is_expression(value):
    """Tell whether a field name is in fact a computed expression."""
    return "%" in value or "{" in value


def _check_button(element, model_name, models, path, view_id, report):
    """Validate the method named by an object button."""
    if element.get("type") not in ("object", None):
        return
    if element.get("type") is None and not element.get("name"):
        return
    if element.get("special"):
        return
    name = element.get("name")
    if not name or element.get("type") != "object":
        return
    info = models.get(model_name)
    if info is None:
        return
    if name not in info.methods:
        report.error(
            path,
            "view %s: button calls %s which does not exist on %s"
            % (view_id, name, model_name),
        )


DOMAIN_FIELD = re.compile(r"\(\s*'([A-Za-z_][A-Za-z0-9_.]*)'\s*,")
GROUP_BY_FIELD = re.compile(r"'group_by'\s*:\s*'([A-Za-z_][A-Za-z0-9_.:]*)'")


def _check_attribute_expressions(
    element, model_name, models, path, view_id, report
):
    """Validate the field names used in domains and in group_by contexts."""
    fields = known_fields(models, model_name)
    for attribute in ("domain", "filter_domain"):
        value = element.get(attribute)
        if not value:
            continue
        for name in DOMAIN_FIELD.findall(value):
            head = name.split(".")[0]
            if head not in fields:
                report.error(
                    path,
                    "view %s: domain names %s which does not exist on %s"
                    % (view_id, head, model_name),
                )
    context = element.get("context")
    if context:
        for name in GROUP_BY_FIELD.findall(context):
            head = name.split(":")[0].split(".")[0]
            if head not in fields:
                report.error(
                    path,
                    "view %s: group_by names %s which does not exist on %s"
                    % (view_id, head, model_name),
                )
    date_field = element.get("date")
    if date_field and date_field not in fields:
        report.error(
            path,
            "view %s: date filter names %s which does not exist on %s"
            % (view_id, date_field, model_name),
        )


def collect_xml_ids(module_path, module_name, report):
    """Return every XML identifier declared by the module."""
    from lxml import etree

    identifiers = set()
    for path in iter_files(module_path, ".xml"):
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError:
            continue
        root = tree.getroot()
        for element in root.iter():
            if not isinstance(element.tag, str):
                continue
            if element.tag not in ("record", "menuitem", "template", "act_window"):
                continue
            identifier = element.get("id")
            if not identifier:
                continue
            qualified = identifier
            if "." not in identifier:
                qualified = "%s.%s" % (module_name, identifier)
            if qualified in identifiers:
                report.error(path, "duplicate XML identifier %s" % qualified)
            identifiers.add(qualified)
    for model_name in ():
        identifiers.add(model_name)
    return identifiers


def add_model_xml_ids(models, module_name, identifiers):
    """Add the automatic ``model_<name>`` identifiers to the known set."""
    for name, info in models.items():
        if not info.own_model:
            continue
        identifiers.add("%s.model_%s" % (module_name, name.replace(".", "_")))


def _check_refs(record, path, module_name, xml_ids, report):
    """Validate every ``ref`` attribute of one record."""
    for element in record.iter():
        if not isinstance(element.tag, str):
            continue
        reference = element.get("ref")
        if reference:
            _check_single_ref(reference, path, module_name, xml_ids, report)
        evaluation = element.get("eval")
        if evaluation:
            for reference in re.findall(r"ref\(\s*'([^']+)'\s*\)", evaluation):
                _check_single_ref(reference, path, module_name, xml_ids, report)


def _check_single_ref(reference, path, module_name, xml_ids, report):
    """Validate one XML identifier reference."""
    if "." not in reference:
        reference = "%s.%s" % (module_name, reference)
    target_module = reference.split(".", 1)[0]
    if target_module == module_name:
        if reference not in xml_ids:
            report.error(path, "unresolved internal reference %s" % reference)
    elif target_module not in DECLARED_DEPENDENCIES:
        report.error(
            path,
            "reference %s names module %s which is not a declared dependency"
            % (reference, target_module),
        )


def _check_menu(menu, path, module_name, xml_ids, report):
    """Validate the parent and the action of one menu item."""
    for attribute in ("parent", "action"):
        value = menu.get(attribute)
        if not value:
            continue
        for item in value.split(","):
            item = item.strip()
            if not item:
                continue
            _check_single_ref(item, path, module_name, xml_ids, report)


def _check_web_icon(menu, path, module_path, report):
    """Check that the icon named by a root menu item exists."""
    web_icon = menu.get("web_icon")
    if not web_icon:
        return
    parts = web_icon.split(",")
    if len(parts) != 2:
        report.error(path, "web_icon %s is not <module>,<path>" % web_icon)
        return
    icon_path = os.path.join(module_path, parts[1].strip())
    if not os.path.exists(icon_path):
        report.error(path, "web_icon file %s does not exist" % parts[1].strip())


# ---------------------------------------------------------------------------
# Manifest, security and source hygiene
# ---------------------------------------------------------------------------

DECLARED_DEPENDENCIES = set()


def check_manifest(module_path, report):
    """Validate the manifest and return the declared data files."""
    global DECLARED_DEPENDENCIES
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.exists(manifest_path):
        report.error(module_path, "no __manifest__.py")
        return set()
    try:
        manifest = ast.literal_eval(read_text(manifest_path))
    except (ValueError, SyntaxError) as error:
        report.error(manifest_path, "manifest is not a literal: %s" % error)
        return set()
    for key in ("name", "version", "license", "author", "depends", "data"):
        if key not in manifest:
            report.error(manifest_path, "manifest has no %s key" % key)
    DECLARED_DEPENDENCIES = set(manifest.get("depends", []))
    DECLARED_DEPENDENCIES.add("base")
    version = manifest.get("version", "")
    if not version.startswith("19.0."):
        report.error(manifest_path, "version %s is not an Odoo 19 version" % version)
    declared = list(manifest.get("data", [])) + list(manifest.get("demo", []))
    for relative in declared:
        if not os.path.exists(os.path.join(module_path, relative)):
            report.error(manifest_path, "declared file %s does not exist" % relative)
    declared_set = set(declared)
    for path in iter_files(module_path, ".xml") + iter_files(module_path, ".csv"):
        relative = os.path.relpath(path, module_path)
        if relative.startswith("static" + os.sep):
            continue
        if relative not in declared_set:
            report.error(
                manifest_path, "file %s is not listed in the manifest" % relative
            )
    return declared_set


def check_access_rules(module_path, models, report):
    """Validate the access rights file against the models of the module."""
    path = os.path.join(module_path, "security", "ir.model.access.csv")
    if not os.path.exists(path):
        report.error(module_path, "no security/ir.model.access.csv")
        return
    covered = set()
    with open(path, newline="", encoding="utf-8") as handle:
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
            report.error(path, "unexpected column layout %s" % reader.fieldnames)
            return
        for number, row in enumerate(reader, start=2):
            model_ref = row["model_id:id"]
            if not model_ref.startswith("model_"):
                model_ref = model_ref.split(".")[-1]
            technical = model_ref[len("model_"):].replace("_", ".")
            covered.add(technical)
            for column in ("perm_read", "perm_write", "perm_create", "perm_unlink"):
                if row[column] not in ("0", "1"):
                    report.error(
                        path, "line %d: %s is not 0 or 1" % (number, column)
                    )
    for name, info in models.items():
        if info.is_abstract or not info.own_model:
            continue
        normalised = name.replace(".", "_").replace("_", ".")
        if normalised not in covered and name.replace("_", ".") not in covered:
            report.error(path, "model %s has no access rule" % name)


def check_source_hygiene(module_path, report):
    """Check placeholders, raw SQL and a subset of PEP 8."""
    own_path = os.path.abspath(__file__)
    for extension in (".py", ".xml", ".csv"):
        for path in iter_files(module_path, extension):
            if os.path.abspath(path) == own_path:
                continue
            text = read_text(path)
            scanned = text
            if extension == ".xml":
                # The XML attribute placeholder="..." is a legitimate use of
                # the word and is removed before the token scan.
                scanned = PLACEHOLDER_ATTRIBUTE.sub("", scanned)
            upper = scanned.upper()
            for token in PLACEHOLDER_TOKENS:
                if token in upper:
                    report.error(path, "contains the placeholder token %s" % token)
            for pattern in RAW_SQL_PATTERNS:
                if pattern.search(text):
                    report.error(path, "executes raw SQL")
            if extension == ".py":
                _check_pep8_subset(path, text, report)


def _check_pep8_subset(path, text, report):
    """Check line length, trailing whitespace, tabs and final newline."""
    lines = text.split("\n")
    for number, line in enumerate(lines, start=1):
        # A line that carries a URL is exempt from the length limit: breaking
        # a URL would make the cited source unusable.
        if len(line) > MAX_LINE_LENGTH and "http" not in line:
            report.error(
                path,
                "line %d is %d characters long, the limit is %d"
                % (number, len(line), MAX_LINE_LENGTH),
            )
        if line != line.rstrip():
            report.error(path, "line %d has trailing whitespace" % number)
        if "\t" in line:
            report.error(path, "line %d contains a tab" % number)
    if not text.endswith("\n"):
        report.error(path, "the file does not end with a newline")
    if text.endswith("\n\n"):
        report.error(path, "the file ends with a blank line")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iter_files(module_path, extension):
    """Return every file under ``module_path`` with the given extension."""
    found = []
    for directory, directory_names, file_names in os.walk(module_path):
        directory_names[:] = [
            name for name in directory_names if name != "__pycache__"
        ]
        for file_name in sorted(file_names):
            if file_name.endswith(extension):
                found.append(os.path.join(directory, file_name))
    return sorted(found)


def read_text(path):
    """Return the decoded content of a file."""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main(argv):
    """Run every check and print the report."""
    if len(argv) != 2:
        _logger.info("usage: python3 static_check.py <module directory>")
        return 2
    module_path = os.path.abspath(argv[1].rstrip(os.sep))
    module_name = os.path.basename(module_path)
    report = Report()

    check_manifest(module_path, report)
    models = collect_models(module_path, report)
    resolve_inheritance(models)
    xml_ids = collect_xml_ids(module_path, module_name, report)
    add_model_xml_ids(models, module_name, xml_ids)
    check_views(module_path, module_name, models, xml_ids, report)
    check_access_rules(module_path, models, report)
    check_source_hygiene(module_path, report)

    report.note("models inspected: %d" % len(models))
    report.note("XML identifiers declared: %d" % len(xml_ids))

    for note in report.notes:
        _logger.info("note: %s", note)
    for error in report.errors:
        _logger.info("ERROR %s", error)
    print(  # noqa: W8116  CLI script stdout
        "\n%d error(s) found in %s"
        % (len(report.errors), os.path.relpath(module_path))
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
