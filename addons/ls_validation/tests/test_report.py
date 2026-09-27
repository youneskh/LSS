# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the Validation Summary Report and of the status it grants."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestReport(ValidationCommon):
    """Completeness rules, approval and propagation to the item status."""

    def setUp(self):
        """Execute and approve a protocol so that a report can be issued."""
        super().setUp()
        self.protocol = self._create_protocol(test_count=2)
        self._approve_protocol(self.protocol)
        self.execution = self._execute_protocol(self.protocol)
        self.report = self.env["ls.validation.report"].create(
            {
                "name": "Validation Summary Report - Test Sterilizer",
                "item_id": self.item.id,
                "execution_ids": [(6, 0, self.execution.ids)],
                "summary": "<p>All test cases passed.</p>",
                "conclusion": "validated",
                "validity_months": 36,
            }
        )

    def test_reference_is_assigned_by_the_sequence(self):
        """A new report receives a reference from the dedicated sequence."""
        self.assertTrue(self.report.reference.startswith("VSR/"))

    def test_report_requires_approved_executions(self):
        """A report cannot consolidate an execution that is not approved."""
        draft_execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.protocol.id}
        )
        self.report.write({"execution_ids": [(4, draft_execution.id)]})
        with self.assertRaises(UserError):
            self.report.action_submit_review()

    def test_report_requires_a_summary(self):
        """A report without summary cannot be submitted for review."""
        self.report.write({"summary": False})
        with self.assertRaises(UserError):
            self.report.action_submit_review()

    def test_executions_must_concern_the_reported_item(self):
        """An execution of another item cannot be consolidated."""
        other_item = self.env["ls.validation.item"].create(
            {
                "code": "TEST-EQ-003",
                "name": "Other item",
                "item_type": "equipment",
                "gxp_impact": "direct",
                "criticality": "low",
            }
        )
        other_protocol = self._create_protocol(item=other_item)
        self._approve_protocol(other_protocol)
        other_execution = self._execute_protocol(other_protocol)
        with self.assertRaises(ValidationError):
            self.report.write({"execution_ids": [(4, other_execution.id)]})

    def test_restrictions_are_mandatory_for_a_restricted_conclusion(self):
        """A restricted conclusion requires documented restrictions."""
        with self.assertRaises(ValidationError):
            self.report.write({"conclusion": "validated_restricted"})

    def test_approval_grants_the_validated_status(self):
        """Approving the report validates the item until the expiry date."""
        self.report.action_submit_review()
        self._sign(self.report, "action_approve", self.user_approver)
        self.assertEqual(self.report.state, "approved")
        today = fields.Date.context_today(self.report)
        self.assertEqual(self.report.valid_from, today)
        self.assertEqual(
            self.report.valid_until, today + relativedelta(months=36)
        )
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "validated")
        self.assertEqual(self.item.current_report_id, self.report)

    def test_engineer_cannot_approve_a_report(self):
        """Approval of a report is restricted to the approver group."""
        self.report.action_submit_review()
        with self.assertRaises(AccessError):
            self._sign(self.report, "action_approve", self.user_engineer)

    def test_approved_report_is_frozen(self):
        """An approved report can no longer be modified or cancelled."""
        self.report.action_submit_review()
        self._sign(self.report, "action_approve", self.user_approver)
        with self.assertRaises(UserError):
            self.report.write({"summary": "<p>Rewritten</p>"})
        with self.assertRaises(UserError):
            self.report.action_cancel()

    def test_validity_without_expiry(self):
        """A validity of zero month grants a status without expiry date."""
        self.report.write({"validity_months": 0})
        self.report.action_submit_review()
        self._sign(self.report, "action_approve", self.user_approver)
        self.assertFalse(self.report.valid_until)
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "validated")

    def test_critical_failure_blocks_a_validated_conclusion(self):
        """A failed critical test case forbids the conclusion 'Validated'."""
        protocol = self._create_protocol(test_count=2)
        self._approve_protocol(protocol)
        execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": protocol.id})
        execution.action_start()
        execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        critical_line = execution.result_ids.filtered("is_critical")[0]
        critical_line.write({"verdict": "fail"})
        critical_line.action_create_discrepancy()
        discrepancy = critical_line.discrepancy_id
        discrepancy.action_start_investigation()
        discrepancy.write(
            {
                "root_cause": "Component failure",
                "corrective_action": "Component replaced",
                "impact_assessment": "Qualification not demonstrated",
            }
        )
        discrepancy.action_resolve()
        self._sign(discrepancy, "action_close", self.user_engineer)
        execution.action_complete()
        self._sign(execution, "action_review", self.user_engineer_2)
        self._sign(execution, "action_approve", self.user_approver)
        report = self.env["ls.validation.report"].create(
            {
                "name": "Report with a critical failure",
                "item_id": self.item.id,
                "execution_ids": [(6, 0, execution.ids)],
                "summary": "<p>One critical test case failed.</p>",
                "conclusion": "validated",
            }
        )
        report.action_submit_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_approver).action_approve()

    def test_expiring_status_is_derived_from_the_notice_period(self):
        """An item expiring within the notice period is flagged as expiring."""
        self.report.write({"validity_months": 1})
        self.report.action_submit_review()
        self._sign(self.report, "action_approve", self.user_approver)
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "expiring")
