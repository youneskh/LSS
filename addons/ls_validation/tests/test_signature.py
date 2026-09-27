# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the electronic signature log and of the signature mixin."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from ..models.ls_validation_constants import PARAM_PASSWORD_REQUIRED
from ..models.ls_validation_signature import GENESIS_HASH
from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestSignature(ValidationCommon):
    """Signature creation, immutability and hash chaining."""

    def test_signature_is_created_with_chained_hash(self):
        """The first signature chains on the genesis hash, the next on it."""
        first = self.item._ls_create_signature(meaning="verified")
        self.assertEqual(first.res_model, "ls.validation.item")
        self.assertEqual(first.res_id, self.item.id)
        self.assertEqual(len(first.signature_hash), 64)
        second = self.master_plan._ls_create_signature(meaning="reviewed")
        self.assertEqual(second.previous_hash, first.signature_hash)
        self.assertNotEqual(second.signature_hash, first.signature_hash)

    def test_first_signature_of_company_uses_genesis_hash(self):
        """A company without signature starts the chain on the genesis hash."""
        company = self.env["res.company"].create({"name": "Second Company"})
        signature = self.env["ls.validation.signature"].create(
            {
                "res_model": "ls.validation.item",
                "res_id": self.item.id,
                "meaning": "verified",
                "company_id": company.id,
            }
        )
        self.assertEqual(signature.previous_hash, GENESIS_HASH)

    def test_signature_cannot_be_modified(self):
        """Writing on a signature is refused."""
        signature = self.item._ls_create_signature(meaning="verified")
        with self.assertRaises(UserError):
            signature.write({"reason": "tampered"})

    def test_signature_cannot_be_deleted(self):
        """Deleting a signature is refused, including for the manager."""
        signature = self.item._ls_create_signature(meaning="verified")
        with self.assertRaises(UserError):
            signature.with_user(self.user_manager).unlink()

    def test_verify_chain_reports_a_valid_chain(self):
        """A chain built by the module verifies successfully."""
        self.item._ls_create_signature(meaning="verified")
        self.master_plan._ls_create_signature(meaning="reviewed")
        result = self.env["ls.validation.signature"].verify_chain(
            company_id=self.company.id
        )
        self.assertTrue(result["valid"])
        self.assertFalse(result["first_broken_id"])
        self.assertEqual(result["checked"], 2)

    def test_verify_chain_detects_a_broken_chain(self):
        """Altering a hash directly in the database breaks the verification."""
        signature = self.item._ls_create_signature(meaning="verified")
        self.env.cr.execute(
            "UPDATE ls_validation_signature SET reason = %s WHERE id = %s",
            ("tampered", signature.id),
        )
        self.env.cr.execute(
            "UPDATE ls_validation_signature SET signed_on = signed_on "
            "+ interval '1 hour' WHERE id = %s",
            (signature.id,),
        )
        signature.invalidate_recordset()
        result = self.env["ls.validation.signature"].verify_chain(
            company_id=self.company.id
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["first_broken_id"], signature.id)

    def test_signature_count_is_exposed_on_the_record(self):
        """The mixin exposes the signatures of the record."""
        self.assertEqual(self.item.signature_count, 0)
        self.item._ls_create_signature(meaning="verified")
        self.item.invalidate_recordset()
        self.assertEqual(self.item.signature_count, 1)

    def test_callback_must_be_whitelisted(self):
        """A callback outside the whitelist is refused by the wizard."""
        wizard = self.env["ls.validation.sign.wizard"].create(
            {
                "res_model": "ls.validation.master.plan",
                "res_id": self.master_plan.id,
                "meaning": "approved",
                "callback": "unlink",
                "login": self.env.user.login,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_sign()

    def test_wrong_login_is_refused(self):
        """A login different from the connected user is refused."""
        with self.assertRaises(ValidationError):
            self.item.with_user(self.user_engineer)._ls_verify_credentials(
                "someone_else", "irrelevant"
            )

    def test_missing_password_is_refused(self):
        """An empty password is refused when the password is required."""
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_PASSWORD_REQUIRED, "1"
        )
        item = self.item.with_user(self.user_engineer)
        with self.assertRaises(ValidationError):
            item._ls_verify_credentials(self.user_engineer.login, "")

    def test_wrong_password_is_refused(self):
        """A wrong password is refused when the password is required.

        This test exercises the version compatibility shim that adapts to the
        signature of ``res.users._check_credentials``.
        """
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_PASSWORD_REQUIRED, "1"
        )
        self.user_engineer.password = "Str0ng-Test-Password"
        item = self.item.with_user(self.user_engineer)
        with self.assertRaises(ValidationError):
            item._ls_verify_credentials(
                self.user_engineer.login, "not-the-password"
            )

    def test_correct_password_is_accepted(self):
        """The correct password lets the signature be recorded."""
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_PASSWORD_REQUIRED, "1"
        )
        self.user_engineer.password = "Str0ng-Test-Password"
        item = self.item.with_user(self.user_engineer)
        item._ls_verify_credentials(
            self.user_engineer.login, "Str0ng-Test-Password"
        )
        signature = item._ls_create_signature(meaning="verified")
        self.assertEqual(signature.user_id, self.user_engineer)
