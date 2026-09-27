# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation tests: every declared artefact must exist after install."""

from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestInstall(ChangeControlCommon):
    """Verify that the module installed all of its artefacts."""

    def test_module_is_installed(self):
        """The module is present in the registry with the installed state."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_change_control")], limit=1
        )
        self.assertTrue(module, "The module record must exist.")
        self.assertEqual(module.state, "installed")

    def test_all_models_are_registered(self):
        """Every model declared by the module is present in the registry."""
        expected = [
            "ls.change_control.request",
            "ls.change_control.assessment",
            "ls.change_control.approval",
            "ls.change_control.implementation",
            "ls.change_control.verification",
            "ls.change_control.category",
            "ls.change_control.impact_area",
            "ls.change_control.approval_template",
            "ls.change_control.decision_wizard",
        ]
        for model_name in expected:
            self.assertIn(model_name, self.env, "Missing model %s" % model_name)

    def test_security_groups_exist(self):
        """The four security groups of the specification exist."""
        for xmlid in (
            self.group_viewer,
            self.group_requester,
            self.group_approver,
            self.group_manager,
        ):
            self.assertTrue(self.env.ref(xmlid), "Missing group %s" % xmlid)

    def test_group_hierarchy(self):
        """Each group implies the previous one, from viewer to manager."""
        viewer = self.env.ref(self.group_viewer)
        requester = self.env.ref(self.group_requester)
        approver = self.env.ref(self.group_approver)
        manager = self.env.ref(self.group_manager)
        self.assertIn(viewer, requester.implied_ids)
        self.assertIn(requester, approver.implied_ids)
        self.assertIn(approver, manager.implied_ids)

    def test_sequence_exists(self):
        """The change request sequence is installed and usable."""
        sequence = self.env.ref("ls_change_control.seq_ls_change_control_request")
        self.assertEqual(sequence.code, "ls.change_control.request")
        self.assertFalse(sequence.company_id)

    def test_scheduled_actions_exist(self):
        """The three scheduled actions are installed and active."""
        for xmlid in (
            "ls_change_control.cron_ls_cc_remind_pending_approvals",
            "ls_change_control.cron_ls_cc_remind_overdue_implementations",
            "ls_change_control.cron_ls_cc_remind_due_verifications",
        ):
            cron = self.env.ref(xmlid)
            self.assertTrue(cron.active, "Cron %s must be active." % xmlid)
            self.assertEqual(cron.interval_type, "days")

    def test_mail_templates_exist(self):
        """The three mail templates are installed on the right models."""
        expected = {
            "ls_change_control.mail_template_approval_requested":
                "ls.change_control.approval",
            "ls_change_control.mail_template_change_approved":
                "ls.change_control.request",
            "ls_change_control.mail_template_change_rejected":
                "ls.change_control.request",
        }
        for xmlid, model_name in expected.items():
            template = self.env.ref(xmlid)
            self.assertEqual(template.model_id.model, model_name)

    def test_seed_configuration_is_loaded(self):
        """The seed impact areas and categories are loaded."""
        areas = self.env["ls.change_control.impact_area"].search([])
        self.assertGreaterEqual(len(areas), 14)
        categories = self.env["ls.change_control.category"].search(
            [("code", "!=", "TESTCAT")]
        )
        self.assertGreaterEqual(len(categories), 10)

    def test_seed_categories_have_approval_templates(self):
        """Every seed category defines at least one approval role."""
        categories = self.env["ls.change_control.category"].search(
            [("code", "!=", "TESTCAT")]
        )
        for category in categories:
            self.assertTrue(
                category.approval_template_ids,
                "Category %s has no approval template." % category.code,
            )

    def test_menus_exist(self):
        """The root menu and the configuration menus are installed."""
        for xmlid in (
            "ls_change_control.menu_ls_change_control_root",
            "ls_change_control.menu_ls_change_control_request_all",
            "ls_change_control.menu_ls_change_control_config_category",
            "ls_change_control.menu_ls_change_control_config_settings",
        ):
            self.assertTrue(self.env.ref(xmlid), "Missing menu %s" % xmlid)

    def test_company_configuration_defaults(self):
        """The company configuration fields carry their documented defaults."""
        company = self.env["res.company"].create({"name": "Default Check"})
        self.assertEqual(company.ls_cc_approval_reminder_days, 3)
        self.assertEqual(company.ls_cc_default_verification_delay, 30)
        self.assertTrue(company.ls_cc_require_verification)
        self.assertTrue(company.ls_cc_block_close_on_open_actions)
