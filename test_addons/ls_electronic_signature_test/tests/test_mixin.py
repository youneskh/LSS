# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the signature capability mixin."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureMixin(SignatureCase):
    """The mixin exposes signatures and enforces transition policies."""

    def test_model_is_marked_signable(self):
        """The mixin sets the marker used by policies and requests."""
        self.assertTrue(getattr(self.Record, "_ls_signature_enabled", False))

    def test_payload_uses_the_declared_whitelist(self):
        """Only whitelisted fields enter the payload content."""
        fields_used = self.record._ls_signature_fields()
        self.assertEqual(
            set(fields_used), {"name", "state", "quantity", "description"}
        )

    def test_payload_excludes_audit_columns(self):
        """Technical audit columns never enter the payload."""
        payload = self.record._ls_signature_payload(
            meaning=self.meaning_approved,
            signed_at=self.record.create_date,
            signer=self.signer,
        )
        self.assertNotIn("write_date", payload["content"])
        self.assertNotIn("create_uid", payload["content"])

    def test_payload_binds_signer_and_meaning(self):
        """The payload names the signer and meaning so it cannot be reused."""
        payload = self.record._ls_signature_payload(
            meaning=self.meaning_approved,
            signed_at=self.record.create_date,
            signer=self.signer,
        )
        self.assertEqual(payload["meaning_code"], self.meaning_approved.code)
        self.assertEqual(payload["signer_login"], self.signer.login)
        self.assertEqual(payload["res_model"], self.record._name)
        self.assertEqual(payload["res_id"], self.record.id)

    def test_signature_count_and_last_signature(self):
        """Computed helpers reflect the signatures recorded."""
        self.assertEqual(self.record.ls_signature_count, 0)
        self._sign()
        self.record.invalidate_recordset()
        self.assertEqual(self.record.ls_signature_count, 1)
        self.assertTrue(self.record.ls_last_signature_id)

    def test_signature_is_current_until_the_record_changes(self):
        """Editing the signed content makes the signature stale."""
        self._sign()
        self.record.invalidate_recordset()
        self.assertTrue(self.record.ls_signature_current)
        self.record.write({"quantity": 999.0})
        self.record.invalidate_recordset()
        self.assertFalse(self.record.ls_signature_current)

    def test_change_outside_the_payload_does_not_stale_the_signature(self):
        """A field outside the whitelist does not invalidate a signature."""
        self._sign()
        self.record.invalidate_recordset()
        self.record.write({"company_id": self.env.company.id})
        self.record.invalidate_recordset()
        self.assertTrue(self.record.ls_signature_current)

    def test_transition_is_blocked_without_signature(self):
        """A controlled transition is refused when unsigned."""
        self.Policy.create(
            {
                "name": "Release requires approval",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "transition",
                "field_name": "state",
                "value_to": "released",
                "meaning_id": self.meaning_approved.id,
                "required_signature_count": 1,
            }
        )
        with self.assertRaises(UserError):
            self.record.write({"state": "released"})

    def test_transition_is_allowed_once_signed(self):
        """The same transition succeeds when the signature is present."""
        policy = self.Policy.create(
            {
                "name": "Release requires approval",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "transition",
                "field_name": "state",
                "value_to": "released",
                "meaning_id": self.meaning_approved.id,
                "required_signature_count": 1,
            }
        )
        self._sign(policy=policy)
        self.record.write({"state": "released"})
        self.assertEqual(self.record.state, "released")

    def test_two_signature_policy_requires_two_distinct_signers(self):
        """Two signatures by one person do not satisfy a dual policy."""
        policy = self.Policy.create(
            {
                "name": "Release requires two approvals",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "transition",
                "field_name": "state",
                "value_to": "released",
                "meaning_id": self.meaning_approved.id,
                "required_signature_count": 2,
                "distinct_signers": True,
            }
        )
        self._sign(policy=policy, user=self.signer)
        with self.assertRaises(UserError):
            self.record._ls_check_policy_satisfied(policy)
        self._sign(policy=policy, user=self.second_signer)
        self.assertTrue(self.record._ls_check_policy_satisfied(policy))

    def test_stale_signature_does_not_satisfy_a_policy(self):
        """A signature no longer covering the content stops counting."""
        policy = self.Policy.create(
            {
                "name": "Release requires approval",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "transition",
                "field_name": "state",
                "value_to": "released",
                "meaning_id": self.meaning_approved.id,
            }
        )
        self._sign(policy=policy)
        self.record.write({"quantity": 42.0})
        with self.assertRaises(UserError):
            self.record.write({"state": "released"})

    def test_uncontrolled_transition_is_not_blocked(self):
        """A transition to a value outside the policy is unaffected."""
        self.Policy.create(
            {
                "name": "Release requires approval",
                "model_id": self.env["ir.model"]._get(self.Record._name).id,
                "trigger": "transition",
                "field_name": "state",
                "value_to": "released",
                "meaning_id": self.meaning_approved.id,
            }
        )
        self.record.write({"state": "draft"})
        self.assertEqual(self.record.state, "draft")
