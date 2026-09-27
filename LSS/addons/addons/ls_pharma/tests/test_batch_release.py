# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the batch release decision and of its append-only guarantees."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..constants import RELEASE_CHECKLIST_FIELDS
from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestBatchRelease(LsPharmaCommon):
    """Exercise the release wizard, its gate and the immutability of records."""

    def setUp(self):
        """Bring a batch to quality assurance review for each test."""
        super().setUp()
        self.batch, self.record = self._run_batch_to_review()

    def _wizard_values(self, **overrides):
        """Return the values of a wizard with every check confirmed."""
        values = {
            "batch_id": self.batch.id,
            "decision": "released",
            "statement": "Reviewed against the approved specification.",
        }
        values.update(
            {field_name: True for field_name in RELEASE_CHECKLIST_FIELDS}
        )
        values.update(overrides)
        return values

    def test_batch_reaches_review(self):
        """The fixture leaves the batch under quality assurance review."""
        self.assertEqual(self.batch.state, "under_review")
        self.assertEqual(self.record.state, "approved")

    def test_release_records_the_decision_and_moves_the_batch(self):
        """A confirmed decision is stored and propagated to the batch."""
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        wizard.action_confirm()
        release = self.batch.release_id
        self.assertTrue(release)
        self.assertEqual(release.decision, "released")
        self.assertEqual(release.decided_by_user_id, self.qa_user)
        self.assertEqual(self.batch.state, "released")
        self.assertTrue(release.name.startswith("REL/"))

    def test_incomplete_checklist_blocks_a_release(self):
        """A release cannot be recorded while a check is unconfirmed."""
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values(check_reserve_samples=False))
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_rejection_does_not_need_the_checklist(self):
        """A rejection can be recorded without confirming every check."""
        values = {
            "batch_id": self.batch.id,
            "decision": "rejected",
            "statement": "Out-of-specification assay on the finished product.",
        }
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(values)
        )
        wizard.action_confirm()
        self.assertEqual(self.batch.state, "rejected")
        self.assertEqual(self.batch.release_id.decision, "rejected")

    def test_manufacturer_cannot_decide_on_the_batch(self):
        """The person who manufactured a batch cannot release it.

        The quality control unit of 21 CFR 211.22 is independent of
        production.
        """
        self.assertEqual(
            self.batch.user_manufactured_id, self.production_manager
        )
        # The production role holds no right on the release wizard
        # (AccessError, a subclass of UserError); the independence check of
        # action_confirm is the second barrier.
        with self.assertRaises(UserError):
            wizard = (
                self.env["ls.pharma.batch.release.wizard"]
                .with_user(self.production_manager)
                .create(self._wizard_values())
            )
            wizard.action_confirm()

    def test_release_requires_an_expiry_date(self):
        """A batch without an expiry date cannot be released."""
        self.batch.write({"date_expiry": False})
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_release_requires_every_record_to_be_approved(self):
        """An unapproved batch record blocks the release of the batch.

        21 CFR 211.192 requires all production and control records to be
        reviewed and approved by the quality control unit before release.
        """
        self._create_batch_record(
            self.batch, master_record_reference="MPR-TEST-002"
        )
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_yield_outside_limits_requires_an_investigation_reference(self):
        """An unexplained yield discrepancy blocks the release."""
        self.batch.write({"actual_yield_qty": 90000.0})
        self.assertTrue(self.batch.yield_investigation_required)
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()
        self.batch.write({"yield_investigation_reference": "DEV-2026-0007"})
        wizard.action_confirm()
        self.assertEqual(self.batch.state, "released")

    def test_decision_is_append_only(self):
        """A recorded decision can be neither modified nor deleted."""
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        wizard.action_confirm()
        release = self.batch.release_id
        with self.assertRaises(UserError):
            release.write({"decision": "rejected"})
        with self.assertRaises(UserError):
            release.write({"statement": "Amended after the fact."})
        with self.assertRaises(UserError):
            release.unlink()

    def test_integrity_digest_is_stamped_and_verifies(self):
        """The digest is stamped on creation and matches the stored values."""
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        wizard.action_confirm()
        release = self.batch.release_id
        self.assertTrue(release.integrity_hash)
        self.assertEqual(len(release.integrity_hash), 64)
        self.assertTrue(release.integrity_verified)
        release.action_verify_integrity()

    def test_checklist_report_lines_match_the_stored_answers(self):
        """The printed checklist is derived from the stored answers."""
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        wizard.action_confirm()
        lines = self.batch.release_id.get_checklist_report_lines()
        self.assertEqual(len(lines), len(RELEASE_CHECKLIST_FIELDS))
        for line in lines:
            self.assertTrue(line["confirmed"])
            self.assertTrue(line["label"])
            self.assertTrue(line["reference"])

    def test_a_batch_cannot_receive_two_decisions(self):
        """A second decision on the same batch is refused."""
        first = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        first.action_confirm()
        second = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(self._wizard_values())
        )
        with self.assertRaises(UserError):
            second.action_confirm()
