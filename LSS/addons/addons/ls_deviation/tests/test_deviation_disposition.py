# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Product disposition tests."""

import psycopg2

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationDisposition(DeviationCommon):
    """Verify the product disposition rules."""

    def setUp(self):
        super().setUp()
        self.deviation = self._advance_to_investigation(self._create_deviation())

    def _make_disposition(self, **overrides):
        values = {
            "deviation_id": self.deviation.id,
            "product_id": self.product.id,
            "lot_id": self.lot.id,
            "quantity": 25.0,
            "decision": "use_as_is",
            "justification": "Quality attributes demonstrated unaffected.",
        }
        values.update(overrides)
        return self.env["ls.deviation.disposition"].create(values)

    def test_disposition_starts_draft(self):
        """A new disposition starts in draft."""
        self.assertEqual(self._make_disposition().state, "draft")

    def test_approval_stamps_approver(self):
        """Approval stamps the approver and the approval date."""
        disposition = self._make_disposition()
        disposition.with_user(self.user_manager).action_approve()
        self.assertEqual(disposition.approved_by_id, self.user_manager)
        self.assertTrue(disposition.approval_date)

    def test_cannot_approve_twice(self):
        """Only a draft disposition can be approved."""
        disposition = self._make_disposition()
        disposition.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            disposition.with_user(self.user_manager).action_approve()

    def test_lot_must_match_product(self):
        """A lot belonging to a different product is rejected."""
        other_product = self.env["product.product"].create(
            {"name": "Other Product", "tracking": "lot"}
        )
        other_lot = self.env["stock.lot"].create(
            {
                "name": "LOT-OTHER",
                "product_id": other_product.id,
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(ValidationError):
            self._make_disposition(lot_id=other_lot.id)

    @mute_logger("odoo.sql_db")
    def test_quantity_must_be_positive(self):
        """The SQL constraint rejects a non-positive quantity."""
        with self.assertRaises(psycopg2.errors.CheckViolation):
            with self.cr.savepoint():
                self._make_disposition(quantity=0.0)

    def test_uom_is_mirrored(self):
        """The disposition mirrors the product unit of measure."""
        self.assertEqual(
            self._make_disposition().product_uom_id, self.product.uom_id
        )

    def test_rejection_sets_state(self):
        """A rejected disposition records the rejected state."""
        disposition = self._make_disposition()
        disposition.with_user(self.user_manager).action_reject()
        self.assertEqual(disposition.state, "rejected")

    def test_all_decisions_are_selectable(self):
        """Every documented disposition decision can be recorded."""
        decisions = [
            "use_as_is",
            "rework",
            "reprocess",
            "quarantine",
            "reject",
            "destroy",
            "return_supplier",
        ]
        for decision in decisions:
            disposition = self._make_disposition(decision=decision)
            self.assertEqual(disposition.decision, decision)
