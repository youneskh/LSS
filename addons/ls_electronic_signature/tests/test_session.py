# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for continuous period of controlled system access tracking."""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureSession(TransactionCase):
    """A period is continuous only inside the configured idle window."""

    @classmethod
    def setUpClass(cls):
        """Create a probe user and a deterministic session token digest."""
        super().setUpClass()
        cls.Session = cls.env["ls.signature.session"]
        cls.user = cls.env["res.users"].create(
            {"name": "Session Probe", "login": "ls.session.probe"}
        )
        cls.token = cls.Session._hash_session_token("probe-session-identifier")

    def test_token_hash_is_not_the_raw_identifier(self):
        """The stored digest never equals the session identifier."""
        self.assertNotEqual(self.token, "probe-session-identifier")
        self.assertEqual(len(self.token), 64)

    def test_token_hash_is_stable(self):
        """The same identifier always produces the same digest."""
        self.assertEqual(
            self.token, self.Session._hash_session_token("probe-session-identifier")
        )

    def test_no_session_is_never_continuous(self):
        """Without a web session no continuity can be demonstrated."""
        self.assertFalse(self.Session.is_continuous(self.user, False))

    def test_first_signature_opens_a_session(self):
        """Registering a signature creates the session record."""
        session = self.Session.register_signature(self.user, self.token)
        self.assertTrue(session)
        self.assertEqual(session.signature_count, 1)
        self.assertFalse(session.closed)

    def test_second_signature_increments_the_counter(self):
        """A repeat signature updates rather than duplicates the session."""
        self.Session.register_signature(self.user, self.token)
        session = self.Session.register_signature(self.user, self.token)
        self.assertEqual(session.signature_count, 2)
        self.assertEqual(
            self.Session.search_count(
                [("user_id", "=", self.user.id), ("token_hash", "=", self.token)]
            ),
            1,
        )

    def test_recent_session_is_continuous(self):
        """A session that has just signed is inside the idle window."""
        self.Session.register_signature(self.user, self.token)
        self.assertTrue(self.Session.is_continuous(self.user, self.token))

    def test_stale_session_is_not_continuous(self):
        """A session idle beyond the timeout is no longer continuous."""
        session = self.Session.register_signature(self.user, self.token)
        timeout = self.Session._idle_timeout_minutes()
        session.sudo().write(
            {
                "last_signed_at": fields.Datetime.subtract(
                    fields.Datetime.now(), minutes=timeout + 1
                )
            }
        )
        self.assertFalse(self.Session.is_continuous(self.user, self.token))

    def test_closed_session_is_not_continuous(self):
        """An explicitly closed session cannot be reused."""
        session = self.Session.register_signature(self.user, self.token)
        session.action_close()
        self.assertFalse(self.Session.is_continuous(self.user, self.token))
        self.assertEqual(session.close_reason, "manual")

    def test_cron_closes_stale_sessions(self):
        """The scheduled action closes sessions past the idle window."""
        session = self.Session.register_signature(self.user, self.token)
        timeout = self.Session._idle_timeout_minutes()
        session.sudo().write(
            {
                "last_signed_at": fields.Datetime.subtract(
                    fields.Datetime.now(), minutes=timeout + 5
                )
            }
        )
        self.Session._cron_close_idle_sessions()
        self.assertTrue(session.closed)
        self.assertEqual(session.close_reason, "idle")

    def test_invalid_timeout_parameter_falls_back_to_default(self):
        """A malformed system parameter does not disable the control."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_electronic_signature.session_idle_minutes", "not-a-number"
        )
        self.assertEqual(self.Session._idle_timeout_minutes(), 15)
