# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the change control record report."""

from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestReports(ChangeControlCommon):
    """Verify that the report is declared and renders the whole record."""

    def test_report_action_is_declared(self):
        """The report action is bound to the change request model."""
        report = self.env.ref(
            "ls_change_control.action_report_change_control_request"
        )
        self.assertEqual(report.model, "ls.change_control.request")
        self.assertEqual(report.report_type, "qweb-pdf")
        self.assertEqual(
            report.report_name,
            "ls_change_control.report_change_control_request",
        )

    def test_report_templates_are_installed(self):
        """Both QWeb templates of the report exist."""
        for xmlid in (
            "ls_change_control.report_change_control_request",
            "ls_change_control.report_change_control_request_document",
        ):
            self.assertTrue(self.env.ref(xmlid), "Missing template %s" % xmlid)

    def test_report_renders_a_complete_record(self):
        """The HTML rendering contains the data of every section.

        The rendering is performed with ``_render_qweb_html``, which avoids
        any dependency on the PDF rendering engine of the host.
        """
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        action.with_user(self.user_manager).write({"evidence_reference": "EV-1"})
        action.with_user(self.user_requester).action_done()

        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            "ls_change_control.report_change_control_request", request.ids
        )
        content = html.decode() if isinstance(html, bytes) else html

        self.assertIn(request.name, content)
        self.assertIn("Change Control Record", content)
        self.assertIn("Impact Assessments", content)
        self.assertIn("Approvals", content)
        self.assertIn("Effectiveness Verification", content)
        self.assertIn("Uncontrolled when printed", content)
        self.assertIn("EV-1", content)

    def test_report_renders_an_empty_draft(self):
        """A draft request with no related record still renders."""
        request = self._create_request(user=self.user_requester)
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            "ls_change_control.report_change_control_request", request.ids
        )
        content = html.decode() if isinstance(html, bytes) else html
        self.assertIn("No impact assessment has been recorded.", content)
        self.assertIn("No approval has been recorded.", content)
