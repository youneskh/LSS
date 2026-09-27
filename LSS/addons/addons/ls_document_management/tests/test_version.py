# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for document versions, their numbering and their immutability."""

import base64
import hashlib

from odoo.exceptions import UserError, ValidationError

from .common import DEMO_FILE_CONTENT, LsDocumentCommon


class TestLsDocumentVersion(LsDocumentCommon):
    """Version numbering, checksum and controlled-record behaviour."""

    def setUp(self):
        """Create a draft document used by every test."""
        super().setUp()
        self.document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )

    def test_first_version_is_numbered_one(self):
        """The first version of a document is version 1."""
        version = self._create_version(self.document)
        self.assertEqual(version.version_number, 1)

    def test_version_numbers_increment(self):
        """Each new version receives the next sequential number."""
        self._create_version(self.document)
        second = self._create_version(self.document, change_summary="Second.")
        third = self._create_version(self.document, change_summary="Third.")
        self.assertEqual(second.version_number, 2)
        self.assertEqual(third.version_number, 3)

    def test_version_numbering_is_per_document(self):
        """Numbering restarts at one for another document."""
        self._create_version(self.document)
        other = self._create_document(name="Other document")
        version = self._create_version(other)
        self.assertEqual(version.version_number, 1)

    def test_checksum_matches_content(self):
        """The stored digest is the SHA-256 of the uploaded content."""
        version = self._create_version(self.document)
        expected = hashlib.sha256(DEMO_FILE_CONTENT).hexdigest()
        self.assertEqual(version.checksum_sha256, expected)

    def test_file_size_matches_content(self):
        """The stored size is the byte length of the decoded content."""
        version = self._create_version(self.document)
        self.assertEqual(version.file_size, len(DEMO_FILE_CONTENT))

    def test_verify_integrity_passes_for_untouched_content(self):
        """Integrity verification succeeds on an unmodified version."""
        version = self._create_version(self.document)
        self.assertTrue(version.verify_integrity())

    def test_verify_integrity_detects_mismatch(self):
        """A digest that no longer matches the content is reported."""
        version = self._create_version(self.document)
        self.env.cr.execute(
            "UPDATE ls_document_version SET checksum_sha256 = %s WHERE id = %s",
            ("0" * 64, version.id),
        )
        version.invalidate_recordset()
        with self.assertRaises(UserError):
            version.verify_integrity()

    def test_content_cannot_be_modified(self):
        """The file of an existing version cannot be replaced."""
        version = self._create_version(self.document)
        with self.assertRaises(UserError):
            version.content = base64.b64encode(b"tampered content")

    def test_change_summary_cannot_be_modified(self):
        """The change summary of an existing version is frozen."""
        version = self._create_version(self.document)
        with self.assertRaises(UserError):
            version.change_summary = "Rewritten history."

    def test_version_number_cannot_be_modified(self):
        """The version number of an existing version is frozen."""
        version = self._create_version(self.document)
        with self.assertRaises(UserError):
            version.version_number = 99

    def test_system_managed_flag_can_still_be_written(self):
        """System managed flags remain writable for the workflow."""
        version = self._create_version(self.document)
        version.write({"is_superseded": True})
        self.assertTrue(version.is_superseded)

    def test_empty_content_is_rejected(self):
        """A version without file is refused."""
        with self.assertRaises(ValidationError):
            self.env["ls.document.version"].create(
                {
                    "document_id": self.document.id,
                    "filename": "empty.txt",
                    "content": False,
                    "change_summary": "No file.",
                }
            )

    def test_unlink_allowed_on_draft_document(self):
        """An unused version of a draft document can be deleted."""
        version = self._create_version(self.document)
        self.assertTrue(version.unlink())

    def test_unlink_blocked_when_document_left_draft(self):
        """A version cannot be deleted once the document left draft."""
        version = self._create_version(self.document)
        self.document.action_submit_review()
        with self.assertRaises(UserError):
            version.unlink()

    def test_unlink_blocked_for_effective_version(self):
        """The effective version cannot be deleted."""
        version = self._create_version(self.document)
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.document.action_start_revision()
        with self.assertRaises(UserError):
            version.unlink()

    def test_display_name_contains_document_and_number(self):
        """The version is displayed as document number and revision."""
        version = self._create_version(self.document)
        self.assertIn(self.document.reference, version.display_name)
        self.assertIn("v1", version.display_name)

    def test_company_is_inherited_from_document(self):
        """The version belongs to the company of its document."""
        version = self._create_version(self.document)
        self.assertEqual(version.company_id, self.document.company_id)
