# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Security tests: access rights, record rules and segregation of duties."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestAccessRights(AuditTrailCase):
    """Verify that each role can do exactly what it is meant to do."""

    def setUp(self):
        """Record one entry that the roles will try to reach."""
        super().setUp()
        self._activate_rule(field_ids=self.field_name.ids)
        self.partner = self.env["res.partner"].create({"name": "Access probe"})
        self.entry = self._entries_for(self.partner, constants.OPERATION_CREATE)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_user_without_group_cannot_read_entries(self):
        """A plain internal user has no access to the audit trail."""
        with self.assertRaises(AccessError):
            self.log_model.with_user(self.user_plain).search([])

    def test_viewer_can_read_entries(self):
        """The viewer role can read entries and their field changes."""
        entries = self.log_model.with_user(self.user_viewer).search([])
        self.assertTrue(entries)
        self.assertTrue(
            self.line_model.with_user(self.user_viewer).search_count([]) >= 0
        )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_configure_rules(self):
        """The viewer role can read rules but cannot change them."""
        self.rule_model.with_user(self.user_viewer).search([])
        with self.assertRaises(AccessError):
            self.rule_model.with_user(self.user_viewer).create(
                {
                    "name": "Escalation attempt",
                    "model_id": self.env["ir.model"]._get("res.users").id,
                }
            )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_evidence_packs(self):
        """Producing evidence is an auditor right, not a viewer right."""
        with self.assertRaises(AccessError):
            self.env["ls.audit_trail.evidence_pack"].with_user(
                self.user_viewer
            ).create(
                {
                    "purpose": "Attempt",
                    "date_from": "2026-01-01 00:00:00",
                    "date_to": "2026-12-31 23:59:59",
                }
            )

    def test_auditor_can_create_evidence_packs(self):
        """The auditor role can define evidence packs."""
        pack = self.env["ls.audit_trail.evidence_pack"].with_user(
            self.user_auditor
        ).create(
            {
                "purpose": "Scheduled review",
                "date_from": "2026-01-01 00:00:00",
                "date_to": "2026-12-31 23:59:59",
            }
        )
        self.assertEqual(pack.state, "draft")

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_auditor_cannot_configure_rules(self):
        """Segregation of duties: an auditor cannot change what is audited."""
        with self.assertRaises(AccessError):
            self.rule_model.with_user(self.user_auditor).create(
                {
                    "name": "Auditor attempt",
                    "model_id": self.env["ir.model"]._get("res.users").id,
                }
            )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_auditor_cannot_open_the_retention_wizard(self):
        """Retention runs are reserved to the administrator role."""
        with self.assertRaises(AccessError):
            self.env["ls.audit_trail.purge.wizard"].with_user(
                self.user_auditor
            ).create({"justification": "Attempt"})

    def test_administrator_can_configure_rules(self):
        """The administrator role can change what is audited."""
        rule = self.rule_model.with_user(self.user_admin).create(
            {
                "name": "Administrator rule",
                "model_id": self.env["ir.model"]._get("res.users").id,
                "note": "Justified by the access control procedure.",
            }
        )
        self.assertTrue(rule.active)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_no_role_can_write_entries(self):
        """No group is granted write or delete access on the trail."""
        for user in (self.user_viewer, self.user_auditor, self.user_admin):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    self.entry.with_user(user).write({"res_name": "tampered"})
                with self.assertRaises(AccessError):
                    self.entry.with_user(user).unlink()

    def test_acl_grants_no_write_or_unlink_on_the_trail(self):
        """The access control list itself grants nothing beyond read."""
        access = self.env["ir.model.access"].sudo().search(
            [
                (
                    "model_id.model",
                    "in",
                    ("ls.audit_trail.log", "ls.audit_trail.log.line"),
                )
            ]
        )
        self.assertTrue(access)
        for entry in access:
            with self.subTest(access=entry.name):
                self.assertFalse(entry.perm_write)
                self.assertFalse(entry.perm_create)
                self.assertFalse(entry.perm_unlink)

    def test_multi_company_record_rules_are_installed(self):
        """A record rule scopes each audited model to the user's companies.

        The rule is asserted through its presence and its domain rather than
        through the computed flag marking a rule as global, because the Python
        name of that flag on ir.rule could not be verified for Odoo 19 from
        official documentation. The behavioural consequence is asserted by
        test_entries_of_another_company_are_not_visible.
        """
        rules = self.env["ir.rule"].sudo().search(
            [("model_id.model", "=", "ls.audit_trail.log")]
        )
        self.assertTrue(rules)
        self.assertTrue(
            any("company_ids" in (rule.domain_force or "") for rule in rules)
        )

    def test_entries_of_another_company_are_not_visible(self):
        """A user sees only the chains of the companies they belong to."""
        other_company = self.env["res.company"].create({"name": "Other co"})
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=other_company.id
        )
        self.env["res.partner"].with_company(other_company).create(
            {"name": "Foreign", "company_id": other_company.id}
        )
        visible = self.log_model.with_user(self.user_viewer).search(
            [("company_id", "=", other_company.id)]
        )
        self.assertFalse(visible)
