# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Configurable risk taxonomy.

The functional specification lists risk identification "across products and
processes" but does not name a taxonomy model. A configurable hierarchical
category is added here so that the classification used by an organisation is
master data under change control rather than a hardcoded selection list.
This deviation from the specification is declared in the module
documentation.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsRiskCategory(models.Model):
    """Hierarchical category used to classify risk register entries."""

    _name = "ls.risk.category"
    _description = "Risk Category"
    _parent_store = True
    _order = "complete_name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    complete_name = fields.Char(compute="_compute_complete_name",
                                recursive=True,
                                store=True,)
    parent_id = fields.Many2one(
        comodel_name="ls.risk.category",
        string="Parent Category",
        ondelete="restrict",
        index=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        comodel_name="ls.risk.category",
        inverse_name="parent_id",
        string="Child Categories",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)
    description = fields.Text()
    risk_count = fields.Integer(compute="_compute_risk_count",
                                help="Number of risk register entries directly classified in this category.",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The risk category code must be unique per company.",
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Build the slash-separated path of the category."""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name

    def _compute_risk_count(self):
        """Count the risks directly attached to each category."""
        grouped = self.env["ls.risk.register"]._read_group(
            domain=[("category_id", "in", self.ids)],
            groupby=["category_id"],
            aggregates=["__count"],
        )
        counts = {category.id: count for category, count in grouped}
        for category in self:
            category.risk_count = counts.get(category.id, 0)

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        """Forbid cycles in the category hierarchy.

        The ancestry is walked explicitly rather than through a helper of the
        base model, because the name of that helper changed between recent
        Odoo versions and could not be verified from official documentation
        for Odoo 19. The walk is bounded by the number of stored categories,
        so a pre-existing cycle cannot loop indefinitely.

        :raise ValidationError: when a category is its own ancestor.
        """
        limit = self.search_count([]) + 1
        for category in self:
            seen = set()
            ancestor = category.parent_id
            steps = 0
            while ancestor and steps <= limit:
                if ancestor.id == category.id or ancestor.id in seen:
                    raise ValidationError(
                        self.env._(
                            "Category %(name)s cannot be its own ancestor.",
                            name=category.name,
                        )
                    )
                seen.add(ancestor.id)
                ancestor = ancestor.parent_id
                steps += 1

    @api.constrains("parent_id", "company_id")
    def _check_parent_company(self):
        """Keep a category and its parent within the same company."""
        for category in self:
            if category.parent_id and category.parent_id.company_id != category.company_id:
                raise ValidationError(
                    self.env._(
                        "Category %(name)s and its parent must belong to the "
                        "same company.",
                        name=category.name,
                    )
                )

    @api.depends("complete_name")
    def _compute_display_name(self):
        """Display the full hierarchical path."""
        for category in self:
            category.display_name = category.complete_name or category.name
