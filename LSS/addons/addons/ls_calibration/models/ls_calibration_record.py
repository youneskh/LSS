# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration record of the Life Sciences calibration module.

A calibration record is the evidence of one calibration event. It carries the
as-found and as-left readings, the reference standards used, the disposition
of an out-of-tolerance situation and the review and approval signatures.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

TOLERANCE_STATUS_SELECTION = [
    ("not_assessed", "Not Assessed"),
    ("in_tolerance", "In Tolerance"),
    ("out_of_tolerance", "Out of Tolerance"),
]

RESULT_SELECTION = [
    ("pass", "Pass"),
    ("pass_adjusted", "Pass After Adjustment"),
    ("fail", "Fail"),
]

LOCKED_STATES = ("approved", "cancelled")
EDITABLE_STATES = ("draft", "in_progress")


class LsCalibrationRecord(models.Model):
    """Evidence of one calibration event of one instrument."""

    _name = "ls.calibration.record"
    _description = "Calibration Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "calibration_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Record Reference",
        required=True,
        copy=False,
        default="/",
        tracking=True,
    )
    instrument_id = fields.Many2one(
        comodel_name="ls.calibration.instrument",
        required=True,
        index=True,
        ondelete="restrict",
        check_company=True,
        tracking=True,
    )
    plan_id = fields.Many2one(
        comodel_name="ls.calibration.plan",
        string="Calibration Plan",
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
    calibration_type = fields.Selection(
        selection=[
            ("periodic", "Periodic"),
            ("initial", "Initial Qualification"),
            ("after_repair", "After Repair"),
            ("after_relocation", "After Relocation"),
            ("verification", "Intermediate Verification"),
            ("unscheduled", "Unscheduled"),
        ],
        required=True,
        default="periodic",
        tracking=True,
    )
    scheduled_date = fields.Date(
        help="Date on which the calibration was planned to be performed.",
    )
    calibration_date = fields.Datetime(tracking=True,
                                       help="Date and time at which the calibration was actually performed.",)
    performed_by_id = fields.Many2one(comodel_name="res.users", tracking=True,
                                      help="User who performed the calibration. This user cannot approve "
                                      "the same record.",)
    performed_externally = fields.Boolean(
        string="Externally Calibrated",
    )
    provider_id = fields.Many2one(
        comodel_name="res.partner",
        string="Calibration Service Provider",
    )
    standard_ids = fields.Many2many(
        comodel_name="ls.calibration.instrument",
        relation="ls_calibration_record_standard_rel",
        column1="record_id",
        column2="standard_id",
        string="Reference Standards",
        check_company=True,
        help="Instruments of the register used as reference standards for "
        "this calibration. A standard whose own calibration is overdue "
        "cannot be used.",
    )
    external_standard_reference = fields.Char(help="Identification and certificate number of a reference standard "
                                              "that is not managed in the instrument register.",)
    ambient_temperature = fields.Float(digits=(16, 2),
                                       )
    ambient_humidity = fields.Float(
        string="Relative Humidity",
        digits=(16, 2),
    )
    line_ids = fields.One2many(
        comodel_name="ls.calibration.record.line",
        inverse_name="record_id",
        string="Test Points",
        copy=True,
    )
    line_count = fields.Integer(compute="_compute_line_count", store=True)
    as_found_status = fields.Selection(
        selection=TOLERANCE_STATUS_SELECTION,
        compute="_compute_tolerance_status",
        store=True,
        tracking=True,
    )
    as_left_status = fields.Selection(
        selection=TOLERANCE_STATUS_SELECTION,
        compute="_compute_tolerance_status",
        store=True,
        tracking=True,
    )
    result = fields.Selection(
        selection=RESULT_SELECTION,
        compute="_compute_tolerance_status",
        store=True,
        tracking=True,
    )
    adjustment_performed = fields.Boolean(
        help="An adjustment of the instrument was performed between the "
        "as-found and the as-left readings.",
    )
    oot_impact_assessment = fields.Text(
        string="Out-of-Tolerance Impact Assessment",
        help="Assessment of the impact of the out-of-tolerance situation on "
        "the products, batches and decisions taken with this instrument "
        "since the previous calibration.",
    )
    oot_action_reference = fields.Char(
        string="Out-of-Tolerance Action Reference",
        help="Identification of the deviation, non-conformance or corrective "
        "action opened in the quality system for this out-of-tolerance "
        "situation.",
    )
    conclusion = fields.Text()
    next_due_date = fields.Date(
        compute="_compute_next_due_date",
        store=True,
        help="Due date of the next calibration derived from the calibration "
        "date and from the interval of the calibration plan.",
    )
    certificate_ids = fields.One2many(
        comodel_name="ls.calibration.certificate",
        inverse_name="record_id",
        string="Certificates",
    )
    certificate_count = fields.Integer(compute="_compute_certificate_count")
    submitted_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,
                                      tracking=True,
                                      help="User who submitted the completed results for approval.",)
    submission_date = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False)
    rejection_reason = fields.Text(readonly=True, copy=False)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("to_review", "To Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        tracking=True,
        copy=False,
    )

    _name_company_unique = models.Constraint(
        "UNIQUE(name, company_id)",
        "The calibration record reference must be unique per company.",
    )

    @api.depends("name", "instrument_id.display_name")
    def _compute_display_name(self):
        """Show the record reference together with the instrument."""
        for record in self:
            instrument_name = record.instrument_id.display_name or ""
            record.display_name = f"{record.name or ''} - {instrument_name}"

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Count the test points of the record."""
        for record in self:
            record.line_count = len(record.line_ids)

    @api.depends("certificate_ids")
    def _compute_certificate_count(self):
        """Count the certificates attached to the record."""
        for record in self:
            record.certificate_count = len(record.certificate_ids)

    @api.depends(
        "line_ids",
        "line_ids.as_found_in_tolerance",
        "line_ids.as_left_in_tolerance",
    )
    def _compute_tolerance_status(self):
        """Derive the as-found status, as-left status and overall result."""
        for record in self:
            lines = record.line_ids
            if not lines:
                record.as_found_status = "not_assessed"
                record.as_left_status = "not_assessed"
                record.result = False
                continue
            record.as_found_status = (
                "in_tolerance"
                if all(lines.mapped("as_found_in_tolerance"))
                else "out_of_tolerance"
            )
            record.as_left_status = (
                "in_tolerance"
                if all(lines.mapped("as_left_in_tolerance"))
                else "out_of_tolerance"
            )
            if record.as_left_status == "out_of_tolerance":
                record.result = "fail"
            elif record.as_found_status == "out_of_tolerance":
                record.result = "pass_adjusted"
            else:
                record.result = "pass"

    @api.depends(
        "calibration_date",
        "plan_id.interval_number",
        "plan_id.interval_uom",
    )
    def _compute_next_due_date(self):
        """Derive the next due date from the plan interval."""
        for record in self:
            if record.plan_id and record.calibration_date:
                record.next_due_date = record.plan_id._add_interval(
                    record.calibration_date.date()
                )
            else:
                record.next_due_date = False

    @api.constrains("plan_id", "instrument_id")
    def _check_plan_instrument(self):
        """Ensure the plan belongs to the instrument of the record."""
        for record in self:
            if (
                record.plan_id
                and record.plan_id.instrument_id != record.instrument_id
            ):
                raise ValidationError(
                    self.env._(
                        "The calibration plan %(plan)s does not belong to the "
                        "instrument %(instrument)s.",
                        plan=record.plan_id.display_name,
                        instrument=record.instrument_id.display_name,
                    )
                )

    @api.constrains("standard_ids", "instrument_id")
    def _check_standard_not_self(self):
        """Prevent an instrument from being its own reference standard."""
        for record in self:
            if record.instrument_id in record.standard_ids:
                raise ValidationError(
                    self.env._(
                        "Instrument %s cannot be used as a reference standard "
                        "for its own calibration.",
                        record.instrument_id.display_name,
                    )
                )

    @api.onchange("instrument_id")
    def _onchange_instrument_id(self):
        """Reset the plan when it does not belong to the new instrument."""
        if self.plan_id and self.plan_id.instrument_id != self.instrument_id:
            self.plan_id = False

    @api.onchange("plan_id")
    def _onchange_plan_id(self):
        """Load the test points of the selected plan."""
        if not self.plan_id:
            return
        self.instrument_id = self.plan_id.instrument_id
        self.performed_externally = self.plan_id.performed_externally
        self.provider_id = self.plan_id.provider_id
        if not self.line_ids:
            self.line_ids = [
                fields.Command.create(point._prepare_record_line_values())
                for point in self.plan_id.point_ids
            ]

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the record reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.calibration.record"
                ) or "/"
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset the reference, the state and the signatures of a copy."""
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals["name"] = "/"
            vals["state"] = "draft"
        return vals_list

    @api.model
    def _get_lock_exempt_fields(self):
        """Return the fields that stay writable on a locked record.

        Locked records are the legal evidence of a completed calibration.
        Only the technical fields listed here, which do not carry calibration
        data, remain writable so that the discussion thread, the activities,
        the attached certificates and the stored computed values keep working.

        :return: a set of field names.
        """
        return {
            "activity_ids",
            "as_found_status",
            "as_left_status",
            "certificate_count",
            "certificate_ids",
            "line_count",
            "message_follower_ids",
            "message_ids",
            "message_main_attachment_id",
            "message_partner_ids",
            "next_due_date",
            "result",
        }

    def write(self, vals):
        """Refuse any modification of the data of a locked record."""
        locked = self.filtered(lambda record: record.state in LOCKED_STATES)
        if locked and set(vals) - self._get_lock_exempt_fields():
            raise UserError(
                self.env._(
                    "Calibration record %s is approved or cancelled and "
                    "cannot be modified.",
                    locked[0].display_name,
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_calibration_record(self):
        """Refuse the deletion of a record that left the draft state."""
        not_draft = self.filtered(lambda record: record.state != "draft")
        if not_draft:
            raise UserError(
                self.env._(
                    "Calibration record %s is not in the draft state and "
                    "cannot be deleted. Cancel it instead.",
                    not_draft[0].display_name,
                )
            )

    def _check_state(self, expected_states, action_label):
        """Raise a user error when a record is not in an expected state.

        :param expected_states: tuple of accepted technical state values.
        :param action_label: translated label of the requested action.
        """
        for record in self:
            if record.state not in expected_states:
                raise UserError(
                    self.env._(
                        "Action %(action)s is not allowed on calibration "
                        "record %(record)s in state %(state)s.",
                        action=action_label,
                        record=record.display_name,
                        state=record.state,
                    )
                )

    def _check_ready_for_review(self):
        """Verify that the record carries all the mandatory evidence."""
        for record in self:
            if not record.calibration_date:
                raise UserError(
                    self.env._(
                        "The calibration date of record %s is required "
                        "before review.",
                        record.display_name,
                    )
                )
            if not record.performed_by_id:
                raise UserError(
                    self.env._(
                        "The user who performed the calibration of record %s "
                        "is required before review.",
                        record.display_name,
                    )
                )
            if not record.line_ids:
                raise UserError(
                    self.env._(
                        "Calibration record %s does not contain any test "
                        "point.",
                        record.display_name,
                    )
                )
            if not record.standard_ids and not record.external_standard_reference:
                raise UserError(
                    self.env._(
                        "At least one reference standard or one external "
                        "standard reference is required on calibration "
                        "record %s.",
                        record.display_name,
                    )
                )
            if (
                record.as_found_status == "out_of_tolerance"
                and not record.oot_impact_assessment
            ):
                raise UserError(
                    self.env._(
                        "The as-found readings of calibration record %s are "
                        "out of tolerance. An impact assessment is required.",
                        record.display_name,
                    )
                )
            record._check_standards_validity()

    def _check_standards_validity(self):
        """Refuse reference standards whose own calibration is overdue."""
        self.ensure_one()
        reference_date = (
            self.calibration_date.date()
            if self.calibration_date
            else fields.Date.context_today(self)
        )
        for standard in self.standard_ids:
            status = standard._get_calibration_status(reference_date)
            if status == "overdue":
                raise UserError(
                    self.env._(
                        "Reference standard %s is overdue for calibration and "
                        "cannot be used to justify a calibration.",
                        standard.display_name,
                    )
                )

    def action_start(self):
        """Move the record from draft to in progress."""
        self._check_state(("draft",), self.env._("Start"))
        self.write({"state": "in_progress"})
        return True

    def action_submit_review(self):
        """Submit the completed record to the reviewer."""
        self._check_state(("in_progress",), self.env._("Submit to review"))
        self._check_ready_for_review()
        self.write(
            {
                "state": "to_review",
                "submitted_by_id": self.env.user.id,
                "submission_date": fields.Datetime.now(),
            }
        )
        for record in self:
            record.message_post(
                body=self.env._(
                    "Calibration results submitted for approval by %s.",
                    self.env.user.name,
                )
            )
        return True

    def action_approve(self):
        """Approve the record and lock it definitively."""
        self._check_state(("to_review",), self.env._("Approve"))
        if not self.env.su and not self.env.user.has_group(
            "ls_calibration.group_ls_calibration_manager"
        ):
            raise UserError(
                self.env._(
                    "Only a Calibration Manager can approve a calibration "
                    "record."
                )
            )
        for record in self:
            if record.performed_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Calibration record %s cannot be approved by the user "
                        "who performed the calibration.",
                        record.display_name,
                    )
                )
            record._check_ready_for_review()
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        for record in self:
            record.message_post(
                body=self.env._(
                    "Calibration record approved by %(user)s on %(date)s. "
                    "Meaning of the signature: approval of the calibration "
                    "results and release of the instrument.",
                    user=self.env.user.name,
                    date=fields.Datetime.to_string(record.approval_date),
                )
            )
        return True

    def action_reject(self, reason=None):
        """Reject the record and return it to the performer.

        :param reason: justification of the rejection.
        """
        self._check_state(("to_review",), self.env._("Reject"))
        if not reason:
            raise UserError(
                self.env._("A reason is required to reject a calibration "
                           "record.")
            )
        self.write({"state": "rejected", "rejection_reason": reason})
        for record in self:
            record.message_post(
                body=self.env._(
                    "Calibration record rejected by %(user)s. Reason: "
                    "%(reason)s",
                    user=self.env.user.name,
                    reason=reason,
                )
            )
        return True

    def action_cancel(self):
        """Cancel a record that will never be completed."""
        self._check_state(
            ("draft", "in_progress", "to_review", "rejected"),
            self.env._("Cancel"),
        )
        self.write({"state": "cancelled"})
        return True

    def action_reset_to_draft(self):
        """Return a rejected record to the draft state."""
        self._check_state(("rejected",), self.env._("Reset to draft"))
        self.write(
            {
                "state": "draft",
                "submitted_by_id": False,
                "submission_date": False,
            }
        )
        return True

    def action_open_reject_wizard(self):
        """Open the wizard collecting the rejection reason."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_record_reject_action"
        )
        action["context"] = {"default_record_id": self.id}
        return action

    def action_view_certificates(self):
        """Open the certificates issued for this record."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_certificate_action"
        )
        action["domain"] = [("record_id", "=", self.id)]
        action["context"] = {
            "default_record_id": self.id,
            "default_instrument_id": self.instrument_id.id,
        }
        return action
