# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for access rights and role separation."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestSecurity(RecallCommon):
    """Each role holds exactly the rights its duties require."""

    def test_viewer_can_read(self):
        """A viewer reads recalls."""
        execution = self._create_execution()
        record = execution.with_user(self.user_viewer)
        record.read(["name", "state"])
        self.assertEqual(record.name, execution.name)

    def test_viewer_cannot_write(self):
        """A viewer cannot change a recall."""
        execution = self._create_execution()
        with self.assertRaises(AccessError):
            execution.with_user(self.user_viewer).write({"reason": "x"})

    def test_viewer_cannot_create(self):
        """A viewer cannot open a recall."""
        with self.assertRaises(AccessError):
            self.env["ls.recall.execution"].with_user(
                self.user_viewer
            ).create(
                {
                    "product_id": self.product.id,
                    "responsible_user_id": self.user_viewer.id,
                }
            )

    def test_coordinator_can_create_and_write(self):
        """A coordinator conducts recalls."""
        execution = (
            self.env["ls.recall.execution"]
            .with_user(self.user_coordinator)
            .create(
                {
                    "product_id": self.product.id,
                    "lot_ids": [(6, 0, self.lot_1.ids)],
                    "reason": "Defect found.",
                    "responsible_user_id": self.user_coordinator.id,
                }
            )
        )
        self.assertTrue(execution.name)

    def test_coordinator_cannot_delete(self):
        """A coordinator cannot remove a recall."""
        execution = self._create_execution()
        with self.assertRaises(AccessError):
            execution.with_user(self.user_coordinator).unlink()

    def test_coordinator_cannot_create_a_plan(self):
        """Plans belong to the manager role."""
        with self.assertRaises(AccessError):
            self.env["ls.recall.plan"].with_user(
                self.user_coordinator
            ).create(
                {
                    "name": "Unauthorised plan",
                    "responsible_user_id": self.user_coordinator.id,
                }
            )

    def test_coordinator_cannot_approve_a_plan(self):
        """Approving a plan is a write and is refused."""
        self.plan.action_submit_review()
        with self.assertRaises(AccessError):
            self.plan.with_user(self.user_coordinator).action_approve()

    def test_manager_holds_coordinator_rights(self):
        """The manager role implies the coordinator role."""
        self.assertTrue(
            self.user_manager.has_group(
                "ls_recall.group_ls_recall_coordinator"
            )
        )
        self.assertTrue(
            self.user_manager.has_group("ls_recall.group_ls_recall_viewer")
        )

    def test_coordinator_holds_viewer_rights(self):
        """The coordinator role implies the viewer role."""
        self.assertTrue(
            self.user_coordinator.has_group(
                "ls_recall.group_ls_recall_viewer"
            )
        )
        self.assertFalse(
            self.user_coordinator.has_group(
                "ls_recall.group_ls_recall_manager"
            )
        )

    def test_user_without_role_has_no_access(self):
        """A plain internal user sees no recall data."""
        plain_user = self._create_user_without_role("plain_user")
        execution = self._create_execution()
        with self.assertRaises(AccessError):
            execution.with_user(plain_user).read(["name"])

    def test_lot_indicator_readable_without_a_recall_role(self):
        """The under-recall warning is visible to warehouse staff.

        The indicator is computed through sudo precisely so that a user
        who cannot open the recall is still warned not to ship the lot.
        """
        plain_user = self._create_user_without_role("warehouse_user")
        execution = self._create_execution()
        execution.action_initiate()
        lot = self.lot_1.with_user(plain_user)
        lot.invalidate_recordset()
        self.assertTrue(lot.ls_recall_open)

    def _create_user_without_role(self, login):
        """Create an internal user holding no recall group."""
        user_model = self.env["res.users"].with_context(
            no_reset_password=True
        )
        field_name = (
            "group_ids" if "group_ids" in user_model._fields else "groups_id"
        )
        return user_model.create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.com",
                field_name: [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )

    def test_closure_override_is_manager_only(self):
        """Only a manager may close a recall whose checks failed."""
        execution = self._advance_to_effectiveness(self._create_execution())
        wizard = (
            self.env["ls.recall.close.wizard"]
            .with_user(self.user_coordinator)
            .create(
                {
                    "execution_id": execution.id,
                    "justification": "Attempted override.",
                    "override_gates": True,
                }
            )
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()
