# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the recall plan controlled-document lifecycle."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestPlanLifecycle(RecallCommon):
    """The plan behaves as a controlled document."""

    def test_reference_allocated_from_sequence(self):
        """A new plan receives a reference instead of the New placeholder."""
        self.assertTrue(self.plan.code)
        self.assertNotEqual(self.plan.code, "New")
        self.assertEqual(self.plan.version, 1)
        self.assertEqual(self.plan.state, "draft")

    def test_full_approval_cycle(self):
        """Draft to review to approved records the approver."""
        self.plan.action_submit_review()
        self.assertEqual(self.plan.state, "under_review")
        self.plan.with_user(self.user_manager).action_approve()
        self.assertEqual(self.plan.state, "approved")
        self.assertEqual(self.plan.approved_by_user_id, self.user_manager)
        self.assertTrue(self.plan.approval_date)

    def test_cannot_approve_from_draft(self):
        """Approval is only possible from the review state."""
        with self.assertRaises(UserError):
            self.plan.action_approve()

    def test_cannot_approve_without_procedure(self):
        """An approved plan must document the arrangement."""
        self.plan.description = False
        self.plan.action_submit_review()
        with self.assertRaises(ValidationError):
            self.plan.action_approve()

    def test_cannot_approve_without_deputy(self):
        """Out-of-hours cover is a condition of approval."""
        self.plan.deputy_user_id = False
        self.plan.action_submit_review()
        with self.assertRaises(ValidationError):
            self.plan.action_approve()

    def test_approved_content_is_frozen(self):
        """An approved plan cannot be edited in place."""
        self.plan.action_submit_review()
        self.plan.action_approve()
        with self.assertRaises(UserError):
            self.plan.name = "Renamed after approval"

    def test_new_revision_supersedes_previous(self):
        """Revising creates version n+1 and retires version n."""
        self.plan.action_submit_review()
        self.plan.action_approve()
        action = self.plan.action_new_revision()
        new_plan = self.env["ls.recall.plan"].browse(action["res_id"])
        self.assertEqual(new_plan.version, 2)
        self.assertEqual(new_plan.state, "draft")
        self.assertEqual(new_plan.code, self.plan.code)
        self.assertEqual(self.plan.state, "obsolete")
        self.assertFalse(self.plan.active)

    def test_scope_requires_products(self):
        """A product-scoped plan must list at least one product."""
        with self.assertRaises(ValidationError):
            self.plan.scope_type = "product"

    def test_only_draft_plans_deletable(self):
        """An approved plan cannot be deleted."""
        self.plan.action_submit_review()
        self.plan.action_approve()
        with self.assertRaises(UserError):
            self.plan.unlink()

    def test_negative_mock_interval_rejected(self):
        """The database rejects a negative rehearsal interval."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.plan.mock_recall_interval_months = -1
            self.plan.flush_recordset()
