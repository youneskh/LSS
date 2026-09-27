# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Configurable nature of a deviation."""

from odoo import fields, models


class LsDeviationType(models.Model):
    """Nature of the departure, for example Procedural or Equipment Failure."""

    _name = "ls.deviation.type"
    _description = "Deviation Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Short code used in reports and exports.",
    )
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        help="Leave empty to share this type across all companies.",
    )
    requires_disposition = fields.Boolean(
        help="Set when a deviation of this type always requires a documented "
        "product disposition, irrespective of the impact assessment.",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The deviation type code must be unique per company.",
    )
