# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the signature execution wizard."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SIGNER_PASSWORD, SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureWizard(SignatureCase):
    """Every control in the signing sequence is exercised."""

    def test_correct_credentials_produce_a_signature(self):
        """A valid signature is recorded and the dialog closes."""
        action = self._sign()
        self.assertEqual(action["type"], "ir.actions.act_window_close")
        self.assertEqual(len(self._signatures_of()), 1)

    def test_wrong_password_is_refused(self):
        """An incorrect password refuses the signature."""
        with self.assertRaises(UserError):
            self._sign(password="wrong-password")
        self.assertFalse(self._signatures_of())

    def test_missing_password_is_refused(self):
        """An empty password refuses the signature."""
        with self.assertRaises(UserError):
            self._sign(password="")

    def test_identity_mismatch_is_refused(self):
        """Signing under another identification code is refused."""
        with self.assertRaises(UserError):
            self._sign(login=self.second_signer.login)
        self.assertFalse(self._signatures_of())

    def test_consent_is_required(self):
        """The binding statement must be acknowledged."""
        with self.assertRaises(UserError):
            self._sign(consent=False)

    def test_mandatory_reason_is_enforced(self):
        """A meaning flagged as requiring a reason refuses an empty one."""
        with self.assertRaises(UserError):
            self._sign(meaning=self.meaning_rejected, reason="   ")
        self._sign(meaning=self.meaning_rejected, reason="Out of specification")
        self.assertEqual(self._signatures_of()[-1].meaning_code, "REJECTED")

    def test_unauthorised_meaning_is_refused(self):
        """A meaning restricted to a group the signer lacks is refused."""
        group = self.env["res.groups"].create({"name": "Wizard probe group"})
        restricted = self.env["ls.signature.meaning"].create(
            {
                "code": "RESTRICTED_PROBE",
                "name": "Restricted",
                "group_ids": [(6, 0, group.ids)],
            }
        )
        with self.assertRaises(UserError):
            self._sign(meaning=restricted)

    def test_unauthorised_policy_signer_is_refused(self):
        """A signer outside the policy's authorised groups is refused."""
        group = self.env["res.groups"].create({"name": "Policy probe group"})
        policy = self.Policy.create(
            {
                "name": "Restricted release",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "manual",
                "meaning_id": self.meaning_approved.id,
                "signer_group_ids": [(6, 0, group.ids)],
            }
        )
        with self.assertRaises(UserError):
            self._sign(policy=policy)

    def _sign_expecting_refusal(self, **kwargs):
        """Sign and assert that the signature is refused.

        ``assertRaises`` of the Odoo test case rolls back a savepoint when
        the exception is raised, which would also discard the attempt log
        written in the same transaction (the isolated cursor is disabled in
        tests). The refusal is therefore caught without a savepoint.
        """
        try:
            self._sign(**kwargs)
        except UserError:
            return
        self.fail("The signature was not refused.")

    def test_lockout_blocks_further_attempts(self):
        """Repeated failures block the identification code."""
        threshold = self.Attempt._max_failures()
        for _index in range(threshold):
            self._sign_expecting_refusal(password="wrong-password")
        self._sign_expecting_refusal(password=SIGNER_PASSWORD)
        self.assertFalse(self._signatures_of())

    def test_every_failure_is_logged(self):
        """A refused signature leaves a security log entry."""
        before = self.Attempt.search_count([])
        self._sign_expecting_refusal(password="wrong-password")
        self.assertEqual(self.Attempt.search_count([]), before + 1)
        latest = self.Attempt.search([], order="id desc", limit=1)
        self.assertEqual(latest.result, "invalid_password")
        self.assertEqual(latest.login_attempted, self.signer.login)

    def test_success_is_logged_and_linked(self):
        """A successful signature leaves a linked security log entry."""
        self._sign()
        latest = self.Attempt.search([], order="id desc", limit=1)
        self.assertEqual(latest.result, "success")
        self.assertTrue(latest.log_id)

    def test_authentication_method_records_the_components(self):
        """A signature with a password records all components presented."""
        self._sign()
        self.assertEqual(
            self._signatures_of()[-1].authentication_method, "full"
        )

    def test_password_is_required_without_a_web_session(self):
        """No web session means no continuity, so the password is required."""
        wizard = self.Wizard.with_user(self.signer).create(
            {
                "res_model": self.record._name,
                "res_id": self.record.id,
                "meaning_id": self.meaning_approved.id,
            }
        )
        self.assertTrue(wizard.require_password)

    def test_missing_record_is_refused(self):
        """Signing a record that no longer exists is refused."""
        record = self.Record.create({"name": "Doomed"})
        record_id = record.id
        record.unlink()
        wizard = self.Wizard.with_user(self.signer).create(
            {
                "res_model": self.Record._name,
                "res_id": record_id,
                "meaning_id": self.meaning_approved.id,
                "login": self.signer.login,
                "password": SIGNER_PASSWORD,
                "consent": True,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_sign()

    def test_unsignable_model_is_refused(self):
        """A model without the mixin cannot be signed."""
        partner = self.env["res.partner"].create({"name": "Not signable"})
        wizard = self.Wizard.with_user(self.signer).create(
            {
                "res_model": "res.partner",
                "res_id": partner.id,
                "meaning_id": self.meaning_approved.id,
                "login": self.signer.login,
                "password": SIGNER_PASSWORD,
                "consent": True,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_sign()

    def test_binding_statement_is_presented(self):
        """The signer is shown a binding statement before signing."""
        wizard = self.Wizard.with_user(self.signer).create(
            {
                "res_model": self.record._name,
                "res_id": self.record.id,
                "meaning_id": self.meaning_approved.id,
            }
        )
        self.assertTrue(wizard.binding_statement)
