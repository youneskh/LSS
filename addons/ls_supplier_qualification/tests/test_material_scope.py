# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the qualified scope."""
from dateutil.relativedelta import relativedelta

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestMaterialScope(SupplierQualificationCommon):
    """Cover the scope lines and their own validity."""

    def test_qualify_sets_date(self):
        """Qualifying a scope line stamps the qualification date."""
        material = self._create_material(self.qualification, self.product)
        self.assertEqual(material.state, "qualified")
        self.assertEqual(material.qualification_date, self.today)

    def test_qualified_line_requires_date(self):
        """A qualified line without a date is rejected."""
        material = self._create_material(self.qualification, state="draft")
        with self.assertRaises(ValidationError):
            material.state = "qualified"

    def test_expiry_after_qualification_date(self):
        """The scope validity end must follow the qualification date."""
        material = self._create_material(self.qualification, self.product)
        with self.assertRaises(ValidationError):
            material.expiry_date = material.qualification_date

    def test_product_unique_per_dossier(self):
        """A catalogue product appears at most once per dossier."""
        self._create_material(self.qualification, self.product)
        with self.assertRaises(pg_errors.UniqueViolation):
            self._create_material(self.qualification, self.product)
            self.env.flush_all()

    def test_suspend_requires_qualified_state(self):
        """Only a qualified line can be suspended."""
        material = self._create_material(self.qualification, state="draft")
        with self.assertRaises(UserError):
            material.action_suspend()

    def test_cron_suspends_expired_scope(self):
        """The scheduled action suspends scope lines past their validity."""
        material = self._create_material(self.qualification, self.product)
        material.write({
            "qualification_date": self.today - relativedelta(years=2),
            "expiry_date": self.today - relativedelta(days=1),
        })
        self.assertTrue(material.is_expired)
        self.env["ls.supplier.material"]._cron_check_material_expiry()
        self.assertEqual(material.state, "suspended")
        self.assertTrue(material.suspension_reason)
