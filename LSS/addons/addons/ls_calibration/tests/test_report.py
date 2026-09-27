# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the QWeb reports of the calibration module."""

from odoo.tests import tagged

from .common import LsCalibrationCommon

RECORD_REPORT = "ls_calibration.report_ls_calibration_record"
CERTIFICATE_REPORT = "ls_calibration.report_ls_calibration_certificate"


@tagged("post_install", "-at_install")
class TestLsCalibrationReport(LsCalibrationCommon):
    """Rendering of the calibration record and certificate reports."""

    @classmethod
    def setUpClass(cls):
        """Approve one calibration record and issue its certificate."""
        super().setUpClass()
        cls.record = cls._create_record()
        cls._fill_readings(cls.record)
        cls.record.action_start()
        cls.record.action_submit_review()
        cls.record.with_user(cls.user_manager).action_approve()
        cls.certificate = cls.env["ls.calibration.certificate"].create(
            {
                "instrument_id": cls.instrument.id,
                "record_id": cls.record.id,
                "issuer_type": "internal",
            }
        )
        cls.certificate.action_issue()

    def test_record_report_renders(self):
        """The calibration record report contains its main data."""
        content, content_type = self.env["ir.actions.report"]._render_qweb_html(
            RECORD_REPORT, self.record.ids
        )
        html = content.decode() if isinstance(content, bytes) else content
        self.assertEqual(content_type, "html")
        self.assertIn(self.record.name, html)
        self.assertIn(self.instrument.name, html)
        for line in self.record.line_ids:
            self.assertIn(line.name, html)

    def test_record_report_shows_out_of_tolerance_block(self):
        """The out-of-tolerance section appears only when relevant."""
        record = self._create_record()
        self._fill_readings(record, as_found=[10.5, 100.0], as_left=[10.0, 100.0])
        record.write({"oot_impact_assessment": "No batch impacted."})
        content, _ = self.env["ir.actions.report"]._render_qweb_html(
            RECORD_REPORT, record.ids
        )
        html = content.decode() if isinstance(content, bytes) else content
        self.assertIn("Out-of-tolerance handling", html)
        self.assertIn("No batch impacted.", html)

    def test_certificate_report_renders(self):
        """The certificate report contains the instrument and the readings."""
        content, content_type = self.env["ir.actions.report"]._render_qweb_html(
            CERTIFICATE_REPORT, self.certificate.ids
        )
        html = content.decode() if isinstance(content, bytes) else content
        self.assertEqual(content_type, "html")
        self.assertIn(self.certificate.name, html)
        self.assertIn(self.instrument.name, html)

    def test_report_actions_are_installed(self):
        """Both report actions are created and bound to their model."""
        record_report = self.env.ref(
            "ls_calibration.action_report_ls_calibration_record"
        )
        certificate_report = self.env.ref(
            "ls_calibration.action_report_ls_calibration_certificate"
        )
        self.assertEqual(record_report.model, "ls.calibration.record")
        self.assertEqual(record_report.report_type, "qweb-pdf")
        self.assertEqual(
            certificate_report.model, "ls.calibration.certificate"
        )
