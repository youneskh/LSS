#!/usr/bin/env python3
# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Scan other Life Sciences Suite modules for Odoo 19 construct regressions.

This tool exists because `ls_lab` was the first module in the suite built with
access to Odoo 19 source. Several facts that earlier modules had to engineer
around are now verified, and one defect class was positively identified:

    <group expand="0" string="Group By">   in a SEARCH view

The Odoo 19 grammar (odoo/addons/base/rng/common.rng) permits neither
``expand`` nor ``string`` on ``<group>``. Search views are validated against
that grammar at install time; form views are not, which is why the same
construct is harmless in a form view and fatal in a search view.

Offline XML well-formedness checking cannot see this. A module can therefore
pass a static check with zero findings and still fail to install.

This scanner reports, per module:

* search views whose ``<group>`` carries a disallowed attribute (**blocking**);
* other Odoo 19 construct regressions (blocking or advisory as marked).

It reports; it does not modify anything. Run it against the directory holding
the suite modules::

    python3 retrofit_scan.py /path/to/addons
    python3 retrofit_scan.py /path/to/addons --fix-preview
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


#: Attributes the Odoo 19 grammar permits on <group>.
GROUP_ALLOWED_ATTRS = {
    "position", "groups", "colspan", "rowspan", "fill", "height", "width",
    "name", "color", "invisible", "col",
}

#: (regex, severity, explanation) for non-view regressions.
CONSTRUCT_CHECKS = [
    (r"<tree[\s>]", "BLOCKING", "<tree> was replaced by <list> in Odoo 19"),
    (r"_sql_constraints\s*=", "SILENT",
     "VERIFIED: odoo/orm/model_classes.py L162 logs \"Model attribute "
     "'_sql_constraints' is no longer supported\" and IGNORES it. The module "
     "installs, but the constraints are NEVER CREATED in the database. Replace "
     "with models.Constraint"),
    (r"def name_get\b", "SILENT",
     "VERIFIED: name_get has 0 references in the Odoo 19 ORM. The method is "
     "never called; display names silently fall back to the default. Replace "
     "with _compute_display_name"),
    (r"oe_chatter", "VERIFY",
     "Odoo 19 core uses <chatter/> exclusively and zero mail_thread or "
     "mail_followers widgets. Whether the legacy div still renders was NOT "
     "verified; test on a running instance"),
    (r'name="numbercall"', "BLOCKING",
     "ir.cron.numbercall does not exist in Odoo 19"),
    (r'name="doall"', "BLOCKING", "ir.cron.doall does not exist in Odoo 19"),
    (r"\bstock\.production\.lot\b", "BLOCKING",
     "the model is stock.lot in Odoo 19"),
    (r"['\"]quality['\"]", "ADVISORY",
     "the 'quality' module is absent from Odoo 19 Community; verify this is "
     "not a dependency"),
]

#: ``groups_id`` needs context. A module declaring its own field called
#: groups_id is perfectly legal; only res.users and ir.ui.menu renamed theirs
#: to group_ids. These two patterns separate the cases.
GROUPS_ID_OWN_FIELD = re.compile(r"^\s*groups_id\s*=\s*fields\.", re.M)
GROUPS_ID_AS_KEY = re.compile(r"['\"]groups_id['\"]\s*:")


def scan_search_views(path):
    """Return findings for disallowed <group> attributes in search views."""
    findings = []
    try:
        doc = etree.parse(path)
    except etree.XMLSyntaxError as error:
        return [("BLOCKING", 0, f"file is not well-formed: {error}", "")]

    for record in doc.getroot().iter("record"):
        if record.get("model") != "ir.ui.view":
            continue
        arch = record.find("./field[@name='arch']")
        if arch is None:
            continue
        children = [c for c in arch if isinstance(c.tag, str)]
        if not children or children[0].tag != "search":
            continue
        for group in children[0].iter("group"):
            bad = set(group.attrib) - GROUP_ALLOWED_ATTRS
            if bad:
                original = etree.tostring(
                    group, encoding="unicode"
                ).split(">")[0] + ">"
                findings.append((
                    "BLOCKING",
                    group.sourceline or 0,
                    f"view '{record.get('id')}': <group> in a SEARCH view "
                    f"carries {sorted(bad)}, which the Odoo 19 grammar "
                    f"rejects at install time",
                    original.strip(),
                ))
    return findings


def scan_constructs(path):
    """Return findings for construct regressions in one file."""
    findings = []
    content = open(path, encoding="utf-8", errors="replace").read()
    if path.endswith(".xml"):
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    # groups_id: distinguish a module's own field from a res.users write.
    for match in re.finditer(r"\bgroups_id\b", content):
        line_start = content.rfind("\n", 0, match.start()) + 1
        line_end = content.find("\n", match.end())
        line_text = content[line_start:line_end if line_end != -1 else None]
        if GROUPS_ID_OWN_FIELD.match(line_text):
            continue  # the module declares its own field; legal
        line_no = content[:match.start()].count("\n") + 1
        if GROUPS_ID_AS_KEY.search(line_text) or 'name="groups_id"' in line_text:
            findings.append((
                "VERIFY", line_no,
                "groups_id written as a value. If the target is res.users or "
                "ir.ui.menu this FAILS: Odoo 19 renamed the field to "
                "group_ids (verified: res_users.py L257, ir_ui_menu.py L29). "
                "If the target is this module's own model, it is fine", "",
            ))
        else:
            findings.append((
                "ADVISORY", line_no,
                "groups_id referenced; confirm the target model. res.users and "
                "ir.ui.menu use group_ids in Odoo 19", "",
            ))

    for pattern, severity, explanation in CONSTRUCT_CHECKS:
        for match in re.finditer(pattern, content):
            line = content[:match.start()].count("\n") + 1
            findings.append((
                severity, line,
                f"{explanation} (found {match.group(0).strip()!r})", "",
            ))
    return findings


# ---------------------------------------------------------------------------
# Computed-field consistency
#
# VERIFIED against odoo/orm/registry.py, Registry.field_computed: Odoo groups
# every field of a model by its compute method and, for any group of two or
# more, warns when 'compute_sudo', 'precompute' or 'store' differ across the
# group.
#
# The 'store' case is the dangerous one. Odoo's own wording:
#
#     "accessing {non-stored} may recompute and update {stored}"
#
# Merely READING a non-stored field in the group triggers a recomputation that
# WRITES the stored field. When the stored field holds a regulated verdict, that
# is an uncontrolled write to a GxP record on a read path.
#
# VERIFIED default (odoo/orm/fields.py L448):
#     attrs['compute_sudo'] = attrs.get('compute_sudo', store)
# so compute_sudo defaults to the value of store. A group with mixed store
# therefore acquires mixed compute_sudo automatically unless it is set
# explicitly, which is why the two warnings usually appear together.
# ---------------------------------------------------------------------------

def _kwarg_bool(call, name):
    """Return a literal boolean keyword argument, or None when absent."""
    for keyword in call.keywords:
        if keyword.arg == name:
            if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, bool):
                return keyword.value.value
            return "?"  # present but not a literal
    return None


def _kwarg_str(call, name):
    """Return a literal string keyword argument, or None when absent."""
    for keyword in call.keywords:
        if keyword.arg == name:
            if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, str):
                return keyword.value.value
    return None


def scan_compute_consistency(module_path):
    """Return {relative path: [findings]} for inconsistent compute groups.

    Fields are grouped per MODEL, matching Odoo, so a group split across two
    classes or two files is still detected.
    """
    # model name -> compute method -> list of field descriptors
    models_map = {}

    for root, dirs, files in os.walk(module_path):
        dirs[:] = [
            d for d in dirs
            if d not in ("__pycache__", "rng", ".git", "tools", "doc")
        ]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            relative = os.path.relpath(path, module_path)
            try:
                tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                model_name = None
                pending = []
                for stmt in node.body:
                    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                        continue
                    target = stmt.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    value = stmt.value
                    if target.id == "_name" and isinstance(value, ast.Constant):
                        model_name = value.value
                    elif target.id == "_inherit" and model_name is None:
                        if isinstance(value, ast.Constant):
                            model_name = value.value
                        elif isinstance(value, (ast.List, ast.Tuple)) and value.elts:
                            first = value.elts[0]
                            if isinstance(first, ast.Constant):
                                model_name = first.value
                    elif (isinstance(value, ast.Call)
                          and isinstance(value.func, ast.Attribute)
                          and isinstance(value.func.value, ast.Name)
                          and value.func.value.id == "fields"):
                        compute = _kwarg_str(value, "compute")
                        if not compute:
                            continue
                        if _kwarg_str(value, "related"):
                            continue  # related fields do not share a group
                        store = _kwarg_bool(value, "store")
                        store = False if store is None else store
                        sudo = _kwarg_bool(value, "compute_sudo")
                        sudo_explicit = sudo is not None
                        if sudo is None:
                            sudo = store  # verified default: compute_sudo = store
                        precompute = _kwarg_bool(value, "precompute")
                        precompute = False if precompute is None else precompute
                        pending.append({
                            "field": target.id,
                            "compute": compute,
                            "store": store,
                            "sudo": sudo,
                            "sudo_explicit": sudo_explicit,
                            "precompute": precompute,
                            "path": relative,
                            "line": stmt.lineno,
                        })
                if model_name:
                    for entry in pending:
                        models_map.setdefault(model_name, []).append(entry)

    results = {}

    def add(entry_path, severity, line, message):
        results.setdefault(entry_path, []).append((severity, line, message, ""))

    for model_name in sorted(models_map):
        entries = models_map[model_name]

        # A field may be declared more than once for the same model: a genuine
        # override in an inheriting class, or an accidental redeclaration. Odoo
        # keeps ONE field either way, so the duplicates must not be treated as
        # separate members of a compute group. Keep the last declaration and
        # report the duplication when the declarations disagree.
        by_field = {}
        for entry in entries:
            by_field.setdefault(entry["field"], []).append(entry)

        resolved = []
        for field_name, declarations in by_field.items():
            resolved.append(declarations[-1])
            if len(declarations) < 2:
                continue
            differing = {
                (d["compute"], d["store"], d["sudo"]) for d in declarations
            }
            if len(differing) > 1:
                where = ", ".join(
                    f"{d['path']}:{d['line']} (store={d['store']})"
                    for d in declarations
                )
                add(declarations[0]["path"], "INTEGRITY",
                    declarations[0]["line"],
                    f"{model_name}.{field_name} is declared {len(declarations)} "
                    f"times with DIFFERENT attributes: {where}. Odoo keeps one "
                    f"declaration; which one depends on module load order, so "
                    f"whether this field is stored is not deterministic from "
                    f"the source. Resolve to a single declaration")
            else:
                add(declarations[0]["path"], "ADVISORY",
                    declarations[0]["line"],
                    f"{model_name}.{field_name} is declared "
                    f"{len(declarations)} times with identical attributes; "
                    f"the redundant declaration can be removed")

        groups = {}
        for entry in resolved:
            groups.setdefault(entry["compute"], []).append(entry)

        for compute, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            first = members[0]

            if len({m["store"] for m in members}) > 1:
                stored = [m["field"] for m in members if m["store"]]
                unstored = [m["field"] for m in members if not m["store"]]
                add(first["path"], "INTEGRITY", first["line"],
                    f"{model_name}.{compute}: inconsistent 'store'. Reading "
                    f"{', '.join(unstored)} may recompute and WRITE "
                    f"{', '.join(stored)}. When a stored field holds a "
                    f"regulated verdict this is an uncontrolled write on a "
                    f"read path. Use distinct compute methods for stored and "
                    f"non-stored fields")

            if len({m["sudo"] for m in members}) > 1:
                implicit = [m["field"] for m in members if not m["sudo_explicit"]]
                note = ""
                if implicit:
                    note = (f" ({', '.join(implicit)} inherit compute_sudo from "
                            f"their 'store' value)")
                add(first["path"], "INTEGRITY", first["line"],
                    f"{model_name}.{compute}: inconsistent 'compute_sudo'{note}. "
                    f"The same computation may run with different record "
                    f"visibility depending on the access path, so the result "
                    f"can differ. Set compute_sudo identically across the group")

            if len({m["precompute"] for m in members}) > 1:
                add(first["path"], "ADVISORY", first["line"],
                    f"{model_name}.{compute}: inconsistent 'precompute' across "
                    f"the group. Set it identically or use distinct compute "
                    f"methods")

    return results


def scan_module(module_path):
    """Return {relative path: [findings]} for one module."""
    results = {}
    for root, dirs, files in os.walk(module_path):
        # The 'tools' directory holds the checkers themselves, whose source
        # necessarily contains these patterns as string literals.
        dirs[:] = [
            d for d in dirs
            if d not in ("__pycache__", "rng", ".git", "tools", "doc")
        ]
        for name in sorted(files):
            if not name.endswith((".xml", ".py", ".csv")):
                continue
            # Checker sources necessarily contain these patterns as string
            # literals. Skip them wherever a module keeps them.
            if name in ("static_check.py", "retrofit_scan.py") or \
                    name.startswith("negative_control"):
                continue
            full = os.path.join(root, name)
            relative = os.path.relpath(full, module_path)
            findings = []
            if name.endswith(".xml"):
                findings += scan_search_views(full)
            findings += scan_constructs(full)
            if findings:
                results[relative] = findings

    for relative, findings in scan_compute_consistency(module_path).items():
        results.setdefault(relative, []).extend(findings)

    return results


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("addons_path",
                        help="directory containing the suite modules")
    parser.add_argument("--fix-preview", action="store_true",
                        help="show the corrected form of each blocking "
                             "search-view group")
    args = parser.parse_args()

    root = os.path.abspath(args.addons_path)
    if not os.path.isdir(root):
        _logger.info(f"Not a directory: {root}")
        return 2

    modules = sorted(
        name for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name, "__manifest__.py"))
    )
    if not modules:
        _logger.info(f"No Odoo module found under {root}")
        return 2

    _logger.info(f"Scanning {len(modules)} module(s) under {root}")
    _logger.info()
    total_blocking = 0
    total_advisory = 0
    total_silent = 0
    total_integrity = 0
    total_verify = 0
    affected = []

    for module in modules:
        results = scan_module(os.path.join(root, module))
        counts = {"BLOCKING": 0, "SILENT": 0, "INTEGRITY": 0,
                  "VERIFY": 0, "ADVISORY": 0}
        for findings in results.values():
            for severity, *_ in findings:
                counts[severity] = counts.get(severity, 0) + 1
        blocking = counts["BLOCKING"]
        advisory = counts["ADVISORY"]
        total_blocking += blocking
        total_advisory += advisory
        total_silent += counts["SILENT"]
        total_integrity += counts["INTEGRITY"]
        total_verify += counts["VERIFY"]
        if not results:
            _logger.info(f"  {module}: clean")
            continue
        affected.append(module)
        print(f"  {module}: {counts['BLOCKING']} blocking, "  # noqa: W8116  CLI script stdout
              f"{counts['SILENT']} silent, {counts['INTEGRITY']} integrity, "
              f"{counts['VERIFY']} verify, {counts['ADVISORY']} advisory")
        for relative, findings in sorted(results.items()):
            for severity, line, message, snippet in findings:
                _logger.info(f"      [{severity}] {relative}:{line} {message}")
                if args.fix_preview and snippet:
                    fixed = re.sub(r'\s+(expand|string)="[^"]*"', "", snippet)
                    _logger.info(f"          current: {snippet}")
                    _logger.info("          corrected: %s", fixed)
        _logger.info()

    _logger.info("=" * 70)
    _logger.info(f"SUMMARY across {len(affected)} of {len(modules)} module(s):")
    _logger.info("  BLOCKING %(total_blocking)4s  install fails", total_blocking)
    print(f"  SILENT   {total_silent:4}  installs, but the control is ABSENT "  # noqa: W8116  CLI script stdout
          f"- highest GxP risk")
    print(f"  INTEGRITY{total_integrity:4}  computed-field group may write a "  # noqa: W8116  CLI script stdout
          f"stored field on a read path")
    _logger.info(f"  VERIFY   {total_verify:4}  needs a check on a running instance")
    _logger.info("  ADVISORY %(total_advisory)4s  confirm intent", total_advisory)
    if affected:
        _logger.info(f"Modules needing attention: {', '.join(affected)}")
        _logger.info()
        _logger.info("The search-view <group> defect is corrected by deleting the")
        _logger.info("offending attributes, leaving a bare <group>. Odoo 19 core")
        _logger.info("itself writes the Group By block that way; see")
        _logger.info("addons/stock/views/stock_lot_views.xml, search_product_lot_filter.")
    return 1 if (total_blocking or total_silent or total_integrity) else 0


if __name__ == "__main__":
    sys.exit(main())
