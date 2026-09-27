# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Certifications proving that an employee completed a training course."""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

DEFAULT_EXPIRY_WARNING_DAYS = 30
EXPIRY_WARNING_PARAMETER = "ls_training.expiry_warning_days"


class LsTrainingCertification(models.Model):
    """Evidence that an employee holds a valid qualification for a course.

    Certifications are never overwritten on renewal: a new record is issued
    and the previous one is left to expire. The complete history therefore
    remains reconstructable, which is the behaviour expected of a GxP
    training record.
    """

    _name = "ls.training.certification"
    _description = "Training Certification"
    _inherit = ["mail.thread"]
    _order = "date_granted desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        index=True,
    )
    employee_id = fields.Many2one(comodel_name="hr.employee", required=True,
                                  ondelete="restrict",
                                  index=True,
                                  tracking=True,)
    course_id = fields.Many2one(comodel_name="ls.training.course", required=True,
                                ondelete="restrict",
                                index=True,
                                tracking=True,)
    session_id = fields.Many2one(
        comodel_name="ls.training.session",
        string="Source Session",
        ondelete="restrict",
        index=True,
        help="Session that issued this certification. Empty when the "
             "certification records externally delivered training.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    course_version = fields.Char(required=True,
                                 help="Version of the course material at the time of certification. "
                                 "Frozen on creation so that later course revisions do not "
                                 "alter historical evidence.",)
    date_granted = fields.Date(
        string="Granted On",
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
    )
    date_expiry = fields.Date(
        string="Expires On",
        compute="_compute_date_expiry",
        store=True,
        readonly=False,
        index=True,
        tracking=True,
        help="Computed from the course validity period. It can be "
             "overridden for externally issued certifications.",
    )
    score = fields.Float(
        string="Assessment Score (%)",
        default=0.0,
    )
    revoked = fields.Boolean(default=False,
                             copy=False,
                             tracking=True,)
    revocation_reason = fields.Text(copy=False,)
    state = fields.Selection(
        selection=[
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        string="Status",
        compute="_compute_state",
        store=True,
        index=True,
        default="valid",
    )
    days_to_expiry = fields.Integer(compute="_compute_days_to_expiry",)
    competency_ids = fields.Many2many(
        comodel_name="ls.training.competency",
        relation="ls_training_certification_competency_rel",
        column1="certification_id",
        column2="competency_id",
        string="Competencies Granted",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The certification reference must be unique per company.",
    )

    @api.model
    def _get_expiry_warning_days(self):
        """Return the configured 'expiring soon' window, in days.

        The value is read from the ``ls_training.expiry_warning_days``
        system parameter. Any non-numeric or negative value falls back to
        the module default so that a mistyped parameter cannot silently
        disable expiry warnings.
        """
        raw_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(EXPIRY_WARNING_PARAMETER)
        )
        try:
            days = int(raw_value)
        except (TypeError, ValueError):
            return DEFAULT_EXPIRY_WARNING_DAYS
        if days < 0:
            return DEFAULT_EXPIRY_WARNING_DAYS
        return days

    @api.depends("date_granted", "course_id.validity_months")
    def _compute_date_expiry(self):
        """Derive the expiry date from the course validity period."""
        for record in self:
            validity = record.course_id.validity_months
            if validity and record.date_granted:
                record.date_expiry = record.date_granted + relativedelta(
                    months=validity
                )
            else:
                record.date_expiry = False

    @api.depends("date_expiry", "revoked")
    def _compute_state(self):
        """Derive the certification status from its expiry date.

        The stored value is refreshed daily by the
        ``_cron_refresh_certification_state`` scheduled action, because the
        result depends on the current date and not only on stored fields.
        """
        today = fields.Date.context_today(self)
        warning_days = self._get_expiry_warning_days()
        for record in self:
            if record.revoked:
                record.state = "revoked"
            elif not record.date_expiry:
                record.state = "valid"
            elif record.date_expiry < today:
                record.state = "expired"
            elif (record.date_expiry - today).days <= warning_days:
                record.state = "expiring"
            else:
                record.state = "valid"

    @api.depends("date_expiry")
    def _compute_days_to_expiry(self):
        """Report the remaining validity in days."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_expiry:
                record.days_to_expiry = (record.date_expiry - today).days
            else:
                record.days_to_expiry = 0

    @api.depends("name", "employee_id", "course_id")
    def _compute_display_name(self):
        """Display the reference with employee and course."""
        for record in self:
            record.display_name = "%s - %s / %s" % (
                record.name,
                record.employee_id.name or "",
                record.course_id.name or "",
            )

    @api.constrains("date_granted", "date_expiry")
    def _check_dates(self):
        """A certification cannot expire before it was granted."""
        for record in self:
            if record.date_expiry and record.date_expiry < (
                record.date_granted
            ):
                raise ValidationError(
                    _("Certification '%s' expires before it was granted.")
                    % record.display_name
                )

    @api.constrains("score")
    def _check_score(self):
        """The score is a percentage between 0 and 100."""
        for record in self:
            if not 0.0 <= record.score <= 100.0:
                raise ValidationError(
                    _("The score of certification '%s' must be between 0 "
                      "and 100.")
                    % record.display_name
                )

    @api.constrains("revoked", "revocation_reason")
    def _check_revocation_reason(self):
        """Revocation must always be justified in writing."""
        for record in self:
            if record.revoked and not record.revocation_reason:
                raise ValidationError(
                    _("Certification '%s' cannot be revoked without a "
                      "documented reason.")
                    % record.display_name
                )

    @api.model
    def _prepare_from_attendance(self, attendance):
        """Build the certification values issued from an attendance record.

        :param attendance: a single ``ls.training.attendance`` record whose
            result is ``passed``.
        :return: a dictionary of values suitable for ``create``.
        """
        course = attendance.course_id
        return {
            "employee_id": attendance.employee_id.id,
            "course_id": course.id,
            "session_id": attendance.session_id.id,
            "company_id": attendance.company_id.id,
            "course_version": course.version,
            "date_granted": fields.Date.to_date(
                attendance.session_id.date_end
            ),
            "score": attendance.score,
            "competency_ids": [fields.Command.set(course.competency_ids.ids)],
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the reference and freeze the course version."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.training.certification")
                    or _("New")
                )
            if not vals.get("course_version") and vals.get("course_id"):
                course = self.env["ls.training.course"].browse(
                    vals["course_id"]
                )
                vals["course_version"] = course.version
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_training_certification(self):
        """Certifications are permanent evidence and are never deleted."""
        raise UserError(
            _("Training certifications are retained as quality evidence and "
              "cannot be deleted. Revoke the certification instead.")
        )

    def action_revoke(self):
        """Open the revocation wizard for the selected certifications."""
        self.ensure_one()
        if self.revoked:
            raise UserError(
                _("Certification '%s' is already revoked.")
                % self.display_name
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Revoke Certification"),
            "res_model": "ls.training.certification",
            "res_id": self.id,
            "view_mode": "form",
            "views": [
                (
                    self.env.ref(
                        "ls_training."
                        "ls_training_certification_revoke_form_view"
                    ).id,
                    "form",
                )
            ],
            "target": "new",
        }

    def action_confirm_revoke(self):
        """Apply the revocation entered in the revocation dialog."""
        for record in self:
            if not record.revocation_reason:
                raise UserError(
                    _("Enter the reason before revoking certification "
                      "'%s'.")
                    % record.display_name
                )
            record.write({"revoked": True})
        return {"type": "ir.actions.act_window_close"}

    def _ls_recompute_stored(self, method_name):
        """Recompute and save the stored fields computed by ``method_name``.

        Calling a compute method directly does not persist the values of
        stored computed fields; the recomputation is therefore scheduled and
        run through the ORM so that the new values are written.

        :param str method_name: name of the compute method.
        """
        names = [
            name
            for name, field in self._fields.items()
            if field.store and field.compute == method_name
        ]
        for name in names:
            self.env.add_to_compute(self._fields[name], self)
        self._recompute_recordset(names)

    @api.model
    def _cron_refresh_certification_state(self):
        """Recompute stored statuses so expiry transitions are picked up.

        Scheduled daily. Revoked certifications are excluded because their
        status is terminal and unaffected by the passage of time.
        """
        certifications = self.search([("revoked", "=", False)])
        certifications._ls_recompute_stored("_compute_state")
        return len(certifications)

    @api.model
    def _cron_send_expiry_reminders(self):
        """Email employees whose certification expires or has expired.

        Only certifications in the ``expiring`` or ``expired`` status and
        belonging to an employee with a work email are notified.
        :return: the number of reminder emails queued.
        """
        template = self.env.ref(
            "ls_training.ls_training_certification_expiry_mail_template",
            raise_if_not_found=False,
        )
        if not template:
            return 0
        certifications = self.search(
            [
                ("state", "in", ("expiring", "expired")),
                ("employee_id.work_email", "!=", False),
            ]
        )
        sent = 0
        for certification in certifications:
            template.send_mail(certification.id, force_send=False)
            sent += 1
        return sent
