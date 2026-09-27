# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration plan of the Life Sciences calibration module.

A calibration plan defines what is calibrated, how often, against which
acceptance criteria and by whom. It is the authoritative source of the
calibration interval and of the resulting due dates.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

INTERVAL_TO_RELATIVEDELTA = {
    "day": "days",
    "week": "weeks",
    "month": "months",
    "year": "years",
}

OPEN_RECORD_STATES = ("draft", "in_progress", "to_review")


class LsCalibrationPlan(models.Model):
    """Periodic calibration programme applied to one instrument."""

    _name = "ls.calibration.plan"
    _description = "Calibration Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "next_due_date, id"
    _check_company_auto = True

    name = fields.Char(
        string="Plan Reference",
        required=True,
        copy=False,
        default="/",
        tracking=True,
    )
    active = fields.Boolean(default=True)
    instrument_id = fields.Many2one(
        comodel_name="ls.calibration.instrument",
        required=True,
        index=True,
        ondelete="restrict",
        check_company=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="instrument_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    description = fields.Char(
        help="Short description of the scope of the plan, for example "
        "'Annual temperature calibration, 3 points'.",
    )
    procedure_reference = fields.Char(help="Identification of the approved written procedure that describes "
                                      "the calibration method, for example the SOP number.",)
    method_description = fields.Text(
        string="Method",
        help="Summary of the calibration method applied by this plan.",
    )
    interval_number = fields.Integer(
        string="Interval",
        required=True,
        default=12,
        tracking=True,
    )
    interval_uom = fields.Selection(
        selection=[
            ("day", "Days"),
            ("week", "Weeks"),
            ("month", "Months"),
            ("year", "Years"),
        ],
        string="Interval Unit",
        required=True,
        default="month",
        tracking=True,
    )
    start_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date of the first calibration planned by this plan. It is used "
        "as the next due date as long as no calibration record has been "
        "approved for this plan.",
    )
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    performed_externally = fields.Boolean(
        string="Externally Calibrated",
        help="The calibration is subcontracted to an external calibration "
        "service provider.",
    )
    provider_id = fields.Many2one(
        comodel_name="res.partner",
        string="Calibration Service Provider",
    )
    point_ids = fields.One2many(
        comodel_name="ls.calibration.plan.point",
        inverse_name="plan_id",
        string="Test Points",
        copy=True,
    )
    record_ids = fields.One2many(
        comodel_name="ls.calibration.record",
        inverse_name="plan_id",
        string="Calibration Records",
    )
    record_count = fields.Integer(compute="_compute_record_count")
    last_calibration_date = fields.Date(
        compute="_compute_schedule_dates",
        store=True,
        help="Date of the most recent approved calibration record of this "
        "plan.",
    )
    next_due_date = fields.Date(
        compute="_compute_schedule_dates",
        store=True,
        index=True,
        help="Date on which the next calibration of this plan is due.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("obsolete", "Obsolete"),
        ],
        required=True,
        default="draft",
        tracking=True,
        copy=False,
    )

    _name_company_unique = models.Constraint(
        "UNIQUE(name, company_id)",
        "The calibration plan reference must be unique per company.",
    )
    _interval_number_positive = models.Constraint(
        "CHECK(interval_number > 0)",
        "The calibration interval must be strictly greater than zero.",
    )

    @api.depends("name", "instrument_id.display_name")
    def _compute_display_name(self):
        """Show the plan reference together with the instrument."""
        for plan in self:
            instrument_name = plan.instrument_id.display_name or ""
            plan.display_name = f"{plan.name or ''} - {instrument_name}"

    @api.depends("record_ids")
    def _compute_record_count(self):
        """Count the calibration records generated by the plan."""
        for plan in self:
            plan.record_count = len(plan.record_ids)

    @api.depends(
        "record_ids.state",
        "record_ids.calibration_date",
        "interval_number",
        "interval_uom",
        "start_date",
        "state",
    )
    def _compute_schedule_dates(self):
        """Derive the last calibration date and the next due date."""
        for plan in self:
            approved = plan.record_ids.filtered(
                lambda record: record.state == "approved"
                and record.calibration_date
            )
            last_datetime = max(approved.mapped("calibration_date"), default=False)
            plan.last_calibration_date = (
                last_datetime.date() if last_datetime else False
            )
            if plan.state in ("suspended", "obsolete"):
                plan.next_due_date = False
            elif plan.last_calibration_date:
                plan.next_due_date = plan._add_interval(plan.last_calibration_date)
            else:
                plan.next_due_date = plan.start_date

    def _add_interval(self, date_from):
        """Return ``date_from`` shifted by the interval of the plan.

        :param date_from: date used as the origin of the computation.
        :return: the resulting :class:`datetime.date`.
        """
        self.ensure_one()
        key = INTERVAL_TO_RELATIVEDELTA[self.interval_uom]
        return date_from + relativedelta(**{key: self.interval_number})

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the plan reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.calibration.plan"
                ) or "/"
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset the reference and the state of a duplicated plan."""
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals["name"] = "/"
            vals["state"] = "draft"
        return vals_list

    def action_activate(self):
        """Release the plan so that calibrations are scheduled."""
        for plan in self:
            if plan.state not in ("draft", "suspended"):
                raise UserError(
                    self.env._(
                        "Only draft or suspended plans can be activated. "
                        "Plan %s is in state %s.",
                        plan.display_name,
                        plan.state,
                    )
                )
            if not plan.point_ids:
                raise UserError(
                    self.env._(
                        "Plan %s cannot be activated without at least one "
                        "test point.",
                        plan.display_name,
                    )
                )
        self.write({"state": "active"})
        return True

    def action_suspend(self):
        """Suspend the plan without deleting its history."""
        for plan in self:
            if plan.state != "active":
                raise UserError(
                    self.env._(
                        "Only active plans can be suspended. Plan %s is in "
                        "state %s.",
                        plan.display_name,
                        plan.state,
                    )
                )
        self.write({"state": "suspended"})
        return True

    def action_set_obsolete(self):
        """Close the plan definitively."""
        for plan in self:
            if plan.state == "obsolete":
                raise UserError(
                    self.env._(
                        "Plan %s is already obsolete.", plan.display_name
                    )
                )
        self.write({"state": "obsolete"})
        return True

    def action_reset_to_draft(self):
        """Return a suspended or obsolete plan to the draft state."""
        for plan in self:
            if plan.state not in ("suspended", "obsolete"):
                raise UserError(
                    self.env._(
                        "Only suspended or obsolete plans can be reset to "
                        "draft. Plan %s is in state %s.",
                        plan.display_name,
                        plan.state,
                    )
                )
        self.write({"state": "draft"})
        return True

    def _prepare_record_values(self):
        """Return the values of a calibration record created from the plan.

        :return: a dictionary accepted by ``ls.calibration.record.create``.
        """
        self.ensure_one()
        return {
            "instrument_id": self.instrument_id.id,
            "plan_id": self.id,
            "calibration_type": "periodic",
            "scheduled_date": self.next_due_date,
            "performed_externally": self.performed_externally,
            "provider_id": self.provider_id.id,
            "performed_by_id": self.responsible_user_id.id,
            "line_ids": [
                fields.Command.create(point._prepare_record_line_values())
                for point in self.point_ids
            ],
        }

    def _get_open_records(self):
        """Return the calibration records of the plan that are not closed."""
        self.ensure_one()
        return self.record_ids.filtered(
            lambda record: record.state in OPEN_RECORD_STATES
        )

    def action_create_calibration_record(self):
        """Create one calibration record for each selected plan.

        :return: an act_window action showing the created records.
        """
        records = self.env["ls.calibration.record"]
        for plan in self:
            if plan.state != "active":
                raise UserError(
                    self.env._(
                        "Calibration records can only be created from active "
                        "plans. Plan %s is in state %s.",
                        plan.display_name,
                        plan.state,
                    )
                )
            records |= records.create(plan._prepare_record_values())
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_record_action"
        )
        if len(records) == 1:
            action["view_mode"] = "form"
            action["views"] = [(False, "form")]
            action["res_id"] = records.id
        else:
            action["domain"] = [("id", "in", records.ids)]
        return action

    def action_view_records(self):
        """Open the calibration records generated by the plan."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_record_action"
        )
        action["domain"] = [("plan_id", "=", self.id)]
        action["context"] = {
            "default_plan_id": self.id,
            "default_instrument_id": self.instrument_id.id,
            "default_company_id": self.company_id.id,
        }
        return action

    @api.model
    def _cron_generate_calibration_records(self):
        """Create the calibration records of the plans due within the horizon.

        Executed by the scheduled action
        ``ls_calibration.ls_calibration_cron_generate_records``. A record is
        only created when the plan has no open record left.

        :return: the number of calibration records that have been created.
        """
        horizon_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_calibration.generation_horizon_days", "30")
        )
        limit_date = fields.Date.context_today(self) + relativedelta(
            days=horizon_days
        )
        plans = self.search(
            [
                ("state", "=", "active"),
                ("next_due_date", "!=", False),
                ("next_due_date", "<=", limit_date),
            ]
        )
        created = self.env["ls.calibration.record"]
        for plan in plans:
            if plan._get_open_records():
                continue
            created |= created.create(plan._prepare_record_values())
        return len(created)
