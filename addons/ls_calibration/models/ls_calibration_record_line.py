# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Test point result of a calibration record.

Each line carries the nominal value applied by the reference standard, the
as-found reading measured before any adjustment and the as-left reading
measured after the adjustment, together with the resulting verdicts.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from .ls_calibration_plan_point import TOLERANCE_TYPE_SELECTION

FLOAT_PRECISION_DIGITS = 6


class LsCalibrationRecordLine(models.Model):
    """As-found and as-left readings of one calibration test point."""

    _name = "ls.calibration.record.line"
    _description = "Calibration Record Test Point Result"
    _order = "record_id, sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        required=True,
        index=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="record_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    plan_point_id = fields.Many2one(
        comodel_name="ls.calibration.plan.point",
        string="Plan Test Point",
        ondelete="set null",
        check_company=True,
    )
    name = fields.Char(string="Point", required=True)
    nominal_value = fields.Float(required=True, digits=(16, 6))
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
    as_found_value = fields.Float(
        string="As Found",
        digits=(16, 6),
        help="Reading of the instrument before any adjustment.",
    )
    as_left_value = fields.Float(
        string="As Left",
        digits=(16, 6),
        help="Reading of the instrument after the adjustment. When no "
        "adjustment is performed it is equal to the as-found reading.",
    )
    as_found_deviation = fields.Float(compute="_compute_deviations",
                                      store=True,
                                      digits=(16, 6),
                                      )
    as_left_deviation = fields.Float(compute="_compute_deviations",
                                     store=True,
                                     digits=(16, 6),
                                     )
    as_found_in_tolerance = fields.Boolean(compute="_compute_in_tolerance",
                                           store=True,)
    as_left_in_tolerance = fields.Boolean(compute="_compute_in_tolerance",
                                          store=True,)
    _tolerance_value_positive = models.Constraint(
        "CHECK(tolerance_value >= 0)",
        "The tolerance of a test point must be greater than or equal to zero.",
    )

    @api.depends("name", "record_id.name")
    def _compute_display_name(self):
        """Show the point name together with its calibration record."""
        for line in self:
            line.display_name = f"{line.record_id.name or ''} / {line.name or ''}"

    @api.depends("nominal_value", "tolerance_type", "tolerance_value")
    def _compute_limits(self):
        """Derive the acceptance limits from the tolerance definition."""
        point_model = self.env["ls.calibration.plan.point"]
        for line in self:
            line.limit_min, line.limit_max = point_model._get_limits(
                line.nominal_value, line.tolerance_type, line.tolerance_value
            )

    @api.depends("nominal_value", "as_found_value", "as_left_value")
    def _compute_deviations(self):
        """Derive the deviation of each reading from the nominal value."""
        for line in self:
            line.as_found_deviation = line.as_found_value - line.nominal_value
            line.as_left_deviation = line.as_left_value - line.nominal_value

    @api.depends(
        "as_found_value", "as_left_value", "limit_min", "limit_max"
    )
    def _compute_in_tolerance(self):
        """Compare each reading with the acceptance limits."""
        for line in self:
            line.as_found_in_tolerance = line._is_within_limits(
                line.as_found_value
            )
            line.as_left_in_tolerance = line._is_within_limits(
                line.as_left_value
            )

    def _is_within_limits(self, value):
        """Return whether a reading lies inside the acceptance limits.

        :param value: reading to be evaluated.
        :return: ``True`` when the reading is within the limits.
        """
        self.ensure_one()
        above_min = (
            float_compare(
                value, self.limit_min, precision_digits=FLOAT_PRECISION_DIGITS
            )
            >= 0
        )
        below_max = (
            float_compare(
                value, self.limit_max, precision_digits=FLOAT_PRECISION_DIGITS
            )
            <= 0
        )
        return above_min and below_max

    @api.onchange("as_found_value")
    def _onchange_as_found_value(self):
        """Propose the as-found reading as the as-left reading."""
        if not self.as_left_value:
            self.as_left_value = self.as_found_value

    def _check_record_editable(self):
        """Refuse any change when the parent record is no longer editable."""
        for line in self:
            if line.record_id.state not in ("draft", "in_progress"):
                raise UserError(
                    self.env._(
                        "The test points of calibration record %s can only be "
                        "modified while the record is in the draft or in "
                        "progress state.",
                        line.record_id.display_name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Refuse the creation of a line on a record that is not editable."""
        lines = super().create(vals_list)
        lines._check_record_editable()
        return lines

    @api.model
    def _get_recompute_exempt_fields(self):
        """Return the stored computed fields written by the ORM itself.

        Writing these fields is a consequence of a recomputation and never a
        modification of the calibration evidence, therefore it stays allowed
        whatever the state of the parent calibration record.

        :return: a set of field names.
        """
        return {
            "as_found_deviation",
            "as_found_in_tolerance",
            "as_left_deviation",
            "as_left_in_tolerance",
            "company_id",
            "limit_max",
            "limit_min",
        }

    def write(self, vals):
        """Refuse the modification of a line of a submitted record."""
        if set(vals) - self._get_recompute_exempt_fields():
            self._check_record_editable()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_calibration_record_line(self):
        """Refuse the deletion of a line of a submitted record."""
        self._check_record_editable()
