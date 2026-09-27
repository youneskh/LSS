# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Investigation model tests."""

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationInvestigation(DeviationCommon):
    """Verify the investigation lifecycle and its invariants."""

    def setUp(self):
        super().setUp()
        self.deviation = self._advance_to_assessed(self._create_deviation())
        self.investigation = self.env["ls.deviation.investigation"].create(
            {
                "deviation_id": self.deviation.id,
                "name": "Investigation",
                "rca_method_id": self.rca_method.id,
                "investigator_id": self.user_investigator.id,
            }
        )

    def test_initial_state_is_draft(self):
        """A new investigation starts in draft."""
        self.assertEqual(self.investigation.state, "draft")

    def test_company_is_inherited(self):
        """The company is inherited from the parent deviation."""
        self.assertEqual(
            self.investigation.company_id, self.deviation.company_id
        )

    def test_start_moves_to_in_progress(self):
        """Starting an investigation moves it to in progress."""
        self.investigation.action_start()
        self.assertEqual(self.investigation.state, "in_progress")

    def test_complete_requires_root_cause(self):
        """Completion is blocked without a root cause."""
        self.investigation.findings = "Findings."
        with self.assertRaises(ValidationError):
            self.investigation.action_complete()

    def test_complete_requires_findings(self):
        """Completion is blocked without recorded findings."""
        self.investigation.root_cause = "Root cause."
        with self.assertRaises(ValidationError):
            self.investigation.action_complete()

    def test_complete_stamps_date(self):
        """Completion stamps the completion date."""
        self.investigation.write(
            {"findings": "Findings.", "root_cause": "Root cause."}
        )
        self.investigation.action_complete()
        self.assertEqual(self.investigation.state, "completed")
        self.assertTrue(self.investigation.date_completed)

    def test_completion_before_start_rejected(self):
        """A completion date earlier than the start date is rejected."""
        with self.assertRaises(ValidationError):
            self.investigation.date_completed = (
                fields.Datetime.now() - timedelta(days=1)
            )

    def test_root_cause_not_determined_flag(self):
        """The most probable cause case is representable."""
        self.investigation.write(
            {
                "findings": "Findings.",
                "root_cause": "Most probable cause with rationale.",
                "root_cause_determined": False,
            }
        )
        self.investigation.action_complete()
        self.assertFalse(self.investigation.root_cause_determined)
        self.assertEqual(self.investigation.state, "completed")

    def test_cascade_delete_with_deviation(self):
        """Investigations are removed with their deviation."""
        deviation = self._create_deviation()
        investigation = self.env["ls.deviation.investigation"].create(
            {
                "deviation_id": deviation.id,
                "name": "Temp",
                "rca_method_id": self.rca_method.id,
                "investigator_id": self.user_investigator.id,
            }
        )
        deviation.unlink()
        self.assertFalse(investigation.exists())
