# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the reading capture and tool return-to-service wizards."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestReadingWizard(MedicalPlasticsCommon):
    """Bulk capture of parameter readings."""

    def setUp(self):
        """Create a run positioned at start-up verification."""
        super().setUp()
        self.run = self._create_run()
        self.run.action_start_setup()
        self.run.action_start_startup_check()

    def test_wizard_preloads_specification_parameters(self):
        """The wizard pre-loads every parameter of the frozen specification."""
        wizard = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id})
        self.assertEqual(len(wizard.line_ids), len(self.spec.line_ids))

    def test_wizard_defaults_values_to_target(self):
        """Pre-loaded lines default to the specification target."""
        wizard = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id})
        melt = wizard.line_ids.filtered(
            lambda line: line.parameter_line_id.code == "MELT-T"
        )
        self.assertEqual(melt.value_numeric, 220.0)

    def test_wizard_creates_readings(self):
        """Recording creates one reading per selected parameter."""
        wizard = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id, "reading_type": "startup"})
        wizard.action_record()
        self.assertEqual(len(self.run.reading_ids), len(self.spec.line_ids))

    def test_wizard_requires_a_selection(self):
        """Recording without any selected parameter is refused."""
        wizard = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id})
        wizard.line_ids.write({"capture": False})
        with self.assertRaises(ValidationError):
            wizard.action_record()

    def test_wizard_correction_requires_reason(self):
        """A correction selected in the wizard requires a reason."""
        wizard = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id, "reading_type": "startup"})
        wizard.action_record()
        original = self.run.reading_ids[0]
        second = self.env["ls.mp.reading.wizard"].with_context(
            default_run_id=self.run.id
        ).create({"run_id": self.run.id, "reading_type": "startup"})
        line = second.line_ids.filtered(
            lambda item: item.parameter_line_id == original.parameter_line_id
        )
        with self.assertRaises(ValidationError):
            line.write({"supersedes_id": original.id})

    def test_reading_wizard_blocked_on_closed_run(self):
        """The wizard cannot be opened for a closed run."""
        run = self._create_run()
        self._run_to_completed(run)
        run.with_user(self.user_manager).action_review()
        run.with_user(self.user_manager).action_close()
        with self.assertRaises(ValidationError):
            run.action_open_reading_wizard()


@tagged("post_install", "-at_install")
class TestToolServiceWizard(MedicalPlasticsCommon):
    """Controlled return of a tool to production."""

    def test_return_from_maintenance(self):
        """A tool under maintenance returns to service through the wizard."""
        self.tool.action_send_to_maintenance()
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {"tool_id": self.tool.id, "cavity_ids": [(6, 0, self.tool.cavity_ids.ids)]}
        )
        wizard.action_return_to_service()
        self.assertEqual(self.tool.state, "in_service")

    def test_return_requires_active_cavity(self):
        """At least one cavity must be confirmed active."""
        self.tool.action_send_to_maintenance()
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {"tool_id": self.tool.id}
        )
        with self.assertRaises(ValidationError):
            wizard.action_return_to_service()

    def test_quarantined_tool_requires_requalification(self):
        """A quarantined tool cannot return without requalification."""
        self.tool.action_quarantine()
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {"tool_id": self.tool.id, "cavity_ids": [(6, 0, self.tool.cavity_ids.ids)]}
        )
        with self.assertRaises(ValidationError):
            wizard.action_return_to_service()
        wizard.write(
            {"requalification_performed": True, "qualification_date": "2026-07-01"}
        )
        wizard.action_return_to_service()
        self.assertEqual(self.tool.state, "in_service")
        self.assertEqual(str(self.tool.qualification_date), "2026-07-01")

    def test_return_unblocks_confirmed_cavities(self):
        """Cavities confirmed active are unblocked on return to service."""
        cavity = self.tool.cavity_ids[0]
        cavity.blocked_reason = "Blocked for investigation."
        cavity.action_block()
        self.tool.action_send_to_maintenance()
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {"tool_id": self.tool.id, "cavity_ids": [(6, 0, self.tool.cavity_ids.ids)]}
        )
        wizard.action_return_to_service()
        self.assertEqual(cavity.state, "active")

    def test_return_resets_maintenance_baseline(self):
        """Returning to service can reset the maintenance baseline."""
        self.tool.write({"opening_shot_count": 8000})
        self.tool.action_send_to_maintenance()
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {
                "tool_id": self.tool.id,
                "cavity_ids": [(6, 0, self.tool.cavity_ids.ids)],
                "reset_maintenance_baseline": True,
            }
        )
        wizard.action_return_to_service()
        self.assertEqual(self.tool.shot_count_at_last_maintenance, 8000)
        self.assertEqual(self.tool.shots_since_maintenance, 0)

    def test_tool_not_awaiting_service_rejected(self):
        """A tool already in service cannot be returned to service."""
        wizard = self.env["ls.mp.tool.service.wizard"].create(
            {"tool_id": self.tool.id, "cavity_ids": [(6, 0, self.tool.cavity_ids.ids)]}
        )
        with self.assertRaises(ValidationError):
            wizard.action_return_to_service()
