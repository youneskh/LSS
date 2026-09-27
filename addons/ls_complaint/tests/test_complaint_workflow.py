# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Workflow tests for the ls.complaint state machine."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestComplaintWorkflow(TestLsComplaintCommon):
    """Verify every transition of the complaint state machine."""

    def test_01_sequence_assigned_on_create(self):
        """A complaint receives a reference from the sequence."""
        complaint = self._create_complaint()
        self.assertTrue(complaint.name.startswith("CMP/"))
        self.assertEqual(complaint.state, "received")

    def test_02_start_assessment_requires_owner_and_category(self):
        """Assessment cannot start without a responsible user and a category."""
        complaint = self._create_complaint(owner_id=False)
        with self.assertRaises(UserError):
            complaint.action_start_assessment()

    def test_03_start_assessment(self):
        """Assessment stamps the assessor and the assessment date."""
        complaint = self._create_complaint()
        complaint.action_start_assessment()
        self.assertEqual(complaint.state, "assessment")
        self.assertTrue(complaint.assessment_date)
        self.assertEqual(complaint.assessed_by_id, self.env.user)

    def test_04_start_investigation_requires_assessment_data(self):
        """Investigation cannot start before the assessment is documented."""
        complaint = self._create_complaint()
        complaint.action_start_assessment()
        with self.assertRaises(UserError):
            complaint.action_start_investigation()

    def test_05_start_investigation_creates_investigation(self):
        """Starting the investigation creates a draft investigation record."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self.assertEqual(complaint.state, "investigation")
        self.assertEqual(complaint.investigation_count, 1)
        self.assertEqual(complaint.investigation_ids.state, "draft")

    def test_06_resolution_requires_approved_investigation(self):
        """Resolution cannot start while an investigation is pending."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        with self.assertRaises(UserError):
            complaint.action_start_resolution()

    def test_07_full_happy_path(self):
        """A complaint can be driven from receipt to closure."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        self.assertEqual(complaint.state, "resolution")
        self._add_done_resolution(complaint)
        complaint.action_close(
            closure_summary="Root cause corrected, replacement shipped.",
            reviewer=self.user_reviewer,
            customer_notified=True,
        )
        self.assertEqual(complaint.state, "closed")
        self.assertTrue(complaint.date_closed)
        self.assertEqual(complaint.reviewer_id, self.user_reviewer)
        self.assertTrue(complaint.customer_notification_date)
        self.assertGreaterEqual(complaint.closure_duration_days, 0.0)

    def test_08_close_requires_resolution(self):
        """Closure is refused when no resolution is recorded."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        with self.assertRaises(UserError):
            complaint.action_close(
                closure_summary="Nothing done.", reviewer=self.user_reviewer
            )

    def test_09_close_requires_reviewer_other_than_owner(self):
        """The reviewer cannot be the responsible user."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        self._add_done_resolution(complaint)
        with self.assertRaises(UserError):
            complaint.action_close(
                closure_summary="Closed.", reviewer=self.user_investigator
            )

    def test_10_capa_required_path(self):
        """The CAPA branch requires a justification and a reference."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        with self.assertRaises(UserError):
            complaint.action_mark_capa_required()
        complaint.capa_justification = "Systemic tooling maintenance gap."
        complaint.action_mark_capa_required()
        self.assertEqual(complaint.state, "capa_required")
        self.assertTrue(complaint.capa_required)
        with self.assertRaises(UserError):
            complaint.action_start_resolution()
        complaint.capa_reference = "CAPA-2026-0007"
        complaint.action_start_resolution()
        self.assertEqual(complaint.state, "resolution")

    def test_11_close_requires_capa_reference(self):
        """Closure is refused when a declared CAPA has no reference."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.capa_justification = "Systemic gap."
        complaint.action_mark_capa_required()
        complaint.capa_reference = "CAPA-2026-0008"
        complaint.action_start_resolution()
        self._add_done_resolution(complaint)
        complaint.capa_reference = False
        with self.assertRaises(UserError):
            complaint.action_close(
                closure_summary="Closed.", reviewer=self.user_reviewer
            )

    def test_12_waive_investigation(self):
        """The investigation can be waived only when the category allows it."""
        complaint = self._create_complaint(category_id=self.category.id)
        complaint.action_start_assessment()
        complaint.write(
            {
                "severity": "minor",
                "complaint_type": "packaging",
                "assessment_summary": "No product impact.",
                "investigation_waiver_reason": "Isolated logistics issue.",
            }
        )
        with self.assertRaises(UserError):
            complaint.action_skip_investigation()
        complaint.category_id = self.category_no_investigation
        complaint.action_skip_investigation()
        self.assertEqual(complaint.state, "resolution")

    def test_13_waiver_blocked_by_adverse_event(self):
        """An adverse event makes the investigation mandatory."""
        complaint = self._create_complaint(
            category_id=self.category_no_investigation.id
        )
        complaint.action_start_assessment()
        complaint.write(
            {
                "severity": "minor",
                "complaint_type": "safety",
                "assessment_summary": "Reaction reported.",
                "investigation_waiver_reason": "Not needed.",
            }
        )
        self.env["ls.complaint.adverse_event"].create(
            {
                "complaint_id": complaint.id,
                "event_description": "Skin reaction.",
            }
        )
        with self.assertRaises(UserError):
            complaint.action_skip_investigation()

    def test_14_cancel_and_reset(self):
        """A complaint can be cancelled with a reason and reset afterwards."""
        complaint = self._create_complaint()
        with self.assertRaises(UserError):
            complaint.action_cancel(reason=False)
        complaint.action_cancel(reason="Duplicate of CMP/2026/00001.")
        self.assertEqual(complaint.state, "cancelled")
        self.assertTrue(complaint.cancellation_reason)
        complaint.action_reset_to_received()
        self.assertEqual(complaint.state, "received")
        self.assertFalse(complaint.cancellation_reason)

    def test_15_invalid_transition_is_refused(self):
        """A transition from a wrong state raises a user error."""
        complaint = self._create_complaint()
        with self.assertRaises(UserError):
            complaint.action_start_resolution()
        with self.assertRaises(UserError):
            complaint.action_reset_to_received()

    def test_16_closed_record_is_frozen(self):
        """A closed complaint can no longer be modified."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        self._add_done_resolution(complaint)
        complaint.action_close(
            closure_summary="Closed.", reviewer=self.user_reviewer
        )
        with self.assertRaises(UserError):
            complaint.summary = "Tampered subject"
        complaint.active = False
        self.assertFalse(complaint.active)

    def test_17_close_requires_closed_adverse_events(self):
        """Closure is refused while an adverse event is still open."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self.env["ls.complaint.adverse_event"].create(
            {
                "complaint_id": complaint.id,
                "event_description": "Reaction reported.",
            }
        )
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        self._add_done_resolution(complaint)
        with self.assertRaises(UserError):
            complaint.action_close(
                closure_summary="Closed.", reviewer=self.user_reviewer
            )

    def test_18_open_wizards_from_actions(self):
        """The closure and cancellation wizards are opened by the actions."""
        complaint = self._create_complaint()
        cancel_action = complaint.action_open_cancel_wizard()
        self.assertEqual(cancel_action["res_model"], "ls.complaint.cancel.wizard")
        self._bring_to_investigation(complaint)
        self._approve_investigation(complaint.investigation_ids)
        complaint.action_start_resolution()
        self._add_done_resolution(complaint)
        close_action = complaint.action_open_close_wizard()
        self.assertEqual(close_action["res_model"], "ls.complaint.close.wizard")
