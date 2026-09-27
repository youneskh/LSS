# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Training course master data under an approval lifecycle."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsTrainingCourse(models.Model):
    """A controlled training course definition.

    Courses carry an explicit approval lifecycle because, in a GxP context,
    training may only be delivered against approved training material. Only
    courses in state ``approved`` can be scheduled into sessions.
    """

    _name = "ls.training.course"
    _description = "Training Course"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(
        string="Course Title",
        required=True,
        translate=True,
        index=True,
        tracking=True,
    )
    code = fields.Char(
        string="Course Code",
        required=True,
        copy=False,
        default=lambda self: _("New"),
        tracking=True,
        help="Unique course identifier. Generated from the sequence "
             "'ls.training.course' when left to its default value.",
    )
    version = fields.Char(required=True,
                          default="1.0",
                          tracking=True,
                          help="Version of the training material this course record describes.",)
    active = fields.Boolean(default=True,)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("review", "Under Review"),
            ("approved", "Approved"),
            ("obsolete", "Obsolete"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        tracking=True,
        index=True,
    )
    course_type = fields.Selection(
        selection=[
            ("induction", "Induction"),
            ("gmp", "GMP / GxP"),
            ("sop", "Procedure / SOP"),
            ("technical", "Technical"),
            ("safety", "Health and Safety"),
            ("quality", "Quality System"),
            ("regulatory", "Regulatory"),
        ],
        required=True,
        default="sop",
        tracking=True,
    )
    delivery_mode = fields.Selection(
        selection=[
            ("classroom", "Classroom"),
            ("on_the_job", "On-the-Job"),
            ("self_study", "Self-Study"),
            ("external_elearning", "External e-Learning"),
        ],
        required=True,
        default="classroom",
        tracking=True,
    )
    elearning_url = fields.Char(
        string="e-Learning URL",
        help="Address of the external e-Learning course. Only used when the "
             "delivery mode is 'External e-Learning'.",
    )
    description = fields.Html(
        string="Course Content",
        translate=True,
    )
    objective = fields.Text(
        string="Learning Objectives",
        translate=True,
    )
    duration_hours = fields.Float(
        string="Duration (Hours)",
        required=True,
        default=1.0,
        tracking=True,
    )
    validity_months = fields.Integer(
        string="Certification Validity (Months)",
        default=0,
        tracking=True,
        help="Number of months a certification issued by this course stays "
             "valid. Zero means the certification does not expire.",
    )
    requires_assessment = fields.Boolean(default=False,
                                         tracking=True,
                                         help="When enabled, an attendee must reach the pass score to obtain "
                                         "a certification.",)
    pass_score = fields.Float(
        string="Pass Score (%)",
        default=80.0,
        tracking=True,
    )
    competency_ids = fields.Many2many(
        comodel_name="ls.training.competency",
        relation="ls_training_course_competency_rel",
        column1="course_id",
        column2="competency_id",
        string="Granted Competencies",
    )
    session_ids = fields.One2many(
        comodel_name="ls.training.session",
        inverse_name="course_id",
        string="Sessions",
    )
    session_count = fields.Integer(compute="_compute_session_count",)
    certification_ids = fields.One2many(
        comodel_name="ls.training.certification",
        inverse_name="course_id",
        string="Certifications",
    )
    certification_count = fields.Integer(compute="_compute_certification_count",)
    requirement_ids = fields.One2many(
        comodel_name="ls.training.requirement",
        inverse_name="course_id",
        string="Training Requirements",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The course code must be unique per company.",
    )

    @api.depends("session_ids")
    def _compute_session_count(self):
        """Count sessions scheduled for each course."""
        grouped = self.env["ls.training.session"]._read_group(
            domain=[("course_id", "in", self.ids)],
            groupby=["course_id"],
            aggregates=["__count"],
        )
        mapped = {course.id: count for course, count in grouped}
        for record in self:
            record.session_count = mapped.get(record.id, 0)

    @api.depends("certification_ids")
    def _compute_certification_count(self):
        """Count certifications issued for each course."""
        grouped = self.env["ls.training.certification"]._read_group(
            domain=[("course_id", "in", self.ids)],
            groupby=["course_id"],
            aggregates=["__count"],
        )
        mapped = {course.id: count for course, count in grouped}
        for record in self:
            record.certification_count = mapped.get(record.id, 0)

    @api.depends("code", "name", "version")
    def _compute_display_name(self):
        """Display the course code, title and version."""
        for record in self:
            record.display_name = "[%s] %s (v%s)" % (
                record.code,
                record.name,
                record.version,
            )

    @api.constrains("duration_hours")
    def _check_duration_hours(self):
        """A course must have a strictly positive duration."""
        for record in self:
            if record.duration_hours <= 0.0:
                raise ValidationError(
                    _("The duration of course '%s' must be greater than "
                      "zero.")
                    % record.display_name
                )

    @api.constrains("pass_score")
    def _check_pass_score(self):
        """The pass score is a percentage between 0 and 100."""
        for record in self:
            if not 0.0 <= record.pass_score <= 100.0:
                raise ValidationError(
                    _("The pass score of course '%s' must be between 0 and "
                      "100.")
                    % record.display_name
                )

    @api.constrains("validity_months")
    def _check_validity_months(self):
        """Certification validity cannot be negative."""
        for record in self:
            if record.validity_months < 0:
                raise ValidationError(
                    _("The certification validity of course '%s' cannot be "
                      "negative.")
                    % record.display_name
                )

    @api.constrains("delivery_mode", "elearning_url")
    def _check_elearning_url(self):
        """External e-Learning courses must carry their access address."""
        for record in self:
            if record.delivery_mode == "external_elearning" and not (
                record.elearning_url
            ):
                raise ValidationError(
                    _("Course '%s' is delivered as external e-Learning and "
                      "therefore requires an e-Learning URL.")
                    % record.display_name
                )

    @api.onchange("requires_assessment")
    def _onchange_requires_assessment(self):
        """Reset the pass score when no assessment is performed."""
        for record in self:
            if not record.requires_assessment:
                record.pass_score = 0.0
            elif record.pass_score <= 0.0:
                record.pass_score = 80.0

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the course code from the sequence when not supplied."""
        for vals in vals_list:
            if vals.get("code", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                vals["code"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.training.course")
                    or _("New")
                )
        return super().create(vals_list)

    def action_submit_review(self):
        """Move a draft course to the review state."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft course can be submitted for review. "
                      "Course '%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
        return self.write({"state": "review"})

    def action_approve(self):
        """Approve a course under review so it can be scheduled."""
        for record in self:
            if record.state != "review":
                raise UserError(
                    _("Only a course under review can be approved. Course "
                      "'%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
        return self.write({"state": "approved"})

    def action_set_obsolete(self):
        """Retire an approved course."""
        for record in self:
            if record.state != "approved":
                raise UserError(
                    _("Only an approved course can be made obsolete. Course "
                      "'%s' is in state '%s'.")
                    % (record.display_name, record.state)
                )
            open_sessions = record.session_ids.filtered(
                lambda session: session.state in ("draft", "confirmed",
                                                  "in_progress")
            )
            if open_sessions:
                raise UserError(
                    _("Course '%s' still has %d open session(s). Close or "
                      "cancel them before making the course obsolete.")
                    % (record.display_name, len(open_sessions))
                )
        return self.write({"state": "obsolete"})

    def action_reset_to_draft(self):
        """Return a course to draft for revision."""
        for record in self:
            if record.state == "draft":
                raise UserError(
                    _("Course '%s' is already in draft.")
                    % record.display_name
                )
        return self.write({"state": "draft"})

    def action_view_sessions(self):
        """Open the sessions of this course."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_session_action"
        )
        action["domain"] = [("course_id", "=", self.id)]
        action["context"] = {"default_course_id": self.id}
        return action

    def action_view_certifications(self):
        """Open the certifications issued by this course."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_certification_action"
        )
        action["domain"] = [("course_id", "=", self.id)]
        action["context"] = {"default_course_id": self.id}
        return action
