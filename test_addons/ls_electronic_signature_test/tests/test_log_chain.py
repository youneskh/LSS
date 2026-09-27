# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for the signature hash chain required by 21 CFR 11.70."""

from odoo.tests import tagged

from .common import SignatureCase


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureChain(SignatureCase):
    """Signatures form a verifiable, gapless, tamper evident chain."""

    def test_first_signature_starts_from_genesis(self):
        """The first entry of a company chain follows the genesis value."""
        existing = self.Log.search_count([("company_id", "=", self.env.company.id)])
        self._sign()
        signature = self._signatures_of()[-1]
        self.assertEqual(signature.chain_sequence, existing + 1)
        self.assertEqual(len(signature.previous_hash), 64)

    def test_sequence_increments_without_gaps(self):
        """Consecutive signatures receive consecutive sequence numbers."""
        self._sign(meaning=self.meaning_reviewed)
        self._sign(meaning=self.meaning_approved)
        signatures = self._signatures_of()
        sequences = signatures.mapped("chain_sequence")
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(sequences[-1] - sequences[0], len(sequences) - 1)

    def test_each_entry_links_to_its_predecessor(self):
        """The previous hash of an entry equals the chain hash before it."""
        self._sign(meaning=self.meaning_reviewed)
        self._sign(meaning=self.meaning_approved)
        signatures = self.Log.search(
            [("company_id", "=", self.env.company.id)], order="chain_sequence asc"
        )
        for earlier, later in zip(signatures, signatures[1:]):
            self.assertEqual(later.previous_hash, earlier.chain_hash)

    def test_record_hash_matches_the_stored_payload(self):
        """The digest recomputes from the payload kept with the signature."""
        self._sign()
        signature = self._signatures_of()[-1]
        outcome = signature.verify()[signature.id]
        self.assertTrue(outcome["payload_ok"], outcome["messages"])
        self.assertTrue(outcome["chain_ok"], outcome["messages"])

    def test_chain_verifies_end_to_end(self):
        """Walking the whole company chain reports no divergence."""
        self._sign(meaning=self.meaning_reviewed)
        self._sign(meaning=self.meaning_approved)
        outcome = self.Log.verify_chain(self.env.company)
        self.assertTrue(outcome["passed"], outcome["messages"])
        self.assertFalse(outcome["first_divergence_id"])

    def test_tampered_payload_is_detected(self):
        """Altering a payload directly in SQL breaks verification."""
        self._sign()
        signature = self._signatures_of()[-1]
        self.env.cr.execute(
            "ALTER TABLE ls_signature_log DISABLE TRIGGER USER"
        )
        self.env.cr.execute(
            "UPDATE ls_signature_log SET payload_json = %s WHERE id = %s",
            ('{"tampered":true}', signature.id),
        )
        self.env.cr.execute("ALTER TABLE ls_signature_log ENABLE TRIGGER USER")
        signature.invalidate_recordset(["payload_json"])
        outcome = signature.verify()[signature.id]
        self.assertFalse(outcome["payload_ok"])

    def test_deleted_entry_is_detected_as_a_gap(self):
        """Removing an entry in SQL makes the chain report a divergence."""
        self._sign(meaning=self.meaning_reviewed)
        self._sign(meaning=self.meaning_approved)
        signatures = self.Log.search(
            [("company_id", "=", self.env.company.id)], order="chain_sequence desc"
        )
        victim = signatures[1] if len(signatures) > 1 else signatures[0]
        self.env.cr.execute(
            "ALTER TABLE ls_signature_log DISABLE TRIGGER USER"
        )
        # The attempt log references the signature; detach it first so that
        # only the signature row itself disappears.
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_signature_attempt SET log_id = NULL WHERE log_id = %s",
            (victim.id,),
        )
        self.env.cr.execute(
            "DELETE FROM ls_signature_log WHERE id = %s", (victim.id,)
        )
        self.env.cr.execute("ALTER TABLE ls_signature_log ENABLE TRIGGER USER")
        self.Log.invalidate_model()
        outcome = self.Log.verify_chain(self.env.company)
        self.assertFalse(outcome["passed"])
        self.assertTrue(outcome["messages"])

    def test_manifestation_fields_are_snapshots(self):
        """Renaming the signer does not rewrite a past signature."""
        self._sign()
        signature = self._signatures_of()[-1]
        original_name = signature.signer_name
        self.signer.sudo().write({"name": "Renamed After Signing"})
        signature.invalidate_recordset()
        self.assertEqual(signature.signer_name, original_name)
        self.assertNotEqual(signature.signer_name, self.signer.name)

    def test_manifestation_carries_the_three_required_items(self):
        """Printed name, date and time, and meaning are all recorded."""
        self._sign()
        signature = self._signatures_of()[-1]
        self.assertTrue(signature.signer_name)
        self.assertTrue(signature.signed_at)
        self.assertTrue(signature.meaning_name)

    def test_is_current_reacts_to_an_edit_in_the_same_transaction(self):
        """A signature goes stale as soon as the signed content changes."""
        self._sign()
        signature = self._signatures_of()[-1]
        self.assertTrue(signature.is_current)
        self.record.write({"quantity": 12345.0})
        signature.invalidate_recordset(["is_current"])
        self.assertFalse(signature.is_current)
