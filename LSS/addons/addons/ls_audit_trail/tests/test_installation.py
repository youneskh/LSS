# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Installation tests: the module registers what it declares."""

from odoo.tests import tagged

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestInstallation(AuditTrailCase):
    """Verify that installing the module produces a usable registry."""

    def test_module_is_installed(self):
        """The module is reported as installed."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_audit_trail")]
        )
        self.assertEqual(len(module), 1)
        self.assertEqual(module.state, "installed")

    def test_models_are_registered(self):
        """Every model declared by the module is present in the registry."""
        for model_name in (
            "ls.audit_trail.rule",
            "ls.audit_trail.log",
            "ls.audit_trail.log.line",
            "ls.audit_trail.verification",
            "ls.audit_trail.evidence_pack",
            "ls.audit_trail.verify.wizard",
            "ls.audit_trail.purge.wizard",
        ):
            with self.subTest(model=model_name):
                self.assertIn(model_name, self.env)

    def test_groups_are_created(self):
        """The three audit groups exist and imply one another."""
        viewer = self.env.ref("ls_audit_trail.group_ls_audit_trail_viewer")
        auditor = self.env.ref("ls_audit_trail.group_ls_audit_trail_auditor")
        admin = self.env.ref("ls_audit_trail.group_ls_audit_trail_admin")
        self.assertIn(viewer, auditor.implied_ids)
        self.assertIn(auditor, admin.implied_ids)

    def test_scheduled_action_exists(self):
        """The integrity verification scheduled action is installed."""
        cron = self.env.ref("ls_audit_trail.cron_verify_chain")
        self.assertEqual(cron.state, "code")
        self.assertEqual(cron.model_id.model, "ls.audit_trail.log")

    def test_sequence_exists(self):
        """The evidence pack sequence is installed."""
        sequence = self.env["ir.sequence"].search(
            [("code", "=", "ls.audit_trail.evidence_pack")]
        )
        self.assertTrue(sequence)

    def test_no_rule_means_no_capture(self):
        """With no audit rule configured, no entry is ever written."""
        before = self.log_model.sudo().search_count([])
        partner = self.env["res.partner"].create({"name": "Unaudited"})
        partner.write({"name": "Unaudited renamed"})
        partner.unlink()
        self.assertEqual(self.log_model.sudo().search_count([]), before)

    def test_report_actions_exist(self):
        """Both PDF report actions are installed and bound to their model."""
        pack_report = self.env.ref(
            "ls_audit_trail.action_report_ls_audit_trail_evidence_pack"
        )
        self.assertEqual(pack_report.model, "ls.audit_trail.evidence_pack")
        verification_report = self.env.ref(
            "ls_audit_trail.action_report_ls_audit_trail_verification"
        )
        self.assertEqual(verification_report.model, "ls.audit_trail.verification")
