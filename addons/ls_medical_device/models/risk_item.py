# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Individual risk within a risk management file.

Each record carries the chain described by ISO 14971:2019: a hazard, the
foreseeable sequence of events leading to a hazardous situation, the resulting
harm, the initial risk estimate, the risk control measure applied, the residual
risk estimate after that measure, the verification of the implementation and
effectiveness of the measure, and an assessment of whether the measure
introduced a new hazard.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdRiskItem(models.Model):
    """One hazard-to-residual-risk record."""

    _name = "ls.md.risk_item"
    _description = "Medical Device Risk"
    _order = "risk_assessment_id, sequence, id"

    sequence = fields.Integer(default=10)
    risk_assessment_id = fields.Many2one(
        comodel_name="ls.md.risk_assessment",
        string="Risk Management File",
        required=True,
        ondelete="cascade",
        index=True,
    )
    device_id = fields.Many2one(comodel_name="ls.md.device", related="risk_assessment_id.device_id",
                                store=True,
                                index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="risk_assessment_id.company_id",
                                 store=True,
                                 index=True,)
    reference = fields.Char(
        string="Risk Identifier",
        required=True,
        help="Identifier of the risk within the risk management file.",
    )
    hazard = fields.Text(required=True,
                         help="Potential source of harm.",)
    hazard_category = fields.Char(help=(
            "Category of the hazard as used by the organisation, for example "
            "an energy, biological, environmental or use-related hazard."),
    )
    sequence_of_events = fields.Text(
        string="Foreseeable Sequence of Events",
        help="Sequence of events that leads from the hazard to exposure.",
    )
    hazardous_situation = fields.Text(required=True,
                                      help="Circumstance in which people, property or the environment are exposed.",)
    harm = fields.Text(required=True,
                       help="Injury or damage to health that can result from the hazardous situation.",)
    affected_party = fields.Char(help="Party exposed to the harm, for example patient, user or third party.",)

    # ------------------------------------------------------------------
    # Initial risk estimate
    # ------------------------------------------------------------------
    initial_severity = fields.Selection(selection=constants.RISK_SEVERITY_SELECTION, required=True,
                                        default="3",)
    initial_probability = fields.Selection(selection=constants.RISK_PROBABILITY_SELECTION, required=True,
                                           default="3",)
    initial_index = fields.Integer(
        string="Initial Risk Index",
        compute="_compute_initial_index",
        store=True,
        help="Product of the initial severity and the initial probability.",
    )

    # ------------------------------------------------------------------
    # Risk control
    # ------------------------------------------------------------------
    control_option = fields.Selection(selection=constants.RISK_CONTROL_OPTION_SELECTION, help=(
            "Category of the risk control measure. ISO 14971:2019 requires "
            "control options to be considered in the order in which they are "
            "listed here."),
    )
    control_measure = fields.Text(
        string="Risk Control Measure",
        help="Description of the measure applied to reduce the risk.",
    )
    control_implementation_reference = fields.Char(
        string="Implementation Evidence",
        help=(
            "Reference of the record demonstrating that the measure has been "
            "implemented, for example a drawing, specification or test report."
        ),
    )
    control_verification_reference = fields.Char(
        string="Effectiveness Evidence",
        help=(
            "Reference of the record demonstrating that the measure is "
            "effective."
        ),
    )
    control_verified = fields.Boolean(
        string="Effectiveness Verified",
        help="The effectiveness of the risk control measure has been verified.",
    )
    introduces_new_hazard = fields.Boolean(
        string="Introduces a New Hazard",
        help=(
            "The risk control measure introduces a new hazard or increases an "
            "existing risk, which must itself be assessed."
        ),
    )
    new_hazard_description = fields.Text(help="Description of the hazard introduced by the risk control measure.",)

    # ------------------------------------------------------------------
    # Residual risk
    # ------------------------------------------------------------------
    residual_severity = fields.Selection(selection=constants.RISK_SEVERITY_SELECTION, required=True,
                                         default="3",)
    residual_probability = fields.Selection(selection=constants.RISK_PROBABILITY_SELECTION, required=True,
                                            default="3",)
    residual_index = fields.Integer(
        string="Residual Risk Index",
        compute="_compute_residual_index",
        store=True,
        help="Product of the residual severity and the residual probability.",
    )
    proposed_acceptability = fields.Selection(selection=constants.RISK_ACCEPTABILITY_SELECTION, compute="_compute_proposed_acceptability",
                                              store=True,
                                              help=(
                                                  "Acceptability proposed by the shipped default matrix. The "
                                                  "proposal is informative; the recorded decision is the one held in "
                                                  "the residual acceptability field."),
                                              )
    residual_acceptability = fields.Selection(selection=constants.RISK_ACCEPTABILITY_SELECTION, required=True,
                                              default="alarp",
                                              help=(
                                                  "Acceptability decision recorded by the organisation against its "
                                                  "own risk acceptability criteria."),
                                              )
    acceptability_justification = fields.Text(help="Justification of the recorded acceptability decision.",)
    disclosed_to_user = fields.Boolean(
        string="Residual Risk Disclosed",
        help="The residual risk is disclosed in the information for safety.",
    )
    notes = fields.Text()

    _reference_unique = models.Constraint(
        "UNIQUE(risk_assessment_id, reference)",
        "The risk identifier must be unique within a risk management file.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("initial_severity", "initial_probability")
    def _compute_initial_index(self):
        """Multiply the initial severity by the initial probability."""
        for record in self:
            record.initial_index = int(record.initial_severity or 0) * int(
                record.initial_probability or 0
            )

    @api.depends("residual_severity", "residual_probability")
    def _compute_residual_index(self):
        """Multiply the residual severity by the residual probability."""
        for record in self:
            record.residual_index = int(record.residual_severity or 0) * int(
                record.residual_probability or 0
            )

    @api.depends("residual_index")
    def _compute_proposed_acceptability(self):
        """Propose an acceptability band from the shipped default matrix."""
        for record in self:
            index = record.residual_index
            if index >= constants.RISK_INDEX_UNACCEPTABLE_FROM:
                record.proposed_acceptability = "unacceptable"
            elif index < constants.RISK_INDEX_ACCEPTABLE_BELOW:
                record.proposed_acceptability = "acceptable"
            else:
                record.proposed_acceptability = "alarp"

    @api.depends("reference", "hazard")
    def _compute_display_name(self):
        """Show the risk identifier and the beginning of the hazard text."""
        for record in self:
            hazard = (record.hazard or "").splitlines()
            summary = hazard[0][:60] if hazard else ""
            record.display_name = f"{record.reference or ''} {summary}".strip()

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains(
        "initial_severity",
        "initial_probability",
        "residual_severity",
        "residual_probability",
    )
    def _check_residual_not_worse_than_initial(self):
        """Reject a residual risk estimate above the initial estimate.

        A risk control measure cannot increase the risk it addresses. Where a
        measure introduces a new hazard, that hazard is recorded as a separate
        risk rather than by raising the residual estimate of this one.
        """
        for record in self:
            if record.residual_index > record.initial_index:
                raise ValidationError(
                    self.env._(
                        "Risk '%(reference)s': the residual risk index "
                        "(%(residual)s) cannot exceed the initial risk index "
                        "(%(initial)s). Record a hazard introduced by the "
                        "control measure as a separate risk.",
                        reference=record.reference or "",
                        residual=record.residual_index,
                        initial=record.initial_index,
                    )
                )

    @api.constrains("introduces_new_hazard", "new_hazard_description")
    def _check_new_hazard_description(self):
        """Require a description when a new hazard is flagged."""
        for record in self:
            if record.introduces_new_hazard and not record.new_hazard_description:
                raise ValidationError(
                    self.env._(
                        "Risk '%(reference)s' is flagged as introducing a new "
                        "hazard. Describe that hazard.",
                        reference=record.reference or "",
                    )
                )

    @api.constrains("residual_acceptability", "acceptability_justification")
    def _check_acceptability_justification(self):
        """Require a justification when the decision differs from the proposal."""
        for record in self:
            if (
                record.proposed_acceptability
                and record.residual_acceptability != record.proposed_acceptability
                and not record.acceptability_justification
            ):
                raise ValidationError(
                    self.env._(
                        "Risk '%(reference)s': the recorded acceptability "
                        "differs from the value proposed by the risk matrix. "
                        "Record a justification.",
                        reference=record.reference or "",
                    )
                )

    @api.constrains("residual_acceptability", "control_measure")
    def _check_control_measure_present(self):
        """Require a control measure whenever risk reduction was applied."""
        for record in self:
            if record.residual_index < record.initial_index and not (
                record.control_measure
            ):
                raise ValidationError(
                    self.env._(
                        "Risk '%(reference)s' shows a reduced residual risk "
                        "but records no risk control measure.",
                        reference=record.reference or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    def _check_parent_editable(self):
        """Raise when the parent risk management file is no longer editable."""
        for record in self:
            parent = record.risk_assessment_id
            if parent and parent.state != "draft":
                raise UserError(
                    self.env._(
                        "Risk management file '%(name)s' is closed for "
                        "editing. Create a new version to change its risks.",
                        name=parent.name or "",
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Reject the creation of a risk in a closed file."""
        records = super().create(vals_list)
        records._check_parent_editable()
        return records

    def write(self, vals):
        """Reject changes to a risk held in a closed file."""
        self._check_parent_editable()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_risk_item(self):
        """Reject deletion of a risk held in a closed file."""
        self._check_parent_editable()
