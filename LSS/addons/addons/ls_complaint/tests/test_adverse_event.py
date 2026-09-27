# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the ls.complaint.adverse_event model."""

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestAdverseEvent(TestLsComplaintCommon):
    """Verify the adverse event state machine and its reporting controls."""

    def setUp(self):
        """Create a complaint and an attached draft adverse event."""
        super().setUp()
        self.complaint = self._create_complaint()
        self.event = self.env["ls.complaint.adverse_event"].create(
            {
                "complaint_id": self.complaint.id,
                "event_description": "Localised skin reaction after administration.",
                "seriousness": "non_serious",
                "outcome": "recovering",
            }
        )
        self.authority = self.env["res.partner"].create(
            {"name": "Test Competent Authority"}
        )

    def test_01_sequence_and_display_name(self):
        """The event gets a reference and a qualified display name."""
        self.assertTrue(self.event.name.startswith("CMP/AE/"))
        self.assertIn(self.complaint.name, self.event.display_name)

    def test_02_no_due_date_when_not_reportable(self):
        """No deadline is derived while the event is not reportable."""
        self.assertFalse(self.event.report_due_date)

    def test_03_due_date_from_category_configuration(self):
        """The deadline is derived from the configured category value."""
        self.event.reportable = True
        self.event.invalidate_recordset()
        expected = self.event.awareness_date + timedelta(days=15)
        self.assertEqual(self.event.report_due_date, expected)

    def test_04_no_due_date_without_configuration(self):
        """No deadline is produced when the category has no configured value."""
        self.complaint.category_id = self.category_no_investigation
        self.event.reportable = True
        self.event.invalidate_recordset()
        self.assertFalse(self.event.report_due_date)

    def test_05_assess_requires_rationale_and_causality(self):
        """Assessment is refused without rationale and causality."""
        with self.assertRaises(UserError):
            self.event.action_assess()
        self.event.reportability_rationale = "Not reportable under the procedure."
        with self.assertRaises(UserError):
            self.event.action_assess()
        self.event.causality_assessment = "unlikely"
        self.event.action_assess()
        self.assertEqual(self.event.state, "assessed")

    def test_06_reportable_requires_authority(self):
        """A reportable event must identify the competent authority."""
        self.event.write(
            {
                "reportable": True,
                "reportability_rationale": "Reportable under the procedure.",
                "causality_assessment": "possible",
            }
        )
        with self.assertRaises(UserError):
            self.event.action_assess()
        self.event.authority_id = self.authority
        self.event.action_assess()
        self.assertEqual(self.event.state, "assessed")

    def test_07_submission_requires_reference(self):
        """The submission requires the authority acknowledgement reference."""
        self._assess_reportable()
        with self.assertRaises(UserError):
            self.event.action_submit()
        self.event.report_reference = "ACK-2026-001"
        self.event.action_submit()
        self.assertEqual(self.event.state, "submitted")
        self.assertTrue(self.event.report_submitted_date)
        self.assertEqual(self.event.submitted_by_id, self.env.user)

    def test_08_non_reportable_cannot_be_submitted(self):
        """A non reportable event cannot be submitted."""
        self.event.write(
            {
                "reportability_rationale": "Not reportable.",
                "causality_assessment": "unrelated",
            }
        )
        self.event.action_assess()
        with self.assertRaises(UserError):
            self.event.action_submit()

    def test_09_reportable_cannot_be_closed_before_submission(self):
        """A reportable event must be submitted before closure."""
        self._assess_reportable()
        with self.assertRaises(UserError):
            self.event.action_close()
        self.event.report_reference = "ACK-2026-002"
        self.event.action_submit()
        self.event.action_close()
        self.assertEqual(self.event.state, "closed")

    def test_10_follow_up_notes_required(self):
        """Closure requires notes when a follow-up was declared."""
        self.event.write(
            {
                "reportability_rationale": "Not reportable.",
                "causality_assessment": "unlikely",
                "follow_up_required": True,
            }
        )
        self.event.action_assess()
        with self.assertRaises(UserError):
            self.event.action_close()
        self.event.follow_up_notes = "Outcome confirmed with the reporter."
        self.event.action_close()
        self.assertEqual(self.event.state, "closed")

    def test_11_closed_event_is_frozen(self):
        """A closed event can no longer be modified."""
        self.event.write(
            {
                "reportability_rationale": "Not reportable.",
                "causality_assessment": "unlikely",
            }
        )
        self.event.action_assess()
        self.event.action_close()
        with self.assertRaises(UserError):
            self.event.event_description = "Tampered"

    def test_12_awareness_date_not_in_future(self):
        """An awareness date in the future is refused."""
        with self.assertRaises(ValidationError):
            self.event.awareness_date = fields.Date.context_today(
                self.env.user
            ) + timedelta(days=1)

    def test_13_event_date_before_awareness(self):
        """An event date later than the awareness date is refused."""
        with self.assertRaises(ValidationError):
            self.event.event_date = self.event.awareness_date + timedelta(days=1)

    def test_14_rationale_mandatory_once_assessed(self):
        """The reportability rationale cannot be removed after assessment."""
        self.event.write(
            {
                "reportability_rationale": "Not reportable.",
                "causality_assessment": "unlikely",
            }
        )
        self.event.action_assess()
        with self.assertRaises(ValidationError):
            self.event.reportability_rationale = False

    def test_15_overdue_compute_and_search(self):
        """The overdue reporting flag is computed and searchable."""
        self._assess_reportable()
        self.event.awareness_date = fields.Date.context_today(
            self.env.user
        ) - timedelta(days=60)
        self.event.invalidate_recordset()
        self.assertTrue(self.event.is_report_overdue)
        found = self.env["ls.complaint.adverse_event"].search(
            [("is_report_overdue", "=", True), ("id", "=", self.event.id)]
        )
        self.assertIn(self.event, found)
        excluded = self.env["ls.complaint.adverse_event"].search(
            [("is_report_overdue", "!=", True), ("id", "=", self.event.id)]
        )
        self.assertNotIn(self.event, excluded)

    def test_16_overdue_search_operator_guard(self):
        """An unsupported operator on the overdue filter raises an error.

        Odoo 19 rejects an ordering operator on a boolean field in its domain
        parser (ValueError), before the custom search method runs.
        """
        with self.assertRaises(ValueError):
            self.env["ls.complaint.adverse_event"].search(
                [("is_report_overdue", ">", True)]
            )

    def test_17_unlink_guard(self):
        """An assessed event cannot be deleted."""
        self.event.write(
            {
                "reportability_rationale": "Not reportable.",
                "causality_assessment": "unlikely",
            }
        )
        self.event.action_assess()
        with self.assertRaises(UserError):
            self.event.unlink()

    def test_18_wrong_state_transition(self):
        """A transition from a wrong state raises a user error."""
        with self.assertRaises(UserError):
            self.event.action_submit()
        with self.assertRaises(UserError):
            self.event.action_close()

    def _assess_reportable(self):
        """Bring the event to the Assessed state as a reportable event."""
        self.event.write(
            {
                "reportable": True,
                "reportability_rationale": "Reportable under the procedure.",
                "causality_assessment": "possible",
                "authority_id": self.authority.id,
            }
        )
        self.event.action_assess()
