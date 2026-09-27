# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the discrepancy lifecycle."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestDiscrepancy(ValidationCommon):
    """Investigation, resolution and closure rules."""

    def setUp(self):
        """Create an execution carrying one failed test case."""
        super().setUp()
        self.protocol = self._create_protocol(test_count=2)
        self._approve_protocol(self.protocol)
        self.execution = self.env["ls.validation.execution"].with_user(
            self.user_engineer
        ).create({"protocol_id": self.protocol.id})
        self.execution.action_start()
        self.execution.result_ids.write(
            {"actual_result": "Observed", "verdict": "pass"}
        )
        self.failing_line = self.execution.result_ids[0]
        self.failing_line.write({"verdict": "fail"})
        self.failing_line.action_create_discrepancy()
        self.discrepancy = self.failing_line.discrepancy_id

    def test_discrepancy_is_prefilled_from_the_failed_line(self):
        """The discrepancy created from a line inherits its context."""
        self.assertTrue(self.discrepancy.reference.startswith("DISC/"))
        self.assertEqual(self.discrepancy.execution_id, self.execution)
        self.assertEqual(self.discrepancy.item_id, self.item)
        self.assertEqual(self.discrepancy.state, "open")
        self.assertIn(self.failing_line, self.discrepancy.result_ids)

    def test_discrepancy_is_only_created_for_a_failure(self):
        """A passing line cannot raise a discrepancy."""
        passing_line = self.execution.result_ids[1]
        with self.assertRaises(UserError):
            passing_line.action_create_discrepancy()

    def test_resolution_requires_the_investigation_documentation(self):
        """Root cause, impact and corrective action are mandatory."""
        self.discrepancy.action_start_investigation()
        with self.assertRaises(UserError):
            self.discrepancy.action_resolve()
        self.discrepancy.write({"root_cause": "Sensor drift"})
        with self.assertRaises(UserError):
            self.discrepancy.action_resolve()
        self.discrepancy.write({"corrective_action": "Sensor replaced"})
        with self.assertRaises(UserError):
            self.discrepancy.action_resolve()
        self.discrepancy.write({"impact_assessment": "No product impact"})
        self.discrepancy.action_resolve()
        self.assertEqual(self.discrepancy.state, "resolved")

    def test_closure_requires_a_capa_reference_when_flagged(self):
        """A discrepancy flagged as requiring a CAPA needs its reference."""
        self._resolve()
        self.discrepancy.write({"requires_capa": True})
        with self.assertRaises(UserError):
            self.discrepancy.action_close()
        self.discrepancy.write({"capa_reference": "CAPA-2026-014"})
        self._sign(self.discrepancy, "action_close", self.user_engineer)
        self.assertEqual(self.discrepancy.state, "closed")
        self.assertEqual(self.discrepancy.closed_by_id, self.user_engineer)

    def test_closed_discrepancy_is_frozen(self):
        """A closed discrepancy can no longer be modified or cancelled."""
        self._resolve()
        self._sign(self.discrepancy, "action_close", self.user_engineer)
        with self.assertRaises(UserError):
            self.discrepancy.write({"root_cause": "Rewritten"})
        with self.assertRaises(UserError):
            self.discrepancy.action_cancel()

    def test_closing_the_discrepancy_unblocks_the_execution(self):
        """The execution becomes approvable once discrepancies are closed."""
        self._resolve()
        self._sign(self.discrepancy, "action_close", self.user_engineer)
        self.execution.action_complete()
        self._sign(self.execution, "action_review", self.user_engineer_2)
        self._sign(self.execution, "action_approve", self.user_approver)
        self.assertEqual(self.execution.state, "approved")
        self.assertEqual(self.execution.open_discrepancy_count, 0)

    def test_only_open_discrepancy_can_be_deleted(self):
        """Deletion is limited to discrepancies still open."""
        self.discrepancy.action_start_investigation()
        with self.assertRaises(UserError):
            self.discrepancy.unlink()

    def _resolve(self):
        """Bring the discrepancy of the fixture to the resolved state."""
        self.discrepancy.action_start_investigation()
        self.discrepancy.write(
            {
                "root_cause": "Sensor drift",
                "corrective_action": "Sensor replaced and re-tested",
                "impact_assessment": "No impact on product quality",
            }
        )
        self.discrepancy.action_resolve()
