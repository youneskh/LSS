# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Test point of a calibration plan.

A test point carries the nominal value that is applied to the instrument
during the calibration and the acceptance criteria applied to the reading.
"""

from odoo import api, fields, models

TOLERANCE_TYPE_SELECTION = [
    ("absolute", "Absolute"),
    ("relative", "Percentage of Reading"),
]


class LsCalibrationPlanPoint(models.Model):
    """Nominal value and acceptance criteria of one calibration point."""

    _name = "ls.calibration.plan.point"
    _description = "Calibration Plan Test Point"
    _order = "plan_id, sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    plan_id = fields.Many2one(
        comodel_name="ls.calibration.plan",
        required=True,
        index=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="plan_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    name = fields.Char(
        string="Point",
        required=True,
        help="Identification of the test point, for example "
        "'25 % of the range'.",
    )
    nominal_value = fields.Float(
        required=True,
        digits=(16, 6),
        help="Value of the reference standard applied to the instrument.",
    )
    unit = fields.Char(string="Unit of Measurement")
    tolerance_type = fields.Selection(
        selection=TOLERANCE_TYPE_SELECTION,
        required=True,
        default="absolute",
    )
    tolerance_value = fields.Float(
        string="Tolerance",
        required=True,
        digits=(16, 6),
        help="Maximum permissible error of the reading at this test point. "
        "Expressed in the unit of measurement for an absolute tolerance and "
        "in percent of the nominal value for a relative tolerance.",
    )
    limit_min = fields.Float(
        string="Lower Limit",
        compute="_compute_limits",
        store=True,
        digits=(16, 6),
    )
    limit_max = fields.Float(
        string="Upper Limit",
        compute="_compute_limits",
        store=True,
        digits=(16, 6),
    )

    _tolerance_value_positive = models.Constraint(
        "CHECK(tolerance_value >= 0)",
        "The tolerance of a test point must be greater than or equal to zero.",
    )

    @api.depends("name", "nominal_value", "unit")
    def _compute_display_name(self):
        """Show the point name together with its nominal value."""
        for point in self:
            unit = f" {point.unit}" if point.unit else ""
            point.display_name = (
                f"{point.name or ''} ({point.nominal_value}{unit})"
            )

    @api.depends("nominal_value", "tolerance_type", "tolerance_value")
    def _compute_limits(self):
        """Derive the acceptance limits from the tolerance definition."""
        for point in self:
            point.limit_min, point.limit_max = self._get_limits(
                point.nominal_value, point.tolerance_type, point.tolerance_value
            )

    @api.model
    def _get_limits(self, nominal_value, tolerance_type, tolerance_value):
        """Return the lower and upper acceptance limits of a test point.

        :param nominal_value: value applied by the reference standard.
        :param tolerance_type: ``absolute`` or ``relative``.
        :param tolerance_value: tolerance expressed in the selected type.
        :return: a tuple ``(limit_min, limit_max)``.
        """
        if tolerance_type == "relative":
            delta = abs(nominal_value) * abs(tolerance_value) / 100.0
        else:
            delta = abs(tolerance_value)
        return nominal_value - delta, nominal_value + delta

    @api.onchange("plan_id")
    def _onchange_plan_id(self):
        """Propose the metrological defaults of the instrument."""
        instrument = self.plan_id.instrument_id
        if not instrument:
            return
        if not self.unit:
            self.unit = instrument.unit
        if not self.tolerance_value:
            self.tolerance_type = instrument.tolerance_type
            self.tolerance_value = instrument.tolerance_value

    def _prepare_record_line_values(self):
        """Return the values of the calibration record line of this point.

        :return: a dictionary accepted by ``ls.calibration.record.line``.
        """
        self.ensure_one()
        return {
            "sequence": self.sequence,
            "plan_point_id": self.id,
            "name": self.name,
            "nominal_value": self.nominal_value,
            "unit": self.unit,
            "tolerance_type": self.tolerance_type,
            "tolerance_value": self.tolerance_value,
        }
