# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""CAPA category configuration model."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsCapaCategory(models.Model):
    """Classification scheme applied to CAPA records.

    Categories let a quality organization group CAPA records by the process
    area they originate from (for example ``Production`` or ``Laboratory``)
    and define a default resolution lead time used to compute the CAPA due
    date.
    """

    _name = "ls.capa.category"
    _description = "CAPA Category"
    _order = "sequence, name"

    name = fields.Char(
        string="Category",
        required=True,
        translate=True,
        help="Display name of the CAPA category.",
    )
    code = fields.Char(required=True,
                       help="Short unique code used in reports and exports.",)
    sequence = fields.Integer(default=10,
                              help="Order in which categories are presented to users.",)
    description = fields.Text(translate=True,
                              help="Scope of the category and guidance on when to use it.",)
    default_due_days = fields.Integer(
        string="Default Resolution Lead Time (days)",
        default=30,
        help="Number of calendar days added to the identification date to "
             "propose a CAPA due date when this category is selected.",
    )
    active = fields.Boolean(default=True,
                            help="Uncheck to archive the category without deleting historical "
                            "CAPA records that reference it.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this category.",)
    issue_ids = fields.One2many(
        comodel_name="ls.capa.issue",
        inverse_name="category_id",
        string="CAPA Records",
    )
    issue_count = fields.Integer(
        string="CAPA Count",
        compute="_compute_issue_count",
        help="Number of CAPA records classified under this category.",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The CAPA category code must be unique per company.",
    )
    _default_due_days_positive = models.Constraint(
        "CHECK(default_due_days > 0)",
        "The default resolution lead time must be strictly positive.",
    )

    @api.depends("issue_ids")
    def _compute_issue_count(self):
        """Count CAPA records linked to each category."""
        data = self.env["ls.capa.issue"]._read_group(
            domain=[("category_id", "in", self.ids)],
            groupby=["category_id"],
            aggregates=["__count"],
        )
        mapped = {category.id: count for category, count in data}
        for record in self:
            record.issue_count = mapped.get(record.id, 0)

    @api.constrains("code")
    def _check_code(self):
        """Reject blank or whitespace-only category codes."""
        for record in self:
            if not record.code.strip():
                raise ValidationError(
                    _("The CAPA category code cannot be empty.")
                )

    def action_view_issues(self):
        """Open the CAPA records classified under this category.

        :return: an ``ir.actions.act_window`` dictionary.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("CAPA Records"),
            "res_model": "ls.capa.issue",
            "view_mode": "list,form",
            "domain": [("category_id", "=", self.id)],
            "context": {"default_category_id": self.id},
        }
