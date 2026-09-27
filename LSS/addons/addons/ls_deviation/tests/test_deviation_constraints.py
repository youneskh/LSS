# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Constraint and data integrity tests."""

from datetime import timedelta

import psycopg2

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationConstraints(DeviationCommon):
    """Verify Python and SQL level invariants."""

    def test_occurrence_after_detection_rejected(self):
        """Occurrence cannot postdate detection."""
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            self._create_deviation(
                occurrence_date=now,
                detection_date=now - timedelta(hours=1),
            )

    def test_detection_after_report_rejected(self):
        """Detection cannot postdate the moment of recording."""
        deviation = self._create_deviation()
        with self.assertRaises(ValidationError):
            deviation.detection_date = fields.Datetime.now() + timedelta(days=2)

    def test_planned_deviation_requires_justification(self):
        """A planned deviation must be justified."""
        with self.assertRaises(ValidationError):
            self._create_deviation(is_planned=True)

    def test_planned_deviation_with_justification_accepted(self):
        """A justified planned deviation is accepted."""
        deviation = self._create_deviation(
            is_planned=True,
            justification="Approved in advance under change control.",
        )
        self.assertTrue(deviation.is_planned)

    def test_quantity_requires_product(self):
        """An affected quantity without a product is rejected."""
        with self.assertRaises(ValidationError):
            self._create_deviation(quantity_affected=5.0)

    @mute_logger("odoo.sql_db")
    def test_negative_quantity_rejected_by_sql(self):
        """The SQL check constraint rejects a negative quantity."""
        with self.assertRaises(psycopg2.errors.CheckViolation):
            with self.cr.savepoint():
                self._create_deviation(
                    product_id=self.product.id, quantity_affected=-1.0
                )

    def test_has_impact_computed(self):
        """has_impact reflects the individual impact flags."""
        deviation = self._create_deviation()
        self.assertFalse(deviation.has_impact)
        deviation.impact_regulatory = True
        self.assertTrue(deviation.has_impact)

    def test_product_uom_mirrored(self):
        """The product unit of measure is mirrored onto the deviation."""
        deviation = self._create_deviation(product_id=self.product.id)
        self.assertEqual(deviation.product_uom_id, self.product.uom_id)

    def test_days_open_uses_closure_date(self):
        """days_open stops counting once the record is closed."""
        deviation = self._create_deviation(
            occurrence_date=fields.Datetime.now() - timedelta(days=10, hours=1),
            detection_date=fields.Datetime.now() - timedelta(days=10),
        )
        self.assertGreaterEqual(deviation.days_open, 10)
        deviation.closure_date = deviation.detection_date + timedelta(days=3)
        deviation.invalidate_recordset(["days_open"])
        self.assertEqual(deviation.days_open, 3)

    def test_is_overdue_flag_and_search(self):
        """is_overdue is computed and searchable."""
        deviation = self._create_deviation(
            due_date=fields.Date.context_today(self.env.user) - timedelta(days=1)
        )
        self.assertTrue(deviation.is_overdue)
        found = self.env["ls.deviation"].search(
            [("is_overdue", "=", True), ("id", "=", deviation.id)]
        )
        self.assertIn(deviation, found)
        not_found = self.env["ls.deviation"].search(
            [("is_overdue", "=", False), ("id", "=", deviation.id)]
        )
        self.assertNotIn(deviation, not_found)

    def test_closed_record_is_not_overdue(self):
        """A closed record is never flagged overdue."""
        deviation = self._create_deviation(
            due_date=fields.Date.context_today(self.env.user) - timedelta(days=5)
        )
        deviation.state = "closed"
        deviation.invalidate_recordset(["is_overdue"])
        self.assertFalse(deviation.is_overdue)

    def test_is_overdue_search_rejects_bad_operator(self):
        """The is_overdue search only supports equality operators."""
        # Odoo 19 rejects an ordering operator on a boolean field in its
        # domain parser (ValueError), before the custom search method runs.
        with self.assertRaises(ValueError):
            self.env["ls.deviation"].search([("is_overdue", ">", True)])

    def test_delete_blocked_beyond_reported(self):
        """A deviation past Reported cannot be deleted."""
        deviation = self._advance_to_assessed(self._create_deviation())
        with self.assertRaises(UserError):
            deviation.unlink()

    def test_delete_allowed_while_reported(self):
        """A deviation still in Reported may be deleted by a manager."""
        deviation = self._create_deviation()
        deviation.unlink()
        self.assertFalse(deviation.exists())

    def test_copy_resets_workflow(self):
        """Duplicating a deviation resets its state and reference."""
        deviation = self._advance_to_assessed(self._create_deviation())
        copy = deviation.copy()
        self.assertEqual(copy.state, "reported")
        self.assertNotEqual(copy.name, deviation.name)

    def test_terminal_record_not_writable_by_investigator(self):
        """A closed record is protected from non-manager edits."""
        deviation = self._create_deviation()
        deviation.state = "closed"
        with self.assertRaises(UserError):
            deviation.with_user(self.user_investigator).write(
                {"title": "Changed after closure"}
            )

    def test_company_target_days_fallback(self):
        """An unset closure target falls back to the documented default."""
        self.company.ls_deviation_target_days_major = 0
        self.assertEqual(self.company._ls_deviation_target_days("major"), 30)
        self.company.ls_deviation_target_days_major = 45
        self.assertEqual(self.company._ls_deviation_target_days("major"), 45)
