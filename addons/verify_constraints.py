#!/usr/bin/env python3
# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Generate SQL that proves ``models.Constraint`` declarations reached the database.

WHY THIS IS NECESSARY
---------------------

Converting ``_sql_constraints`` to ``models.Constraint`` makes Odoo *try* to
create the constraint. It does not guarantee the constraint exists afterwards.

Verified in odoo/orm/registry.py::

    def finalize_constraints(self, cr):
        for func in self._constraint_queue.values():
            try:
                with cr.savepoint(flush=False):
                    func(cr)
            except Exception as e:
                # warn only, this is not a deployment showstopper, and
                # can sometimes be a transient error
                _schema.warning(*e.args)

If rows already in the table violate the constraint - which is likely, because
the constraint was never enforced while ``_sql_constraints`` was being ignored -
``ALTER TABLE ... ADD CONSTRAINT`` fails, the upgrade **still succeeds**, and the
constraint is **still absent**. The only WARNING lands in the log.

So a converted module can look fixed and not be. This tool emits two SQL
scripts:

1.  **PRE-FLIGHT** - run BEFORE the upgrade. Finds rows that would violate each
    constraint. Anything returned must be remediated first, under your change
    control procedure.
2.  **VERIFY** - run AFTER the upgrade. Lists every expected constraint and
    whether PostgreSQL actually has it.

Constraint naming is derived exactly as Odoo derives it
(odoo/orm/table_objects.py): attribute ``_foo`` on a model whose table is
``bar`` produces the database constraint ``bar_foo``.

Usage::

    python3 verify_constraints.py <module_path> -o checks
    # produces checks_preflight.sql and checks_verify.sql
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
import logging

_logger = logging.getLogger(__name__)


def model_table(model_name, explicit_table):
    """Return the table name Odoo will use for a model."""
    if explicit_table:
        return explicit_table
    return model_name.replace(".", "_")


def collect_constraints(root):
    """Return a list of (table, constraint_name, definition, source)."""
    found = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                model_name, explicit_table, constraints = None, None, []
                for stmt in node.body:
                    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                        continue
                    target = stmt.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    value = stmt.value
                    if target.id == "_name" and isinstance(value, ast.Constant):
                        model_name = value.value
                    elif target.id == "_table" and isinstance(value, ast.Constant):
                        explicit_table = value.value
                    elif target.id == "_inherit" and model_name is None:
                        if isinstance(value, ast.Constant):
                            model_name = value.value
                        elif isinstance(value, (ast.List, ast.Tuple)) and value.elts:
                            first = value.elts[0]
                            if isinstance(first, ast.Constant):
                                model_name = first.value
                    elif (isinstance(value, ast.Call)
                          and isinstance(value.func, ast.Attribute)
                          and value.func.attr == "Constraint"
                          and target.id.startswith("_")):
                        definition = None
                        if value.args and isinstance(value.args[0], ast.Constant):
                            definition = value.args[0].value
                        constraints.append(
                            (target.id[1:], definition, stmt.lineno)
                        )
                if model_name and constraints:
                    table = model_table(model_name, explicit_table)
                    for suffix, definition, lineno in constraints:
                        found.append((
                            table, f"{table}_{suffix}", definition,
                            f"{os.path.relpath(path, root)}:{lineno}",
                        ))
    return found


def preflight_sql(constraints):
    """Return SQL finding rows that would violate each constraint."""
    lines = [
        "-- PRE-FLIGHT: run BEFORE upgrading the module.",
        "-- Any non-zero count is data that will make ADD CONSTRAINT fail.",
        "-- Odoo will then log a WARNING and continue, leaving the constraint",
        "-- ABSENT while the upgrade reports success. Remediate first, under",
        "-- your change control procedure.",
        "",
    ]
    for table, conname, definition, source in constraints:
        if not definition:
            lines.append(f"-- {conname}: non-literal definition, check by hand "
                         f"({source})")
            lines.append("")
            continue
        unique = re.search(r"UNIQUE\s*\(([^)]*)\)", definition, re.IGNORECASE)
        check = re.search(r"CHECK\s*\((.*)\)\s*$", definition, re.IGNORECASE | re.DOTALL)
        if unique:
            columns = ", ".join(
                part.strip() for part in unique.group(1).split(",") if part.strip()
            )
            lines.append(f"-- {conname}  ({source})")
            lines.append(f"--    {definition}")
            lines.append(
                f"SELECT '{conname}' AS constraint_name, COUNT(*) AS violating_groups"
            )
            lines.append(f"  FROM (SELECT {columns} FROM {table}")
            lines.append(f"         GROUP BY {columns} HAVING COUNT(*) > 1) dup;")
            lines.append("")
        elif check:
            condition = check.group(1).strip()
            lines.append(f"-- {conname}  ({source})")
            lines.append(f"--    {definition}")
            lines.append(
                f"SELECT '{conname}' AS constraint_name, COUNT(*) AS violating_rows"
            )
            lines.append(f"  FROM {table} WHERE NOT ({condition});")
            lines.append("")
        else:
            lines.append(f"-- {conname}: definition is neither UNIQUE nor CHECK; "
                         f"check by hand ({source})")
            lines.append(f"--    {definition}")
            lines.append("")
    return "\n".join(lines)


def verify_sql(constraints):
    """Return SQL listing expected constraints and whether they exist."""
    pairs = sorted({(table, conname) for table, conname, _d, _s in constraints})
    values = ",\n        ".join(f"('{table}', '{conname}')" for table, conname in pairs)
    return f"""-- VERIFY: run AFTER upgrading the module.
-- Every row must read PRESENT. A row reading ABSENT means the constraint was
-- NOT created: Odoo logged a schema WARNING and continued. Run the pre-flight
-- script to find the data that blocked it.

WITH expected(table_name, constraint_name) AS (
    VALUES
        {values}
)
SELECT e.table_name,
       e.constraint_name,
       CASE WHEN c.conname IS NULL THEN 'ABSENT  <-- CONTROL MISSING'
            ELSE 'PRESENT' END AS status,
       COALESCE(pg_get_constraintdef(c.oid), '') AS definition
  FROM expected e
  LEFT JOIN pg_constraint c ON c.conname = e.constraint_name
 ORDER BY status DESC, e.table_name, e.constraint_name;


-- Summary: this must report absent = 0.
WITH expected(table_name, constraint_name) AS (
    VALUES
        {values}
)
SELECT COUNT(*)                                        AS expected,
       COUNT(c.conname)                                AS present,
       COUNT(*) - COUNT(c.conname)                     AS absent
  FROM expected e
  LEFT JOIN pg_constraint c ON c.conname = e.constraint_name;
"""


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_path", help="converted module directory")
    parser.add_argument("-o", "--output", default="constraint_checks",
                        help="output file prefix")
    args = parser.parse_args()

    root = os.path.abspath(args.module_path)
    if not os.path.isdir(root):
        _logger.info(f"Not a directory: {root}")
        return 2

    constraints = collect_constraints(root)
    if not constraints:
        _logger.info(f"No models.Constraint declarations found under {root}")
        return 1

    preflight_path = f"{args.output}_preflight.sql"
    verify_path = f"{args.output}_verify.sql"
    open(preflight_path, "w", encoding="utf-8").write(preflight_sql(constraints))
    open(verify_path, "w", encoding="utf-8").write(verify_sql(constraints))

    tables = sorted({table for table, _c, _d, _s in constraints})
    _logger.info(f"Module    : {os.path.basename(root)}")
    _logger.info("Constraints found : %s across %s table(s)", len(constraints), len(tables))
    _logger.info()
    for table, conname, definition, source in sorted(constraints):
        shown = (definition or "<non-literal>")
        if len(shown) > 52:
            shown = shown[:49] + "..."
        _logger.info(f"  {conname:<52} {shown}")
    _logger.info()
    _logger.info(f"Written: {preflight_path}")
    _logger.info("Written: %s", verify_path)
    _logger.info()
    _logger.info("Order of operations:")
    _logger.info(f"  1. psql -f {preflight_path}      # BEFORE upgrading")
    _logger.info("  2. remediate any non-zero count, under change control")
    _logger.info("  3. odoo -u <module> --stop-after-init")
    _logger.info(f"  4. psql -f {verify_path}         # AFTER upgrading")
    _logger.info("  5. every row must read PRESENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
