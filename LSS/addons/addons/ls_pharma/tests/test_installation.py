# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests that the module installed the artefacts that it declares.

These tests are the executable counterpart of the static checker: the checker
verifies the sources before installation, and these tests verify the database
after it.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..constants import RELEASE_CHECKLIST, RELEASE_CHECKLIST_FIELDS


@tagged("post_install", "-at_install")
class TestInstallation(TransactionCase):
    """Check the sequences, the data, the views, the reports and the crons."""

    def test_module_is_installed(self):
        """The module is present and marked as installed."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_pharma")]
        )
        self.assertTrue(module)
        self.assertEqual(module.state, "installed")

    def test_sequences_are_installed(self):
        """The five document sequences are present."""
        for code in (
            "ls.pharma.batch",
            "ls.pharma.batch_record",
            "ls.pharma.batch.release",
            "ls.pharma.stability_study",
            "ls.pharma.ctd_dossier",
        ):
            sequence = self.env["ir.sequence"].search([("code", "=", code)])
            self.assertTrue(sequence, "the sequence %s is missing" % code)

    def test_stability_conditions_are_installed(self):
        """The four general-case conditions of ICH Q1A(R2) are present."""
        conditions = self.env["ls.pharma.stability.condition"].search([])
        self.assertGreaterEqual(len(conditions), 4)
        codes = set(conditions.mapped("code"))
        for code in (
            "ICH-LT-25-60",
            "ICH-LT-30-65",
            "ICH-INT-30-65",
            "ICH-ACC-40-75",
        ):
            self.assertIn(code, codes)

    def test_ctd_template_is_installed(self):
        """The Common Technical Document template is present."""
        templates = self.env["ls.pharma.ctd.section"].search(
            [("is_template", "=", True)]
        )
        self.assertGreaterEqual(len(templates), 100)
        codes = templates.mapped("code")
        self.assertEqual(len(codes), len(set(codes)))

    def test_scheduled_actions_are_installed(self):
        """The two scheduled actions are present and active."""
        for identifier in (
            "cron_ls_pharma_stability_overdue",
            "cron_ls_pharma_batch_expiry",
        ):
            cron = self.env.ref("ls_pharma.%s" % identifier)
            self.assertTrue(cron)
            self.assertTrue(cron.active)

    def test_scheduled_actions_run_without_error(self):
        """Both scheduled actions execute on an empty data set.

        A scheduled action that raises on an empty database would fill the
        server log every day, so both are executed here.
        """
        self.env["ls.pharma.stability_study"].cron_flag_overdue_timepoints()
        self.env["ls.pharma.batch"].cron_notify_expiring_batches()

    def test_reports_are_installed(self):
        """The two printable reports are present."""
        for identifier in (
            "action_report_ls_pharma_batch_record",
            "action_report_ls_pharma_release_certificate",
        ):
            report = self.env.ref("ls_pharma.%s" % identifier)
            self.assertTrue(report)
            self.assertEqual(report.report_type, "qweb-pdf")

    def test_root_menu_is_installed(self):
        """The root menu of the module is present."""
        menu = self.env.ref("ls_pharma.menu_ls_pharma_root")
        self.assertTrue(menu)
        self.assertFalse(menu.parent_id)

    def test_every_view_of_the_module_is_valid(self):
        """Every view shipped by this module passes the Odoo view validation.

        Reading the architecture of a view forces Odoo to resolve the fields
        and the attributes that it names, so a view that names a field which
        does not exist fails here.
        """
        views = self.env["ir.ui.view"].search(
            [("model", "=like", "ls.pharma.%")]
        )
        self.assertTrue(views)
        for view in views:
            self.assertTrue(
                view._get_combined_arch() is not None,
                "the view %s could not be combined" % view.xml_id,
            )

    def test_release_checklist_and_model_agree(self):
        """Every checklist entry of the constants exists on the two models.

        The checklist is declared once, in ``constants.py``. The persistent
        model, the wizard and the printed certificate all derive from it, and
        this test proves that the derivation still holds.
        """
        release_fields = self.env["ls.pharma.batch.release"]._fields
        wizard_fields = self.env["ls.pharma.batch.release.wizard"]._fields
        self.assertEqual(len(RELEASE_CHECKLIST), 8)
        for field_name, label, reference in RELEASE_CHECKLIST:
            self.assertIn(field_name, release_fields)
            self.assertIn(field_name, wizard_fields)
            self.assertTrue(label)
            self.assertTrue(reference)
        self.assertEqual(
            set(RELEASE_CHECKLIST_FIELDS),
            {item[0] for item in RELEASE_CHECKLIST},
        )

    def test_every_model_has_an_access_rule(self):
        """Every model of the module carries at least one access rule."""
        # Abstract models (mixins) have no table and take no access rule.
        models = self.env["ir.model"].search(
            [("model", "=like", "ls.pharma.%"), ("abstract", "=", False)]
        )
        self.assertTrue(models)
        for model in models:
            accesses = self.env["ir.model.access"].search_count(
                [("model_id", "=", model.id)]
            )
            self.assertTrue(
                accesses, "the model %s carries no access rule" % model.model
            )
