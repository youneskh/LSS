# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Constraint tests for ``ls.audit_trail.rule``."""

import psycopg2

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestRuleConstraints(AuditTrailCase):
    """Verify that a rule cannot be configured into an unsafe state."""

    def test_reject_own_models(self):
        """A rule cannot target a model of the audit engine itself."""
        engine_model = self.env["ir.model"]._get("ls.audit_trail.log")
        with self.assertRaises(ValidationError):
            self.rule_model.create(
                {"name": "Recursive", "model_id": engine_model.id}
            )

    def test_reject_transient_models(self):
        """A rule cannot target a transient model."""
        wizard_model = self.env["ir.model"]._get("base.language.install")
        with self.assertRaises(ValidationError):
            self.rule_model.create(
                {"name": "Transient", "model_id": wizard_model.id}
            )

    def test_reject_abstract_models(self):
        """A rule cannot target an abstract model."""
        abstract_model = self.env["ir.model"]._get("mail.thread")
        with self.assertRaises(ValidationError):
            self.rule_model.create(
                {"name": "Abstract", "model_id": abstract_model.id}
            )

    def test_reject_foreign_fields(self):
        """A rule cannot select a field of another model."""
        foreign_field = self.env["ir.model.fields"]._get("res.users", "login")
        with self.assertRaises(ValidationError):
            self.rule_model.create(
                {
                    "name": "Foreign field",
                    "model_id": self.partner_model.id,
                    "field_ids": [(6, 0, foreign_field.ids)],
                }
            )

    def test_reject_no_operation(self):
        """A rule must audit at least one operation."""
        with self.assertRaises(ValidationError):
            self.rule_model.create(
                {
                    "name": "No operation",
                    "model_id": self.partner_model.id,
                    "log_create": False,
                    "log_write": False,
                    "log_unlink": False,
                }
            )

    @mute_logger("odoo.sql_db")
    def test_reject_duplicate_rule(self):
        """Only one rule may target a model for a given company."""
        self._activate_rule()
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.rule_model.create(
                    {"name": "Duplicate", "model_id": self.partner_model.id}
                )

    def test_changing_model_clears_field_selection(self):
        """The onchange clears the field lists when the model changes."""
        rule = self.rule_model.new(
            {
                "name": "Onchange",
                "model_id": self.partner_model.id,
                "field_ids": [(6, 0, self.field_name.ids)],
            }
        )
        rule.model_id = self.env["ir.model"]._get("res.users")
        rule._onchange_model_id()
        self.assertFalse(rule.field_ids)
        self.assertFalse(rule.excluded_field_ids)

    def test_rule_change_invalidates_configuration_cache(self):
        """Deactivating a rule stops capture immediately."""
        rule = self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Cache probe"})
        self.assertTrue(self._entries_for(partner))
        rule.active = False
        other = self.env["res.partner"].create({"name": "After deactivation"})
        self.assertFalse(self._entries_for(other))
