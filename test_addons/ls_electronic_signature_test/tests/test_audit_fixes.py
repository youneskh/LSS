# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Regression tests for the findings of the 2026-09-25 audit.

F-02 authorised signers include users holding the signer group through an
implied group, F-11 the password typed in the signature dialog is never
stored.
"""

from odoo.tests import tagged

from .common import SIGNER_PASSWORD, SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestAuditFixes(SignatureCase):
    """Behaviour restored by the 2026-09-25 remediation."""

    def _wizard(self, password):
        """Create the signature dialog as the signer would save it."""
        return self.Wizard.with_user(self.signer).create(
            {
                "res_model": self.record._name,
                "res_id": self.record.id,
                "meaning_id": self.meaning_approved.id,
                "login": self.signer.login,
                "password": password,
                "consent": True,
            }
        )

    def test_password_column_does_not_exist(self):
        """No column of the wizard table can hold the password."""
        self.env.cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'ls_signature_wizard' AND column_name = 'password'"
        )
        self.assertFalse(self.env.cr.fetchone())

    def test_only_the_verification_outcome_is_kept(self):
        """The submitted password is verified at save time and discarded."""
        wizard = self._wizard(SIGNER_PASSWORD)
        # Read back as the next request of the web client would: the value
        # typed by the signer only lives in the memory of the saving request.
        self.env.flush_all()
        wizard.invalidate_recordset()
        self.assertFalse(wizard.password)
        self.assertEqual(wizard.sudo().password_check, "ok")
        self.assertEqual(wizard.sudo().password_check_uid, self.signer)
        rejected = self._wizard("wrong")
        self.env.flush_all()
        rejected.invalidate_recordset()
        self.assertFalse(rejected.password)
        self.assertEqual(rejected.sudo().password_check, "bad")

    def test_signature_consumes_the_verification(self):
        """A successful signature clears the verification outcome."""
        wizard = self._wizard(SIGNER_PASSWORD)
        wizard.action_sign()
        self.assertFalse(wizard.sudo().password_check)
        self.assertTrue(self._signatures_of())

    def test_signer_group_obtained_through_an_implied_group(self):
        """A user holding the policy group through implication can sign."""
        policy_group = self.env["res.groups"].create({"name": "Policy signers"})
        wrapper_group = self.env["res.groups"].create(
            {"name": "Wrapper", "implied_ids": [(4, policy_group.id)]}
        )
        self.signer.write({"group_ids": [(4, wrapper_group.id)]})
        self.assertNotIn(policy_group, self.signer.group_ids)
        self.assertIn(policy_group, self.signer.all_group_ids)
        policy = self.Policy.create(
            {
                "name": "Implied group policy",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "manual",
                "meaning_id": self.meaning_approved.id,
                "signer_group_ids": [(6, 0, policy_group.ids)],
            }
        )
        self._sign(policy=policy)
        self.assertTrue(self._signatures_of())
