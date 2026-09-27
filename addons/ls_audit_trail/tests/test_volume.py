# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Volume tests: the chain stays consistent under batched and repeated writes.

These are correctness-under-load tests, not performance benchmarks. They assert
that sequencing and linkage survive many operations in one transaction. No
timing threshold is asserted, because a meaningful throughput figure can only be
measured on the deploying organisation's own hardware and Odoo runtime.
"""

from odoo.tests import tagged

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestVolume(AuditTrailCase):
    """Verify chain consistency across larger batches."""

    def setUp(self):
        """Record in a company of its own to isolate the chain under test."""
        super().setUp()
        self.volume_company = self.env["res.company"].create({"name": "Volume co"})
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=self.volume_company.id
        )

    def _positions(self):
        """Return the ordered chain positions of the isolated company."""
        entries = self.log_model.sudo().search(
            [("company_id", "=", self.volume_company.id)],
            order="sequence_number asc",
        )
        return entries.mapped("sequence_number")

    def test_large_batch_create_is_consecutive(self):
        """A batch of 200 creations produces 200 consecutive positions."""
        self.env["res.partner"].with_company(self.volume_company).create(
            [
                {"name": f"Vol {index}", "company_id": self.volume_company.id}
                for index in range(200)
            ]
        )
        positions = self._positions()
        self.assertEqual(len(positions), 200)
        self.assertEqual(positions, list(range(1, 201)))

    def test_batch_write_produces_one_entry_per_changed_record(self):
        """Writing one value across a recordset audits each changed record once."""
        partners = self.env["res.partner"].with_company(self.volume_company).create(
            [
                {"name": f"Batch write {index}", "company_id": self.volume_company.id}
                for index in range(50)
            ]
        )
        base = len(self._positions())
        partners.write({"name": "Uniform name"})
        writes = self.log_model.sudo().search_count(
            [
                ("company_id", "=", self.volume_company.id),
                ("operation", "=", constants.OPERATION_WRITE),
            ]
        )
        # The first record keeps its distinct old value, the others already
        # differed from "Uniform name" as well, so every one of the 50 records
        # changes and is audited exactly once.
        self.assertEqual(writes, 50)
        self.assertEqual(len(self._positions()), base + 50)

    def test_mixed_operations_stay_linked(self):
        """A mix of creations, writes and deletions keeps the chain linked."""
        partners = self.env["res.partner"].with_company(self.volume_company).create(
            [
                {"name": f"Mixed {index}", "company_id": self.volume_company.id}
                for index in range(20)
            ]
        )
        partners[:10].write({"name": "Rewritten"})
        partners[10:].unlink()
        entries = self.log_model.sudo().search(
            [("company_id", "=", self.volume_company.id)],
            order="sequence_number asc",
        )
        for previous, current in zip(entries, entries[1:]):
            with self.subTest(position=current.sequence_number):
                self.assertEqual(current.hash_prev, previous.hash_current)
        outcome = self.log_model.sudo()._ls_verify_chain(self.volume_company)
        self.assertTrue(outcome["passed"], outcome["details"])

    def test_verification_scales_to_the_whole_chain(self):
        """A full verification of a few hundred entries passes."""
        self.env["res.partner"].with_company(self.volume_company).create(
            [
                {"name": f"Scale {index}", "company_id": self.volume_company.id}
                for index in range(300)
            ]
        )
        outcome = self.log_model.sudo()._ls_verify_chain(self.volume_company)
        self.assertTrue(outcome["passed"])
        self.assertEqual(outcome["checked"], 300)
