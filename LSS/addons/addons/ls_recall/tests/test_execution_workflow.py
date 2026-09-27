# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the recall state machine and its quality gates."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestExecutionWorkflow(RecallCommon):
    """Forward transitions are gated on the evidence they claim."""

    def test_reference_and_initial_state(self):
        """A new recall is Planned and carries a reference."""
        execution = self._create_execution()
        self.assertEqual(execution.state, "planned")
        self.assertTrue(execution.name.startswith("RCL/"))

    def test_initiate_requires_reason(self):
        """A recall cannot be initiated without a stated reason."""
        execution = self._create_execution(reason=False)
        with self.assertRaises(UserError):
            execution.action_initiate()

    def test_initiate_requires_lots(self):
        """A recall cannot be initiated without affected lots."""
        execution = self._create_execution(lot_ids=[(5, 0, 0)])
        with self.assertRaises(UserError):
            execution.action_initiate()

    def test_initiate_requires_hazard_evaluation(self):
        """A real field action needs a hazard evaluation to start."""
        execution = self._create_execution(health_hazard_evaluation=False)
        with self.assertRaises(UserError):
            execution.action_initiate()

    def test_initiate_requires_classification(self):
        """A real field action needs a classification to start."""
        execution = self._create_execution(classification="not_classified")
        with self.assertRaises(UserError):
            execution.action_initiate()

    def test_mock_recall_skips_strategy_gate(self):
        """A rehearsal may start without a hazard evaluation."""
        execution = self._create_execution(
            action_type="mock_recall",
            classification="not_classified",
            health_hazard_evaluation=False,
            depth=False,
        )
        execution.action_initiate()
        self.assertEqual(execution.state, "initiated")
        self.assertTrue(execution.is_mock)

    def test_initiation_stamps_dates(self):
        """Initiation records when it happened."""
        execution = self._create_execution()
        execution.action_initiate()
        self.assertTrue(execution.initiation_date)
        self.assertTrue(execution.decision_date)

    def test_cannot_skip_a_state(self):
        """The forward path cannot be short-circuited."""
        execution = self._create_execution()
        execution.action_initiate()
        with self.assertRaises(UserError):
            execution.action_start_effectiveness()

    def test_decision_fields_frozen_after_initiation(self):
        """Change-controlled fields are locked once initiated."""
        execution = self._create_execution()
        execution.action_initiate()
        with self.assertRaises(UserError):
            execution.classification = "class_i"

    def test_reset_to_planned_only_when_clean(self):
        """A recall with related records cannot be reset."""
        execution = self._create_execution()
        execution.action_initiate()
        execution.action_reset_to_planned()
        self.assertEqual(execution.state, "planned")
        execution.action_initiate()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        with self.assertRaises(UserError):
            execution.action_reset_to_planned()

    def test_communication_state_requires_a_sent_message(self):
        """Moving to Communication needs a communication actually sent."""
        execution = self._create_execution()
        execution.action_initiate()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.write({"state": "in_progress"})
        with self.assertRaises(UserError):
            execution.action_start_communication()

    def test_effectiveness_state_requires_planned_checks(self):
        """Level A requires a check for every consignee."""
        execution = self._create_execution()
        execution.action_initiate()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        self._add_line(execution, self.partner_b, self.lot_1, 5.0)
        execution.write({"state": "in_progress"})
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        execution.action_start_communication()
        self.assertEqual(execution.effectiveness_required_count, 2)
        with self.assertRaises(UserError):
            execution.action_start_effectiveness()

    def test_required_checks_follow_the_level(self):
        """The sample size is derived from the selected level."""
        execution = self._create_execution()
        for index in range(10):
            partner = self.env["res.partner"].create(
                {"name": f"Consignee {index}"}
            )
            self._add_line(execution, partner, self.lot_1, 1.0)
        self.assertEqual(execution.consignee_count, 10)
        execution.effectiveness_level = "a"
        self.assertEqual(execution.effectiveness_required_count, 10)
        execution.effectiveness_level = "c"
        self.assertEqual(execution.effectiveness_required_count, 1)
        execution.effectiveness_level = "d"
        self.assertEqual(execution.effectiveness_required_count, 1)
        execution.effectiveness_level = "e"
        self.assertEqual(execution.effectiveness_required_count, 0)

    def test_level_b_sample_bounds(self):
        """Level B is strictly between 10 and 100 percent."""
        execution = self._create_execution(effectiveness_level="b")
        with self.assertRaises(ValidationError):
            execution.effectiveness_sample_pct = 5.0
        with self.assertRaises(ValidationError):
            execution.effectiveness_sample_pct = 100.0
        execution.effectiveness_sample_pct = 50.0
        self.assertEqual(execution.effectiveness_sample_pct, 50.0)

    def test_lot_must_belong_to_product(self):
        """A lot of another product cannot be attached."""
        other_product = self._create_tracked_product("Other tablets")
        other_lot = self.env["stock.lot"].create(
            {"name": "LOT-OTHER", "product_id": other_product.id}
        )
        with self.assertRaises(ValidationError):
            self._create_execution(lot_ids=[(6, 0, other_lot.ids)])

    def test_target_date_cannot_precede_decision(self):
        """The completion target must not be in the past of the decision."""
        with self.assertRaises(ValidationError):
            self._create_execution(
                decision_date="2026-06-01 08:00:00",
                target_completion_date="2026-05-01",
            )

    def test_closure_gates_reported(self):
        """Every gate is evaluated and returned with a label."""
        execution = self._advance_to_effectiveness(self._create_execution())
        results = execution._evaluate_closure_gates()
        self.assertTrue(results)
        labels = [label for _, label in results]
        self.assertEqual(len(labels), len(set(labels)))

    def test_close_blocked_without_final_report(self):
        """A real recall cannot be closed without an approved report."""
        execution = self._advance_to_effectiveness(self._create_execution())
        wizard = self.env["ls.recall.close.wizard"].create(
            {"execution_id": execution.id, "justification": "Complete."}
        )
        self.assertFalse(wizard.gates_passed)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_manager_may_override_failed_gates(self):
        """A manager can close with failed gates and a justification."""
        execution = self._advance_to_effectiveness(self._create_execution())
        wizard = (
            self.env["ls.recall.close.wizard"]
            .with_user(self.user_manager)
            .create(
                {
                    "execution_id": execution.id,
                    "justification": "Closed on documented risk basis.",
                    "override_gates": True,
                }
            )
        )
        wizard.action_confirm()
        self.assertEqual(execution.state, "closed")
        self.assertEqual(execution.closed_by_user_id, self.user_manager)
        self.assertTrue(execution.closure_justification)

    def test_coordinator_cannot_override_failed_gates(self):
        """Overriding is reserved to the manager role."""
        execution = self._advance_to_effectiveness(self._create_execution())
        wizard = (
            self.env["ls.recall.close.wizard"]
            .with_user(self.user_coordinator)
            .create(
                {
                    "execution_id": execution.id,
                    "justification": "Trying to force closure.",
                    "override_gates": True,
                }
            )
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_closed_recall_is_immutable(self):
        """A closed recall rejects further changes."""
        execution = self._advance_to_effectiveness(self._create_execution())
        wizard = (
            self.env["ls.recall.close.wizard"]
            .with_user(self.user_manager)
            .create(
                {
                    "execution_id": execution.id,
                    "justification": "Closed.",
                    "override_gates": True,
                }
            )
        )
        wizard.action_confirm()
        with self.assertRaises(UserError):
            execution.reason = "Changed after closure"

    def test_cancellation_records_the_reason(self):
        """Cancelling keeps the record and the stated reason."""
        execution = self._create_execution()
        execution.action_initiate()
        wizard = self.env["ls.recall.close.wizard"].create(
            {
                "execution_id": execution.id,
                "mode": "cancel",
                "justification": "Defect not confirmed on retest.",
            }
        )
        wizard.action_confirm()
        self.assertEqual(execution.state, "cancelled")
        self.assertIn("retest", execution.cancellation_reason)

    def test_initiated_recall_cannot_be_deleted(self):
        """Deletion is refused once a decision has been recorded."""
        execution = self._create_execution()
        execution.action_initiate()
        with self.assertRaises(UserError):
            execution.unlink()
