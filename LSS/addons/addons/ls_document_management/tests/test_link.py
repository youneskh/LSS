# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the links between documents and other Odoo records."""

from odoo.exceptions import ValidationError

from .common import LsDocumentCommon


class TestLsDocumentLink(LsDocumentCommon):
    """Creation, resolution and validation of document links."""

    def setUp(self):
        """Create a document and a partner used as link target."""
        super().setUp()
        self.document = self._create_document()
        self.partner = self.env["res.partner"].create({"name": "Linked Partner"})

    def _create_link(self, **values):
        """Create a link to the test partner.

        :param values: field values overriding the defaults.
        :return: the created ``ls.document.link`` record.
        """
        defaults = {
            "document_id": self.document.id,
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "relation_type": "applies_to",
        }
        defaults.update(values)
        return self.env["ls.document.link"].create(defaults)

    def test_link_resolves_the_target_name(self):
        """The link displays the name of the target record."""
        link = self._create_link()
        self.assertEqual(link.res_name, "Linked Partner")

    def test_link_count_on_document(self):
        """The document counts its links."""
        self._create_link()
        self.document.invalidate_recordset()
        self.assertEqual(self.document.link_count, 1)

    def test_unknown_model_is_rejected(self):
        """A link to a model that is not installed is refused."""
        with self.assertRaises(ValidationError):
            self._create_link(res_model="ls.model.that.does.not.exist")

    def test_deleted_target_is_reported(self):
        """A link whose target was deleted reports it explicitly."""
        link = self._create_link()
        self.partner.unlink()
        link.invalidate_recordset()
        link._compute_res_name()
        self.assertIn("Deleted record", link.res_name)

    def test_company_is_inherited_from_document(self):
        """The link belongs to the company of its document."""
        link = self._create_link()
        self.assertEqual(link.company_id, self.document.company_id)

    def test_open_linked_record_action(self):
        """The action opens the form view of the target record."""
        link = self._create_link()
        action = link.action_open_linked_record()
        self.assertEqual(action["res_model"], "res.partner")
        self.assertEqual(action["res_id"], self.partner.id)

    def test_links_are_removed_with_the_document(self):
        """Deleting a draft document removes its links."""
        link = self._create_link()
        self.document.unlink()
        self.assertFalse(link.exists())
