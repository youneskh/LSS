#!/usr/bin/env python3
"""Negative control for static_check.py.

A static checker that has never been observed to fail proves nothing. This
harness copies the module to a temporary location, injects one deliberate fault
at a time, runs the checker, and asserts that the checker reports an error
containing an expected fragment.

A fault that the checker fails to detect is reported as a MISS, which means the
checker's clean result on the real module cannot be relied on for that class of
defect.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import logging

_logger = logging.getLogger(__name__)


SOURCE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ls_environmental_monitoring")


def inject_replace(root, relpath, old, new):
    path = os.path.join(root, relpath)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    if old not in content:
        raise AssertionError("fixture text not found in %s: %r" % (relpath, old[:60]))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content.replace(old, new, 1))


def inject_append(root, relpath, text):
    with open(os.path.join(root, relpath), "a", encoding="utf-8") as fh:
        fh.write(text)


def inject_delete(root, relpath):
    os.remove(os.path.join(root, relpath))


# Each case: label, mutation callable, fragment expected in the checker output.
CASES = [
    (
        "view references a field that does not exist",
        lambda r: inject_replace(
            r, "views/ls_env_grade_views.xml",
            '<field name="code"/>', '<field name="nonexistent_field"/>'),
        "does not exist on that model",
    ),
    (
        "sub-view references a field absent from the comodel",
        lambda r: inject_replace(
            r, "views/ls_env_plan_views.xml",
            '<field name="frequency_unit"/>', '<field name="bogus_line_field"/>'),
        "does not exist on that model",
    ),
    (
        "XML ref points at an undefined id",
        lambda r: inject_replace(
            r, "data/ls_env_cron.xml",
            'ref="model_ls_env_sample"', 'ref="model_does_not_exist"'),
        "does not resolve to a known XML id",
    ),
    (
        "manifest lists a file that is absent",
        lambda r: inject_replace(
            r, "__manifest__.py",
            '"views/ls_env_menus.xml",', '"views/ls_env_missing.xml",'),
        "does not exist",
    ),
    (
        "XML file exists but is not in the manifest",
        lambda r: inject_replace(
            r, "__manifest__.py",
            '        "views/ls_env_grade_views.xml",\n', ""),
        "is not listed in the manifest",
    ),
    (
        "model has no access control list row",
        lambda r: inject_replace(
            r, "security/ir.model.access.csv",
            "access_grade_viewer,ls.env.grade viewer,model_ls_env_grade,"
            "ls_environmental_monitoring.group_ls_env_viewer,1,0,0,0\n", ""),
        "",  # only the manager/technician rows remain, so expect no error here
    ),
    (
        "access row references an unknown model",
        lambda r: inject_replace(
            r, "security/ir.model.access.csv",
            "model_ls_env_grade,ls_environmental_monitoring.group_ls_env_manager",
            "model_ls_env_ghost,ls_environmental_monitoring.group_ls_env_manager"),
        "does not correspond to any model",
    ),
    (
        "duplicate access control list id",
        lambda r: inject_append(
            r, "security/ir.model.access.csv",
            "access_grade_manager,dup,model_ls_env_grade,"
            "ls_environmental_monitoring.group_ls_env_manager,1,1,1,1\n"),
        "Duplicate access control list id",
    ),
    (
        "non-boolean permission value",
        lambda r: inject_replace(
            r, "security/ir.model.access.csv",
            "access_grade_viewer,ls.env.grade viewer,model_ls_env_grade,"
            "ls_environmental_monitoring.group_ls_env_viewer,1,0,0,0",
            "access_grade_viewer,ls.env.grade viewer,model_ls_env_grade,"
            "ls_environmental_monitoring.group_ls_env_viewer,yes,0,0,0"),
        "non-boolean value",
    ),
    (
        "removed <tree> element reintroduced",
        lambda r: (
            inject_replace(
                r, "views/ls_env_grade_views.xml",
                '<list string="Cleanroom Grades">', '<tree string="Cleanroom Grades">'),
            inject_replace(r, "views/ls_env_grade_views.xml", "</list>", "</tree>"),
        ),
        "renamed to <list>",
    ),
    (
        "removed attrs dictionary reintroduced",
        lambda r: inject_replace(
            r, "views/ls_env_grade_views.xml",
            '<field name="sequence"/>',
            '<field name="sequence" attrs="{\'invisible\': [(\'code\',\'=\',False)]}"/>'),
        "attrs dictionary was removed",
    ),
    (
        "removed _sql_constraints reintroduced",
        lambda r: inject_append(
            r, "models/ls_env_grade.py",
            "\n\n_sql_constraints = [('x', 'UNIQUE(code)', 'msg')]\n"),
        "_sql_constraints was replaced",
    ),
    (
        "removed read_group call reintroduced",
        lambda r: inject_append(
            r, "models/ls_env_grade.py",
            "\n\ndef _legacy(self):\n    return self.read_group([], [], [])\n"),
        "read_group was replaced",
    ),
    (
        "raw SQL execution introduced",
        lambda r: inject_append(
            r, "models/ls_env_grade.py",
            "\n\ndef _raw(self):\n    self.env.cr.execute('SELECT 1')\n"),
        "executes raw SQL",
    ),
    (
        "placeholder token left in source",
        lambda r: inject_append(
            r, "models/ls_env_grade.py", "\n# TODO finish this\n"),
        "placeholder token",
    ),
    (
        "malformed XML",
        lambda r: inject_replace(
            r, "views/ls_env_grade_views.xml", "</odoo>", "</odo>"),
        "not well-formed",
    ),
    (
        "Python syntax error",
        lambda r: inject_append(
            r, "models/ls_env_grade.py", "\ndef broken(:\n    pass\n"),
        "syntax error",
    ),
    (
        "missing licence header",
        lambda r: inject_replace(
            r, "models/ls_env_grade.py",
            "# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).",
            "# proprietary"),
        "missing the AGPL-3.0 licence header",
    ),
    (
        "manifest version does not follow the convention",
        lambda r: inject_replace(
            r, "__manifest__.py", '"version": "19.0.1.0.0"', '"version": "1.0"'),
        "does not follow the 19.0.x.y.z convention",
    ),
    (
        "trailing whitespace introduced",
        lambda r: inject_append(
            r, "models/ls_env_grade.py", "\nX = 1   \n"),
        "trailing whitespace",
    ),
]


def run_checker(root):
    result = subprocess.run(
        [sys.executable, os.path.join(root, "static_check.py")],
        capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main():
    # Confirm the pristine module passes before injecting anything.
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "ls_environmental_monitoring")
        shutil.copytree(SOURCE, root)
        code, output = run_checker(root)
        if code != 0:
            _logger.info("BASELINE FAILED: the unmodified module does not pass.")
            _logger.info(output)
            return 1
    _logger.info("Baseline: unmodified module passes.\n")

    misses = []
    for index, (label, mutate, expected) in enumerate(CASES, start=1):
        if not expected:
            _logger.info("%2d. SKIP  %s (not an error condition by design)", index, label)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "ls_environmental_monitoring")
            shutil.copytree(SOURCE, root)
            try:
                mutate(root)
            except AssertionError as exc:
                _logger.info("%2d. SETUP FAILED  %s -> %s", index, label, exc)
                misses.append(label)
                continue
            code, output = run_checker(root)
            detected = code != 0 and expected.lower() in output.lower()
            _logger.info("%2d. %s  %s", index, "CAUGHT" if detected else "MISS  ", label)
            if not detected:
                misses.append(label)

    _logger.info("\n" + "=" * 72)
    if misses:
        _logger.info("NEGATIVE CONTROL FAILED: %d fault(s) not detected", len(misses))
        for label in misses:
            _logger.info("  - %s", label)
        return 1
    _logger.info("NEGATIVE CONTROL PASSED: every injected fault was detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
