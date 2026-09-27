# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for automatic excursion creation and the excursion lifecycle."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestExcursion(EnvMonitoringCommon):
    """Breaches open excursions; excursions are closed, never deleted."""

    def _approved_sample_with(self, value, **limit_overrides):
        """Return an approved sample whose single result has ``value``."""
        limit = self._create_limit(
            self.point, self.parameter_count, **limit_overrides)
        self._approve_limit(limit)
        sample = self._create_sample()
        sample.action_schedule()
        sample.with_user(self.technician).action_collect()
        sample.with_user(self.technician).action_start_analysis()
        sample.result_ids.write({"value_numeric": value, "value_set": True})
        sample.with_user(self.technician).action_enter_results()
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        return sample

    def test_action_exceedance_opens_an_excursion(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        self.assertEqual(len(sample.excursion_ids), 1)
        excursion = sample.excursion_ids
        self.assertEqual(excursion.excursion_type, "action_exceeded")
        self.assertEqual(excursion.state, "open")
        self.assertEqual(excursion.sampling_point_id, self.point)

    def test_alert_exceedance_does_not_open_an_excursion_by_default(self):
        sample = self._approved_sample_with(
            7.0, alert_set=True, alert_value=5.0, action_value=10.0)
        self.assertEqual(sample.result_ids.evaluation, "alert_exceeded")
        self.assertEqual(len(sample.excursion_ids), 0)

    def test_alert_exceedance_opens_an_excursion_when_configured_to_escalate(self):
        sample = self._approved_sample_with(
            7.0, alert_set=True, alert_value=5.0, action_value=10.0,
            escalate_alert=True)
        self.assertEqual(sample.result_ids.evaluation, "alert_exceeded")
        self.assertEqual(len(sample.excursion_ids), 1)

    def test_compliant_result_opens_no_excursion(self):
        sample = self._approved_sample_with(1.0, action_value=10.0)
        self.assertEqual(len(sample.excursion_ids), 0)

    def test_specification_breach_marks_investigation_required(self):
        sample = self._approved_sample_with(
            500.0, action_value=10.0, spec_set=True, spec_value=100.0)
        excursion = sample.excursion_ids
        self.assertEqual(excursion.excursion_type, "spec_exceeded")
        self.assertTrue(excursion.investigation_required)

    def test_several_breaches_on_one_sample_share_one_excursion(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._create_sample(
            parameters=[self.parameter_count, self.parameter_qualitative])
        sample.action_schedule()
        sample.with_user(self.technician).action_collect()
        sample.with_user(self.technician).action_start_analysis()
        for result in sample.result_ids:
            if result.result_type == "quantitative":
                result.write({"value_numeric": 50.0, "value_set": True})
            else:
                result.write({"value_qualitative": "fail"})
        sample.with_user(self.technician).action_enter_results()
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        self.assertEqual(len(sample.excursion_ids), 1)
        self.assertEqual(len(sample.excursion_ids.result_ids), 2)

    def test_investigation_requires_an_impact_assessment(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.action_start_assessment()
        with self.assertRaises(UserError):
            excursion.action_start_investigation()

    def test_closure_requires_the_product_impact_to_be_assessed(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.action_start_assessment()
        excursion.impact_assessment = "No product exposed at the time."
        with self.assertRaises(UserError):
            excursion.action_propose_closure()

    def test_closure_requires_a_root_cause_when_investigation_is_required(self):
        sample = self._approved_sample_with(
            500.0, action_value=10.0, spec_set=True, spec_value=100.0)
        excursion = sample.excursion_ids
        excursion.action_start_assessment()
        excursion.write(
            {
                "impact_assessment": "Batch quarantined.",
                "product_impact": "potential",
            }
        )
        with self.assertRaises(UserError):
            excursion.action_propose_closure()

    def test_full_closure_path(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.owner_id = self.technician
        excursion.action_start_assessment()
        excursion.write(
            {
                "impact_assessment": "No product exposed.",
                "product_impact": "none",
            }
        )
        excursion.action_propose_closure()
        self.assertEqual(excursion.state, "pending_closure")
        excursion.with_user(self.manager).close("Cleaning verified effective.")
        self.assertEqual(excursion.state, "closed")
        self.assertEqual(excursion.closed_by_id, self.manager)
        self.assertTrue(excursion.closure_datetime)

    def test_owner_cannot_close_own_excursion(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.owner_id = self.manager
        excursion.action_start_assessment()
        excursion.write(
            {"impact_assessment": "Assessed.", "product_impact": "none"})
        excursion.action_propose_closure()
        with self.assertRaises(UserError):
            excursion.with_user(self.manager).close("Closing.")

    def test_closure_requires_a_justification(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.owner_id = self.technician
        excursion.action_start_assessment()
        excursion.write(
            {"impact_assessment": "Assessed.", "product_impact": "none"})
        excursion.action_propose_closure()
        with self.assertRaises(UserError):
            excursion.with_user(self.manager).close("")

    def test_closed_excursion_is_immutable(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.owner_id = self.technician
        excursion.action_start_assessment()
        excursion.write(
            {"impact_assessment": "Assessed.", "product_impact": "none"})
        excursion.action_propose_closure()
        excursion.with_user(self.manager).close("Resolved.")
        with self.assertRaises(UserError):
            excursion.severity = "major"

    def test_external_reference_remains_editable_after_closure(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        excursion = sample.excursion_ids
        excursion.owner_id = self.technician
        excursion.action_start_assessment()
        excursion.write(
            {"impact_assessment": "Assessed.", "product_impact": "none"})
        excursion.action_propose_closure()
        excursion.with_user(self.manager).close("Resolved.")
        excursion.external_reference = "CAPA-2026-0007"
        self.assertEqual(excursion.external_reference, "CAPA-2026-0007")

    def test_excursion_cannot_be_deleted(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        with self.assertRaises(UserError):
            sample.excursion_ids.unlink()

    def test_external_record_hook_reports_that_no_module_is_installed(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        with self.assertRaises(UserError):
            sample.excursion_ids.action_create_external_record()

    def test_invalid_transition_is_refused(self):
        sample = self._approved_sample_with(50.0, action_value=10.0)
        with self.assertRaises(UserError):
            sample.excursion_ids.action_propose_closure()
