# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for Certificates of Analysis."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabCoa(LsLabCommon):
    """Cover BRU-22 and BRU-23."""

    def _approved_sample(self):
        """Return a sample carried through to the approved state."""
        sample = self._create_sample()
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        result.with_user(self.reviewer).action_review()
        sample.action_record_results()
        sample.with_user(self.reviewer).action_review()
        sample.with_user(self.manager).action_approve()
        return sample

    def test_certificate_requires_approved_sample(self):
        """A certificate cannot be issued from an unapproved sample (BRU-22)."""
        sample = self._create_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        with self.assertRaises(UserError):
            certificate.with_user(self.manager).action_issue()

    def test_issue_from_approved_sample(self):
        """A certificate issues from an approved sample and records the issuer."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        self.assertIn("LAB/COA/", certificate.name)
        certificate.with_user(self.manager).action_issue()
        self.assertEqual(certificate.state, "issued")
        self.assertEqual(certificate.issued_by_id, self.manager)
        self.assertEqual(certificate.conclusion, "conforms")

    def test_reportable_results_follow_specification_flag(self):
        """Only results flagged reportable appear on the certificate."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        expected = sample.result_ids.filtered(
            lambda res: res.specification_line_id.report_on_coa
        )
        self.assertEqual(certificate.reportable_result_ids, expected)

    def test_issued_certificate_is_frozen(self):
        """An issued certificate cannot be modified (BRU-23)."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        certificate.with_user(self.manager).action_issue()
        with self.assertRaises(UserError):
            certificate.write({"remarks": "Amended after issue"})

    def test_revision_requires_reason_and_supersedes(self):
        """A revision needs a reason and supersedes its predecessor."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        certificate.with_user(self.manager).action_issue()
        with self.assertRaises(UserError):
            certificate.with_user(self.manager).action_create_revision()
        certificate.write({"revision_reason": "Customer address corrected."})
        action = certificate.with_user(self.manager).action_create_revision()
        successor = self.env["ls.lab.coa"].browse(action["res_id"])
        self.assertEqual(successor.version, certificate.version + 1)
        self.assertEqual(successor.state, "draft")
        self.assertEqual(certificate.state, "superseded")
        self.assertEqual(certificate.successor_id, successor)
        self.assertEqual(successor.predecessor_id, certificate)

    def test_cancel_requires_reason(self):
        """Cancelling a draft certificate demands a reason."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        with self.assertRaises(UserError):
            certificate.with_user(self.manager).action_cancel()
        certificate.write({"cancel_reason": "Raised against the wrong sample."})
        certificate.with_user(self.manager).action_cancel()
        self.assertEqual(certificate.state, "cancelled")

    def test_issued_certificate_cannot_be_deleted(self):
        """An issued certificate cannot be deleted."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        certificate.with_user(self.manager).action_issue()
        with self.assertRaises(UserError):
            certificate.unlink()

    def test_signature_intent_recorded_on_issue(self):
        """The signature wizard records intent and issues the certificate."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        wizard = self.env["ls.lab.signature_wizard"].with_user(self.manager).create({
            "res_model": "ls.lab.coa",
            "res_id": certificate.id,
            "meaning": "issued",
            "acknowledged": True,
        })
        wizard.action_confirm()
        self.assertEqual(certificate.state, "issued")
        self.assertEqual(certificate.signature_user_id, self.manager)
        self.assertTrue(certificate.signature_date)
        self.assertTrue(certificate.signature_meaning)

    def test_signature_requires_acknowledgement(self):
        """The wizard refuses to act without the acknowledgement ticked."""
        sample = self._approved_sample()
        certificate = self.env["ls.lab.coa"].create({"sample_id": sample.id})
        wizard = self.env["ls.lab.signature_wizard"].with_user(self.manager).create({
            "res_model": "ls.lab.coa",
            "res_id": certificate.id,
            "meaning": "issued",
            "acknowledged": False,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_signature_refuses_unsupported_model(self):
        """The wizard only signs models that declare support."""
        wizard = self.env["ls.lab.signature_wizard"].create({
            "res_model": "res.partner",
            "res_id": self.env.user.partner_id.id,
            "meaning": "approved",
            "acknowledged": True,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()
