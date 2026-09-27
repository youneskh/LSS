# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the validation item, its status derivation and its constraints."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from psycopg2 import IntegrityError

from odoo.tools import mute_logger

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestItem(ValidationCommon):
    """Status derivation, constraints and actions of a validation item."""

    def test_new_item_is_not_validated(self):
        """A freshly created item has no validated status."""
        self.assertEqual(self.item.validation_state, "not_validated")
        self.assertFalse(self.item.valid_until)

    def test_display_name_uses_code_and_name(self):
        """The item is displayed as ``[CODE] Designation``."""
        self.assertEqual(
            self.item.display_name, "[TEST-EQ-001] Test Sterilizer"
        )

    @mute_logger("odoo.sql_db")
    def test_code_is_unique_per_company(self):
        """Two items of a company cannot share the same code."""
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["ls.validation.item"].create(
                    {
                        "code": self.item.code,
                        "name": "Duplicate",
                        "item_type": "equipment",
                        "gxp_impact": "direct",
                        "criticality": "low",
                    }
                )
                self.env.flush_all()

    def test_item_is_in_validation_when_a_protocol_is_approved(self):
        """An approved protocol moves the item to the in validation status."""
        protocol = self._create_protocol()
        self._approve_protocol(protocol)
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "in_validation")

    def test_retirement_requires_a_date(self):
        """Retiring without a date is refused by the Python constraint."""
        with self.assertRaises(ValidationError):
            self.item.write({"retired": True})

    def test_action_retire_and_reinstate(self):
        """The retirement action sets the date and the retired status."""
        self.item.action_retire()
        self.assertTrue(self.item.retired)
        self.assertEqual(self.item.validation_state, "retired")
        self.assertEqual(
            self.item.retirement_date, fields.Date.context_today(self.item)
        )
        with self.assertRaises(UserError):
            self.item.action_retire()
        self.item.action_reinstate()
        self.assertFalse(self.item.retired)
        with self.assertRaises(UserError):
            self.item.action_reinstate()

    def test_next_review_date_uses_the_interval(self):
        """The proposed review date follows the configured interval."""
        self.item.revalidation_interval_months = 12
        today = fields.Date.context_today(self.item)
        self.assertEqual(
            self.item._next_review_date(),
            today + relativedelta(months=12),
        )

    def test_next_review_date_is_empty_without_interval(self):
        """No review date is proposed when the interval is zero."""
        self.item.revalidation_interval_months = 0
        self.assertFalse(self.item._next_review_date())

    def test_expiry_notice_days_falls_back_on_the_default(self):
        """An unreadable parameter falls back on the documented default."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_validation.expiry_notice_days", "not-a-number"
        )
        self.assertEqual(self.item._expiry_notice_days(), 60)

    def test_action_view_protocols_filters_on_the_item(self):
        """The stat button opens the protocols of the item only."""
        action = self.item.action_view_protocols()
        self.assertEqual(action["res_model"], "ls.validation.protocol")
        self.assertIn(("item_id", "=", self.item.id), action["domain"])
