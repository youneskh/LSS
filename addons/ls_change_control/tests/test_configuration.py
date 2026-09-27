# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the configuration models: categories, areas and templates."""

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestConfiguration(ChangeControlCommon):
    """Verify the configuration constraints and helper methods."""

    @mute_logger("odoo.sql_db")
    def test_impact_area_code_is_unique(self):
        """Two impact areas cannot share the same code."""
        self.env["ls.change_control.impact_area"].create(
            {"name": "Area One", "code": "UNIQ1"}
        )
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["ls.change_control.impact_area"].create(
                    {"name": "Area Two", "code": "UNIQ1"}
                )

    @mute_logger("odoo.sql_db")
    def test_category_code_is_unique(self):
        """Two categories cannot share the same code."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["ls.change_control.category"].create(
                    {"name": "Duplicate", "code": "TESTCAT"}
                )

    @mute_logger("odoo.sql_db")
    def test_category_delays_cannot_be_negative(self):
        """The implementation delay is checked at database level."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["ls.change_control.category"].create(
                    {
                        "name": "Negative",
                        "code": "NEG",
                        "implementation_delay": -1,
                    }
                )

    @mute_logger("odoo.sql_db")
    def test_approval_role_is_unique_per_category(self):
        """A role can only be defined once in an approval template."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["ls.change_control.approval_template"].create(
                    {
                        "category_id": self.category.id,
                        "approval_role": "quality_assurance",
                    }
                )

    def test_default_approver_must_be_internal(self):
        """A portal user cannot be a default approver."""
        portal_user = new_test_user(
            self.env, login="ls_cc_portal", groups="base.group_portal"
        )
        with self.assertRaises(ValidationError):
            self.env["ls.change_control.approval_template"].create(
                {
                    "category_id": self.category.id,
                    "approval_role": "validation",
                    "user_id": portal_user.id,
                }
            )

    def test_get_verification_delay_uses_category_first(self):
        """The category delay wins over the company default."""
        self.assertEqual(
            self.category.get_verification_delay(self.company), 15
        )

    def test_get_verification_delay_falls_back_to_company(self):
        """The company default is used when the category defines none."""
        self.category.verification_delay = 0
        self.company.ls_cc_default_verification_delay = 45
        self.assertEqual(
            self.category.get_verification_delay(self.company), 45
        )

    def test_mandatory_verification_needs_a_delay(self):
        """A mandatory verification without any usable delay is refused."""
        self.company.ls_cc_default_verification_delay = 0
        with self.assertRaises(ValidationError):
            self.env["ls.change_control.category"].create(
                {
                    "name": "No Delay",
                    "code": "NODELAY",
                    "requires_verification": True,
                    "verification_delay": 0,
                }
            )
