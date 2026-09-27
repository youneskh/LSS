# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Free classification tags for trending."""

from odoo import fields, models


class LsDeviationTag(models.Model):
    """Cross-cutting label used for trend analysis."""

    _name = "ls.deviation.tag"
    _description = "Deviation Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Colour Index")
    active = fields.Boolean(default=True)

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "A tag with this name already exists.",
    )
