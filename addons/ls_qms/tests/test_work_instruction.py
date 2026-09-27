# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Work instruction specific behaviour."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestWorkInstruction(LsQmsCommon):
    """Subordination to the parent procedure."""

    def _create_instruction(self, sop, **values):
        """Return a draft work instruction attached to ``sop``."""
        defaults = {
            "name": "Test Work Instruction",
            "sop_id": sop.id,
            "author_id": self.user_author.id,
            "instruction_body": "<p>Perform the operation.</p>",
        }
        defaults.update(values)
        return self.env["ls.qms.work_instruction"].create(defaults)

    def test_01_reference_prefix(self):
        """A work instruction is numbered with the WI prefix."""
        sop = self._publish(self._create_sop())
        self.assertTrue(self._create_instruction(sop).reference.startswith("WI-"))

    def test_02_body_is_mandatory_before_review(self):
        """A work instruction without body cannot be submitted."""
        sop = self._publish(self._create_sop())
        instruction = self._create_instruction(sop, instruction_body=False)
        with self.assertRaises(UserError):
            instruction.with_user(
                self.user_author
            ).action_submit_for_review()

    def test_03_publication_requires_a_published_procedure(self):
        """A work instruction cannot precede its parent procedure."""
        sop = self._create_sop()
        instruction = self._create_instruction(sop)
        instruction.with_user(self.user_author).action_submit_for_review()
        instruction.with_user(self.user_approver).action_approve()
        with self.assertRaises(UserError):
            instruction.with_user(self.user_approver).action_publish()

    def test_04_publication_succeeds_after_the_procedure(self):
        """Once the procedure is published the instruction follows."""
        sop = self._publish(self._create_sop())
        instruction = self._publish(self._create_instruction(sop))
        self.assertEqual(instruction.state, "published")

    def test_05_parent_procedure_is_required(self):
        """A work instruction without procedure cannot be created."""
        with self.assertRaises(pg_errors.NotNullViolation):
            self.env["ls.qms.work_instruction"].create(
                {
                    "name": "Orphan instruction",
                    "author_id": self.user_author.id,
                }
            )
