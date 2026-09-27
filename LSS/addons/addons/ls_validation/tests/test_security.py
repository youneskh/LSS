# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Access right and record rule tests."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestSecurity(ValidationCommon):
    """Verification of the access matrix of the module."""

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_an_item(self):
        """The viewer group has no creation right."""
        with self.assertRaises(AccessError):
            self.env["ls.validation.item"].with_user(self.user_viewer).create(
                {
                    "code": "TEST-EQ-900",
                    "name": "Forbidden item",
                    "item_type": "equipment",
                    "gxp_impact": "none",
                    "criticality": "low",
                }
            )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_write_on_an_item(self):
        """The viewer group has no write right."""
        with self.assertRaises(AccessError):
            self.item.with_user(self.user_viewer).write({"name": "Renamed"})

    def test_viewer_can_read_an_item(self):
        """The viewer group can read the validation documentation."""
        self.assertEqual(
            self.item.with_user(self.user_viewer).name, "Test Sterilizer"
        )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_engineer_cannot_delete_a_protocol(self):
        """Deletion of a protocol is reserved to the manager group."""
        protocol = self._create_protocol()
        with self.assertRaises(AccessError):
            protocol.with_user(self.user_engineer).unlink()

    def test_manager_can_delete_a_draft_protocol(self):
        """The manager group can delete a draft protocol."""
        protocol = self._create_protocol()
        protocol.with_user(self.user_manager).unlink()
        self.assertFalse(protocol.exists())

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_engineer_cannot_modify_a_signature(self):
        """No group may modify the signature log."""
        signature = self.item._ls_create_signature(meaning="verified")
        with self.assertRaises(UserError):
            signature.with_user(self.user_engineer).write({"reason": "x"})

    def test_records_of_another_company_are_not_visible(self):
        """The multi-company rule hides the records of another company."""
        other_company = self.env["res.company"].create({"name": "Other Site"})
        other_item = (
            self.env["ls.validation.item"]
            .with_company(other_company)
            .create(
                {
                    "code": "OTHER-EQ-001",
                    "name": "Item of another company",
                    "item_type": "equipment",
                    "gxp_impact": "direct",
                    "criticality": "low",
                    "company_id": other_company.id,
                }
            )
        )
        visible = (
            self.env["ls.validation.item"]
            .with_user(self.user_engineer)
            .search([("id", "=", other_item.id)])
        )
        self.assertFalse(visible)

    def test_engineer_can_read_its_own_company_records(self):
        """Records of the active company remain visible."""
        visible = (
            self.env["ls.validation.item"]
            .with_user(self.user_engineer)
            .search([("id", "=", self.item.id)])
        )
        self.assertEqual(visible, self.item)
