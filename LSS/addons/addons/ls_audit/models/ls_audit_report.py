# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit report.

The audit report carries the conclusion of the audit and is subject to a
three-step control: preparation, independent review and approval.  The same
user may not both prepare and approve a report, which supports the
segregation of duties expected of a controlled quality record.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsAuditReport(models.Model):
    """Formal report concluding an audit."""

    _name = "ls.audit.report"
    _description = "Audit Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "report_date desc, reference desc"

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            help="Unique reference allocated automatically on creation.",
                            )
    name = fields.Char(
        string="Title",
        required=True,
        translate=True,
        tracking=True,
        help="Title of the audit report.",
    )
    audit_id = fields.Many2one(comodel_name="ls.audit.schedule", required=True,
                               ondelete="restrict",
                               index=True,
                               tracking=True,
                               help="Audit this report concludes.",)
    report_date = fields.Date(required=True,
                              default=fields.Date.context_today,
                              tracking=True,
                              help="Date of the report.",)
    executive_summary = fields.Text(required=True,
                                    help="Summary of how the audit was conducted and what was covered.",)
    conclusion = fields.Text(required=True,
                             help="Overall conclusion on the conformity and effectiveness of the "
                             "audited areas against the audit criteria.",)
    positive_observations = fields.Text(help="Strengths and good practices observed during the audit.",)
    distribution_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_audit_report_distribution_rel",
        column1="report_id",
        column2="user_id",
        string="Distribution List",
        help="Users the report is formally distributed to. Audit results are "
             "expected to be reported to the management responsible for the "
             "audited areas.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("issued", "Issued"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
        help="Lifecycle status of the report.",
    )
    prepared_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     readonly=True,
                                     tracking=True,
                                     help="User who prepared the report.",)
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,
                                     help="User who reviewed the report.",)
    review_date = fields.Datetime(readonly=True,
                                  copy=False,
                                  tracking=True,
                                  help="Date and time at which the report was reviewed.",)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,
                                     help="User who approved the report.",)
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,
                                    help="Date and time at which the report was approved.",)
    issue_date = fields.Datetime(readonly=True,
                                 copy=False,
                                 tracking=True,
                                 help="Date and time at which the report was distributed.",)
    cancellation_reason = fields.Text(readonly=True,
                                      copy=False,
                                      help="Justification recorded when the report was cancelled.",)
    finding_count = fields.Integer(
        string="Findings",
        related="audit_id.finding_count",
        readonly=True,
        help="Number of findings raised during the audited engagement.",
    )
    conformity_rate = fields.Float(
        string="Conformity Rate (%)",
        related="audit_id.conformity_rate",
        readonly=True,
        help="Conformity rate computed from the checklist responses.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,
                                 help="Company owning this report.",)
    active = fields.Boolean(default=True,
                            help="Archived reports are hidden from selection lists.",)

    _reference_company_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The audit report reference must be unique per company.",
    )

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Show the reference together with the report title."""
        for report in self:
            report.display_name = "[%s] %s" % (
                report.reference or "",
                report.name or "",
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the report reference from the dedicated sequence.

        :param vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: recordset
        """
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                vals["reference"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.audit.report")
                    or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modification of an issued or cancelled report.

        :param vals: values to write.
        :return: ``True``.
        :rtype: bool
        :raise UserError: when a locked report would be modified.
        """
        allowed_fields = {
            "active",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        if not set(vals) <= allowed_fields:
            locked = self.filtered(
                lambda report: report.state in ("issued", "cancelled")
            )
            if locked:
                raise UserError(
                    _(
                        "Report(s) %(refs)s reached a final status and can "
                        "no longer be modified.",
                        refs=", ".join(locked.mapped("reference")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_report(self):
        """Forbid deletion of a report that left the draft status.

        :return: ``True``.
        :rtype: bool
        :raise UserError: when a submitted report would be deleted.
        """
        submitted = self.filtered(lambda report: report.state != "draft")
        if submitted:
            raise UserError(
                _(
                    "Report(s) %(refs)s left the draft status and cannot be "
                    "deleted. Cancel them instead so that the record and its "
                    "audit trail are retained.",
                    refs=", ".join(submitted.mapped("reference")),
                )
            )

    @api.constrains("audit_id", "company_id")
    def _check_company_consistency(self):
        """Forbid a report attached to an audit of another company.

        :raise ValidationError: when the audit belongs to another company.
        """
        for report in self:
            if report.audit_id.company_id != report.company_id:
                raise ValidationError(
                    _(
                        "Report %(ref)s is attached to an audit of another "
                        "company.",
                        ref=report.reference,
                    )
                )

    def _check_state(self, expected, action_label):
        """Verify that every report is in one of the ``expected`` statuses.

        :param expected: tuple of accepted status codes.
        :param action_label: translated label of the attempted transition.
        :raise UserError: when a report is in an unexpected status.
        """
        wrong = self.filtered(lambda report: report.state not in expected)
        if wrong:
            raise UserError(
                _(
                    "Action '%(action)s' is not allowed for report(s) "
                    "%(refs)s in their current status.",
                    action=action_label,
                    refs=", ".join(wrong.mapped("reference")),
                )
            )

    def action_submit_review(self):
        """Submit the report for independent review.

        :raise UserError: when the report is not in draft status or when the
            audit fieldwork is not complete.
        """
        self._check_state(("draft",), _("Submit for Review"))
        for report in self:
            if report.audit_id.state not in (
                "completed",
                "follow_up",
                "closed",
            ):
                raise UserError(
                    _(
                        "Report %(ref)s cannot be submitted because the "
                        "fieldwork of audit %(audit)s is not complete.",
                        ref=report.reference,
                        audit=report.audit_id.reference,
                    )
                )
        self.write({"state": "under_review"})
        return True

    def action_review(self):
        """Record the independent review of the report.

        :raise UserError: when the report is not under review or when the
            reviewer prepared the report.
        """
        self._check_state(("under_review",), _("Review"))
        for report in self:
            if self.env.user == report.prepared_by_id:
                raise UserError(
                    _(
                        "Report %(ref)s cannot be reviewed by the user who "
                        "prepared it. The review must be independent.",
                        ref=report.reference,
                    )
                )
        self.write(
            {
                "reviewed_by_id": self.env.user.id,
                "review_date": fields.Datetime.now(),
            }
        )
        return True

    def action_approve(self):
        """Approve the report after review.

        :raise UserError: when the report has not been reviewed or when the
            approver prepared the report.
        """
        self._check_state(("under_review",), _("Approve"))
        for report in self:
            if not report.reviewed_by_id:
                raise UserError(
                    _(
                        "Report %(ref)s must be reviewed before it can be "
                        "approved.",
                        ref=report.reference,
                    )
                )
            if self.env.user == report.prepared_by_id:
                raise UserError(
                    _(
                        "Report %(ref)s cannot be approved by the user who "
                        "prepared it. Preparation and approval must be "
                        "performed by different users.",
                        ref=report.reference,
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

    def action_issue(self):
        """Issue the report to its distribution list.

        :raise UserError: when the report is not approved or when the
            distribution list is empty.
        """
        self._check_state(("approved",), _("Issue"))
        for report in self:
            if not report.distribution_ids:
                raise UserError(
                    _(
                        "Report %(ref)s cannot be issued because its "
                        "distribution list is empty. Audit results must be "
                        "reported to the responsible management.",
                        ref=report.reference,
                    )
                )
        self.write(
            {"state": "issued", "issue_date": fields.Datetime.now()}
        )
        template = self.env.ref(
            "ls_audit.mail_template_audit_report_issued",
            raise_if_not_found=False,
        )
        for report in self:
            report.message_subscribe(
                partner_ids=report.distribution_ids.partner_id.ids
            )
            if template:
                template.send_mail(report.id, force_send=False)
        return True

    def action_reset_to_draft(self):
        """Send a report under review back to draft.

        :raise UserError: when the report is not under review.
        """
        self._check_state(("under_review",), _("Reset to Draft"))
        self.write(
            {
                "state": "draft",
                "reviewed_by_id": False,
                "review_date": False,
            }
        )
        return True

    def action_cancel(self):
        """Open the cancellation wizard requesting a justification.

        :return: an act window action opening the cancellation wizard.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.audit.cancel",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }
