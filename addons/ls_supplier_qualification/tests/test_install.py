# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation-level checks: data, sequences, crons, reports and views."""
from odoo.tests import tagged

from .common import SupplierQualificationCommon

MODEL_NAMES = [
    "ls.supplier.standard",
    "ls.supplier.category",
    "ls.supplier.criterion",
    "ls.supplier.assessment.template",
    "ls.supplier.assessment.template.line",
    "ls.supplier.qualification",
    "ls.supplier.material",
    "ls.supplier.assessment",
    "ls.supplier.assessment.line",
    "ls.supplier.audit",
    "ls.supplier.audit.finding",
    "ls.supplier.performance",
    "ls.supplier.review",
    "ls.supplier.signature",
    "ls.supplier.approve.wizard",
    "ls.supplier.status.wizard",
]

SEQUENCE_CODES = [
    "ls.supplier.qualification",
    "ls.supplier.assessment",
    "ls.supplier.audit",
    "ls.supplier.performance",
    "ls.supplier.review",
]

CRON_XML_IDS = [
    "ls_supplier_qualification.cron_ls_supplier_qualification_expiry",
    "ls_supplier_qualification.cron_ls_supplier_due_dates",
    "ls_supplier_qualification.cron_ls_supplier_material_expiry",
]

REPORT_XML_IDS = [
    "ls_supplier_qualification.action_report_ls_supplier_qualification",
    "ls_supplier_qualification.action_report_ls_supplier_assessment",
    "ls_supplier_qualification.action_report_ls_supplier_audit",
]


@tagged("post_install", "-at_install")
class TestInstall(SupplierQualificationCommon):
    """Verify that the module data set is complete after installation."""

    def test_models_registered(self):
        """Every model declared by the module is present in the registry."""
        for model_name in MODEL_NAMES:
            self.assertIn(
                model_name, self.env, "Model %s is missing" % model_name
            )

    def test_models_have_description(self):
        """Every model of the module declares a description."""
        for model_name in MODEL_NAMES:
            self.assertTrue(
                self.env[model_name]._description,
                "Model %s has no description" % model_name,
            )

    def test_sequences_present(self):
        """Every sequence code used by the code exists and produces a value."""
        for code in SEQUENCE_CODES:
            sequence = self.env["ir.sequence"].search([("code", "=", code)])
            self.assertTrue(sequence, "Sequence %s is missing" % code)

    def test_crons_present_and_callable(self):
        """The scheduled actions exist and their method runs without error."""
        for xml_id in CRON_XML_IDS:
            cron = self.env.ref(xml_id)
            self.assertTrue(cron.active, "Cron %s is inactive" % xml_id)
        self.env["ls.supplier.qualification"]._cron_check_expiry()
        self.env["ls.supplier.qualification"]._cron_check_due_dates()
        self.env["ls.supplier.material"]._cron_check_material_expiry()

    def test_reports_present(self):
        """The three PDF report actions are registered."""
        for xml_id in REPORT_XML_IDS:
            report = self.env.ref(xml_id)
            self.assertEqual(report.report_type, "qweb-pdf")

    def test_starter_configuration_loaded(self):
        """The starter categories, criteria and templates are loaded."""
        self.assertTrue(
            self.env.ref("ls_supplier_qualification.category_api_manufacturer")
        )
        self.assertTrue(
            self.env.ref("ls_supplier_qualification.criterion_qms_certified")
        )
        template = self.env.ref(
            "ls_supplier_qualification.assessment_template_full"
        )
        self.assertTrue(template.line_ids)

    def test_groups_hierarchy(self):
        """The manager group implies the assessor and viewer groups."""
        viewer = self.env.ref(
            "ls_supplier_qualification.group_ls_supplier_viewer"
        )
        assessor = self.env.ref(
            "ls_supplier_qualification.group_ls_supplier_assessor"
        )
        manager = self.env.ref(
            "ls_supplier_qualification.group_ls_supplier_manager"
        )
        self.assertIn(viewer, assessor.implied_ids)
        self.assertIn(assessor, manager.implied_ids)
