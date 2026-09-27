#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Offline static analyser for the ``ls_calibration`` module.

The build environment has no Odoo runtime, no PostgreSQL and no network
access, so flake8, pylint-odoo and a live installation are unavailable. This
script performs the subset of their checks that can be carried out from the
source tree alone, using only the Python standard library and ``lxml``.

Checks performed
----------------
1.  Python syntax of every ``.py`` file.
2.  XML well-formedness of every ``.xml`` file.
3.  Manifest completeness and data-file existence.
4.  Every field referenced in a view exists on the target model.
5.  Every ``ref=`` in XML resolves to a record defined in this module or to a
    whitelisted external identifier.
6.  Every model has at least one ``ir.model.access`` line.
7.  Every ACL line names a model and a group defined by this module.
8.  Every Python method invoked from a view button exists on the model.
9.  Odoo 19 API compliance: no ``<tree>``, no ``attrs=``, no ``states=``,
    no ``_sql_constraints``, no ``name_get``.
10. No placeholder tokens, no raw SQL, no bare ``except``.
11. PEP 8 subset: line length, trailing whitespace, tabs.
12. Every model class carries a docstring, and so does every public method.

Run with ``--self-test`` to execute the negative controls that prove the
checker detects the faults it claims to detect.
"""

from __future__ import annotations

import argparse
import ast
import csv
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


MAX_LINE_LENGTH = 88

#: External XML identifiers this module is allowed to reference. Anything
#: outside this set must be defined by the module itself.
ALLOWED_EXTERNAL_REFS: Set[str] = {
    "base.main_company",
    "base.user_root",
    "base.group_user",
    "base.group_multi_company",
    "base.group_system",
    "base.module_category_human_resources",
}

#: Tokens that must never appear in shipped source.
PLACEHOLDER_TOKENS: Tuple[str, ...] = (
    "TODO",
    "FIXME",
    "XXX",
    "HACK",
    "PLACEHOLDER",
    "LOREM IPSUM",
    "<<<",
    ">>>",
)

#: Compiled forms of the placeholder tokens. A token only counts when it
#: stands alone: ``NEW_SEQUENCE_PLACEHOLDER`` is a legitimate constant name,
#: whereas a bare ``PLACEHOLDER`` is a leftover marker.
PLACEHOLDER_REGEXES = [
    (
        token,
        re.compile(
            r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])"
        ),
    )
    for token in PLACEHOLDER_TOKENS
]

#: Odoo APIs removed or renamed in Odoo 18/19.
FORBIDDEN_PY_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"^\s*_sql_constraints\s*=", "_sql_constraints removed in Odoo 19; use models.Constraint"),
    (r"def\s+name_get\s*\(", "name_get removed; use _compute_display_name"),
    (r"\.read_group\s*\(", "read_group replaced by _read_group"),
    (r"\bcr\.execute\s*\(", "raw SQL is not permitted in shipped code"),
    (r"\bself\.env\.cr\.execute\s*\(", "raw SQL is not permitted in shipped code"),
    (r"except\s*:", "bare except is not permitted"),
    (r"\bgroups_id\b", "unverified res.users groups field name"),
)

FORBIDDEN_XML_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"<tree[\s>]", "<tree> renamed to <list> in Odoo 18+"),
    (r"</tree>", "<tree> renamed to <list> in Odoo 18+"),
    (r"\battrs\s*=", "attrs removed in Odoo 17+; use direct expressions"),
    (r'\bstates\s*=\s*"', "states removed in Odoo 17+; use invisible expressions"),
    (r'view_mode">[^<]*\btree\b', "view_mode must use 'list', not 'tree'"),
    (r'oe_chatter', "oe_chatter div replaced by the <chatter/> element"),
    (r'<field name="category_id"[^>]*/>\s*</record>\s*<!--res.groups-->',
     "res.groups uses privilege_id in Odoo 19"),
)


class Finding:
    """One static-analysis finding."""

    def __init__(self, severity: str, path: str, line: int, message: str):
        """Store the location and description of the finding."""
        self.severity = severity
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        """Render the finding as a single diagnostic line."""
        return f"[{self.severity}] {self.path}:{self.line}: {self.message}"


class ModuleChecker:
    """Static analyser bound to one Odoo module directory."""

    def __init__(self, root: Path):
        """Index the module source tree."""
        self.root = root
        self.findings: List[Finding] = []
        self.py_files = sorted(
            p for p in root.rglob("*.py") if "__pycache__" not in p.parts
        )
        self.xml_files = sorted(root.rglob("*.xml"))
        self.model_fields: Dict[str, Set[str]] = {}
        self.model_methods: Dict[str, Set[str]] = {}
        self.model_inherits: Dict[str, List[str]] = {}
        self.defined_xml_ids: Set[str] = set()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def error(self, path: Path, line: int, message: str) -> None:
        """Record a blocking finding."""
        self.findings.append(
            Finding("ERROR", str(path.relative_to(self.root)), line, message)
        )

    def warn(self, path: Path, line: int, message: str) -> None:
        """Record a non-blocking finding."""
        self.findings.append(
            Finding("WARN", str(path.relative_to(self.root)), line, message)
        )

    # ------------------------------------------------------------------
    # 1. Python syntax and model inventory
    # ------------------------------------------------------------------
    def check_python_syntax_and_index(self) -> None:
        """Parse every Python file and index models, fields and methods."""
        for path in self.py_files:
            source = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                self.error(path, exc.lineno or 0, f"syntax error: {exc.msg}")
                continue
            self._index_module(path, tree)

    def _index_module(self, path: Path, tree: ast.Module) -> None:
        """Collect the models declared in one parsed module."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            model_name = None
            inherits: List[str] = []
            fields: Set[str] = set()
            methods: Set[str] = set()
            has_doc = ast.get_docstring(node) is not None
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if target.id == "_name" and isinstance(
                            item.value, ast.Constant
                        ):
                            model_name = item.value.value
                        elif target.id == "_inherit":
                            inherits = self._literal_str_list(item.value)
                        elif self._is_field_call(item.value):
                            fields.add(target.id)
                elif isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
                    if not item.name.startswith("_") and not ast.get_docstring(
                        item
                    ):
                        self.warn(
                            path,
                            item.lineno,
                            f"public method '{item.name}' has no docstring",
                        )
            if model_name is None and len(inherits) == 1:
                model_name = inherits[0]
            if model_name is None:
                continue
            if not has_doc:
                self.error(
                    path, node.lineno, f"model class '{node.name}' has no docstring"
                )
            self.model_fields.setdefault(model_name, set()).update(fields)
            self.model_methods.setdefault(model_name, set()).update(methods)
            self.model_inherits[model_name] = inherits

    @staticmethod
    def _is_field_call(value: ast.AST) -> bool:
        """Return whether an assignment right-hand side is a ``fields.X(...)``."""
        return (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "fields"
        )

    @staticmethod
    def _literal_str_list(value: ast.AST) -> List[str]:
        """Return a list of string literals from a list or single constant."""
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return [value.value]
        if isinstance(value, (ast.List, ast.Tuple)):
            return [
                element.value
                for element in value.elts
                if isinstance(element, ast.Constant)
                and isinstance(element.value, str)
            ]
        return []

    def _fields_of(self, model: str) -> Set[str]:
        """Return the fields of a model, including inherited mixin fields."""
        known = set(self.model_fields.get(model, set()))
        # Fields contributed by framework mixins used by this module.
        if any(
            "mail.thread" in self.model_inherits.get(model, [])
            or "mail.activity.mixin" in self.model_inherits.get(model, [])
            for _ in (0,)
        ):
            known.update(
                {
                    "message_ids",
                    "message_follower_ids",
                    "message_partner_ids",
                    "message_main_attachment_id",
                    "activity_ids",
                    "activity_state",
                    "activity_user_id",
                    "activity_type_id",
                    "activity_date_deadline",
                    "activity_summary",
                }
            )
        known.update({"id", "display_name", "create_date", "write_date"})
        return known

    # ------------------------------------------------------------------
    # 2. XML well-formedness and XML-ID inventory
    # ------------------------------------------------------------------
    def check_xml_wellformed_and_index(self) -> None:
        """Parse every XML file and index the record identifiers it defines."""
        module = self.root.name
        for path in self.xml_files:
            try:
                tree = etree.parse(str(path))
            except etree.XMLSyntaxError as exc:
                line = exc.lineno if exc.lineno else 0
                self.error(path, line, f"XML syntax error: {exc.msg}")
                continue
            for element in tree.iter():
                if element.tag not in ("record", "template", "menuitem"):
                    continue
                xml_id = element.get("id")
                if not xml_id:
                    continue
                self.defined_xml_ids.add(xml_id)
                self.defined_xml_ids.add(f"{module}.{xml_id}")
        # Models declared in Python are addressable as model_<underscored>.
        for model in self.model_fields:
            token = "model_" + model.replace(".", "_")
            self.defined_xml_ids.add(token)
            self.defined_xml_ids.add(f"{module}.{token}")

    # ------------------------------------------------------------------
    # 3. Manifest
    # ------------------------------------------------------------------
    def check_manifest(self) -> None:
        """Validate the manifest keys and that every data file exists."""
        manifest_path = self.root / "__manifest__.py"
        if not manifest_path.exists():
            self.error(self.root, 0, "__manifest__.py is missing")
            return
        try:
            manifest = ast.literal_eval(
                manifest_path.read_text(encoding="utf-8")
            )
        except (ValueError, SyntaxError) as exc:
            self.error(manifest_path, 0, f"manifest is not a literal: {exc}")
            return
        for key in ("name", "version", "license", "depends", "data", "author"):
            if key not in manifest:
                self.error(manifest_path, 0, f"manifest key '{key}' is missing")
        version = manifest.get("version", "")
        if not re.match(r"^19\.0\.\d+\.\d+\.\d+$", version):
            self.error(
                manifest_path,
                0,
                f"version '{version}' does not follow 19.0.x.y.z",
            )
        for relative in manifest.get("data", []) + manifest.get("demo", []):
            if not (self.root / relative).exists():
                self.error(
                    manifest_path, 0, f"declared data file missing: {relative}"
                )
        declared = set(manifest.get("data", [])) | set(manifest.get("demo", []))
        for path in self.xml_files:
            relative = str(path.relative_to(self.root))
            if relative.startswith("static/"):
                continue
            if relative not in declared:
                self.error(
                    manifest_path,
                    0,
                    f"XML file not declared in the manifest: {relative}",
                )

    # ------------------------------------------------------------------
    # 4-5. View field references and ref resolution
    # ------------------------------------------------------------------
    def check_view_fields(self) -> None:
        """Verify that every field named in a view exists on its model."""
        for path in self.xml_files:
            if path.parts[-2] == "static":
                continue
            try:
                tree = etree.parse(str(path))
            except etree.XMLSyntaxError:
                continue
            for record in tree.iter("record"):
                if record.get("model") != "ir.ui.view":
                    continue
                model_field = record.find("field[@name='model']")
                if model_field is None or not model_field.text:
                    continue
                model = model_field.text.strip()
                if model not in self.model_fields:
                    continue
                arch = record.find("field[@name='arch']")
                if arch is None:
                    continue
                known = self._fields_of(model)
                self._walk_arch(path, arch, model, known)

    def _walk_arch(
        self, path: Path, arch: etree._Element, model: str, known: Set[str]
    ) -> None:
        """Check the field and button names inside one view architecture."""
        # Fields of a nested one2many/many2many list belong to the comodel, so
        # only top-level fields are checked; nested blocks are skipped.
        nested_roots = set()
        for element in arch.iter("field"):
            for child in element.iter():
                if child is not element and child.tag in ("list", "form"):
                    nested_roots.add(child)
        skip: Set[etree._Element] = set()
        for root in nested_roots:
            for descendant in root.iter():
                skip.add(descendant)

        for element in arch.iter():
            if element is arch or element in skip:
                # The <field name="arch"> wrapper is the ir.ui.view field
                # carrying the architecture, not a field of the target model.
                continue
            if element.tag == "field":
                name = element.get("name")
                if name and name not in known:
                    self.error(
                        path,
                        element.sourceline or 0,
                        f"view field '{name}' does not exist on {model}",
                    )
            elif element.tag == "button":
                method = element.get("name")
                if (
                    method
                    and element.get("type") == "object"
                    and method not in self.model_methods.get(model, set())
                ):
                    self.error(
                        path,
                        element.sourceline or 0,
                        f"button method '{method}' does not exist on {model}",
                    )

    def check_refs(self) -> None:
        """Verify that every ``ref`` resolves to a known identifier."""
        pattern = re.compile(r"""ref\s*=\s*["']([^"']+)["']""")
        eval_pattern = re.compile(r"""ref\(\s*['"]([^'"]+)['"]\s*\)""")
        for path in self.xml_files:
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), start=1):
                for match in list(pattern.finditer(line)) + list(
                    eval_pattern.finditer(line)
                ):
                    target = match.group(1)
                    if target in ALLOWED_EXTERNAL_REFS:
                        continue
                    if target in self.defined_xml_ids:
                        continue
                    self.error(
                        path, number, f"unresolved ref '{target}'"
                    )

    def check_attribute_refs(self) -> None:
        """Resolve identifiers carried by attributes other than ``ref``.

        Menu items point at actions and parents through ``action`` and
        ``parent`` attributes, views restrict elements through ``groups``, and
        QWeb templates include one another through ``t-call``. None of these
        use ``ref=``, so they are checked separately here.
        """
        module = self.root.name
        for path in self.xml_files:
            try:
                tree = etree.parse(str(path))
            except etree.XMLSyntaxError:
                continue
            for element in tree.iter():
                line = element.sourceline or 0
                for attribute in ("action", "parent"):
                    value = element.get(attribute)
                    if element.tag == "menuitem" and value:
                        self._assert_known(path, line, value, attribute)
                groups = element.get("groups")
                if groups:
                    for token in groups.split(","):
                        token = token.strip().lstrip("!")
                        if token:
                            self._assert_known(path, line, token, "groups")
                template = element.get("t-call")
                if template and template.startswith(f"{module}."):
                    self._assert_known(path, line, template, "t-call")

    def _assert_known(
        self, path: Path, line: int, target: str, origin: str
    ) -> None:
        """Record an error when an identifier resolves to nothing."""
        if target in ALLOWED_EXTERNAL_REFS or target in self.defined_xml_ids:
            return
        if target.startswith("web."):
            # Framework-provided layouts and templates.
            return
        self.error(path, line, f"unresolved {origin} identifier '{target}'")

    # ------------------------------------------------------------------
    # 6-7. Access control
    # ------------------------------------------------------------------
    def check_access_rights(self) -> None:
        """Verify ACL coverage and that ACL targets are defined."""
        acl_path = self.root / "security" / "ir.model.access.csv"
        if not acl_path.exists():
            self.error(self.root, 0, "security/ir.model.access.csv is missing")
            return
        with acl_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        covered: Set[str] = set()
        for number, row in enumerate(rows, start=2):
            model_ref = (row.get("model_id:id") or "").strip()
            group_ref = (row.get("group_id:id") or "").strip()
            if model_ref not in self.defined_xml_ids:
                self.error(acl_path, number, f"unknown ACL model '{model_ref}'")
            else:
                covered.add(model_ref)
            if group_ref and group_ref not in self.defined_xml_ids:
                self.error(acl_path, number, f"unknown ACL group '{group_ref}'")
        for model in sorted(self.model_fields):
            token = "model_" + model.replace(".", "_")
            if token not in covered:
                self.error(
                    acl_path, 0, f"model '{model}' has no access-rights line"
                )

    # ------------------------------------------------------------------
    # 9-11. Textual rules
    # ------------------------------------------------------------------
    def check_forbidden_patterns(self) -> None:
        """Apply the removed-API, placeholder and style rules."""
        checker_dir = (self.root / "tools").resolve()
        for path in self.py_files + self.xml_files:
            if checker_dir in path.resolve().parents:
                # The checker's own source declares the tokens it hunts for.
                continue
            text = path.read_text(encoding="utf-8")
            patterns = (
                FORBIDDEN_PY_PATTERNS
                if path.suffix == ".py"
                else FORBIDDEN_XML_PATTERNS
            )
            for number, line in enumerate(text.splitlines(), start=1):
                for pattern, message in patterns:
                    if re.search(pattern, line):
                        self.error(path, number, message)
                for token, token_re in PLACEHOLDER_REGEXES:
                    if token_re.search(line):
                        self.error(
                            path, number, f"placeholder token '{token}' present"
                        )
                if line.rstrip() != line:
                    self.error(path, number, "trailing whitespace")
                if "\t" in line:
                    self.error(path, number, "tab character")
                if path.suffix == ".py" and len(line) > MAX_LINE_LENGTH:
                    self.warn(
                        path,
                        number,
                        f"line exceeds {MAX_LINE_LENGTH} characters "
                        f"({len(line)})",
                    )

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------
    def run(self) -> List[Finding]:
        """Execute every check and return the accumulated findings."""
        self.check_python_syntax_and_index()
        self.check_xml_wellformed_and_index()
        self.check_manifest()
        self.check_view_fields()
        self.check_refs()
        self.check_attribute_refs()
        self.check_access_rights()
        self.check_forbidden_patterns()
        return self.findings


def run_self_test() -> int:
    """Inject known faults and confirm the checker detects each one.

    A static checker that has never been shown to fail on bad input provides
    no evidence. Each control below writes a deliberately broken module into a
    temporary directory and asserts that the expected finding appears.
    """
    controls = [
        (
            "python syntax",
            {"models/broken.py": "class X(:\n"},
            "syntax error",
        ),
        (
            "xml syntax",
            {"views/broken.xml": "<odoo><record></odoo>\n"},
            "XML syntax error",
        ),
        (
            "tree tag",
            {"views/legacy.xml": '<odoo><tree string="x"/></odoo>\n'},
            "renamed to <list>",
        ),
        (
            "attrs attribute",
            {
                "views/legacy2.xml": (
                    '<odoo><field name="a" attrs="{}"/></odoo>\n'
                )
            },
            "attrs removed",
        ),
        (
            "sql constraints",
            {"models/legacy.py": "class X:\n    _sql_constraints = []\n"},
            "_sql_constraints removed",
        ),
        (
            "placeholder token",
            {"models/todo.py": "# TODO: finish this\n"},
            "placeholder token",
        ),
        (
            "raw sql",
            {"models/sql.py": "def f(cr):\n    cr.execute('SELECT 1')\n"},
            "raw SQL",
        ),
        (
            "bare except",
            {"models/exc.py": "try:\n    pass\nexcept:\n    pass\n"},
            "bare except",
        ),
        (
            "trailing whitespace",
            {"models/ws.py": "x = 1   \n"},
            "trailing whitespace",
        ),
        (
            "bare placeholder marker",
            {"models/mark.py": "value = PLACEHOLDER\n"},
            "placeholder token",
        ),
        (
            "unresolved menu action",
            {
                "views/menu.xml": (
                    '<odoo><menuitem id="m" action="action_missing"/></odoo>\n'
                )
            },
            "unresolved action identifier",
        ),
        (
            "unresolved groups attribute",
            {
                "views/grp.xml": (
                    '<odoo><record id="v" model="ir.ui.view">'
                    '<field name="arch" type="xml"><form>'
                    '<button name="x" groups="fake_module.group_ghost"/>'
                    "</form></field></record></odoo>\n"
                )
            },
            "unresolved groups identifier",
        ),
    ]

    failures = 0
    for label, files, expected in controls:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fake_module"
            for relative, content in files.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            checker = ModuleChecker(root)
            checker.check_python_syntax_and_index()
            checker.check_xml_wellformed_and_index()
            checker.check_forbidden_patterns()
            checker.check_attribute_refs()
            detected = any(
                expected in finding.message for finding in checker.findings
            )
            status = "PASS" if detected else "FAIL"
            if not detected:
                failures += 1
            _logger.info("  negative control [%s] %s", status, label)

    # Positive control: a clean file must produce no forbidden-pattern finding.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "clean_module"
        (root / "models").mkdir(parents=True)
        (root / "models" / "clean.py").write_text(
            '"""Clean."""\n\nNEW_SEQUENCE_PLACEHOLDER = "/"\nVALUE = 1\n',
            encoding="utf-8",
        )
        checker = ModuleChecker(root)
        checker.check_python_syntax_and_index()
        checker.check_forbidden_patterns()
        errors = [f for f in checker.findings if f.severity == "ERROR"]
        status = "PASS" if not errors else "FAIL"
        if errors:
            failures += 1
            for finding in errors:
                _logger.info("    unexpected: %s", finding)
        _logger.info("  positive control [%s] clean file produces no error", status)

    return failures


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "module", nargs="?", default=".", help="path to the module directory"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the negative controls instead of checking a module",
    )
    args = parser.parse_args()

    if args.self_test:
        _logger.info("Negative-control validation of the static checker")
        failures = run_self_test()
        if failures:
            _logger.info("\nSELF-TEST: FAIL (%s control(s) did not fire)", failures)
            return 2
        _logger.info("\nSELF-TEST: PASS (checker detects every injected fault)")
        return 0

    root = Path(args.module).resolve()
    if not root.is_dir():
        print("not a directory:", root, file=sys.stderr)  # noqa: W8116
        return 2

    findings = ModuleChecker(root).run()
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]

    for finding in errors + warnings:
        _logger.info(finding)

    print(  # noqa: W8116  CLI script stdout
        f"\n{os.path.basename(root)}: "
        f"{len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
