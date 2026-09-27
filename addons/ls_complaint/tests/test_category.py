# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the ls.complaint.category model."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestCategory(TestLsComplaintCommon):
    """Verify the category master data model."""

    def test_01_targets_default_to_zero(self):
        """A new category has no configured target."""
        category = self.env["ls.complaint.category"].create(
            {"name": "Fresh", "code": "TST-FRESH", "company_id": self.company.id}
        )
        self.assertEqual(category.acknowledgement_target_days, 0)
        self.assertEqual(category.investigation_target_days, 0)
        self.assertEqual(category.closure_target_days, 0)
        self.assertEqual(category.ae_reporting_deadline_days, 0)

    def test_02_negative_targets_refused(self):
        """Negative day targets are refused."""
        with self.assertRaises(ValidationError):
            self.env["ls.complaint.category"].create(
                {
                    "name": "Negative",
                    "code": "TST-NEG",
                    "company_id": self.company.id,
                    "closure_target_days": -1,
                }
            )

    def test_03_acknowledgement_after_closure_refused(self):
        """The acknowledgement target cannot exceed the closure target."""
        with self.assertRaises(ValidationError):
            self.env["ls.complaint.category"].create(
                {
                    "name": "Inconsistent",
                    "code": "TST-INC",
                    "company_id": self.company.id,
                    "acknowledgement_target_days": 40,
                    "closure_target_days": 30,
                }
            )

    def test_04_complaint_count(self):
        """The complaint count reflects the attached complaints."""
        self.assertEqual(self.category.complaint_count, 0)
        self._create_complaint()
        self.category.invalidate_recordset()
        self.assertEqual(self.category.complaint_count, 1)

    def test_05_action_view_complaints(self):
        """The stat button returns a window action filtered on the category."""
        action = self.category.action_view_complaints()
        self.assertEqual(action["res_model"], "ls.complaint")
        self.assertIn(("category_id", "=", self.category.id), action["domain"])
