# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Sampling point."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .constants import LIMIT_STATE_APPROVED, OCCUPANCY_ANY


class LsEnvSamplingPoint(models.Model):
    """A defined location at which samples are taken.

    The rationale for selecting the location is captured on the record so that
    the basis of the monitoring programme is retained with the point itself
    rather than only in a separate document.
    """

    _name = "ls.env.sampling_point"
    _description = "Environmental Monitoring Sampling Point"
    _inherit = ["mail.thread"]
    _order = "area_id, sequence, code"

    name = fields.Char(string="Sampling Point", required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    area_id = fields.Many2one(comodel_name="ls.env.area", required=True,
                              tracking=True,
                              index=True,
                              ondelete="restrict",)
    grade_id = fields.Many2one(
        comodel_name="ls.env.grade",
        string="Classification Grade",
        compute="_compute_grade_id",
        store=True,
        readonly=False,
        tracking=True,
        ondelete="restrict",
        help="Defaults to the grade of the area and may be overridden when a "
        "point sits in a locally different classification.",
    )
    position_description = fields.Text(
        string="Position",
        help="Physical description of the location, precise enough for the "
        "point to be found again by a different operator.",
    )
    selection_rationale = fields.Text(tracking=True,
                                      help="Documented reason for monitoring at this location, for example "
                                      "the outcome of the risk assessment that identified it.",)
    is_critical = fields.Boolean(
        string="Critical Location",
        tracking=True,
        help="Marks a location identified as critical by risk assessment.",
    )
    responsible_id = fields.Many2one(comodel_name="res.users", tracking=True,)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    limit_ids = fields.One2many(
        comodel_name="ls.env.limit",
        inverse_name="sampling_point_id",
        string="Limits",
    )
    approved_limit_count = fields.Integer(
        string="Approved Limits",
        compute="_compute_approved_limit_count", search="_search_approved_limit_count",
    )
    sample_ids = fields.One2many(
        comodel_name="ls.env.sample",
        inverse_name="sampling_point_id",
        string="Samples",
    )

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The sampling point code must be unique per company.",
    )

    @api.depends("area_id.grade_id")
    def _compute_grade_id(self):
        """Inherit the grade of the area, allowing a manual override."""
        for record in self:
            record.grade_id = record.area_id.grade_id

    @api.depends("limit_ids.state")
    def _compute_approved_limit_count(self):
        """Count the currently approved limits of each point."""
        grouped = self.env["ls.env.limit"]._read_group(
            [
                ("sampling_point_id", "in", self.ids),
                ("state", "=", LIMIT_STATE_APPROVED),
            ],
            groupby=["sampling_point_id"],
            aggregates=["__count"],
        )
        counts = {point.id: count for point, count in grouped}
        for record in self:
            record.approved_limit_count = counts.get(record.id, 0)

    @api.constrains("area_id", "company_id")
    def _check_area_company(self):
        """Reject an area belonging to a different company."""
        for record in self:
            if record.area_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "Sampling point '%(point)s' must belong to an area of the "
                        "same company.",
                        point=record.name,
                    )
                )

    def find_approved_limit(self, parameter, occupancy_state, direction):
        """Return the approved limit applicable to a measurement.

        A limit configured for a specific occupancy state takes precedence
        over one configured to apply in any state, so that a general fallback
        can be defined without preventing a state-specific override.

        :param parameter: ``ls.env.parameter`` record
        :param str occupancy_state: occupancy state recorded on the sample
        :param str direction: bound direction being resolved
        :returns: a single ``ls.env.limit`` record, empty when none applies
        """
        self.ensure_one()
        limit_model = self.env["ls.env.limit"]
        base_domain = [
            ("sampling_point_id", "=", self.id),
            ("parameter_id", "=", parameter.id),
            ("direction", "=", direction),
            ("state", "=", LIMIT_STATE_APPROVED),
        ]
        specific = limit_model.search(
            base_domain + [("occupancy_state", "=", occupancy_state)], limit=1
        )
        if specific:
            return specific
        return limit_model.search(
            base_domain + [("occupancy_state", "=", OCCUPANCY_ANY)], limit=1
        )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the code alongside the sampling point name."""
        for record in self:
            record.display_name = "[%s] %s" % (record.code or "", record.name or "")

    def _search_approved_limit_count(self, operator, value):
        """Allow filtering on the non-stored approved_limit_count field."""
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.approved_limit_count, operator, value)
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

    def action_view_limits(self):
        """Open the limits configured for this sampling point."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Limits"),
            "res_model": "ls.env.limit",
            "view_mode": "list,form",
            "domain": [("sampling_point_id", "=", self.id)],
            "context": {"default_sampling_point_id": self.id},
        }
