# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Registration and outcome of one employee in one training session."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsTrainingAttendance(models.Model):
    """Attendance evidence for a single employee in a single session.

    The outcome is derived from recorded facts (presence and, where the
    course requires it, the assessment score) rather than entered by hand.
    This keeps the result reproducible from the underlying evidence, which
    is what an auditor reconstructs during a data-integrity review.
    """

    _name = "ls.training.attendance"
    _description = "Training Attendance"
    _order = "session_id desc, employee_id"

    session_id = fields.Many2one(comodel_name="ls.training.session", required=True,
                                 ondelete="cascade",
                                 index=True,)
    employee_id = fields.Many2one(comodel_name="hr.employee", required=True,
                                  ondelete="restrict",
                                  index=True,)
    course_id = fields.Many2one(comodel_name="ls.training.course", related="session_id.course_id",
                                store=True,
                                index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="session_id.company_id",
                                 store=True,
                                 index=True,)
    session_state = fields.Selection(
        related="session_id.state",
        string="Session Status",
        store=True,
    )
    date_start = fields.Datetime(
        string="Session Start",
        related="session_id.date_start",
        store=True,
    )
    attended = fields.Boolean(default=False,
                              help="Tick once the employee's presence has been verified.",)
    score = fields.Float(
        string="Assessment Score (%)",
        default=0.0,
    )
    requires_assessment = fields.Boolean(
        related="course_id.requires_assessment",
        string="Assessment Required",
    )
    pass_score = fields.Float(
        related="course_id.pass_score",
        string="Pass Score (%)",
    )
    result = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        compute="_compute_result",
        store=True,
        index=True,
    )
    comment = fields.Text(
        string="Trainer Comment",
    )

    _session_employee_uniq = models.Constraint(
        "UNIQUE(session_id, employee_id)",
        "An employee can only be registered once per training session.",
    )

    @api.depends(
        "attended",
        "score",
        "course_id.requires_assessment",
        "course_id.pass_score",
    )
    def _compute_result(self):
        """Derive the outcome from attendance and assessment evidence.

        An absent employee is never marked as failed: absence is not a
        failed assessment, so the record stays pending until the employee
        is either registered on another session or marked as attended.
        """
        for record in self:
            if not record.attended:
                record.result = "pending"
            elif not record.course_id.requires_assessment:
                record.result = "passed"
            elif record.score >= record.course_id.pass_score:
                record.result = "passed"
            else:
                record.result = "failed"

    @api.depends("employee_id", "session_id")
    def _compute_display_name(self):
        """Display employee and session together."""
        for record in self:
            record.display_name = "%s - %s" % (
                record.employee_id.name or "",
                record.session_id.name or "",
            )

    @api.constrains("session_id")
    def _check_session_capacity(self):
        """Refuse a registration beyond the capacity of the session.

        The capacity rule of the session is declared on its one2many, which
        the ORM does not re-check when an attendance is created on its own;
        it is therefore re-evaluated from the attendance side.
        """
        self.session_id._check_capacity()

    @api.constrains("score")
    def _check_score(self):
        """The assessment score is a percentage between 0 and 100."""
        for record in self:
            if not 0.0 <= record.score <= 100.0:
                raise ValidationError(
                    _("The score of attendance '%s' must be between 0 and "
                      "100.")
                    % record.display_name
                )

    @api.constrains("employee_id", "company_id")
    def _check_employee_company(self):
        """The attendee must belong to the company running the session."""
        for record in self:
            employee_company = record.employee_id.company_id
            if employee_company and employee_company != record.company_id:
                raise ValidationError(
                    _("Employee '%s' belongs to company '%s' and cannot "
                      "attend a session of company '%s'.")
                    % (
                        record.employee_id.name,
                        employee_company.name,
                        record.company_id.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Forbid registering attendees on a closed or cancelled session."""
        records = super().create(vals_list)
        for record in records:
            if record.session_id.state in ("done", "cancelled"):
                raise UserError(
                    _("Session '%s' is %s; no attendee can be added.")
                    % (
                        record.session_id.display_name,
                        record.session_id.state,
                    )
                )
        return records

    def write(self, vals):
        """Freeze attendance evidence once the session has been closed."""
        if set(vals).intersection({"attended", "score", "employee_id"}):
            for record in self:
                if record.session_id.state == "done":
                    raise UserError(
                        _("Session '%s' is closed. Attendance evidence can "
                          "no longer be modified.")
                        % record.session_id.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_training_attendance(self):
        """Attendance of a closed session is retained as GxP evidence."""
        for record in self:
            if record.session_id.state == "done":
                raise UserError(
                    _("Attendance '%s' belongs to a closed session and "
                      "cannot be deleted.")
                    % record.display_name
                )

    def action_mark_attended(self):
        """Mark the selected attendees as present."""
        return self.write({"attended": True})

    def action_mark_absent(self):
        """Mark the selected attendees as absent."""
        return self.write({"attended": False, "score": 0.0})
