# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the protocol lifecycle and of the pre-approval freeze."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestProtocol(ValidationCommon):
    """Approval rules, content freeze and versioning of a protocol."""

    def test_protocol_without_test_cannot_be_submitted(self):
        """A protocol without test case cannot leave the draft state."""
        protocol = self.env["ls.validation.protocol"].create(
            {
                "name": "Empty protocol",
                "protocol_type": "iq",
                "item_id": self.item.id,
            }
        )
        with self.assertRaises(UserError):
            protocol.action_submit_review()

    def test_protocol_approval_records_the_approver(self):
        """The approval stamps the approver and the approval date."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        self.assertEqual(protocol.state, "approved")
        self.assertEqual(protocol.approver_id, self.user_approver)
        self.assertTrue(protocol.approval_date)
        self.assertEqual(protocol.signature_count, 1)

    def test_engineer_cannot_approve_a_protocol(self):
        """Approval authority is restricted to the approver group."""
        protocol = self._create_protocol()
        protocol.action_submit_review()
        with self.assertRaises(AccessError):
            self._sign(protocol, "action_approve", self.user_engineer)

    def test_test_cases_are_frozen_after_approval(self):
        """Test cases cannot be added, changed or removed after approval."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        with self.assertRaises(UserError):
            protocol.test_ids[0].write({"acceptance_criteria": "Changed"})
        with self.assertRaises(UserError):
            self.env["ls.validation.protocol.test"].create(
                {
                    "protocol_id": protocol.id,
                    "code": "TC-999",
                    "name": "Late test case",
                    "acceptance_criteria": "Late criterion",
                }
            )
        with self.assertRaises(UserError):
            protocol.test_ids[0].unlink()

    def test_protocol_content_is_frozen_after_approval(self):
        """The protocol header cannot be modified after approval."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        with self.assertRaises(UserError):
            protocol.write({"name": "Renamed after approval"})

    def test_planned_dates_are_ordered(self):
        """The planned end date cannot precede the planned start date."""
        protocol = self._create_protocol()
        with self.assertRaises(ValidationError):
            protocol.write(
                {
                    "planned_start_date": "2026-03-10",
                    "planned_end_date": "2026-03-01",
                }
            )

    def test_item_must_belong_to_the_master_plan_scope(self):
        """A protocol cannot reference an item outside the plan scope."""
        other_item = self.env["ls.validation.item"].create(
            {
                "code": "TEST-EQ-002",
                "name": "Out of scope item",
                "item_type": "equipment",
                "gxp_impact": "indirect",
                "criticality": "low",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["ls.validation.protocol"].create(
                {
                    "name": "Out of scope protocol",
                    "protocol_type": "iq",
                    "item_id": other_item.id,
                    "master_plan_id": self.master_plan.id,
                }
            )

    def test_new_version_copies_the_test_cases(self):
        """A new version starts in draft with the same test cases."""
        protocol = self._create_protocol(test_count=3)
        self._approve_protocol(protocol)
        action = protocol.action_new_version()
        new_protocol = self.env["ls.validation.protocol"].browse(
            action["res_id"]
        )
        self.assertEqual(new_protocol.state, "draft")
        self.assertEqual(new_protocol.version, 2)
        self.assertEqual(len(new_protocol.test_ids), 3)
        self.assertFalse(new_protocol.approver_id)

    def test_execution_requires_an_approved_protocol(self):
        """An execution cannot be created from a draft protocol."""
        protocol = self._create_protocol()
        with self.assertRaises(UserError):
            protocol.action_create_execution()
        with self.assertRaises(ValidationError):
            self.env["ls.validation.execution"].create(
                {"protocol_id": protocol.id}
            )

    def test_creating_an_execution_moves_the_protocol_to_execution(self):
        """The first execution switches the protocol to the execution state."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        protocol.action_create_execution()
        self.assertEqual(protocol.state, "execution")

    def test_protocol_with_executions_cannot_be_cancelled(self):
        """A protocol that has been executed cannot be cancelled."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        protocol.action_create_execution()
        with self.assertRaises(UserError):
            protocol.action_cancel()

    def test_test_case_code_is_unique_in_a_protocol(self):
        """Two test cases of a protocol cannot share the same identifier."""
        protocol = self._create_protocol()
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.env["ls.validation.protocol.test"].create(
                    {
                        "protocol_id": protocol.id,
                        "code": "TC-001",
                        "name": "Duplicate identifier",
                        "acceptance_criteria": "Criterion",
                    }
                )
                self.env.flush_all()
