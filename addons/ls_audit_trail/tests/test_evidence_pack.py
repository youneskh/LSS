# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Evidence pack tests: generation, sealing and self-verification."""

import base64
import io
import json
import zipfile

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestEvidencePack(AuditTrailCase):
    """Verify that a pack is a faithful, sealed, self-describing export."""

    def setUp(self):
        """Record a short chain to export."""
        super().setUp()
        self.pack_company = self.env["res.company"].create({"name": "Pack co"})
        self._activate_rule(
            field_ids=(self.field_name + self.field_email).ids,
            company_id=self.pack_company.id,
        )
        self.partners = self.env["res.partner"].with_company(
            self.pack_company
        ).create(
            [
                {
                    "name": f"Pack {index}",
                    "email": f"pack{index}@example.org",
                    "company_id": self.pack_company.id,
                }
                for index in range(3)
            ]
        )

    def _new_pack(self, **overrides):
        """Create a draft evidence pack over the recorded chain."""
        values = {
            "purpose": "Test export",
            "company_id": self.pack_company.id,
            "date_from": "2026-01-01 00:00:00",
            "date_to": "2099-12-31 23:59:59",
        }
        values.update(overrides)
        return self.env["ls.audit_trail.evidence_pack"].create(values)

    def test_reference_is_assigned(self):
        """A pack receives a sequence based reference on creation."""
        pack = self._new_pack()
        self.assertTrue(pack.name)
        self.assertNotEqual(pack.name, "New")

    def test_generation_populates_the_record(self):
        """Generating a pack fills the result fields and seals it."""
        pack = self._new_pack()
        pack.action_generate()
        self.assertEqual(pack.state, "generated")
        self.assertTrue(pack.entry_count >= 3)
        self.assertTrue(pack.attachment_id)
        self.assertEqual(len(pack.pack_digest), constants.DIGEST_LENGTH)
        self.assertTrue(pack.verification_id)
        self.assertEqual(pack.verification_result, "passed")

    def test_generated_pack_is_immutable(self):
        """A generated pack refuses further edits to its selection."""
        pack = self._new_pack()
        pack.action_generate()
        with self.assertRaises(AccessError):
            pack.write({"purpose": "changed"})

    def test_generated_pack_can_still_be_archived(self):
        """Archiving remains available after generation."""
        pack = self._new_pack()
        pack.action_generate()
        pack.write({"active": False})
        self.assertFalse(pack.active)

    def test_pack_cannot_be_deleted(self):
        """A pack cannot be removed through the ORM."""
        pack = self._new_pack()
        with self.assertRaises(AccessError):
            pack.unlink()

    def test_empty_selection_is_rejected(self):
        """Generating a pack that matches no entry raises."""
        pack = self._new_pack(
            date_from="1990-01-01 00:00:00", date_to="1990-01-02 00:00:00"
        )
        with self.assertRaises(UserError):
            pack.action_generate()

    def test_archive_contains_the_three_files(self):
        """The archive holds the JSON, the CSV and the manifest."""
        pack = self._new_pack()
        pack.action_generate()
        raw = base64.b64decode(pack.attachment_id.datas)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = set(archive.namelist())
        self.assertEqual(
            names,
            {
                constants.EVIDENCE_FILE_ENTRIES_JSON,
                constants.EVIDENCE_FILE_ENTRIES_CSV,
                constants.EVIDENCE_FILE_MANIFEST,
            },
        )

    def test_manifest_digests_match_the_files(self):
        """The digests recorded in the manifest match the archived files."""
        pack = self._new_pack()
        pack.action_generate()
        raw = base64.b64decode(pack.attachment_id.datas)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            manifest = json.loads(archive.read(constants.EVIDENCE_FILE_MANIFEST))
            json_bytes = archive.read(constants.EVIDENCE_FILE_ENTRIES_JSON)
            csv_bytes = archive.read(constants.EVIDENCE_FILE_ENTRIES_CSV)
        from ..tools import serialization
        self.assertEqual(
            manifest["files"][constants.EVIDENCE_FILE_ENTRIES_JSON]["sha256"],
            serialization.sha256_hex(json_bytes.decode("utf-8")),
        )
        self.assertEqual(
            manifest["files"][constants.EVIDENCE_FILE_ENTRIES_CSV]["sha256"],
            serialization.sha256_hex(csv_bytes.decode("utf-8")),
        )

    def test_manifest_records_the_verification(self):
        """The manifest embeds the outcome of the integrity verification."""
        pack = self._new_pack()
        pack.action_generate()
        raw = base64.b64decode(pack.attachment_id.datas)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            manifest = json.loads(archive.read(constants.EVIDENCE_FILE_MANIFEST))
        self.assertEqual(manifest["integrity_verification"]["result"], "passed")

    def test_archive_digest_self_check_passes(self):
        """The stored archive matches its recorded digest."""
        pack = self._new_pack()
        pack.action_generate()
        self.assertTrue(pack.action_verify_archive())

    def test_archive_digest_self_check_detects_tampering(self):
        """A tampered stored archive is detected by the self check."""
        pack = self._new_pack()
        pack.action_generate()
        # The archive may live in the filestore: detach it from its file and
        # store tampered content in the database column instead, so that the
        # attachment now returns different bytes.
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ir_attachment SET store_fname = NULL, db_datas = %s "
            "WHERE id = %s",
            (b"tampered archive", pack.attachment_id.id),
        )
        self.env.invalidate_all()
        with self.assertRaises(UserError):
            pack.action_verify_archive()

    def test_download_requires_generation(self):
        """A draft pack cannot be downloaded."""
        pack = self._new_pack()
        with self.assertRaises(UserError):
            pack.action_download()

    def test_inverted_range_is_rejected(self):
        """A pack whose start is after its end is rejected."""
        with self.assertRaises(ValidationError):
            self._new_pack(
                date_from="2099-01-01 00:00:00", date_to="2000-01-01 00:00:00"
            )

    def test_model_filter_restricts_the_export(self):
        """A model filter that matches nothing yields no entry."""
        pack = self._new_pack(model_names="account.move")
        with self.assertRaises(UserError):
            pack.action_generate()
