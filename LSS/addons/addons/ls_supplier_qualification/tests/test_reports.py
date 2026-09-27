# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests that the QWeb report templates render without error."""
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestReports(SupplierQualificationCommon):
    """Render each report to HTML and check its key content."""

    def setUp(self):
        """Build a dossier carrying every kind of evidence."""
        super().setUp()
        self.qualification.action_start_assessment()
        self.assessment = self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.audit = self._create_closed_audit(self.qualification)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)

    def _render(self, report_xml_id, records):
        """Render a report to HTML and return the decoded document."""
        report = self.env["ir.actions.report"]._render_qweb_html(
            report_xml_id, records.ids
        )[0]
        return report.decode("utf-8") if isinstance(report, bytes) else report

    def test_qualification_dossier_renders(self):
        """The dossier report renders and contains the supplier name."""
        html = self._render(
            "ls_supplier_qualification.report_ls_supplier_qualification",
            self.qualification,
        )
        self.assertIn(self.partner.name, html)
        self.assertIn(self.qualification.name, html)

    def test_assessment_report_renders(self):
        """The assessment report renders and contains the criteria."""
        html = self._render(
            "ls_supplier_qualification.report_ls_supplier_assessment",
            self.assessment,
        )
        self.assertIn(self.criterion_mandatory.code, html)

    def test_audit_report_renders(self):
        """The audit report renders and contains the finding reference."""
        html = self._render(
            "ls_supplier_qualification.report_ls_supplier_audit",
            self.audit,
        )
        self.assertIn("F-01", html)

    def test_report_filenames(self):
        """Each printable record proposes a readable file name."""
        self.assertIn(
            self.partner.name, self.qualification._get_report_base_filename()
        )
        self.assertIn(
            self.partner.name, self.assessment._get_report_base_filename()
        )
        self.assertIn(
            self.partner.name, self.audit._get_report_base_filename()
        )
