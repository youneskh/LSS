# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Installation and upgrade assertions."""

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "ls_signature")
class TestInstallation(TransactionCase):
    """The module must install completely and leave no gap in its controls."""

    def test_module_is_installed(self):
        """The module reports itself installed."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_electronic_signature")], limit=1
        )
        self.assertTrue(module)
        self.assertEqual(module.state, "installed")

    def test_every_model_is_present(self):
        """All declared models exist in the registry."""
        for model_name in (
            "ls.signature.meaning",
            "ls.signature.policy",
            "ls.signature.log",
            "ls.signature.attempt",
            "ls.signature.session",
            "ls.signature.request",
            "ls.signature.integrity.check",
            "ls.signature.mixin",
            "ls.signature.wizard",
            "ls.signature.decline.wizard",
        ):
            self.assertIn(model_name, self.env, model_name)

    def test_no_group_holds_write_or_unlink_on_the_log(self):
        """No access right permits altering or deleting a signature."""
        accesses = self.env["ir.model.access"].search(
            [("model_id.model", "=", "ls.signature.log")]
        )
        self.assertTrue(accesses)
        for access in accesses:
            self.assertFalse(access.perm_write, access.name)
            self.assertFalse(access.perm_unlink, access.name)

    def test_no_group_holds_write_or_unlink_on_attempts(self):
        """No access right permits altering or deleting the security log."""
        accesses = self.env["ir.model.access"].search(
            [("model_id.model", "=", "ls.signature.attempt")]
        )
        self.assertTrue(accesses)
        for access in accesses:
            self.assertFalse(access.perm_write, access.name)
            self.assertFalse(access.perm_unlink, access.name)

    def test_scheduled_actions_are_active(self):
        """The three scheduled actions are installed and enabled."""
        for external_id in (
            "ls_electronic_signature.cron_verify_signature_chain",
            "ls_electronic_signature.cron_close_idle_sessions",
            "ls_electronic_signature.cron_expire_signature_requests",
        ):
            cron = self.env.ref(external_id)
            self.assertTrue(cron.active, external_id)

    def test_database_immutability_trigger_state_is_recorded(self):
        """Installation records whether the database trigger is active."""
        state = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.db_immutability_trigger")
        )
        self.assertIn(state, ("installed", "absent"))

    def test_immutability_trigger_is_present_in_postgresql(self):
        """The trigger exists on the signature log table.

        Skipped when installation reported that the trigger could not be
        created, so that a database role without trigger privileges does not
        produce a misleading failure.
        """
        state = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.db_immutability_trigger")
        )
        if state != "installed":
            self.skipTest("Database immutability trigger was not installed.")
        self.env.cr.execute(
            """
            SELECT COUNT(*) FROM pg_trigger
             WHERE tgrelid = 'ls_signature_log'::regclass
               AND NOT tgisinternal
            """
        )
        self.assertGreaterEqual(self.env.cr.fetchone()[0], 1)

    def test_mail_templates_are_present(self):
        """The three notification templates are installed."""
        for external_id in (
            "ls_electronic_signature.mail_template_signature_request",
            "ls_electronic_signature.mail_template_signature_alert",
            "ls_electronic_signature.mail_template_integrity_failure",
        ):
            self.assertTrue(self.env.ref(external_id), external_id)
