# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit checklist template.

A checklist is a controlled, versioned template of questions used to conduct
an audit consistently.  Only approved checklists can be loaded into an audit,
so that auditors cannot execute a draft or an obsolete question set.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsAuditChecklist(models.Model):
    """Controlled template of audit questions."""

    _name = "ls.audit.checklist"
    _description = "Audit Checklist Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, version desc"

    name = fields.Char(required=True,
                       translate=True,
                       tracking=True,
                       help="Title of the checklist template.",)
    code = fields.Char(required=True,
                       tracking=True,
                       help="Code shared by every version of this checklist.",)
    version = fields.Integer(required=True,
                             default=1,
                             tracking=True,
                             help="Version number of the checklist. A new version is created "
                             "rather than modifying an approved checklist.",)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("obsolete", "Obsolete"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        help="Lifecycle status. Only approved checklists can be loaded into "
             "an audit.",
    )
    audit_type_id = fields.Many2one(comodel_name="ls.audit.type", tracking=True,
                                    help="Audit type this checklist is designed for. Leave empty when "
                                    "the checklist applies to every audit type.",)
    area_ids = fields.Many2many(
        comodel_name="ls.audit.area",
        relation="ls_audit_checklist_area_rel",
        column1="checklist_id",
        column2="area_id",
        string="Applicable Areas",
        help="Areas this checklist is designed for. Leave empty when the "
             "checklist applies to every area.",
    )
    line_ids = fields.One2many(
        comodel_name="ls.audit.checklist.line",
        inverse_name="checklist_id",
        string="Questions",
        copy=True,
        help="Ordered list of questions making up the checklist.",
    )
    line_count = fields.Integer(
        string="Question Count",
        compute="_compute_line_count",
        store=True,
        help="Number of questions in the checklist.",
    )
    description = fields.Text(
        string="Purpose",
        translate=True,
        help="Purpose and intended use of the checklist.",
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,
                                     help="User who approved this checklist version.",)
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,
                                    help="Date and time at which the checklist version was approved.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this checklist.",)
    active = fields.Boolean(default=True,
                            help="Archived checklists are hidden from selection lists.",)

    _code_version_company_uniq = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "A checklist with this code and version already exists in this "
        "company.",
    )
    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The checklist version must be a positive number.",
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Count the questions of the checklist."""
        for checklist in self:
            checklist.line_count = len(checklist.line_ids)

    @api.depends("name", "code", "version")
    def _compute_display_name(self):
        """Show code, version and title so that versions are unambiguous."""
        for checklist in self:
            checklist.display_name = "[%s v%s] %s" % (
                checklist.code or "",
                checklist.version,
                checklist.name or "",
            )

    def action_approve(self):
        """Approve the checklist so that it can be used in audits.

        :raise UserError: when the checklist is not in draft status or has no
            question.
        """
        for checklist in self:
            if checklist.state != "draft":
                raise UserError(
                    _(
                        "Checklist '%(name)s' can only be approved from the "
                        "draft status.",
                        name=checklist.display_name,
                    )
                )
            if not checklist.line_ids:
                raise UserError(
                    _(
                        "Checklist '%(name)s' cannot be approved because it "
                        "contains no question.",
                        name=checklist.display_name,
                    )
                )
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        return True

    def action_set_obsolete(self):
        """Mark the checklist as obsolete so that it can no longer be used.

        :raise UserError: when the checklist is still in draft status.
        """
        for checklist in self:
            if checklist.state != "approved":
                raise UserError(
                    _(
                        "Only an approved checklist can be made obsolete. "
                        "Checklist '%(name)s' is not approved.",
                        name=checklist.display_name,
                    )
                )
        self.write({"state": "obsolete"})
        return True

    def action_reset_to_draft(self):
        """Send an approved checklist back to draft.

        :raise UserError: when the checklist has already been used by an
            audit, because the executed question set must remain traceable.
        """
        for checklist in self:
            used = self.env["ls.audit.schedule"].search_count(
                [("checklist_id", "=", checklist.id)]
            )
            if used:
                raise UserError(
                    _(
                        "Checklist '%(name)s' has been used by %(count)s "
                        "audit(s) and cannot be sent back to draft. Create a "
                        "new version instead.",
                        name=checklist.display_name,
                        count=used,
                    )
                )
        self.write(
            {
                "state": "draft",
                "approved_by_id": False,
                "approval_date": False,
            }
        )
        return True

    def action_new_version(self):
        """Create the next draft version of the checklist.

        :return: an act window action opening the newly created version.
        :rtype: dict
        """
        self.ensure_one()
        highest = self.search(
            [
                ("code", "=", self.code),
                ("company_id", "=", self.company_id.id),
            ],
            order="version desc",
            limit=1,
        )
        new_checklist = self.copy(
            {
                "version": highest.version + 1,
                "state": "draft",
                "approved_by_id": False,
                "approval_date": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": new_checklist.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.constrains("audit_type_id", "area_ids", "company_id")
    def _check_company_consistency(self):
        """Forbid references to records of another company."""
        for checklist in self:
            if (
                checklist.audit_type_id
                and checklist.audit_type_id.company_id != checklist.company_id
            ):
                raise ValidationError(
                    _(
                        "The audit type of checklist '%(name)s' belongs to "
                        "another company.",
                        name=checklist.display_name,
                    )
                )
            other_areas = checklist.area_ids.filtered(
                lambda area, checklist=checklist: area.company_id
                != checklist.company_id
            )
            if other_areas:
                raise ValidationError(
                    _(
                        "The applicable areas of checklist '%(name)s' "
                        "contain areas of another company.",
                        name=checklist.display_name,
                    )
                )
