# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Periodic post-market reports.

Article 85 of Regulation (EU) 2017/745 requires manufacturers of class I
devices to prepare a post-market surveillance report summarising the results and
conclusions of the analyses of the post-market surveillance data gathered as a
result of the post-market surveillance plan referred to in Article 84, together
with a rationale and description of any preventive and corrective actions taken.
That report is updated when necessary and made available to the competent
authority upon request.

Article 86 requires manufacturers of class IIa, class IIb and class III devices
to prepare a periodic safety update report for each device, and where relevant
for each category or group of devices, on the same basis. Throughout the
lifetime of the device the report sets out the conclusions of the benefit-risk
determination, the main findings of the post-market clinical follow-up, and the
volume of sales together with an estimate of the size and other characteristics
of the population using the device and, where practicable, its usage frequency.

Manufacturers of class IIb and class III devices update the report at least
annually. Manufacturers of class IIa devices update it when necessary and at
least every two years.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdPmsReport(models.Model):
    """One periodic post-market report covering one reporting period."""

    _name = "ls.md.pms_report"
    _description = "Periodic Post-Market Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "device_id, period_end desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,)
    pms_id = fields.Many2one(
        comodel_name="ls.md.pms",
        string="Surveillance Plan",
        ondelete="set null",
        tracking=True,
        help="Post-market surveillance plan under which the data was gathered.",
    )
    report_type = fields.Selection(selection=constants.PERIODIC_REPORT_TYPE_SELECTION, required=True,
                                   tracking=True,
                                   help=(
                                       "Kind of report. The value is proposed from the risk class of the "
                                       "device and remains editable so that a report can be recorded for "
                                       "a device whose classification changed during the period."),
                                   )
    state = fields.Selection(
        selection=constants.REGULATORY_DOC_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    period_start = fields.Date(required=True, tracking=True)
    period_end = fields.Date(required=True, tracking=True)
    next_report_due = fields.Date(compute="_compute_next_report_due",
                                  store=True,
                                  help=(
                                      "Computed by adding the maximum interval of the risk class to the "
                                      "end of the covered period. Empty when no maximum interval applies."),
                                  )

    # ------------------------------------------------------------------
    # Content required by Article 86(1)
    # ------------------------------------------------------------------
    benefit_risk_conclusion = fields.Text(
        string="Benefit-Risk Determination Conclusion",
        tracking=True,
        help="Conclusions of the benefit-risk determination for the period.",
    )
    conclusion = fields.Selection(selection=constants.PERIODIC_REPORT_CONCLUSION_SELECTION, tracking=True,)
    pmcf_main_findings = fields.Text(
        string="Main PMCF Findings",
        help="Main findings of the post-market clinical follow-up for the period.",
    )
    sales_volume = fields.Float(
        string="Volume of Sales",
        digits=(16, 2),
        help="Number of units placed on the market during the period.",
    )
    population_estimate = fields.Text(
        string="User Population Estimate",
        help=(
            "Estimate of the size and other characteristics of the population "
            "using the device and, where practicable, the usage frequency."
        ),
    )

    # ------------------------------------------------------------------
    # Data summary for the period
    # ------------------------------------------------------------------
    complaint_count = fields.Integer(
        string="Complaints Received",
        help=(
            "Number of complaints received during the period. Entered "
            "manually, or written by an integrating module. This module does "
            "not hold complaint records."
        ),
    )
    serious_incident_count = fields.Integer(
        string="Serious Incidents Reported",
        help="Number of serious incidents reported during the period.",
    )
    non_serious_incident_count = fields.Integer(
        string="Non-Serious Incidents Recorded",
        help=(
            "Number of non-serious incidents and undesirable side-effects "
            "recorded during the period."
        ),
    )
    fsca_count = fields.Integer(
        string="Field Safety Corrective Actions",
        help="Number of field safety corrective actions initiated during the period.",
    )
    trend_signal_identified = fields.Boolean(tracking=True,
                                             help=(
                                                 "A statistically significant increase in the frequency or severity "
                                                 "of incidents was identified during the period."),
                                             )
    trend_signal_description = fields.Text()
    data_analysis_summary = fields.Text(
        string="Analysis Summary",
        help=(
            "Summary of the results and conclusions of the analyses of the "
            "post-market surveillance data gathered under the plan."
        ),
    )
    capa_summary = fields.Text(
        string="Preventive and Corrective Actions",
        help=(
            "Rationale and description of any preventive and corrective "
            "actions taken during the period."
        ),
    )
    risk_file_update_required = fields.Boolean(
        string="Risk Management File Update Required", tracking=True
    )
    clinical_evaluation_update_required = fields.Boolean(tracking=True)
    labelling_update_required = fields.Boolean(
        string="Labelling or IFU Update Required", tracking=True
    )

    # ------------------------------------------------------------------
    # Submission and approval
    # ------------------------------------------------------------------
    author_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                tracking=True,)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    notified_body_submission_required = fields.Boolean(help=(
            "Article 86(2) routes the reports of class III devices and "
            "implantable devices to the notified body through the electronic "
            "system referred to in Article 92."
        ),
    )
    notified_body_submission_date = fields.Date(
        string="Submitted to Notified Body", copy=False, tracking=True
    )
    notified_body_reference = fields.Char(
        string="Notified Body Submission Reference", copy=False
    )
    notes = fields.Text()

    _period_order = models.Constraint(
        "CHECK(period_end >= period_start)",
        "The reporting period end cannot precede its start.",
    )
    _device_period_unique = models.Constraint(
        "UNIQUE(device_id, period_start, period_end)",
        "A device cannot have two reports covering exactly the same period.",
    )
    _counts_non_negative = models.Constraint(
        "CHECK(complaint_count >= 0 AND serious_incident_count >= 0 "
        "AND non_serious_incident_count >= 0 AND fsca_count >= 0)",
        "Incident and complaint counts cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute and onchange methods
    # ------------------------------------------------------------------
    @api.depends("period_end", "device_id.periodic_report_interval_months")
    def _compute_next_report_due(self):
        """Derive the due date of the following periodic report."""
        for record in self:
            interval = record.device_id.periodic_report_interval_months
            if interval and record.period_end:
                record.next_report_due = record.period_end + relativedelta(
                    months=interval
                )
            else:
                record.next_report_due = False

    @api.onchange("device_id")
    def _onchange_device_id(self):
        """Propose the report type and the submission obligation."""
        for record in self:
            device = record.device_id
            if not device:
                continue
            record.report_type = (
                device.periodic_report_type or constants.PERIODIC_REPORT_PSUR
            )
            record.notified_body_submission_required = bool(device.is_implantable)

    @api.depends("name", "device_id", "period_start", "period_end")
    def _compute_display_name(self):
        """Show the reference together with the covered period."""
        for record in self:
            if record.period_start and record.period_end:
                record.display_name = (
                    f"{record.name or ''} ({record.period_start} - {record.period_end})"
                )
            else:
                record.display_name = record.name or ""

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("trend_signal_identified", "trend_signal_description")
    def _check_trend_signal_description(self):
        """Require a description when a trend signal is flagged."""
        for record in self:
            if record.trend_signal_identified and not record.trend_signal_description:
                raise ValidationError(
                    self.env._(
                        "Report '%(name)s' flags a trend signal but records no "
                        "description of it.",
                        name=record.name or "",
                    )
                )

    @api.constrains("device_id", "pms_id")
    def _check_plan_device(self):
        """Reject a surveillance plan belonging to another device."""
        for record in self:
            if record.pms_id and record.pms_id.device_id != record.device_id:
                raise ValidationError(
                    self.env._(
                        "The selected surveillance plan belongs to a different "
                        "device."
                    )
                )

    @api.constrains("period_start", "period_end", "device_id")
    def _check_periods_do_not_overlap(self):
        """Reject a reporting period overlapping another report of the device.

        Overlapping periods would double-count the post-market data and make
        the series of reports impossible to reconcile.
        """
        for record in self:
            if not (record.period_start and record.period_end and record.device_id):
                continue
            overlapping = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("device_id", "=", record.device_id.id),
                    ("state", "!=", "cancelled"),
                    ("period_start", "<=", record.period_end),
                    ("period_end", ">=", record.period_start),
                ]
            )
            if overlapping:
                raise ValidationError(
                    self.env._(
                        "The reporting period of '%(name)s' overlaps an "
                        "existing report for device '%(device)s'.",
                        name=record.name or "",
                        device=record.device_id.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the report reference and default the report type.

        The submission obligation is defaulted here as well as in the
        onchange. An onchange only fires in the user interface, so a report
        created through the ORM -- by the reporting wizard, by an import or by
        another module -- would otherwise lose the Article 86(2) obligation
        silently. An explicit value passed by the caller is never overridden.
        """
        placeholder = self.env._("New")
        device_model = self.env["ls.md.device"]
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.pms_report"
                ) or self.env._("PMR/UNSEQUENCED")
            if not vals.get("device_id"):
                continue
            device = device_model.browse(vals["device_id"])
            if not vals.get("report_type"):
                vals["report_type"] = (
                    device.periodic_report_type or constants.PERIODIC_REPORT_PSUR
                )
            if "notified_body_submission_required" not in vals:
                vals["notified_body_submission_required"] = bool(
                    device.is_implantable
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the content of a report in two steps.

        The content prepared by the author is frozen when the report is
        submitted for review, so that the reviewer approves the version that
        was submitted. The conclusions, recorded during the review, are frozen
        at approval.
        """
        author_content = {
            "period_start",
            "period_end",
            "device_id",
            "report_type",
            "data_analysis_summary",
            "sales_volume",
        }
        review_content = {"benefit_risk_conclusion", "conclusion"}
        for record in self:
            if author_content.intersection(vals) and record.state != "draft":
                raise UserError(
                    self.env._(
                        "Report '%(name)s' has been submitted: its content can "
                        "no longer be modified.",
                        name=record.name or "",
                    )
                )
            if review_content.intersection(vals) and record.state not in (
                "draft",
                "under_review",
            ):
                raise UserError(
                    self.env._(
                        "Report '%(name)s' is approved and can no longer "
                        "be modified.",
                        name=record.name or "",
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_pms_report(self):
        """Prevent deletion of approved or superseded reports."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "Report '%(name)s' can no longer be deleted. Cancel it "
                        "instead.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Reset the identity and approval of a duplicated report."""
        default = dict(default or {})
        default.setdefault("name", self.env._("New"))
        default.setdefault("state", "draft")
        default.setdefault("approver_id", False)
        default.setdefault("approval_date", False)
        default.setdefault("notified_body_submission_date", False)
        default.setdefault("notified_body_reference", False)
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def _check_approval_authority(self):
        """Raise unless the current user may approve regulatory records."""
        if not (
            self.env.user.has_group(constants.GROUP_REGULATORY)
            or self.env.user.has_group(constants.GROUP_MANAGER)
        ):
            raise UserError(
                self.env._(
                    "Approving a periodic post-market report requires the "
                    "Medical Devices Regulatory Affairs or Manager access "
                    "level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft report to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft report can be submitted for review."
                    )
                )
            if not record.data_analysis_summary:
                raise UserError(
                    self.env._(
                        "Record the analysis summary of report '%(name)s' "
                        "before submitting it for review.",
                        name=record.name or "",
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the report once its regulatory content is recorded.

        :raise UserError: when the approver is the author of the report
            (segregation of duties).
        """
        self._check_approval_authority()
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._("Only a report under review can be approved.")
                )
            if record.author_id == self.env.user:
                raise UserError(
                    self.env._(
                        "The author of report '%(name)s' cannot approve it.",
                        name=record.name or "",
                    )
                )
            if not record.benefit_risk_conclusion:
                raise UserError(
                    self.env._(
                        "Record the benefit-risk determination conclusion of "
                        "report '%(name)s' before approving it.",
                        name=record.name or "",
                    )
                )
            if not record.conclusion:
                raise UserError(
                    self.env._(
                        "Record the conclusion of report '%(name)s' before "
                        "approving it.",
                        name=record.name or "",
                    )
                )
            record.write(
                {
                    "state": "approved",
                    "approver_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
        return True

    def action_supersede(self):
        """Mark an approved report as superseded by a later revision."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._("Only an approved report can be superseded.")
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel a report that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "Report '%(name)s' is already closed.",
                        name=record.name or "",
                    )
                )
            record.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        """Return a report under review to draft."""
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a report under review can be returned to draft."
                    )
                )
            record.state = "draft"
        return True

    def action_record_notified_body_submission(self):
        """Record that the report was submitted to the notified body."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved report can be recorded as submitted "
                        "to the notified body."
                    )
                )
            record.notified_body_submission_date = (
                record.notified_body_submission_date or today
            )
        return True
