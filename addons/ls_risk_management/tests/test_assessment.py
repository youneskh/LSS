# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Tests of the risk assessment model."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged

from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskAssessment(RiskCommon):
    """Verify evaluation, approval segregation of duties and immutability."""

    def test_sequence_assigned(self):
        """An assessment receives a reference from the sequence."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        self.assertTrue(assessment.name.startswith("RA/"))

    def test_matrix_inherited_from_risk(self):
        """An assessment adopts the matrix of its risk."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        self.assertEqual(assessment.matrix_id, self.matrix)

    def test_evaluation_resolves_from_matrix(self):
        """The risk level and acceptability come from the matrix cell."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk, severity=3, probability=3)
        self.assertEqual(assessment.risk_level, "very_high")
        self.assertEqual(assessment.acceptability, "not_acceptable")
        self.assertEqual(assessment.matrix_cell_id, self.matrix.get_cell(3, 3))

    def test_ordinal_index_is_product(self):
        """The ordinal index is the product of the two ordinal values."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk, severity=3, probability=2)
        self.assertEqual(assessment.ordinal_index, 6)

    def test_confirm_requires_rationale(self):
        """An assessment without a rationale cannot be confirmed."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk, estimation_rationale="   ")
        with self.assertRaises(UserError):
            assessment.action_confirm()

    def test_confirm_moves_to_confirmed(self):
        """Confirming a draft assessment moves it to confirmed."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        assessment.action_confirm()
        self.assertEqual(assessment.state, "confirmed")

    def test_approve_requires_confirmed(self):
        """A draft assessment cannot be approved directly."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        with self.assertRaises(UserError):
            assessment.with_user(self.user_manager).action_approve()

    def test_approve_blocks_self_approval(self):
        """The assessor cannot approve their own assessment."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk, user=self.user_manager)
        assessment.with_user(self.user_manager).action_confirm()
        with self.assertRaises(UserError):
            assessment.with_user(self.user_manager).action_approve()

    def test_approve_allows_second_manager(self):
        """A different manager may approve the assessment."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk, user=self.user_manager)
        assessment.with_user(self.user_manager).action_confirm()
        assessment.with_user(self.user_manager_two).action_approve()
        self.assertEqual(assessment.state, "approved")
        self.assertEqual(assessment.approved_by_id, self.user_manager_two)
        self.assertTrue(assessment.approval_date)

    def test_approve_requires_manager_role(self):
        """An analyst cannot approve an assessment through the ORM."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        assessment.action_confirm()
        with self.assertRaises(AccessError):
            assessment.with_user(self.user_analyst).action_approve()

    def test_approve_requires_approved_matrix(self):
        """An assessment on an unapproved matrix cannot be approved."""
        draft_matrix = self._build_matrix(self.env, self.company, "DRAFT-3X3")
        risk = self._make_risk(matrix_id=draft_matrix.id)
        assessment = self._make_assessment(risk)
        assessment.action_confirm()
        with self.assertRaises(UserError):
            assessment.with_user(self.user_manager).action_approve()

    def test_confirm_requires_matrix_cell(self):
        """An assessment outside the matrix grid cannot be confirmed."""
        big = self._build_matrix(self.env, self.company, "BIG-4X4", size=4)
        small_risk = self._make_risk(matrix_id=big.id)
        assessment = self._make_assessment(small_risk, severity=4, probability=4)
        big.cell_ids.filtered(
            lambda cell: cell.severity_value == 4 and cell.probability_value == 4
        ).unlink()
        assessment.invalidate_recordset()
        with self.assertRaises(UserError):
            assessment.action_confirm()

    def test_approved_assessment_is_immutable(self):
        """An approved assessment rejects estimation changes."""
        risk = self._make_risk()
        assessment = self._approved_assessment(risk)
        with self.assertRaises(UserError):
            assessment.severity_level_id = self._severity(3)

    def test_approved_assessment_notes_still_editable(self):
        """Non-estimation fields remain editable after approval."""
        risk = self._make_risk()
        assessment = self._approved_assessment(risk)
        assessment.note = "Additional context recorded after approval."
        self.assertTrue(assessment.note)

    def test_only_one_initial_assessment(self):
        """A risk may carry only one non-cancelled initial assessment."""
        risk = self._make_risk()
        self._make_assessment(risk)
        with self.assertRaises(ValidationError):
            self._make_assessment(risk)

    def test_cancelled_initial_allows_replacement(self):
        """A cancelled initial assessment frees the slot for a new one."""
        risk = self._make_risk()
        first = self._make_assessment(risk)
        first.write({"state": "cancelled", "cancel_reason": "Superseded."})
        second = self._make_assessment(risk)
        self.assertEqual(second.assessment_type, "initial")

    def test_unlink_blocked_after_confirm(self):
        """A confirmed assessment cannot be deleted."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        assessment.action_confirm()
        with self.assertRaises(UserError):
            assessment.unlink()

    def test_reset_to_draft_requires_confirmed(self):
        """An approved assessment cannot be returned to draft."""
        risk = self._make_risk()
        assessment = self._approved_assessment(risk)
        with self.assertRaises(UserError):
            assessment.action_reset_to_draft()

    def test_level_from_wrong_scale_rejected(self):
        """A probability level cannot be used as a severity."""
        risk = self._make_risk()
        with self.assertRaises(ValidationError):
            self.env["ls.risk.assessment"].create(
                {
                    "risk_id": risk.id,
                    "severity_level_id": self._probability(1).id,
                    "probability_level_id": self._probability(1).id,
                    "estimation_rationale": "Wrong scale on purpose.",
                }
            )

    def test_level_from_other_matrix_rejected(self):
        """A level from another matrix cannot be used."""
        other = self._build_matrix(self.env, self.company, "OTH-3X3")
        risk = self._make_risk()
        with self.assertRaises(ValidationError):
            self.env["ls.risk.assessment"].create(
                {
                    "risk_id": risk.id,
                    "matrix_id": self.matrix.id,
                    "severity_level_id": self._severity(1, other).id,
                    "probability_level_id": self._probability(1).id,
                    "estimation_rationale": "Wrong matrix on purpose.",
                }
            )

    def test_company_follows_risk(self):
        """The stored company of an assessment follows its risk."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        self.assertEqual(assessment.company_id, self.company)

    def test_display_name_includes_type(self):
        """The display name shows the reference and assessment type."""
        risk = self._make_risk()
        assessment = self._make_assessment(risk)
        self.assertIn("Initial", assessment.display_name)
