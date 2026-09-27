# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for signature request routing and lifecycle."""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureRequest(SignatureCase):
    """A request routes and expires but never produces a signature itself."""

    def _make_request(self, **overrides):
        """Create a signature request against the fixture record."""
        values = {
            "res_model": self.record._name,
            "res_id": self.record.id,
            "meaning_id": self.meaning_approved.id,
            "signer_ids": [(6, 0, self.signer.ids)],
        }
        values.update(overrides)
        return self.env["ls.signature.request"].create(values)

    def test_reference_is_assigned(self):
        """A created request receives a sequence reference."""
        request = self._make_request()
        self.assertNotEqual(request.name, "/")
        self.assertTrue(request.name)

    def test_record_label_is_resolved(self):
        """The request captures the label of the record to be signed."""
        request = self._make_request()
        self.assertEqual(request.res_name, self.record.display_name)

    def test_request_on_unsignable_model_is_refused(self):
        """A request against a model without the mixin is refused."""
        partner = self.env["res.partner"].create({"name": "Not signable"})
        with self.assertRaises(UserError):
            self._make_request(res_model="res.partner", res_id=partner.id)

    def test_send_moves_to_pending(self):
        """Sending a draft request makes it awaiting signature."""
        request = self._make_request()
        request.action_send()
        self.assertEqual(request.state, "pending")

    def test_send_is_refused_outside_draft(self):
        """A request already sent cannot be sent again."""
        request = self._make_request()
        request.action_send()
        with self.assertRaises(UserError):
            request.action_send()

    def test_only_expected_signers_may_open_the_wizard(self):
        """A user outside the signer list cannot open the dialog."""
        request = self._make_request()
        request.action_send()
        with self.assertRaises(UserError):
            request.with_user(self.second_signer).action_open_wizard()

    def test_signing_through_a_request_closes_it(self):
        """Executing the signature marks the request signed and links it."""
        request = self._make_request()
        request.action_send()
        wizard = self.Wizard.with_user(self.signer).create(
            {
                "res_model": self.record._name,
                "res_id": self.record.id,
                "meaning_id": self.meaning_approved.id,
                "request_id": request.id,
                "login": self.signer.login,
                "password": "Fixture-Signer-Password-1",
                "consent": True,
            }
        )
        wizard.action_sign()
        self.assertEqual(request.state, "signed")
        self.assertTrue(request.log_id)
        self.assertEqual(request.log_id.request_id, request)

    def test_decline_requires_a_reason(self):
        """Declining without a justification is refused."""
        request = self._make_request()
        request.action_send()
        wizard = self.env["ls.signature.decline.wizard"].with_user(self.signer)
        with self.assertRaises(Exception):
            wizard.create({"request_id": request.id, "reason": "   "}).action_decline()

    def test_decline_records_the_reason(self):
        """A declined request keeps the justification."""
        request = self._make_request()
        request.action_send()
        self.env["ls.signature.decline.wizard"].with_user(self.signer).create(
            {"request_id": request.id, "reason": "Data incomplete"}
        ).action_decline()
        self.assertEqual(request.state, "declined")
        self.assertEqual(request.decline_reason, "Data incomplete")

    def test_cancel_is_refused_after_signing(self):
        """A signed request cannot be cancelled."""
        request = self._make_request()
        request.action_send()
        request.write({"state": "signed"})
        with self.assertRaises(UserError):
            request.action_cancel()

    def test_overdue_requests_expire(self):
        """The scheduled action expires requests past their deadline."""
        request = self._make_request(
            deadline=fields.Datetime.subtract(fields.Datetime.now(), days=1)
        )
        request.action_send()
        self.env["ls.signature.request"]._cron_expire_requests()
        self.assertEqual(request.state, "expired")

    def test_requests_without_a_deadline_do_not_expire(self):
        """A request with no deadline stays pending."""
        request = self._make_request()
        request.action_send()
        self.env["ls.signature.request"]._cron_expire_requests()
        self.assertEqual(request.state, "pending")
