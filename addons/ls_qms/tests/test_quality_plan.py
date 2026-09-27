# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality plans and their control lines."""

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestQualityPlan(LsQmsCommon):
    """Control lines, freezing and revision copy."""

    def test_01_reference_prefix(self):
        """A quality plan is numbered with the QPL prefix."""
        self.assertTrue(
            self._create_quality_plan().reference.startswith("QPL-")
        )

    def test_02_at_least_one_control_line(self):
        """A plan without control line cannot be submitted."""
        plan = self._create_quality_plan(line_ids=[])
        with self.assertRaises(UserError):
            plan.with_user(self.user_author).action_submit_for_review()

    def test_03_line_count_and_company_propagation(self):
        """Lines are counted and inherit the company of the plan."""
        plan = self._create_quality_plan()
        self.assertEqual(plan.line_count, 1)
        self.assertEqual(plan.line_ids.company_id, plan.company_id)

    def test_04_lines_are_frozen_once_published(self):
        """Control lines cannot be changed on a published plan."""
        plan = self._publish(self._create_quality_plan())
        with self.assertRaises(UserError):
            plan.write(
                {
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "stage": "Packaging",
                                "characteristic": "Leaflet presence",
                            },
                        )
                    ]
                }
            )

    def test_05_revision_copies_the_control_lines(self):
        """The next revision starts from a copy of the control plan."""
        plan = self._publish(self._create_quality_plan())
        revision = plan.with_user(self.user_author).create_new_revision(
            "Addition of a packaging control."
        )
        self.assertEqual(revision.line_count, 1)
        self.assertEqual(
            revision.line_ids.characteristic, plan.line_ids.characteristic
        )
        self.assertNotEqual(revision.line_ids, plan.line_ids)

    def test_06_deleting_the_plan_deletes_its_lines(self):
        """Control lines are removed with their draft plan."""
        plan = self._create_quality_plan()
        line = plan.line_ids
        plan.unlink()
        self.assertFalse(line.exists())
