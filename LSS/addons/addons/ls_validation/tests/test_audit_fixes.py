# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

Odoo 19 normalises the operators "=" and "!=" to "in" and "not in" before
it calls the search method of a non-stored field; the counters of the
executions must still be searchable.
"""

from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(ValidationCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def test_counter_search_with_equality(self):
        """Searching executions on an exact counter value finds them."""
        protocol = self._create_protocol(test_count=1, critical=False)
        self._approve_protocol(protocol)
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": protocol.id}
        )
        found = self.env["ls.validation.execution"].search(
            [("failed_count", "=", 0), ("id", "=", execution.id)]
        )
        self.assertEqual(found, execution)
        found = self.env["ls.validation.execution"].search(
            [("open_discrepancy_count", "!=", 0), ("id", "=", execution.id)]
        )
        self.assertFalse(found)

    def test_operator_evaluation(self):
        """The helper evaluates the normalised operators."""
        evaluate = self.env["ls.validation.execution"]._evaluate_operator
        self.assertTrue(evaluate(0, "in", [0]))
        self.assertTrue(evaluate(1, "not in", [0]))
        self.assertTrue(evaluate(2, ">", 1))
        self.assertFalse(evaluate(2, "like", 2))
