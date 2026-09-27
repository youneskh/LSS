# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation-level tests.

These tests assert that the artefacts the module ships were actually loaded:
the configuration records, the sequences, the scheduled actions created by the
post-installation hook, the security groups and the report actions. They are
the checks that would otherwise only be confirmed by opening the database by
hand after an installation.
"""

from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestInstallation(MedicalDeviceCommon):
    """Artefacts created when the module is installed."""

    def test_device_classes_loaded(self):
        """The seven shipped risk classes are present."""
        classes = self.env["ls.md.device_class"].search([])
        codes = set(classes.mapped("code"))
        for expected in ("I", "Is", "Im", "Ir", "IIa", "IIb", "III"):
            self.assertIn(expected, codes)

    def test_class_report_intervals_match_regulation(self):
        """The shipped intervals match Articles 85 and 86.

        Class I devices prepare a post-market surveillance report under
        Article 85, which the Regulation does not tie to a fixed interval.
        Class IIa is updated at least every two years and classes IIb and III
        at least annually, under Article 86(1).
        """
        self.assertEqual(self.class_i.periodic_report_type, "pmsr")
        self.assertEqual(self.class_iia.periodic_report_type, "psur")
        self.assertEqual(self.class_iia.periodic_report_interval_months, 24)
        self.assertEqual(self.class_iib.periodic_report_interval_months, 12)
        self.assertEqual(self.class_iii.periodic_report_interval_months, 12)

    def test_only_class_iii_requires_annual_pmcf_update(self):
        """Article 61(11) drives the annual PMCF update flag."""
        self.assertTrue(self.class_iii.annual_pmcf_update_required)
        self.assertFalse(self.class_iia.annual_pmcf_update_required)
        self.assertFalse(self.class_i.annual_pmcf_update_required)

    def test_clinical_evidence_sources_loaded(self):
        """The shipped clinical evidence sources are present."""
        sources = self.env["ls.md.clinical_evidence_source"].search([])
        self.assertGreaterEqual(len(sources), 5)

    def test_section_templates_loaded(self):
        """The technical documentation section templates are present."""
        templates = self.env["ls.md.technical_file_section_template"].search(
            [("annex_reference", "=", "annex_ii")]
        )
        self.assertTrue(templates)

    def test_sequences_loaded(self):
        """Every model that allocates a reference has its sequence."""
        codes = (
            "ls.md.device",
            "ls.md.udi",
            "ls.md.risk_assessment",
            "ls.md.clinical_evaluation",
            "ls.md.pmcf_evaluation",
            "ls.md.technical_file",
            "ls.md.ce_marking",
            "ls.md.pms",
            "ls.md.pms_report",
        )
        for code in codes:
            sequence = self.env["ir.sequence"].search(
                [("code", "=", code)], limit=1
            )
            self.assertTrue(sequence, f"sequence missing for {code}")

    def test_security_groups_loaded(self):
        """The four access levels are present."""
        for identifier in (
            "ls_medical_device.group_ls_md_viewer",
            "ls_medical_device.group_ls_md_user",
            "ls_medical_device.group_ls_md_regulatory",
            "ls_medical_device.group_ls_md_manager",
        ):
            self.assertTrue(self.env.ref(identifier))

    def test_scheduled_actions_created_by_hook(self):
        """The post-installation hook created both scheduled actions."""
        for identifier in (
            "ls_medical_device.cron_check_post_market_obligations",
            "ls_medical_device.cron_expire_certificates",
        ):
            cron = self.env.ref(identifier, raise_if_not_found=False)
            self.assertTrue(cron, f"scheduled action missing: {identifier}")

    def test_report_actions_loaded(self):
        """The three report actions are present."""
        for identifier in (
            "ls_medical_device.action_report_ls_md_device_regulatory_summary",
            "ls_medical_device.action_report_ls_md_risk_management",
            "ls_medical_device.action_report_ls_md_pms_periodic",
        ):
            self.assertTrue(self.env.ref(identifier))

    def test_root_menu_loaded(self):
        """The application root menu is present."""
        self.assertTrue(self.env.ref("ls_medical_device.menu_ls_md_root"))

    def test_every_model_is_registered(self):
        """Each model declared by the module is present in the registry."""
        model_names = (
            "ls.md.device",
            "ls.md.device_class",
            "ls.md.notified_body",
            "ls.md.udi",
            "ls.md.risk_assessment",
            "ls.md.risk_item",
            "ls.md.clinical_evaluation",
            "ls.md.clinical_evidence_source",
            "ls.md.pmcf_evaluation",
            "ls.md.technical_file",
            "ls.md.technical_file_section",
            "ls.md.technical_file_section_template",
            "ls.md.ce_marking",
            "ls.md.pms",
            "ls.md.pms_report",
        )
        for model_name in model_names:
            self.assertIn(model_name, self.env, f"model missing: {model_name}")
