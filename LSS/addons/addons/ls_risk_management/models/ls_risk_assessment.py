# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Risk assessment.

An assessment records one estimation of a risk: the severity of harm and the
probability of its occurrence, evaluated against the acceptability criteria
held on the risk matrix. Supports the risk estimation of ISO 14971:2019
clause 5.5 and the risk evaluation of clause 6.

Detectability is intentionally absent from this model: it is an FMEA
construct and is held on ``ls.risk.fmea.line``.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsRiskAssessment(models.Model):
    """One dated, approvable estimation and evaluation of a risk."""

    _name = "ls.risk.assessment"
    _description = "Risk Assessment"
    _inherit = ["mail.thread", "ls.risk.role.mixin"]
    _order = "assessment_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=constants.SEQUENCE_PLACEHOLDER,
        index=True,
    )
    risk_id = fields.Many2one(comodel_name="ls.risk.register", required=True,
                              ondelete="cascade",
                              index=True,
                              tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="risk_id.company_id",
                                 store=True,
                                 readonly=True,
                                 index=True,)
    assessment_type = fields.Selection(selection=constants.ASSESSMENT_TYPES, required=True,
                                       default="initial",
                                       tracking=True,)
    matrix_id = fields.Many2one(
        comodel_name="ls.risk.matrix",
        string="Risk Matrix",
        required=True,
        readonly=True,
        help="Copied from the risk when the assessment is created, so that "
        "historical assessments remain interpretable after the risk is "
        "re-pointed at a revised matrix.",
    )
    severity_level_id = fields.Many2one(
        comodel_name="ls.risk.matrix.level",
        string="Severity",
        required=True,
        domain="[('matrix_id', '=', matrix_id), ('scale', '=', 'severity')]",
        tracking=True,
    )
    probability_level_id = fields.Many2one(
        comodel_name="ls.risk.matrix.level",
        string="Probability",
        required=True,
        domain="[('matrix_id', '=', matrix_id), ('scale', '=', 'probability')]",
        tracking=True,
    )
    severity_value = fields.Integer(related="severity_level_id.value",
                                    store=True,
                                    readonly=True,)
    probability_value = fields.Integer(related="probability_level_id.value",
                                       store=True,
                                       readonly=True,)
    matrix_cell_id = fields.Many2one(comodel_name="ls.risk.matrix.cell", compute="_compute_evaluation",
                                     store=True,)
    risk_level = fields.Selection(selection=constants.RISK_LEVELS, compute="_compute_evaluation",
                                  store=True,
                                  tracking=True,
                                  index=True,)
    acceptability = fields.Selection(selection=constants.ACCEPTABILITY, compute="_compute_evaluation",
                                     store=True,
                                     tracking=True,
                                     index=True,)
    ordinal_index = fields.Integer(compute="_compute_evaluation",
                                   store=True,
                                   help="Product of the severity and probability ordinal values. This is "
                                   "a sorting convenience only. It is not a normative risk measure of "
                                   "ISO 14971:2019 and must not be used as an acceptability criterion; "
                                   "acceptability comes from the matrix cell.",)
    estimation_rationale = fields.Text(help="Objective basis for the severity and probability selected.",)
    assessed_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    assessment_date = fields.Date(required=True,
                                  default=fields.Date.context_today,
                                  tracking=True,)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    state = fields.Selection(
        selection=constants.ASSESSMENT_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)
    note = fields.Text(string="Notes")

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The assessment reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "severity_value",
        "probability_value",
        "matrix_id",
        "matrix_id.cell_ids.risk_level",
        "matrix_id.cell_ids.acceptability",
    )
    def _compute_evaluation(self):
        """Resolve the matrix cell and copy its evaluation onto the record."""
        for assessment in self:
            cell = self.env["ls.risk.matrix.cell"]
            if assessment.matrix_id and assessment.severity_value and assessment.probability_value:
                cell = assessment.matrix_id.get_cell(
                    assessment.severity_value, assessment.probability_value
                )
            assessment.matrix_cell_id = cell
            assessment.risk_level = cell.risk_level if cell else False
            assessment.acceptability = cell.acceptability if cell else False
            assessment.ordinal_index = (
                assessment.severity_value * assessment.probability_value
            )

    @api.depends("name", "risk_id.name", "assessment_type")
    def _compute_display_name(self):
        """Show the assessment reference and its type."""
        types = dict(constants.ASSESSMENT_TYPES)
        for assessment in self:
            label = types.get(assessment.assessment_type, assessment.assessment_type)
            assessment.display_name = f"{assessment.name} ({label})"

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("risk_id")
    def _onchange_risk_id(self):
        """Copy the matrix from the risk and clear incompatible levels."""
        if self.risk_id:
            self.matrix_id = self.risk_id.matrix_id
        if self.severity_level_id.matrix_id != self.matrix_id:
            self.severity_level_id = False
        if self.probability_level_id.matrix_id != self.matrix_id:
            self.probability_level_id = False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("severity_level_id", "probability_level_id", "matrix_id")
    def _check_levels_belong_to_matrix(self):
        """Ensure both levels come from the assessment's matrix and scale."""
        for assessment in self:
            if assessment.severity_level_id.matrix_id != assessment.matrix_id:
                raise ValidationError(
                    self.env._(
                        "The severity level of %(name)s must belong to matrix "
                        "%(matrix)s.",
                        name=assessment.name,
                        matrix=assessment.matrix_id.display_name,
                    )
                )
            if assessment.probability_level_id.matrix_id != assessment.matrix_id:
                raise ValidationError(
                    self.env._(
                        "The probability level of %(name)s must belong to matrix "
                        "%(matrix)s.",
                        name=assessment.name,
                        matrix=assessment.matrix_id.display_name,
                    )
                )
            if assessment.severity_level_id.scale != "severity":
                raise ValidationError(
                    self.env._("The severity field must reference a severity level.")
                )
            if assessment.probability_level_id.scale != "probability":
                raise ValidationError(
                    self.env._(
                        "The probability field must reference a probability level."
                    )
                )

    @api.constrains("risk_id", "assessment_type", "state")
    def _check_single_initial_assessment(self):
        """Allow at most one non-cancelled initial assessment per risk."""
        for assessment in self:
            if assessment.assessment_type != "initial" or assessment.state == "cancelled":
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", assessment.id),
                    ("risk_id", "=", assessment.risk_id.id),
                    ("assessment_type", "=", "initial"),
                    ("state", "!=", "cancelled"),
                ]
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "Risk %(name)s already has an initial assessment. Record "
                        "later estimations as Residual, Periodic Review or "
                        "Production / Post-Production Information.",
                        name=assessment.risk_id.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the reference and inherit the matrix from the risk.

        :param list vals_list: list of field value dictionaries.
        :return: the created records.
        :rtype: :class:`odoo.models.Model`
        """
        risk_model = self.env["ls.risk.register"]
        for vals in vals_list:
            if not vals.get("matrix_id") and vals.get("risk_id"):
                vals["matrix_id"] = risk_model.browse(vals["risk_id"]).matrix_id.id
            if vals.get("name", constants.SEQUENCE_PLACEHOLDER) == constants.SEQUENCE_PLACEHOLDER:
                company_id = (
                    risk_model.browse(vals["risk_id"]).company_id.id
                    if vals.get("risk_id")
                    else self.env.company.id
                )
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code(constants.SEQUENCE_ASSESSMENT)
                    or constants.SEQUENCE_PLACEHOLDER
                )
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modification of the estimation once approved.

        :param dict vals: field values to write.
        :raise UserError: when an approved assessment's estimation is edited.
        :return: ``True`` when the write succeeded.
        :rtype: bool
        """
        protected = {
            "severity_level_id",
            "probability_level_id",
            "assessment_type",
            "matrix_id",
            "assessed_by_id",
            "assessment_date",
            "estimation_rationale",
        }
        if protected.intersection(vals):
            locked = self.filtered(lambda a: a.state == "approved")
            if locked:
                raise UserError(
                    self.env._(
                        "An approved assessment cannot be modified because it "
                        "forms part of the risk management file. Cancel it and "
                        "record a new assessment instead. Blocked references: "
                        "%(refs)s",
                        refs=", ".join(locked.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_risk_assessment(self):
        """Restrict deletion to draft assessments.

        :raise UserError: when any record has left the draft state.
        :return: ``True`` when deletion succeeded.
        :rtype: bool
        """
        blocked = self.filtered(lambda a: a.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Only draft assessments can be deleted. Cancel the others "
                    "instead. Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        """Confirm the estimation and submit it for approval.

        :raise UserError: when the assessment is not in draft, has no
            rationale, or falls outside the matrix grid.
        :return: ``True`` when all records were confirmed.
        :rtype: bool
        """
        for assessment in self:
            if assessment.state != "draft":
                raise UserError(
                    self.env._("Only a draft assessment can be confirmed.")
                )
            if not (assessment.estimation_rationale or "").strip():
                raise UserError(
                    self.env._(
                        "Record the estimation rationale for %(name)s before "
                        "confirming it.",
                        name=assessment.name,
                    )
                )
            if not assessment.matrix_cell_id:
                raise UserError(
                    self.env._(
                        "Matrix %(matrix)s does not define a cell for severity "
                        "%(severity)s and probability %(probability)s. Complete "
                        "the matrix before confirming assessment %(name)s.",
                        matrix=assessment.matrix_id.display_name,
                        severity=assessment.severity_value,
                        probability=assessment.probability_value,
                        name=assessment.name,
                    )
                )
            assessment.state = "confirmed"
        return True

    def action_approve(self):
        """Approve a confirmed assessment.

        Segregation of duties is enforced at ORM level: the approver may not
        be the person who performed the assessment.

        :raise UserError: when the assessment is not confirmed, when the
            approver performed the assessment, or when the matrix is not
            approved.
        :return: ``True`` when all records were approved.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("approve a risk assessment"))
        for assessment in self:
            if assessment.state != "confirmed":
                raise UserError(
                    self.env._("Only a confirmed assessment can be approved.")
                )
            if assessment.assessed_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Segregation of duties: %(user)s performed assessment "
                        "%(name)s and therefore cannot approve it.",
                        user=self.env.user.display_name,
                        name=assessment.name,
                    )
                )
            if assessment.matrix_id.state != "approved":
                raise UserError(
                    self.env._(
                        "Risk matrix %(matrix)s is not approved, so assessment "
                        "%(name)s cannot be approved.",
                        matrix=assessment.matrix_id.display_name,
                        name=assessment.name,
                    )
                )
            assessment.write(
                {
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
            assessment.risk_id.write(
                {"last_review_date": fields.Date.context_today(assessment)}
            )
        return True

    def action_open_cancel_wizard(self):
        """Open the assessment cancellation wizard.

        :return: an action opening the cancellation wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Assessments"),
            "res_model": "ls.risk.assessment.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_assessment_ids": self.ids},
        }

    def action_reset_to_draft(self):
        """Return a confirmed assessment to draft for correction.

        :raise UserError: when the assessment is not confirmed.
        :return: ``True`` when all records were reset.
        :rtype: bool
        """
        for assessment in self:
            if assessment.state != "confirmed":
                raise UserError(
                    self.env._(
                        "Only a confirmed assessment can be returned to Draft. "
                        "An approved assessment must be cancelled instead."
                    )
                )
            assessment.state = "draft"
        return True
