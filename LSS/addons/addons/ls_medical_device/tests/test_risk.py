# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the risk management file and its risks."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestRiskManagement(MedicalDeviceCommon):
    """Behaviour of ``ls.md.risk_assessment`` and ``ls.md.risk_item``."""

    def setUp(self):
        """Create a draft risk management file with one risk."""
        super().setUp()
        self.risk_file = self.env["ls.md.risk_assessment"].create(
            {
                "title": "Risk Management File Under Test",
                "device_id": self.device_iia.id,
                "standard_reference": "ISO 14971:2019",
                "responsible_id": self.user_second.id,
            }
        )
        self.risk = self.env["ls.md.risk_item"].create(
            {
                "risk_assessment_id": self.risk_file.id,
                "reference": "R-001",
                "hazard": "Test hazard",
                "hazardous_situation": "Test hazardous situation",
                "harm": "Test harm",
                "initial_severity": "4",
                "initial_probability": "3",
                "control_option": "protective_measure",
                "control_measure": "Test control measure",
                "residual_severity": "4",
                "residual_probability": "1",
                "residual_acceptability": "acceptable",
                "acceptability_justification": "Test justification",
            }
        )

    def test_initial_index_is_product(self):
        """The initial index is the product of severity and probability."""
        self.assertEqual(self.risk.initial_index, 12)

    def test_residual_index_is_product(self):
        """The residual index is the product of severity and probability."""
        self.assertEqual(self.risk.residual_index, 4)

    def test_residual_cannot_exceed_initial(self):
        """A residual risk worse than the initial risk is rejected."""
        with self.assertRaises(ValidationError):
            self.risk.write({"residual_probability": "5"})

    def test_new_hazard_requires_description(self):
        """Declaring a new hazard requires a description of it."""
        with self.assertRaises(ValidationError):
            self.risk.write({"introduces_new_hazard": True})

    def test_statistics_computed(self):
        """The file statistics reflect the recorded risks."""
        self.assertEqual(self.risk_file.risk_item_count, 1)
        self.assertEqual(self.risk_file.max_residual_index, 4)
        self.assertEqual(self.risk_file.unacceptable_risk_count, 0)

    def test_unacceptable_risk_counted(self):
        """A residual risk judged unacceptable is counted as such."""
        self.risk.write({"residual_acceptability": "unacceptable"})
        self.risk_file.invalidate_recordset()
        self.assertEqual(self.risk_file.unacceptable_risk_count, 1)

    def test_approval_requires_conclusion(self):
        """A file without an overall conclusion cannot be approved."""
        self.risk_file.action_submit_for_review()
        with self.assertRaises(ValidationError):
            self.risk_file.with_user(self.user_regulatory).action_approve()

    def test_approval_by_regulatory_user(self):
        """A complete file is approved by a regulatory user."""
        self.risk_file.write(
            {
                "overall_benefit_risk_conclusion": "Overall residual risk acceptable.",
                "overall_risk_acceptable": True,
            }
        )
        self.risk_file.action_submit_for_review()
        self.risk_file.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.risk_file.state, "approved")
        self.assertTrue(self.risk_file.approval_date)

    def test_plain_user_cannot_approve(self):
        """A plain user cannot approve a risk management file."""
        self.risk_file.write(
            {
                "overall_benefit_risk_conclusion": "Overall residual risk acceptable.",
                "overall_risk_acceptable": True,
            }
        )
        self.risk_file.action_submit_for_review()
        with self.assertRaises(UserError):
            self.risk_file.with_user(self.user_user).action_approve()

    def test_risks_locked_after_approval(self):
        """Risks can no longer be edited once the file leaves draft."""
        self.risk_file.write(
            {
                "overall_benefit_risk_conclusion": "Overall residual risk acceptable.",
                "overall_risk_acceptable": True,
            }
        )
        self.risk_file.action_submit_for_review()
        with self.assertRaises(UserError):
            self.risk.write({"hazard": "Changed after submission"})

    def test_approved_file_cannot_be_deleted(self):
        """An approved file is preserved rather than deleted."""
        self.risk_file.write(
            {
                "overall_benefit_risk_conclusion": "Overall residual risk acceptable.",
                "overall_risk_acceptable": True,
            }
        )
        self.risk_file.action_submit_for_review()
        self.risk_file.with_user(self.user_regulatory).action_approve()
        with self.assertRaises(UserError):
            self.risk_file.unlink()

    def test_copy_increments_version(self):
        """Duplicating a file opens a new version in draft."""
        copy = self.risk_file.copy()
        self.assertEqual(copy.version, self.risk_file.version + 1)
        self.assertEqual(copy.state, "draft")

    def test_reference_unique_within_file(self):
        """Two risks in one file cannot share a reference."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.md.risk_item"].create(
                {
                    "risk_assessment_id": self.risk_file.id,
                    "reference": "R-001",
                    "hazard": "Duplicate reference",
                    "hazardous_situation": "Situation",
                    "harm": "Harm",
                }
            )
            self.env["ls.md.risk_item"].flush_model()
