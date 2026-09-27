# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the transaction safeguards of 21 CFR 11.300(d)."""

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureAttempt(TransactionCase):
    """Attempts are an immutable security log driving lockout."""

    @classmethod
    def setUpClass(cls):
        """Create the attempt model handle and disable the isolated cursor."""
        super().setUpClass()
        cls.Attempt = cls.env["ls.signature.attempt"]
        # The isolated cursor is disabled so that rows written by the tests are
        # visible inside the test transaction.
        cls.env["ir.config_parameter"].sudo().set_param(
            "ls_electronic_signature.attempt_isolated_cursor", "0"
        )

    def _fail(self, login="ls.lockout.probe"):
        """Record one failed attempt for ``login``."""
        return self.Attempt.record(
            {
                "user_id": self.env.uid,
                "login_attempted": login,
                "result": "invalid_password",
            }
        )

    def test_attempt_cannot_be_modified(self):
        """The security log refuses modification."""
        attempt = self._fail()
        with self.assertRaises(UserError):
            attempt.write({"detail": "tampered"})

    def test_attempt_cannot_be_deleted(self):
        """The security log refuses deletion."""
        attempt = self._fail()
        with self.assertRaises(UserError):
            attempt.unlink()

    def test_login_is_not_locked_out_initially(self):
        """An unknown identification code is not blocked."""
        self.assertFalse(self.Attempt.is_locked_out("ls.fresh.probe"))

    def test_lockout_after_configured_failures(self):
        """Reaching the failure threshold blocks further attempts."""
        threshold = self.Attempt._max_failures()
        for _index in range(threshold):
            self._fail()
        self.assertTrue(self.Attempt.is_locked_out("ls.lockout.probe"))

    def test_below_threshold_does_not_lock_out(self):
        """One failure short of the threshold does not block."""
        threshold = self.Attempt._max_failures()
        for _index in range(threshold - 1):
            self._fail("ls.partial.probe")
        self.assertFalse(self.Attempt.is_locked_out("ls.partial.probe"))

    def test_success_clears_the_lockout(self):
        """A successful signature inside the window unblocks the code."""
        threshold = self.Attempt._max_failures()
        for _index in range(threshold):
            self._fail("ls.recover.probe")
        self.assertTrue(self.Attempt.is_locked_out("ls.recover.probe"))
        self.Attempt.record(
            {
                "user_id": self.env.uid,
                "login_attempted": "ls.recover.probe",
                "result": "success",
            }
        )
        self.assertFalse(self.Attempt.is_locked_out("ls.recover.probe"))

    def test_empty_login_is_never_locked_out(self):
        """A missing identification code is handled without error."""
        self.assertFalse(self.Attempt.is_locked_out(""))

    def test_security_unit_recipients_resolve_from_the_group(self):
        """The notification list is derived from the security unit group."""
        group = self.env.ref("ls_electronic_signature.group_ls_signature_security")
        self.env["res.users"].create(
            {
                "name": "Security Probe",
                "login": "ls.security.probe",
                "email": "security.probe@example.invalid",
                "group_ids": [(4, group.id), (4, self.env.ref("base.group_user").id)],
            }
        )
        self.assertIn(
            "security.probe@example.invalid",
            self.Attempt._security_unit_recipients(),
        )

    def test_invalid_threshold_parameter_falls_back_to_default(self):
        """A malformed threshold does not disable the lockout control."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_electronic_signature.max_failed_attempts", "zero"
        )
        self.assertEqual(self.Attempt._max_failures(), 3)
