# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for consignee line reconciliation arithmetic and status."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestLineReconciliation(RecallCommon):
    """Reconciliation totals and statuses follow the recorded quantities."""

    def test_accounted_and_outstanding(self):
        """Accounted is the sum of the three disposition quantities."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 100.0)
        line.write(
            {
                "qty_returned": 60.0,
                "qty_destroyed": 25.0,
                "qty_not_recovered": 5.0,
            }
        )
        self.assertEqual(line.qty_accounted, 90.0)
        self.assertEqual(line.qty_outstanding, 10.0)
        self.assertEqual(execution.qty_accounted, 90.0)
        self.assertEqual(execution.reconciliation_rate, 90.0)

    def test_status_reconciled(self):
        """A fully accounted line is reconciled."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 40.0)
        line.qty_returned = 40.0
        self.assertEqual(line.status, "reconciled")

    def test_status_discrepancy(self):
        """Accounting for more than was shipped is a discrepancy."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 40.0)
        line.qty_returned = 45.0
        self.assertEqual(line.status, "discrepancy")

    def test_status_progression(self):
        """Status follows notification and response."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 40.0)
        self.assertEqual(line.status, "pending")
        line.action_mark_notified()
        self.assertEqual(line.status, "notified")
        line.response_received = True
        self.assertEqual(line.status, "responded")

    def test_duplicate_consignee_and_lot_rejected(self):
        """The same consignee and lot cannot appear twice."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        with self.assertRaises(pg_errors.UniqueViolation):
            self._add_line(execution, self.partner_a, self.lot_1, 5.0)
            execution.line_ids.flush_recordset()

    def test_negative_quantity_rejected(self):
        """The database refuses a negative quantity."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        with self.assertRaises(pg_errors.CheckViolation):
            line.qty_returned = -1.0
            line.flush_recordset()

    def test_quantity_change_written_to_chatter(self):
        """A reconciliation edit is visible on the recall chatter."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        before = len(execution.message_ids)
        line.qty_returned = 4.0
        self.assertGreater(len(execution.message_ids), before)
        self.assertIn(
            "Reconciliation updated",
            execution.message_ids[0].body,
        )

    def test_lines_locked_on_finalised_recall(self):
        """Lines cannot be edited once the recall is finalised."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_initiate()
        wizard = self.env["ls.recall.close.wizard"].create(
            {
                "execution_id": execution.id,
                "mode": "cancel",
                "justification": "Withdrawn.",
            }
        )
        wizard.action_confirm()
        with self.assertRaises(UserError):
            line.qty_returned = 1.0

    def test_response_rate_counts_distinct_consignees(self):
        """A consignee holding two lots is counted once."""
        execution = self._create_execution(
            lot_ids=[(6, 0, (self.lot_1 + self.lot_2).ids)]
        )
        line_1 = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        self._add_line(execution, self.partner_a, self.lot_2, 10.0)
        self.assertEqual(execution.consignee_count, 1)
        line_1.response_received = True
        self.assertEqual(execution.consignee_responded_count, 1)
        self.assertEqual(execution.response_rate, 100.0)
