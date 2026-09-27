# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Configurable root cause analysis methods."""

from odoo import fields, models


class LsDeviationRcaMethod(models.Model):
    """Structured technique applied to determine the root cause."""

    _name = "ls.deviation.rca.method"
    _description = "Root Cause Analysis Method"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "The root cause analysis method code must be unique.",
    )
