# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality objectives, measurements and achievement computation."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError

from odoo.addons.ls_qms.models.ls_qms_objective import compute_achievement_rate

from .common import LsQmsCommon


class TestObjective(LsQmsCommon):
    """Formulas, lifecycle and constraints of the quality objectives."""

    def test_01_reference_prefix(self):
        """An objective is numbered with the OBJ prefix."""
        self.assertTrue(self._create_objective().reference.startswith("OBJ-"))

    def test_02_increase_formula(self):
        """(current - baseline) / (target - baseline) * 100."""
        self.assertEqual(
            compute_achievement_rate("increase", 70.0, 90.0, 80.0, 0.0), 50.0
        )
        self.assertEqual(
            compute_achievement_rate("increase", 70.0, 90.0, 90.0, 0.0), 100.0
        )
        self.assertEqual(
            compute_achievement_rate("increase", 70.0, 90.0, 60.0, 0.0), 0.0
        )

    def test_03_decrease_formula(self):
        """(baseline - current) / (baseline - target) * 100."""
        self.assertEqual(
            compute_achievement_rate("decrease", 20.0, 8.0, 14.0, 0.0), 50.0
        )
        self.assertEqual(
            compute_achievement_rate("decrease", 20.0, 8.0, 8.0, 0.0), 100.0
        )

    def test_04_maintain_formula(self):
        """The tolerance drives the rate of a maintain objective."""
        self.assertEqual(
            compute_achievement_rate("maintain", 0.0, 100.0, 100.0, 10.0),
            100.0,
        )
        self.assertEqual(
            compute_achievement_rate("maintain", 0.0, 100.0, 95.0, 10.0), 50.0
        )
        self.assertEqual(
            compute_achievement_rate("maintain", 0.0, 100.0, 80.0, 10.0), 0.0
        )
        self.assertEqual(
            compute_achievement_rate("maintain", 0.0, 100.0, 100.0, 0.0),
            100.0,
        )
        self.assertEqual(
            compute_achievement_rate("maintain", 0.0, 100.0, 99.0, 0.0), 0.0
        )

    def test_05_degenerate_span_returns_zero(self):
        """A null span cannot produce a rate and returns zero."""
        self.assertEqual(
            compute_achievement_rate("increase", 90.0, 90.0, 95.0, 0.0), 0.0
        )

    def test_06_current_value_is_the_latest_measurement(self):
        """The most recent measurement drives the current value."""
        objective = self._create_objective()
        self.assertEqual(objective.current_value, 70.0)
        self.env["ls.qms.objective.measurement"].create(
            {
                "objective_id": objective.id,
                "date": self.today - relativedelta(months=2),
                "value": 75.0,
            }
        )
        self.env["ls.qms.objective.measurement"].create(
            {
                "objective_id": objective.id,
                "date": self.today - relativedelta(days=1),
                "value": 85.0,
            }
        )
        self.assertEqual(objective.current_value, 85.0)
        self.assertEqual(objective.measurement_count, 2)
        self.assertEqual(objective.achievement_rate, 75.0)

    def test_07_measurement_before_start_is_refused(self):
        """A measurement cannot precede the start of the objective."""
        objective = self._create_objective()
        with self.assertRaises(ValidationError):
            self.env["ls.qms.objective.measurement"].create(
                {
                    "objective_id": objective.id,
                    "date": objective.date_start - relativedelta(days=1),
                    "value": 75.0,
                }
            )

    def test_08_direction_constraint(self):
        """The target must be consistent with the declared direction."""
        with self.assertRaises(ValidationError):
            self._create_objective(
                direction="increase", baseline_value=90.0, target_value=70.0
            )
        with self.assertRaises(ValidationError):
            self._create_objective(
                direction="decrease", baseline_value=70.0, target_value=90.0
            )

    def test_09_performance_status(self):
        """Progress is compared with the elapsed share of the period."""
        objective = self._create_objective()
        self.assertEqual(objective.performance_status, "no_data")
        self.env["ls.qms.objective.measurement"].create(
            {
                "objective_id": objective.id,
                "date": self.today,
                "value": 90.0,
            }
        )
        self.assertEqual(objective.performance_status, "target_reached")

    def test_10_expected_progress(self):
        """Half of the period elapsed means fifty percent expected."""
        objective = self._create_objective()
        self.assertAlmostEqual(
            objective._expected_progress(self.today), 50.0, delta=2.0
        )

    def test_11_lifecycle(self):
        """Draft, in progress and closure follow each other."""
        objective = self._create_objective()
        objective.action_start()
        self.assertEqual(objective.state, "in_progress")
        objective.action_close_achieved()
        self.assertEqual(objective.state, "achieved")
        objective.action_reset_to_draft()
        self.assertEqual(objective.state, "draft")

    def test_12_close_requires_in_progress(self):
        """A draft objective cannot be closed."""
        objective = self._create_objective()
        with self.assertRaises(UserError):
            objective.action_close_not_achieved()

    def test_13_start_requires_draft(self):
        """An objective in progress cannot be started again."""
        objective = self._create_objective()
        objective.action_start()
        with self.assertRaises(UserError):
            objective.action_start()

    def test_14_non_draft_objective_cannot_be_deleted(self):
        """A started objective is cancelled, not deleted."""
        objective = self._create_objective()
        objective.action_start()
        with self.assertRaises(UserError):
            objective.unlink()
        objective.action_cancel()
        self.assertEqual(objective.state, "cancelled")

    def test_15_display_name(self):
        """The display name carries the reference."""
        objective = self._create_objective(name="Reduce complaints")
        self.assertEqual(
            objective.display_name,
            "[%s] Reduce complaints" % objective.reference,
        )

    def test_16_action_view_measurements(self):
        """The stat button returns an action filtered on the objective."""
        objective = self._create_objective()
        action = objective.action_view_measurements()
        self.assertEqual(
            action["res_model"], "ls.qms.objective.measurement"
        )
        self.assertIn(("objective_id", "=", objective.id), action["domain"])
