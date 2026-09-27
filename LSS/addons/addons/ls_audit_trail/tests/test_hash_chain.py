# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Hash chain tests: sequencing, linkage and digest correctness."""

from odoo.tests import tagged

from ..tools import constants, serialization

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestHashChain(AuditTrailCase):
    """Verify the properties the chain is required to guarantee."""

    def test_chain_positions_are_consecutive(self):
        """Successive captures occupy successive chain positions."""
        self._activate_rule(field_ids=self.field_name.ids)
        partners = [
            self.env["res.partner"].create({"name": f"Chain {index}"})
            for index in range(4)
        ]
        entries = self.log_model.sudo().search(
            [("company_id", "=", self.company.id)], order="sequence_number asc"
        )
        positions = entries.mapped("sequence_number")
        expected = list(range(positions[0], positions[0] + len(positions)))
        self.assertEqual(positions, expected)
        self.assertEqual(len(partners), 4)

    def test_each_entry_links_to_its_predecessor(self):
        """The previous digest of an entry equals the digest of the entry before."""
        self._activate_rule(field_ids=self.field_name.ids)
        for index in range(3):
            self.env["res.partner"].create({"name": f"Linked {index}"})
        entries = self.log_model.sudo().search(
            [("company_id", "=", self.company.id)], order="sequence_number asc"
        )
        for previous, current in zip(entries, entries[1:]):
            with self.subTest(position=current.sequence_number):
                self.assertEqual(current.hash_prev, previous.hash_current)

    def test_chain_tail_of_an_unused_company_is_the_genesis(self):
        """A company that owns no entry reports the genesis chain tail.

        The head of the chain of the company running the test suite cannot be
        asserted directly, because other tests of the same database may already
        have written entries to it. A company created for this test owns an empty
        chain, so its tail is the documented genesis value.
        """
        fresh_company = self.env["res.company"].create({"name": "Empty chain co"})
        position, digest = self.log_model.sudo()._ls_chain_tail(fresh_company.id)
        self.assertEqual(position, 0)
        self.assertEqual(digest, constants.GENESIS_DIGEST)

    def test_first_entry_of_a_new_chain_uses_the_genesis_digest(self):
        """The first entry written to an empty chain links to the genesis digest."""
        fresh_company = self.env["res.company"].create({"name": "Genesis co"})
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=fresh_company.id
        )
        partner = (
            self.env["res.partner"]
            .with_company(fresh_company)
            .create({"name": "Genesis probe", "company_id": fresh_company.id})
        )
        entry = self.log_model.sudo().search(
            [("company_id", "=", fresh_company.id)], order="sequence_number asc"
        )[0]
        self.assertEqual(entry.sequence_number, 1)
        self.assertEqual(entry.hash_prev, constants.GENESIS_DIGEST)
        self.assertEqual(entry.res_id, partner.id)

    def test_digests_are_reproducible(self):
        """Recomputing the digests of an entry reproduces the stored values."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Reproducible"})
        entry = self._entries_for(partner, constants.OPERATION_CREATE)
        payload_digest = serialization.sha256_hex(
            serialization.canonical_json(entry._ls_payload())
        )
        self.assertEqual(payload_digest, entry.payload_digest)
        self.assertEqual(
            serialization.chain_digest(payload_digest, entry.hash_prev),
            entry.hash_current,
        )

    def test_digest_lengths(self):
        """Every stored digest is a full length hexadecimal SHA-256 digest."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Digest length"})
        entry = self._entries_for(partner, constants.OPERATION_CREATE)
        for value in (entry.payload_digest, entry.hash_prev, entry.hash_current):
            with self.subTest(value=value):
                self.assertEqual(len(value), constants.DIGEST_LENGTH)
                int(value, 16)

    def test_canonical_json_is_key_order_independent(self):
        """The canonical form of two equal payloads is byte identical."""
        first = serialization.canonical_json({"b": 2, "a": 1})
        second = serialization.canonical_json({"a": 1, "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(
            serialization.sha256_hex(first), serialization.sha256_hex(second)
        )

    def test_payload_covers_stored_evidence_but_not_registry_metadata(self):
        """Stored snapshots are hashed; values resolved at read time are not."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Payload scope"})
        entry = self._entries_for(partner, constants.OPERATION_CREATE)
        payload = entry._ls_payload()
        self.assertIn("res_name", payload)
        line_payload = payload["lines"][0]
        keys = ("field_name", "old_value", "new_value", "old_display", "new_display")
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, line_payload)
        for key in ("field_label", "field_type"):
            with self.subTest(key=key):
                self.assertNotIn(key, line_payload)
