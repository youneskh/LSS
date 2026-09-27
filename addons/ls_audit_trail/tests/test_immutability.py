# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Immutability tests: entries resist modification, including by the superuser."""

from odoo.exceptions import AccessError
from odoo.tests import tagged

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestImmutability(AuditTrailCase):
    """Verify that no ORM path can alter or remove recorded evidence."""

    def setUp(self):
        """Record one entry to operate on."""
        super().setUp()
        self._activate_rule(field_ids=self.field_name.ids)
        self.partner = self.env["res.partner"].create({"name": "Immutable"})
        self.entry = self._entries_for(self.partner, constants.OPERATION_CREATE)
        self.assertTrue(self.entry)

    def test_write_is_refused(self):
        """A business field of a sealed entry cannot be written."""
        with self.assertRaises(AccessError):
            self.entry.sudo().write({"res_name": "tampered"})

    def test_write_of_sealing_fields_is_refused_once_sealed(self):
        """Even the sealing fields cannot be rewritten after sealing."""
        with self.assertRaises(AccessError):
            self.entry.sudo().write({"hash_current": "0" * 64})

    def test_unlink_is_refused_for_the_superuser(self):
        """Deletion through the ORM is refused for every user."""
        with self.assertRaises(AccessError):
            self.entry.sudo().unlink()

    def test_line_write_is_refused(self):
        """A field change line cannot be written."""
        with self.assertRaises(AccessError):
            self.entry.line_ids.sudo().write({"new_value_technical": "tampered"})

    def test_line_unlink_is_refused(self):
        """A field change line cannot be deleted through the ORM."""
        with self.assertRaises(AccessError):
            self.entry.line_ids.sudo().unlink()

    def test_verification_record_is_immutable(self):
        """A verification record cannot be modified or deleted."""
        verification = self.env["ls.audit_trail.verification"].sudo()._ls_run(
            company=self.company
        )
        with self.assertRaises(AccessError):
            verification.write({"result": "passed"})
        with self.assertRaises(AccessError):
            verification.unlink()

    def test_company_with_entries_cannot_be_deleted(self):
        """A company referenced by an entry is protected by the database."""
        self.assertTrue(
            self.log_model.sudo().search_count([("company_id", "=", self.company.id)])
        )
        field = self.log_model._fields["company_id"]
        self.assertEqual(field.ondelete, "restrict")

    def test_user_with_entries_cannot_be_deleted(self):
        """A user referenced by an entry is protected by the database."""
        field = self.log_model._fields["user_id"]
        self.assertEqual(field.ondelete, "restrict")

    def test_audited_record_deletion_does_not_remove_its_entries(self):
        """Entries survive the record they describe."""
        partner_id = self.partner.id
        self.partner.unlink()
        remaining = self.log_model.sudo().search_count(
            [("model_name", "=", "res.partner"), ("res_id", "=", partner_id)]
        )
        self.assertGreaterEqual(remaining, 2)
