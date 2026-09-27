# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the manufacturing batch and of its yield rules."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestBatch(LsPharmaCommon):
    """Exercise the batch state machine, its yield rules and its guards."""

    def test_reference_is_taken_from_the_sequence(self):
        """A new batch receives a reference from its dedicated sequence."""
        batch = self._create_batch()
        self.assertTrue(batch.name)
        self.assertNotEqual(batch.name, "New")
        self.assertTrue(batch.name.startswith("BAT/"))

    def test_yield_percentage(self):
        """The percentage of theoretical yield is computed from the two.

        With a theoretical yield of 100000 and an actual yield of 99000 the
        percentage is 99000 / 100000 * 100 = 99.00.
        """
        batch = self._create_batch()
        batch.actual_yield_qty = 99000.0
        self.assertAlmostEqual(batch.yield_percentage, 99.0, places=2)
        self.assertFalse(batch.yield_investigation_required)

    def test_yield_below_the_lower_limit_requires_an_investigation(self):
        """A yield under the lower limit raises the investigation flag.

        With limits of 95 and 102 per cent, an actual yield of 90000 against
        a theoretical yield of 100000 gives 90.00 per cent, which is below the
        lower limit. 21 CFR 211.192 requires such a discrepancy to be
        investigated.
        """
        batch = self._create_batch()
        batch.actual_yield_qty = 90000.0
        self.assertAlmostEqual(batch.yield_percentage, 90.0, places=2)
        self.assertTrue(batch.yield_investigation_required)

    def test_yield_above_the_upper_limit_requires_an_investigation(self):
        """A yield over the upper limit also raises the flag."""
        batch = self._create_batch()
        batch.actual_yield_qty = 105000.0
        self.assertAlmostEqual(batch.yield_percentage, 105.0, places=2)
        self.assertTrue(batch.yield_investigation_required)

    def test_state_machine(self):
        """A batch walks the states of its life cycle in order."""
        batch = self._create_batch()
        self.assertEqual(batch.state, "draft")
        batch.with_user(self.production_manager).action_start()
        self.assertEqual(batch.state, "in_process")
        self.assertTrue(batch.date_start)
        batch.actual_yield_qty = 99000.0
        batch.with_user(self.production_manager).action_complete()
        self.assertEqual(batch.state, "manufactured")
        self.assertEqual(
            batch.user_manufactured_id, self.production_manager
        )
        batch.with_user(self.production_manager).action_quarantine()
        self.assertEqual(batch.state, "quarantine")

    def test_completion_requires_an_actual_yield(self):
        """Manufacturing cannot be declared complete without a yield.

        21 CFR 211.103 requires actual yields to be determined at the
        conclusion of each appropriate phase of manufacturing.
        """
        batch = self._create_batch()
        batch.with_user(self.production_manager).action_start()
        with self.assertRaises(UserError):
            batch.with_user(self.production_manager).action_complete()

    def test_review_requires_a_batch_record(self):
        """A batch without a batch record cannot go to review.

        21 CFR 211.188 requires batch production and control records to be
        prepared for each batch produced.
        """
        batch = self._create_batch()
        batch.with_user(self.production_manager).action_start()
        batch.actual_yield_qty = 99000.0
        batch.with_user(self.production_manager).action_complete()
        with self.assertRaises(UserError):
            batch.with_user(self.production_manager).action_submit_review()

    def test_actions_refuse_unexpected_states(self):
        """An action is refused from a state that does not permit it."""
        batch = self._create_batch()
        with self.assertRaises(UserError):
            batch.action_complete()
        with self.assertRaises(UserError):
            batch.action_submit_review()

    def test_cancel_and_reset(self):
        """A planned batch can be cancelled and returned to the draft state."""
        batch = self._create_batch()
        batch.with_user(self.production_manager).action_cancel()
        self.assertEqual(batch.state, "cancelled")
        batch.action_set_draft()
        self.assertEqual(batch.state, "draft")

    def test_cancel_is_refused_after_manufacturing(self):
        """A manufactured batch can no longer be cancelled."""
        batch = self._create_batch()
        batch.with_user(self.production_manager).action_start()
        batch.actual_yield_qty = 99000.0
        batch.with_user(self.production_manager).action_complete()
        with self.assertRaises(UserError):
            batch.action_cancel()

    def test_components_carry_the_second_person_verification(self):
        """A component records who charged it and who verified the charge.

        21 CFR 211.101(c) requires the weight or measure of each component to
        be verified by a second person.
        """
        batch = self._create_batch()
        components = self._add_components(batch)
        self.assertEqual(len(components), 2)
        for component in components:
            self.assertTrue(component.charged_by_user_id)
            self.assertTrue(component.verified_by_user_id)
            self.assertNotEqual(
                component.charged_by_user_id, component.verified_by_user_id
            )

    def test_component_verifier_must_differ_from_the_charger(self):
        """One person cannot both charge and verify a component."""
        batch = self._create_batch()
        with self.assertRaises(UserError):
            self.env["ls.pharma.batch.component"].create(
                {
                    "batch_id": batch.id,
                    "product_id": self.component_product.id,
                    "quantity": 10.0,
                    "uom_id": self.uom.id,
                    "charged_by_user_id": self.operator.id,
                    "verified_by_user_id": self.operator.id,
                }
            )

    def test_expiry_date_cannot_precede_manufacturing(self):
        """An expiry date before the manufacturing date is refused."""
        batch = self._create_batch()
        with self.assertRaises(UserError):
            batch.write(
                {
                    "date_manufacture": "2026-06-01",
                    "date_expiry": "2026-05-01",
                }
            )

    def test_related_record_counts(self):
        """The counters of related records follow the records themselves."""
        batch = self._create_batch()
        self.assertEqual(batch.batch_record_count, 0)
        self._create_batch_record(batch)
        self.assertEqual(batch.batch_record_count, 1)
