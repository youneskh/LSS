# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Tests of the risk management wizards."""

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskWizards(RiskCommon):
    """Verify batch assessment, residual acceptance, closure and cancellation."""

    def test_assess_wizard_creates_one_per_risk(self):
        """The assessment wizard creates one assessment per selected risk."""
        risks = self._make_risk() + self._make_risk(title="Second risk")
        wizard = self.env["ls.risk.assess.wizard"].create(
            {
                "risk_ids": [(6, 0, risks.ids)],
                "severity_level_id": self._severity(2).id,
                "probability_level_id": self._probability(2).id,
                "estimation_rationale": "Batch rationale.",
            }
        )
        wizard.action_create_assessments()
        for risk in risks:
            self.assertEqual(risk.assessment_count, 1)

    def test_assess_wizard_adopts_shared_matrix(self):
        """The wizard adopts the matrix shared by the selected risks."""
        risks = self._make_risk() + self._make_risk(title="Second risk")
        # A new (unsaved) wizard: the severity and probability are required
        # and are only chosen by the user after the matrix is proposed.
        wizard = self.env["ls.risk.assess.wizard"].new(
            {"risk_ids": [(6, 0, risks.ids)]}
        )
        self.assertEqual(wizard.matrix_id, self.matrix)

    def test_assess_wizard_rejects_mixed_matrices(self):
        """Risks using different matrices cannot be assessed together."""
        other = self._build_matrix(self.env, self.company, "WIZ-3X3")
        other.with_user(self.user_manager).action_approve()
        risks = self._make_risk() + self._make_risk(
            title="Other matrix", matrix_id=other.id
        )
        wizard = self.env["ls.risk.assess.wizard"].create(
            {
                "risk_ids": [(6, 0, risks.ids)],
                "severity_level_id": self._severity(1).id,
                "probability_level_id": self._probability(1).id,
                "estimation_rationale": "Mixed matrices.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_create_assessments()

    def test_residual_wizard_records_decision(self):
        """The residual wizard records the acceptance and its author."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=3, probability=1)
        wizard = self.env["ls.risk.residual.wizard"].with_user(
            self.user_manager
        ).create({"risk_id": risk.id, "justification": "Controls reduce exposure."})
        wizard.action_accept()
        self.assertTrue(risk.residual_risk_accepted)
        self.assertEqual(risk.residual_risk_accepted_by_id, self.user_manager)
        self.assertTrue(risk.residual_risk_justification)

    def test_residual_wizard_requires_assessment(self):
        """Residual risk cannot be accepted without an approved assessment."""
        risk = self._make_risk()
        wizard = self.env["ls.risk.residual.wizard"].with_user(
            self.user_manager
        ).create({"risk_id": risk.id, "justification": "Premature."})
        with self.assertRaises(UserError):
            wizard.action_accept()

    def test_residual_wizard_requires_benefit_risk(self):
        """A not-acceptable risk needs a benefit-risk analysis."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=3, probability=3)
        wizard = self.env["ls.risk.residual.wizard"].with_user(
            self.user_manager
        ).create({"risk_id": risk.id, "justification": "No analysis supplied."})
        with self.assertRaises(UserError):
            wizard.action_accept()

    def test_residual_wizard_accepts_with_benefit_risk(self):
        """A benefit-risk analysis permits accepting an unacceptable risk."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=3, probability=3)
        wizard = self.env["ls.risk.residual.wizard"].with_user(
            self.user_manager
        ).create(
            {
                "risk_id": risk.id,
                "justification": "No alternative treatment exists.",
                "benefit_risk_analysis": "Clinical benefit outweighs residual risk.",
            }
        )
        wizard.action_accept()
        self.assertTrue(risk.residual_risk_accepted)
        self.assertTrue(risk.benefit_risk_analysis)

    def test_residual_wizard_is_not_repeatable(self):
        """Residual risk cannot be accepted twice."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=1, probability=1)
        values = {"risk_id": risk.id, "justification": "First acceptance."}
        model = self.env["ls.risk.residual.wizard"].with_user(self.user_manager)
        model.create(values).action_accept()
        with self.assertRaises(UserError):
            model.create(dict(values, justification="Second acceptance.")).action_accept()

    def test_close_wizard_blocks_draft(self):
        """A draft risk cannot be closed."""
        risk = self._make_risk()
        wizard = self.env["ls.risk.close.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "closure_reason": "Too early."}
        )
        with self.assertRaises(UserError):
            wizard.action_close()

    def test_close_wizard_requires_residual_decision(self):
        """Closure requires the residual decision when acceptability demands it."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=3, probability=1)
        risk.action_start_assessment()
        wizard = self.env["ls.risk.close.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "closure_reason": "No decision recorded."}
        )
        with self.assertRaises(UserError):
            wizard.action_close()

    def test_close_wizard_closes_acceptable_risk(self):
        """An acceptable risk closes and records the reason and author."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=1, probability=1)
        risk.action_start_assessment()
        wizard = self.env["ls.risk.close.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "closure_reason": "Risk no longer present."}
        )
        wizard.action_close()
        self.assertEqual(risk.state, "closed")
        self.assertEqual(risk.closed_by_id, self.user_manager)
        self.assertTrue(risk.closure_reason)

    def test_cancel_wizard_records_reason(self):
        """Cancelling a risk records the reason."""
        risk = self._make_risk()
        wizard = self.env["ls.risk.cancel.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "cancel_reason": "Duplicate entry."}
        )
        wizard.action_cancel()
        self.assertEqual(risk.state, "cancelled")
        self.assertEqual(risk.cancel_reason, "Duplicate entry.")

    def test_cancel_wizard_blocks_closed(self):
        """A closed risk cannot be cancelled."""
        risk = self._make_risk()
        self._approved_assessment(risk, severity=1, probability=1)
        risk.action_start_assessment()
        self.env["ls.risk.close.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "closure_reason": "Closed first."}
        ).action_close()
        wizard = self.env["ls.risk.cancel.wizard"].with_user(self.user_manager).create(
            {"risk_ids": [(6, 0, risk.ids)], "cancel_reason": "Too late."}
        )
        with self.assertRaises(UserError):
            wizard.action_cancel()

    def test_assessment_cancel_wizard(self):
        """Cancelling an assessment records the reason."""
        risk = self._make_risk()
        assessment = self._approved_assessment(risk)
        wizard = self.env["ls.risk.assessment.cancel.wizard"].with_user(
            self.user_manager
        ).create(
            {
                "assessment_ids": [(6, 0, assessment.ids)],
                "cancel_reason": "Superseded by a corrected estimation.",
            }
        )
        wizard.action_cancel()
        self.assertEqual(assessment.state, "cancelled")

    def test_mitigation_cancel_wizard_blocks_verified(self):
        """A verified measure cannot be cancelled."""
        risk = self._make_risk()
        measure = self.env["ls.risk.mitigation"].create(
            {
                "risk_id": risk.id,
                "title": "Measure",
                "description": "Description.",
                "control_option": "protective_measure",
                "responsible_id": self.user_analyst.id,
            }
        )
        measure.with_user(self.user_manager).action_approve()
        measure.action_start()
        measure.implementation_evidence = "Done."
        measure.with_user(self.user_analyst).action_mark_implemented()
        measure.effectiveness_evidence = "Effective."
        measure.with_user(self.user_manager).action_verify_effectiveness()
        wizard = self.env["ls.risk.mitigation.cancel.wizard"].with_user(
            self.user_manager
        ).create(
            {"mitigation_ids": [(6, 0, measure.ids)], "cancel_reason": "Too late."}
        )
        with self.assertRaises(UserError):
            wizard.action_cancel()

    def test_fmea_cancel_wizard(self):
        """Cancelling an FMEA worksheet records the reason."""
        fmea = self._make_fmea()
        wizard = self.env["ls.risk.fmea.cancel.wizard"].with_user(
            self.user_manager
        ).create({"fmea_ids": [(6, 0, fmea.ids)], "cancel_reason": "Scope withdrawn."})
        wizard.action_cancel()
        self.assertEqual(fmea.state, "cancelled")
