# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the configuration models and their constraints."""

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestAuditConfiguration(AuditCommon):
    """Audit types, areas, auditor qualifications and finding categories."""

    def test_audit_type_code_unique_per_company(self):
        """A duplicated audit type code is rejected by the database."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.cr.savepoint():
                self.env["ls.audit.type"].create(
                    {
                        "name": "Duplicate",
                        "code": self.audit_type.code,
                        "company_id": self.company.id,
                    }
                )

    def test_area_complete_name_is_hierarchical(self):
        """The complete name concatenates the ancestor names."""
        self.assertEqual(
            self.area.complete_name, "Test Site / Test Filling Area"
        )

    def test_area_complete_name_follows_parent_rename(self):
        """Renaming a parent propagates to the children complete name."""
        self.area_parent.name = "Renamed Site"
        self.assertEqual(
            self.area.complete_name, "Renamed Site / Test Filling Area"
        )

    def test_area_cannot_be_its_own_ancestor(self):
        """A cycle in the area hierarchy is refused.

        Odoo 19 detects the cycle while maintaining the parent path and
        raises UserError ("Recursion Detected."), the parent class of
        ValidationError.
        """
        with self.assertRaises(UserError):
            self.area_parent.parent_id = self.area.id

    def test_area_parent_must_share_company(self):
        """A parent area of another company is refused."""
        other_company = self.env["res.company"].create(
            {"name": "Other Test Company"}
        )
        other_area = self.env["ls.audit.area"].create(
            {
                "name": "Other Area",
                "code": "OTHER-AREA",
                "company_id": other_company.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.area.parent_id = other_area.id

    def test_qualification_state_valid(self):
        """A qualification expiring far ahead is valid."""
        self.assertEqual(self.qualification_lead.qualification_state, "valid")

    def test_qualification_state_expiring(self):
        """A qualification within the warning window is flagged expiring."""
        self.qualification_auditor.expiry_date = self.today + relativedelta(
            days=10
        )
        self.assertEqual(
            self.qualification_auditor.qualification_state, "expiring"
        )

    def test_qualification_state_expired(self):
        """A lapsed qualification is flagged expired."""
        self.qualification_auditor.expiry_date = self.today - relativedelta(
            days=1
        )
        self.assertEqual(
            self.qualification_auditor.qualification_state, "expired"
        )

    def test_qualification_without_expiry_is_valid(self):
        """A qualification with no expiry date never lapses."""
        self.qualification_auditor.expiry_date = False
        self.assertEqual(
            self.qualification_auditor.qualification_state, "valid"
        )

    def test_qualification_expiry_before_qualification_date(self):
        """An expiry date earlier than the qualification date is refused."""
        with self.assertRaises(ValidationError):
            self.qualification_auditor.expiry_date = (
                self.qualification_auditor.qualification_date
                - relativedelta(days=1)
            )

    def test_qualification_scope_empty_covers_every_area(self):
        """An empty qualified scope covers every area."""
        self.assertTrue(
            self.qualification_auditor.is_qualified_for(
                self.area | self.area_other
            )
        )

    def test_qualification_scope_restricts_areas(self):
        """A restricted scope refuses areas outside it."""
        self.qualification_auditor.scope_ids = [(6, 0, self.area.ids)]
        self.assertTrue(self.qualification_auditor.is_qualified_for(self.area))
        self.assertFalse(
            self.qualification_auditor.is_qualified_for(self.area_other)
        )

    def test_expired_qualification_is_never_qualified(self):
        """An expired qualification covers no area at all."""
        self.qualification_auditor.expiry_date = self.today - relativedelta(
            days=1
        )
        self.assertFalse(
            self.qualification_auditor.is_qualified_for(self.area)
        )

    def test_one_qualification_per_user_and_company(self):
        """A second qualification for the same user is rejected."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.cr.savepoint():
                self.env["ls.audit.auditor"].create(
                    {
                        "user_id": self.user_auditor.id,
                        "company_id": self.company.id,
                        "qualification_date": self.today,
                    }
                )

    def test_finding_category_negative_deadline_refused(self):
        """A negative response deadline is refused."""
        with self.assertRaises(ValidationError):
            self.category_minor.response_deadline_days = -1

    def test_finding_category_defaults_are_loaded(self):
        """The five default finding categories are installed."""
        categories = self.env["ls.audit.finding.category"].search(
            [("company_id", "=", self.company.id)]
        )
        severities = set(categories.mapped("severity"))
        self.assertEqual(
            severities,
            {"critical", "major", "minor", "observation", "improvement"},
        )

    def test_critical_category_requires_capa(self):
        """The shipped critical category requires a CAPA and a root cause."""
        critical = self.env.ref("ls_audit.finding_category_critical")
        self.assertTrue(critical.requires_capa)
        self.assertTrue(critical.requires_root_cause)
