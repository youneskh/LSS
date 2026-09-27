# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Monitored area."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsEnvArea(models.Model):
    """A physical area subject to environmental monitoring.

    Areas form a hierarchy so that a suite can contain rooms and a room can
    contain zones. The hierarchy is used for reporting roll-up only; sampling
    points are always attached to a single area.
    """

    _name = "ls.env.area"
    _description = "Environmental Monitoring Area"
    _inherit = ["mail.thread"]
    _order = "complete_name"
    _parent_store = True

    name = fields.Char(
        string="Area",
        required=True,
        tracking=True,
        help="Name of the room, suite or zone.",
    )
    code = fields.Char(required=True,
                       tracking=True,
                       help="Short unique code for the area, used in sample identifiers.",)
    complete_name = fields.Char(
        string="Full Path",
        compute="_compute_complete_name",
        recursive=True,
        store=True,
    )
    parent_id = fields.Many2one(
        comodel_name="ls.env.area",
        string="Parent Area",
        index=True,
        ondelete="restrict",
        help="Area that contains this one.",
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        comodel_name="ls.env.area",
        inverse_name="parent_id",
        string="Contained Areas",
    )
    grade_id = fields.Many2one(
        comodel_name="ls.env.grade",
        string="Classification Grade",
        tracking=True,
        ondelete="restrict",
        help="Classification grade assigned to this area.",
    )
    responsible_id = fields.Many2one(comodel_name="res.users", tracking=True,
                                     help="User accountable for the monitoring of this area.",)
    description = fields.Text()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    sampling_point_ids = fields.One2many(
        comodel_name="ls.env.sampling_point",
        inverse_name="area_id",
        string="Sampling Points",
    )
    sampling_point_count = fields.Integer(
        string="Sampling Points",
        compute="_compute_sampling_point_count",
    )
    open_excursion_count = fields.Integer(
        string="Open Excursions",
        compute="_compute_open_excursion_count", search="_search_open_excursion_count",
    )

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The area code must be unique per company.",
    )

    @api.depends("name", "code", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Build the slash-separated path from the root area downwards."""
        for record in self:
            label = "%s [%s]" % (record.name or "", record.code or "")
            if record.parent_id:
                record.complete_name = "%s / %s" % (
                    record.parent_id.complete_name,
                    label,
                )
            else:
                record.complete_name = label

    @api.depends("sampling_point_ids")
    def _compute_sampling_point_count(self):
        """Count the sampling points defined directly in this area."""
        grouped = self.env["ls.env.sampling_point"]._read_group(
            [("area_id", "in", self.ids)],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        counts = {area.id: count for area, count in grouped}
        for record in self:
            record.sampling_point_count = counts.get(record.id, 0)

    def _compute_open_excursion_count(self):
        """Count excursions in this area that are not closed or cancelled."""
        grouped = self.env["ls.env.excursion"]._read_group(
            [
                ("area_id", "in", self.ids),
                ("state", "not in", ["closed", "cancelled"]),
            ],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        counts = {area.id: count for area, count in grouped}
        for record in self:
            record.open_excursion_count = counts.get(record.id, 0)

    @api.constrains("parent_id")
    def _check_area_hierarchy(self):
        """Reject cycles in the area hierarchy."""
        if self._has_cycle():
            raise ValidationError(
                self.env._("An area cannot be placed inside one of its own sub-areas.")
            )

    @api.constrains("parent_id", "company_id")
    def _check_parent_company(self):
        """Reject a parent area belonging to a different company."""
        for record in self:
            if record.parent_id and record.parent_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "Area '%(area)s' cannot belong to a parent area of another "
                        "company.",
                        area=record.name,
                    )
                )

    @api.depends("complete_name")
    def _compute_display_name(self):
        """Display the full hierarchical path."""
        for record in self:
            record.display_name = record.complete_name or record.name or ""

    def _search_open_excursion_count(self, operator, value):
        """Allow filtering on the non-stored open_excursion_count field.

        :param str operator: one of =, !=, in, not in, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.open_excursion_count, operator, value)
        ]
        return [("id", "in", matching_ids)]

    @staticmethod
    def _evaluate_operator(actual, operator, expected):
        """Evaluate a comparison operator between two values."""
        ops = {
            "=": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            # Odoo 19 normalises "=" and "!=" to "in" and "not in" before it
            # calls a field search method.
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
        }
        return ops.get(operator, lambda a, b: False)(actual, expected)

    def action_view_sampling_points(self):
        """Open the sampling points of this area."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Sampling Points"),
            "res_model": "ls.env.sampling_point",
            "view_mode": "list,form",
            "domain": [("area_id", "=", self.id)],
            "context": {"default_area_id": self.id},
        }

    def action_view_open_excursions(self):
        """Open the excursions of this area that are still in progress."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Open Excursions"),
            "res_model": "ls.env.excursion",
            "view_mode": "list,form",
            "domain": [
                ("area_id", "=", self.id),
                ("state", "not in", ["closed", "cancelled"]),
            ],
        }
