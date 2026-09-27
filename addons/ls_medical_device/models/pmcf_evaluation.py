# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Post-market clinical follow-up evaluation reports.

Part B of Annex XIV of Regulation (EU) 2017/745 describes post-market clinical
follow-up as a continuous process that updates the clinical evaluation referred
to in Article 61 and Part A of Annex XIV, and requires it to be addressed in the
post-market surveillance plan. Section 8 of Part B requires the conclusions of
the post-market clinical follow-up evaluation report to be taken into account
for the clinical evaluation and for risk management, and requires the
manufacturer to implement preventive or corrective measures where the follow-up
identifies a need for them.

Article 61(11) requires the post-market clinical follow-up evaluation report of
class III devices and implantable devices to be updated at least annually.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdPmcfEvaluation(models.Model):
    """One post-market clinical follow-up evaluation report."""

    _name = "ls.md.pmcf_evaluation"
    _description = "PMCF Evaluation Report"
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
    clinical_evaluation_id = fields.Many2one(comodel_name="ls.md.clinical_evaluation", ondelete="set null",
                                             tracking=True,
                                             help="Clinical evaluation that this report updates.",)
    state = fields.Selection(
        selection=constants.REGULATORY_DOC_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    period_start = fields.Date(required=True,
                               tracking=True,
                               help="Start of the period covered by the report.",)
    period_end = fields.Date(required=True,
                             tracking=True,
                             help="End of the period covered by the report.",)
    annual_update_required = fields.Boolean(related="device_id.annual_pmcf_update_required",
                                            store=True,
                                            help=(
                                                "True for class III devices and implantable devices, which require "
                                                "the report to be updated at least annually under Article 61(11)."
                                                ),
                                            )
    next_update_due = fields.Date(compute="_compute_next_update_due",
                                  store=True,
                                  help=(
                                      "Computed as twelve months after the end of the covered period "
                                      "when an annual update is required."),
                                  )
    activities_performed = fields.Text(
        string="PMCF Activities Performed",
        help=(
            "General and specific methods and procedures carried out during "
            "the period, for example literature screening, user feedback "
            "collection, registry data analysis or post-market studies."
        ),
    )
    data_collected = fields.Text(
        string="Clinical Data Collected",
        help="Clinical data gathered through the activities performed.",
    )
    findings = fields.Text(
        string="Main Findings",
        tracking=True,
        help="Main findings of the post-market clinical follow-up activities.",
    )
    new_risks_identified = fields.Boolean(
        string="New or Emerging Risks Identified",
        tracking=True,
    )
    new_risks_description = fields.Text(
        string="New or Emerging Risks",
        help="Description of the new or emerging risks identified.",
    )
    off_label_use_observed = fields.Boolean(
        string="Off-Label Use or Misuse Observed",
        help="Use outside the intended purpose, or misuse, was observed.",
    )
    off_label_use_description = fields.Text(string="Off-Label Use or Misuse")
    benefit_risk_conclusion = fields.Text(
        string="Benefit-Risk Conclusion",
        tracking=True,
        help="Conclusion on the continued acceptability of the benefit-risk ratio.",
    )
    benefit_risk_remains_acceptable = fields.Boolean(
        string="Benefit-Risk Remains Acceptable",
        default=True,
        tracking=True,
    )
    actions_required = fields.Boolean(
        string="Preventive or Corrective Action Required",
        tracking=True,
        help=(
            "Section 8 of Part B of Annex XIV requires the manufacturer to "
            "implement preventive or corrective measures where the follow-up "
            "identifies a need for them."
        ),
    )
    actions_description = fields.Text(
        string="Actions",
        help="Preventive or corrective measures identified and their status.",
    )
    clinical_evaluation_update_required = fields.Boolean(tracking=True,
                                                         help="The conclusions require the clinical evaluation to be updated.",)
    risk_file_update_required = fields.Boolean(
        string="Risk Management File Update Required",
        tracking=True,
        help="The conclusions require the risk management file to be updated.",
    )
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
    notes = fields.Text()

    _period_order = models.Constraint(
        "CHECK(period_end >= period_start)",
        "The period end cannot precede the period start.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("period_end", "annual_update_required")
    def _compute_next_update_due(self):
        """Derive the due date of the next annual update."""
        for record in self:
            if record.annual_update_required and record.period_end:
                record.next_update_due = record.period_end + relativedelta(
                    months=constants.PMCF_ANNUAL_UPDATE_MONTHS
                )
            else:
                record.next_update_due = False

    @api.depends("name", "device_id", "period_end")
    def _compute_display_name(self):
        """Show the reference together with the covered period end."""
        for record in self:
            if record.period_end:
                record.display_name = f"{record.name or ''} ({record.period_end})"
            else:
                record.display_name = record.name or ""

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("new_risks_identified", "new_risks_description")
    def _check_new_risks_description(self):
        """Require a description when new risks are flagged."""
        for record in self:
            if record.new_risks_identified and not record.new_risks_description:
                raise ValidationError(
                    self.env._(
                        "PMCF evaluation report '%(name)s' flags new or "
                        "emerging risks but records no description.",
                        name=record.name or "",
                    )
                )

    @api.constrains("actions_required", "actions_description")
    def _check_actions_description(self):
        """Require a description when actions are flagged as required."""
        for record in self:
            if record.actions_required and not record.actions_description:
                raise ValidationError(
                    self.env._(
                        "PMCF evaluation report '%(name)s' requires preventive "
                        "or corrective action but records no description of "
                        "that action.",
                        name=record.name or "",
                    )
                )

    @api.constrains("device_id", "clinical_evaluation_id")
    def _check_clinical_evaluation_device(self):
        """Reject a clinical evaluation belonging to another device."""
        for record in self:
            if (
                record.clinical_evaluation_id
                and record.clinical_evaluation_id.device_id != record.device_id
            ):
                raise ValidationError(
                    self.env._(
                        "The selected clinical evaluation belongs to a "
                        "different device."
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the report reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.pmcf_evaluation"
                ) or self.env._("PMCF/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the content of an approved report."""
        protected = {
            "period_start",
            "period_end",
            "findings",
            "benefit_risk_conclusion",
            "benefit_risk_remains_acceptable",
            "device_id",
        }
        if protected.intersection(vals):
            for record in self:
                if record.state == "approved":
                    raise UserError(
                        self.env._(
                            "PMCF evaluation report '%(name)s' is approved and "
                            "can no longer be modified.",
                            name=record.name or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_pmcf_evaluation(self):
        """Prevent deletion of approved or superseded reports."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "PMCF evaluation report '%(name)s' can no longer be "
                        "deleted. Cancel it instead.",
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
                    "Approving a PMCF evaluation report requires the Medical "
                    "Devices Regulatory Affairs or Manager access level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft report to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft PMCF evaluation report can be submitted "
                        "for review."
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the report and record the approver."""
        self._check_approval_authority()
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a PMCF evaluation report under review can be "
                        "approved."
                    )
                )
            if record.author_id == self.env.user:
                raise UserError(
                    self.env._(
                        "The author of '%(name)s' cannot approve it "
                        "(segregation of duties).",
                        name=record.display_name or "",
                    )
                )
            if not record.benefit_risk_conclusion:
                raise UserError(
                    self.env._(
                        "Record the benefit-risk conclusion of PMCF "
                        "evaluation report '%(name)s' before approving it.",
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
        """Mark an approved report as superseded by a later one."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved PMCF evaluation report can be "
                        "superseded."
                    )
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel a report that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "PMCF evaluation report '%(name)s' is already closed.",
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
                        "Only a PMCF evaluation report under review can be "
                        "returned to draft."
                    )
                )
            record.state = "draft"
        return True
