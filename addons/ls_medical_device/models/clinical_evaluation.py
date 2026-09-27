# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Clinical evaluation records.

Article 61 of Regulation (EU) 2017/745 requires the manufacturer to plan,
conduct and document a clinical evaluation in accordance with Part A of Annex
XIV. Article 61(12) requires the evaluation, its results and the clinical
evidence derived from it to be documented in a clinical evaluation report which,
except for custom-made devices, forms part of the technical documentation
referred to in Annex II.

Article 61(11) requires the clinical evaluation and its documentation to be
updated throughout the life cycle of the device with clinical data obtained from
the implementation of the post-market clinical follow-up plan drawn up under
Part B of Annex XIV and from the post-market surveillance plan of Article 84.

This model covers the clinical evaluation plan and report as a single
controlled record with distinct sections, because the two documents share one
approval cycle in most quality systems. The post-market clinical follow-up
evaluation report is held separately on ``ls.md.pmcf_evaluation`` because it has
its own update frequency.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdClinicalEvaluation(models.Model):
    """Clinical evaluation plan and report for one device."""

    _name = "ls.md.clinical_evaluation"
    _description = "Medical Device Clinical Evaluation"
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
    evaluator_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                   tracking=True,)
    evaluator_qualification = fields.Text(help=(
            "Record of the qualification of the person or persons who carried "
            "out the clinical evaluation."),
    )
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    # ------------------------------------------------------------------
    # Clinical evaluation plan (Annex XIV Part A)
    # ------------------------------------------------------------------
    plan_scope = fields.Text(help="Scope of the clinical evaluation defined in the evaluation plan.",)
    gspr_requiring_clinical_data = fields.Text(
        string="Requirements Supported by Clinical Data",
        help=(
            "Identification of the general safety and performance requirements "
            "that require support from relevant clinical data, as required by "
            "Part A of Annex XIV."
        ),
    )
    intended_clinical_benefits = fields.Text(help="Clinical benefits claimed for the device, with measurable outcomes.",)
    target_population = fields.Text(help="Indications and target population covered by the evaluation.",)
    acceptance_criteria = fields.Text(help=(
            "Criteria against which the benefit-risk ratio is assessed for the "
            "indications and intended purpose of the device."),
    )
    literature_search_protocol = fields.Text(help="Search strategy, inclusion and exclusion criteria, and appraisal method.",)

    # ------------------------------------------------------------------
    # Clinical evidence
    # ------------------------------------------------------------------
    evidence_source_ids = fields.Many2many(
        comodel_name="ls.md.clinical_evidence_source",
        string="Clinical Evidence Sources",
        help="Kinds of clinical evidence relied on in this evaluation.",
    )
    equivalence_claimed = fields.Boolean(tracking=True,
                                         help="Clinical data from an equivalent device is relied on.",)
    equivalent_device_description = fields.Text(
        string="Equivalent Device",
        help="Identification of the device claimed to be equivalent.",
    )
    equivalence_demonstration = fields.Text(help=(
            "Demonstration of technical, biological and clinical equivalence, "
            "together with the basis for access to the underlying data."),
    )
    clinical_investigation_performed = fields.Boolean(tracking=True,)
    clinical_investigation_reference = fields.Char(help="Identifier of the clinical investigation supporting the evaluation.",)
    clinical_investigation_justification = fields.Text(
        string="Justification for Not Performing an Investigation",
        help=(
            "Justification recorded when no clinical investigation was carried "
            "out for a device for which one would normally be expected."
        ),
    )

    # ------------------------------------------------------------------
    # Clinical evaluation report (Annex XIV Part A, Section 4)
    # ------------------------------------------------------------------
    data_appraisal = fields.Text(
        string="Appraisal of Clinical Data",
        help="Assessment of the suitability and quality of the clinical data.",
    )
    data_analysis = fields.Text(
        string="Analysis of Clinical Data",
        help="Analysis of the clinical data against the acceptance criteria.",
    )
    benefit_risk_conclusion = fields.Text(
        string="Benefit-Risk Conclusion",
        tracking=True,
        help=(
            "Conclusion on the acceptability of the benefit-risk ratio and on "
            "any undesirable side-effects."
        ),
    )
    conformity_confirmed = fields.Boolean(
        string="Conformity With Requirements Confirmed",
        tracking=True,
        help=(
            "Records the conclusion that the device meets the applicable "
            "general safety and performance requirements under normal "
            "conditions of intended use."
        ),
    )
    residual_gaps = fields.Text(
        string="Residual Gaps in Clinical Evidence",
        help="Gaps carried forward into the post-market clinical follow-up plan.",
    )

    # ------------------------------------------------------------------
    # Post-market clinical follow-up plan (Annex XIV Part B)
    # ------------------------------------------------------------------
    pmcf_applicable = fields.Boolean(default=True,
                                     tracking=True,
                                     help=(
                                         "Part B of Annex XIV expects a post-market clinical follow-up "
                                         "plan. Uncheck only where a device-specific justification is "
                                         "recorded below."),
                                     )
    pmcf_plan_summary = fields.Text(help="Objectives, methods and schedule of the planned PMCF activities.",)
    pmcf_justification = fields.Text(
        string="Justification for Not Applying PMCF",
        help=(
            "Justification recorded when no post-market clinical follow-up "
            "plan is drawn up, as permitted by Section 1.1 of Annex III."
        ),
    )
    next_review_date = fields.Date(
        string="Next Review Due",
        tracking=True,
        help="Planned date of the next update of the clinical evaluation.",
    )
    pmcf_evaluation_ids = fields.One2many(
        comodel_name="ls.md.pmcf_evaluation",
        inverse_name="clinical_evaluation_id",
        string="PMCF Evaluation Reports",
    )
    notes = fields.Text()

    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The clinical evaluation version must be strictly positive.",
    )
    _device_version_unique = models.Constraint(
        "UNIQUE(device_id, version)",
        "A device cannot have two clinical evaluations with the same version.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
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
    @api.constrains("equivalence_claimed", "equivalence_demonstration")
    def _check_equivalence_demonstration(self):
        """Require a demonstration whenever equivalence is claimed."""
        for record in self:
            if record.equivalence_claimed and not record.equivalence_demonstration:
                raise ValidationError(
                    self.env._(
                        "Clinical evaluation '%(name)s' claims equivalence but "
                        "records no equivalence demonstration.",
                        name=record.name or "",
                    )
                )

    @api.constrains(
        "pmcf_applicable", "pmcf_plan_summary", "pmcf_justification", "state"
    )
    def _check_pmcf_documentation(self):
        """Require either a PMCF plan summary or a justification.

        The requirement applies from the submission for review onwards, so
        that a draft evaluation can be created and completed step by step.
        """
        for record in self:
            if record.state == "draft":
                continue
            if record.pmcf_applicable and not record.pmcf_plan_summary:
                raise ValidationError(
                    self.env._(
                        "Clinical evaluation '%(name)s' declares post-market "
                        "clinical follow-up applicable but records no plan "
                        "summary.",
                        name=record.name or "",
                    )
                )
            if not record.pmcf_applicable and not record.pmcf_justification:
                raise ValidationError(
                    self.env._(
                        "Clinical evaluation '%(name)s' declares post-market "
                        "clinical follow-up not applicable but records no "
                        "justification.",
                        name=record.name or "",
                    )
                )

    @api.constrains(
        "clinical_investigation_performed",
        "clinical_investigation_reference",
        "clinical_investigation_justification",
        "state",
    )
    def _check_clinical_investigation(self):
        """Require a reference or a justification for the investigation status.

        A declared investigation needs its reference at any time. The
        justification for not performing an investigation is required from
        the submission for review onwards.
        """
        for record in self:
            if (
                record.clinical_investigation_performed
                and not record.clinical_investigation_reference
            ):
                raise ValidationError(
                    self.env._(
                        "Clinical evaluation '%(name)s' declares a clinical "
                        "investigation but records no reference for it.",
                        name=record.name or "",
                    )
                )
            if (
                record.state != "draft"
                and not record.clinical_investigation_performed
                and not record.clinical_investigation_justification
            ):
                raise ValidationError(
                    self.env._(
                        "Clinical evaluation '%(name)s' records no clinical "
                        "investigation: the justification for not performing "
                        "one is required.",
                        name=record.name or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the evaluation reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.clinical_evaluation"
                ) or self.env._("CER/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the technical content of an evaluation in two steps.

        The content prepared by the evaluator is frozen when the evaluation
        is submitted for review; the conclusions are frozen at approval.
        """
        author_content = {
            "title",
            "device_id",
            "version",
            "plan_scope",
            "data_appraisal",
            "data_analysis",
            "equivalence_claimed",
            "equivalence_demonstration",
        }
        review_content = {"benefit_risk_conclusion", "conformity_confirmed"}
        for record in self:
            if author_content.intersection(vals) and record.state != "draft":
                raise UserError(
                    self.env._(
                        "Clinical evaluation '%(name)s' has been submitted. "
                        "Return it to draft or create a new version to change "
                        "its content.",
                        name=record.name or "",
                    )
                )
            if review_content.intersection(vals) and record.state not in (
                "draft",
                "under_review",
            ):
                raise UserError(
                    self.env._(
                        "Clinical evaluation '%(name)s' is approved. "
                        "Create a new version to record further changes.",
                        name=record.name or "",
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_clinical_evaluation(self):
        """Prevent deletion of approved or superseded evaluations."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "Clinical evaluation '%(name)s' can no longer be "
                        "deleted. Cancel it instead.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Create the next version of the evaluation when duplicating."""
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
                    "Approving a clinical evaluation requires the Medical "
                    "Devices Regulatory Affairs or Manager access level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft evaluation to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft clinical evaluation can be submitted "
                        "for review."
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the clinical evaluation."""
        self._check_approval_authority()
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a clinical evaluation under review can be "
                        "approved."
                    )
                )
            if record.evaluator_id == self.env.user:
                raise UserError(
                    self.env._(
                        "The evaluator of clinical evaluation '%(name)s' "
                        "cannot approve it.",
                        name=record.name or "",
                    )
                )
            if not record.benefit_risk_conclusion:
                raise UserError(
                    self.env._(
                        "Record the benefit-risk conclusion of clinical "
                        "evaluation '%(name)s' before approving it.",
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
        """Mark an approved evaluation as superseded."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved clinical evaluation can be "
                        "superseded."
                    )
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel an evaluation that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "Clinical evaluation '%(name)s' is already closed.",
                        name=record.name or "",
                    )
                )
            record.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        """Return an evaluation under review to draft."""
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only a clinical evaluation under review can be "
                        "returned to draft."
                    )
                )
            record.state = "draft"
        return True


class LsMdClinicalEvidenceSource(models.Model):
    """Catalogue of clinical evidence kinds.

    Held as a model rather than a selection so that an organisation can extend
    the catalogue without a code change, which is required because Annex XIV
    Part A does not close the list of admissible data sources.
    """

    _name = "ls.md.clinical_evidence_source"
    _description = "Clinical Evidence Source"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "The clinical evidence source code must be unique.",
    )
