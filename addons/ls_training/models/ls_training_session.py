# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Delivery of a training course to a group of employees."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsTrainingSession(models.Model):
    """A scheduled delivery of an approved course.

    The session drives the operational workflow. Closing a session is the
    single point at which certifications are issued, which keeps the
    evidence chain (session -> attendance -> certification) unambiguous.
    """

    _name = "ls.training.session"
    _description = "Training Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        index=True,
    )
    course_id = fields.Many2one(comodel_name="ls.training.course", required=True,
                                ondelete="restrict",
                                index=True,
                                tracking=True,
                                domain="[('state', '=', 'approved')]",
                                )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In Progress"),
            ("done", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        tracking=True,
        index=True,
    )
    date_start = fields.Datetime(
        string="Start",
        required=True,
        tracking=True,
        default=fields.Datetime.now,
    )
    date_end = fields.Datetime(
        string="End",
        required=True,
        tracking=True,
    )
    trainer_employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Internal Trainer",
        ondelete="restrict",
        tracking=True,
    )
    trainer_external = fields.Char(
        string="External Trainer",
        tracking=True,
        help="Name and organisation of the trainer when the training is "
             "delivered by an external provider.",
    )
    location = fields.Char()
    capacity = fields.Integer(
        string="Maximum Attendees",
        default=0,
        help="Maximum number of attendees. Zero means no limit.",
    )
    attendance_ids = fields.One2many(
        comodel_name="ls.training.attendance",
        inverse_name="session_id",
        string="Attendees",
    )
    attendee_count = fields.Integer(
        string="Registered",
        compute="_compute_attendance_statistics",
        store=True,
    )
    passed_count = fields.Integer(
        string="Passed",
        compute="_compute_attendance_statistics",
        store=True,
    )
    failed_count = fields.Integer(
        string="Failed",
        compute="_compute_attendance_statistics",
        store=True,
    )
    certification_ids = fields.One2many(
        comodel_name="ls.training.certification",
        inverse_name="session_id",
        string="Issued Certifications",
    )
    certification_count = fields.Integer(compute="_compute_certification_count",)
    note = fields.Text(
        string="Session Notes",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The session reference must be unique per company.",
    )
    _capacity_positive = models.Constraint(
        "CHECK(capacity >= 0)",
        "The maximum number of attendees cannot be negative.",
    )

    @api.depends("attendance_ids", "attendance_ids.result")
    def _compute_attendance_statistics(self):
        """Aggregate registration and result counters for the session."""
        for record in self:
            attendances = record.attendance_ids
            record.attendee_count = len(attendances)
            record.passed_count = len(
                attendances.filtered(lambda line: line.result == "passed")
            )
            record.failed_count = len(
                attendances.filtered(lambda line: line.result == "failed")
            )

    @api.depends("certification_ids")
    def _compute_certification_count(self):
        """Count certifications issued by each session."""
        grouped = self.env["ls.training.certification"]._read_group(
            domain=[("session_id", "in", self.ids)],
            groupby=["session_id"],
            aggregates=["__count"],
        )
        mapped = {session.id: count for session, count in grouped}
        for record in self:
            record.certification_count = mapped.get(record.id, 0)

    @api.depends("name", "course_id")
    def _compute_display_name(self):
        """Display the session reference together with the course title."""
        for record in self:
            if record.course_id:
                record.display_name = "%s - %s" % (
                    record.name,
                    record.course_id.name,
                )
            else:
                record.display_name = record.name

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """The session must end after it starts."""
        for record in self:
            if record.date_end <= record.date_start:
                raise ValidationError(
                    _("Session '%s' must end after it starts.")
                    % record.display_name
                )

    @api.constrains("capacity", "attendance_ids")
    def _check_capacity(self):
        """Registrations may not exceed the declared capacity."""
        for record in self:
            if record.capacity and len(record.attendance_ids) > (
                record.capacity
            ):
                raise ValidationError(
                    _("Session '%s' accepts at most %d attendees; %d are "
                      "registered.")
                    % (
                        record.display_name,
                        record.capacity,
                        len(record.attendance_ids),
                    )
                )

    @api.constrains("trainer_employee_id", "trainer_external")
    def _check_trainer(self):
        """A session must name exactly one responsible trainer."""
        for record in self:
            if record.trainer_employee_id and record.trainer_external:
                raise ValidationError(
                    _("Session '%s' names both an internal and an external "
                      "trainer. Record only one of them.")
                    % record.display_name
                )

    @api.onchange("course_id")
    def _onchange_course_id(self):
        """Propose an end date derived from the course duration."""
        for record in self:
            if record.course_id and record.date_start:
                record.date_end = fields.Datetime.add(
                    record.date_start,
                    hours=record.course_id.duration_hours,
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the session reference from the sequence."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.training.session")
                    or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Protect closed sessions against retroactive modification."""
        protected_fields = {
            "course_id",
            "date_start",
            "date_end",
            "trainer_employee_id",
            "trainer_external",
        }
        if protected_fields.intersection(vals):
            for record in self:
                if record.state == "done":
                    raise UserError(
                        _("Session '%s' is closed. Its course, dates and "
                          "trainer can no longer be modified.")
                        % record.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_training_session(self):
        """Only draft or cancelled sessions may be deleted."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    _("Session '%s' is in state '%s' and cannot be deleted. "
                      "Cancel it instead.")
                    % (record.display_name, record.state)
                )

    def action_confirm(self):
        """Confirm a draft session that has at least one attendee."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft session can be confirmed. Session '%s' "
                      "is in state '%s'.")
                    % (record.display_name, record.state)
                )
            if not record.attendance_ids:
                raise UserError(
                    _("Session '%s' has no registered attendee.")
                    % record.display_name
                )
        return self.write({"state": "confirmed"})

    def action_start(self):
        """Mark a confirmed session as being delivered."""
        for record in self:
            if record.state != "confirmed":
                raise UserError(
                    _("Only a confirmed session can be started. Session "
                      "'%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
        return self.write({"state": "in_progress"})

    def action_close(self):
        """Close the session and issue certifications to passing attendees.

        Attendances still pending are rejected: every attendee must have a
        recorded outcome before the training evidence can be closed.
        """
        certification_model = self.env["ls.training.certification"]
        for record in self:
            if record.state != "in_progress":
                raise UserError(
                    _("Only a session in progress can be closed. Session "
                      "'%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
            pending = record.attendance_ids.filtered(
                lambda line: line.result == "pending"
            )
            if pending:
                raise UserError(
                    _("Session '%s' still has %d attendee(s) without a "
                      "recorded outcome.")
                    % (record.display_name, len(pending))
                )
            values_list = []
            for attendance in record.attendance_ids.filtered(
                lambda line: line.result == "passed"
            ):
                values_list.append(
                    certification_model._prepare_from_attendance(attendance)
                )
            if values_list:
                certification_model.create(values_list)
            record.write({"state": "done"})
        return True

    def action_cancel(self):
        """Cancel a session that has not been closed."""
        for record in self:
            if record.state == "done":
                raise UserError(
                    _("Session '%s' is closed and can no longer be "
                      "cancelled.")
                    % record.display_name
                )
        return self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        """Return a cancelled session to draft."""
        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    _("Only a cancelled session can be reset to draft. "
                      "Session '%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
        return self.write({"state": "draft"})

    def action_open_register_wizard(self):
        """Open the bulk registration wizard for this session."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_session_register_wizard_action"
        )
        action["context"] = {"default_session_id": self.id}
        return action

    def action_view_certifications(self):
        """Open the certifications issued by this session."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_certification_action"
        )
        action["domain"] = [("session_id", "=", self.id)]
        action["context"] = {"default_session_id": self.id}
        return action
