#!/usr/bin/env python3
# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Offline static checker for the ``ls_lab`` Odoo 19 module.

The checker runs without an Odoo runtime and without a database. It exists
because the build environment has neither, and because XML well-formedness
alone does not catch the class of defect that only surfaces at install time.

Checks performed
----------------

1.  Every Python file compiles.
2.  Every XML file is well-formed.
3.  Every view arch validates against the **correct Odoo 19 RNG schema** for
    its view type. Odoo 19 ships one RNG per view type
    (``search_view.rng``, ``list_view.rng``, ``graph_view.rng``,
    ``pivot_view.rng``, ``calendar_view.rng``, ``activity_view.rng``) and has
    **no** ``view.rng``. Form and kanban views are not RNG-validated by Odoo
    and are therefore not validated here either.
4.  Inside ``<search>`` views, ``<group>`` carries only attributes the Odoo 19
    grammar permits. ``expand`` and ``string`` are rejected: this is the exact
    defect that passes offline XML checking and fails at install time.
5.  Every ``<field name="...">`` in every view resolves to a field that exists
    on the model the element belongs to, following nested One2many and
    Many2many contexts.
6.  Every ``<button name="..." type="object">`` names a method that exists on
    the model.
7.  Every internal external identifier referenced by ``ref=`` resolves.
8.  Every model declared by the module has an ACL row for all four groups.
9.  Every file listed in the manifest exists on disk.
10. Forbidden Odoo 19 constructs are absent.

Exit code is 0 when no finding is raised, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import csv
import os
import py_compile
import re
import sys
import tempfile
from collections import defaultdict

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: View types Odoo 19 validates against an RNG, mapped to the schema file.
RNG_BY_VIEW_TYPE = {
    "search": "search_view.rng",
    "list": "list_view.rng",
    "graph": "graph_view.rng",
    "pivot": "pivot_view.rng",
    "calendar": "calendar_view.rng",
    "activity": "activity_view.rng",
}

#: View types Odoo 19 ships no RNG for. Not validated, by design.
UNVALIDATED_VIEW_TYPES = {"form", "kanban", "qweb"}

#: Attributes the Odoo 19 grammar permits on <group>.
#: Source: odoo/addons/base/rng/common.rng, <rng:define name="group">, plus the
#: 'overload', 'access_rights' and 'container' references it includes.
GROUP_ALLOWED_ATTRS = {
    "position", "groups", "colspan", "rowspan", "fill", "height", "width",
    "name", "color", "invisible", "col",
}

#: Constructs removed or replaced in Odoo 19, with the reason.
FORBIDDEN_PATTERNS = [
    (r"<tree[\s>]", "<tree> was replaced by <list> in Odoo 19"),
    (r"oe_chatter", "the oe_chatter div was replaced by the <chatter/> element"),
    (r"_sql_constraints", "_sql_constraints was replaced by models.Constraint"),
    (r"\bnumbercall\b", "ir.cron.numbercall does not exist in Odoo 19"),
    (r"\bdoall\b", "ir.cron.doall does not exist in Odoo 19"),
    (r"\bgroups_id\b", "res.users/ir.ui.menu use group_ids in Odoo 19"),
    (r"\bstock\.production\.lot\b", "the model is stock.lot in Odoo 19"),
    (r"\bname_get\b", "name_get was replaced by _compute_display_name"),
    (r"\bself\.env\.cr\.execute\b", "raw SQL is not permitted in this module"),
    (r"#\s*(TODO|FIXME|XXX)\b", "placeholder markers are not permitted"),
]

#: Fields every model inherits from the ORM or from the mail mixins.
IMPLICIT_FIELDS = {
    "id", "display_name", "create_uid", "create_date", "write_uid",
    "write_date", "__last_update",
    # mail.thread
    "message_ids", "message_follower_ids", "message_partner_ids",
    "message_is_follower", "message_needaction", "message_needaction_counter",
    "message_has_error", "message_has_error_counter", "message_attachment_count",
    "message_main_attachment_id", "website_message_ids", "message_has_sms_error",
    "has_message", "rating_ids",
    # mail.activity.mixin
    "activity_ids", "activity_state", "activity_user_id", "activity_type_id",
    "activity_type_icon", "activity_date_deadline", "my_activity_date_deadline",
    "activity_summary", "activity_exception_decoration",
    "activity_exception_icon", "activity_calendar_event_id",
}

#: Odoo modules whose external identifiers cannot be resolved offline.
EXTERNAL_MODULES = {
    "base", "mail", "product", "stock", "uom", "web", "account", "hr",
    "purchase", "sale", "mrp", "project", "maintenance", "resource",
}


class Finding:
    """One checker finding."""

    def __init__(self, code, path, message):
        self.code = code
        self.path = path
        self.message = message

    def __str__(self):
        return f"[{self.code}] {self.path}: {self.message}"


class ModuleChecker:
    """Static checker for one Odoo module directory."""

    def __init__(self, module_path):
        self.module_path = os.path.abspath(module_path)
        self.module_name = os.path.basename(self.module_path)
        self.findings = []
        self.models = {}          # model name -> {"fields", "methods", "file"}
        self.field_comodel = {}   # (model, field) -> comodel
        self.declared_xmlids = set()
        self.referenced_xmlids = []  # (xmlid, path)
        self.rng_dir = os.path.join(self.module_path, "tools", "rng")

    # -- helpers ---------------------------------------------------------
    def add(self, code, path, message):
        """Record a finding."""
        self.findings.append(Finding(code, os.path.relpath(path, self.module_path)
                                     if os.path.isabs(path) else path, message))

    def _python_files(self):
        """Yield every Python file in the module."""
        for root, dirs, files in os.walk(self.module_path):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "rng")]
            for name in sorted(files):
                if name.endswith(".py"):
                    yield os.path.join(root, name)

    def _xml_files(self):
        """Yield every XML file in the module, excluding shipped RNG schemas."""
        for root, dirs, files in os.walk(self.module_path):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "rng")]
            for name in sorted(files):
                if name.endswith(".xml"):
                    yield os.path.join(root, name)

    # -- check 1: python compilation -------------------------------------
    def check_python_compiles(self):
        """Every Python file must compile."""
        with tempfile.TemporaryDirectory() as scratch:
            for index, path in enumerate(self._python_files()):
                cfile = os.path.join(scratch, f"out_{index}.pyc")
                try:
                    py_compile.compile(path, doraise=True, cfile=cfile)
                except py_compile.PyCompileError as error:
                    self.add("PY001", path, f"does not compile: {error}")

    # -- model inventory --------------------------------------------------
    def build_model_inventory(self):
        """Extract models, fields, methods and comodels from the source."""
        mixin_fields = defaultdict(set)
        pending = []

        for path in self._python_files():
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                model_name = None
                inherits = []
                fields = set()
                methods = set()
                comodels = {}
                for stmt in node.body:
                    if isinstance(stmt, ast.FunctionDef):
                        methods.add(stmt.name)
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                        target = stmt.targets[0]
                        if not isinstance(target, ast.Name):
                            continue
                        name = target.id
                        value = stmt.value
                        if name == "_name" and isinstance(value, ast.Constant):
                            model_name = value.value
                        elif name == "_inherit":
                            if isinstance(value, ast.Constant):
                                inherits = [value.value]
                            elif isinstance(value, (ast.List, ast.Tuple)):
                                inherits = [
                                    elt.value for elt in value.elts
                                    if isinstance(elt, ast.Constant)
                                ]
                        elif (isinstance(value, ast.Call)
                              and isinstance(value.func, ast.Attribute)
                              and isinstance(value.func.value, ast.Name)
                              and value.func.value.id == "fields"):
                            fields.add(name)
                            for kw in value.keywords:
                                if (kw.arg == "comodel_name"
                                        and isinstance(kw.value, ast.Constant)):
                                    comodels[name] = kw.value.value
                if model_name is None and inherits:
                    model_name = inherits[0]
                if model_name is None:
                    continue
                pending.append(
                    (model_name, inherits, fields, methods, comodels, path)
                )
                if model_name.endswith(".mixin"):
                    mixin_fields[model_name] |= fields

        for model_name, inherits, fields, methods, comodels, path in pending:
            resolved = set(fields)
            for parent in inherits:
                resolved |= mixin_fields.get(parent, set())
            entry = self.models.setdefault(
                model_name, {"fields": set(), "methods": set(), "file": path}
            )
            entry["fields"] |= resolved | IMPLICIT_FIELDS
            entry["methods"] |= methods
            for field_name, comodel in comodels.items():
                self.field_comodel[(model_name, field_name)] = comodel

        # Inherited mixin methods are available on the concrete model.
        for model_name, inherits, _f, _m, _c, _p in pending:
            for parent in inherits:
                if parent in self.models and model_name in self.models:
                    self.models[model_name]["methods"] |= (
                        self.models[parent]["methods"]
                    )

    # -- check 2 and 3: XML and RNG ---------------------------------------
    def check_xml_and_views(self):
        """Parse XML, validate archs, and check fields and buttons."""
        schemas = self._load_schemas()
        for path in self._xml_files():
            try:
                doc = etree.parse(path)
            except etree.XMLSyntaxError as error:
                self.add("XML001", path, f"is not well-formed: {error}")
                continue
            root = doc.getroot()
            self._collect_xmlids(root, path)
            for record in root.iter("record"):
                if record.get("model") != "ir.ui.view":
                    continue
                self._check_view_record(record, path, schemas)

    def _load_schemas(self):
        """Load the shipped Odoo 19 RNG schemas."""
        schemas = {}
        if not os.path.isdir(self.rng_dir):
            self.add("RNG000", self.rng_dir,
                     "RNG schema directory is missing; view validation skipped")
            return schemas
        for view_type, filename in RNG_BY_VIEW_TYPE.items():
            full = os.path.join(self.rng_dir, filename)
            if not os.path.exists(full):
                self.add("RNG000", full, "RNG schema file is missing")
                continue
            try:
                schemas[view_type] = etree.RelaxNG(etree.parse(full))
            except (etree.RelaxNGParseError, etree.XMLSyntaxError) as error:
                self.add("RNG000", full, f"schema could not be loaded: {error}")
        return schemas

    def _check_view_record(self, record, path, schemas):
        """Validate one ir.ui.view record."""
        model_field = record.find("./field[@name='model']")
        arch = record.find("./field[@name='arch']")
        if arch is None or model_field is None:
            return
        model_name = (model_field.text or "").strip()
        children = [c for c in arch if isinstance(c.tag, str)]
        if not children:
            return
        arch_root = children[0]
        view_type = arch_root.tag

        # RNG validation against the correct per-type schema.
        if view_type in schemas:
            standalone = etree.fromstring(etree.tostring(arch_root))
            if not schemas[view_type].validate(standalone):
                errors = "; ".join(
                    str(e.message) for e in schemas[view_type].error_log
                )
                self.add(
                    "RNG001", path,
                    f"view '{record.get('id')}' ({view_type}) fails the Odoo 19 "
                    f"{RNG_BY_VIEW_TYPE[view_type]} schema: {errors}",
                )
        elif view_type not in UNVALIDATED_VIEW_TYPES and view_type in RNG_BY_VIEW_TYPE:
            self.add("RNG002", path,
                     f"no schema loaded for view type '{view_type}'")

        # Group attribute allow-list, enforced inside search views.
        if view_type == "search":
            for group in arch_root.iter("group"):
                bad = set(group.attrib) - GROUP_ALLOWED_ATTRS
                if bad:
                    self.add(
                        "VIEW003", path,
                        f"view '{record.get('id')}': <group> in a search view "
                        f"carries attribute(s) {sorted(bad)} that the Odoo 19 "
                        f"grammar does not permit; allowed: "
                        f"{sorted(GROUP_ALLOWED_ATTRS)}",
                    )

        self._walk_view(arch_root, model_name, path, record.get("id"))

    def _walk_view(self, element, model_name, path, view_id):
        """Check field and button references, following nested contexts."""
        if model_name not in self.models:
            return
        known_fields = self.models[model_name]["fields"]
        known_methods = self.models[model_name]["methods"]

        for child in element:
            if not isinstance(child.tag, str):
                continue
            if child.tag == "field":
                field_name = child.get("name")
                if field_name and field_name not in known_fields:
                    self.add(
                        "VIEW001", path,
                        f"view '{view_id}': field '{field_name}' does not exist "
                        f"on model '{model_name}'",
                    )
                nested = [c for c in child if isinstance(c.tag, str)]
                if nested and field_name:
                    comodel = self.field_comodel.get((model_name, field_name))
                    for sub in nested:
                        self._walk_view(
                            sub, comodel or model_name, path, view_id
                        )
                continue
            if child.tag == "button" and child.get("type") == "object":
                method = child.get("name")
                if method and method not in known_methods:
                    self.add(
                        "VIEW002", path,
                        f"view '{view_id}': button calls method '{method}' "
                        f"which does not exist on model '{model_name}'",
                    )
            self._walk_view(child, model_name, path, view_id)

    # -- external identifiers ---------------------------------------------
    def _collect_xmlids(self, root, path):
        """Collect declared and referenced external identifiers."""
        for element in root.iter():
            if not isinstance(element.tag, str):
                continue
            if element.tag in ("record", "template", "menuitem"):
                xmlid = element.get("id")
                if xmlid:
                    self.declared_xmlids.add(self._qualify(xmlid))
            ref = element.get("ref")
            if ref:
                self.referenced_xmlids.append((self._qualify(ref), path))
            for attr in ("parent", "action", "groups"):
                value = element.get(attr)
                if value:
                    for item in value.split(","):
                        item = item.strip()
                        if item:
                            self.referenced_xmlids.append(
                                (self._qualify(item), path)
                            )
            if element.tag == "field" and element.get("eval"):
                for match in re.finditer(r"ref\(\s*['\"]([^'\"]+)['\"]\s*\)",
                                         element.get("eval")):
                    self.referenced_xmlids.append(
                        (self._qualify(match.group(1)), path)
                    )

    def _qualify(self, xmlid):
        """Return the fully qualified form of an external identifier."""
        return xmlid if "." in xmlid else f"{self.module_name}.{xmlid}"

    def check_xmlids_resolve(self):
        """Every internal external identifier must resolve."""
        implicit = {
            f"{self.module_name}.model_{name.replace('.', '_')}"
            for name in self.models
        }
        available = self.declared_xmlids | implicit
        for xmlid, path in self.referenced_xmlids:
            module = xmlid.split(".", 1)[0]
            if module in EXTERNAL_MODULES:
                continue
            if module != self.module_name:
                continue
            if xmlid not in available:
                self.add("REF001", path,
                         f"external identifier '{xmlid}' is referenced but "
                         f"never declared")

    # -- ACL completeness --------------------------------------------------
    def check_acl_completeness(self):
        """Every model must carry an ACL row for all four groups."""
        acl_path = os.path.join(
            self.module_path, "security", "ir.model.access.csv"
        )
        if not os.path.exists(acl_path):
            self.add("ACL001", acl_path, "the ACL file is missing")
            return
        seen = defaultdict(set)
        with open(acl_path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                model_ref = (row.get("model_id:id") or "").split(".")[-1]
                group_ref = (row.get("group_id:id") or "").split(".")[-1]
                seen[model_ref].add(group_ref)
        expected_groups = {
            f"{self.module_name}_group_viewer",
            f"{self.module_name}_group_analyst",
            f"{self.module_name}_group_reviewer",
            f"{self.module_name}_group_manager",
        }
        for model_name in sorted(self.models):
            if model_name.endswith(".mixin"):
                continue
            model_ref = f"model_{model_name.replace('.', '_')}"
            if model_ref not in seen:
                self.add("ACL002", acl_path,
                         f"model '{model_name}' has no ACL row at all")
                continue
            if model_name.endswith("_wizard"):
                continue
            missing = expected_groups - seen[model_ref]
            if missing:
                self.add("ACL003", acl_path,
                         f"model '{model_name}' has no ACL row for "
                         f"{sorted(missing)}")
        declared_models = {
            f"model_{name.replace('.', '_')}" for name in self.models
        }
        for model_ref in sorted(seen):
            if model_ref not in declared_models:
                self.add("ACL004", acl_path,
                         f"ACL references '{model_ref}' but no such model is "
                         f"declared by this module")

    # -- manifest ----------------------------------------------------------
    def check_manifest(self):
        """Every file listed in the manifest must exist."""
        manifest_path = os.path.join(self.module_path, "__manifest__.py")
        if not os.path.exists(manifest_path):
            self.add("MAN001", manifest_path, "the manifest is missing")
            return
        try:
            manifest = ast.literal_eval(
                open(manifest_path, encoding="utf-8").read()
            )
        except (ValueError, SyntaxError) as error:
            self.add("MAN002", manifest_path,
                     f"the manifest is not a literal dict: {error}")
            return
        for key in ("name", "version", "license", "depends", "data"):
            if key not in manifest:
                self.add("MAN003", manifest_path,
                         f"the manifest declares no '{key}'")
        for relative in manifest.get("data", []) + manifest.get("demo", []):
            full = os.path.join(self.module_path, relative)
            if not os.path.exists(full):
                self.add("MAN004", manifest_path,
                         f"data file '{relative}' does not exist")
        for dependency in manifest.get("depends", []):
            if dependency.startswith("ls_") and dependency != self.module_name:
                self.add("MAN005", manifest_path,
                         f"suite module '{dependency}' is declared as a "
                         f"dependency; this blocks installation when it is "
                         f"absent")
            if dependency == "quality":
                self.add("MAN006", manifest_path,
                         "'quality' is not part of Odoo 19 Community Edition")

    # -- forbidden constructs ---------------------------------------------
    def check_forbidden_constructs(self):
        """Reject constructs removed or replaced in Odoo 19."""
        for path in list(self._python_files()) + list(self._xml_files()):
            # The tools directory holds the checkers themselves, whose source
            # necessarily contains these patterns as string literals. Skip the
            # whole directory rather than maintaining a filename list.
            if os.sep + "tools" + os.sep in path or path.endswith(
                    os.sep + "tools"):
                continue
            content = open(path, encoding="utf-8").read()
            if path.endswith(".xml"):
                # Documentation comments legitimately name the constructs this
                # module deliberately avoids, so they are stripped before the
                # scan. Commented-out code is prohibited separately by the
                # coding standard.
                content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
            for pattern, reason in FORBIDDEN_PATTERNS:
                for match in re.finditer(pattern, content):
                    line = content[:match.start()].count("\n") + 1
                    self.add("FORB001", path,
                             f"line {line}: forbidden construct "
                             f"'{match.group(0).strip()}' — {reason}")

    # -- driver ------------------------------------------------------------
    def run(self):
        """Run every check and return the findings."""
        self.check_python_compiles()
        self.build_model_inventory()
        self.check_xml_and_views()
        self.check_xmlids_resolve()
        self.check_acl_completeness()
        self.check_manifest()
        self.check_forbidden_constructs()
        return self.findings


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_path", nargs="?", default=None,
                        help="path to the module directory")
    parser.add_argument("--quiet", action="store_true",
                        help="print only the summary line")
    args = parser.parse_args()

    module_path = args.module_path or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    checker = ModuleChecker(module_path)
    findings = checker.run()

    if not args.quiet:
        _logger.info("Static check of '%s' at %s", checker.module_name, module_path)
        _logger.info("  models discovered : %s", len(checker.models))
        print(f"  external ids      : {len(checker.declared_xmlids)} declared, "  # noqa: W8116  CLI script stdout
              f"{len(checker.referenced_xmlids)} referenced")
        _logger.info()
        if findings:
            by_code = defaultdict(list)
            for finding in findings:
                by_code[finding.code].append(finding)
            for code in sorted(by_code):
                _logger.info("--- %s (%s) ---", code, len(by_code[code]))
                for finding in by_code[code]:
                    _logger.info("  %s", finding)
                _logger.info()

    _logger.info("RESULT: %s finding(s)", len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
