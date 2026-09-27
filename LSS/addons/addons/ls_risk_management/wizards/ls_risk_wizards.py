# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Transient models supporting the risk management workflows.

Every wizard that terminates or reverses a decision requires a written
reason, so that the reason for a state change is part of the record rather
than being inferred from the absence of data.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models import constants


class LsRiskAssessWizard(models.TransientModel):
    """Create one assessment for each of the selected risks."""

    _name = "ls.risk.assess.wizard"
    _description = "Assess Risks"

    risk_ids = fields.Many2many(
        comodel_name="ls.risk.register",
        relation="ls_risk_assess_wizard_risk_rel",
        column1="wizard_id",
        column2="risk_id",
        string="Risks",
        required=True,
    )
    matrix_id = fields.Many2one(
        comodel_name="ls.risk.matrix",
        string="Risk Matrix",
        compute="_compute_matrix_id",
        store=True,
    )
    assessment_type = fields.Selection(selection=constants.ASSESSMENT_TYPES, required=True,
                                       default="initial",)
    severity_level_id = fields.Many2one(
        comodel_name="ls.risk.matrix.level",
        string="Severity",
        required=True,
        domain="[('matrix_id', '=', matrix_id), ('scale', '=', 'severity')]",
    )
    probability_level_id = fields.Many2one(
        comodel_name="ls.risk.matrix.level",
        string="Probability",
        required=True,
        domain="[('matrix_id', '=', matrix_id), ('scale', '=', 'probability')]",
    )
    assessment_date = fields.Date(required=True, default=fields.Date.context_today)
    estimation_rationale = fields.Text(required=True)

    @api.depends("risk_ids")
    def _compute_matrix_id(self):
        """Adopt the shared matrix of the selected risks."""
        for wizard in self:
            matrices = wizard.risk_ids.mapped("matrix_id")
            wizard.matrix_id = matrices if len(matrices) == 1 else False

    def action_create_assessments(self):
        """Create one assessment per selected risk.

        :raise UserError: when the selected risks do not share one matrix.
        :return: an action listing the created assessments.
        :rtype: dict
        """
        self.ensure_one()
        matrices = self.risk_ids.mapped("matrix_id")
        if len(matrices) != 1:
            raise UserError(
                self.env._(
                    "The selected risks use %(count)s different risk matrices. "
                    "Assess risks that share one matrix at a time.",
                    count=len(matrices),
                )
            )
        assessments = self.env["ls.risk.assessment"].create(
            [
                {
                    "risk_id": risk.id,
                    "matrix_id": self.matrix_id.id,
                    "assessment_type": self.assessment_type,
                    "severity_level_id": self.severity_level_id.id,
                    "probability_level_id": self.probability_level_id.id,
                    "assessment_date": self.assessment_date,
                    "estimation_rationale": self.estimation_rationale,
                }
                for risk in self.risk_ids
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Assessments"),
            "res_model": "ls.risk.assessment",
            "view_mode": "list,form",
            "domain": [("id", "in", assessments.ids)],
        }


class LsRiskResidualWizard(models.TransientModel):
    """Record the residual risk acceptance decision for one risk."""

    _name = "ls.risk.residual.wizard"
    _description = "Accept Residual Risk"

    risk_id = fields.Many2one(comodel_name="ls.risk.register", required=True)
    current_risk_level = fields.Selection(selection=constants.RISK_LEVELS, related="risk_id.current_risk_level",
                                          readonly=True,)
    current_acceptability = fields.Selection(selection=constants.ACCEPTABILITY, related="risk_id.current_acceptability",
                                             readonly=True,)
    justification = fields.Text(
        string="Acceptance Justification",
        required=True,
        help="Objective justification for accepting the residual risk, "
        "supporting ISO 14971:2019 clause 7.3.",
    )
    benefit_risk_analysis = fields.Text(
        string="Benefit-Risk Analysis",
        help="Required when the residual risk is not judged acceptable "
        "against the criteria, supporting ISO 14971:2019 clause 7.4.",
    )

    def action_accept(self):
        """Record the acceptance decision on the risk.

        :raise UserError: when no approved assessment exists, when the risk
            already carries an acceptance, or when a benefit-risk analysis is
            required but absent.
        :return: ``True`` when the decision was recorded.
        :rtype: bool
        """
        self.ensure_one()
        risk = self.risk_id
        if not risk.current_assessment_id:
            raise UserError(
                self.env._(
                    "Risk %(name)s has no approved assessment, so its residual "
                    "risk cannot be evaluated.",
                    name=risk.display_name,
                )
            )
        if risk.residual_risk_accepted:
            raise UserError(
                self.env._(
                    "The residual risk of %(name)s has already been accepted by "
                    "%(user)s.",
                    name=risk.display_name,
                    user=risk.residual_risk_accepted_by_id.display_name,
                )
            )
        if risk.current_acceptability == "not_acceptable" and not (
            self.benefit_risk_analysis or ""
        ).strip():
            raise UserError(
                self.env._(
                    "The current acceptability of %(name)s is Not Acceptable. "
                    "Record a benefit-risk analysis before accepting the "
                    "residual risk.",
                    name=risk.display_name,
                )
            )
        values = {
            "residual_risk_accepted": True,
            "residual_risk_accepted_by_id": self.env.user.id,
            "residual_risk_acceptance_date": fields.Datetime.now(),
            "residual_risk_justification": self.justification,
        }
        if (self.benefit_risk_analysis or "").strip():
            values["benefit_risk_analysis"] = self.benefit_risk_analysis
        risk.write(values)
        risk.message_post(
            body=self.env._(
                "Residual risk accepted. Justification: %(text)s",
                text=self.justification,
            )
        )
        return True


class LsRiskCloseWizard(models.TransientModel):
    """Close the selected risks against a recorded reason."""

    _name = "ls.risk.close.wizard"
    _description = "Close Risks"

    risk_ids = fields.Many2many(
        comodel_name="ls.risk.register",
        relation="ls_risk_close_wizard_risk_rel",
        column1="wizard_id",
        column2="risk_id",
        string="Risks",
        required=True,
    )
    closure_reason = fields.Text(required=True)

    def action_close(self):
        """Close each selected risk after checking its evidence.

        :raise UserError: when a risk is not in a closable state, or requires
            a residual risk acceptance decision that has not been recorded.
        :return: ``True`` when all risks were closed.
        :rtype: bool
        """
        self.ensure_one()
        not_closable = self.risk_ids.filtered(
            lambda risk: risk.state not in ("assessed", "control", "monitoring")
        )
        if not_closable:
            raise UserError(
                self.env._(
                    "Only risks in Assessed, Risk Control or Monitoring can be "
                    "closed. Blocked references: %(refs)s",
                    refs=", ".join(not_closable.mapped("name")),
                )
            )
        missing_decision = self.risk_ids.filtered(
            lambda risk: risk._requires_residual_decision()
            and not risk.residual_risk_accepted
        )
        if missing_decision:
            raise UserError(
                self.env._(
                    "The following risks require a recorded residual risk "
                    "acceptance decision before closure: %(refs)s",
                    refs=", ".join(missing_decision.mapped("name")),
                )
            )
        self.risk_ids.write(
            {
                "state": "closed",
                "closure_reason": self.closure_reason,
                "closed_by_id": self.env.user.id,
                "closed_date": fields.Datetime.now(),
            }
        )
        for risk in self.risk_ids:
            risk.message_post(
                body=self.env._(
                    "Risk closed. Reason: %(text)s", text=self.closure_reason
                )
            )
        return True


class LsRiskCancelWizard(models.TransientModel):
    """Cancel the selected risks against a recorded reason."""

    _name = "ls.risk.cancel.wizard"
    _description = "Cancel Risks"

    risk_ids = fields.Many2many(
        comodel_name="ls.risk.register",
        relation="ls_risk_cancel_wizard_risk_rel",
        column1="wizard_id",
        column2="risk_id",
        string="Risks",
        required=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", required=True)

    def action_cancel(self):
        """Cancel each selected risk.

        :raise UserError: when a risk is already closed or cancelled.
        :return: ``True`` when all risks were cancelled.
        :rtype: bool
        """
        self.ensure_one()
        blocked = self.risk_ids.filtered(
            lambda risk: risk.state in ("closed", "cancelled")
        )
        if blocked:
            raise UserError(
                self.env._(
                    "Closed or already cancelled risks cannot be cancelled. "
                    "Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )
        self.risk_ids.write(
            {"state": "cancelled", "cancel_reason": self.cancel_reason}
        )
        for risk in self.risk_ids:
            risk.message_post(
                body=self.env._(
                    "Risk cancelled. Reason: %(text)s", text=self.cancel_reason
                )
            )
        return True


class LsRiskAssessmentCancelWizard(models.TransientModel):
    """Cancel the selected assessments against a recorded reason."""

    _name = "ls.risk.assessment.cancel.wizard"
    _description = "Cancel Risk Assessments"

    assessment_ids = fields.Many2many(
        comodel_name="ls.risk.assessment",
        relation="ls_risk_assessment_cancel_wizard_rel",
        column1="wizard_id",
        column2="assessment_id",
        string="Assessments",
        required=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", required=True)

    def action_cancel(self):
        """Cancel each selected assessment.

        :raise UserError: when an assessment is already cancelled.
        :return: ``True`` when all assessments were cancelled.
        :rtype: bool
        """
        self.ensure_one()
        blocked = self.assessment_ids.filtered(lambda a: a.state == "cancelled")
        if blocked:
            raise UserError(
                self.env._(
                    "The following assessments are already cancelled: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )
        self.assessment_ids.write(
            {"state": "cancelled", "cancel_reason": self.cancel_reason}
        )
        for assessment in self.assessment_ids:
            assessment.message_post(
                body=self.env._(
                    "Assessment cancelled. Reason: %(text)s",
                    text=self.cancel_reason,
                )
            )
        return True


class LsRiskMitigationCancelWizard(models.TransientModel):
    """Cancel the selected risk control measures against a recorded reason."""

    _name = "ls.risk.mitigation.cancel.wizard"
    _description = "Cancel Risk Control Measures"

    mitigation_ids = fields.Many2many(
        comodel_name="ls.risk.mitigation",
        relation="ls_risk_mitigation_cancel_wizard_rel",
        column1="wizard_id",
        column2="mitigation_id",
        string="Risk Control Measures",
        required=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", required=True)

    def action_cancel(self):
        """Cancel each selected risk control measure.

        :raise UserError: when a measure is verified or already cancelled.
        :return: ``True`` when all measures were cancelled.
        :rtype: bool
        """
        self.ensure_one()
        blocked = self.mitigation_ids.filtered(
            lambda m: m.state in ("verified", "cancelled")
        )
        if blocked:
            raise UserError(
                self.env._(
                    "Verified or already cancelled risk control measures cannot "
                    "be cancelled. Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )
        self.mitigation_ids.write(
            {"state": "cancelled", "cancel_reason": self.cancel_reason}
        )
        for measure in self.mitigation_ids:
            measure.message_post(
                body=self.env._(
                    "Risk control measure cancelled. Reason: %(text)s",
                    text=self.cancel_reason,
                )
            )
        return True


class LsRiskFmeaCancelWizard(models.TransientModel):
    """Cancel the selected FMEA worksheets against a recorded reason."""

    _name = "ls.risk.fmea.cancel.wizard"
    _description = "Cancel FMEA Worksheets"

    fmea_ids = fields.Many2many(
        comodel_name="ls.risk.fmea",
        relation="ls_risk_fmea_cancel_wizard_rel",
        column1="wizard_id",
        column2="fmea_id",
        string="FMEA Worksheets",
        required=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", required=True)

    def action_cancel(self):
        """Cancel each selected FMEA worksheet.

        :raise UserError: when a worksheet is closed or already cancelled.
        :return: ``True`` when all worksheets were cancelled.
        :rtype: bool
        """
        self.ensure_one()
        blocked = self.fmea_ids.filtered(
            lambda fmea: fmea.state in ("closed", "cancelled")
        )
        if blocked:
            raise UserError(
                self.env._(
                    "Closed or already cancelled FMEA worksheets cannot be "
                    "cancelled. Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )
        self.fmea_ids.write(
            {"state": "cancelled", "cancel_reason": self.cancel_reason}
        )
        for fmea in self.fmea_ids:
            fmea.message_post(
                body=self.env._(
                    "FMEA worksheet cancelled. Reason: %(text)s",
                    text=self.cancel_reason,
                )
            )
        return True
