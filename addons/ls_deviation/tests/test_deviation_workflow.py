# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Workflow and state machine tests."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationWorkflow(DeviationCommon):
    """Exercise every transition of the deviation state machine."""

    def test_sequence_assigned_on_create(self):
        """A created deviation receives a sequence-generated reference."""
        deviation = self._create_deviation()
        self.assertNotEqual(deviation.name, "New")
        self.assertTrue(deviation.name.startswith("DEV/"))

    def test_initial_state_is_reported(self):
        """A new deviation starts in the Reported state."""
        deviation = self._create_deviation()
        self.assertEqual(deviation.state, "reported")

    def test_creation_writes_initial_transition_log(self):
        """Creation writes one transition log entry with no source state."""
        deviation = self._create_deviation()
        self.assertEqual(len(deviation.stage_log_ids), 1)
        self.assertFalse(deviation.stage_log_ids.from_state)
        self.assertEqual(deviation.stage_log_ids.to_state, "reported")

    def test_assess_requires_severity(self):
        """Assessment is blocked until a severity is recorded."""
        deviation = self._create_deviation()
        deviation.write(
            {
                "impact_assessment": "Narrative.",
                "owner_id": self.user_investigator.id,
            }
        )
        with self.assertRaises(UserError):
            deviation.action_assess()

    def test_assess_requires_impact_assessment(self):
        """Assessment is blocked until an impact narrative is recorded."""
        deviation = self._create_deviation()
        deviation.write(
            {"severity": "minor", "owner_id": self.user_investigator.id}
        )
        with self.assertRaises(UserError):
            deviation.action_assess()

    def test_assess_requires_owner(self):
        """Assessment is blocked until an investigator is assigned."""
        deviation = self._create_deviation()
        deviation.write(
            {"severity": "minor", "impact_assessment": "Narrative."}
        )
        with self.assertRaises(UserError):
            deviation.action_assess()

    def test_assess_stamps_assessor_and_date(self):
        """A successful assessment stamps the assessor and the date."""
        deviation = self._advance_to_assessed(self._create_deviation())
        self.assertEqual(deviation.state, "assessed")
        self.assertTrue(deviation.impact_assessed_by_id)
        self.assertTrue(deviation.impact_assessment_date)

    def test_investigation_requires_an_investigation_record(self):
        """The investigation stage requires at least one investigation."""
        deviation = self._advance_to_assessed(self._create_deviation())
        with self.assertRaises(UserError):
            deviation.action_start_investigation()

    def test_disposition_requires_completed_investigation(self):
        """An incomplete investigation blocks the disposition stage."""
        deviation = self._advance_to_investigation(self._create_deviation())
        deviation.extension_rationale = "Reviewed."
        with self.assertRaises(UserError):
            deviation.action_disposition()

    def test_disposition_requires_extension_rationale(self):
        """21 CFR 211.192 extension rationale is mandatory."""
        deviation = self._advance_to_investigation(self._create_deviation())
        investigation = deviation.investigation_ids[0]
        investigation.write(
            {"findings": "Findings.", "root_cause": "Root cause."}
        )
        investigation.action_start()
        investigation.action_complete()
        with self.assertRaises(UserError):
            deviation.action_disposition()

    def test_disposition_requires_disposition_when_impacted(self):
        """An impacting deviation requires a product disposition."""
        deviation = self._advance_to_investigation(self._create_deviation())
        investigation = deviation.investigation_ids[0]
        investigation.write(
            {"findings": "Findings.", "root_cause": "Root cause."}
        )
        investigation.action_start()
        investigation.action_complete()
        deviation.extension_rationale = "Reviewed adjacent batches."
        self.assertTrue(deviation.has_impact)
        with self.assertRaises(UserError):
            deviation.action_disposition()

    def test_disposition_not_required_without_impact(self):
        """A non-impacting deviation reaches disposition with no disposition."""
        deviation = self._create_deviation()
        deviation.write(
            {
                "severity": "minor",
                "impact_assessment": "No impact identified.",
                "owner_id": self.user_investigator.id,
            }
        )
        deviation.action_assess()
        self.env["ls.deviation.investigation"].create(
            {
                "deviation_id": deviation.id,
                "name": "Investigation",
                "rca_method_id": self.rca_method.id,
                "investigator_id": self.user_investigator.id,
                "findings": "Findings.",
                "root_cause": "Root cause.",
            }
        )
        deviation.action_start_investigation()
        deviation.investigation_ids[0].action_start()
        deviation.investigation_ids[0].action_complete()
        deviation.extension_rationale = "No other batch affected."
        deviation.action_disposition()
        self.assertEqual(deviation.state, "disposition")

    def test_full_happy_path_to_disposition(self):
        """The nominal path reaches the disposition state."""
        deviation = self._advance_to_disposition(self._create_deviation())
        self.assertEqual(deviation.state, "disposition")

    def test_require_capa_needs_rationale(self):
        """Requiring a CAPA needs a documented rationale."""
        deviation = self._advance_to_disposition(self._create_deviation())
        with self.assertRaises(UserError):
            deviation.action_require_capa()

    def test_require_capa_sets_flag(self):
        """Requiring a CAPA sets the flag and moves the state."""
        deviation = self._advance_to_disposition(self._create_deviation())
        deviation.capa_decision_rationale = "Systemic cause identified."
        deviation.action_require_capa()
        self.assertEqual(deviation.state, "capa_required")
        self.assertTrue(deviation.capa_required)

    def test_illegal_transition_is_rejected(self):
        """A transition outside the state machine raises."""
        deviation = self._create_deviation()
        with self.assertRaises(UserError):
            deviation._apply_transition("closed", "illegal")

    def test_transition_from_terminal_state_is_rejected(self):
        """No transition is possible out of a terminal state."""
        deviation = self._create_deviation()
        deviation._apply_transition("cancelled", "voided")
        with self.assertRaises(UserError):
            deviation._apply_transition("reported", "reopen")

    def test_every_transition_is_logged(self):
        """Each transition appends exactly one log entry."""
        deviation = self._create_deviation()
        before = len(deviation.stage_log_ids)
        self._advance_to_assessed(deviation)
        self.assertEqual(len(deviation.stage_log_ids), before + 1)

    def test_group_expand_returns_all_states(self):
        """The kanban group expansion lists every state."""
        states = self.env["ls.deviation"]._group_expand_state(None, None)
        self.assertIn("reported", states)
        self.assertIn("cancelled", states)
        self.assertEqual(len(states), 7)
