# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Regression tests for the findings of the 2026-09-25 audit.

F-09 the audit rule applied to a record is the rule of the company owning
the record, F-38 one rule per model and company including rules without
company, F-10 the chain tail read after the chain lock includes the entries
committed by other transactions.
"""

import psycopg2

from odoo.tests import tagged
from odoo.tools import mute_logger

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestAuditFixes(AuditTrailCase):
    """Behaviour restored by the 2026-09-25 remediation."""

    @classmethod
    def setUpClass(cls):
        """Add a second company available to the test user."""
        super().setUpClass()
        cls.company_b = cls.env["res.company"].create({"name": "Audit fix B"})
        cls.env.user.write({"company_ids": [(4, cls.company_b.id)]})

    def _env_with(self, current):
        """Return an environment with both companies, ``current`` first."""
        other = self.company_b if current == self.company else self.company
        return self.env(
            context=dict(self.env.context, allowed_company_ids=[current.id, other.id])
        )

    def test_rule_of_the_record_company_applies(self):
        """A change to a company B record is audited when A is active."""
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=self.company_b.id
        )
        partner = self.env["res.partner"].create(
            {"name": "Owned by B", "company_id": self.company_b.id}
        )
        partner.with_env(self._env_with(self.company)).write({"name": "Renamed"})
        entries = self._entries_for(partner, constants.OPERATION_WRITE)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.company_id, self.company_b)

    def test_rule_of_another_company_does_not_apply(self):
        """A rule of company B does not audit company A records."""
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=self.company_b.id
        )
        partner = self.env["res.partner"].create(
            {"name": "Owned by A", "company_id": self.company.id}
        )
        partner.with_env(self._env_with(self.company_b)).write({"name": "Renamed"})
        self.assertFalse(self._entries_for(partner))

    def test_mixed_recordset_is_split_by_company(self):
        """A write on records of two companies audits each under its rule."""
        self._activate_rule(field_ids=self.field_name.ids)
        partners = self.env["res.partner"].create(
            [
                {"name": "A", "company_id": self.company.id},
                {"name": "B", "company_id": self.company_b.id},
            ]
        )
        partners.write({"name": "Renamed"})
        for partner in partners:
            entry = self._entries_for(partner, constants.OPERATION_WRITE)
            self.assertEqual(entry.company_id, partner.company_id)

    @mute_logger("odoo.sql_db")
    def test_second_rule_without_company_is_refused(self):
        """Two rules without company on one model are refused."""
        self._activate_rule()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._activate_rule(name="Second global rule")

    def test_chain_tail_is_read_after_the_lock(self):
        """The chain tail includes the entries sealed in this transaction."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Chain"})
        partner.write({"name": "Chain 2"})
        self.env.flush_all()
        entries = self._entries_for(partner)
        position, digest = self.log_model.sudo()._ls_chain_tail(self.company.id)
        self.assertEqual(position, max(entries.mapped("sequence_number")))
        self.assertEqual(
            digest,
            entries.filtered(lambda entry: entry.sequence_number == position).hash_current,
        )
