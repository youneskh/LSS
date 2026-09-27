# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Instrument register of the Life Sciences calibration module.

The instrument is the master record of every measuring, monitoring or test
device whose measurement result is used to accept or reject a product, a
process or an environmental condition.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

CALIBRATION_STATUS_SELECTION = [
    ("not_applicable", "Not Applicable"),
    ("not_scheduled", "Not Scheduled"),
    ("valid", "Valid"),
    ("due_soon", "Due Soon"),
    ("overdue", "Overdue"),
]

INACTIVE_INSTRUMENT_STATES = ("out_of_service", "retired")


class LsCalibrationInstrument(models.Model):
    """Master record of a measuring, monitoring or test instrument."""

    _name = "ls.calibration.instrument"
    _description = "Calibration Instrument"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, id"
    _check_company_auto = True

    name = fields.Char(
        string="Instrument Name",
        required=True,
        index=True,
        tracking=True,
    )
    code = fields.Char(
        string="Instrument Reference",
        required=True,
        copy=False,
        default="/",
        tracking=True,
        help="Unique identification of the instrument inside the company. "
        "Generated from the sequence 'ls.calibration.instrument' when left "
        "to the default value '/'.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment",
        string="Related Equipment",
        ondelete="set null",
        check_company=True,
        help="Equipment record of the Maintenance application this instrument "
        "belongs to or is installed on.",
    )
    category_id = fields.Many2one(
        comodel_name="maintenance.equipment.category",
        string="Instrument Category",
        ondelete="restrict",
    )
    manufacturer = fields.Char()
    model_reference = fields.Char(string="Manufacturer Model")
    serial_number = fields.Char(tracking=True)
    location = fields.Char(
        string="Physical Location",
        help="Room, area or production line where the instrument is installed.",
    )
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        tracking=True,
        default=lambda self: self.env.user,
        help="User who receives the calibration due and overdue activities.",
    )
    criticality = fields.Selection(
        selection=[
            ("critical", "Critical"),
            ("major", "Major"),
            ("minor", "Minor"),
        ],
        required=True,
        default="major",
        tracking=True,
        help="Criticality classification defined by the organisation's "
        "quality risk management procedure.",
    )
    gxp_impact = fields.Selection(
        selection=[
            ("direct", "Direct Impact"),
            ("indirect", "Indirect Impact"),
            ("none", "No Impact"),
        ],
        required=True,
        default="direct",
        tracking=True,
        help="Impact of the instrument on product quality, patient safety or "
        "data integrity, as classified by the organisation.",
    )
    range_min = fields.Float(
        string="Range Minimum",
        digits=(16, 6),
    )
    range_max = fields.Float(
        string="Range Maximum",
        digits=(16, 6),
    )
    unit = fields.Char(
        string="Unit of Measurement",
        help="Metrological unit of the measured quantity, for example "
        "degC, kPa, mg, pH.",
    )
    tolerance_type = fields.Selection(
        selection=[
            ("absolute", "Absolute"),
            ("relative", "Percentage of Reading"),
        ],
        required=True,
        default="absolute",
        help="Default tolerance type proposed on the calibration plan points "
        "created for this instrument.",
    )
    tolerance_value = fields.Float(
        string="Maximum Permissible Error",
        digits=(16, 6),
        help="Default maximum permissible error proposed on the calibration "
        "plan points created for this instrument.",
    )
    alert_lead_days = fields.Integer(
        string="Alert Lead Time (Days)",
        required=True,
        default=30,
        help="Number of days before the next due date from which the "
        "instrument is reported as 'Due Soon'.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_service", "In Service"),
            ("out_of_service", "Out of Service"),
            ("retired", "Retired"),
        ],
        required=True,
        default="draft",
        tracking=True,
        copy=False,
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
    plan_count = fields.Integer(compute="_compute_counts")
    record_count = fields.Integer(compute="_compute_counts")
    certificate_count = fields.Integer(compute="_compute_counts")
    last_calibration_date = fields.Date(
        compute="_compute_calibration_dates",
        store=True,
        help="Date of the most recent approved calibration record.",
    )
    next_calibration_date = fields.Date(
        compute="_compute_calibration_dates",
        store=True,
        index=True,
        help="Earliest due date of the active calibration plans.",
    )
    calibration_status = fields.Selection(
        selection=CALIBRATION_STATUS_SELECTION,
        compute="_compute_calibration_status",
        search="_search_calibration_status",
        help="Calculated at read time from the next due date, the alert lead "
        "time and the current date.",
    )
    note = fields.Html(string="Internal Notes", sanitize=True)

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The instrument reference must be unique per company.",
    )
    _range_consistent = models.Constraint(
        "CHECK(range_max >= range_min)",
        "The maximum of the measuring range must be greater than or equal to "
        "the minimum of the measuring range.",
    )
    _alert_lead_days_positive = models.Constraint(
        "CHECK(alert_lead_days >= 0)",
        "The alert lead time must be greater than or equal to zero days.",
    )
    _tolerance_value_positive = models.Constraint(
        "CHECK(tolerance_value >= 0)",
        "The maximum permissible error must be greater than or equal to zero.",
    )

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Prefix the instrument name with its unique reference."""
        for instrument in self:
            name = instrument.name or ""
            if instrument.code and instrument.code != "/":
                instrument.display_name = f"[{instrument.code}] {name}"
            else:
                instrument.display_name = name

    @api.depends("plan_ids", "record_ids", "certificate_ids")
    def _compute_counts(self):
        """Count the related plans, records and certificates."""
        for instrument in self:
            instrument.plan_count = len(instrument.plan_ids)
            instrument.record_count = len(instrument.record_ids)
            instrument.certificate_count = len(instrument.certificate_ids)

    @api.depends(
        "record_ids.state",
        "record_ids.calibration_date",
        "plan_ids.state",
        "plan_ids.next_due_date",
    )
    def _compute_calibration_dates(self):
        """Derive the last calibration date and the next due date."""
        for instrument in self:
            approved = instrument.record_ids.filtered(
                lambda record: record.state == "approved"
                and record.calibration_date
            )
            last_datetime = max(approved.mapped("calibration_date"), default=False)
            instrument.last_calibration_date = (
                last_datetime.date() if last_datetime else False
            )
            due_dates = [
                plan.next_due_date
                for plan in instrument.plan_ids
                if plan.state == "active" and plan.next_due_date
            ]
            instrument.next_calibration_date = min(due_dates) if due_dates else False

    @api.depends("state", "next_calibration_date", "alert_lead_days")
    def _compute_calibration_status(self):
        """Classify the instrument against its next due date."""
        today = fields.Date.context_today(self)
        for instrument in self:
            instrument.calibration_status = instrument._get_calibration_status(today)

    def _get_calibration_status(self, today):
        """Return the calibration status of a single instrument at ``today``.

        :param today: date used as the reference for the comparison.
        :return: one of the technical values of ``CALIBRATION_STATUS_SELECTION``.
        """
        self.ensure_one()
        if self.state in INACTIVE_INSTRUMENT_STATES:
            return "not_applicable"
        if not self.next_calibration_date:
            return "not_scheduled"
        if self.next_calibration_date < today:
            return "overdue"
        if (self.next_calibration_date - today).days <= self.alert_lead_days:
            return "due_soon"
        return "valid"

    @api.model
    def _search_calibration_status(self, operator, value):
        """Return the domain matching a calibration status.

        The status depends on the current date and on the per instrument alert
        lead time, therefore it cannot be expressed as a plain SQL domain. The
        candidate instruments are read and filtered in Python. The number of
        instruments of a manufacturing site is small enough for this approach;
        the retrieved set is restricted by the access rights of the user.
        """
        supported_operators = ("=", "!=", "in", "not in")
        if operator not in supported_operators:
            raise UserError(
                self.env._(
                    "The operator %s is not supported on the calibration "
                    "status field.",
                    operator,
                )
            )
        if operator in ("=", "!="):
            values = [value]
        else:
            values = list(value)
        negate = operator in ("!=", "not in")
        today = fields.Date.context_today(self)
        candidates = self.with_context(active_test=False).search([])
        matched = candidates.filtered(
            lambda instrument: (
                instrument._get_calibration_status(today) in values
            )
            != negate
        )
        return [("id", "in", matched.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the instrument reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("code") or vals["code"] == "/":
                vals["code"] = self.env["ir.sequence"].next_by_code(
                    "ls.calibration.instrument"
                ) or "/"
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset the reference of a duplicated instrument."""
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals["code"] = "/"
        return vals_list

    def action_set_in_service(self):
        """Release the instrument for production use."""
        for instrument in self:
            if instrument.state not in ("draft", "out_of_service"):
                raise UserError(
                    self.env._(
                        "Only draft or out of service instruments can be set "
                        "in service. Instrument %s is in state %s.",
                        instrument.display_name,
                        instrument.state,
                    )
                )
        self.write({"state": "in_service"})
        return True

    def action_set_out_of_service(self):
        """Withdraw the instrument from production use."""
        for instrument in self:
            if instrument.state != "in_service":
                raise UserError(
                    self.env._(
                        "Only instruments in service can be set out of "
                        "service. Instrument %s is in state %s.",
                        instrument.display_name,
                        instrument.state,
                    )
                )
        self.write({"state": "out_of_service"})
        return True

    def action_retire(self):
        """Retire the instrument definitively."""
        for instrument in self:
            if instrument.state == "retired":
                raise UserError(
                    self.env._(
                        "Instrument %s is already retired.",
                        instrument.display_name,
                    )
                )
        self.write({"state": "retired"})
        self.plan_ids.filtered(lambda plan: plan.state == "active").write(
            {"state": "obsolete"}
        )
        return True

    def action_reset_to_draft(self):
        """Return a retired instrument to the draft state."""
        for instrument in self:
            if instrument.state != "retired":
                raise UserError(
                    self.env._(
                        "Only retired instruments can be reset to draft. "
                        "Instrument %s is in state %s.",
                        instrument.display_name,
                        instrument.state,
                    )
                )
        self.write({"state": "draft"})
        return True

    def action_view_plans(self):
        """Open the calibration plans of the instrument."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_plan_action"
        )
        action["domain"] = [("instrument_id", "=", self.id)]
        action["context"] = {
            "default_instrument_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action

    def action_view_records(self):
        """Open the calibration records of the instrument."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_record_action"
        )
        action["domain"] = [("instrument_id", "=", self.id)]
        action["context"] = {
            "default_instrument_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action

    def action_view_certificates(self):
        """Open the calibration certificates of the instrument."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_certificate_action"
        )
        action["domain"] = [("instrument_id", "=", self.id)]
        action["context"] = {
            "default_instrument_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action

    @api.model
    def _cron_notify_due_calibrations(self):
        """Schedule an activity for every instrument due soon or overdue.

        Executed by the scheduled action
        ``ls_calibration.ls_calibration_cron_notify_due``.

        :return: the number of activities that have been scheduled.
        """
        today = fields.Date.context_today(self)
        instruments = self.search(
            [
                ("state", "=", "in_service"),
                ("next_calibration_date", "!=", False),
            ]
        )
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        scheduled = 0
        for instrument in instruments:
            status = instrument._get_calibration_status(today)
            if status not in ("due_soon", "overdue"):
                continue
            if status == "overdue":
                summary = self.env._("Calibration overdue")
            else:
                summary = self.env._("Calibration due soon")
            already_open = instrument.activity_ids.filtered(
                lambda activity, summary=summary: activity.summary == summary
            )
            if already_open:
                continue
            note = self.env._(
                "Instrument %(instrument)s is due for calibration on "
                "%(date)s.",
                instrument=instrument.display_name,
                date=instrument.next_calibration_date,
            )
            if activity_type:
                instrument.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=instrument.next_calibration_date,
                    summary=summary,
                    note=note,
                    user_id=(
                        instrument.responsible_user_id.id or self.env.user.id
                    ),
                )
            else:
                instrument.message_post(body=note)
            scheduled += 1
        return scheduled
