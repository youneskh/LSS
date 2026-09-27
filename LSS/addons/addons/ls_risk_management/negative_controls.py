#!/usr/bin/env python3
"""Negative controls for ``static_check.py``.

A static checker that reports nothing proves nothing until it has been shown
to fail on known-bad input. This harness copies the module to a temporary
directory, injects one deliberate fault at a time, runs the checker, and
asserts that the expected finding appears.

Run from the module root::

    python3 negative_controls.py

Exit status is 0 when every control behaved as expected.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import logging

_logger = logging.getLogger(__name__)


MODULE_ROOT = os.path.dirname(os.path.abspath(__file__))


def substitute(path, old, new):
    """Return a mutator that replaces text in a file.

    :param str path: module-relative path of the file to mutate.
    :param str old: text to replace; must occur at least once.
    :param str new: replacement text.
    :return: a callable taking the working directory.
    :rtype: callable
    """

    def apply(workdir):
        target = os.path.join(workdir, path)
        content = open(target, encoding="utf-8").read()
        if old not in content:
            raise AssertionError(f"fault target not present in {path}: {old!r}")
        open(target, "w", encoding="utf-8").write(content.replace(old, new, 1))

    return apply


def pair(path, *replacements):
    """Return a mutator applying several replacements to one file.

    Used where a fault must keep the file well formed, such as renaming both
    the opening and the closing tag of an element.

    :param str path: module-relative path of the file to mutate.
    :param replacements: ``(old, new)`` tuples applied in order.
    :return: a callable taking the working directory.
    :rtype: callable
    """

    def apply(workdir):
        target = os.path.join(workdir, path)
        content = open(target, encoding="utf-8").read()
        for old, new in replacements:
            if old not in content:
                raise AssertionError(f"fault target not present in {path}: {old!r}")
            content = content.replace(old, new, 1)
        open(target, "w", encoding="utf-8").write(content)

    return apply


def append(path, text):
    """Return a mutator that appends text to a file.

    :param str path: module-relative path of the file.
    :param str text: text to append.
    :return: a callable taking the working directory.
    :rtype: callable
    """

    def apply(workdir):
        with open(os.path.join(workdir, path), "a", encoding="utf-8") as handle:
            handle.write(text)

    return apply


def write(path, text):
    """Return a mutator that creates a new file.

    :param str path: module-relative path of the new file.
    :param str text: file contents.
    :return: a callable taking the working directory.
    :rtype: callable
    """

    def apply(workdir):
        with open(os.path.join(workdir, path), "w", encoding="utf-8") as handle:
            handle.write(text)

    return apply


#: Each control is a name, a mutator, and a pattern the finding must match.
CONTROLS = [
    (
        "view references a nonexistent field",
        substitute(
            "views/ls_risk_register_views.xml",
            '<field name="title"/>',
            '<field name="field_that_does_not_exist"/>',
        ),
        r"view field 'field_that_does_not_exist' does not exist",
    ),
    (
        "view references a nonexistent method",
        substitute(
            "views/ls_risk_register_views.xml",
            'name="action_start_risk_control" type="object"',
            'name="action_method_that_does_not_exist" type="object"',
        ),
        r"button method 'action_method_that_does_not_exist' does not exist",
    ),
    (
        "embedded list references a field of the wrong model",
        substitute(
            "views/ls_risk_register_views.xml",
            '<field name="assessment_type"/>\n'
            + " " * 36
            + '<field name="assessment_date"/>',
            '<field name="assessment_type"/>\n'
            + " " * 36
            + '<field name="review_interval_months"/>',
        ),
        r"view field 'review_interval_months' does not exist on model 'ls\.risk\.assessment'",
    ),
    (
        "unresolved external identifier",
        substitute(
            "views/ls_risk_register_views.xml",
            'ref="view_ls_risk_register_search"',
            'ref="view_that_does_not_exist"',
        ),
        r"unresolved ref 'view_that_does_not_exist'",
    ),
    (
        "unresolved group on a button",
        substitute(
            "views/ls_risk_register_views.xml",
            'groups="ls_risk_management.group_risk_manager"',
            'groups="ls_risk_management.group_that_does_not_exist"',
        ),
        r"unresolved group 'ls_risk_management\.group_that_does_not_exist'",
    ),
    (
        "model without an access control list",
        substitute(
            "security/ir.model.access.csv",
            "access_ls_risk_fmea_line_viewer,ls.risk.fmea.line viewer,"
            "model_ls_risk_fmea_line,group_risk_viewer,1,0,0,0\n"
            "access_ls_risk_fmea_line_analyst,ls.risk.fmea.line analyst,"
            "model_ls_risk_fmea_line,group_risk_analyst,1,1,1,1\n"
            "access_ls_risk_fmea_line_manager,ls.risk.fmea.line manager,"
            "model_ls_risk_fmea_line,group_risk_manager,1,1,1,1\n",
            "",
        ),
        r"model 'ls\.risk\.fmea\.line' has no ACL line",
    ),
    (
        "ACL naming an unknown model",
        append(
            "security/ir.model.access.csv",
            "access_bogus,bogus,model_ls_risk_nonexistent,group_risk_viewer,1,0,0,0\n",
        ),
        r"ACL references unknown model 'ls\.risk\.nonexistent'",
    ),
    (
        "ACL naming an unknown group",
        append(
            "security/ir.model.access.csv",
            "access_bogus_group,bogus,model_ls_risk_register,group_nonexistent,1,0,0,0\n",
        ),
        r"ACL references unknown group 'group_nonexistent'",
    ),
    (
        "ACL with a non-boolean permission",
        append(
            "security/ir.model.access.csv",
            "access_bad_perm,bad,model_ls_risk_register,group_risk_viewer,2,0,0,0\n",
        ),
        r"perm_read must be 0 or 1",
    ),
    (
        "deprecated <tree> element",
        pair(
            "views/ls_risk_category_views.xml",
            ('<list string="Risk Categories">', '<tree string="Risk Categories">'),
            ("</list>", "</tree>"),
        ),
        r"'<tree>' was renamed to '<list>'",
    ),
    (
        "_sql_constraints instead of models.Constraint",
        append(
            "models/constants.py",
            "\n# _sql_constraints = [('x', 'UNIQUE(x)', 'msg')]\n",
        ),
        r"forbidden token '_sql_constraints'",
    ),
    (
        "TODO marker left in source",
        append("models/constants.py", "\n# TODO finish this later\n"),
        r"forbidden token 'TODO'",
    ),
    (
        "raw SQL execution",
        append(
            "models/constants.py",
            "\ndef unsafe(self):\n    self.env.cr.execute('SELECT 1')\n",
        ),
        r"raw SQL execution is not permitted",
    ),
    (
        "bare _() translation helper",
        substitute(
            "models/ls_risk_register.py",
            'self.env._("No linked record is set on this risk.")',
            '_("No linked record is set on this risk.")',
        ),
        r"use self\.env\._\(\)",
    ),
    (
        "manifest lists a missing file",
        substitute(
            "__manifest__.py",
            '"data/ir_cron_data.xml",',
            '"data/file_that_does_not_exist.xml",',
        ),
        r"listed file does not exist",
    ),
    (
        "data file on disk missing from the manifest",
        write("views/orphan_view.xml", '<?xml version="1.0"?>\n<odoo/>\n'),
        r"file on disk is not listed in the manifest",
    ),
    (
        "invalid version string",
        substitute("__manifest__.py", '"version": "19.0.1.0.0"', '"version": "1.0"'),
        r"is not of the form 19\.0\.x\.y\.z",
    ),
    (
        "trailing whitespace",
        append("models/constants.py", "\nSPACER = 1   \n"),
        r"trailing whitespace",
    ),
    (
        "tab character",
        append("models/constants.py", "\nif True:\n\tSPACER = 1\n"),
        r"tab character",
    ),
    (
        "overlong Python line",
        append("models/constants.py", "\nLONG = " + '"x" * 1 + ' * 30 + '"end"\n'),
        r"line exceeds 100 characters",
    ),
    (
        "malformed XML",
        append("views/ls_risk_menus.xml", "<unclosed>\n"),
        r"XML syntax error",
    ),
    (
        "Python syntax error",
        append("models/constants.py", "\ndef broken(:\n    pass\n"),
        r"Python syntax error",
    ),
]


def run_control(name, mutator, pattern):
    """Apply one fault and assert that the checker reports it.

    :param str name: description of the control.
    :param mutator: callable applying the fault.
    :param str pattern: regular expression the output must match.
    :return: ``True`` when the control behaved as expected.
    :rtype: bool
    """
    with tempfile.TemporaryDirectory() as workdir:
        target = os.path.join(workdir, "module")
        shutil.copytree(
            MODULE_ROOT,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        mutator(target)
        result = subprocess.run(
            [sys.executable, "static_check.py"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr
        detected = bool(re.search(pattern, output))
        if detected and result.returncode == 0:
            _logger.info("  FAIL  %s: finding reported but exit status was 0", name)
            return False
        if not detected:
            _logger.info("  FAIL  %s: expected /%s/ but it was not reported", name, pattern)
            return False
        _logger.info("  ok    %s", name)
        return True


def main():
    """Run every negative control.

    :return: process exit status.
    :rtype: int
    """
    baseline = subprocess.run(
        [sys.executable, "static_check.py"],
        cwd=MODULE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _logger.info("Baseline (unmodified module):")
    if baseline.returncode != 0:
        _logger.info("  FAIL  the unmodified module already reports findings")
        _logger.info(baseline.stdout)
        return 1
    _logger.info("  ok    clean, exit status 0\n")

    _logger.info("Negative controls (%s):", len(CONTROLS))
    passed = sum(run_control(*control) for control in CONTROLS)
    _logger.info("\n%s/%s controls behaved as expected.", passed, len(CONTROLS))
    return 0 if passed == len(CONTROLS) else 1


if __name__ == "__main__":
    sys.exit(main())
