# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for access rights, record rules and folder level access control."""

from odoo.exceptions import AccessError, UserError

from .common import LsDocumentCommon


class TestLsDocumentSecurity(LsDocumentCommon):
    """Model access rights and folder scoped record rules."""

    def setUp(self):
        """Create a document readable by every document role."""
        super().setUp()
        self.document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )
        self._create_version(self.document)

    def test_viewer_can_read(self):
        """A viewer can read controlled documents."""
        document = self.document.with_user(self.user_viewer)
        self.assertEqual(document.name, "Test Document")

    def test_viewer_cannot_write(self):
        """A viewer cannot modify a controlled document."""
        with self.assertRaises(AccessError):
            self.document.with_user(self.user_viewer).write({"name": "Changed"})

    def test_viewer_cannot_create(self):
        """A viewer cannot create a controlled document."""
        with self.assertRaises(AccessError):
            self._create_document(user=self.user_viewer, name="Forbidden")

    def test_editor_can_create_and_write(self):
        """An editor can create and modify documents."""
        document = self._create_document(
            user=self.user_editor, name="Editor document"
        )
        document.write({"name": "Editor document updated"})
        self.assertEqual(document.name, "Editor document updated")

    def test_editor_cannot_unlink(self):
        """An editor cannot delete a controlled document."""
        document = self._create_document(
            user=self.user_editor, name="Editor document"
        )
        with self.assertRaises(AccessError):
            document.unlink()

    def test_manager_can_unlink_draft(self):
        """A manager can delete a draft document."""
        document = self._create_document(
            user=self.user_manager, name="Manager document"
        )
        self.assertTrue(document.with_user(self.user_manager).unlink())

    def test_viewer_cannot_manage_folders(self):
        """A viewer cannot create folders."""
        with self.assertRaises(AccessError):
            self.env["ls.document.folder"].with_user(self.user_viewer).create(
                {"name": "Forbidden folder"}
            )

    def test_editor_cannot_manage_retention_policies(self):
        """An editor cannot create retention policies."""
        with self.assertRaises(AccessError):
            self.env["ls.document.retention_policy"].with_user(
                self.user_editor
            ).create({"name": "Forbidden policy", "code": "NOPE"})

    def test_folder_read_restriction_hides_documents(self):
        """A folder restricted to a group is invisible to other users."""
        self.folder.group_read_ids = [(6, 0, [self.group_manager.id])]
        readable = (
            self.env["ls.document.document"]
            .with_user(self.user_viewer)
            .search([("id", "=", self.document.id)])
        )
        self.assertFalse(readable)

    def test_folder_read_restriction_allows_members(self):
        """A user belonging to the folder read group keeps access."""
        self.folder.group_read_ids = [(6, 0, [self.group_viewer.id])]
        readable = (
            self.env["ls.document.document"]
            .with_user(self.user_viewer)
            .search([("id", "=", self.document.id)])
        )
        self.assertEqual(readable, self.document)

    def test_folder_without_restriction_is_readable(self):
        """A folder with no read group is readable by every role."""
        readable = (
            self.env["ls.document.document"]
            .with_user(self.user_viewer)
            .search([("id", "=", self.document.id)])
        )
        self.assertEqual(readable, self.document)

    def test_manager_bypasses_folder_restriction(self):
        """A manager keeps access to every folder for administration."""
        self.folder.group_read_ids = [(6, 0, [self.group_viewer.id])]
        readable = (
            self.env["ls.document.document"]
            .with_user(self.user_manager)
            .search([("id", "=", self.document.id)])
        )
        self.assertEqual(readable, self.document)

    def test_folder_write_restriction_blocks_editor(self):
        """An editor outside the folder write group cannot modify."""
        self.folder.group_write_ids = [(6, 0, [self.group_manager.id])]
        with self.assertRaises(AccessError):
            self.document.with_user(self.user_editor).write({"name": "Changed"})

    def test_approver_cannot_publish(self):
        """The publication role check rejects an approver."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        with self.assertRaises(UserError):
            self.document.with_user(self.user_approver).action_publish()

    def test_approver_cannot_create_documents(self):
        """An approver cannot author documents, preserving segregation."""
        with self.assertRaises(AccessError):
            self._create_document(user=self.user_approver, name="Forbidden")
