# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for SQL and Python constraints across the CAPA models."""

from datetime import timedelta

import psycopg2

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaConstraints(CapaCommon):
    """Database and application level integrity rules."""

    def test_due_date_before_identification_rejected(self):
        """The due date cannot precede the identification date."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            issue.date_due = issue.date_identified - timedelta(days=1)

    def test_due_date_equal_to_identification_accepted(self):
        """A same-day due date is accepted."""
        issue = self._make_issue()
        issue.date_due = issue.date_identified
        self.assertEqual(issue.date_due, issue.date_identified)

    @mute_logger("odoo.sql_db")
    def test_capa_reference_unique_per_company(self):
        """Two CAPA records in one company cannot share a reference."""
        issue = self._make_issue()
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self._make_issue(name=issue.name)

    @mute_logger("odoo.sql_db")
    def test_category_code_unique_per_company(self):
        """Category codes are unique within a company."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.env["ls.capa.category"].create(
                    {
                        "name": "Duplicate",
                        "code": self.category.code,
                        "company_id": self.company.id,
                    }
                )

    @mute_logger("odoo.sql_db")
    def test_category_lead_time_must_be_positive(self):
        """A category lead time of zero is rejected by the database."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.env["ls.capa.category"].create(
                    {
                        "name": "Zero",
                        "code": "ZERO",
                        "default_due_days": 0,
                    }
                )

    def test_category_code_cannot_be_blank(self):
        """A whitespace-only category code is rejected."""
        with self.assertRaises(ValidationError):
            self.env["ls.capa.category"].create(
                {"name": "Blank", "code": "   "}
            )

    @mute_logger("odoo.sql_db")
    def test_action_reference_unique(self):
        """Action references are unique."""
        action = self._make_action(self._make_issue())
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self._make_action(self._make_issue(), name=action.name)

    def test_cancelled_action_requires_reason_on_write(self):
        """Writing the cancelled state without a reason is rejected."""
        action = self._make_action(self._make_issue())
        with self.assertRaises(ValidationError):
            action.write({"state": "cancelled"})
