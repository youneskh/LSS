# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the execution record and of its data entry rules."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestExecution(ValidationCommon):
    """Result generation, completion rules and review segregation."""

    def setUp(self):
        """Approve a protocol used by every test of the class."""
        super().setUp()
        self.protocol = self._create_protocol(test_count=3)
        self._approve_protocol(self.protocol)

    def test_results_are_generated_from_the_protocol(self):
        """Creating an execution copies the pre-approved test cases."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        self.assertEqual(len(execution.result_ids), 3)
        self.assertEqual(execution.test_count, 3)
        self.assertEqual(execution.pending_count, 3)
        self.assertEqual(execution.overall_result, "pending")
        self.assertEqual(
            execution.result_ids.mapped("protocol_test_id"),
            self.protocol.test_ids,
        )

    def test_execution_round_is_incremented(self):
        """A second execution of the same protocol gets the next round."""
        first = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        second = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        self.assertEqual(first.execution_round, 1)
        self.assertEqual(second.execution_round, 2)

    def test_completion_requires_every_verdict(self):
        """An execution with a pending result cannot be completed."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        execution.action_start()
        execution.result_ids[0].write(
            {"actual_result": "Value", "verdict": "pass"}
        )
        with self.assertRaises(UserError):
            execution.action_complete()

    def test_completion_requires_an_observed_result(self):
        """A verdict without observed result blocks the completion."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        execution.action_start()
        execution.result_ids.write({"verdict": "pass"})
        with self.assertRaises(UserError):
            execution.action_complete()

    def test_failure_requires_a_discrepancy(self):
        """A failed test case must be linked to a discrepancy."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        failing = execution.result_ids[0]
        failing.write({"verdict": "fail"})
        with self.assertRaises(UserError):
            execution.action_complete()
        failing.action_create_discrepancy()
        execution.action_complete()
        self.assertEqual(execution.state, "completed")
        self.assertEqual(execution.overall_result, "fail")

    def test_verdict_stamps_the_executor_and_the_timestamp(self):
        """Recording a verdict attributes the result to its author."""
        execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": self.protocol.id})
        execution.action_start()
        line = execution.result_ids[0]
        line.write({"actual_result": "Observed", "verdict": "pass"})
        self.assertEqual(line.performed_by_id, self.user_engineer)
        self.assertTrue(line.performed_on)

    def test_reviewer_must_differ_from_the_executor(self):
        """The four eyes principle is enforced on the review."""
        execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": self.protocol.id})
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        execution.action_complete()
        with self.assertRaises(UserError):
            self._sign(execution, "action_review", self.user_engineer)

    def test_results_are_frozen_after_completion(self):
        """Result lines cannot be modified once the execution is completed."""
        execution = self._execute_protocol(self.protocol)
        with self.assertRaises(UserError):
            execution.result_ids[0].write({"actual_result": "Rewritten"})

    def test_approval_requires_the_approver_group(self):
        """Approval of an execution is restricted to the approver group."""
        execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": self.protocol.id})
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        execution.action_complete()
        self._sign(execution, "action_review", self.user_engineer_2)
        with self.assertRaises(AccessError):
            self._sign(execution, "action_approve", self.user_engineer)

    def test_open_discrepancy_blocks_the_approval(self):
        """An execution carrying an open discrepancy cannot be approved."""
        execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": self.protocol.id})
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        failing = execution.result_ids[0]
        failing.write({"verdict": "fail"})
        failing.action_create_discrepancy()
        execution.action_complete()
        self._sign(execution, "action_review", self.user_engineer_2)
        with self.assertRaises(UserError):
            execution.with_user(self.user_approver).action_approve()

    def test_approved_execution_marks_the_protocol_executed(self):
        """The protocol becomes executed once every execution is approved."""
        execution = self._execute_protocol(self.protocol)
        self.assertEqual(execution.state, "approved")
        self.assertEqual(self.protocol.state, "executed")

    def test_approved_execution_cannot_be_cancelled_or_deleted(self):
        """An approved execution is protected."""
        execution = self._execute_protocol(self.protocol)
        with self.assertRaises(UserError):
            execution.action_cancel()
        with self.assertRaises(UserError):
            execution.unlink()

    def test_rejection_requires_a_reason(self):
        """Rejecting an execution requires a documented reason."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        execution.action_complete()
        with self.assertRaises(UserError):
            execution.action_reject()
        execution.write({"rejection_reason": "Instrument out of calibration"})
        execution.action_reject()
        self.assertEqual(execution.state, "rejected")

    def test_result_must_belong_to_the_executed_protocol(self):
        """A result line cannot reference a foreign test case."""
        other_protocol = self._create_protocol(test_count=1)
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        with self.assertRaises(ValidationError):
            self.env["ls.validation.execution.result"].create(
                {
                    "execution_id": execution.id,
                    "protocol_test_id": other_protocol.test_ids[0].id,
                }
            )

    def test_dates_are_ordered(self):
        """The end date cannot precede the start date."""
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        with self.assertRaises(ValidationError):
            execution.write(
                {
                    "date_start": "2026-05-10 10:00:00",
                    "date_end": "2026-05-09 10:00:00",
                }
            )
