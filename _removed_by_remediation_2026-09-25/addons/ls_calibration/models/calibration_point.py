# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration points.

A calibration point is one nominal value at which an instrument is verified,
together with the acceptance tolerance applied at that value. Acceptance
limits are derived here so that a single algorithm governs both the user
interface and the pass/fail evaluation of readings.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationPoint(models.Model):
    """One nominal value and its acceptance tolerance for an instrument."""

    _name = "ls.calibration.point"
    _description = "Calibration Point"
    _order = "instrument_id, sequence, nominal_value, id"

    name = fields.Char(
        string="Point Name",
        required=True,
        help="Label of the calibration point, for example 'Zero', "
        "'Mid-scale' or 'Full scale'.",
    )
    sequence = fields.Integer(default=10)
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", required=True,
                                    ondelete="cascade",
                                    index=True,)
    nominal_value = fields.Float(required=True,
                                 digits=constants.MEASUREMENT_DIGITS,)
    unit_label = fields.Char(
        string="Unit",
        related="instrument_id.unit_label",
        readonly=True,
    )
    tolerance_type = fields.Selection(selection=constants.TOLERANCE_TYPE_SELECTION, required=True,
                                      default=constants.TOLERANCE_ABSOLUTE,)
    tolerance_value = fields.Float(
        string="Tolerance",
        required=True,
        digits=constants.MEASUREMENT_DIGITS,
        help="Half-width of the acceptance interval. For a percentage "
        "tolerance type the value is expressed in percent, so 0.5 means "
        "0.5 %, not 50 %.",
    )
    tolerance_absolute = fields.Float(
        string="Absolute Tolerance",
        compute="_compute_limits",
        store=True,
        digits=constants.MEASUREMENT_DIGITS,
        help="Tolerance converted into the measurement unit of the "
        "instrument.",
    )
    lower_limit = fields.Float(compute="_compute_limits",
                               store=True,
                               digits=constants.MEASUREMENT_DIGITS,)
    upper_limit = fields.Float(compute="_compute_limits",
                               store=True,
                               digits=constants.MEASUREMENT_DIGITS,)
    reading_ids = fields.One2many(
        comodel_name="ls.calibration.reading",
        inverse_name="point_id",
        string="Readings",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="instrument_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)
    active = fields.Boolean(default=True)

    _tolerance_non_negative = models.Constraint(
        "CHECK(tolerance_value >= 0)",
        "The tolerance cannot be negative.",
    )
    _point_name_instrument_uniq = models.Constraint(
        "UNIQUE(instrument_id, name)",
        "A calibration point name must be unique within an instrument.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "nominal_value",
        "tolerance_type",
        "tolerance_value",
        "instrument_id.span",
    )
    def _compute_limits(self) -> None:
        """Convert the declared tolerance into absolute acceptance limits.

        Three tolerance conventions are supported:

        * ``absolute`` - the tolerance is already expressed in the measurement
          unit of the instrument.
        * ``percent_of_reading`` - the tolerance is a percentage of the
          absolute nominal value of the point.
        * ``percent_of_span`` - the tolerance is a percentage of the
          instrument span (range maximum minus range minimum).
        """
        for point in self:
            absolute = point._get_absolute_tolerance()
            point.tolerance_absolute = absolute
            point.lower_limit = point.nominal_value - absolute
            point.upper_limit = point.nominal_value + absolute

    def _get_absolute_tolerance(self) -> float:
        """Return the tolerance of this point expressed in measurement units."""
        self.ensure_one()
        if self.tolerance_type == constants.TOLERANCE_ABSOLUTE:
            return abs(self.tolerance_value)
        if self.tolerance_type == constants.TOLERANCE_PERCENT_OF_READING:
            return abs(self.tolerance_value) * abs(self.nominal_value) / 100.0
        if self.tolerance_type == constants.TOLERANCE_PERCENT_OF_SPAN:
            return abs(self.tolerance_value) * abs(self.instrument_id.span) / 100.0
        raise UserError(
            self.env._(
                "Unsupported tolerance type '%(tolerance_type)s'.",
                tolerance_type=self.tolerance_type,
            )
        )

    @api.depends("name", "nominal_value", "unit_label")
    def _compute_display_name(self) -> None:
        """Show the point name together with its nominal value."""
        for point in self:
            unit = f" {point.unit_label}" if point.unit_label else ""
            point.display_name = f"{point.name} ({point.nominal_value}{unit})"

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains(
        "nominal_value", "instrument_id", "tolerance_type", "instrument_id.span"
    )
    def _check_nominal_within_range(self) -> None:
        """The nominal value must lie inside the declared instrument range.

        The check is skipped when the instrument declares a degenerate range
        (minimum equal to maximum), which indicates that no range has been
        captured yet.
        """
        for point in self:
            instrument = point.instrument_id
            if instrument.range_min == instrument.range_max:
                continue
            low = min(instrument.range_min, instrument.range_max)
            high = max(instrument.range_min, instrument.range_max)
            if not low <= point.nominal_value <= high:
                raise ValidationError(
                    self.env._(
                        "Calibration point '%(point)s' has a nominal value of "
                        "%(nominal)s, which lies outside the range "
                        "%(low)s to %(high)s declared for instrument "
                        "%(instrument)s.",
                        point=point.name,
                        nominal=point.nominal_value,
                        low=low,
                        high=high,
                        instrument=instrument.code,
                    )
                )

    @api.constrains("tolerance_type", "instrument_id")
    def _check_span_available_for_percent_of_span(self) -> None:
        """A percent-of-span tolerance requires a non-zero instrument span."""
        for point in self:
            if point.tolerance_type != constants.TOLERANCE_PERCENT_OF_SPAN:
                continue
            if not point.instrument_id.span:
                raise ValidationError(
                    self.env._(
                        "Calibration point '%(point)s' uses a percent-of-span "
                        "tolerance but instrument %(instrument)s declares a "
                        "zero span. Enter the instrument range first.",
                        point=point.name,
                        instrument=point.instrument_id.code,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    #: Fields that define the acceptance criteria of a calibration point.
    #: Changing any of them after the point has been used in a calibration
    #: that left data entry would retroactively alter the pass/fail basis of
    #: an existing result.
    _ACCEPTANCE_FIELDS = (
        "nominal_value",
        "tolerance_type",
        "tolerance_value",
        "instrument_id",
    )

    def write(self, vals: dict) -> bool:
        """Reject changes to acceptance criteria already used in a result.

        A calibration point may be renamed, resequenced or archived at any
        time. Its nominal value and tolerance become frozen as soon as a
        reading referencing it belongs to a record that has passed data entry.
        """
        touched = set(vals) & set(self._ACCEPTANCE_FIELDS)
        if not touched:
            return super().write(vals)
        frozen_states = (
            constants.RECORD_STATE_PERFORMED,
            constants.RECORD_STATE_UNDER_REVIEW,
            constants.RECORD_STATE_APPROVED,
            constants.RECORD_STATE_REJECTED,
            constants.RECORD_STATE_CANCELLED,
        )
        for point in self:
            committed = point.reading_ids.filtered(
                lambda reading: reading.record_id.state in frozen_states
            )
            if committed:
                raise UserError(
                    self.env._(
                        "Calibration point '%(point)s' has been used in "
                        "%(count)s committed calibration record(s). Its "
                        "acceptance criteria can no longer be changed. "
                        "Archive this point and create a new one instead. "
                        "Field(s) refused: %(fields)s.",
                        point=point.name,
                        count=len(committed),
                        fields=", ".join(sorted(touched)),
                    )
                )
        return super().write(vals)

    def unlink(self) -> bool:
        """Forbid deletion of points that already carry recorded readings."""
        for point in self:
            if point.reading_ids:
                raise UserError(
                    self.env._(
                        "Calibration point '%(point)s' carries recorded "
                        "readings and cannot be deleted. Archive it instead.",
                        point=point.name,
                    )
                )
        return super().unlink()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def is_within_tolerance(self, measured_value: float) -> bool:
        """Return whether a measured value falls inside the acceptance limits.

        :param measured_value: the indicated value read from the instrument.
        :return: ``True`` when ``lower_limit <= measured_value <= upper_limit``.
        """
        self.ensure_one()
        return self.lower_limit <= measured_value <= self.upper_limit
