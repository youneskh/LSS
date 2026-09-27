# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the folder hierarchy and its integrity rules."""

from odoo.exceptions import UserError, ValidationError

from .common import LsDocumentCommon


class TestLsDocumentFolder(LsDocumentCommon):
    """Folder hierarchy, computed path and deletion guards."""

    def test_complete_name_root(self):
        """A root folder exposes its own name as full path."""
        self.assertEqual(self.folder.complete_name, "Test Root Folder")

    def test_complete_name_child(self):
        """A child folder exposes the concatenated path."""
        self.assertEqual(
            self.child_folder.complete_name,
            "Test Root Folder / Test Child Folder",
        )

    def test_complete_name_is_recomputed_on_parent_rename(self):
        """Renaming a parent updates the path of its descendants."""
        self.folder.name = "Renamed Root"
        self.assertEqual(
            self.child_folder.complete_name, "Renamed Root / Test Child Folder"
        )

    def test_direct_self_parenting_is_rejected(self):
        """A folder cannot be its own parent."""
        # Odoo 19 detects the cycle while maintaining parent_path and raises
        # UserError ("Recursion Detected."), the parent class of
        # ValidationError, before the module constraint runs.
        with self.assertRaises(UserError):
            self.folder.parent_id = self.folder

    def test_indirect_cycle_is_rejected(self):
        """A folder cannot become a descendant of one of its descendants."""
        with self.assertRaises(UserError):
            self.folder.parent_id = self.child_folder

    def test_deep_cycle_is_rejected(self):
        """Cycle detection also covers three-level hierarchies."""
        grand_child = self.env["ls.document.folder"].create(
            {"name": "Grand Child", "parent_id": self.child_folder.id}
        )
        with self.assertRaises(UserError):
            self.folder.parent_id = grand_child

    def test_child_count(self):
        """The sub-folder counter reflects the direct children."""
        self.assertEqual(self.folder.child_count, 1)
        self.assertEqual(self.child_folder.child_count, 0)

    def test_document_count(self):
        """The document counter reflects the documents of the folder."""
        self.assertEqual(self.folder.document_count, 0)
        self._create_document()
        self.folder.invalidate_recordset()
        self.assertEqual(self.folder.document_count, 1)

    def test_unlink_blocked_when_documents_present(self):
        """A folder holding documents cannot be deleted."""
        self._create_document()
        with self.assertRaises(ValidationError):
            self.folder.unlink()

    def test_unlink_blocked_when_children_present(self):
        """A folder holding sub-folders cannot be deleted."""
        with self.assertRaises(ValidationError):
            self.folder.unlink()

    def test_unlink_allowed_when_empty(self):
        """An empty folder can be deleted."""
        empty = self.env["ls.document.folder"].create({"name": "Empty"})
        self.assertTrue(empty.unlink())

    def test_company_consistency_between_parent_and_child(self):
        """A sub-folder must share the company of its parent."""
        other_company = self.env["res.company"].create({"name": "Second Company"})
        with self.assertRaises(ValidationError):
            self.child_folder.company_id = other_company

    def test_action_open_documents_filters_on_folder(self):
        """The stat button action is restricted to the folder documents."""
        action = self.folder.action_open_documents()
        self.assertEqual(action["res_model"], "ls.document.document")
        self.assertIn(("folder_id", "=", self.folder.id), action["domain"])
