# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the clinical evaluation and the PMCF evaluation report."""

from datetime import date

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestClinicalEvaluation(MedicalDeviceCommon):
    """Behaviour of ``ls.md.clinical_evaluation``."""

    def setUp(self):
        """Create a draft clinical evaluation."""
        super().setUp()
        self.evaluation = self.env["ls.md.clinical_evaluation"].create(
            {
                "title": "Clinical Evaluation Under Test",
                "device_id": self.device_iia.id,
                "evaluator_id": self.user_second.id,
                "plan_scope": "Scope recorded for the test.",
                "pmcf_plan_summary": "PMCF plan summary recorded for the test.",
                "clinical_investigation_justification": (
                    "Equivalent device data are sufficient."
                ),
                "benefit_risk_conclusion": "Benefit-risk ratio acceptable.",
            }
        )

    def test_equivalence_requires_demonstration(self):
        """Claiming equivalence requires the demonstration to be recorded."""
        with self.assertRaises(ValidationError):
            self.evaluation.write({"equivalence_claimed": True})

    def test_equivalence_accepted_with_demonstration(self):
        """Equivalence is accepted once the demonstration is recorded."""
        self.evaluation.write(
            {
                "equivalence_claimed": True,
                "equivalence_demonstration": "Demonstration recorded.",
            }
        )
        self.assertTrue(self.evaluation.equivalence_claimed)

    def test_no_investigation_requires_justification(self):
        """Omitting a clinical investigation requires a justification."""
        with self.assertRaises(ValidationError):
            self.evaluation.write(
                {
                    "clinical_investigation_performed": False,
                    "clinical_investigation_justification": False,
                    "state": "under_review",
                }
            )

    def test_pmcf_not_applicable_requires_justification(self):
        """Declaring PMCF not applicable requires a justification."""
        with self.assertRaises(ValidationError):
            self.evaluation.write(
                {"pmcf_applicable": False, "pmcf_justification": False,
                 "state": "under_review"}
            )

    def test_version_unique_per_device(self):
        """Two evaluations of one device cannot share a version."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.md.clinical_evaluation"].create(
                {
                    "title": "Duplicate Version",
                    "device_id": self.device_iia.id,
                    "version": self.evaluation.version,
                }
            )
            self.env["ls.md.clinical_evaluation"].flush_model()

    def test_self_approval_rejected(self):
        """The evaluator cannot approve their own evaluation."""
        self.evaluation.write({"evaluator_id": self.user_regulatory.id})
        self.evaluation.action_submit_for_review()
        with self.assertRaises(UserError):
            self.evaluation.with_user(self.user_regulatory).action_approve()

    def test_approval_by_regulatory_user(self):
        """A regulatory user approves an evaluation prepared by another user."""
        self.evaluation.action_submit_for_review()
        self.evaluation.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.evaluation.state, "approved")

    def test_content_locked_after_submission(self):
        """The content can no longer be edited after submission."""
        self.evaluation.action_submit_for_review()
        with self.assertRaises(UserError):
            self.evaluation.write({"plan_scope": "Changed after submission"})


@tagged("post_install", "-at_install")
class TestPmcfEvaluation(MedicalDeviceCommon):
    """Behaviour of ``ls.md.pmcf_evaluation``."""

    def setUp(self):
        """Create a draft PMCF evaluation report."""
        super().setUp()
        self.pmcf = self.env["ls.md.pmcf_evaluation"].create(
            {
                "device_id": self.device_iii.id,
                "period_start": date(2025, 1, 1),
                "period_end": date(2025, 12, 31),
                "author_id": self.user_second.id,
            }
        )

    def test_period_order_enforced(self):
        """A period ending before it starts is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.pmcf.write({"period_end": date(2024, 1, 1)})
            self.pmcf.flush_recordset()

    def test_annual_update_required_for_class_iii(self):
        """A class III device requires an annual PMCF update."""
        self.assertTrue(self.pmcf.annual_update_required)
        self.assertTrue(self.pmcf.next_update_due)

    def test_new_risks_require_description(self):
        """Declaring new risks requires a description of them."""
        with self.assertRaises(ValidationError):
            self.pmcf.write({"new_risks_identified": True})

    def test_actions_require_description(self):
        """Declaring required actions requires a description of them."""
        with self.assertRaises(ValidationError):
            self.pmcf.write({"actions_required": True})

    def test_linked_evaluation_must_match_device(self):
        """A clinical evaluation of another device cannot be linked."""
        other = self.env["ls.md.clinical_evaluation"].create(
            {"title": "Other Device Evaluation", "device_id": self.device_iia.id}
        )
        with self.assertRaises(ValidationError):
            self.pmcf.write({"clinical_evaluation_id": other.id})

    def test_approval_workflow(self):
        """A PMCF report moves from draft through review to approval."""
        self.pmcf.action_submit_for_review()
        self.assertEqual(self.pmcf.state, "under_review")
        self.pmcf.benefit_risk_conclusion = "Benefit-risk remains acceptable."
        self.pmcf.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.pmcf.state, "approved")
