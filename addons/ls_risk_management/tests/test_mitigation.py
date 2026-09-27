# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Tests of the risk control measure model."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged

from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskMitigation(RiskCommon):
    """Verify the control option hierarchy and the dual verification path."""

    def setUp(self):
        """Create a risk and a draft control measure for each test."""
        super().setUp()
        self.risk = self._make_risk()
        self.measure = self.env["ls.risk.mitigation"].create(
            {
                "risk_id": self.risk.id,
                "title": "Interlock the mixing time",
                "description": "Constrain the recipe to the validated range.",
                "control_option": "inherent_safety",
                "responsible_id": self.user_analyst.id,
            }
        )

    def test_sequence_assigned(self):
        """A measure receives a reference from the sequence."""
        self.assertTrue(self.measure.name.startswith("RCM/"))

    def test_option_priority_mapped(self):
        """The control option determines the numeric priority."""
        self.assertEqual(self.measure.option_priority, 1)
        self.measure.control_option = "information_for_safety"
        self.assertEqual(self.measure.option_priority, 3)

    def test_option_ordering(self):
        """Measures order by the preference of their control option."""
        info = self.env["ls.risk.mitigation"].create(
            {
                "risk_id": self.risk.id,
                "title": "Add a warning to the instructions",
                "description": "Information for safety.",
                "control_option": "information_for_safety",
                "responsible_id": self.user_analyst.id,
            }
        )
        ordered = self.risk.mitigation_ids
        self.assertEqual(ordered[0], self.measure)
        self.assertEqual(ordered[-1], info)

    def test_approve_requires_manager_role(self):
        """An analyst cannot approve a measure through the ORM."""
        with self.assertRaises(AccessError):
            self.measure.with_user(self.user_analyst).action_approve()

    def test_full_verification_path(self):
        """A measure progresses from draft to verified with two verifiers."""
        self.measure.with_user(self.user_manager).action_approve()
        self.assertEqual(self.measure.state, "approved")
        self.measure.action_start()
        self.assertEqual(self.measure.state, "in_progress")
        self.measure.implementation_evidence = "Recipe locked, change control CC-1."
        self.measure.with_user(self.user_analyst).action_mark_implemented()
        self.assertEqual(self.measure.state, "implemented")
        self.assertEqual(
            self.measure.implementation_verified_by_id, self.user_analyst
        )
        self.measure.effectiveness_evidence = "Three consecutive batches conforming."
        self.measure.with_user(self.user_manager).action_verify_effectiveness()
        self.assertEqual(self.measure.state, "verified")
        self.assertEqual(
            self.measure.effectiveness_verified_by_id, self.user_manager
        )

    def test_implementation_requires_evidence(self):
        """A measure cannot be marked implemented without evidence."""
        self.measure.with_user(self.user_manager).action_approve()
        self.measure.action_start()
        with self.assertRaises(UserError):
            self.measure.action_mark_implemented()

    def test_effectiveness_requires_evidence(self):
        """Effectiveness cannot be verified without evidence."""
        self.measure.with_user(self.user_manager).action_approve()
        self.measure.action_start()
        self.measure.implementation_evidence = "Implemented."
        self.measure.with_user(self.user_analyst).action_mark_implemented()
        with self.assertRaises(UserError):
            self.measure.with_user(self.user_manager).action_verify_effectiveness()

    def test_effectiveness_blocks_same_verifier(self):
        """The implementation verifier cannot verify effectiveness."""
        self.measure.with_user(self.user_manager).action_approve()
        self.measure.action_start()
        self.measure.implementation_evidence = "Implemented."
        self.measure.with_user(self.user_manager).action_mark_implemented()
        self.measure.effectiveness_evidence = "Evidence recorded."
        with self.assertRaises(UserError):
            self.measure.with_user(self.user_manager).action_verify_effectiveness()

    def test_start_requires_approval(self):
        """A draft measure cannot be started."""
        with self.assertRaises(UserError):
            self.measure.action_start()

    def test_verified_measure_is_immutable(self):
        """A verified measure rejects changes to its evidence."""
        self.measure.with_user(self.user_manager).action_approve()
        self.measure.action_start()
        self.measure.implementation_evidence = "Implemented."
        self.measure.with_user(self.user_analyst).action_mark_implemented()
        self.measure.effectiveness_evidence = "Effective."
        self.measure.with_user(self.user_manager).action_verify_effectiveness()
        with self.assertRaises(UserError):
            self.measure.description = "Rewritten after verification."

    def test_new_risk_requires_description(self):
        """Declaring a new risk requires describing it."""
        with self.assertRaises(ValidationError):
            self.measure.introduces_new_risk = True

    def test_create_new_risk_record(self):
        """A declared new risk can be raised as a register entry."""
        self.measure.write(
            {
                "introduces_new_risk": True,
                "new_risk_description": "Locking the recipe delays deviation handling.",
            }
        )
        self.measure.action_create_new_risk()
        self.assertTrue(self.measure.new_risk_id)
        self.assertEqual(self.measure.new_risk_id.company_id, self.company)
        self.assertEqual(self.measure.new_risk_id.state, "draft")

    def test_create_new_risk_requires_declaration(self):
        """A new risk record cannot be raised without the declaration."""
        with self.assertRaises(UserError):
            self.measure.action_create_new_risk()

    def test_create_new_risk_is_not_repeatable(self):
        """A second new risk record cannot be raised for one measure."""
        self.measure.write(
            {
                "introduces_new_risk": True,
                "new_risk_description": "Consequence of the control.",
            }
        )
        self.measure.action_create_new_risk()
        with self.assertRaises(UserError):
            self.measure.action_create_new_risk()

    def test_new_risk_cannot_be_self(self):
        """The introduced risk cannot be the controlled risk."""
        with self.assertRaises(ValidationError):
            self.measure.write(
                {
                    "introduces_new_risk": True,
                    "new_risk_description": "Circular reference.",
                    "new_risk_id": self.risk.id,
                }
            )

    def test_overdue_flag(self):
        """A pending measure past its due date is flagged overdue."""
        from odoo import fields
        from dateutil.relativedelta import relativedelta

        self.measure.due_date = fields.Date.context_today(
            self.measure
        ) - relativedelta(days=1)
        self.assertTrue(self.measure.is_overdue)

    def test_unlink_blocked_after_approval(self):
        """An approved measure cannot be deleted."""
        self.measure.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            self.measure.unlink()

    def test_risk_counts_reflect_measures(self):
        """Risk level counters follow the state of their measures."""
        self.assertEqual(self.risk.mitigation_count, 1)
        self.assertEqual(self.risk.mitigation_open_count, 1)
        self.assertFalse(self.risk.all_mitigations_verified)
