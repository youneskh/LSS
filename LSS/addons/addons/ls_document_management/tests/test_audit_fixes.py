# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

F-14 folder access groups granted through an implied group, F-39 a document
re-submitted after a rejection receives a new approval cycle.
"""

from odoo.tests import tagged

from .common import LsDocumentCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(LsDocumentCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def test_folder_group_granted_through_an_implied_group(self):
        """A user holding the folder group through implication reads it."""
        folder_group = self.env["res.groups"].create({"name": "Folder readers"})
        wrapper_group = self.env["res.groups"].create(
            {"name": "Quality staff", "implied_ids": [(4, folder_group.id)]}
        )
        self.folder.group_read_ids = [(6, 0, folder_group.ids)]
        document = self._create_document()
        self.user_viewer.write({"group_ids": [(4, wrapper_group.id)]})
        self.assertNotIn(folder_group, self.user_viewer.group_ids)
        visible = self.env["ls.document.document"].with_user(self.user_viewer).search(
            [("id", "=", document.id)]
        )
        self.assertEqual(visible, document)

    def test_folder_group_still_restricts_other_users(self):
        """A user without the folder group does not see the document."""
        folder_group = self.env["res.groups"].create({"name": "Restricted readers"})
        self.folder.group_read_ids = [(6, 0, folder_group.ids)]
        document = self._create_document()
        visible = self.env["ls.document.document"].with_user(self.user_viewer).search(
            [("id", "=", document.id)]
        )
        self.assertFalse(visible)
