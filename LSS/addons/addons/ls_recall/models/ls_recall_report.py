# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Recall report.

A recall report is the document submitted to management or to a competent
authority describing the progress or the outcome of a field action.
21 CFR 7.53 describes periodic recall status reports and the information
they contain.

The report freezes the figures it states. When the report is approved the
current totals are copied into snapshot fields, so a report submitted on
a given date continues to say what it said on that date even though the
underlying recall keeps moving.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    REPORT_FROZEN_STATES,
    REPORT_STATE_SELECTION,
    REPORT_TYPE_SELECTION,
)

#: Totals copied from the recall into the report when it is approved.
SNAPSHOT_FIELDS = {
    "snapshot_qty_distributed": "qty_distributed",
    "snapshot_qty_returned": "qty_returned",
    "snapshot_qty_destroyed": "qty_destroyed",
    "snapshot_qty_not_recovered": "qty_not_recovered",
    "snapshot_qty_accounted": "qty_accounted",
    "snapshot_qty_outstanding": "qty_outstanding",
    "snapshot_reconciliation_rate": "reconciliation_rate",
    "snapshot_consignee_count": "consignee_count",
    "snapshot_responded_count": "consignee_responded_count",
    "snapshot_checks_required": "effectiveness_required_count",
    "snapshot_checks_performed": "effectiveness_performed_count",
    "snapshot_checks_successful": "effectiveness_success_count",
}


class LsRecallReport(models.Model):
    """A status or final report on a recall."""

    _name = "ls.recall.report"
    _description = "Recall Report"
    _inherit = ["mail.thread"]
    _order = "execution_id, report_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self.env._("New"),
    )
    execution_id = fields.Many2one(
        comodel_name="ls.recall.execution",
        string="Recall",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        related="execution_id.company_id", store=True, index=True
    )
    report_type = fields.Selection(
        selection=REPORT_TYPE_SELECTION,
        required=True,
        default="status",
        tracking=True,
    )
    report_date = fields.Date(
        required=True, default=fields.Date.context_today, tracking=True
    )
    period_start = fields.Date()
    period_end = fields.Date()
    state = fields.Selection(
        selection=REPORT_STATE_SELECTION,
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )

    summary = fields.Html(sanitize=True, string="Situation Summary")
    actions_taken = fields.Html(sanitize=True)
    disposition = fields.Html(
        sanitize=True,
        string="Product Disposition",
        help="How recovered product has been or will be dealt with.",
    )
    conclusion = fields.Html(sanitize=True)

    prepared_by_user_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user,
        tracking=True,
    )
    reviewed_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False, tracking=True
    )
    review_date = fields.Datetime(readonly=True, copy=False)
    approved_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False, tracking=True
    )
    approval_date = fields.Datetime(readonly=True, copy=False)
    submitted_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="ls_recall_report_partner_rel",
        column1="report_id",
        column2="partner_id",
        string="Submitted To",
    )
    submission_date = fields.Datetime(readonly=True, copy=False)
    submission_reference = fields.Char()

    snapshot_qty_distributed = fields.Float(readonly=True, copy=False)
    snapshot_qty_returned = fields.Float(readonly=True, copy=False)
    snapshot_qty_destroyed = fields.Float(readonly=True, copy=False)
    snapshot_qty_not_recovered = fields.Float(readonly=True, copy=False)
    snapshot_qty_accounted = fields.Float(readonly=True, copy=False)
    snapshot_qty_outstanding = fields.Float(readonly=True, copy=False)
    snapshot_reconciliation_rate = fields.Float(readonly=True, copy=False)
    snapshot_consignee_count = fields.Integer(readonly=True, copy=False)
    snapshot_responded_count = fields.Integer(readonly=True, copy=False)
    snapshot_checks_required = fields.Integer(readonly=True, copy=False)
    snapshot_checks_performed = fields.Integer(readonly=True, copy=False)
    snapshot_checks_successful = fields.Integer(readonly=True, copy=False)
    snapshot_taken_on = fields.Datetime(readonly=True, copy=False)

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The report reference must be unique.",
    )

    @api.constrains("period_start", "period_end")
    def _check_period(self):
        """The reporting period must not end before it starts."""
        for report in self:
            if not (report.period_start and report.period_end):
                continue
            if report.period_end < report.period_start:
                raise ValidationError(
                    self.env._(
                        "The reporting period of %(name)s ends before it "
                        "starts.",
                        name=report.name,
                    )
                )

    @api.constrains("report_type", "execution_id")
    def _check_single_final_report(self):
        """A recall carries at most one final report."""
        for report in self.filtered(lambda r: r.report_type == "final"):
            duplicates = self.search_count(
                [
                    ("execution_id", "=", report.execution_id.id),
                    ("report_type", "=", "final"),
                    ("id", "!=", report.id),
                ]
            )
            if duplicates:
                raise ValidationError(
                    self.env._(
                        "Recall %(name)s already has a final report.",
                        name=report.execution_id.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the report reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == new_label:
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("ls.recall.report")
                    or new_label
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the report content once it is approved."""
        frozen = self.filtered(lambda r: r.state in REPORT_FROZEN_STATES)
        if frozen:
            allowed = {
                "state",
                "submitted_partner_ids",
                "submission_date",
                "submission_reference",
                "message_follower_ids",
                "message_ids",
                "message_main_attachment_id",
            }
            forbidden = set(vals) - allowed
            if forbidden:
                raise UserError(
                    self.env._(
                        "Report %(name)s is approved and its content is "
                        "frozen. The following cannot be changed: "
                        "%(fields)s.",
                        name=frozen[0].name,
                        fields=", ".join(sorted(forbidden)),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        """Only a draft report may be deleted."""
        blocked = self.filtered(lambda r: r.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Report %(name)s is no longer a draft and cannot be "
                    "deleted.",
                    name=blocked[0].name,
                )
            )

    def action_review(self):
        """Record the technical review of a draft report."""
        for report in self:
            if report.state != "draft":
                raise UserError(
                    self.env._("Only a draft report can be reviewed.")
                )
            if not report.summary:
                raise UserError(
                    self.env._(
                        "Report %(name)s has no situation summary.",
                        name=report.name,
                    )
                )
        self.write(
            {
                "state": "reviewed",
                "reviewed_by_user_id": self.env.user.id,
                "review_date": fields.Datetime.now(),
            }
        )
        return True

    def action_approve(self):
        """Approve the report and freeze the figures it states."""
        for report in self:
            if report.state != "reviewed":
                raise UserError(
                    self.env._(
                        "Report %(name)s must be reviewed before it is "
                        "approved.",
                        name=report.name,
                    )
                )
            if report.reviewed_by_user_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Report %(name)s must be approved by someone "
                        "other than the reviewer.",
                        name=report.name,
                    )
                )
        for report in self:
            report._take_snapshot()
        self.write(
            {
                "state": "approved",
                "approved_by_user_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        return True

    def action_submit(self):
        """Record the submission of an approved report."""
        for report in self:
            if report.state != "approved":
                raise UserError(
                    self.env._(
                        "Report %(name)s must be approved before it is "
                        "submitted.",
                        name=report.name,
                    )
                )
            if not report.submitted_partner_ids:
                raise UserError(
                    self.env._(
                        "Record who report %(name)s was submitted to.",
                        name=report.name,
                    )
                )
        self.write(
            {"state": "submitted", "submission_date": fields.Datetime.now()}
        )
        for report in self:
            report.execution_id.message_post(
                body=self.env._(
                    "Report %(name)s submitted to %(partners)s.",
                    name=report.name,
                    partners=", ".join(
                        report.submitted_partner_ids.mapped("display_name")
                    ),
                )
            )
        return True

    def _take_snapshot(self):  # noqa: W8110
        """Copy the current recall totals into the report.

        Called when the report is approved. Writing through ``sudo`` is
        not used here: the values are read from a record the user is
        already allowed to read, and written to the report itself.
        """
        self.ensure_one()
        execution = self.execution_id
        values = {
            target: execution[source]
            for target, source in SNAPSHOT_FIELDS.items()
        }
        values["snapshot_taken_on"] = fields.Datetime.now()
        # Bypass the frozen-content guard: the record is still in the
        # "reviewed" state at this point, so the guard does not apply.
        super().write(values)
