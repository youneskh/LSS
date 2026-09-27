# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the checklist template lifecycle and of the load wizard."""

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestChecklist(AuditCommon):
    """Approval, versioning, immutability and loading of checklists."""

    def test_approved_checklist_has_approver_and_date(self):
        """Approval records who approved the checklist and when."""
        self.assertEqual(self.checklist.state, "approved")
        self.assertTrue(self.checklist.approved_by_id)
        self.assertTrue(self.checklist.approval_date)

    def test_line_count_is_computed(self):
        """The question count reflects the number of lines."""
        self.assertEqual(self.checklist.line_count, 3)

    def test_empty_checklist_cannot_be_approved(self):
        """A checklist without question cannot be approved."""
        empty = self.env["ls.audit.checklist"].create(
            {
                "name": "Empty Checklist",
                "code": "TEST-EMPTY",
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(UserError):
            empty.action_approve()

    def test_approved_checklist_questions_are_immutable(self):
        """Questions of an approved checklist cannot be modified."""
        with self.assertRaises(UserError):
            self.checklist.line_ids[0].name = "Modified question"

    def test_approved_checklist_questions_cannot_be_deleted(self):
        """Questions of an approved checklist cannot be deleted."""
        with self.assertRaises(UserError):
            self.checklist.line_ids[0].unlink()

    def test_approved_checklist_cannot_receive_new_questions(self):
        """A new question cannot be added to an approved checklist."""
        with self.assertRaises(UserError):
            self.env["ls.audit.checklist.line"].create(
                {
                    "checklist_id": self.checklist.id,
                    "name": "Late addition",
                }
            )

    def test_new_version_creates_a_draft_copy(self):
        """A new version copies the questions and starts in draft."""
        action = self.checklist.action_new_version()
        new_checklist = self.env["ls.audit.checklist"].browse(
            action["res_id"]
        )
        self.assertEqual(new_checklist.version, 2)
        self.assertEqual(new_checklist.state, "draft")
        self.assertEqual(new_checklist.code, self.checklist.code)
        self.assertEqual(new_checklist.line_count, 3)
        self.assertFalse(new_checklist.approved_by_id)

    def test_duplicate_code_and_version_refused(self):
        """A checklist duplicating code and version is rejected."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.cr.savepoint():
                self.env["ls.audit.checklist"].create(
                    {
                        "name": "Clash",
                        "code": self.checklist.code,
                        "version": self.checklist.version,
                        "company_id": self.company.id,
                    }
                )

    def test_used_checklist_cannot_return_to_draft(self):
        """A checklist used by an audit cannot be reset to draft."""
        self._load_checklist()
        with self.assertRaises(UserError):
            self.checklist.action_reset_to_draft()

    def test_unused_checklist_can_return_to_draft(self):
        """An approved but unused checklist can be reset to draft."""
        self.checklist.action_reset_to_draft()
        self.assertEqual(self.checklist.state, "draft")

    def test_obsolete_checklist_cannot_be_loaded(self):
        """An obsolete checklist cannot be loaded into an audit."""
        self.checklist.action_set_obsolete()
        wizard = self.env["ls.audit.checklist.load"].create(
            {"audit_id": self.audit.id, "checklist_id": self.checklist.id}
        )
        with self.assertRaises(UserError):
            wizard.action_load()

    def test_load_copies_question_text(self):
        """Loading copies the question text into the audit."""
        responses = self._load_checklist()
        self.assertEqual(len(responses), 3)
        self.assertEqual(
            set(responses.mapped("name")),
            set(self.checklist.line_ids.mapped("name")),
        )
        self.assertEqual(self.audit.checklist_id, self.checklist)

    def test_loaded_responses_start_pending(self):
        """Loaded questions start without assessment."""
        responses = self._load_checklist()
        self.assertEqual(set(responses.mapped("result")), {"pending"})

    def test_template_change_does_not_alter_executed_audit(self):
        """A later template version does not change a loaded audit."""
        responses = self._load_checklist()
        original_names = set(responses.mapped("name"))
        action = self.checklist.action_new_version()
        new_checklist = self.env["ls.audit.checklist"].browse(
            action["res_id"]
        )
        new_checklist.line_ids[0].name = "Reworded question"
        self.assertEqual(set(self.audit.response_ids.mapped("name")),
                         original_names)

    def test_load_refuses_second_checklist_without_replace(self):
        """Loading over existing questions requires explicit replacement."""
        self._load_checklist()
        wizard = self.env["ls.audit.checklist.load"].create(
            {
                "audit_id": self.audit.id,
                "checklist_id": self.checklist.id,
                "replace_existing": False,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_load()

    def test_load_refused_once_fieldwork_started(self):
        """A checklist cannot be loaded after the fieldwork started."""
        self._bring_audit_to_in_progress()
        wizard = self.env["ls.audit.checklist.load"].create(
            {
                "audit_id": self.audit.id,
                "checklist_id": self.checklist.id,
                "replace_existing": True,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_load()
