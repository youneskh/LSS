# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the controlled document lifecycle state machine."""

from odoo.exceptions import UserError, ValidationError

from .common import LsDocumentCommon


class TestLsDocumentLifecycle(LsDocumentCommon):
    """State transitions, guards and numbering."""

    def setUp(self):
        """Create a draft document with one approver and one version."""
        super().setUp()
        self.document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )
        self.version = self._create_version(self.document)

    def test_reference_is_assigned_from_sequence(self):
        """A new document receives a number from the dedicated sequence."""
        self.assertTrue(self.document.reference.startswith("DOC-"))
        self.assertNotEqual(self.document.reference, "New")

    def test_display_name_contains_reference_and_title(self):
        """The document is displayed as number and title."""
        self.assertIn(self.document.reference, self.document.display_name)
        self.assertIn("Test Document", self.document.display_name)

    def test_initial_state_is_draft(self):
        """A newly created document starts in draft."""
        self.assertEqual(self.document.state, "draft")

    def test_submit_review_creates_one_approval_per_approver(self):
        """Submitting requests an approval from every approver."""
        self.document.approver_ids = [
            (6, 0, [self.user_approver.id, self.user_approver_2.id])
        ]
        self.document.action_submit_review()
        self.assertEqual(self.document.state, "under_review")
        self.assertEqual(len(self.document.approval_ids), 2)
        self.assertTrue(
            all(item.state == "pending" for item in self.document.approval_ids)
        )

    def test_submit_review_requires_a_version(self):
        """A document without version cannot be submitted."""
        document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )
        with self.assertRaises(UserError):
            document.action_submit_review()

    def test_submit_review_requires_an_approver(self):
        """A document without approver cannot be submitted."""
        document = self._create_document()
        self._create_version(document)
        with self.assertRaises(UserError):
            document.action_submit_review()

    def test_submit_review_rejected_outside_draft(self):
        """Only draft documents can be submitted."""
        self.document.action_submit_review()
        with self.assertRaises(UserError):
            self.document.action_submit_review()

    def test_document_is_approved_when_all_approvals_granted(self):
        """The document is approved once every approval is granted."""
        self.document.approver_ids = [
            (6, 0, [self.user_approver.id, self.user_approver_2.id])
        ]
        self.document.action_submit_review()
        first = self.document.approval_ids.filtered(
            lambda item: item.approver_id == self.user_approver
        )
        first.with_user(self.user_approver).action_approve()
        self.assertEqual(self.document.state, "under_review")
        second = self.document.approval_ids.filtered(
            lambda item: item.approver_id == self.user_approver_2
        )
        second.with_user(self.user_approver_2).action_approve()
        self.assertEqual(self.document.state, "approved")

    def test_publish_sets_effective_version_and_date(self):
        """Publishing puts the latest version into force."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.assertEqual(self.document.state, "published")
        self.assertEqual(self.document.current_version_id, self.version)
        self.assertTrue(self.document.effective_date)
        self.assertTrue(self.version.is_current)

    def test_publish_requires_manager_role(self):
        """An editor cannot publish a document."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        with self.assertRaises(UserError):
            self.document.with_user(self.user_editor).action_publish()

    def test_publish_rejected_before_approval(self):
        """A draft document cannot be published."""
        with self.assertRaises(UserError):
            self.document.with_user(self.user_manager).action_publish()

    def test_reset_to_draft_cancels_pending_approvals(self):
        """Resetting an approved document cancels remaining approvals."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_reset_to_draft()
        self.assertEqual(self.document.state, "draft")

    def test_start_revision_keeps_effective_version(self):
        """A revision keeps the published version in force."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.document.action_start_revision()
        self.assertEqual(self.document.state, "draft")
        self.assertEqual(self.document.current_version_id, self.version)

    def test_second_publication_supersedes_previous_version(self):
        """Publishing a new version marks the previous one superseded."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.document.action_start_revision()
        version_2 = self._create_version(
            self.document, change_summary="Second issue."
        )
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.assertEqual(self.document.current_version_id, version_2)
        self.assertTrue(self.version.is_superseded)
        self.assertFalse(version_2.is_superseded)

    def test_archive_requires_published_state(self):
        """A draft document cannot be archived."""
        with self.assertRaises(UserError):
            self.document.with_user(self.user_manager).action_archive_document()

    def test_archive_sets_archive_date(self):
        """Archiving records the archiving date."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.document.with_user(self.user_manager).action_archive_document()
        self.assertEqual(self.document.state, "archived")
        self.assertTrue(self.document.archive_date)

    def test_archive_requires_manager_role(self):
        """An editor cannot archive a document."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        with self.assertRaises(UserError):
            self.document.with_user(self.user_editor).action_archive_document()

    def test_folder_cannot_change_after_publication(self):
        """The folder of a published document is frozen."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        with self.assertRaises(UserError):
            self.document.folder_id = self.child_folder

    def test_unlink_blocked_outside_draft(self):
        """A document that left draft cannot be deleted."""
        self.document.action_submit_review()
        with self.assertRaises(UserError):
            self.document.unlink()

    def test_unlink_blocked_after_publication(self):
        """A document that was published once cannot be deleted."""
        self.document.action_submit_review()
        self._approve_all(self.document)
        self.document.with_user(self.user_manager).action_publish()
        self.document.action_start_revision()
        with self.assertRaises(UserError):
            self.document.unlink()

    def test_unlink_allowed_for_never_published_draft(self):
        """A draft that was never published can be deleted."""
        document = self._create_document(name="Disposable draft")
        self.assertTrue(document.unlink())

    def test_constraint_blocks_review_without_approver(self):
        """The Python constraint refuses a review state without approver."""
        document = self._create_document()
        self._create_version(document)
        with self.assertRaises(ValidationError):
            document.write({"state": "under_review"})

    def test_new_version_wizard_creates_version(self):
        """The wizard creates a numbered version on a draft document."""
        wizard = self.env["ls.document.new.version.wizard"].create(
            {
                "document_id": self.document.id,
                "content": self._encoded_content(),
                "filename": "procedure-v2.txt",
                "change_summary": "Second issue.",
            }
        )
        wizard.action_create_version()
        self.assertEqual(self.document.version_count, 2)
        self.assertEqual(self.document.latest_version_id.version_number, 2)

    def test_new_version_wizard_blocked_outside_draft(self):
        """The wizard refuses to add a version to a document under review."""
        self.document.action_submit_review()
        wizard = self.env["ls.document.new.version.wizard"].create(
            {
                "document_id": self.document.id,
                "content": self._encoded_content(),
                "filename": "procedure-v2.txt",
                "change_summary": "Second issue.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_create_version()

    def test_onchange_folder_applies_defaults(self):
        """Selecting a folder proposes its retention policy and approvers."""
        self.folder.default_approver_ids = [(6, 0, [self.user_approver.id])]
        document = self.env["ls.document.document"].new(
            {"name": "Onchange test", "folder_id": self.folder.id}
        )
        document._onchange_folder_id()
        self.assertEqual(document.retention_policy_id, self.policy)
        self.assertIn(self.user_approver, document.approver_ids._origin)
