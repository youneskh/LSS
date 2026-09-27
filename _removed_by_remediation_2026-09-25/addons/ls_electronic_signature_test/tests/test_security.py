# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Access right and record rule tests."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureSecurity(SignatureCase):
    """No role may alter evidence; visibility follows the role."""

    @classmethod
    def setUpClass(cls):
        """Create one user per role so visibility can be compared."""
        super().setUpClass()
        cls.viewer = cls.env["res.users"].create(
            {
                "name": "Viewer probe",
                "login": "ls.security.viewer",
                "groups_id": [
                    (6, 0, [cls.group_internal.id, cls.group_viewer.id])
                ],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Manager probe",
                "login": "ls.security.manager",
                "groups_id": [
                    (6, 0, [cls.group_internal.id, cls.group_manager.id])
                ],
            }
        )
        cls.outsider = cls.env["res.users"].create(
            {
                "name": "Outsider probe",
                "login": "ls.security.outsider",
                "groups_id": [(6, 0, [cls.group_internal.id])],
            }
        )

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_outsider_cannot_read_the_log(self):
        """A user without any signature role cannot read signatures."""
        self._sign()
        with self.assertRaises(AccessError):
            self.Log.with_user(self.outsider).search([])

    def test_signer_sees_only_their_own_signatures(self):
        """A plain signer is restricted to signatures they executed."""
        self._sign(user=self.signer)
        self._sign(user=self.second_signer, meaning=self.meaning_reviewed)
        visible = self.Log.with_user(self.signer).search([])
        self.assertTrue(visible)
        self.assertEqual(set(visible.mapped("user_id")), {self.signer})

    def test_viewer_sees_every_signature(self):
        """A viewer sees signatures executed by others."""
        self._sign(user=self.signer)
        self._sign(user=self.second_signer, meaning=self.meaning_reviewed)
        visible = self.Log.with_user(self.viewer).search([])
        self.assertGreaterEqual(len(set(visible.mapped("user_id"))), 2)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_manager_cannot_write_a_signature(self):
        """The highest role still cannot alter a signature."""
        self._sign()
        signature = self._signatures_of()[-1]
        with self.assertRaises((AccessError, UserError)):
            signature.with_user(self.manager).write({"reason": "tampered"})

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_manager_cannot_delete_a_signature(self):
        """The highest role still cannot delete a signature."""
        self._sign()
        signature = self._signatures_of()[-1]
        with self.assertRaises((AccessError, UserError)):
            signature.with_user(self.manager).unlink()

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_signer_cannot_configure_meanings(self):
        """Configuration is reserved to the manager role."""
        with self.assertRaises(AccessError):
            self.env["ls.signature.meaning"].with_user(self.signer).create(
                {"code": "SNEAKY", "name": "Sneaky"}
            )

    def test_manager_can_configure_meanings(self):
        """The manager role may create configuration records."""
        meaning = self.env["ls.signature.meaning"].with_user(self.manager).create(
            {"code": "MANAGED", "name": "Managed"}
        )
        self.assertTrue(meaning)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_signer_cannot_read_attempts(self):
        """The security log is not visible to ordinary signers."""
        with self.assertRaises(AccessError):
            self.Attempt.with_user(self.signer).search([])

    def test_auditor_can_read_attempts(self):
        """The auditor role reads the security log."""
        self.assertIsNotNone(self.Attempt.with_user(self.manager).search([]))

    def test_signature_creation_is_permitted_to_signers(self):
        """A signer holds create rights, which signing requires."""
        access = self.env["ir.model.access"].search(
            [
                ("model_id.model", "=", "ls.signature.log"),
                ("group_id", "=", self.group_signer.id),
            ]
        )
        self.assertTrue(access.perm_create)
        self.assertFalse(access.perm_write)
        self.assertFalse(access.perm_unlink)

    def test_signer_cannot_attribute_a_signature_to_someone_else(self):
        """A crafted create call cannot forge another person's signature."""
        payload = '{"schema":1,"forged":true}'
        forged = self.Log.with_user(self.signer).create(
            {
                "user_id": self.second_signer.id,
                "signer_name": self.second_signer.name,
                "signer_login": self.second_signer.login,
                "meaning_id": self.meaning_approved.id,
                "meaning_code": self.meaning_approved.code,
                "meaning_name": self.meaning_approved.name,
                "res_model": self.record._name,
                "res_id": self.record.id,
                "payload_json": payload,
                "authentication_method": "full",
            }
        )
        self.assertEqual(forged.user_id, self.signer)
        self.assertEqual(forged.signer_login, self.signer.login)
        self.assertNotEqual(forged.signer_login, self.second_signer.login)
