# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Recorded assessment of an employee against a defined competency."""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

LEVEL_ORDER = {
    "not_demonstrated": 0,
    "developing": 1,
    "proficient": 2,
    "expert": 3,
}


class LsTrainingCompetencyAssessment(models.Model):
    """Evidence that an assessor evaluated an employee's competency.

    Course attendance proves exposure to training material; a competency
    assessment proves the employee can apply it. The two are kept separate
    so that on-the-job qualification can be evidenced independently of
    classroom attendance.
    """

    _name = "ls.training.competency.assessment"
    _description = "Competency Assessment"
    _inherit = ["mail.thread"]
    _order = "date_assessment desc, id desc"

    employee_id = fields.Many2one(comodel_name="hr.employee", required=True,
                                  ondelete="restrict",
                                  index=True,
                                  tracking=True,)
    competency_id = fields.Many2one(comodel_name="ls.training.competency", required=True,
                                    ondelete="restrict",
                                    index=True,
                                    tracking=True,)
    assessor_id = fields.Many2one(comodel_name="hr.employee", required=True,
                                  ondelete="restrict",
                                  tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    date_assessment = fields.Date(
        string="Assessment Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
    )
    date_next = fields.Date(
        string="Next Assessment",
        compute="_compute_date_next",
        store=True,
        readonly=False,
        index=True,
    )
    level = fields.Selection(
        selection=[
            ("not_demonstrated", "Not Demonstrated"),
            ("developing", "Developing"),
            ("proficient", "Proficient"),
            ("expert", "Expert"),
        ],
        string="Demonstrated Level",
        required=True,
        default="developing",
        tracking=True,
    )
    is_acquired = fields.Boolean(
        string="Competency Acquired",
        compute="_compute_is_acquired",
        store=True,
        help="True when the demonstrated level reaches the minimum "
             "acceptable level defined on the competency.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        tracking=True,
        index=True,
    )
    evidence = fields.Text(
        string="Assessment Evidence",
        help="Description of what was observed or reviewed to support the "
             "level awarded.",
    )

    _employee_competency_date_uniq = models.Constraint(
        "UNIQUE(employee_id, competency_id, date_assessment)",
        "An employee can only be assessed once per competency and date.",
    )

    @api.depends("date_assessment", "competency_id.reassessment_months")
    def _compute_date_next(self):
        """Schedule the next assessment from the competency interval."""
        for record in self:
            interval = record.competency_id.reassessment_months
            if interval and record.date_assessment:
                record.date_next = record.date_assessment + relativedelta(
                    months=interval
                )
            else:
                record.date_next = False

    @api.depends("level", "competency_id.minimum_level")
    def _compute_is_acquired(self):
        """Compare the demonstrated level to the required minimum."""
        for record in self:
            required = LEVEL_ORDER.get(
                record.competency_id.minimum_level, LEVEL_ORDER["proficient"]
            )
            achieved = LEVEL_ORDER.get(record.level, 0)
            record.is_acquired = achieved >= required

    @api.depends("employee_id", "competency_id", "date_assessment")
    def _compute_display_name(self):
        """Display employee, competency and assessment date."""
        for record in self:
            record.display_name = "%s / %s (%s)" % (
                record.employee_id.name or "",
                record.competency_id.name or "",
                record.date_assessment or "",
            )

    @api.constrains("employee_id", "assessor_id")
    def _check_assessor_not_employee(self):
        """An employee may not assess their own competency."""
        for record in self:
            if record.employee_id == record.assessor_id:
                raise ValidationError(
                    _("Employee '%s' cannot assess their own competency.")
                    % record.employee_id.name
                )

    @api.constrains("date_assessment", "date_next")
    def _check_dates(self):
        """The next assessment cannot precede the current one."""
        for record in self:
            if record.date_next and record.date_next < (
                record.date_assessment
            ):
                raise ValidationError(
                    _("The next assessment date of '%s' precedes the "
                      "assessment date.")
                    % record.display_name
                )

    def write(self, vals):
        """Confirmed assessments are read-only evidence."""
        locked_fields = {
            "employee_id",
            "competency_id",
            "assessor_id",
            "date_assessment",
            "level",
            "evidence",
        }
        if locked_fields.intersection(vals):
            for record in self:
                if record.state == "confirmed":
                    raise UserError(
                        _("Assessment '%s' is confirmed and can no longer "
                          "be modified.")
                        % record.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_training_competency_assessment(self):
        """Only draft assessments may be deleted."""
        for record in self:
            if record.state == "confirmed":
                raise UserError(
                    _("Assessment '%s' is confirmed and cannot be deleted.")
                    % record.display_name
                )

    def action_confirm(self):
        """Confirm the assessment and freeze its content."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Assessment '%s' is already confirmed.")
                    % record.display_name
                )
            if not record.evidence:
                raise UserError(
                    _("Assessment '%s' cannot be confirmed without recorded "
                      "evidence.")
                    % record.display_name
                )
        return self.write({"state": "confirmed"})
