# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the tool register, cavity handling and maintenance scheduling."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestTool(MedicalPlasticsCommon):
    """Tool lifecycle, cavity register and shot counting."""

    def test_code_assigned_from_sequence(self):
        """A tool created without a code receives one from the sequence."""
        self.assertTrue(self.tool.code)
        self.assertNotEqual(self.tool.code, "New")

    def test_cavity_register_created_automatically(self):
        """Cavities are created to match the declared cavity count."""
        self.assertEqual(len(self.tool.cavity_ids), 4)
        self.assertEqual(sorted(self.tool.cavity_ids.mapped("number")), [1, 2, 3, 4])
        self.assertEqual(self.tool.active_cavity_count, 4)

    def test_increasing_cavity_count_adds_cavities(self):
        """Raising the cavity count extends the register without duplicates."""
        self.tool.write({"cavity_count": 6})
        self.assertEqual(len(self.tool.cavity_ids), 6)
        self.assertEqual(sorted(self.tool.cavity_ids.mapped("number")), [1, 2, 3, 4, 5, 6])

    def test_cavity_count_cannot_be_reduced(self):
        """Reducing the count below registered cavities is refused."""
        with self.assertRaises(ValidationError):
            self.tool.write({"cavity_count": 2})

    def test_cavity_block_requires_reason(self):
        """A cavity cannot be blocked without a recorded reason."""
        cavity = self.tool.cavity_ids[0]
        with self.assertRaises(ValidationError):
            cavity.action_block()

    def test_cavity_block_and_unblock(self):
        """Blocking stamps the user and timestamp; unblocking clears them."""
        cavity = self.tool.cavity_ids[0]
        cavity.blocked_reason = "Damaged gate detected during inspection."
        cavity.action_block()
        self.assertEqual(cavity.state, "blocked")
        self.assertTrue(cavity.blocked_date)
        self.assertEqual(cavity.blocked_by_id, self.env.user)
        self.assertEqual(self.tool.active_cavity_count, 3)
        self.assertEqual(self.tool.blocked_cavity_count, 1)
        cavity.action_unblock()
        self.assertEqual(cavity.state, "active")
        self.assertFalse(cavity.blocked_date)
        self.assertEqual(self.tool.active_cavity_count, 4)

    def test_cavity_number_unique_per_tool(self):
        """Cavity numbers cannot repeat within one tool."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.mp.tool.cavity"].create(
                {"tool_id": self.tool.id, "number": 1}
            )

    def test_qualification_required_for_service(self):
        """A tool cannot be qualified without a qualification date."""
        tool = self.env["ls.mp.tool"].create(
            {"name": "Unqualified", "cavity_count": 1}
        )
        with self.assertRaises(ValidationError):
            tool.write({"state": "qualified"})

    def test_cannot_enter_service_without_active_cavity(self):
        """A tool with no active cavity cannot be placed in service."""
        tool = self.env["ls.mp.tool"].create(
            {
                "name": "All Blocked",
                "cavity_count": 1,
                "qualification_date": "2026-01-01",
            }
        )
        tool.action_qualify()
        cavity = tool.cavity_ids[0]
        cavity.blocked_reason = "Cavity removed pending repair."
        cavity.action_block()
        with self.assertRaises(ValidationError):
            tool.action_place_in_service()

    def test_shot_count_only_from_closed_runs(self):
        """Shots accumulate only once a run is closed."""
        run = self._create_run()
        self._run_to_completed(run, shot_count_end=500)
        self.assertEqual(self.tool.recorded_shot_count, 0)
        run.with_user(self.user_manager).action_review()
        run.with_user(self.user_manager).action_close()
        self.tool.invalidate_recordset()
        self.assertEqual(self.tool.recorded_shot_count, 500)
        self.assertEqual(self.tool.total_shot_count, 500)

    def test_opening_shot_count_included(self):
        """The opening counter is added to shots recorded in the system."""
        self.tool.write({"opening_shot_count": 12000})
        self.assertEqual(self.tool.total_shot_count, 12000)

    def test_maintenance_status_transitions(self):
        """The maintenance traffic light follows the shot-based interval."""
        self.tool.write(
            {"maintenance_interval_shots": 1000, "opening_shot_count": 0}
        )
        self.assertEqual(self.tool.maintenance_status, "ok")
        self.tool.write({"opening_shot_count": 950})
        self.assertEqual(self.tool.maintenance_status, "due_soon")
        self.tool.write({"opening_shot_count": 1200})
        self.assertEqual(self.tool.maintenance_status, "overdue")

    def test_maintenance_status_not_applicable(self):
        """With no interval configured the status is not applicable."""
        tool = self.env["ls.mp.tool"].create(
            {"name": "No Interval", "cavity_count": 1}
        )
        self.assertEqual(tool.maintenance_status, "not_applicable")

    def test_requalification_due_computed(self):
        """The requalification due date derives from the interval."""
        self.tool.write({"requalification_interval_months": 12})
        self.assertTrue(self.tool.requalification_due_date)
        self.assertEqual(str(self.tool.requalification_due_date), "2027-01-10")

    def test_cannot_send_to_maintenance_with_open_run(self):
        """A tool with an open run cannot be taken out of service."""
        run = self._create_run()
        run.action_start_setup()
        with self.assertRaises(ValidationError):
            self.tool.action_send_to_maintenance()
        run.write({"cancellation_reason": "Test teardown."})
        run.action_cancel()
        self.tool.action_send_to_maintenance()
        self.assertEqual(self.tool.state, "maintenance")

    def test_decommission_archives_tool(self):
        """Decommissioning withdraws and archives the tool."""
        self.tool.action_decommission()
        self.assertEqual(self.tool.state, "decommissioned")
        self.assertFalse(self.tool.active)

    def test_cron_check_tool_status_runs(self):
        """The scheduled status check executes without error."""
        self.tool.write({"maintenance_interval_shots": 1, "opening_shot_count": 100})
        self.assertTrue(self.env["ls.mp.tool"]._cron_check_tool_status())


@tagged("post_install", "-at_install")
class TestToolMaintenance(MedicalPlasticsCommon):
    """Tool maintenance events and their effect on the tool."""

    def setUp(self):
        """Create a preventive maintenance event on the fixture tool."""
        super().setUp()
        self.maintenance = self.env["ls.mp.tool.maintenance"].create(
            {
                "tool_id": self.tool.id,
                "maintenance_type": "preventive",
                "date_planned": "2026-06-01",
            }
        )

    def test_reference_assigned_from_sequence(self):
        """The event receives a reference from the sequence."""
        self.assertTrue(self.maintenance.name)
        self.assertNotEqual(self.maintenance.name, "New")

    def test_start_snapshots_shot_count(self):
        """Starting the event snapshots the current tool shot count."""
        self.tool.write({"opening_shot_count": 5000})
        self.maintenance.action_start()
        self.assertEqual(self.maintenance.state, "in_progress")
        self.assertEqual(self.maintenance.shot_count_at_event, 5000)

    def test_complete_requires_actions_taken(self):
        """A completed event must record the actions taken."""
        self.maintenance.action_start()
        with self.assertRaises(ValidationError):
            self.maintenance.action_done()

    def test_complete_resets_maintenance_baseline(self):
        """Completing a preventive event resets the tool baseline."""
        self.tool.write({"opening_shot_count": 5000})
        self.maintenance.action_start()
        self.maintenance.actions_taken = "Polished cavities and replaced O-rings."
        self.maintenance.action_done()
        self.assertEqual(self.tool.shot_count_at_last_maintenance, 5000)
        self.assertEqual(self.tool.shots_since_maintenance, 0)
        self.assertTrue(self.tool.last_maintenance_date)

    def test_requalification_quarantines_tool(self):
        """An event requiring requalification quarantines the tool."""
        self.maintenance.write({"requalification_required": True})
        self.maintenance.action_start()
        self.maintenance.actions_taken = "Cavity insert replaced."
        self.maintenance.action_done()
        self.assertEqual(self.tool.state, "quarantined")

    def test_completed_event_cannot_be_deleted(self):
        """A completed event forms part of the tool history."""
        self.maintenance.action_start()
        self.maintenance.actions_taken = "Cleaning performed."
        self.maintenance.action_done()
        with self.assertRaises(ValidationError):
            self.maintenance.unlink()

    def test_cancelled_event_can_be_reset(self):
        """A cancelled event can be returned to draft."""
        self.maintenance.action_cancel()
        self.assertEqual(self.maintenance.state, "cancelled")
        self.maintenance.action_reset_to_draft()
        self.assertEqual(self.maintenance.state, "draft")
