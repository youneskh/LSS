# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Retention run tests: controlled removal that keeps the chain verifiable."""

from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestPurge(AuditTrailCase):
    """Verify the preconditions, the effect and the safety of a retention run."""

    def setUp(self):
        """Record an old chain in a company configured for retention."""
        super().setUp()
        self.purge_company = self.env["res.company"].create(
            {
                "name": "Purge co",
                "ls_audit_retention_days": 30,
                "ls_audit_retention_procedure": "SOP-QA-014",
                "ls_audit_allow_purge": True,
            }
        )
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=self.purge_company.id
        )
        # Record the entries 90 days in the past by freezing the clock, so
        # that they are sealed with their real event time. Ageing them with
        # SQL afterwards would change sealed content and break the chain.
        with freeze_time(fields.Datetime.now() - timedelta(days=90)):
            self.partners = self.env["res.partner"].with_company(
                self.purge_company
            ).create(
                [
                    {"name": f"Old {index}", "company_id": self.purge_company.id}
                    for index in range(5)
                ]
            )
            self.env.flush_all()
        self.env.invalidate_all()

    def _wizard(self, **overrides):
        """Create a retention wizard for the configured company."""
        values = {
            "company_id": self.purge_company.id,
            "justification": "Approved by QA under SOP-QA-014.",
        }
        values.update(overrides)
        wizard = self.env["ls.audit_trail.purge.wizard"].create(values)
        wizard.confirm_entry_count = wizard.entry_count
        return wizard

    def test_scope_counts_the_aged_entries(self):
        """The wizard reports the entries older than the retention window."""
        wizard = self._wizard()
        self.assertEqual(wizard.entry_count, 5)
        self.assertTrue(wizard.cutoff_datetime)

    def test_retention_requires_period_before_allowing(self):
        """A company cannot allow retention runs without a period."""
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {"name": "No period co", "ls_audit_allow_purge": True}
            )

    def test_retention_requires_procedure_before_allowing(self):
        """A company cannot allow retention runs without a procedure reference."""
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {
                    "name": "No procedure co",
                    "ls_audit_retention_days": 30,
                    "ls_audit_allow_purge": True,
                }
            )

    def test_disallowed_company_cannot_purge(self):
        """A run is refused when the company does not allow it."""
        self.purge_company.sudo().write({"ls_audit_allow_purge": False})
        wizard = self.env["ls.audit_trail.purge.wizard"].create(
            {
                "company_id": self.purge_company.id,
                "justification": "Attempt",
                "confirm_entry_count": 5,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_execute()

    def test_confirmation_count_must_match(self):
        """A wrong confirmation count aborts the run."""
        wizard = self._wizard()
        wizard.confirm_entry_count = wizard.entry_count + 1
        with self.assertRaises(UserError):
            wizard.action_execute()

    def test_justification_is_required(self):
        """An empty justification aborts the run."""
        wizard = self._wizard(justification="   ")
        with self.assertRaises(UserError):
            wizard.action_execute()

    @mute_logger("odoo.addons.ls_audit_trail.wizards.ls_audit_trail_purge_wizard")
    def test_run_removes_entries_and_writes_an_anchor(self):
        """A run removes the aged entries and records a retention anchor."""
        wizard = self._wizard()
        expected = wizard.entry_count
        wizard.action_execute()
        remaining_data = self.log_model.sudo().search_count(
            [
                ("company_id", "=", self.purge_company.id),
                ("entry_type", "=", constants.ENTRY_TYPE_DATA),
            ]
        )
        self.assertEqual(remaining_data, 0)
        anchor = self.log_model.sudo().search(
            [
                ("company_id", "=", self.purge_company.id),
                ("entry_type", "=", constants.ENTRY_TYPE_ANCHOR),
            ]
        )
        self.assertEqual(len(anchor), 1)
        self.assertEqual(anchor.purged_entry_count, expected)
        self.assertEqual(len(anchor.purged_aggregate_digest), constants.DIGEST_LENGTH)
        self.assertIn("SOP-QA-014", anchor.purge_reason)

    @mute_logger("odoo.addons.ls_audit_trail.wizards.ls_audit_trail_purge_wizard")
    def test_chain_still_verifies_after_a_run(self):
        """After a run the surviving chain, anchor included, still verifies."""
        self._wizard().action_execute()
        outcome = self.log_model.sudo()._ls_verify_chain(self.purge_company)
        self.assertTrue(outcome["passed"], outcome["details"])

    @mute_logger("odoo.addons.ls_audit_trail.wizards.ls_audit_trail_purge_wizard")
    def test_run_refuses_a_broken_chain(self):
        """A run aborts when the chain does not verify beforehand."""
        target = self.log_model.sudo().search(
            [("company_id", "=", self.purge_company.id)],
            order="sequence_number asc",
        )[2]
        self.env.cr.execute(
            "UPDATE ls_audit_trail_log SET user_login = %s WHERE id = %s",
            ("tampered", target.id),
        )
        self.env.invalidate_all()
        wizard = self._wizard()
        with self.assertRaises(UserError):
            wizard.action_execute()

    def test_new_entries_continue_the_chain_after_a_run(self):
        """A capture after a run links onto the anchor."""
        with mute_logger(
            "odoo.addons.ls_audit_trail.wizards.ls_audit_trail_purge_wizard"
        ):
            self._wizard().action_execute()
        partner = self.env["res.partner"].with_company(self.purge_company).create(
            {"name": "After purge", "company_id": self.purge_company.id}
        )
        entries = self.log_model.sudo().search(
            [("company_id", "=", self.purge_company.id)],
            order="sequence_number asc",
        )
        self.assertEqual(entries[-1].res_id, partner.id)
        self.assertEqual(entries[-1].hash_prev, entries[-2].hash_current)
        outcome = self.log_model.sudo()._ls_verify_chain(self.purge_company)
        self.assertTrue(outcome["passed"], outcome["details"])
