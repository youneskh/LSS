# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the Validation Master Plan lifecycle."""

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestMasterPlan(ValidationCommon):
    """Lifecycle, versioning and content freeze of a master plan."""

    def test_reference_is_assigned_by_the_sequence(self):
        """A new plan receives a reference from the dedicated sequence."""
        self.assertTrue(self.master_plan.reference.startswith("VMP/"))
        self.assertNotEqual(self.master_plan.reference, "New")

    def test_submit_requires_a_documented_scope(self):
        """A plan without scope cannot be submitted for review."""
        plan = self.env["ls.validation.master.plan"].create(
            {"name": "Plan without scope"}
        )
        with self.assertRaises(UserError):
            plan.action_submit_review()

    def test_full_lifecycle_up_to_activation(self):
        """Draft, review, approval and activation follow each other."""
        self.master_plan.action_submit_review()
        self.assertEqual(self.master_plan.state, "review")
        self._sign(self.master_plan, "action_approve", self.user_approver)
        self.assertEqual(self.master_plan.state, "approved")
        self.assertEqual(self.master_plan.approver_id, self.user_approver)
        self.master_plan.action_activate()
        self.assertEqual(self.master_plan.state, "active")
        self.assertEqual(
            self.master_plan.effective_date,
            fields.Date.context_today(self.master_plan),
        )

    def test_approval_requires_the_approver_group(self):
        """An engineer cannot approve a master plan."""
        self.master_plan.action_submit_review()
        with self.assertRaises(AccessError):
            self._sign(self.master_plan, "action_approve", self.user_engineer)

    def test_content_is_frozen_after_approval(self):
        """The content cannot be modified once the plan is approved."""
        self.master_plan.action_submit_review()
        self._sign(self.master_plan, "action_approve", self.user_approver)
        with self.assertRaises(UserError):
            self.master_plan.write({"scope": "<p>Changed after approval</p>"})

    def test_new_version_supersedes_the_previous_one(self):
        """Activating a new version supersedes the previous active version."""
        self.master_plan.action_submit_review()
        self._sign(self.master_plan, "action_approve", self.user_approver)
        self.master_plan.action_activate()
        action = self.master_plan.action_new_version()
        new_plan = self.env["ls.validation.master.plan"].browse(action["res_id"])
        self.assertEqual(new_plan.version, 2)
        self.assertEqual(new_plan.previous_version_id, self.master_plan)
        self.assertEqual(new_plan.state, "draft")
        new_plan.action_submit_review()
        self._sign(new_plan, "action_approve", self.user_approver)
        new_plan.action_activate()
        self.assertEqual(self.master_plan.state, "superseded")

    def test_new_version_is_refused_on_a_draft_plan(self):
        """A draft plan has no approved content to version."""
        with self.assertRaises(UserError):
            self.master_plan.action_new_version()

    def test_next_review_date_follows_the_effective_date(self):
        """The next review date is computed from the effective date."""
        self.master_plan.write(
            {"effective_date": "2026-01-31", "review_interval_months": 12}
        )
        self.assertEqual(
            fields.Date.to_string(self.master_plan.next_review_date),
            "2027-01-31",
        )

    def test_active_plan_cannot_be_cancelled_or_deleted(self):
        """An active plan is protected against cancellation and deletion."""
        self.master_plan.action_submit_review()
        self._sign(self.master_plan, "action_approve", self.user_approver)
        self.master_plan.action_activate()
        with self.assertRaises(UserError):
            self.master_plan.action_cancel()
        with self.assertRaises(UserError):
            self.master_plan.unlink()

    def test_draft_plan_can_be_deleted_by_the_manager(self):
        """A draft plan is deletable."""
        plan = self.env["ls.validation.master.plan"].create(
            {"name": "Disposable plan"}
        )
        plan.with_user(self.user_manager).unlink()
        self.assertFalse(plan.exists())
