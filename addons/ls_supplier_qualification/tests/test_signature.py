# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the append-only signature log and its hash chain."""
import json

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestSignature(SupplierQualificationCommon):
    """Cover immutability, chaining and verification of the signature log."""

    def setUp(self):
        """Create one signature entry for each test."""
        super().setUp()
        self.signature = self.env["ls.supplier.signature"].sign(
            record=self.qualification,
            meaning="authored",
            reason="Reason recorded by the test suite.",
        )

    def test_entry_fields_populated(self):
        """A signature entry records who, when, what and why."""
        self.assertEqual(self.signature.user_id, self.env.user)
        self.assertEqual(self.signature.res_model, "ls.supplier.qualification")
        self.assertEqual(self.signature.res_id, self.qualification.id)
        self.assertEqual(self.signature.meaning, "authored")
        self.assertTrue(self.signature.signed_on)
        self.assertEqual(len(self.signature.record_hash), 64)

    def test_entry_cannot_be_modified(self):
        """Writing on a signature entry is refused."""
        with self.assertRaises(UserError):
            self.signature.reason = "Tampered."

    def test_entry_cannot_be_deleted(self):
        """Deleting a signature entry is refused."""
        with self.assertRaises(UserError):
            self.signature.unlink()

    def test_chain_increments_and_links(self):
        """Each new entry increments the sequence and links the previous hash."""
        second = self.env["ls.supplier.signature"].sign(
            record=self.qualification,
            meaning="reviewed",
            reason="Second reason recorded by the test suite.",
        )
        self.assertEqual(
            second.sequence_number, self.signature.sequence_number + 1
        )
        self.assertEqual(second.previous_hash, self.signature.record_hash)

    def test_chain_verification_passes(self):
        """A consistent chain reports no broken entry."""
        self.env["ls.supplier.signature"].sign(
            record=self.qualification,
            meaning="reviewed",
            reason="Second reason recorded by the test suite.",
        )
        broken = self.env["ls.supplier.signature"].verify_chain(self.company)
        self.assertFalse(broken)

    def test_chain_verification_detects_tampering(self):
        """A direct database modification is detected by the verification."""
        self.env.cr.execute(
            "UPDATE ls_supplier_signature SET reason = %s WHERE id = %s",
            ("Tampered directly in the database.", self.signature.id),
        )
        self.signature.invalidate_recordset()
        broken = self.env["ls.supplier.signature"].verify_chain(self.company)
        self.assertIn(self.signature, broken)

    def test_payload_is_json(self):
        """The frozen payload is stored as JSON."""
        signature = self.env["ls.supplier.signature"].sign(
            record=self.qualification,
            meaning="approved",
            payload={"state": "approved", "score": 91.0},
        )
        payload = json.loads(signature.payload)
        self.assertEqual(payload["state"], "approved")
        self.assertEqual(payload["score"], 91.0)

    def test_qualification_back_reference(self):
        """An entry signed on a child record points back to the dossier."""
        assessment = self._create_assessment(self.qualification)
        entry = self.env["ls.supplier.signature"].search(
            [("res_model", "=", "ls.supplier.assessment"),
             ("res_id", "=", assessment.id)],
            limit=1,
        )
        self.assertEqual(entry.qualification_id, self.qualification)

    def test_verification_action_returns_notification(self):
        """The verification button returns a client notification action."""
        action = self.env["ls.supplier.signature"].action_verify_chain()
        self.assertEqual(action["tag"], "display_notification")
