# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Access right and record rule tests."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestComplaintSecurity(TestLsComplaintCommon):
    """Verify the four access levels and the segregation record rules."""

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_01_viewer_can_read_only(self):
        """A viewer can read but cannot write, create or delete."""
        complaint = self._create_complaint()
        self.assertTrue(complaint.with_user(self.user_viewer).read(["name"]))
        with self.assertRaises(AccessError):
            complaint.with_user(self.user_viewer).write({"summary": "Changed"})
        with self.assertRaises(AccessError):
            self.env["ls.complaint"].with_user(self.user_viewer).create(
                {
                    "summary": "New",
                    "description": "New",
                    "channel": "email",
                    "received_by_id": self.user_viewer.id,
                }
            )

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_02_investigator_can_create(self):
        """An investigator can create a complaint."""
        complaint = (
            self.env["ls.complaint"]
            .with_user(self.user_investigator)
            .create(
                {
                    "summary": "Created by investigator",
                    "description": "Description",
                    "channel": "email",
                    "category_id": self.category.id,
                    "owner_id": self.user_investigator.id,
                    "received_by_id": self.user_investigator.id,
                    "product_related": False,
                }
            )
        )
        self.assertTrue(complaint.name.startswith("CMP/"))

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_03_investigator_cannot_write_foreign_complaint(self):
        """The record rule limits an investigator to the complaints he owns."""
        complaint = self._create_complaint(
            owner_id=self.user_investigator.id,
            received_by_id=self.user_investigator.id,
        )
        with self.assertRaises(AccessError):
            complaint.with_user(self.user_other_investigator).write(
                {"summary": "Hijacked"}
            )
        complaint.with_user(self.user_investigator).write({"summary": "Own update"})
        self.assertEqual(complaint.summary, "Own update")

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_04_reviewer_can_write_any_complaint(self):
        """A reviewer is not limited by the ownership rule."""
        complaint = self._create_complaint()
        complaint.with_user(self.user_reviewer).write({"summary": "Reviewed"})
        self.assertEqual(complaint.summary, "Reviewed")

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_05_only_manager_can_delete(self):
        """Deletion is restricted to the manager group."""
        complaint = self._create_complaint()
        with self.assertRaises(AccessError):
            complaint.with_user(self.user_reviewer).unlink()
        complaint.with_user(self.user_manager).unlink()

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_06_only_manager_can_configure_categories(self):
        """Category master data is restricted to the manager group."""
        with self.assertRaises(AccessError):
            self.env["ls.complaint.category"].with_user(
                self.user_investigator
            ).create({"name": "Forbidden", "code": "FRB"})
        category = self.env["ls.complaint.category"].with_user(
            self.user_manager
        ).create({"name": "Allowed", "code": "ALW"})
        self.assertTrue(category)

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_07_cancel_wizard_restricted_to_manager(self):
        """The cancellation wizard is only available to managers."""
        complaint = self._create_complaint()
        with self.assertRaises(AccessError):
            self.env["ls.complaint.cancel.wizard"].with_user(
                self.user_reviewer
            ).create({"complaint_id": complaint.id, "reason": "Test"})
        wizard = self.env["ls.complaint.cancel.wizard"].with_user(
            self.user_manager
        ).create({"complaint_id": complaint.id, "reason": "Test"})
        self.assertTrue(wizard)

    def test_08_group_hierarchy(self):
        """Each group implies the less privileged one."""
        self.assertIn(self.group_viewer, self.group_investigator.implied_ids)
        self.assertIn(self.group_investigator, self.group_reviewer.implied_ids)
        self.assertIn(self.group_reviewer, self.group_manager.implied_ids)

    def test_09_multi_company_rule_present(self):
        """A global multi-company rule protects each model of the module."""
        models = [
            "ls.complaint",
            "ls.complaint.category",
            "ls.complaint.investigation",
            "ls.complaint.resolution",
            "ls.complaint.adverse_event",
        ]
        for model_name in models:
            rules = self.env["ir.rule"].search(
                [("model_id.model", "=", model_name), ("global", "=", True)]
            )
            self.assertTrue(
                rules, f"No global record rule found for {model_name}"
            )
