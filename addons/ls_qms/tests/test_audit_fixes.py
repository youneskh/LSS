# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Regression tests for the findings of the 2026-09-25 audit.

F-24 cross-company references refused by the ORM, F-39 revision of a
quality plan.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsQmsCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(LsQmsCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def test_quality_plan_revision(self):
        """A published quality plan can be revised with its control lines."""
        plan = self._publish(self._create_quality_plan())
        revision = plan.with_user(self.user_author).create_new_revision(
            "Annual review of the controls."
        )
        self.assertEqual(revision.previous_revision_id, plan)
        self.assertIn(revision, plan.next_revision_ids)
        self.assertEqual(revision.version, plan.version + 1)
        self.assertEqual(len(revision.line_ids), len(plan.line_ids))
        self.assertEqual(plan.state, "under_revision")

    def test_objective_refuses_a_policy_of_another_company(self):
        """An objective cannot reference a policy of another company."""
        other_company = self.env["res.company"].create({"name": "QMS fix other"})
        policy = self._create_policy(company_id=other_company.id)
        with self.assertRaises(UserError):
            self._create_objective(policy_id=policy.id)
