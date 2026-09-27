# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the access rights and the record rules."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestSecurity(ChangeControlCommon):
    """Verify that each group has exactly the rights of the specification."""

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_a_request(self):
        """A viewer has read only access."""
        with self.assertRaises(AccessError):
            self._create_request(user=self.user_viewer)

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_viewer_cannot_write_a_request(self):
        """A viewer cannot modify a request."""
        request = self._create_request(user=self.user_requester)
        with self.assertRaises(AccessError):
            request.with_user(self.user_viewer).write({"title": "Rewritten"})

    def test_viewer_can_read_a_request(self):
        """A viewer sees the change requests of their company."""
        request = self._create_request(user=self.user_requester)
        self.assertTrue(request.with_user(self.user_viewer).read(["title"]))

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_requester_cannot_modify_another_requester_draft(self):
        """The ownership record rule isolates the drafts of each requester."""
        request = self._create_request(user=self.user_requester)
        with self.assertRaises(AccessError):
            request.with_user(self.user_other_requester).write(
                {"title": "Rewritten"}
            )

    def test_manager_may_modify_any_request(self):
        """A manager is not restricted by the ownership rule."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_manager).write({"title": "Reviewed"})
        self.assertEqual(request.title, "Reviewed")

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_requester_cannot_delete_a_request(self):
        """Deletion is reserved to change control managers."""
        request = self._create_request(user=self.user_requester)
        with self.assertRaises(AccessError):
            request.with_user(self.user_requester).unlink()

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_requester_cannot_edit_the_configuration(self):
        """The configuration is reserved to change control managers."""
        with self.assertRaises(AccessError):
            self.env["ls.change_control.category"].with_user(
                self.user_requester
            ).create({"name": "Forbidden", "code": "FORB"})

    def test_manager_may_edit_the_configuration(self):
        """A manager maintains the change control configuration."""
        category = self.env["ls.change_control.category"].with_user(
            self.user_manager
        ).create({"name": "Allowed", "code": "ALLOW"})
        self.assertTrue(category.exists())

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_multi_company_isolation(self):
        """A user does not see the requests of another company."""
        other_company = self.env["res.company"].create({"name": "Other Site"})
        # The manager must belong to the other company to create in it.
        self.user_manager.write({"company_ids": [(4, other_company.id)]})
        request = self._create_request(
            user=self.user_manager, company_id=other_company.id
        )
        visible = self.request_model.with_user(self.user_requester).search(
            [("id", "=", request.id)]
        )
        self.assertFalse(
            visible, "A request of another company must not be visible."
        )

    def test_approver_cannot_change_the_request_state_directly(self):
        """An approver acts through the approval, never on the state."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        with self.assertRaises(AccessError):
            request.with_user(self.user_approver_qa).write({"state": "approved"})

    def test_group_membership_is_cumulative(self):
        """A manager holds the rights of every lower group."""
        self.assertTrue(self.user_manager.has_group(self.group_approver))
        self.assertTrue(self.user_manager.has_group(self.group_requester))
        self.assertTrue(self.user_manager.has_group(self.group_viewer))
        self.assertFalse(self.user_requester.has_group(self.group_manager))
