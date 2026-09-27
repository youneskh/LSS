#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Validate every view arch in a module against the local Odoo RNG schema.

Run this on the machine that has Odoo installed. It answers two questions
that cannot be answered without an Odoo installation:

1. Exactly which view archs fail schema validation, and why.
2. For search views, which rewrite of the "Group By" block is accepted by
   this particular Odoo version.

The second question is answered by generating candidate variants and
validating each one, rather than by guessing which syntax a given Odoo
version wants.

Usage::

    python3 diagnose_views.py /mnt/extra-addons/ls_cosmetics

Only lxml and the standard library are used. Odoo itself is imported only
to locate its RNG file; if that import fails, pass the path explicitly with
--rng.
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


def locate_rng(explicit=None):
    """Return the path to Odoo's view.rng.

    :param explicit: a path supplied on the command line, or None.
    :return: the path to view.rng.
    :raises SystemExit: when the schema cannot be located.
    """
    if explicit:
        if os.path.exists(explicit):
            return explicit
        sys.exit(f"RNG not found at {explicit}")
    candidates = []
    try:
        import odoo  # noqa: PLC0415  - located at runtime on purpose
        base = os.path.dirname(odoo.__file__)
        candidates.append(os.path.join(base, "addons", "base", "rng", "view.rng"))
        candidates.append(
            os.path.join(os.path.dirname(base), "addons", "base", "rng", "view.rng")
        )
    except ImportError:
        pass
    candidates += glob.glob("/usr/lib/python3/dist-packages/odoo/**/rng/view.rng",
                            recursive=True)
    candidates += glob.glob("/usr/lib/python3/*/odoo/**/rng/view.rng", recursive=True)
    candidates += glob.glob("/opt/odoo/**/rng/view.rng", recursive=True)
    for path in candidates:
        if path and os.path.exists(path):
            return path
    sys.exit(
        "Could not locate Odoo's view.rng. Find it with:\n"
        "  find / -name view.rng -path '*rng*' 2>/dev/null\n"
        "then re-run with --rng /path/to/view.rng"
    )


def iter_view_records(module_path):
    """Yield (file, xml_id, is_inherited, arch_root) for every ir.ui.view.

    :param module_path: path to the module directory.
    """
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
            if not roots:
                continue
            yield path, record.get("id"), inherited, roots[0]


def validate(relaxng, element):
    """Validate one element against the schema.

    :return: None when valid, else the error log as a string.
    """
    document = etree.ElementTree(copy.deepcopy(element))
    if relaxng.validate(document):
        return None
    return "\n".join(f"      {entry.message}" for entry in relaxng.error_log)


def variant_drop_expand(search_element):
    """Variant 1: remove the ``expand`` attribute from Group By blocks."""
    clone = copy.deepcopy(search_element)
    for group in clone.iter("group"):
        group.attrib.pop("expand", None)
    return clone


def variant_flatten(search_element):
    """Variant 2: hoist group-by filters out of the <group> wrapper."""
    clone = copy.deepcopy(search_element)
    for group in list(clone.iter("group")):
        parent = group.getparent()
        if parent is None:
            continue
        index = list(parent).index(group)
        for offset, child in enumerate(list(group)):
            parent.insert(index + offset, child)
        parent.remove(group)
    return clone


def variant_group_bare(search_element):
    """Variant 3: <group> with neither expand nor string."""
    clone = copy.deepcopy(search_element)
    for group in clone.iter("group"):
        group.attrib.pop("expand", None)
        group.attrib.pop("string", None)
    return clone


VARIANTS = (
    ("as shipped", lambda element: copy.deepcopy(element)),
    ("without expand=\"0\"", variant_drop_expand),
    ("group wrapper removed", variant_flatten),
    ("group without expand or string", variant_group_bare),
)


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", help="path to the module directory")
    parser.add_argument("--rng", help="explicit path to Odoo's view.rng")
    arguments = parser.parse_args()

    rng_path = locate_rng(arguments.rng)
    _logger.info("Schema: %s\n", rng_path)
    relaxng = etree.RelaxNG(etree.parse(rng_path))

    failures = []
    search_elements = []
    checked = 0

    _logger.info("=" * 72)
    _logger.info("PART 1 - every view arch against the schema")
    _logger.info("=" * 72)
    for path, xml_id, inherited, root in iter_view_records(arguments.module):
        relative = os.path.relpath(path, arguments.module)
        if root.tag not in ROOT_VIEW_TAGS:
            _logger.info("  -- %s: inheritance arch (<%s>), skipped", xml_id, root.tag)
            continue
        checked += 1
        errors = validate(relaxng, root)
        if errors:
            failures.append((relative, xml_id, root.tag, errors))
            _logger.info("  FAIL %s :: %s  (<%s>)", relative, xml_id, root.tag)
            _logger.info(errors)
        else:
            note = " [inherited]" if inherited else ""
            _logger.info("  ok   %s :: %s  (<%s>)%s", relative, xml_id, root.tag, note)
        if root.tag == "search":
            search_elements.append((relative, xml_id, root))

    _logger.info("\n%s arch(s) validated, %s failure(s).\n", checked, len(failures))

    _logger.info("=" * 72)
    _logger.info("PART 2 - which Group By syntax does this Odoo accept?")
    _logger.info("=" * 72)
    if not search_elements:
        _logger.info("  no search views found")
        return 1 if failures else 0

    relative, xml_id, sample = search_elements[0]
    _logger.info("Testing candidate rewrites on %s (%s):\n", xml_id, relative)
    accepted = []
    for label, build in VARIANTS:
        errors = validate(relaxng, build(sample))
        status = "ACCEPTED" if errors is None else "rejected"
        _logger.info("  [%s] %s", status, label)
        if errors:
            first = errors.strip().splitlines()[:2]
            for line in first:
                _logger.info("           %s", line.strip())
        else:
            accepted.append(label)
    _logger.info()
    if accepted:
        _logger.info("Use this form: %s", accepted[0])
    else:
        _logger.info("No candidate was accepted. Paste PART 1 output back for analysis.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
