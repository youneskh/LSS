# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit programme.

An audit programme groups the audits planned over a defined period, together
with the objective and the frequency rationale.  It supports the expectation,
common to quality management standards, that audits are planned as a
programme taking into account the importance and past performance of the
processes concerned, rather than scheduled individually and informally.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsAuditProgram(models.Model):
    """Planned set of audits covering a defined period."""

    _name = "ls.audit.program"
    _description = "Audit Programme"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, reference desc"

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
        help="Title of the audit programme, for example the year covered.",
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        tracking=True,
        help="First day of the period covered by the programme.",
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
        tracking=True,
        help="Last day of the period covered by the programme.",
    )
    responsible_id = fields.Many2one(
        comodel_name="res.users",
        string="Programme Owner",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User accountable for building and delivering the programme.",
    )
    objective = fields.Text(help="Objective of the programme and the rationale used to set the "
                            "audit frequency, such as process criticality, regulatory "
                            "impact and results of previous audits.",)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        help="Lifecycle status of the programme.",
    )
    audit_ids = fields.One2many(
        comodel_name="ls.audit.schedule",
        inverse_name="program_id",
        string="Audits",
        help="Audits planned under this programme.",
    )
    audit_count = fields.Integer(compute="_compute_audit_statistics",
                                 help="Number of audits planned under this programme.",)
    closed_audit_count = fields.Integer(
        string="Closed Audits",
        compute="_compute_audit_statistics",
        help="Number of audits that reached the closed status.",
    )
    completion_rate = fields.Float(
        string="Completion Rate (%)",
        compute="_compute_audit_statistics",
        help="Share of programme audits that reached the closed status.",
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,
                                     help="User who approved the programme.",)
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,
                                    help="Date and time at which the programme was approved.",)
    cancellation_reason = fields.Text(readonly=True,
                                      copy=False,
                                      help="Justification recorded when the programme was cancelled.",)
    notes = fields.Text(help="Free text notes on the programme.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this programme.",)
    active = fields.Boolean(default=True,
                            help="Archived programmes are hidden from selection lists.",)

    _reference_company_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The audit programme reference must be unique per company.",
    )

    @api.depends("audit_ids", "audit_ids.state")
    def _compute_audit_statistics(self):
        """Count programme audits and derive the completion rate."""
        for program in self:
            audits = program.audit_ids
            closed = audits.filtered(lambda audit: audit.state == "closed")
            program.audit_count = len(audits)
            program.closed_audit_count = len(closed)
            program.completion_rate = (
                100.0 * len(closed) / len(audits) if audits else 0.0
            )

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Show the reference together with the programme title."""
        for program in self:
            program.display_name = "[%s] %s" % (
                program.reference or "",
                program.name or "",
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the programme reference from the dedicated sequence.

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
                    .next_by_code("ls.audit.program")
                    or _("New")
                )
        return super().create(vals_list)

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """Forbid a programme ending before it starts."""
        for program in self:
            if program.date_end < program.date_start:
                raise ValidationError(
                    _(
                        "The end date of programme '%(name)s' is earlier "
                        "than its start date.",
                        name=program.name,
                    )
                )

    def action_approve(self):
        """Approve the programme so that its audits can be scheduled.

        :raise UserError: when the programme is not in draft status or has no
            audit.
        """
        for program in self:
            if program.state != "draft":
                raise UserError(
                    _(
                        "Programme '%(name)s' can only be approved from the "
                        "draft status.",
                        name=program.display_name,
                    )
                )
            if not program.audit_ids:
                raise UserError(
                    _(
                        "Programme '%(name)s' cannot be approved because it "
                        "contains no audit.",
                        name=program.display_name,
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

    def action_start(self):
        """Move the programme to the in progress status.

        :raise UserError: when the programme has not been approved.
        """
        for program in self:
            if program.state != "approved":
                raise UserError(
                    _(
                        "Programme '%(name)s' must be approved before it can "
                        "be started.",
                        name=program.display_name,
                    )
                )
        self.write({"state": "in_progress"})
        return True

    def action_close(self):
        """Close the programme once every audit reached a final status.

        :raise UserError: when at least one audit is neither closed nor
            cancelled.
        """
        for program in self:
            if program.state != "in_progress":
                raise UserError(
                    _(
                        "Programme '%(name)s' must be in progress before it "
                        "can be closed.",
                        name=program.display_name,
                    )
                )
            pending = program.audit_ids.filtered(
                lambda audit: audit.state not in ("closed", "cancelled")
            )
            if pending:
                raise UserError(
                    _(
                        "Programme '%(name)s' still contains %(count)s audit"
                        "(s) that are neither closed nor cancelled: "
                        "%(audits)s.",
                        name=program.display_name,
                        count=len(pending),
                        audits=", ".join(pending.mapped("reference")),
                    )
                )
        self.write({"state": "closed"})
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

    def action_view_audits(self):
        """Open the audits belonging to this programme.

        :return: an act window action listing the programme audits.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audits"),
            "res_model": "ls.audit.schedule",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
            "context": {
                "default_program_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }
