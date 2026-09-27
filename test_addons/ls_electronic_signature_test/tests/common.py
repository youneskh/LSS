# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Shared fixtures for the electronic signature integration tests."""

from odoo.tests import TransactionCase

#: Password given to every fixture signer. It is only ever used against the
#: throwaway accounts created by the test suite.
SIGNER_PASSWORD = "Fixture-Signer-Password-1"


class SignatureCase(TransactionCase):
    """Base case providing a signable record and authorised signers."""

    @classmethod
    def setUpClass(cls):
        """Create signable fixtures, meanings and authorised signer accounts."""
        super().setUpClass()
        cls.Log = cls.env["ls.signature.log"]
        cls.Policy = cls.env["ls.signature.policy"]
        cls.Wizard = cls.env["ls.signature.wizard"]
        cls.Attempt = cls.env["ls.signature.attempt"]
        cls.Record = cls.env["ls.signature.test.record"]

        # Attempts are written on the test cursor so that they are visible
        # inside the test transaction.
        cls.env["ir.config_parameter"].sudo().set_param(
            "ls_electronic_signature.attempt_isolated_cursor", "0"
        )

        cls.group_signer = cls.env.ref(
            "ls_electronic_signature.group_ls_signature_signer"
        )
        cls.group_viewer = cls.env.ref(
            "ls_electronic_signature.group_ls_signature_viewer"
        )
        cls.group_manager = cls.env.ref(
            "ls_electronic_signature.group_ls_signature_manager"
        )
        cls.group_internal = cls.env.ref("base.group_user")

        cls.meaning_approved = cls.env.ref(
            "ls_electronic_signature.meaning_approved"
        )
        cls.meaning_reviewed = cls.env.ref(
            "ls_electronic_signature.meaning_reviewed"
        )
        cls.meaning_rejected = cls.env.ref(
            "ls_electronic_signature.meaning_rejected"
        )

        cls.signer = cls._make_signer("ls.test.signer.one")
        cls.second_signer = cls._make_signer("ls.test.signer.two")

        cls.record = cls.Record.create(
            {"name": "Fixture Record", "state": "review", "quantity": 10.0}
        )

    @classmethod
    def _make_signer(cls, login):
        """Create an internal user holding the Signer role."""
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "password": SIGNER_PASSWORD,
                "group_ids": [
                    (6, 0, [cls.group_internal.id, cls.group_signer.id])
                ],
            }
        )

    def _sign(
        self,
        record=None,
        user=None,
        meaning=None,
        password=SIGNER_PASSWORD,
        reason=None,
        policy=None,
        consent=True,
        login=None,
    ):
        """Execute a signature through the wizard, as a signer would.

        :returns: The action returned by the wizard.
        """
        record = record if record is not None else self.record
        user = user or self.signer
        meaning = meaning or self.meaning_approved
        wizard = self.Wizard.with_user(user).create(
            {
                "res_model": record._name,
                "res_id": record.id,
                "meaning_id": meaning.id,
                "policy_id": policy.id if policy else False,
                "login": login if login is not None else user.login,
                "password": password,
                "reason": reason,
                "consent": consent,
            }
        )
        return wizard.action_sign()

    def _signatures_of(self, record=None):
        """Return the signatures recorded against ``record``."""
        record = record if record is not None else self.record
        return self.Log.search(
            [("res_model", "=", record._name), ("res_id", "=", record.id)],
            order="chain_sequence asc",
        )
