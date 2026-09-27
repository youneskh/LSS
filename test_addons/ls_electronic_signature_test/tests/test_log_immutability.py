# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests that the signature log is append only at every layer."""

import psycopg2

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureImmutability(SignatureCase):
    """Modification and deletion are refused by the ORM and by PostgreSQL."""

    def setUp(self):
        """Execute one signature so each test has a target to attack."""
        super().setUp()
        self._sign()
        self.signature = self._signatures_of()[-1]

    def test_write_is_refused(self):
        """A field cannot be changed through the ORM."""
        with self.assertRaises(UserError):
            self.signature.write({"reason": "tampered"})

    def test_write_is_refused_even_with_sudo(self):
        """Elevated rights do not permit modification."""
        with self.assertRaises(UserError):
            self.signature.sudo().write({"reason": "tampered"})

    def test_unlink_is_refused(self):
        """A signature cannot be deleted through the ORM."""
        with self.assertRaises(UserError):
            self.signature.unlink()

    def test_unlink_is_refused_even_with_sudo(self):
        """Elevated rights do not permit deletion."""
        with self.assertRaises(UserError):
            self.signature.sudo().unlink()

    @mute_logger("odoo.sql_db")
    def test_direct_sql_update_is_refused_by_postgresql(self):
        """The database trigger refuses a direct UPDATE."""
        state = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.db_immutability_trigger")
        )
        if state != "installed":
            self.skipTest("Database immutability trigger was not installed.")
        with self.assertRaises(psycopg2.errors.RaiseException):
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "UPDATE ls_signature_log SET reason = %s WHERE id = %s",
                    ("tampered", self.signature.id),
                )

    @mute_logger("odoo.sql_db")
    def test_direct_sql_delete_is_refused_by_postgresql(self):
        """The database trigger refuses a direct DELETE."""
        state = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.db_immutability_trigger")
        )
        if state != "installed":
            self.skipTest("Database immutability trigger was not installed.")
        with self.assertRaises(psycopg2.errors.RaiseException):
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "DELETE FROM ls_signature_log WHERE id = %s", (self.signature.id,)
                )

    @mute_logger("odoo.sql_db")
    def test_signer_account_cannot_be_deleted(self):
        """A user who has signed cannot be removed, only archived."""
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            with self.env.cr.savepoint():
                self.signer.sudo().unlink()

    def test_signer_account_can_be_archived(self):
        """Deactivating a signer is permitted and preserves the signature."""
        self.signer.sudo().write({"active": False})
        self.signature.invalidate_recordset()
        self.assertTrue(self.signature.signer_name)
