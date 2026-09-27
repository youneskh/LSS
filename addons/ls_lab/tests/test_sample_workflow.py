# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for the sample state machine and segregation of duties."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabSampleWorkflow(LsLabCommon):
    """Cover BRU-06, BRU-07 and BRU-11 to BRU-15."""

    def test_registration_generates_result_lines(self):
        """One result line is created per specification line (BRU-07)."""
        specification = self._create_approved_specification()
        sample = self._create_sample(specification)
        self.assertEqual(len(sample.result_ids), len(specification.line_ids))
        self.assertTrue(all(res.state == "draft" for res in sample.result_ids))
        self.assertEqual(sample.overall_result, "pending")

    def test_sample_requires_approved_specification(self):
        """A draft specification cannot be used by a sample (BRU-06)."""
        method = self._create_approved_method(name="Unapproved spec method")
        draft_specification = self.env["ls.lab.specification"].create({
            "name": "Draft specification",
            "product_id": self.product.id,
            "line_ids": [(0, 0, {
                "test_method_id": method.id,
                "criterion_type": "min",
                "min_value": 1.0,
            })],
        })
        with self.assertRaises(ValidationError):
            self.env["ls.lab.sample"].create({
                "product_id": self.product.id,
                "specification_id": draft_specification.id,
            })

    def test_sequence_assigned_on_create(self):
        """A sample receives a reference from the sequence."""
        sample = self._create_sample()
        self.assertNotEqual(sample.name, "New")
        self.assertIn("LAB/SMP/", sample.name)

    def test_full_happy_path(self):
        """A conforming sample proceeds through every state to approved."""
        sample = self._create_sample()
        sample.action_start()
        self.assertEqual(sample.state, "in_progress")
        sample.action_start_testing()
        self.assertEqual(sample.state, "testing")

        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        self.assertEqual(result.evaluation, "conform")

        sample.action_record_results()
        self.assertEqual(sample.state, "results_recorded")

        result.with_user(self.reviewer).action_review()
        sample.with_user(self.reviewer).action_review()
        self.assertEqual(sample.state, "reviewed")
        self.assertEqual(sample.reviewed_by_id, self.reviewer)

        sample.with_user(self.manager).action_approve()
        self.assertEqual(sample.state, "approved")
        self.assertEqual(sample.overall_result, "conform")

    def test_cannot_record_results_with_pending_mandatory_test(self):
        """Results cannot be confirmed while a mandatory test is empty (BRU-11)."""
        sample = self._create_sample()
        sample.action_start()
        sample.action_start_testing()
        with self.assertRaises(UserError):
            sample.action_record_results()

    def test_cannot_review_with_unreviewed_result(self):
        """The sample cannot be reviewed while a result is unreviewed (BRU-12)."""
        sample = self._create_sample()
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        sample.action_record_results()
        with self.assertRaises(UserError):
            sample.with_user(self.reviewer).action_review()

    def test_analyst_cannot_review_own_sample(self):
        """The sample reviewer may not be an analyst on it (BRU-13)."""
        sample = self._create_sample()
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        result.with_user(self.reviewer).action_review()
        sample.action_record_results()
        with self.assertRaises(ValidationError):
            sample.with_user(self.analyst).action_review()

    def test_reviewer_cannot_approve_own_review(self):
        """The approver may not be the reviewer (BRU-14)."""
        sample = self._create_sample()
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        result.with_user(self.reviewer).action_review()
        sample.action_record_results()
        sample.with_user(self.reviewer).action_review()
        with self.assertRaises(ValidationError):
            sample.with_user(self.reviewer).action_approve()

    def test_cancellation_requires_reason(self):
        """The cancellation wizard demands a reason (BRU-26)."""
        sample = self._create_sample()
        wizard = self.env["ls.lab.sample_cancel_wizard"].create({
            "sample_id": sample.id,
            "reason": "Sample container damaged in transit",
        })
        wizard.action_confirm()
        self.assertEqual(sample.state, "cancelled")
        self.assertTrue(sample.cancel_reason)
        self.assertEqual(sample.cancelled_by_id, self.env.user)

    def test_no_result_added_to_approved_sample(self):
        """A result cannot be created on an approved sample."""
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
        with self.assertRaises(UserError):
            self.env["ls.lab.test_result"].create({
                "sample_id": sample.id,
                "specification_line_id": sample.specification_id.line_ids[0].id,
            })

    def test_overdue_cron_does_not_change_state(self):
        """The overdue notice never mutates a regulated state (BRU-29)."""
        sample = self._create_sample()
        sample.write({"due_date": "2000-01-01"})
        state_before = sample.state
        self.env["ls.lab.sample"]._cron_notify_overdue_samples()
        self.assertEqual(sample.state, state_before)
