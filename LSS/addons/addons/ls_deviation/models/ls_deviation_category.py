# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Configurable functional area in which a deviation arises."""

from odoo import fields, models


class LsDeviationCategory(models.Model):
    """Functional area classification, for example Production or QC Laboratory."""

    _name = "ls.deviation.category"
    _description = "Deviation Category"
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
        help="Leave empty to share this category across all companies.",
    )
    deviation_count = fields.Integer(compute="_compute_deviation_count")

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The category code must be unique per company.",
    )

    def _compute_deviation_count(self):
        """Count deviations classified under each category.

        Uses the ``_read_group`` API, which returns a list of tuples whose
        first element is the grouping recordset. ``read_group`` is deprecated
        in Odoo 19.
        """
        data = self.env["ls.deviation"]._read_group(
            domain=[("category_id", "in", self.ids)],
            groupby=["category_id"],
            aggregates=["__count"],
        )
        mapped = {category.id: count for category, count in data}
        for record in self:
            record.deviation_count = mapped.get(record.id, 0)
