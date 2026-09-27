# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Periodic measurements attached to a quality objective."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsQmsObjectiveMeasurement(models.Model):
    """One dated measurement of a quality objective indicator."""

    _name = "ls.qms.objective.measurement"
    _description = "Quality Objective Measurement"
    _order = "date desc, id desc"

    objective_id = fields.Many2one(comodel_name="ls.qms.objective", required=True,
                                   ondelete="cascade",
                                   index=True,)
    company_id = fields.Many2one(
        related="objective_id.company_id",
        store=True,
        index=True,
    )
    date = fields.Date(
        string="Measurement Date",
        required=True,
        default=fields.Date.context_today,
    )
    value = fields.Float(required=True)
    comment = fields.Text()
    recorded_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,)

    @api.constrains("date", "objective_id")
    def _check_date_within_objective(self):
        """Reject measurements dated before the objective start date."""
        for measurement in self:
            start = measurement.objective_id.date_start
            if start and measurement.date < start:
                raise ValidationError(
                    _(
                        "A measurement dated %(date)s cannot precede the "
                        "start date of objective %(reference)s.",
                        date=measurement.date,
                        reference=measurement.objective_id.reference,
                    )
                )

    @api.depends("objective_id", "date", "value")
    def _compute_display_name(self):
        """Render measurements as ``date: value``."""
        for measurement in self:
            measurement.display_name = "%s: %s" % (
                measurement.date or "",
                measurement.value,
            )
