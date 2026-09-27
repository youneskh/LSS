# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation and upgrade safety tests.

These tests assert the structural properties that make the module installable
and upgradeable: the manifest is coherent, every declared model is registered,
every master data record referenced by the code exists, and the menu tree is
reachable.
"""

from odoo.tests import tagged

from .common import AuditCommon

#: Every model contributed by this module.
MODULE_MODELS = [
    "ls.audit.type",
    "ls.audit.area",
    "ls.audit.auditor",
    "ls.audit.finding.category",
    "ls.audit.checklist",
    "ls.audit.checklist.line",
    "ls.audit.program",
    "ls.audit.schedule",
    "ls.audit.response",
    "ls.audit.finding",
    "ls.audit.report",
    "ls.audit.checklist.load",
    "ls.audit.finding.response",
    "ls.audit.cancel",
]

#: External identifiers the Python code resolves at runtime.
RUNTIME_XMLIDS = [
    "ls_audit.mail_template_finding_issued",
    "ls_audit.mail_template_finding_overdue",
    "ls_audit.mail_template_audit_report_issued",
    "ls_audit.mail_template_auditor_qualification_expiry",
    "ls_audit.seq_ls_audit_program",
    "ls_audit.seq_ls_audit_schedule",
    "ls_audit.seq_ls_audit_finding",
    "ls_audit.seq_ls_audit_report",
]


@tagged("post_install", "-at_install")
class TestInstallation(AuditCommon):
    """Structural checks on the installed module."""

    def test_module_is_installed(self):
        """The module is present and installed."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_audit")], limit=1
        )
        self.assertTrue(module)
        self.assertEqual(module.state, "installed")

    def test_every_model_is_registered(self):
        """Every model declared by the module exists in the registry."""
        for model_name in MODULE_MODELS:
            with self.subTest(model=model_name):
                self.assertIn(model_name, self.env)

    def test_runtime_xmlids_resolve(self):
        """Every external identifier used by the code resolves."""
        for xmlid in RUNTIME_XMLIDS:
            with self.subTest(xmlid=xmlid):
                self.assertTrue(
                    self.env.ref(xmlid, raise_if_not_found=False),
                    "Missing external identifier %s" % xmlid,
                )

    def test_sequences_produce_prefixed_numbers(self):
        """Each sequence produces a number with its documented prefix."""
        expected = {
            "ls.audit.program": "APG/",
            "ls.audit.schedule": "AUD/",
            "ls.audit.finding": "FND/",
            "ls.audit.report": "ARP/",
        }
        for code, prefix in expected.items():
            with self.subTest(sequence=code):
                value = self.env["ir.sequence"].next_by_code(code)
                self.assertTrue(value.startswith(prefix))

    def test_menu_root_is_reachable(self):
        """The root menu exists and is restricted to the audit groups."""
        menu = self.env.ref("ls_audit.menu_ls_quality_root")
        self.assertTrue(menu)
        self.assertIn(self.group_auditee, menu.group_ids)

    def test_all_actions_point_to_existing_models(self):
        """Every window action of the module targets a real model."""
        actions = self.env["ir.actions.act_window"].search(
            [("res_model", "like", "ls.audit")]
        )
        self.assertTrue(actions)
        for action in actions:
            with self.subTest(action=action.name):
                self.assertIn(action.res_model, self.env)

    def test_no_view_uses_the_legacy_tree_tag(self):
        """No view of this module uses the pre-Odoo-17 tree root tag.

        Odoo 19 renamed the list view root element from tree to list. A
        leftover tree tag would silently degrade or fail to load.
        """
        views = self.env["ir.ui.view"].search(
            [("model", "like", "ls.audit")]
        )
        self.assertTrue(views)
        for view in views:
            with self.subTest(view=view.name):
                self.assertNotIn("<tree", view.arch_db or "")

    def test_group_hierarchy_reaches_base_user(self):
        """The lowest audit group implies the internal user group."""
        base_user = self.env.ref("base.group_user")
        self.assertIn(base_user, self.group_auditee.implied_ids)
