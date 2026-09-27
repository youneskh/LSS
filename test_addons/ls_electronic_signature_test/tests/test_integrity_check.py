# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the scheduled chain verification."""

from odoo.tests import tagged

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestIntegrityCheck(SignatureCase):
    """Verification results are recorded as evidence in their own right."""

    def test_clean_chain_passes(self):
        """A chain with no divergence records a passing check."""
        self._sign()
        check = self.env["ls.signature.integrity.check"].run(self.env.company)
        self.assertEqual(check.state, "passed")
        self.assertGreaterEqual(check.entries_checked, 1)
        self.assertFalse(check.first_divergence_log_id)

    def test_manual_trigger_is_recorded(self):
        """A manually started check records who started it."""
        check = self.env["ls.signature.integrity.check"].run(
            self.env.company, trigger="manual"
        )
        self.assertEqual(check.trigger, "manual")
        self.assertEqual(check.checked_by_id, self.env.user)

    def test_scheduled_run_covers_every_company(self):
        """The scheduled action produces one check per company."""
        companies = self.env["res.company"].search([])
        created = self.env["ls.signature.integrity.check"]._cron_verify_all_companies()
        self.assertEqual(created, len(companies))

    def test_tampered_chain_fails(self):
        """A payload altered in SQL produces a failing check."""
        self._sign()
        signature = self._signatures_of()[-1]
        self.env.cr.execute("ALTER TABLE ls_signature_log DISABLE TRIGGER USER")
        self.env.cr.execute(
            "UPDATE ls_signature_log SET payload_json = %s WHERE id = %s",
            ('{"tampered":true}', signature.id),
        )
        self.env.cr.execute("ALTER TABLE ls_signature_log ENABLE TRIGGER USER")
        self.Log.invalidate_model()
        check = self.env["ls.signature.integrity.check"].run(self.env.company)
        self.assertEqual(check.state, "failed")
        self.assertTrue(check.details)
        self.assertEqual(check.first_divergence_log_id, signature)
