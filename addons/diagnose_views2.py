#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Validate a module's view archs using Odoo's own schema loader.

Odoo does not ship a single ``view.rng``. It ships one schema per view type,
named ``<type>_view.rng`` (``search_view.rng``, ``form_view.rng`` and so on),
loaded by ``odoo.tools.view_validation.relaxng(view_type)``. This script uses
that loader directly, so it validates exactly what the server validates, on
whatever Odoo version is installed.

Run it on the machine that has Odoo installed::

    python3 diagnose_views2.py /mnt/extra-addons/ls_cosmetics

If Odoo cannot be imported, point the script at the schema directory::

    python3 diagnose_views2.py /mnt/extra-addons/ls_cosmetics \\
        --rng-dir /usr/lib/python3/dist-packages/odoo/addons/base/rng
"""

import argparse
import copy
import glob
import os
import sys

from lxml import etree
import logging

_logger = logging.getLogger(__name__)


#: Elements that are view roots rather than inheritance instructions.
ROOT_VIEW_TAGS = {
    "form", "list", "tree", "search", "kanban", "graph", "pivot",
    "calendar", "gantt", "activity", "map", "cohort", "dashboard",
}


class SchemaSource:
    """Supplies a RelaxNG validator for a given view type."""

    def __init__(self, rng_dir=None):
        """Prepare the schema source.

        :param rng_dir: directory holding ``<type>_view.rng`` files, or None
            to use Odoo's own loader.
        """
        self.rng_dir = rng_dir
        self.odoo_relaxng = None
        self.cache = {}
        self.origin = None
        if not rng_dir:
            try:
                from odoo.tools.view_validation import relaxng
                self.odoo_relaxng = relaxng
                self.origin = "odoo.tools.view_validation.relaxng"
            except Exception as error:  # noqa: BLE001 - report and fall back
                _logger.info("  (could not import Odoo's loader: %s)", error)
        if self.rng_dir:
            self.origin = f"directory {self.rng_dir}"

    def available(self):
        """Return the list of schema files found, for reporting."""
        directory = self.rng_dir
        if not directory:
            try:
                import odoo
                directory = os.path.join(
                    os.path.dirname(odoo.__file__), "addons", "base", "rng"
                )
            except Exception:  # noqa: BLE001
                return []
        return sorted(
            os.path.basename(path)
            for path in glob.glob(os.path.join(directory, "*.rng"))
        )

    def get(self, view_type):
        """Return a validator for a view type, or None when unavailable."""
        if view_type in self.cache:
            return self.cache[view_type]
        validator = None
        if self.odoo_relaxng is not None:
            try:
                validator = self.odoo_relaxng(view_type)
            except Exception:  # noqa: BLE001 - no schema for this type
                validator = None
        elif self.rng_dir:
            path = os.path.join(self.rng_dir, f"{view_type}_view.rng")
            if os.path.exists(path):
                validator = etree.RelaxNG(etree.parse(path))
        self.cache[view_type] = validator
        return validator


def iter_view_records(module_path):
    """Yield (file, xml_id, is_inherited, arch_root) for every ir.ui.view."""
    pattern = os.path.join(module_path, "**", "*.xml")
    for path in sorted(glob.glob(pattern, recursive=True)):
        if os.sep + "static" + os.sep in path:
            continue
        try:
            tree = etree.parse(path)
        except etree.XMLSyntaxError as error:
            _logger.info("  !! %s: not well formed: %s", path, error)
            continue
        for record in tree.iter("record"):
            if record.get("model") != "ir.ui.view":
                continue
            arch = record.find("field[@name='arch']")
            if arch is None:
                continue
            inherited = record.find("field[@name='inherit_id']") is not None
            roots = [child for child in arch if isinstance(child.tag, str)]
            if roots:
                yield path, record.get("id"), inherited, roots[0]


def validate(validator, element):
    """Validate one element. Return None when valid, else the error text."""
    document = etree.ElementTree(copy.deepcopy(element))
    if validator.validate(document):
        return None
    return [entry.message for entry in validator.error_log]


def variant_drop_expand(element):
    """Remove the ``expand`` attribute from every group."""
    clone = copy.deepcopy(element)
    for group in clone.iter("group"):
        group.attrib.pop("expand", None)
    return clone


def variant_flatten(element):
    """Hoist the children of every group up into the search element."""
    clone = copy.deepcopy(element)
    for group in list(clone.iter("group")):
        parent = group.getparent()
        if parent is None:
            continue
        index = list(parent).index(group)
        for offset, child in enumerate(list(group)):
            parent.insert(index + offset, child)
        parent.remove(group)
    return clone


def variant_group_bare(element):
    """Strip both ``expand`` and ``string`` from every group."""
    clone = copy.deepcopy(element)
    for group in clone.iter("group"):
        group.attrib.pop("expand", None)
        group.attrib.pop("string", None)
    return clone


def variant_no_separator(element):
    """Remove <separator/> elements, keeping the group as shipped."""
    clone = copy.deepcopy(element)
    for separator in clone.findall("separator"):
        clone.remove(separator)
    return clone


def variant_minimal(element):
    """Keep only the search fields, dropping filters, separators and groups."""
    clone = copy.deepcopy(element)
    for child in list(clone):
        if child.tag != "field":
            clone.remove(child)
    return clone


VARIANTS = (
    ("as shipped", copy.deepcopy),
    ('without expand="0"', variant_drop_expand),
    ("group wrapper removed", variant_flatten),
    ("group without expand or string", variant_group_bare),
    ("separators removed", variant_no_separator),
    ("fields only (minimal)", variant_minimal),
)


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", help="path to the module directory")
    parser.add_argument("--rng-dir", help="directory holding <type>_view.rng")
    arguments = parser.parse_args()

    source = SchemaSource(arguments.rng_dir)
    found = source.available()
    _logger.info("Schema files found:", ", ".join(found) if found else "(none listed)")
    _logger.info("Schema source:", source.origin or "unavailable")
    _logger.info()

    if source.odoo_relaxng is None and not source.rng_dir:
        sys.exit(
            "No schema source. Locate the directory with:\n"
            "  find / -name '*_view.rng' 2>/dev/null\n"
            "then re-run with --rng-dir /that/directory"
        )

    failures = []
    searches = []
    checked = 0
    skipped_types = set()

    _logger.info("=" * 72)
    _logger.info("PART 1 - every view arch against its schema")
    _logger.info("=" * 72)
    for path, xml_id, inherited, root in iter_view_records(arguments.module):
        relative = os.path.relpath(path, arguments.module)
        if root.tag not in ROOT_VIEW_TAGS:
            _logger.info("  --   %s: inheritance arch (<%s>), skipped", xml_id, root.tag)
            continue
        validator = source.get(root.tag)
        if validator is None:
            skipped_types.add(root.tag)
            _logger.info("  --   %s: no schema for <%s>, skipped", xml_id, root.tag)
            continue
        checked += 1
        errors = validate(validator, root)
        if errors:
            failures.append((relative, xml_id, root.tag, errors))
            _logger.info("  FAIL %s :: %s  (<%s>)", relative, xml_id, root.tag)
            for message in errors:
                _logger.info("         %s", message)
        else:
            note = " [inherited]" if inherited else ""
            _logger.info("  ok   %s :: %s  (<%s>)%s", relative, xml_id, root.tag, note)
        if root.tag == "search":
            searches.append((relative, xml_id, root))

    _logger.info("\n%s arch(s) validated, %s failure(s).", checked, len(failures))
    if skipped_types:
        _logger.info("No schema available for: %s", ', '.join(sorted(skipped_types)))
    _logger.info()

    _logger.info("=" * 72)
    _logger.info("PART 2 - which search syntax does this Odoo accept?")
    _logger.info("=" * 72)
    validator = source.get("search")
    if validator is None or not searches:
        _logger.info("  skipped (no search schema or no search views)")
        return 1 if failures else 0

    relative, xml_id, sample = searches[0]
    _logger.info("Candidate rewrites tested on %s (%s):\n", xml_id, relative)
    accepted = []
    for label, build in VARIANTS:
        errors = validate(validator, build(sample))
        if errors is None:
            _logger.info("  [ACCEPTED] %s", label)
            accepted.append(label)
        else:
            _logger.info("  [rejected] %s", label)
            for message in errors[:2]:
                _logger.info("             %s", message)
    _logger.info()
    _logger.info("Accepted forms:", ", ".join(accepted) if accepted else "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
