# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Instrument register.

``ls.calibration.instrument`` is the master record for every measuring
instrument and item of measuring equipment whose measurement accuracy is
controlled by the organisation.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationInstrument(models.Model):
    """Measuring instrument subject to periodic calibration."""

    _name = "ls.calibration.instrument"
    _description = "Calibration Instrument"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, id"

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Instrument Name",
        required=True,
        tracking=True,
        index=True,
    )
    code = fields.Char(
        string="Instrument ID",
        required=True,
        copy=False,
        readonly=False,
        default=lambda self: constants.NEW_SEQUENCE_PLACEHOLDER,
        tracking=True,
        index=True,
        help="Unique asset identifier of the instrument. Left as '/' the code "
        "is drawn from the instrument sequence on creation.",
    )
    category_id = fields.Many2one(comodel_name="ls.calibration.instrument.category", required=True,
                                  ondelete="restrict",
                                  tracking=True,
                                  index=True,)
    manufacturer = fields.Char(tracking=True)
    model_reference = fields.Char(string="Model", tracking=True)
    serial_number = fields.Char(tracking=True, index=True)
    asset_tag = fields.Char()
    location = fields.Char(tracking=True,
                           help="Free-text physical location. This module does not depend on the "
                           "Inventory application, so locations are recorded as text.",)
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        tracking=True,
        default=lambda self: self.env.user,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        help="Partner from which the instrument was procured.",
    )

    # ------------------------------------------------------------------
    # Metrological characteristics
    # ------------------------------------------------------------------
    unit_label = fields.Char(
        string="Measurement Unit",
        help="Unit of measurement of the instrument indication, entered as "
        "free text (for example 'g', 'degC', 'bar', 'mL').",
    )
    range_min = fields.Float(
        string="Range Minimum",
        digits=constants.MEASUREMENT_DIGITS,
    )
    range_max = fields.Float(
        string="Range Maximum",
        digits=constants.MEASUREMENT_DIGITS,
    )
    span = fields.Float(compute="_compute_span",
                        store=True,
                        digits=constants.MEASUREMENT_DIGITS,
                        help="Range Maximum minus Range Minimum. Used to evaluate tolerances "
                        "expressed as a percentage of span.",)
    resolution = fields.Float(digits=constants.MEASUREMENT_DIGITS,)
    accuracy_class = fields.Char()

    # ------------------------------------------------------------------
    # GxP classification
    # ------------------------------------------------------------------
    criticality = fields.Selection(selection=constants.CRITICALITY_SELECTION, required=True,
                                   default=constants.CRITICALITY_MAJOR,
                                   tracking=True,
                                   help="Impact of an inaccurate measurement from this instrument on "
                                   "product quality, patient safety or data integrity. The classification "
                                   "is established by the organisation's own risk assessment.",)
    is_gxp_critical = fields.Boolean(
        string="GxP Critical",
        compute="_compute_is_gxp_critical",
        store=True,
        readonly=False,
        tracking=True,
        help="Set when the instrument is used to generate or control data "
        "subject to Good Practice requirements. Defaults from the criticality "
        "but may be overridden.",
    )
    requires_oot_assessment = fields.Boolean(
        string="Requires OOT Impact Assessment",
        default=True,
        help="When set, an out-of-tolerance as-found result on this instrument "
        "raises an OOT event that must be assessed and closed.",
    )

    # ------------------------------------------------------------------
    # Calibration interval and status
    # ------------------------------------------------------------------
    calibration_interval_value = fields.Integer(
        string="Calibration Interval",
        required=True,
        default=1,
        tracking=True,
    )
    calibration_interval_uom = fields.Selection(
        selection=constants.INTERVAL_UOM_SELECTION,
        string="Interval Unit",
        required=True,
        default=constants.INTERVAL_UOM_YEAR,
        tracking=True,
    )
    due_soon_threshold_days = fields.Integer(
        string="Due Soon Threshold (days)",
        required=True,
        default=constants.DEFAULT_DUE_SOON_THRESHOLD_DAYS,
        help="Number of days before the next due date at which the instrument "
        "is reported as Due Soon.",
    )
    last_calibration_date = fields.Date(
        string="Last Calibration",
        compute="_compute_calibration_dates",
        store=True,
        tracking=True,
    )
    last_record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Last Approved Record",
        compute="_compute_calibration_dates",
        store=True,
    )
    next_due_date = fields.Date(
        string="Next Due",
        compute="_compute_calibration_dates",
        store=True,
        tracking=True,
    )
    days_to_due = fields.Integer(compute="_compute_calibration_status",
                                 help="Positive when the due date is in the future, negative when the "
                                 "instrument is overdue.",)
    calibration_status = fields.Selection(selection=constants.CAL_STATUS_SELECTION, compute="_compute_calibration_status",
                                          store=True,
                                          tracking=True,)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.INSTRUMENT_STATE_SELECTION,
        string="Status",
        required=True,
        default=constants.INSTRUMENT_STATE_DRAFT,
        tracking=True,
        copy=False,
    )
    commissioning_date = fields.Date(tracking=True)
    retirement_date = fields.Date(readonly=True, copy=False)
    quarantine_reason = fields.Text(copy=False)

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------
    point_ids = fields.One2many(
        comodel_name="ls.calibration.point",
        inverse_name="instrument_id",
        string="Calibration Points",
        copy=True,
    )
    plan_ids = fields.One2many(
        comodel_name="ls.calibration.plan",
        inverse_name="instrument_id",
        string="Calibration Plans",
    )
    record_ids = fields.One2many(
        comodel_name="ls.calibration.record",
        inverse_name="instrument_id",
        string="Calibration Records",
    )
    certificate_ids = fields.One2many(
        comodel_name="ls.calibration.certificate",
        inverse_name="instrument_id",
        string="Certificates",
    )
    oot_ids = fields.One2many(
        comodel_name="ls.calibration.oot",
        inverse_name="instrument_id",
        string="Out-of-Tolerance Events",
    )
    point_count = fields.Integer(compute="_compute_counts")
    plan_count = fields.Integer(compute="_compute_counts")
    record_count = fields.Integer(compute="_compute_counts")
    certificate_count = fields.Integer(compute="_compute_counts")
    oot_count = fields.Integer(compute="_compute_counts")
    open_oot_count = fields.Integer(compute="_compute_counts")

    # ------------------------------------------------------------------
    # Extension point
    # ------------------------------------------------------------------
    external_equipment_reference = fields.Char(help="Free-text reference to the same physical asset in another "
                                               "application (for example a maintenance or asset management system). "
                                               "This module declares no dependency on such an application; a separate "
                                               "bridge module may replace this field with a relational link.",
                                               )

    description = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Database constraints
    # ------------------------------------------------------------------
    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The instrument ID must be unique per company.",
    )
    _interval_positive = models.Constraint(
        "CHECK(calibration_interval_value > 0)",
        "The calibration interval must be strictly positive.",
    )
    _due_soon_threshold_non_negative = models.Constraint(
        "CHECK(due_soon_threshold_days >= 0)",
        "The Due Soon threshold cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("range_min", "range_max")
    def _compute_span(self) -> None:
        """Derive the measuring span from the declared range."""
        for instrument in self:
            instrument.span = instrument.range_max - instrument.range_min

    @api.depends("criticality")
    def _compute_is_gxp_critical(self) -> None:
        """Default the GxP flag from the criticality classification."""
        for instrument in self:
            instrument.is_gxp_critical = (
                instrument.criticality == constants.CRITICALITY_CRITICAL
            )

    @api.depends(
        "record_ids.state",
        "record_ids.performed_date",
        "record_ids.next_due_date",
    )
    def _compute_calibration_dates(self) -> None:
        """Derive the last calibration and next due date from approved records.

        Only records in the ``approved`` state contribute. A performed but not
        yet approved calibration does not release the instrument.
        """
        for instrument in self:
            approved = instrument.record_ids.filtered(
                lambda record: record.state == constants.RECORD_STATE_APPROVED
                and record.performed_date
            ).sorted(key=lambda record: record.performed_date, reverse=True)
            latest = approved[:1]
            instrument.last_record_id = latest
            instrument.last_calibration_date = (
                latest.performed_date if latest else False
            )
            if latest and latest.next_due_date:
                instrument.next_due_date = latest.next_due_date
            elif latest:
                instrument.next_due_date = instrument._add_interval(
                    latest.performed_date,
                    instrument.calibration_interval_value,
                    instrument.calibration_interval_uom,
                )
            else:
                instrument.next_due_date = False

    @api.depends("next_due_date", "due_soon_threshold_days", "last_calibration_date")
    def _compute_calibration_status(self) -> None:
        """Classify the instrument as never calibrated, OK, due soon or overdue."""
        today = fields.Date.context_today(self)
        for instrument in self:
            if not instrument.next_due_date:
                instrument.calibration_status = constants.CAL_STATUS_NEVER
                instrument.days_to_due = 0
                continue
            delta_days = (instrument.next_due_date - today).days
            instrument.days_to_due = delta_days
            if delta_days < 0:
                instrument.calibration_status = constants.CAL_STATUS_OVERDUE
            elif delta_days <= instrument.due_soon_threshold_days:
                instrument.calibration_status = constants.CAL_STATUS_DUE_SOON
            else:
                instrument.calibration_status = constants.CAL_STATUS_OK

    @api.depends(
        "point_ids",
        "plan_ids",
        "record_ids",
        "certificate_ids",
        "oot_ids",
        "oot_ids.state",
    )
    def _compute_counts(self) -> None:
        """Populate the smart-button counters."""
        for instrument in self:
            instrument.point_count = len(instrument.point_ids)
            instrument.plan_count = len(instrument.plan_ids)
            instrument.record_count = len(instrument.record_ids)
            instrument.certificate_count = len(instrument.certificate_ids)
            instrument.oot_count = len(instrument.oot_ids)
            instrument.open_oot_count = len(
                instrument.oot_ids.filtered(
                    lambda event: event.state != constants.OOT_STATE_CLOSED
                )
            )

    @api.depends("code", "name")
    def _compute_display_name(self) -> None:
        """Show the instrument ID together with its name."""
        for instrument in self:
            instrument.display_name = f"[{instrument.code}] {instrument.name}"

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("category_id")
    def _onchange_category_id(self) -> None:
        """Propose the category defaults on a new instrument."""
        for instrument in self:
            category = instrument.category_id
            if not category:
                continue
            if category.default_interval_value:
                instrument.calibration_interval_value = (
                    category.default_interval_value
                )
            if category.default_interval_uom:
                instrument.calibration_interval_uom = category.default_interval_uom
            if category.default_criticality:
                instrument.criticality = category.default_criticality

    # ------------------------------------------------------------------
    # Python constraints
    # ------------------------------------------------------------------
    @api.constrains("range_min", "range_max")
    def _check_range(self) -> None:
        """The upper range limit must not be below the lower range limit."""
        for instrument in self:
            if instrument.range_max < instrument.range_min:
                raise ValidationError(
                    self.env._(
                        "Instrument %(code)s: the range maximum (%(maximum)s) "
                        "cannot be lower than the range minimum (%(minimum)s).",
                        code=instrument.code,
                        maximum=instrument.range_max,
                        minimum=instrument.range_min,
                    )
                )

    @api.constrains("commissioning_date", "retirement_date")
    def _check_lifecycle_dates(self) -> None:
        """Retirement cannot precede commissioning."""
        for instrument in self:
            if (
                instrument.commissioning_date
                and instrument.retirement_date
                and instrument.retirement_date < instrument.commissioning_date
            ):
                raise ValidationError(
                    self.env._(
                        "Instrument %(code)s: the retirement date cannot "
                        "precede the commissioning date.",
                        code=instrument.code,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _add_interval(start: date, value: int, uom: str) -> date:
        """Return ``start`` shifted forward by ``value`` units of ``uom``.

        :param start: the base date.
        :param value: a strictly positive number of interval units.
        :param uom: one of the keys of
            :data:`constants.INTERVAL_UOM_TO_RELATIVEDELTA_KEY`.
        :return: the shifted date.
        """
        keyword = constants.INTERVAL_UOM_TO_RELATIVEDELTA_KEY[uom]
        return start + relativedelta(**{keyword: value})

    def _compute_next_due_from(self, performed_date: date) -> date:
        """Return the due date implied by a calibration performed on a date."""
        self.ensure_one()
        return self._add_interval(
            performed_date,
            self.calibration_interval_value,
            self.calibration_interval_uom,
        )

    def _assert_transition(self, target_state: str) -> None:
        """Raise when the requested lifecycle transition is not permitted."""
        for instrument in self:
            allowed = constants.INSTRUMENT_STATE_TRANSITIONS.get(
                instrument.state, ()
            )
            if target_state not in allowed:
                raise UserError(
                    self.env._(
                        "Instrument %(code)s cannot move from '%(current)s' to "
                        "'%(target)s'.",
                        code=instrument.code,
                        current=instrument.state,
                        target=target_state,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list: list) -> "LsCalibrationInstrument":
        """Draw the instrument code from the sequence when left as '/'."""
        for vals in vals_list:
            if vals.get("code", constants.NEW_SEQUENCE_PLACEHOLDER) in (
                False,
                constants.NEW_SEQUENCE_PLACEHOLDER,
            ):
                company_id = vals.get("company_id") or self.env.company.id
                vals["code"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code(
                    constants.SEQUENCE_CODE_INSTRUMENT
                ) or constants.NEW_SEQUENCE_PLACEHOLDER
        return super().create(vals_list)

    def unlink(self) -> bool:
        """Forbid deletion of instruments that carry calibration history.

        Calibration records are Good Practice evidence. Once an instrument has
        any record attached, the instrument master data must be retired rather
        than deleted so that the record remains interpretable.
        """
        for instrument in self:
            if instrument.record_ids:
                raise UserError(
                    self.env._(
                        "Instrument %(code)s carries %(count)s calibration "
                        "record(s) and cannot be deleted. Retire it instead.",
                        code=instrument.code,
                        count=len(instrument.record_ids),
                    )
                )
        return super().unlink()

    # ------------------------------------------------------------------
    # Lifecycle actions
    # ------------------------------------------------------------------
    def action_place_in_service(self) -> bool:
        """Move the instrument to ``in_service``."""
        self._assert_transition(constants.INSTRUMENT_STATE_IN_SERVICE)
        for instrument in self:
            if not instrument.point_ids:
                raise UserError(
                    self.env._(
                        "Instrument %(code)s has no calibration point defined. "
                        "At least one calibration point is required before the "
                        "instrument can be placed in service.",
                        code=instrument.code,
                    )
                )
            if not instrument.commissioning_date:
                instrument.commissioning_date = fields.Date.context_today(instrument)
        self.write({"state": constants.INSTRUMENT_STATE_IN_SERVICE})
        return True

    def action_quarantine(self) -> bool:
        """Move the instrument to ``quarantined``."""
        self._assert_transition(constants.INSTRUMENT_STATE_QUARANTINED)
        self.write({"state": constants.INSTRUMENT_STATE_QUARANTINED})
        for instrument in self:
            instrument.message_post(
                body=self.env._("Instrument placed in quarantine.")
            )
        return True

    def action_take_out_of_service(self) -> bool:
        """Move the instrument to ``out_of_service``."""
        self._assert_transition(constants.INSTRUMENT_STATE_OUT_OF_SERVICE)
        self.write({"state": constants.INSTRUMENT_STATE_OUT_OF_SERVICE})
        return True

    def action_retire(self) -> bool:
        """Move the instrument to ``retired`` and stamp the retirement date."""
        self._assert_transition(constants.INSTRUMENT_STATE_RETIRED)
        self.write(
            {
                "state": constants.INSTRUMENT_STATE_RETIRED,
                "retirement_date": fields.Date.context_today(self),
                "active": False,
            }
        )
        return True

    def action_reset_to_draft(self) -> bool:
        """Return a draft-eligible instrument to ``draft``.

        Only instruments that have never been calibrated may return to draft.
        """
        for instrument in self:
            if instrument.record_ids:
                raise UserError(
                    self.env._(
                        "Instrument %(code)s has calibration history and "
                        "cannot be reset to draft.",
                        code=instrument.code,
                    )
                )
        self.write({"state": constants.INSTRUMENT_STATE_DRAFT})
        return True

    # ------------------------------------------------------------------
    # Navigation actions
    # ------------------------------------------------------------------
    def _action_open_related(self, xml_id: str) -> dict:
        """Return a window action filtered on this instrument."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xml_id)
        action["domain"] = [("instrument_id", "=", self.id)]
        action["context"] = {
            "default_instrument_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action

    def action_open_points(self) -> dict:
        """Open the calibration points of this instrument."""
        return self._action_open_related("ls_calibration.action_ls_calibration_point")

    def action_open_plans(self) -> dict:
        """Open the calibration plans of this instrument."""
        return self._action_open_related("ls_calibration.action_ls_calibration_plan")

    def action_open_records(self) -> dict:
        """Open the calibration records of this instrument."""
        return self._action_open_related("ls_calibration.action_ls_calibration_record")

    def action_open_certificates(self) -> dict:
        """Open the calibration certificates of this instrument."""
        return self._action_open_related(
            "ls_calibration.action_ls_calibration_certificate"
        )

    def action_open_oot(self) -> dict:
        """Open the out-of-tolerance events of this instrument."""
        return self._action_open_related("ls_calibration.action_ls_calibration_oot")

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def _cron_refresh_calibration_status(self) -> bool:
        """Recompute the calibration status of every active instrument.

        ``calibration_status`` is stored and depends on the current date, so it
        does not invalidate itself when the day changes. This scheduled action
        forces the recomputation and posts a message on instruments that have
        newly become overdue.
        """
        instruments = self.search(
            [("state", "in", (
                constants.INSTRUMENT_STATE_IN_SERVICE,
                constants.INSTRUMENT_STATE_QUARANTINED,
            ))]
        )
        previous_status = {
            instrument.id: instrument.calibration_status
            for instrument in instruments
        }
        instruments.invalidate_recordset(
            ["calibration_status", "days_to_due"]
        )
        instruments._compute_calibration_status()
        instruments.flush_recordset(["calibration_status"])
        for instrument in instruments:
            became_overdue = (
                instrument.calibration_status == constants.CAL_STATUS_OVERDUE
                and previous_status.get(instrument.id)
                != constants.CAL_STATUS_OVERDUE
            )
            if became_overdue:
                instrument.message_post(
                    body=self.env._(
                        "Calibration is overdue. Due date was %(due)s.",
                        due=instrument.next_due_date,
                    )
                )
        return True
