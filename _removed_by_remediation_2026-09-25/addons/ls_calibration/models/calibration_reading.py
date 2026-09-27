# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration readings.

One reading holds the as-found and as-left measured values obtained at one
calibration point during one calibration record, together with the derived
deviation and the pass/fail evaluation against the acceptance limits.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationReading(models.Model):
    """As-found and as-left values measured at one calibration point."""

    _name = "ls.calibration.reading"
    _description = "Calibration Reading"
    _order = "record_id, sequence, id"

    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        required=True,
        ondelete="cascade",
        index=True,
    )
    point_id = fields.Many2one(
        comodel_name="ls.calibration.point",
        string="Calibration Point",
        required=True,
        ondelete="restrict",
        index=True,
    )
    sequence = fields.Integer(related="point_id.sequence",
                              store=True,
                              readonly=True,)
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", related="record_id.instrument_id",
                                    store=True,
                                    readonly=True,
                                    index=True,)
    record_state = fields.Selection(
        related="record_id.state",
        string="Record Status",
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Acceptance criteria mirrored from the point
    # ------------------------------------------------------------------
    nominal_value = fields.Float(
        string="Nominal",
        related="point_id.nominal_value",
        store=True,
        readonly=True,
        digits=constants.MEASUREMENT_DIGITS,
    )
    lower_limit = fields.Float(related="point_id.lower_limit",
                               store=True,
                               readonly=True,
                               digits=constants.MEASUREMENT_DIGITS,)
    upper_limit = fields.Float(related="point_id.upper_limit",
                               store=True,
                               readonly=True,
                               digits=constants.MEASUREMENT_DIGITS,)
    unit_label = fields.Char(
        string="Unit", related="point_id.unit_label", readonly=True
    )

    # ------------------------------------------------------------------
    # Measured values
    # ------------------------------------------------------------------
    as_found_value = fields.Float(
        string="As Found",
        digits=constants.MEASUREMENT_DIGITS,
    )
    as_found_recorded = fields.Boolean(
        string="As-Found Recorded",
        default=False,
        help="Set explicitly when an as-found value has been entered. A "
        "separate flag is required because zero is a legitimate measurement.",
    )
    as_left_value = fields.Float(
        string="As Left",
        digits=constants.MEASUREMENT_DIGITS,
    )
    as_left_recorded = fields.Boolean(
        string="As-Left Recorded",
        default=False,
        help="Set explicitly when an as-left value has been entered. A "
        "separate flag is required because zero is a legitimate measurement.",
    )

    # ------------------------------------------------------------------
    # Derived evaluation
    # ------------------------------------------------------------------
    as_found_deviation = fields.Float(
        string="As-Found Deviation",
        compute="_compute_evaluation",
        store=True,
        digits=constants.MEASUREMENT_DIGITS,
    )
    as_left_deviation = fields.Float(
        string="As-Left Deviation",
        compute="_compute_evaluation",
        store=True,
        digits=constants.MEASUREMENT_DIGITS,
    )
    as_found_in_tolerance = fields.Boolean(compute="_compute_evaluation",
                                           store=True,)
    as_left_in_tolerance = fields.Boolean(compute="_compute_evaluation",
                                          store=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="record_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    _point_record_uniq = models.Constraint(
        "UNIQUE(record_id, point_id)",
        "A calibration point may appear only once in a calibration record.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "as_found_value",
        "as_left_value",
        "as_found_recorded",
        "as_left_recorded",
        "nominal_value",
        "lower_limit",
        "upper_limit",
    )
    def _compute_evaluation(self) -> None:
        """Derive the deviations and the in-tolerance verdicts.

        A series with no recorded value evaluates to a zero deviation and to
        ``True`` for the in-tolerance flag, so that an unrecorded series never
        makes the parent record fail. Whether a series was recorded at all is
        carried separately by the ``*_recorded`` flags, which the parent record
        consults before aggregating.
        """
        for reading in self:
            if reading.as_found_recorded:
                reading.as_found_deviation = (
                    reading.as_found_value - reading.nominal_value
                )
                reading.as_found_in_tolerance = (
                    reading.lower_limit
                    <= reading.as_found_value
                    <= reading.upper_limit
                )
            else:
                reading.as_found_deviation = 0.0
                reading.as_found_in_tolerance = True

            if reading.as_left_recorded:
                reading.as_left_deviation = (
                    reading.as_left_value - reading.nominal_value
                )
                reading.as_left_in_tolerance = (
                    reading.lower_limit
                    <= reading.as_left_value
                    <= reading.upper_limit
                )
            else:
                reading.as_left_deviation = 0.0
                reading.as_left_in_tolerance = True

    @api.depends("point_id.name", "record_id.name")
    def _compute_display_name(self) -> None:
        """Show the record reference together with the point name."""
        for reading in self:
            reading.display_name = (
                f"{reading.record_id.name} / {reading.point_id.name}"
            )

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("as_found_value")
    def _onchange_as_found_value(self) -> None:
        """Flag the as-found series as recorded once a value is typed."""
        for reading in self:
            reading.as_found_recorded = True

    @api.onchange("as_left_value")
    def _onchange_as_left_value(self) -> None:
        """Flag the as-left series as recorded once a value is typed."""
        for reading in self:
            reading.as_left_recorded = True

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("point_id", "record_id")
    def _check_point_belongs_to_instrument(self) -> None:
        """A reading's point must belong to the record's instrument."""
        for reading in self:
            if reading.point_id.instrument_id != reading.record_id.instrument_id:
                raise ValidationError(
                    self.env._(
                        "Calibration point '%(point)s' does not belong to "
                        "instrument %(instrument)s.",
                        point=reading.point_id.name,
                        instrument=reading.record_id.instrument_id.code,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def _assert_parent_editable(self, operation: str) -> None:
        """Raise when the parent calibration record no longer accepts changes.

        Readings are the measurement evidence of the calibration. They must
        follow exactly the same immutability rule as their parent record, and
        the rule is enforced here rather than being left to the parent's own
        ``write`` override, because a reading can be reached directly.
        """
        editable_states = (
            constants.RECORD_STATE_DRAFT,
            constants.RECORD_STATE_IN_PROGRESS,
        )
        for reading in self:
            if reading.record_id.state not in editable_states:
                raise UserError(
                    self.env._(
                        "Calibration record %(record)s is in state "
                        "'%(state)s'. Readings can no longer be %(operation)s.",
                        record=reading.record_id.name,
                        state=reading.record_id.state,
                        operation=operation,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list: list) -> "LsCalibrationReading":
        """Reject new readings on a record that has left data entry.

        Without this guard the ``write`` and ``unlink`` overrides could be
        bypassed by adding a fresh reading to an already approved record,
        which would change its aggregated result.
        """
        editable_states = (
            constants.RECORD_STATE_DRAFT,
            constants.RECORD_STATE_IN_PROGRESS,
        )
        record_model = self.env["ls.calibration.record"]
        record_ids = {
            vals.get("record_id") for vals in vals_list if vals.get("record_id")
        }
        for record in record_model.browse(sorted(record_ids)):
            if record.state not in editable_states:
                raise UserError(
                    self.env._(
                        "Calibration record %(record)s is in state "
                        "'%(state)s'. No further reading can be added.",
                        record=record.name,
                        state=record.state,
                    )
                )
        return super().create(vals_list)

    def write(self, vals: dict) -> bool:
        """Reject reading changes once the parent record has left data entry."""
        self._assert_parent_editable(self.env._("modified"))
        return super().write(vals)

    def unlink(self) -> bool:
        """Reject reading deletion once the parent record has left data entry."""
        self._assert_parent_editable(self.env._("deleted"))
        return super().unlink()
