# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the sample state machine and segregation of duties."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestSampleWorkflow(EnvMonitoringCommon):
    """The sample lifecycle records who did what, and refuses shortcuts."""

    def setUp(self):
        super().setUp()
        limit = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(limit)
        self.sample = self._create_sample()

    def test_reference_is_assigned_from_the_sequence(self):
        self.assertNotEqual(self.sample.name, "New")
        self.assertTrue(self.sample.name)

    def test_forward_transitions_follow_the_declared_order(self):
        self.sample.action_schedule()
        self.assertEqual(self.sample.state, "scheduled")
        self.sample.with_user(self.technician).action_collect()
        self.assertEqual(self.sample.state, "collected")
        self.assertEqual(self.sample.collected_by_id, self.technician)
        self.sample.with_user(self.technician).action_start_analysis()
        self.assertEqual(self.sample.state, "in_analysis")

    def test_transition_that_skips_a_state_is_refused(self):
        with self.assertRaises(UserError):
            self.sample.action_collect()

    def test_collection_requires_at_least_one_result_line(self):
        empty = self.env["ls.env.sample"].create(
            {"sampling_point_id": self.point.id})
        empty.action_schedule()
        with self.assertRaises(UserError):
            empty.action_collect()

    def test_results_cannot_be_submitted_without_values(self):
        self.sample.action_schedule()
        self.sample.with_user(self.technician).action_collect()
        self.sample.with_user(self.technician).action_start_analysis()
        with self.assertRaises(UserError):
            self.sample.with_user(self.technician).action_enter_results()

    def _advance_to_results_entered(self, value=1.0):
        self.sample.action_schedule()
        self.sample.with_user(self.technician).action_collect()
        self.sample.with_user(self.technician).action_start_analysis()
        self.sample.result_ids.write({"value_numeric": value, "value_set": True})
        self.sample.with_user(self.technician).action_enter_results()

    def test_reviewer_must_differ_from_the_results_author(self):
        self._advance_to_results_entered()
        manager_also_entered = self.sample.results_entered_by_id
        self.assertEqual(manager_also_entered, self.technician)
        with self.assertRaises(UserError):
            self.sample.with_user(self.technician).action_review()

    def test_technician_cannot_review(self):
        self._advance_to_results_entered()
        with self.assertRaises(UserError):
            self.sample.with_user(self.second_technician).action_review()

    def test_manager_can_review_and_approve(self):
        self._advance_to_results_entered()
        self.sample.with_user(self.manager).action_review()
        self.assertEqual(self.sample.state, "reviewed")
        self.assertEqual(self.sample.reviewed_by_id, self.manager)
        self.sample.with_user(self.manager).action_approve()
        self.assertEqual(self.sample.state, "approved")
        self.assertTrue(self.sample.approval_datetime)

    def test_approved_sample_is_immutable(self):
        self._advance_to_results_entered()
        self.sample.with_user(self.manager).action_review()
        self.sample.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            self.sample.scheduled_date = "2026-01-01"

    def test_notes_remain_editable_on_an_approved_sample(self):
        self._advance_to_results_entered()
        self.sample.with_user(self.manager).action_review()
        self.sample.with_user(self.manager).action_approve()
        self.sample.notes = "Observation added during periodic review."
        self.assertTrue(self.sample.notes)

    def test_cancellation_requires_a_reason(self):
        self.sample.action_schedule()
        with self.assertRaises(UserError):
            self.sample.action_cancel()

    def test_cancellation_records_the_reason(self):
        self.sample.action_schedule()
        self.sample.with_context(
            cancellation_reason="Room released before sampling."
        ).action_cancel()
        self.assertEqual(self.sample.state, "cancelled")
        self.assertIn("Room released", self.sample.cancellation_reason)

    def test_only_a_draft_sample_can_be_deleted(self):
        self.sample.action_schedule()
        with self.assertRaises(UserError):
            self.sample.unlink()

    def test_overdue_flag_and_search(self):
        self.sample.action_schedule()
        self.sample.scheduled_date = "2020-01-01"
        self.assertTrue(self.sample.is_overdue)
        found = self.env["ls.env.sample"].search([("is_overdue", "=", True)])
        self.assertIn(self.sample, found)
        not_overdue = self.env["ls.env.sample"].search(
            [("is_overdue", "=", False)])
        self.assertNotIn(self.sample, not_overdue)

    def test_collection_timestamp_cannot_be_in_the_future(self):
        from odoo import fields
        from datetime import timedelta
        self.sample.action_schedule()
        self.sample.with_user(self.technician).action_collect()
        future = fields.Datetime.now() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.sample.collection_datetime = future

    def test_return_to_analysis_clears_the_review(self):
        self._advance_to_results_entered()
        self.sample.with_user(self.manager).action_review()
        self.sample.with_user(self.manager).action_reopen_analysis()
        self.assertEqual(self.sample.state, "in_analysis")
        self.assertFalse(self.sample.reviewed_by_id)
