# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Lifecycle, versioning and periodic review of controlled documents."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError

from .common import LsQmsCommon


class TestDocumentLifecycle(LsQmsCommon):
    """State machine, revision chain and review programme."""

    def test_01_reference_allocated_from_sequence(self):
        """A new procedure receives a reference from the SOP sequence."""
        sop = self._create_sop()
        self.assertTrue(sop.reference.startswith("SOP-"))
        self.assertNotEqual(sop.reference, "/")
        self.assertEqual(sop.version, 1)
        self.assertEqual(sop.state, "draft")

    def test_02_display_name_contains_reference_and_version(self):
        """The display name follows the pattern [REFERENCE] Title (vN)."""
        sop = self._create_sop(name="Cleaning")
        self.assertEqual(
            sop.display_name, "[%s] Cleaning (v1)" % sop.reference
        )

    def test_03_nominal_lifecycle(self):
        """Draft, under review, approved and published follow each other."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        self.assertEqual(sop.state, "under_review")
        self.assertTrue(sop.date_submitted)
        sop.with_user(self.user_approver).action_approve()
        self.assertEqual(sop.state, "approved")
        self.assertEqual(sop.approver_id, self.user_approver)
        self.assertTrue(sop.date_approved)
        sop.with_user(self.user_approver).action_publish()
        self.assertEqual(sop.state, "published")
        self.assertEqual(sop.date_effective, self.today)

    def test_04_forbidden_transition_is_rejected(self):
        """A draft document cannot be approved directly."""
        sop = self._create_sop()
        with self.assertRaises(UserError):
            sop.with_user(self.user_approver).action_approve()

    def test_05_segregation_of_duties(self):
        """The author cannot approve their own document."""
        sop = self._create_sop(author_id=self.user_approver.id)
        sop.with_user(self.user_approver).action_submit_for_review()
        with self.assertRaises(UserError):
            sop.with_user(self.user_approver).action_approve()

    def test_06_segregation_can_be_disabled(self):
        """Disabling the parameter allows the author to approve."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_qms.enforce_segregation_of_duties", "False"
        )
        sop = self._create_sop(author_id=self.user_approver.id)
        sop.with_user(self.user_approver).action_submit_for_review()
        sop.with_user(self.user_approver).action_approve()
        self.assertEqual(sop.state, "approved")

    def test_07_published_content_is_frozen(self):
        """The body of a published revision cannot be modified."""
        sop = self._publish(self._create_sop())
        with self.assertRaises(UserError):
            sop.write({"procedure": "<p>Modified body.</p>"})

    def test_08_published_document_cannot_be_deleted(self):
        """Only draft revisions may be deleted."""
        sop = self._publish(self._create_sop())
        with self.assertRaises(UserError):
            sop.unlink()

    def test_09_draft_document_can_be_deleted(self):
        """A draft revision is deletable."""
        sop = self._create_sop()
        self.assertTrue(sop.unlink())

    def test_10_new_revision_supersedes_the_previous_one(self):
        """Publishing a revision sets the previous one to obsolete."""
        sop = self._publish(self._create_sop())
        revision = sop.with_user(self.user_author).create_new_revision(
            "Correction of step two."
        )
        self.assertEqual(sop.state, "under_revision")
        self.assertEqual(revision.version, 2)
        self.assertEqual(revision.reference, sop.reference)
        self.assertEqual(revision.previous_revision_id, sop)
        self.assertEqual(revision.state, "draft")
        self._publish(revision)
        self.assertEqual(sop.state, "obsolete")
        self.assertEqual(sop.date_obsolete, self.today)

    def test_11_revision_requires_a_reason(self):
        """An empty reason for change is refused."""
        sop = self._publish(self._create_sop())
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).create_new_revision("   ")

    def test_12_single_published_revision(self):
        """Two published revisions of one document are refused."""
        sop = self._publish(self._create_sop())
        duplicate = self._create_sop(name="Duplicate")
        # Same reference, next version: the unique (reference, version)
        # constraint is respected, so only the single-publication rule is
        # exercised.
        duplicate.write({"reference": sop.reference, "version": sop.version + 1})
        with self.assertRaises(ValidationError):
            duplicate.write({"state": "published"})

    def test_13_next_review_date_is_computed(self):
        """The next review date is the effective date plus the period."""
        sop = self._create_sop(review_period_months=12)
        self._publish(sop)
        self.assertEqual(
            sop.date_next_review, sop.date_effective + relativedelta(months=12)
        )

    def test_14_zero_review_period_disables_the_review(self):
        """A review period of zero produces no review date."""
        sop = self._create_sop(review_period_months=0)
        self._publish(sop)
        self.assertFalse(sop.date_next_review)
        self.assertEqual(sop.review_state, "not_applicable")

    def test_15_negative_review_period_is_refused(self):
        """A negative review period raises a validation error."""
        with self.assertRaises(ValidationError):
            self._create_sop(review_period_months=-1)

    def test_16_review_state_reflects_the_due_date(self):
        """Up to date, due soon and overdue are computed from the date."""
        sop = self._publish(self._create_sop())
        self.assertEqual(sop.review_state, "ok")
        sop.write({"date_next_review": self.today + relativedelta(days=5)})
        self.assertEqual(sop.review_state, "due_soon")
        sop.write({"date_next_review": self.today - relativedelta(days=1)})
        self.assertEqual(sop.review_state, "overdue")

    def test_17_effective_date_cannot_precede_approval(self):
        """A document cannot be effective before it was approved."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        sop.with_user(self.user_approver).action_approve()
        with self.assertRaises(ValidationError):
            sop.write({"date_effective": self.today - relativedelta(days=10)})

    def test_18_obsolete_requires_the_manager_role(self):
        """Only a QMS manager withdraws a document."""
        sop = self._publish(self._create_sop())
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_set_obsolete()
        sop.with_user(self.user_manager).action_set_obsolete()
        self.assertEqual(sop.state, "obsolete")

    def test_19_reset_to_draft_requires_the_manager_role(self):
        """Only a QMS manager reopens a document under review."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        with self.assertRaises(UserError):
            sop.with_user(self.user_author).action_reset_to_draft()
        sop.with_user(self.user_manager).action_reset_to_draft()
        self.assertEqual(sop.state, "draft")
        self.assertFalse(sop.approver_id)

    def test_20_reject_returns_the_document_to_its_author(self):
        """Rejection sets the document back to draft and logs the reason."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        sop.with_user(self.user_approver).ls_qms_reject("Step two is unclear.")
        self.assertEqual(sop.state, "draft")
        bodies = sop.message_ids.mapped("body")
        self.assertTrue(any("Step two is unclear." in body for body in bodies))

    def test_21_reject_requires_a_reason(self):
        """An empty rejection reason is refused."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        with self.assertRaises(UserError):
            sop.with_user(self.user_approver).ls_qms_reject("")

    def test_22_attachment_count(self):
        """The attachment counter reflects the linked attachments."""
        sop = self._create_sop()
        self.assertEqual(sop.attachment_count, 0)
        self.env["ir.attachment"].create(
            {
                "name": "evidence.txt",
                "res_model": sop._name,
                "res_id": sop.id,
                "raw": b"content",
            }
        )
        sop.invalidate_recordset(["attachment_count"])
        self.assertEqual(sop.attachment_count, 1)

    def test_23_document_models_registry(self):
        """The mixin lists the four concrete controlled document models."""
        models = self.env["ls.qms.document.mixin"]._ls_qms_document_models()
        self.assertEqual(
            sorted(models),
            [
                "ls.qms.policy",
                "ls.qms.quality_plan",
                "ls.qms.sop",
                "ls.qms.work_instruction",
            ],
        )

    def test_24_reviewer_activities_are_scheduled(self):
        """Submitting a document creates an activity for each reviewer."""
        sop = self._create_sop(reviewer_ids=[(6, 0, [self.user_approver.id])])
        sop.with_user(self.user_author).action_submit_for_review()
        activities = self.env["mail.activity"].search(
            [("res_model", "=", sop._name), ("res_id", "=", sop.id)]
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.user_approver)

    def test_25_documents_due_for_review_selection(self):
        """The helper returns published documents inside the lead window."""
        sop = self._publish(self._create_sop())
        sop.write({"date_next_review": self.today + relativedelta(days=5)})
        due = self.env["ls.qms.sop"]._ls_qms_documents_due_for_review()
        self.assertIn(sop, due)
        sop.write({"date_next_review": self.today + relativedelta(days=365)})
        due = self.env["ls.qms.sop"]._ls_qms_documents_due_for_review()
        self.assertNotIn(sop, due)

    def test_26_parameter_fallbacks(self):
        """Invalid parameters fall back to the documented defaults."""
        mixin = self.env["ls.qms.document.mixin"]
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_qms.default_review_period_months", "not-a-number"
        )
        self.assertEqual(mixin._default_review_period_months(), 24)
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_qms.default_review_period_months", "-5"
        )
        self.assertEqual(mixin._default_review_period_months(), 24)
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_qms.default_review_period_months", "36"
        )
        self.assertEqual(mixin._default_review_period_months(), 36)

    def test_27_signature_hook_is_called(self):
        """The signature extension point returns True in the base module."""
        sop = self._create_sop()
        self.assertTrue(sop._ls_qms_signature_hook("approval"))

    def test_28_effective_date_defaults_to_today(self):
        """Publishing without an effective date uses the current date."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        sop.with_user(self.user_approver).action_approve()
        self.assertFalse(sop.date_effective)
        sop.with_user(self.user_approver).action_publish()
        self.assertEqual(sop.date_effective, fields.Date.context_today(sop))
