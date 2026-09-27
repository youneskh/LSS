# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Access right and record rule tests for the CAPA module."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaSecurity(CapaCommon):
    """Verify that each group holds the intended permissions."""

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_capa(self):
        """A viewer has read-only access to CAPA records."""
        with self.assertRaises(AccessError):
            self.env["ls.capa.issue"].with_user(self.user_viewer).create(
                {
                    "title": "Blocked",
                    "description": "Should not be created.",
                    "source": "deviation",
                    "capa_type": "corrective",
                    "severity": "minor",
                }
            )

    def test_viewer_can_read_capa(self):
        """A viewer can read existing CAPA records."""
        issue = self._make_issue()
        self.assertEqual(
            issue.with_user(self.user_viewer).title, issue.title
        )

    def test_investigator_can_create_capa(self):
        """An investigator can raise a CAPA."""
        issue = self.env["ls.capa.issue"].with_user(
            self.user_investigator
        ).create(
            {
                "title": "Investigator CAPA",
                "description": "Raised during an investigation.",
                "source": "deviation",
                "capa_type": "corrective",
                "severity": "minor",
            }
        )
        self.assertTrue(issue.name.startswith("CAPA/"))

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_investigator_cannot_create_action(self):
        """Action planning is reserved to coordinators and above."""
        issue = self._make_issue()
        with self.assertRaises(AccessError):
            self.env["ls.capa.action"].with_user(
                self.user_investigator
            ).create(
                {
                    "issue_id": issue.id,
                    "action_type": "corrective",
                    "description": "Blocked.",
                    "responsible_id": self.user_investigator.id,
                    "date_planned": self.today,
                }
            )

    def test_coordinator_can_create_action(self):
        """A coordinator can plan actions."""
        issue = self._make_issue()
        action = self.env["ls.capa.action"].with_user(
            self.user_coordinator
        ).create(
            {
                "issue_id": issue.id,
                "action_type": "corrective",
                "description": "Allowed.",
                "responsible_id": self.user_coordinator.id,
                "date_planned": self.today,
            }
        )
        self.assertTrue(action.name.startswith("CAPA-ACT/"))

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_coordinator_cannot_delete_capa(self):
        """Deletion is reserved to CAPA managers."""
        issue = self._make_issue()
        with self.assertRaises(AccessError):
            issue.with_user(self.user_coordinator).unlink()

    def test_manager_can_delete_capa(self):
        """A manager can delete a CAPA still in Identified."""
        issue = self._make_issue()
        issue.with_user(self.user_manager).unlink()
        self.assertFalse(issue.exists())

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_manage_categories(self):
        """Configuration is reserved to CAPA managers."""
        with self.assertRaises(AccessError):
            self.env["ls.capa.category"].with_user(self.user_viewer).create(
                {"name": "Blocked", "code": "BLK"}
            )

    def test_group_implication_chain(self):
        """Each group implies the permissions of the group below it."""
        self.assertIn(self.group_viewer, self.group_investigator.implied_ids)
        self.assertIn(
            self.group_investigator, self.group_coordinator.implied_ids
        )
        self.assertIn(self.group_coordinator, self.group_manager.implied_ids)

    def test_multi_company_rule_hides_other_company_records(self):
        """The record rule hides CAPA records of another company."""
        other_company = self.env["res.company"].create({"name": "Other Co"})
        foreign = self._make_issue(company_id=other_company.id)
        visible = self.env["ls.capa.issue"].with_user(
            self.user_manager
        ).search([("id", "=", foreign.id)])
        self.assertFalse(visible)
