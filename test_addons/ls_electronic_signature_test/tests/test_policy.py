# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for signature policy configuration and its constraints."""

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignaturePolicy(SignatureCase):
    """Policies refuse configurations that could not be enforced."""

    @classmethod
    def setUpClass(cls):
        """Resolve the ir.model record of the signable fixture model."""
        super().setUpClass()
        cls.model_ref = cls.env["ir.model"]._get(cls.Record._name)

    def _base_values(self, **overrides):
        """Return a valid policy value dictionary with overrides applied."""
        values = {
            "name": "Probe policy",
            "model_id": self.model_ref.id,
            "trigger": "manual",
            "meaning_id": self.meaning_approved.id,
        }
        values.update(overrides)
        return values

    def test_policy_on_signable_model_is_accepted(self):
        """A policy on a model carrying the mixin is created."""
        policy = self.Policy.create(self._base_values())
        self.assertEqual(policy.model_name, self.Record._name)

    def test_policy_on_unsignable_model_is_refused(self):
        """A policy on a model without the mixin is refused."""
        partner_model = self.env["ir.model"]._get("res.partner")
        with self.assertRaises(ValidationError):
            self.Policy.create(self._base_values(model_id=partner_model.id))

    def test_transition_policy_requires_a_field(self):
        """A transition policy without a controlled field is refused."""
        with self.assertRaises(ValidationError):
            self.Policy.create(
                self._base_values(trigger="transition", value_to="released")
            )

    def test_transition_policy_requires_a_target_value(self):
        """A transition policy without a target value is refused."""
        with self.assertRaises(ValidationError):
            self.Policy.create(
                self._base_values(trigger="transition", field_name="state")
            )

    def test_transition_policy_requires_an_existing_field(self):
        """A transition policy naming an absent field is refused."""
        with self.assertRaises(ValidationError):
            self.Policy.create(
                self._base_values(
                    trigger="transition",
                    field_name="no_such_field",
                    value_to="released",
                )
            )

    def test_malformed_domain_is_refused(self):
        """A domain that is not valid literal syntax is refused."""
        with self.assertRaises(ValidationError):
            self.Policy.create(
                self._base_values(applicability_domain="[('state', '=',")
            )

    def test_non_list_domain_is_refused(self):
        """A domain that is not a list is refused."""
        with self.assertRaises(ValidationError):
            self.Policy.create(self._base_values(applicability_domain="{'a': 1}"))

    @mute_logger("odoo.sql_db")
    def test_signature_count_must_be_positive(self):
        """A policy requiring zero signatures is refused by the database."""
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Policy.create(self._base_values(required_signature_count=0))

    def test_domain_restricts_applicability(self):
        """A policy applies only to records matching its domain."""
        policy = self.Policy.create(
            self._base_values(applicability_domain="[('quantity', '>', 100)]")
        )
        self.assertFalse(policy.is_applicable_to(self.record))
        self.record.write({"quantity": 500.0})
        self.assertTrue(policy.is_applicable_to(self.record))

    def test_empty_domain_applies_to_every_record(self):
        """A policy with an empty domain governs all records."""
        policy = self.Policy.create(self._base_values())
        self.assertTrue(policy.is_applicable_to(self.record))

    def test_policy_lookup_filters_by_trigger(self):
        """Policy lookup respects the requested trigger."""
        self.Policy.create(self._base_values(name="Manual probe"))
        self.Policy.create(
            self._base_values(
                name="Transition probe",
                trigger="transition",
                field_name="state",
                value_to="released",
            )
        )
        manual = self.Policy._policies_for_model(self.Record._name, "manual")
        transition = self.Policy._policies_for_model(self.Record._name, "transition")
        self.assertTrue(all(p.trigger == "manual" for p in manual))
        self.assertTrue(all(p.trigger == "transition" for p in transition))
