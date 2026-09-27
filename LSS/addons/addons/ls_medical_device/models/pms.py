# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Post-market surveillance plans.

Article 83 of Regulation (EU) 2017/745 requires manufacturers to plan,
establish, document, implement, maintain and update a post-market surveillance
system proportionate to the risk class and appropriate for the type of device.
Article 84 requires that system to be based on a post-market surveillance plan
whose requirements are set out in Section 1.1 of Annex III. For devices other
than custom-made devices, the plan forms part of the technical documentation
specified in Annex II.

Section 1.1 of Annex III requires the plan to address, among other elements,
the collection and utilisation of available information, a proactive and
systematic process to collect that information, reference to the procedures
that fulfil the obligations of Articles 83, 84 and 86, systematic procedures to
identify and initiate appropriate measures including corrective actions,
effective tools to trace and identify devices for which corrective actions might
be necessary, and a post-market clinical follow-up plan as referred to in Part B
of Annex XIV or a justification as to why such follow-up is not applicable.

The fields below mirror those elements so that a plan can be shown to address
each of them.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdPms(models.Model):
    """Post-market surveillance plan for one device."""

    _name = "ls.md.pms"
    _description = "Post-Market Surveillance Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "device_id, version desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    title = fields.Char(required=True, tracking=True)
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,)
    version = fields.Integer(default=1, required=True, tracking=True)
    state = fields.Selection(
        selection=constants.REGULATORY_DOC_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    effective_date = fields.Date(string="Effective From", tracking=True)
    responsible_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                     tracking=True,)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    # ------------------------------------------------------------------
    # Elements required by Annex III Section 1.1
    # ------------------------------------------------------------------
    information_sources = fields.Text(help=(
            "Sources of information the plan collects, for example serious "
            "incidents and field safety corrective actions, records of "
            "non-serious incidents and undesirable side-effects, trend data, "
            "specialist literature, feedback and complaints from users, "
            "distributors and importers, and publicly available information on "
            "similar devices."),
    )
    collection_process = fields.Text(
        string="Proactive Collection Process",
        help=(
            "The proactive and systematic process used to collect the "
            "information listed above."
        ),
    )
    indicators_and_thresholds = fields.Text(help=(
            "Indicators and threshold values used in the continuous "
            "reassessment of the benefit-risk determination and in risk "
            "management."),
    )
    analysis_methods = fields.Text(help="Methods and tools used to investigate complaints and analyse experience.",)
    communication_methods = fields.Text(help=(
            "Methods and protocols used to communicate with competent "
            "authorities, notified bodies, economic operators and users."),
    )
    referenced_procedures = fields.Text(help=(
            "Reference to the procedures that fulfil the obligations laid down "
            "in Articles 83, 84 and 86."),
    )
    corrective_action_process = fields.Text(help=(
            "Systematic procedures to identify and initiate appropriate "
            "measures, including corrective actions."),
    )
    traceability_tools = fields.Text(help=(
            "Effective tools used to trace and identify devices for which "
            "corrective actions might be necessary."),
    )
    pmcf_plan_included = fields.Boolean(default=True,
                                        tracking=True,
                                        help=(
                                            "Section 1.1 of Annex III requires a post-market clinical "
                                            "follow-up plan as referred to in Part B of Annex XIV, or a "
                                            "justification as to why such follow-up is not applicable."),
                                        )
    pmcf_plan_reference = fields.Char(help="Reference of the post-market clinical follow-up plan.",)
    pmcf_not_applicable_justification = fields.Text(
        string="Justification for PMCF Not Applicable",
    )

    # ------------------------------------------------------------------
    # Reporting obligations derived from the device
    # ------------------------------------------------------------------
    periodic_report_type = fields.Selection(selection=constants.PERIODIC_REPORT_TYPE_SELECTION, related="device_id.periodic_report_type",
                                            store=True,
                                            help="Derived from the risk class of the device.",)
    periodic_report_interval_months = fields.Integer(
        string="Report Interval (Months)",
        related="device_id.periodic_report_interval_months",
        store=True,
    )
    report_ids = fields.One2many(
        comodel_name="ls.md.pms_report",
        inverse_name="pms_id",
        string="Periodic Reports",
    )
    report_count = fields.Integer(compute="_compute_report_count")
    review_frequency_months = fields.Integer(
        string="Plan Review Frequency (Months)",
        default=12,
        help="Interval at which the plan itself is reviewed.",
    )
    next_review_date = fields.Date(string="Next Plan Review", tracking=True)
    notes = fields.Text()

    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The post-market surveillance plan version must be strictly positive.",
    )
    _device_version_unique = models.Constraint(
        "UNIQUE(device_id, version)",
        "A device cannot have two surveillance plans with the same version.",
    )
    _review_frequency_non_negative = models.Constraint(
        "CHECK(review_frequency_months >= 0)",
        "The plan review frequency cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("report_ids")
    def _compute_report_count(self):
        """Count the periodic reports issued under each plan."""
        for record in self:
            record.report_count = len(record.report_ids)

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
    @api.constrains(
        "pmcf_plan_included",
        "pmcf_plan_reference",
        "pmcf_not_applicable_justification",
    )
    def _check_pmcf_element(self):
        """Require either a PMCF plan reference or a justification."""
        for record in self:
            if record.pmcf_plan_included and not record.pmcf_plan_reference:
                raise ValidationError(
                    self.env._(
                        "Plan '%(name)s' declares a post-market clinical "
                        "follow-up plan but records no reference for it.",
                        name=record.name or "",
                    )
                )
            if (
                not record.pmcf_plan_included
                and not record.pmcf_not_applicable_justification
            ):
                raise ValidationError(
                    self.env._(
                        "Plan '%(name)s' omits the post-market clinical "
                        "follow-up plan but records no justification, which "
                        "Section 1.1 of Annex III requires.",
                        name=record.name or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the plan reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.pms"
                ) or self.env._("PMS/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the content of an approved plan."""
        protected = {
            "title",
            "device_id",
            "version",
            "information_sources",
            "collection_process",
            "indicators_and_thresholds",
            "referenced_procedures",
            "corrective_action_process",
            "traceability_tools",
            "pmcf_plan_included",
        }
        if protected.intersection(vals):
            for record in self:
                if record.state == "approved":
                    raise UserError(
                        self.env._(
                            "Surveillance plan '%(name)s' is approved. Create "
                            "a new version to record further changes.",
                            name=record.name or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_pms(self):
        """Prevent deletion of approved or superseded plans."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "Surveillance plan '%(name)s' can no longer be "
                        "deleted. Cancel it instead.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Create the next version of the plan when duplicating."""
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
                    "Approving a surveillance plan requires the Medical "
                    "Devices Regulatory Affairs or Manager access level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft plan to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft surveillance plan can be submitted for "
                        "review."
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the plan once its mandatory elements are recorded."""
        self._check_approval_authority()
        mandatory = (
            ("information_sources", self.env._("information sources")),
            ("collection_process", self.env._("proactive collection process")),
            ("referenced_procedures", self.env._("referenced procedures")),
            ("corrective_action_process", self.env._("corrective action process")),
            ("traceability_tools", self.env._("traceability tools")),
        )
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a surveillance plan under review can be "
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
            missing = [
                label
                for field_name, label in mandatory
                if not record[field_name]
            ]
            if missing:
                raise UserError(
                    self.env._(
                        "Surveillance plan '%(name)s' does not record the "
                        "following elements required by Section 1.1 of Annex "
                        "III: %(missing)s.",
                        name=record.name or "",
                        missing=", ".join(missing),
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
        """Mark an approved plan as superseded."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._("Only an approved surveillance plan can be superseded.")
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel a plan that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "Surveillance plan '%(name)s' is already closed.",
                        name=record.name or "",
                    )
                )
            record.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        """Return a plan under review to draft."""
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a surveillance plan under review can be returned "
                        "to draft."
                    )
                )
            record.state = "draft"
        return True

    def action_view_reports(self):
        """Open the periodic reports issued under the plan."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Periodic Reports"),
            "res_model": "ls.md.pms_report",
            "view_mode": "list,form",
            "domain": [("pms_id", "=", self.id)],
            "context": {
                "default_pms_id": self.id,
                "default_device_id": self.device_id.id,
            },
        }
