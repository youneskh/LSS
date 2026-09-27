# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Access rights and record rules."""

from odoo.exceptions import AccessError, UserError

from .common import LsQmsCommon


class TestSecurity(LsQmsCommon):
    """Visibility and privileges of the four QMS roles."""

    def test_01_viewer_sees_published_documents_only(self):
        """A viewer does not see drafts."""
        sop = self._create_sop()
        found = (
            self.env["ls.qms.sop"]
            .with_user(self.user_viewer)
            .search([("id", "=", sop.id)])
        )
        self.assertFalse(found)
        self._publish(sop)
        found = (
            self.env["ls.qms.sop"]
            .with_user(self.user_viewer)
            .search([("id", "=", sop.id)])
        )
        self.assertEqual(found, sop)

    def test_02_user_sees_drafts(self):
        """A QMS user sees documents in every state."""
        sop = self._create_sop()
        found = (
            self.env["ls.qms.sop"]
            .with_user(self.user_author)
            .search([("id", "=", sop.id)])
        )
        self.assertEqual(found, sop)

    def test_03_viewer_cannot_create(self):
        """A viewer has no creation right."""
        with self.assertRaises(AccessError):
            self.env["ls.qms.sop"].with_user(self.user_viewer).create(
                {"name": "Forbidden procedure"}
            )

    def test_04_viewer_cannot_write(self):
        """A viewer has no write right on a document.

        A draft is used: on a published document the content lock of the
        module refuses the change (UserError) before the access check.
        """
        sop = self._create_sop()
        with self.assertRaises(AccessError):
            sop.with_user(self.user_viewer).write({"name": "Renamed"})

    def test_05_user_cannot_delete(self):
        """A QMS user has no deletion right."""
        sop = self._create_sop()
        with self.assertRaises(AccessError):
            sop.with_user(self.user_author).unlink()

    def test_06_manager_can_delete_a_draft(self):
        """A QMS manager deletes a draft document."""
        sop = self._create_sop()
        self.assertTrue(sop.with_user(self.user_manager).unlink())

    def test_07_user_cannot_approve(self):
        """A QMS user without the approver role cannot approve."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_approve()

    def test_08_user_cannot_publish(self):
        """A QMS user without the approver role cannot publish."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        sop.with_user(self.user_approver).action_approve()
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_publish()

    def test_09_group_hierarchy(self):
        """Each role implies the previous one."""
        self.assertTrue(
            self.user_manager.has_group("ls_qms.group_ls_qms_approver")
        )
        self.assertTrue(
            self.user_manager.has_group("ls_qms.group_ls_qms_user")
        )
        self.assertTrue(
            self.user_approver.has_group("ls_qms.group_ls_qms_user")
        )
        self.assertTrue(
            self.user_author.has_group("ls_qms.group_ls_qms_viewer")
        )
        self.assertFalse(
            self.user_author.has_group("ls_qms.group_ls_qms_approver")
        )

    def test_10_viewer_cannot_read_draft_quality_plan(self):
        """The viewer restriction applies to every document type."""
        plan = self._create_quality_plan()
        found = (
            self.env["ls.qms.quality_plan"]
            .with_user(self.user_viewer)
            .search([("id", "=", plan.id)])
        )
        self.assertFalse(found)

    def test_11_viewer_reads_objectives(self):
        """Objectives are readable by viewers, they are not documents."""
        objective = self._create_objective()
        found = (
            self.env["ls.qms.objective"]
            .with_user(self.user_viewer)
            .search([("id", "=", objective.id)])
        )
        self.assertEqual(found, objective)
