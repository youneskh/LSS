# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration records.

``ls.calibration.record`` is the executed calibration event. It carries the
as-found and as-left readings, the reference standards used, the environmental
conditions, and the review and approval decisions.

Two controls implemented here are load-bearing for regulated use:

* **Segregation of duties.** The user who performs a calibration cannot be the
  user who reviews it, and neither can be the user who approves it. This is
  enforced in the ORM, not only in the user interface.
* **Immutability after approval.** Once approved, the record's data fields are
  rejected by ``write`` and the record cannot be deleted.
"""

from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationRecord(models.Model):
    """One executed calibration of one instrument."""

    _name = "ls.calibration.record"
    _description = "Calibration Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, name desc, id desc"

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Record Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: constants.NEW_SEQUENCE_PLACEHOLDER,
        index=True,
    )
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", required=True,
                                    ondelete="restrict",
                                    tracking=True,
                                    index=True,)
    instrument_code = fields.Char(
        string="Instrument ID",
        related="instrument_id.code",
        store=True,
        readonly=True,
    )
    category_id = fields.Many2one(comodel_name="ls.calibration.instrument.category", related="instrument_id.category_id",
                                  store=True,
                                  readonly=True,)
    criticality = fields.Selection(related="instrument_id.criticality", store=True,
                                   readonly=True,)
    plan_id = fields.Many2one(
        comodel_name="ls.calibration.plan",
        string="Calibration Plan",
        ondelete="restrict",
        tracking=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Scheduling and execution
    # ------------------------------------------------------------------
    scheduled_date = fields.Date(required=True,
                                 default=fields.Date.context_today,
                                 tracking=True,
                                 index=True,)
    performed_date = fields.Date(string="Performed On", tracking=True, copy=False)
    provider_type = fields.Selection(
        selection=constants.PROVIDER_SELECTION,
        string="Performed By",
        required=True,
        default=constants.PROVIDER_INTERNAL,
        tracking=True,
    )
    performed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Performed By (User)",
        tracking=True,
        copy=False,
    )
    performed_by_name = fields.Char(
        string="Performed By (Name)",
        tracking=True,
        copy=False,
        help="Name of the external technician when the calibration is "
        "performed by a service provider.",
    )
    service_provider_id = fields.Many2one(
        comodel_name="res.partner",
        string="External Provider",
        tracking=True,
    )
    procedure_reference = fields.Char(tracking=True)
    standard_ids = fields.Many2many(
        comodel_name="ls.calibration.standard",
        relation="ls_calibration_record_standard_rel",
        column1="record_id",
        column2="standard_id",
        string="Reference Standards",
    )

    # ------------------------------------------------------------------
    # Environmental conditions
    # ------------------------------------------------------------------
    ambient_temperature = fields.Float(digits=constants.MEASUREMENT_DIGITS,)
    ambient_temperature_unit = fields.Char(
        string="Temperature Unit", default="degC"
    )
    ambient_humidity = fields.Float(
        string="Relative Humidity (%)",
        digits=constants.MEASUREMENT_DIGITS,
    )

    # ------------------------------------------------------------------
    # Readings and results
    # ------------------------------------------------------------------
    reading_ids = fields.One2many(
        comodel_name="ls.calibration.reading",
        inverse_name="record_id",
        string="Readings",
        copy=False,
    )
    reading_count = fields.Integer(compute="_compute_results", store=True)
    as_found_result = fields.Selection(
        selection=constants.RESULT_SELECTION,
        string="As-Found Result",
        compute="_compute_results",
        store=True,
        tracking=True,
    )
    as_left_result = fields.Selection(
        selection=constants.RESULT_SELECTION,
        string="As-Left Result",
        compute="_compute_results",
        store=True,
        tracking=True,
    )
    overall_result = fields.Selection(selection=constants.OVERALL_RESULT_SELECTION, compute="_compute_results",
                                      store=True,
                                      tracking=True,)
    adjustment_performed = fields.Boolean(tracking=True,
                                          help="Set when the instrument was adjusted between the as-found and "
                                          "the as-left measurement series.",)
    failed_point_count = fields.Integer(
        string="Failed Points", compute="_compute_results", store=True
    )

    # ------------------------------------------------------------------
    # Due date
    # ------------------------------------------------------------------
    next_due_date = fields.Date(compute="_compute_next_due_date",
                                store=True,
                                readonly=False,
                                tracking=True,
                                help="Computed from the performed date and the applicable interval. "
                                "May be overridden by an authorised user; the override is tracked.",)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.RECORD_STATE_SELECTION,
        string="Status",
        required=True,
        default=constants.RECORD_STATE_DRAFT,
        tracking=True,
        copy=False,
        index=True,
    )
    reviewed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Reviewed By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    reviewed_date = fields.Datetime(
        string="Reviewed On", readonly=True, copy=False, tracking=True
    )
    approved_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_date = fields.Datetime(
        string="Approved On", readonly=True, copy=False, tracking=True
    )
    rejection_reason = fields.Text(copy=False)
    cancellation_reason = fields.Text(copy=False)
    remarks = fields.Text()

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------
    certificate_ids = fields.One2many(
        comodel_name="ls.calibration.certificate",
        inverse_name="record_id",
        string="Certificates",
    )
    certificate_count = fields.Integer(compute="_compute_relation_counts")
    oot_ids = fields.One2many(
        comodel_name="ls.calibration.oot",
        inverse_name="record_id",
        string="Out-of-Tolerance Events",
    )
    oot_count = fields.Integer(compute="_compute_relation_counts")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The calibration record reference must be unique per company.",
    )
    _humidity_range = models.Constraint(
        "CHECK(ambient_humidity >= 0 AND ambient_humidity <= 100)",
        "The relative humidity must lie between 0 and 100 percent.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "reading_ids",
        "reading_ids.as_found_in_tolerance",
        "reading_ids.as_left_in_tolerance",
        "reading_ids.as_found_recorded",
        "reading_ids.as_left_recorded",
        "adjustment_performed",
    )
    def _compute_results(self) -> None:
        """Aggregate the per-point readings into record-level verdicts.

        ``as_found_result`` and ``as_left_result`` are ``pass`` only when every
        recorded reading of the corresponding series is inside tolerance. A
        series with no recorded value at all evaluates to ``not_applicable``.

        ``overall_result`` distinguishes a calibration that passed as found
        from one that only passed after an adjustment, because the two carry
        different consequences for previously generated data.
        """
        for record in self:
            readings = record.reading_ids
            record.reading_count = len(readings)

            found_recorded = readings.filtered("as_found_recorded")
            left_recorded = readings.filtered("as_left_recorded")

            record.as_found_result = record._series_result(found_recorded, "as_found")
            record.as_left_result = record._series_result(left_recorded, "as_left")
            record.failed_point_count = len(
                found_recorded.filtered(lambda line: not line.as_found_in_tolerance)
            )
            record.overall_result = record._compute_overall_result()

    @staticmethod
    def _series_result(readings, prefix: str) -> str:
        """Return the pass/fail verdict of one measurement series."""
        if not readings:
            return constants.RESULT_NOT_APPLICABLE
        field_name = f"{prefix}_in_tolerance"
        if all(readings.mapped(field_name)):
            return constants.RESULT_PASS
        return constants.RESULT_FAIL

    def _compute_overall_result(self) -> str:
        """Combine the as-found and as-left verdicts into an overall result."""
        self.ensure_one()
        found = self.as_found_result
        left = self.as_left_result
        if found == constants.RESULT_NOT_APPLICABLE and left == (
            constants.RESULT_NOT_APPLICABLE
        ):
            return constants.OVERALL_RESULT_NOT_APPLICABLE
        if found == constants.RESULT_PASS and left in (
            constants.RESULT_PASS,
            constants.RESULT_NOT_APPLICABLE,
        ):
            return constants.OVERALL_RESULT_PASS
        if found == constants.RESULT_FAIL and left == constants.RESULT_PASS:
            return constants.OVERALL_RESULT_PASS_AFTER_ADJUSTMENT
        return constants.OVERALL_RESULT_FAIL

    @api.depends(
        "performed_date",
        "plan_id.interval_value",
        "plan_id.interval_uom",
        "instrument_id.calibration_interval_value",
        "instrument_id.calibration_interval_uom",
    )
    def _compute_next_due_date(self) -> None:
        """Derive the next due date from the performed date and the interval.

        The plan interval takes precedence over the instrument interval when a
        plan is attached, because the plan is the approved statement of the
        calibration frequency.
        """
        for record in self:
            if not record.performed_date:
                record.next_due_date = False
                continue
            record.next_due_date = record._get_next_due_date(record.performed_date)

    def _get_next_due_date(self, from_date: date) -> Optional[date]:
        """Return the due date implied by the applicable interval."""
        self.ensure_one()
        if self.plan_id:
            value = self.plan_id.interval_value
            uom = self.plan_id.interval_uom
        else:
            value = self.instrument_id.calibration_interval_value
            uom = self.instrument_id.calibration_interval_uom
        if not value or not uom:
            return False
        keyword = constants.INTERVAL_UOM_TO_RELATIVEDELTA_KEY[uom]
        return from_date + relativedelta(**{keyword: value})

    @api.depends("certificate_ids", "oot_ids")
    def _compute_relation_counts(self) -> None:
        """Populate the smart-button counters."""
        for record in self:
            record.certificate_count = len(record.certificate_ids)
            record.oot_count = len(record.oot_ids)

    @api.depends("name", "instrument_id.code")
    def _compute_display_name(self) -> None:
        """Show the record reference together with the instrument ID."""
        for record in self:
            record.display_name = f"{record.name} - {record.instrument_id.code}"

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("instrument_id")
    def _onchange_instrument_id(self) -> None:
        """Propose the instrument's approved plan and procedure reference."""
        for record in self:
            instrument = record.instrument_id
            if not instrument:
                continue
            effective_plans = instrument.plan_ids.filtered(
                lambda plan: plan.state == constants.PLAN_STATE_APPROVED
                and plan.active
            )
            if len(effective_plans) == 1:
                record.plan_id = effective_plans
                record.provider_type = effective_plans.provider_type
                record.service_provider_id = effective_plans.service_provider_id
                record.procedure_reference = effective_plans.procedure_reference

    @api.onchange("provider_type")
    def _onchange_provider_type(self) -> None:
        """Clear the fields that do not apply to the selected provider type."""
        for record in self:
            if record.provider_type == constants.PROVIDER_INTERNAL:
                record.service_provider_id = False
                record.performed_by_name = False
            else:
                record.performed_by_user_id = False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("plan_id", "instrument_id")
    def _check_plan_instrument_consistency(self) -> None:
        """A record's plan must belong to the same instrument."""
        for record in self:
            if (
                record.plan_id
                and record.plan_id.instrument_id != record.instrument_id
            ):
                raise ValidationError(
                    self.env._(
                        "Record %(record)s references calibration plan "
                        "'%(plan)s', which belongs to a different instrument.",
                        record=record.name,
                        plan=record.plan_id.name,
                    )
                )

    @api.constrains("scheduled_date", "performed_date")
    def _check_performed_date(self) -> None:
        """A calibration cannot be recorded as performed in the future."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.performed_date and record.performed_date > today:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s: the performed date cannot be in "
                        "the future.",
                        record=record.name,
                    )
                )

    @api.constrains(
        "performed_by_user_id", "reviewed_by_user_id", "approved_by_user_id"
    )
    def _check_segregation_of_duties(self) -> None:
        """Enforce distinct performer, reviewer and approver.

        The check runs at ORM level so that it holds for records created or
        modified through the external API as well as through the user
        interface.
        """
        for record in self:
            performer = record.performed_by_user_id
            reviewer = record.reviewed_by_user_id
            approver = record.approved_by_user_id
            if performer and reviewer and performer == reviewer:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s: the user who performed the "
                        "calibration cannot also review it.",
                        record=record.name,
                    )
                )
            if performer and approver and performer == approver:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s: the user who performed the "
                        "calibration cannot also approve it.",
                        record=record.name,
                    )
                )
            if reviewer and approver and reviewer == approver:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s: the user who reviewed the "
                        "calibration cannot also approve it.",
                        record=record.name,
                    )
                )

    @api.constrains("state", "standard_ids", "performed_date")
    def _check_performed_completeness(self) -> None:
        """A performed calibration must cite at least one reference standard."""
        checked_states = (
            constants.RECORD_STATE_PERFORMED,
            constants.RECORD_STATE_UNDER_REVIEW,
            constants.RECORD_STATE_APPROVED,
        )
        for record in self:
            if record.state not in checked_states:
                continue
            if not record.standard_ids:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s must cite at least one reference "
                        "standard before it can be marked as performed.",
                        record=record.name,
                    )
                )
            if not record.performed_date:
                raise ValidationError(
                    self.env._(
                        "Record %(record)s must carry a performed date.",
                        record=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _assert_transition(self, target_state: str) -> None:
        """Raise when the requested record transition is not permitted."""
        for record in self:
            allowed = constants.RECORD_STATE_TRANSITIONS.get(record.state, ())
            if target_state not in allowed:
                raise UserError(
                    self.env._(
                        "Calibration record %(record)s cannot move from "
                        "'%(current)s' to '%(target)s'.",
                        record=record.name,
                        current=record.state,
                        target=target_state,
                    )
                )

    def _populate_readings_from_points(self) -> None:
        """Create one empty reading line per active calibration point."""
        reading_model = self.env["ls.calibration.reading"]
        for record in self:
            existing_points = record.reading_ids.mapped("point_id")
            missing = record.instrument_id.point_ids.filtered(
                lambda point, done=existing_points: point not in done
            )
            if missing:
                reading_model.create(
                    [
                        {"record_id": record.id, "point_id": point.id}
                        for point in missing
                    ]
                )

    def _create_oot_event(self) -> models.Model:
        """Raise an out-of-tolerance event for an as-found failure.

        The affected period runs from the previous approved calibration of the
        same instrument to the as-found measurement of this calibration, since
        that is the window during which measurements may have been wrong.
        """
        self.ensure_one()
        previous = self.search(
            [
                ("instrument_id", "=", self.instrument_id.id),
                ("state", "=", constants.RECORD_STATE_APPROVED),
                ("id", "!=", self.id),
                ("performed_date", "!=", False),
                ("performed_date", "<=", self.performed_date),
            ],
            order="performed_date desc",
            limit=1,
        )
        return self.env["ls.calibration.oot"].create(
            {
                "record_id": self.id,
                "detection_date": self.performed_date,
                "affected_period_start": (
                    previous.performed_date if previous else False
                ),
                "affected_period_end": self.performed_date,
                "description": self.env._(
                    "As-found measurement outside tolerance on "
                    "%(count)s calibration point(s).",
                    count=self.failed_point_count,
                ),
                "company_id": self.company_id.id,
            }
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list: list) -> "LsCalibrationRecord":
        """Draw the record reference from the sequence and seed the readings."""
        for vals in vals_list:
            if vals.get("name", constants.NEW_SEQUENCE_PLACEHOLDER) in (
                False,
                constants.NEW_SEQUENCE_PLACEHOLDER,
            ):
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code(
                    constants.SEQUENCE_CODE_RECORD
                ) or constants.NEW_SEQUENCE_PLACEHOLDER
        records = super().create(vals_list)
        records._populate_readings_from_points()
        return records

    def write(self, vals: dict) -> bool:
        """Reject data changes on approved or cancelled records.

        Messaging, activity and child-collection fields remain writable so that
        the chatter, certificates and out-of-tolerance events attached to a
        closed record continue to function.
        """
        protected = set(vals) - set(constants.RECORD_LOCKED_WRITABLE_FIELDS)
        if protected:
            locked = self.filtered(
                lambda record: record.state in constants.RECORD_LOCKED_STATES
            )
            # A transition out of a locked state is never permitted, so a
            # write that only changes ``state`` is also refused here.
            if locked:
                raise UserError(
                    self.env._(
                        "Calibration record %(record)s is %(state)s and can no "
                        "longer be modified. Field(s) refused: %(fields)s.",
                        record=locked[0].name,
                        state=locked[0].state,
                        fields=", ".join(sorted(protected)),
                    )
                )
        return super().write(vals)

    def unlink(self) -> bool:
        """Permit deletion only of draft records.

        Any calibration that has reached the in-progress state is Good Practice
        evidence and must be cancelled with a recorded reason rather than
        removed.
        """
        for record in self:
            if record.state != constants.RECORD_STATE_DRAFT:
                raise UserError(
                    self.env._(
                        "Calibration record %(record)s is in state "
                        "'%(state)s' and cannot be deleted. Cancel it "
                        "instead.",
                        record=record.name,
                        state=record.state,
                    )
                )
        return super().unlink()

    def copy_data(self, default=None):
        """Duplicate a record as a fresh draft without execution evidence."""
        default = dict(default or {})
        default.setdefault("name", constants.NEW_SEQUENCE_PLACEHOLDER)
        default.setdefault("state", constants.RECORD_STATE_DRAFT)
        default.setdefault("performed_date", False)
        default.setdefault("performed_by_user_id", False)
        default.setdefault("standard_ids", [(5, 0, 0)])
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_start(self) -> bool:
        """Move the record to ``in_progress`` and seed missing readings."""
        self._assert_transition(constants.RECORD_STATE_IN_PROGRESS)
        for record in self:
            if record.instrument_id.state == constants.INSTRUMENT_STATE_RETIRED:
                raise UserError(
                    self.env._(
                        "Instrument %(instrument)s is retired; no further "
                        "calibration can be started.",
                        instrument=record.instrument_id.code,
                    )
                )
        self.write(
            {
                "state": constants.RECORD_STATE_IN_PROGRESS,
                "rejection_reason": False,
            }
        )
        self._populate_readings_from_points()
        return True

    def action_mark_performed(self) -> bool:
        """Close data entry and stamp the performer.

        Records the calling user as the performer for an internal calibration,
        which is what the segregation-of-duties constraint later checks against
        the reviewer and the approver.
        """
        self._assert_transition(constants.RECORD_STATE_PERFORMED)
        today = fields.Date.context_today(self)
        for record in self:
            if not record.reading_ids:
                raise UserError(
                    self.env._(
                        "Record %(record)s carries no reading. Enter the "
                        "measurement results before marking it as performed.",
                        record=record.name,
                    )
                )
            if not record.reading_ids.filtered("as_found_recorded"):
                raise UserError(
                    self.env._(
                        "Record %(record)s carries no as-found value. At "
                        "least one as-found measurement is required.",
                        record=record.name,
                    )
                )
            values = {
                "state": constants.RECORD_STATE_PERFORMED,
                "performed_date": record.performed_date or today,
            }
            if record.provider_type == constants.PROVIDER_INTERNAL:
                values["performed_by_user_id"] = (
                    record.performed_by_user_id.id or self.env.user.id
                )
            record.write(values)
        return True

    def action_submit_for_review(self) -> bool:
        """Send a performed record to review."""
        self._assert_transition(constants.RECORD_STATE_UNDER_REVIEW)
        self.write({"state": constants.RECORD_STATE_UNDER_REVIEW})
        return True

    def action_approve(self) -> bool:
        """Approve the record, releasing the instrument and raising any OOT.

        Approval is the point at which the calibration takes effect: the
        instrument's next due date is refreshed from this record, and an
        out-of-tolerance event is raised when the as-found series failed.
        """
        self._assert_transition(constants.RECORD_STATE_APPROVED)
        now = fields.Datetime.now()
        for record in self:
            if record.approved_by_user_id:
                raise UserError(
                    self.env._(
                        "Record %(record)s already carries an approval.",
                        record=record.name,
                    )
                )
            if record.performed_by_user_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Record %(record)s was performed by you and must be "
                        "approved by a different user.",
                        record=record.name,
                    )
                )
            if record.reviewed_by_user_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Record %(record)s was reviewed by you and must be "
                        "approved by a different user.",
                        record=record.name,
                    )
                )
            record.write(
                {
                    "state": constants.RECORD_STATE_APPROVED,
                    "approved_by_user_id": self.env.user.id,
                    "approved_date": now,
                }
            )
            needs_oot = (
                record.as_found_result == constants.RESULT_FAIL
                and record.instrument_id.requires_oot_assessment
                and not record.oot_ids
            )
            if needs_oot:
                event = record._create_oot_event()
                record.message_post(
                    body=self.env._(
                        "Out-of-tolerance event %(event)s raised on approval.",
                        event=event.name,
                    )
                )
        return True

    def action_review(self) -> bool:
        """Record the reviewer's sign-off without approving the record."""
        for record in self:
            if record.state != constants.RECORD_STATE_UNDER_REVIEW:
                raise UserError(
                    self.env._(
                        "Record %(record)s is not under review.",
                        record=record.name,
                    )
                )
            if record.performed_by_user_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Record %(record)s was performed by you and must be "
                        "reviewed by a different user.",
                        record=record.name,
                    )
                )
            record.write(
                {
                    "reviewed_by_user_id": self.env.user.id,
                    "reviewed_date": fields.Datetime.now(),
                }
            )
        return True

    def action_open_reject_wizard(self) -> dict:
        """Open the wizard that captures a mandatory rejection reason."""
        self.ensure_one()
        self._assert_transition(constants.RECORD_STATE_REJECTED)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Reject Calibration Record"),
            "res_model": "ls.calibration.record.reject",
            "view_mode": "form",
            "target": "new",
            "context": {"default_record_id": self.id},
        }

    def action_reject(self, reason: str) -> bool:
        """Reject a record under review, recording the reason.

        :param reason: the non-empty rejection reason.
        """
        self._assert_transition(constants.RECORD_STATE_REJECTED)
        if not reason or not reason.strip():
            raise UserError(
                self.env._("A rejection reason is required.")
            )
        self.write(
            {
                "state": constants.RECORD_STATE_REJECTED,
                "rejection_reason": reason,
                "reviewed_by_user_id": False,
                "reviewed_date": False,
            }
        )
        return True

    def action_cancel(self) -> bool:
        """Cancel a record, requiring a recorded cancellation reason."""
        self._assert_transition(constants.RECORD_STATE_CANCELLED)
        for record in self:
            if not record.cancellation_reason:
                raise UserError(
                    self.env._(
                        "A cancellation reason is required before record "
                        "%(record)s can be cancelled.",
                        record=record.name,
                    )
                )
        self.write({"state": constants.RECORD_STATE_CANCELLED})
        return True

    def action_open_certificates(self) -> dict:
        """Open the certificates attached to this record."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.action_ls_calibration_certificate"
        )
        action["domain"] = [("record_id", "=", self.id)]
        action["context"] = {
            "default_record_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action

    def action_open_oot(self) -> dict:
        """Open the out-of-tolerance events raised by this record."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.action_ls_calibration_oot"
        )
        action["domain"] = [("record_id", "=", self.id)]
        action["context"] = {"default_record_id": self.id}
        return action

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_upcoming_calibrations(self) -> bool:
        """Post a chatter reminder on scheduled calibrations that fall due.

        Instruments whose calibration status is Due Soon or Overdue receive a
        message on their most recent open calibration record, or on the
        instrument itself when no open record exists.
        """
        instrument_model = self.env["ls.calibration.instrument"]
        instruments = instrument_model.search(
            [
                ("state", "=", constants.INSTRUMENT_STATE_IN_SERVICE),
                (
                    "calibration_status",
                    "in",
                    (constants.CAL_STATUS_DUE_SOON, constants.CAL_STATUS_OVERDUE),
                ),
            ]
        )
        for instrument in instruments:
            open_records = instrument.record_ids.filtered(
                lambda record: record.state
                in (
                    constants.RECORD_STATE_DRAFT,
                    constants.RECORD_STATE_IN_PROGRESS,
                )
            )
            body = self.env._(
                "Calibration of instrument %(instrument)s is %(status)s. "
                "Due date: %(due)s.",
                instrument=instrument.code,
                status=instrument.calibration_status,
                due=instrument.next_due_date,
            )
            target = open_records[:1] or instrument
            target.message_post(body=body)
        return True
