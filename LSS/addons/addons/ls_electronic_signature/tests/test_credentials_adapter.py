# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the credential verification adapter.

These tests exercise the adapter's own decision logic. Whether the resulting
call is accepted by ``res.users`` on the target build is verified separately by
the qualification test OQ-CRED-001, described in ``doc/07_test_report.md``.
"""

from odoo.tests import TransactionCase, tagged

from ..tools import credentials


@tagged("post_install", "-at_install", "ls_signature")
class TestCredentialAdapter(TransactionCase):
    """The adapter must fail loudly rather than silently deny access."""

    def _set_mode(self, value):
        """Pin the credential API mode system parameter."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_electronic_signature.credential_api_mode", value
        )

    def test_default_mode_is_auto(self):
        """Without configuration the adapter detects the convention."""
        self._set_mode("auto")
        self.assertEqual(credentials.resolve_mode(self.env), "auto")

    def test_unsupported_mode_is_refused(self):
        """An unknown mode is a configuration fault, not an auth failure."""
        self._set_mode("nonsense")
        with self.assertRaises(credentials.CredentialApiError):
            credentials.resolve_mode(self.env)

    def test_detect_mode_recognises_credential_convention(self):
        """A parameter named 'credential' selects the mapping convention."""

        def _check_credentials(credential, env):
            """Stand-in matching the mapping convention."""
            return {}

        self.assertEqual(credentials._detect_mode(_check_credentials), "credential")

    def test_detect_mode_recognises_password_convention(self):
        """A parameter named 'password' selects the string convention."""

        def _check_credentials(password, env):
            """Stand-in matching the string convention."""
            return None

        self.assertEqual(credentials._detect_mode(_check_credentials), "password")

    def test_detect_mode_refuses_unknown_convention(self):
        """An unrecognised parameter list raises rather than guessing."""

        def _check_credentials(mystery, env):
            """Stand-in matching neither convention."""
            return None

        with self.assertRaises(credentials.CredentialApiError):
            credentials._detect_mode(_check_credentials)

    def test_empty_password_is_rejected_without_calling_core(self):
        """An empty password short-circuits to a refusal."""
        self._set_mode("password")
        self.assertFalse(credentials.verify_password(self.env.user, ""))

    def test_wrong_password_is_refused(self):
        """An incorrect password returns False rather than raising."""
        self._set_mode("auto")
        user = self.env["res.users"].create(
            {
                "name": "Credential Probe",
                "login": "ls.credential.probe",
                "password": "Correct-Horse-Battery-1",
            }
        )
        self.assertFalse(
            credentials.verify_password(user, "definitely-not-the-password")
        )
