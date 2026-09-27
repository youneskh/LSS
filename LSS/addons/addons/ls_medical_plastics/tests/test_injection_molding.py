# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the moulding run state machine and production controls."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestInjectionMolding(MedicalPlasticsCommon):
    """State machine, gating rules and computed production figures."""

    def test_reference_assigned_from_sequence(self):
        """A run receives a reference from the sequence."""
        run = self._create_run()
        self.assertTrue(run.name)
        self.assertNotEqual(run.name, "New")

    def test_setup_freezes_specification_version(self):
        """Entering setup freezes the approved specification and its version."""
        run = self._create_run()
        run.action_start_setup()
        self.assertEqual(run.state, "setup")
        self.assertEqual(run.parameter_spec_id, self.spec)
        self.assertEqual(run.parameter_spec_version, self.spec.version)

    def test_setup_requires_released_component(self):
        """A run cannot start setup for a component that is not released."""
        self.component.action_hold()
        run = self._create_run()
        with self.assertRaises(ValidationError):
            run.action_start_setup()

    def test_setup_requires_tool_in_service(self):
        """A run cannot start setup with a tool that is not in service."""
        run = self._create_run()
        self.tool.action_send_to_maintenance()
        with self.assertRaises(ValidationError):
            run.action_start_setup()

    def test_setup_requires_approved_specification(self):
        """A run cannot start setup without an approved specification."""
        self.spec.action_set_obsolete()
        run = self._create_run()
        with self.assertRaises(ValidationError):
            run.action_start_setup()

    def test_startup_blocked_by_missing_readings(self):
        """Start-up cannot be confirmed while required readings are missing."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        with self.assertRaises(ValidationError):
            run.action_confirm_startup()

    def test_startup_blocked_by_missing_material(self):
        """Start-up cannot be confirmed without recorded material consumption."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._capture_startup_readings(run)
        with self.assertRaises(ValidationError):
            run.action_confirm_startup()

    def test_startup_blocked_by_failing_critical_parameter(self):
        """A critical parameter out of tolerance blocks the start of production."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        self._capture_startup_readings(run, values={"MELT-T": 300.0})
        with self.assertRaises(ValidationError):
            run.action_confirm_startup()

    def test_successful_startup_starts_production(self):
        """A complete, in-specification start-up releases the run to production."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        self._capture_startup_readings(run)
        run.action_confirm_startup()
        self.assertEqual(run.state, "running")
        self.assertTrue(run.date_start)
        self.assertTrue(run.startup_verified_by_id)

    def test_complete_requires_end_counter(self):
        """A run cannot be completed without the end shot counter."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        self._capture_startup_readings(run)
        run.action_confirm_startup()
        with self.assertRaises(ValidationError):
            run.action_complete()

    def test_shot_count_derived_from_counters(self):
        """The shots produced derive from the start and end counter readings."""
        run = self._create_run(shot_count_start=1000)
        self._run_to_completed(run, shot_count_end=1750)
        self.assertEqual(run.shot_count, 750)

    def test_reject_rate_excludes_startup_scrap(self):
        """Start-up scrap is excluded from the quality reject rate."""
        run = self._create_run()
        self._run_to_completed(run, qty_produced=1000.0)
        self.env["ls.mp.injection_molding.scrap"].create(
            {"run_id": run.id, "reason_id": self.reason_startup.id, "quantity": 100.0}
        )
        self.env["ls.mp.injection_molding.scrap"].create(
            {"run_id": run.id, "reason_id": self.reason_short_shot.id, "quantity": 45.0}
        )
        self.assertEqual(run.qty_startup_scrap, 100.0)
        self.assertEqual(run.qty_rejected, 45.0)
        self.assertEqual(run.qty_good, 855.0)
        self.assertAlmostEqual(run.reject_rate, 5.0, places=4)

    def test_scrap_cannot_exceed_production(self):
        """Recorded rejects cannot exceed the parts produced."""
        run = self._create_run()
        self._run_to_completed(run, qty_produced=100.0)
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.scrap"].create(
                {
                    "run_id": run.id,
                    "reason_id": self.reason_short_shot.id,
                    "quantity": 500.0,
                }
            )

    def test_scrap_cavity_must_belong_to_tool(self):
        """A reject cannot cite a cavity from another tool."""
        other_tool = self.env["ls.mp.tool"].create(
            {"name": "Other Tool", "cavity_count": 2}
        )
        run = self._create_run()
        self._run_to_completed(run)
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.scrap"].create(
                {
                    "run_id": run.id,
                    "reason_id": self.reason_short_shot.id,
                    "quantity": 1.0,
                    "cavity_id": other_tool.cavity_ids[0].id,
                }
            )

    def test_operator_cannot_review_own_run(self):
        """Segregation of duties prevents the operator reviewing the run."""
        run = self._create_run()
        self._run_to_completed(run)
        with self.assertRaises(ValidationError):
            run.with_user(self.user_operator).action_review()

    def test_setter_cannot_review_own_run(self):
        """Segregation of duties prevents the setter reviewing the run."""
        run = self._create_run(setter_id=self.user_technician.id)
        self._run_to_completed(run)
        with self.assertRaises(ValidationError):
            run.with_user(self.user_technician).action_review()

    def test_review_requires_deviation_reference(self):
        """A run with out-of-tolerance readings needs a deviation reference."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        self._capture_startup_readings(run)
        run.action_confirm_startup()
        cooling = self.spec.line_ids.filtered(lambda item: item.code == "COOL-T")
        self.env["ls.mp.injection_molding.reading"].create(
            {
                "run_id": run.id,
                "parameter_line_id": cooling.id,
                "reading_type": "in_process",
                "value_numeric": 25.0,
            }
        )
        run.write({"qty_produced": 500.0, "shot_count_end": 200})
        run.action_complete()
        self.assertTrue(run.has_deviation)
        with self.assertRaises(ValidationError):
            run.with_user(self.user_manager).action_review()
        run.write({"deviation_reference": "DEV-2026-014"})
        run.with_user(self.user_manager).action_review()
        self.assertEqual(run.state, "reviewed")

    def test_return_for_correction_requires_comment(self):
        """Sending a run back for correction requires a review comment."""
        run = self._create_run()
        self._run_to_completed(run)
        with self.assertRaises(ValidationError):
            run.with_user(self.user_manager).action_reject_review()
        run.write({"review_comment": "Recheck the recorded output quantity."})
        run.with_user(self.user_manager).action_reject_review()
        self.assertEqual(run.state, "running")

    def test_close_freezes_record(self):
        """A closed run cannot be modified any further."""
        run = self._create_run()
        self._run_to_completed(run)
        run.with_user(self.user_manager).action_review()
        run.with_user(self.user_manager).action_close()
        self.assertEqual(run.state, "closed")
        with self.assertRaises(ValidationError):
            run.write({"qty_produced": 2000.0})

    def test_closed_run_cannot_be_deleted(self):
        """A closed run is retained as a production record."""
        run = self._create_run()
        self._run_to_completed(run)
        run.with_user(self.user_manager).action_review()
        run.with_user(self.user_manager).action_close()
        with self.assertRaises(ValidationError):
            run.unlink()

    def test_draft_run_can_be_deleted(self):
        """A draft run that never produced anything can be deleted."""
        run = self._create_run()
        run.unlink()

    def test_cancel_requires_reason(self):
        """Cancelling a run requires a recorded reason."""
        run = self._create_run()
        with self.assertRaises(ValidationError):
            run.action_cancel()
        run.write({"cancellation_reason": "Order withdrawn before production."})
        run.action_cancel()
        self.assertEqual(run.state, "cancelled")

    def test_cannot_cancel_running_run(self):
        """A run that has entered production cannot be cancelled."""
        run = self._create_run()
        run.action_start_setup()
        run.action_start_startup_check()
        self._add_material(run)
        self._capture_startup_readings(run)
        run.action_confirm_startup()
        run.write({"cancellation_reason": "Too late."})
        with self.assertRaises(ValidationError):
            run.action_cancel()

    def test_material_grade_must_be_qualified(self):
        """An unqualified grade cannot be consumed."""
        run = self._create_run()
        with self.assertRaises(ValidationError):
            self._add_material(run, material_grade_id=self.grade_unqualified.id)

    def test_drug_contact_material_requires_lot(self):
        """A grade in direct drug contact requires a lot reference."""
        run = self._create_run()
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.material"].create(
                {
                    "run_id": run.id,
                    "material_grade_id": self.grade.id,
                    "quantity": 10.0,
                    "quantity_uom": "kg",
                }
            )

    def test_tool_must_produce_component(self):
        """A run cannot pair a component with an unrelated tool."""
        other_tool = self.env["ls.mp.tool"].create(
            {"name": "Foreign Tool", "cavity_count": 1}
        )
        with self.assertRaises(ValidationError):
            self._create_run(tool_id=other_tool.id)

    def test_active_cavity_count_excludes_blocked(self):
        """Cavities blocked during the run reduce the producing cavity count."""
        run = self._create_run()
        run.write({"blocked_cavity_ids": [(6, 0, [self.tool.cavity_ids[0].id])]})
        self.assertEqual(run.active_cavity_count, 3)

    def test_manufacturing_order_counter(self):
        """The manufacturing order exposes its attached moulding runs."""
        production = self.env["mrp.production"].create(
            {"product_id": self.product_component.id, "product_qty": 100.0}
        )
        run = self._create_run(production_id=production.id)
        self.assertEqual(production.mp_run_count, 1)
        self.assertEqual(production.mp_open_run_count, 1)
        self.assertIn(run, production.mp_run_ids)
