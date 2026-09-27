# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Risk management file.

ISO 14971:2019 specifies a process for manufacturers to identify hazards
associated with medical devices, to estimate and evaluate the associated risks,
to control those risks and to monitor the effectiveness of the controls. The
risk management file is the set of records produced by that process.

This model holds the file header: its scope, the policy criteria in force, the
overall benefit-risk conclusion and the approval record. Individual risks are
held on ``ls.md.risk_item``.

The severity and probability scales shipped with this module are configuration
defaults. ISO 14971:2019 requires the manufacturer to define its own categories
in the risk management plan.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdRiskAssessment(models.Model):
    """Header record of a risk management file for one device."""

    _name = "ls.md.risk_assessment"
    _description = "Medical Device Risk Management File"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "device_id, version desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    title = fields.Char(required=True,
                        tracking=True,
                        help="Title of the risk management file.",)
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,)
    version = fields.Integer(default=1,
                             required=True,
                             tracking=True,
                             help="Version number of the risk management file.",)
    state = fields.Selection(
        selection=constants.REGULATORY_DOC_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    scope = fields.Text(help="Scope of the risk management activities covered by this file.",)
    risk_policy = fields.Text(
        string="Risk Acceptability Policy",
        help=(
            "Criteria for risk acceptability defined by the organisation, as "
            "required by ISO 14971:2019. Record the criteria in force for this "
            "file so that the acceptability decisions below can be audited."
        ),
    )
    standard_reference = fields.Char(default="ISO 14971:2019",
                                     help="Risk management standard applied to this file.",)
    assessment_date = fields.Date(default=fields.Date.context_today,
                                  tracking=True,)
    responsible_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                     tracking=True,
                                     help="User responsible for maintaining the risk management file.",)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,)
    risk_item_ids = fields.One2many(
        comodel_name="ls.md.risk_item",
        inverse_name="risk_assessment_id",
        string="Risks",
        copy=True,
    )
    risk_item_count = fields.Integer(
        string="Risk Count",
        compute="_compute_risk_statistics",
        store=True,
    )
    unacceptable_risk_count = fields.Integer(
        string="Unacceptable Residual Risks",
        compute="_compute_risk_statistics",
        store=True,
        help="Number of risks whose residual acceptability is unacceptable.",
    )
    uncontrolled_risk_count = fields.Integer(
        string="Risks Without Control Measure",
        compute="_compute_risk_statistics",
        store=True,
        help="Number of risks for which no risk control measure is recorded.",
    )
    max_residual_index = fields.Integer(
        string="Highest Residual Risk Index",
        compute="_compute_risk_statistics",
        store=True,
    )
    overall_benefit_risk_conclusion = fields.Text(
        string="Overall Benefit-Risk Conclusion",
        tracking=True,
        help=(
            "Conclusion on the overall residual risk, drawn once all "
            "individual risks have been evaluated."
        ),
    )
    overall_risk_acceptable = fields.Boolean(
        string="Overall Residual Risk Acceptable",
        tracking=True,
        help="Records the outcome of the overall residual risk evaluation.",
    )
    production_information_summary = fields.Text(
        string="Production and Post-Production Information",
        help=(
            "Summary of the information collected from production and "
            "post-production activities that was reviewed for this file."
        ),
    )
    notes = fields.Text()

    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The risk management file version must be strictly positive.",
    )
    _device_version_unique = models.Constraint(
        "UNIQUE(device_id, version)",
        "A device cannot have two risk management files with the same version.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends(
        "risk_item_ids",
        "risk_item_ids.residual_acceptability",
        "risk_item_ids.residual_index",
        "risk_item_ids.control_measure",
    )
    def _compute_risk_statistics(self):
        """Aggregate the risk lines into file-level indicators."""
        for record in self:
            items = record.risk_item_ids
            record.risk_item_count = len(items)
            record.unacceptable_risk_count = len(
                items.filtered(
                    lambda item: item.residual_acceptability == "unacceptable"
                )
            )
            record.uncontrolled_risk_count = len(
                items.filtered(lambda item: not item.control_measure)
            )
            indices = items.mapped("residual_index")
            record.max_residual_index = max(indices) if indices else 0

    @api.depends("name", "title", "version")
    def _compute_display_name(self):
        """Show the reference, the title and the version."""
        for record in self:
            record.display_name = self.env._(
                "%(reference)s - %(title)s (v%(version)s)",
                reference=record.name or "",
                title=record.title or "",
                version=record.version,
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("state", "overall_benefit_risk_conclusion")
    def _check_conclusion_recorded(self):
        """Require an overall conclusion before approval."""
        for record in self:
            if (
                record.state == "approved"
                and not record.overall_benefit_risk_conclusion
            ):
                raise ValidationError(
                    self.env._(
                        "Record the overall benefit-risk conclusion of risk "
                        "management file '%(name)s' before approving it.",
                        name=record.name or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the file reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.risk_assessment"
                ) or self.env._("RMF/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the technical content of an approved file."""
        protected = {
            "title",
            "scope",
            "risk_policy",
            "device_id",
            "version",
            "overall_benefit_risk_conclusion",
            "overall_risk_acceptable",
        }
        if protected.intersection(vals):
            for record in self:
                if record.state == "approved":
                    raise UserError(
                        self.env._(
                            "Risk management file '%(name)s' is approved. "
                            "Create a new version to record further changes.",
                            name=record.name or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_risk_assessment(self):
        """Prevent deletion of approved or superseded files."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' can no longer be "
                        "deleted. Cancel it instead.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Create the next version of the file when duplicating."""
        default = dict(default or {})
        default.setdefault("name", self.env._("New"))
        default.setdefault("state", "draft")
        default.setdefault("approver_id", False)
        default.setdefault("approval_date", False)
        if len(self) == 1:
            default.setdefault("version", self.version + 1)
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
                    "Approving a risk management file requires the Medical "
                    "Devices Regulatory Affairs or Manager access level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft file to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft risk management file can be submitted "
                        "for review."
                    )
                )
            if not record.risk_item_ids:
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' contains no risk. "
                        "Record at least one risk before submitting it.",
                        name=record.name or "",
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the risk management file.

        Approval is refused while any residual risk is recorded as
        unacceptable, or while any risk lacks a control measure. Both
        conditions represent an incomplete risk control activity.
        """
        self._check_approval_authority()
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a risk management file under review can be "
                        "approved."
                    )
                )
            if record.responsible_id == self.env.user:
                raise UserError(
                    self.env._(
                        "The person responsible for '%(name)s' cannot approve it "
                        "(segregation of duties).",
                        name=record.display_name or "",
                    )
                )
            if record.unacceptable_risk_count:
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' contains %(count)s "
                        "residual risk(s) evaluated as unacceptable.",
                        name=record.name or "",
                        count=record.unacceptable_risk_count,
                    )
                )
            if record.uncontrolled_risk_count:
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' contains %(count)s "
                        "risk(s) without a recorded control measure.",
                        name=record.name or "",
                        count=record.uncontrolled_risk_count,
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
        """Mark an approved file as superseded by a later version."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved risk management file can be "
                        "superseded."
                    )
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel a file that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' is already closed.",
                        name=record.name or "",
                    )
                )
            record.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        """Return a file under review to draft."""
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a risk management file under review can be "
                        "returned to draft."
                    )
                )
            record.state = "draft"
        return True
