#!/usr/bin/env python3
# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Negative control harness for :mod:`static_check`.

A static checker that reports no finding is worthless until it is shown to
report findings when they exist. This harness copies the module to a scratch
directory, injects one known fault at a time, runs the checker, and asserts
that the expected finding code is raised.

A fault the checker fails to detect is itself reported as a failure of this
harness. Run it whenever the checker changes.

Usage::

    python3 tools/negative_control.py [module_path]
"""

from __future__ import annotations

import importlib.util
import io
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
import logging

_logger = logging.getLogger(__name__)


def load_checker(tools_dir):
    """Import :mod:`static_check` from the given tools directory."""
    spec = importlib.util.spec_from_file_location(
        "ls_lab_static_check", os.path.join(tools_dir, "static_check.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------

def _edit(path, old, new, required=True):
    """Return a mutation callable replacing ``old`` with ``new``."""
    def mutate(root):
        full = os.path.join(root, path)
        content = open(full, encoding="utf-8").read()
        if old not in content:
            if required:
                raise AssertionError(
                    f"anchor not found in {path}: {old[:70]!r}"
                )
            return
        open(full, "w", encoding="utf-8").write(content.replace(old, new, 1))
    return mutate


def _append(path, text):
    """Return a mutation callable appending ``text`` to a file."""
    def mutate(root):
        with open(os.path.join(root, path), "a", encoding="utf-8") as handle:
            handle.write(text)
    return mutate


def _delete(path):
    """Return a mutation callable deleting a file."""
    def mutate(root):
        os.remove(os.path.join(root, path))
    return mutate


def _drop_csv_line(path, needle):
    """Return a mutation callable removing the CSV row containing ``needle``."""
    def mutate(root):
        full = os.path.join(root, path)
        lines = open(full, encoding="utf-8").read().splitlines(keepends=True)
        kept = [line for line in lines if needle not in line]
        if len(kept) == len(lines):
            raise AssertionError(f"no CSV row containing {needle!r}")
        open(full, "w", encoding="utf-8").writelines(kept)
    return mutate


# ---------------------------------------------------------------------------
# Fault catalogue
# ---------------------------------------------------------------------------

SEARCH_GROUP_ANCHOR = """                <group>
                    <filter name="group_by_state" string="Status"
                            domain="[]" context="{'group_by': 'state'}"/>"""

FAULTS = [
    # -- the ls_cosmetics defect class ----------------------------------
    (
        "F01", "VIEW003",
        "search view <group> carries expand and string (the install-time defect)",
        _edit(
            "views/ls_lab_test_method_views.xml",
            SEARCH_GROUP_ANCHOR,
            SEARCH_GROUP_ANCHOR.replace(
                "<group>", '<group expand="0" string="Group By">'
            ),
        ),
    ),
    (
        "F02", "VIEW003",
        "search view <group> carries string only",
        _edit(
            "views/ls_lab_sample_views.xml",
            SEARCH_GROUP_ANCHOR,
            SEARCH_GROUP_ANCHOR.replace("<group>", '<group string="Group By">'),
        ),
    ),
    (
        "F03", "RNG001",
        "search view <group> carries an attribute the RNG rejects",
        _edit(
            "views/ls_lab_oos_views.xml",
            SEARCH_GROUP_ANCHOR,
            SEARCH_GROUP_ANCHOR.replace("<group>", '<group expand="0">'),
        ),
    ),
    (
        "F04", "RNG001",
        "list view carries an attribute the RNG rejects",
        _edit(
            "views/ls_lab_coa_views.xml",
            '<list decoration-success="state == \'issued\'"',
            '<list bogus_attribute="1" decoration-success="state == \'issued\'"',
        ),
    ),
    (
        "F05", "RNG001",
        "search view <filter> is missing its mandatory name attribute",
        _edit(
            "views/ls_lab_specification_views.xml",
            '<filter name="filter_draft" string="Draft"',
            '<filter string="Draft"',
        ),
    ),
    # -- view reference integrity ----------------------------------------
    (
        "F06", "VIEW001",
        "form view references a field that does not exist",
        _edit(
            "views/ls_lab_sample_views.xml",
            '<field name="sampling_point"/>',
            '<field name="sampling_point_typo"/>',
        ),
    ),
    (
        "F07", "VIEW001",
        "nested list inside a One2many references a field of the wrong model",
        _edit(
            "views/ls_lab_specification_views.xml",
            '<field name="text_criterion"/>',
            '<field name="received_date"/>',
        ),
    ),
    (
        "F08", "VIEW002",
        "button calls a method that does not exist",
        _edit(
            "views/ls_lab_sample_views.xml",
            'name="action_start_testing" type="object"',
            'name="action_start_testing_typo" type="object"',
        ),
    ),
    (
        "F09", "REF001",
        "ref points at an external identifier that is never declared",
        _edit(
            "views/ls_lab_menus.xml",
            'action="ls_lab_action_sample"',
            'action="ls_lab_action_sample_missing"',
        ),
    ),
    # -- Odoo 19 construct regressions ------------------------------------
    (
        "F10", "FORB001",
        "<tree> used instead of <list>",
        _edit(
            "views/ls_lab_stability_views.xml",
            "<list default_order=\"scheduled_date, sequence, id\"",
            "<tree default_order=\"scheduled_date, sequence, id\"",
        ),
    ),
    (
        "F11", "FORB001",
        "_sql_constraints used instead of models.Constraint",
        _append(
            "models/ls_lab_coa.py",
            "\n\n_sql_constraints = [('x', 'UNIQUE (name)', 'x')]\n",
        ),
    ),
    (
        "F12", "FORB001",
        "ir.cron declares numbercall, removed in Odoo 19",
        _edit(
            "data/ir_cron_data.xml",
            "<field name=\"interval_type\">days</field>\n            <field name=\"active\" eval=\"True\"/>",
            "<field name=\"interval_type\">days</field>\n            <field name=\"numbercall\">-1</field>\n            <field name=\"active\" eval=\"True\"/>",
        ),
    ),
    (
        "F13", "FORB001",
        "groups_id used instead of group_ids",
        _append(
            "models/ls_lab_sample.py",
            "\n\n# groups_id = False\n",
        ),
    ),
    (
        "F14", "FORB001",
        "oe_chatter div used instead of the <chatter/> element",
        _edit(
            "views/ls_lab_coa_views.xml",
            "<chatter/>",
            '<div class="oe_chatter"/>',
        ),
    ),
    (
        "F15", "FORB001",
        "name_get used instead of _compute_display_name",
        _append(
            "models/ls_lab_oos.py",
            "\n\ndef name_get(self):\n    return []\n",
        ),
    ),
    (
        "F16", "FORB001",
        "stock.production.lot used instead of stock.lot",
        _edit(
            "models/ls_lab_sample.py",
            'comodel_name="stock.lot"',
            'comodel_name="stock.production.lot"',
        ),
    ),
    (
        "F17", "FORB001",
        "raw SQL execution introduced",
        _append(
            "models/ls_lab_test_result.py",
            "\n\ndef _bad(self):\n    self.env.cr.execute('SELECT 1')\n",
        ),
    ),
    (
        "F18", "FORB001",
        "placeholder marker left in the source",
        _append("models/ls_lab_coa.py", "\n\n# TODO finish this\n"),
    ),
    # -- security and manifest --------------------------------------------
    (
        "F19", "ACL003",
        "an ACL row is missing for one group on one model",
        _drop_csv_line("security/ir.model.access.csv", "access_sample_manager"),
    ),
    (
        "F20", "ACL004",
        "an ACL row references a model the module does not declare",
        _append(
            "security/ir.model.access.csv",
            "access_ghost_manager,ls.lab.ghost.manager,model_ls_lab_ghost,"
            "ls_lab.ls_lab_group_manager,1,1,1,1\n",
        ),
    ),
    (
        "F21", "MAN004",
        "a manifest data file does not exist on disk",
        _delete("views/ls_lab_menus.xml"),
    ),
    (
        "F22", "MAN006",
        "the absent Odoo 19 'quality' module is declared as a dependency",
        _edit("__manifest__.py", '"stock",', '"stock",\n        "quality",'),
    ),
    (
        "F23", "MAN005",
        "a suite module is declared as a hard dependency",
        _edit("__manifest__.py", '"stock",', '"stock",\n        "ls_qms",'),
    ),
    # -- structural integrity ---------------------------------------------
    (
        "F24", "PY001",
        "a Python file no longer compiles",
        _append("models/ls_lab_sample.py", "\n\ndef broken(:\n    pass\n"),
    ),
    (
        "F25", "XML001",
        "an XML file is not well-formed",
        _append("views/ls_lab_coa_views.xml", "\n<unclosed>\n"),
    ),
]


def run_case(module_path, mutate):
    """Apply one mutation to a scratch copy and return the finding codes."""
    with tempfile.TemporaryDirectory() as scratch:
        target = os.path.join(scratch, os.path.basename(module_path))
        shutil.copytree(module_path, target)
        mutate(target)
        checker_module = load_checker(os.path.join(target, "tools"))
        checker = checker_module.ModuleChecker(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            findings = checker.run()
        return {finding.code for finding in findings}


def main():
    """Run every seeded fault and report whether the checker caught it."""
    module_path = (
        sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    module_path = os.path.abspath(module_path)

    # Baseline: the unmutated module must be clean, otherwise the harness
    # cannot distinguish an injected fault from a pre-existing one.
    baseline = run_case(module_path, lambda root: None)
    _logger.info(
        "Baseline (no fault injected): %d finding code(s) %s",
        len(baseline),
        sorted(baseline) if baseline else "- clean",
    )

    caught, missed = 0, []
    for fault_id, expected_code, description, mutate in FAULTS:
        try:
            codes = run_case(module_path, mutate)
        except AssertionError as error:
            _logger.info(f"  {fault_id}  HARNESS ERROR  {description}: {error}")
            missed.append((fault_id, description, "harness anchor missing"))
            continue
        detected = expected_code in (codes - baseline)
        status = "CAUGHT " if detected else "MISSED "
        _logger.info(f"  {fault_id}  {status} expect {expected_code:<8} {description}")
        if detected:
            caught += 1
        else:
            missed.append((fault_id, description, sorted(codes - baseline)))

    _logger.info()
    _logger.info(f"RESULT: {caught}/{len(FAULTS)} seeded faults detected")
    if missed:
        _logger.info()
        _logger.info("Undetected faults:")
        for fault_id, description, codes in missed:
            _logger.info(f"  {fault_id}: {description} (raised: {codes})")
        return 1
    _logger.info("The checker detects every fault it claims to detect.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
