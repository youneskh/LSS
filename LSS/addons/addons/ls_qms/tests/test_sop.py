# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Procedure specific behaviour."""

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestSop(LsQmsCommon):
    """Mandatory sections and link with the work instructions."""

    def test_01_missing_sections_block_the_review(self):
        """Purpose, scope and procedure are required before review."""
        sop = self._create_sop(purpose=False, scope=False, procedure=False)
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_submit_for_review()

    def test_02_partial_content_blocks_the_review(self):
        """A procedure without body cannot be submitted."""
        sop = self._create_sop(procedure=False)
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_submit_for_review()

    def test_03_work_instruction_count(self):
        """The counter reflects the attached work instructions."""
        sop = self._publish(self._create_sop())
        self.assertEqual(sop.work_instruction_count, 0)
        self.env["ls.qms.work_instruction"].create(
            {
                "name": "Instruction",
                "sop_id": sop.id,
                "author_id": self.user_author.id,
                "instruction_body": "<p>Do this.</p>",
            }
        )
        sop.invalidate_recordset(
            ["work_instruction_ids", "work_instruction_count"]
        )
        self.assertEqual(sop.work_instruction_count, 1)

    def test_04_action_view_work_instructions(self):
        """The stat button returns an action filtered on the procedure."""
        sop = self._create_sop()
        action = sop.action_view_work_instructions()
        self.assertEqual(action["res_model"], "ls.qms.work_instruction")
        self.assertIn(("sop_id", "=", sop.id), action["domain"])

    def test_05_training_flag_defaults_to_true(self):
        """A procedure requires training by default."""
        self.assertTrue(self._create_sop().training_required)
