#!/usr/bin/env python3
# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Generate ``docs/02_technical_spec_generated.md`` from the module source.

The field, constraint and method inventory in the technical specification is
derived from the code by AST analysis rather than maintained by hand, so that
the document cannot drift out of step with what actually ships.

Run from the module root::

    python3 docs/generate_inventory.py
"""

from __future__ import annotations

import ast
import pathlib
import sys
from typing import Dict, List, Tuple
import logging

_logger = logging.getLogger(__name__)


#: Presentation order of the models in the generated document.
MODEL_ORDER: List[str] = [
    "ls.calibration.instrument.category",
    "ls.calibration.instrument",
    "ls.calibration.point",
    "ls.calibration.standard",
    "ls.calibration.plan",
    "ls.calibration.record",
    "ls.calibration.reading",
    "ls.calibration.certificate",
    "ls.calibration.oot",
    "ls.calibration.plan.generate",
    "ls.calibration.record.reject",
]

SOURCE_DIRECTORIES: Tuple[str, ...] = ("models", "wizards")


def _decorator_names(node: ast.FunctionDef) -> List[str]:
    """Return the attribute names of a function's decorators."""
    names = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(
            decorator.func, ast.Attribute
        ):
            names.append(decorator.func.attr)
        elif isinstance(decorator, ast.Attribute):
            names.append(decorator.attr)
    return names


def _keyword_is_true(call: ast.Call, keyword_name: str) -> bool:
    """Return whether a call passes ``keyword_name=True``."""
    for keyword in call.keywords:
        if keyword.arg == keyword_name:
            return getattr(keyword.value, "value", None) is True
    return False


def _has_keyword(call: ast.Call, keyword_name: str) -> bool:
    """Return whether a call passes the named keyword at all."""
    return any(keyword.arg == keyword_name for keyword in call.keywords)


def collect(root: pathlib.Path) -> Dict[str, dict]:
    """Walk the source tree and return the model inventory."""
    inventory: Dict[str, dict] = {}
    for directory in SOURCE_DIRECTORIES:
        for path in sorted((root / directory).glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                entry = _collect_class(node)
                if entry:
                    inventory[entry[0]] = entry[1]
    return inventory


def _collect_class(node: ast.ClassDef):
    """Return ``(model_name, details)`` for one class, or ``None``."""
    model_name = None
    description = None
    inherit: List[str] = []
    fields: List[tuple] = []
    constraints: List[Tuple[str, str]] = []
    computes: List[str] = []
    onchanges: List[str] = []
    actions: List[str] = []
    crons: List[str] = []

    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if not isinstance(target, ast.Name):
                    continue
                value = item.value
                if isinstance(value, ast.Constant):
                    if target.id == "_name":
                        model_name = value.value
                    elif target.id == "_description":
                        description = value.value
                if target.id == "_inherit" and isinstance(value, ast.List):
                    inherit = [
                        element.value
                        for element in value.elts
                        if isinstance(element, ast.Constant)
                    ]
                if isinstance(value, ast.Call) and isinstance(
                    value.func, ast.Attribute
                ):
                    base = getattr(value.func.value, "id", None)
                    if base == "fields":
                        fields.append(
                            (
                                target.id,
                                value.func.attr,
                                _keyword_is_true(value, "required"),
                                _has_keyword(value, "compute"),
                                _keyword_is_true(value, "store"),
                                _has_keyword(value, "related"),
                            )
                        )
                    elif base == "models" and value.func.attr == "Constraint":
                        expression = ""
                        if value.args and isinstance(value.args[0], ast.Constant):
                            expression = value.args[0].value
                        constraints.append((target.id, expression))
        elif isinstance(item, ast.FunctionDef):
            decorators = _decorator_names(item)
            if "depends" in decorators:
                computes.append(item.name)
            if "onchange" in decorators:
                onchanges.append(item.name)
            if "constrains" in decorators:
                constraints.append((item.name, "python"))
            if item.name.startswith("action_"):
                actions.append(item.name)
            if item.name.startswith("_cron_"):
                crons.append(item.name)

    if not model_name:
        return None
    return model_name, {
        "cls": node.name,
        "desc": description,
        "inherit": inherit,
        "fields": fields,
        "constraints": constraints,
        "computes": computes,
        "onchanges": onchanges,
        "actions": actions,
        "crons": crons,
    }


def render(inventory: Dict[str, dict]) -> str:
    """Render the inventory as the technical specification document."""
    lines = [
        "# ls_calibration — Technical Specification",
        "",
        "Phases 4 and 5 of the development framework.",
        "",
        "This inventory is generated directly from the module source by AST",
        "analysis (`docs/generate_inventory.py`), not maintained by hand.",
        "Counts and names therefore match the shipped code exactly.",
        "",
        "---",
        "",
        "## 4.1 Model inventory",
        "",
        "| Model | Class | Fields | Constraints | Computes | Onchanges | Actions |",
        "|---|---|---|---|---|---|---|",
    ]
    total_fields = total_constraints = 0
    for model in MODEL_ORDER:
        details = inventory[model]
        total_fields += len(details["fields"])
        total_constraints += len(details["constraints"])
        lines.append(
            f"| `{model}` | {details['cls']} | {len(details['fields'])} | "
            f"{len(details['constraints'])} | {len(details['computes'])} | "
            f"{len(details['onchanges'])} | {len(details['actions'])} |"
        )
    lines.append(
        f"| **Total** | **{len(MODEL_ORDER)}** | **{total_fields}** | "
        f"**{total_constraints}** | | | |"
    )

    for model in MODEL_ORDER:
        details = inventory[model]
        lines += ["", f"### `{model}`", "", f"*{details['desc']}*", ""]
        if details["inherit"]:
            joined = ", ".join(f"`{name}`" for name in details["inherit"])
            lines += [f"Inherits: {joined}", ""]
        lines += [
            "| Field | Type | Required | Computed | Stored | Related |",
            "|---|---|---|---|---|---|",
        ]
        for field in details["fields"]:
            lines.append(
                f"| `{field[0]}` | {field[1]} | {'yes' if field[2] else ''} | "
                f"{'yes' if field[3] else ''} | {'yes' if field[4] else ''} | "
                f"{'yes' if field[5] else ''} |"
            )
        if details["constraints"]:
            lines += ["", "**Constraints**", ""]
            for name, expression in details["constraints"]:
                kind = "Python" if expression == "python" else "SQL"
                suffix = "" if expression == "python" else f" — `{expression}`"
                lines.append(f"- {kind}: `{name}`{suffix}")
        if details["actions"]:
            joined = ", ".join(f"`{name}`" for name in details["actions"])
            lines += ["", f"**Public actions**: {joined}"]
        if details["crons"]:
            joined = ", ".join(f"`{name}`" for name in details["crons"])
            lines += ["", f"**Scheduled methods**: {joined}"]
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Command-line entry point."""
    root = pathlib.Path(__file__).resolve().parent.parent
    inventory = collect(root)
    missing = [model for model in MODEL_ORDER if model not in inventory]
    if missing:
        _logger.info("models declared but not found in source: %s", missing)
        return 1
    target = root / "docs" / "02_technical_spec_generated.md"
    target.write_text(render(inventory), encoding="utf-8")
    field_count = sum(len(inventory[m]["fields"]) for m in MODEL_ORDER)
    _logger.info(
        "written %s: %d models, %d fields",
        target.name,
        len(MODEL_ORDER),
        field_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
