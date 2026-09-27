# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality policy specific behaviour."""

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestPolicy(LsQmsCommon):
    """Content completeness and link with the quality objectives."""

    def test_01_reference_prefix(self):
        """A policy is numbered with the POL prefix."""
        policy = self._create_policy()
        self.assertTrue(policy.reference.startswith("POL-"))

    def test_02_statement_is_mandatory_before_review(self):
        """A policy without statement cannot be submitted."""
        policy = self._create_policy(policy_statement=False)
        with self.assertRaises(UserError):
            policy.with_user(self.user_author).action_submit_for_review()

    def test_03_objective_count(self):
        """The counter reflects the objectives linked to the policy."""
        policy = self._create_policy()
        self.assertEqual(policy.objective_count, 0)
        self._create_objective(policy_id=policy.id)
        policy.invalidate_recordset(["objective_ids", "objective_count"])
        self.assertEqual(policy.objective_count, 1)

    def test_04_action_view_objectives(self):
        """The stat button returns an action filtered on the policy."""
        policy = self._create_policy()
        action = policy.action_view_objectives()
        self.assertEqual(action["res_model"], "ls.qms.objective")
        self.assertIn(("policy_id", "=", policy.id), action["domain"])

    def test_05_content_is_frozen_once_published(self):
        """The statement cannot be changed on a published policy."""
        policy = self._publish(self._create_policy())
        with self.assertRaises(UserError):
            policy.write({"policy_statement": "<p>Other statement.</p>"})
