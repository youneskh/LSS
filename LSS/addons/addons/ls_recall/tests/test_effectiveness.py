# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for effectiveness checks."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestEffectiveness(RecallCommon):
    """Checks record who was contacted, how, and what was established."""

    def test_generation_creates_one_check_per_consignee(self):
        """Planning creates a check for every consignee line."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        self._add_line(execution, self.partner_b, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        self.assertEqual(len(execution.effectiveness_ids), 2)

    def test_generation_is_idempotent(self):
        """Running the planning twice does not duplicate checks."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        execution.action_generate_effectiveness_checks()
        self.assertEqual(len(execution.effectiveness_ids), 1)

    def test_consignee_defaults_from_line(self):
        """The consignee is taken from the linked line."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        self.assertEqual(
            execution.effectiveness_ids.partner_id, self.partner_a
        )

    def test_perform_requires_an_outcome(self):
        """A check cannot be performed without recording what happened."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        check = execution.effectiveness_ids
        with self.assertRaises(UserError):
            check.action_perform()

    def test_perform_stamps_user_and_date(self):
        """Performing records who did it and when."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        check = execution.effectiveness_ids
        check.outcome = "action_taken"
        check.action_perform()
        self.assertEqual(check.state, "performed")
        self.assertTrue(check.performed_date)
        self.assertEqual(check.performed_by_user_id, self.env.user)

    def test_perform_registers_the_consignee_response(self):
        """A performed check marks the consignee line as having replied."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        check = execution.effectiveness_ids
        check.outcome = "no_stock"
        check.action_perform()
        self.assertTrue(line.response_received)

    def test_escalation_plans_a_further_attempt(self):
        """Escalating creates the next attempt."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        first = execution.effectiveness_ids
        first.outcome = "not_reachable"
        first.action_escalate()
        self.assertEqual(first.state, "escalated")
        self.assertEqual(len(execution.effectiveness_ids), 2)
        follow_up = execution.effectiveness_ids - first
        self.assertEqual(follow_up.attempt_number, 2)
        self.assertEqual(follow_up.state, "planned")

    def test_success_count_excludes_unsuccessful_outcomes(self):
        """Only outcomes showing action taken count as successful."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        self._add_line(execution, self.partner_b, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        checks = execution.effectiveness_ids
        checks[0].outcome = "action_taken"
        checks[0].action_perform()
        checks[1].outcome = "no_action"
        checks[1].action_perform()
        self.assertEqual(execution.effectiveness_performed_count, 2)
        self.assertEqual(execution.effectiveness_success_count, 1)

    def test_coverage_against_required_count(self):
        """Coverage compares contacts made with contacts required."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        self._add_line(execution, self.partner_b, self.lot_1, 10.0)
        execution.action_generate_effectiveness_checks()
        check = execution.effectiveness_ids[0]
        check.outcome = "action_taken"
        check.action_perform()
        self.assertEqual(execution.effectiveness_required_count, 2)
        self.assertEqual(execution.effectiveness_coverage, 50.0)

    def test_check_must_belong_to_the_same_recall(self):
        """A check cannot point at another recall's consignee line."""
        execution_a = self._create_execution()
        execution_b = self._create_execution()
        line = self._add_line(execution_a, self.partner_a, self.lot_1, 10.0)
        with self.assertRaises(ValidationError):
            self.env["ls.recall.effectiveness"].create(
                {
                    "execution_id": execution_b.id,
                    "line_id": line.id,
                    "partner_id": self.partner_a.id,
                    "method": "phone",
                }
            )
