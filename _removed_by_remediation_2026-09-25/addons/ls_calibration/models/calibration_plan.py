# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration plans.

A calibration plan defines, for one instrument, how often it is calibrated,
by whom, and against which written procedure. Approved plans are the source
from which scheduled calibration records are generated.
"""

from datetime import date
from typing import List, Optional

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationPlan(models.Model):
    """Periodic calibration plan attached to one instrument."""

    _name = "ls.calibration.plan"
    _description = "Calibration Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "instrument_id, start_date desc, id desc"

    name = fields.Char(
        string="Plan Reference",
        required=True,
        tracking=True,
        help="Reference of the calibration plan, for example the number of "
        "the governing procedure or plan document.",
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

    # ------------------------------------------------------------------
    # Periodicity
    # ------------------------------------------------------------------
    interval_value = fields.Integer(
        string="Interval",
        required=True,
        default=1,
        tracking=True,
    )
    interval_uom = fields.Selection(
        selection=constants.INTERVAL_UOM_SELECTION,
        string="Interval Unit",
        required=True,
        default=constants.INTERVAL_UOM_YEAR,
        tracking=True,
    )
    start_date = fields.Date(
        string="Effective From",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    end_date = fields.Date(string="Effective To", tracking=True)
    next_generation_date = fields.Date(
        string="Next Scheduled Calibration",
        compute="_compute_next_generation_date",
        store=True,
        help="Date of the next calibration this plan will generate. Derived "
        "from the latest scheduled or approved record, or from the plan start "
        "date when no record exists yet.",
    )

    # ------------------------------------------------------------------
    # Execution arrangements
    # ------------------------------------------------------------------
    provider_type = fields.Selection(
        selection=constants.PROVIDER_SELECTION,
        string="Performed By",
        required=True,
        default=constants.PROVIDER_INTERNAL,
        tracking=True,
    )
    service_provider_id = fields.Many2one(
        comodel_name="res.partner",
        string="External Provider",
        tracking=True,
    )
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    procedure_reference = fields.Char(tracking=True,
                                      help="Identifier of the written calibration procedure or SOP applied. "
                                      "Recorded as text; this module declares no dependency on a document "
                                      "management application.",)
    method_description = fields.Text()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.PLAN_STATE_SELECTION,
        string="Status",
        required=True,
        default=constants.PLAN_STATE_DRAFT,
        tracking=True,
        copy=False,
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
    suspension_reason = fields.Text(copy=False)
    closure_reason = fields.Text(copy=False)

    record_ids = fields.One2many(
        comodel_name="ls.calibration.record",
        inverse_name="plan_id",
        string="Calibration Records",
    )
    record_count = fields.Integer(compute="_compute_record_count")
    company_id = fields.Many2one(comodel_name="res.company", related="instrument_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)
    active = fields.Boolean(default=True)

    _interval_positive = models.Constraint(
        "CHECK(interval_value > 0)",
        "The calibration plan interval must be strictly positive.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("record_ids")
    def _compute_record_count(self) -> None:
        """Count the records generated from each plan."""
        for plan in self:
            plan.record_count = len(plan.record_ids)

    @api.depends(
        "start_date",
        "interval_value",
        "interval_uom",
        "record_ids.scheduled_date",
        "record_ids.state",
    )
    def _compute_next_generation_date(self) -> None:
        """Determine the date of the next calibration to be generated."""
        for plan in self:
            plan.next_generation_date = plan._get_next_generation_date()

    @api.depends("name", "instrument_id.code")
    def _compute_display_name(self) -> None:
        """Show the plan reference together with the instrument ID."""
        for plan in self:
            plan.display_name = f"{plan.name} - {plan.instrument_id.code}"

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("instrument_id")
    def _onchange_instrument_id(self) -> None:
        """Inherit the interval declared on the instrument."""
        for plan in self:
            instrument = plan.instrument_id
            if not instrument:
                continue
            plan.interval_value = instrument.calibration_interval_value
            plan.interval_uom = instrument.calibration_interval_uom
            if instrument.responsible_user_id:
                plan.responsible_user_id = instrument.responsible_user_id

    @api.onchange("provider_type")
    def _onchange_provider_type(self) -> None:
        """Clear the external provider when the plan becomes internal."""
        for plan in self:
            if plan.provider_type == constants.PROVIDER_INTERNAL:
                plan.service_provider_id = False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("start_date", "end_date")
    def _check_effective_dates(self) -> None:
        """The effective-to date cannot precede the effective-from date."""
        for plan in self:
            if plan.end_date and plan.end_date < plan.start_date:
                raise ValidationError(
                    self.env._(
                        "Calibration plan '%(plan)s': the effective-to date "
                        "cannot precede the effective-from date.",
                        plan=plan.name,
                    )
                )

    @api.constrains("provider_type", "service_provider_id")
    def _check_external_provider(self) -> None:
        """An external plan must name the external provider."""
        for plan in self:
            if (
                plan.provider_type == constants.PROVIDER_EXTERNAL
                and not plan.service_provider_id
            ):
                raise ValidationError(
                    self.env._(
                        "Calibration plan '%(plan)s' is performed externally "
                        "and must name an external provider.",
                        plan=plan.name,
                    )
                )

    @api.constrains("instrument_id", "state", "start_date", "end_date", "active")
    def _check_single_active_plan(self) -> None:
        """Only one approved plan may be effective per instrument at a time.

        Two approved plans whose effective windows overlap would give an
        instrument two contradictory calibration intervals.
        """
        for plan in self:
            if plan.state != constants.PLAN_STATE_APPROVED or not plan.active:
                continue
            overlapping = self.search(
                [
                    ("id", "!=", plan.id),
                    ("instrument_id", "=", plan.instrument_id.id),
                    ("state", "=", constants.PLAN_STATE_APPROVED),
                    ("active", "=", True),
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", plan.start_date),
                ]
            )
            conflicting = overlapping.filtered(
                lambda other, current=plan: not current.end_date
                or other.start_date <= current.end_date
            )
            if conflicting:
                raise ValidationError(
                    self.env._(
                        "Instrument %(instrument)s already has an approved "
                        "calibration plan (%(other)s) whose effective period "
                        "overlaps this one.",
                        instrument=plan.instrument_id.code,
                        other=conflicting[0].name,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_next_generation_date(self) -> Optional[date]:
        """Return the date of the next calibration this plan should produce.

        The anchor is the latest non-cancelled record already attached to the
        plan. When no such record exists the plan start date is used, so that
        the first generation run creates a calibration on the start date.
        """
        self.ensure_one()
        live_records = self.record_ids.filtered(
            lambda record: record.state != constants.RECORD_STATE_CANCELLED
            and record.scheduled_date
        )
        if not live_records:
            return self.start_date
        latest = max(live_records.mapped("scheduled_date"))
        keyword = constants.INTERVAL_UOM_TO_RELATIVEDELTA_KEY[self.interval_uom]
        return latest + relativedelta(**{keyword: self.interval_value})

    def _assert_transition(self, target_state: str) -> None:
        """Raise when the requested plan transition is not permitted."""
        for plan in self:
            allowed = constants.PLAN_STATE_TRANSITIONS.get(plan.state, ())
            if target_state not in allowed:
                raise UserError(
                    self.env._(
                        "Calibration plan '%(plan)s' cannot move from "
                        "'%(current)s' to '%(target)s'.",
                        plan=plan.name,
                        current=plan.state,
                        target=target_state,
                    )
                )

    def _is_effective_on(self, target_date: date) -> bool:
        """Return whether the plan is effective on the given date."""
        self.ensure_one()
        if self.state != constants.PLAN_STATE_APPROVED or not self.active:
            return False
        if target_date < self.start_date:
            return False
        return not self.end_date or target_date <= self.end_date

    def _prepare_record_values(self, scheduled_date: date) -> dict:
        """Build the values of a calibration record generated from this plan."""
        self.ensure_one()
        return {
            "instrument_id": self.instrument_id.id,
            "plan_id": self.id,
            "scheduled_date": scheduled_date,
            "provider_type": self.provider_type,
            "service_provider_id": self.service_provider_id.id or False,
            "procedure_reference": self.procedure_reference,
            "company_id": self.company_id.id,
        }

    def _generate_records_until(self, horizon_date: date) -> models.Model:
        """Create scheduled calibration records up to a horizon date.

        :param horizon_date: the latest scheduled date to generate.
        :return: the recordset of created ``ls.calibration.record`` records.
        """
        record_model = self.env["ls.calibration.record"]
        values_list: List[dict] = []
        for plan in self:
            if plan.state != constants.PLAN_STATE_APPROVED or not plan.active:
                continue
            candidate = plan._get_next_generation_date()
            guard = 0
            while (
                candidate
                and candidate <= horizon_date
                and plan._is_effective_on(candidate)
            ):
                guard += 1
                if guard > constants.MAX_GENERATED_RECORDS_PER_PLAN:
                    raise UserError(
                        self.env._(
                            "Generating calibrations for plan '%(plan)s' "
                            "would create more than %(limit)s records. "
                            "Reduce the horizon date or review the interval.",
                            plan=plan.name,
                            limit=constants.MAX_GENERATED_RECORDS_PER_PLAN,
                        )
                    )
                values_list.append(plan._prepare_record_values(candidate))
                keyword = constants.INTERVAL_UOM_TO_RELATIVEDELTA_KEY[
                    plan.interval_uom
                ]
                candidate = candidate + relativedelta(
                    **{keyword: plan.interval_value}
                )
        if not values_list:
            return record_model
        return record_model.create(values_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_approve(self) -> bool:
        """Approve the plan so that it can generate calibration records."""
        self._assert_transition(constants.PLAN_STATE_APPROVED)
        for plan in self:
            if plan.instrument_id.state == constants.INSTRUMENT_STATE_RETIRED:
                raise UserError(
                    self.env._(
                        "Instrument %(instrument)s is retired; its "
                        "calibration plan cannot be approved.",
                        instrument=plan.instrument_id.code,
                    )
                )
            if not plan.instrument_id.point_ids:
                raise UserError(
                    self.env._(
                        "Instrument %(instrument)s has no calibration point "
                        "defined. Define at least one point before approving "
                        "the plan.",
                        instrument=plan.instrument_id.code,
                    )
                )
        self.write(
            {
                "state": constants.PLAN_STATE_APPROVED,
                "approved_by_user_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            }
        )
        return True

    def action_suspend(self) -> bool:
        """Suspend the plan, stopping the generation of new records."""
        self._assert_transition(constants.PLAN_STATE_SUSPENDED)
        for plan in self:
            if not plan.suspension_reason:
                raise UserError(
                    self.env._(
                        "A suspension reason is required before calibration "
                        "plan '%(plan)s' can be suspended.",
                        plan=plan.name,
                    )
                )
        self.write({"state": constants.PLAN_STATE_SUSPENDED})
        return True

    def action_resume(self) -> bool:
        """Return a suspended plan to the approved state."""
        self._assert_transition(constants.PLAN_STATE_APPROVED)
        self.write(
            {
                "state": constants.PLAN_STATE_APPROVED,
                "suspension_reason": False,
            }
        )
        return True

    def action_close(self) -> bool:
        """Close the plan permanently."""
        self._assert_transition(constants.PLAN_STATE_CLOSED)
        for plan in self:
            if not plan.closure_reason:
                raise UserError(
                    self.env._(
                        "A closure reason is required before calibration plan "
                        "'%(plan)s' can be closed.",
                        plan=plan.name,
                    )
                )
        self.write({"state": constants.PLAN_STATE_CLOSED, "active": False})
        return True

    def action_open_records(self) -> dict:
        """Open the calibration records generated from this plan."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.action_ls_calibration_record"
        )
        action["domain"] = [("plan_id", "=", self.id)]
        action["context"] = {
            "default_plan_id": self.id,
            "default_instrument_id": self.instrument_id.id,
            "default_company_id": self.company_id.id,
        }
        return action

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def unlink(self) -> bool:
        """Forbid deletion of plans that already produced calibration records."""
        for plan in self:
            if plan.record_ids:
                raise UserError(
                    self.env._(
                        "Calibration plan '%(plan)s' has generated "
                        "%(count)s record(s) and cannot be deleted. "
                        "Close it instead.",
                        plan=plan.name,
                        count=len(plan.record_ids),
                    )
                )
        return super().unlink()
