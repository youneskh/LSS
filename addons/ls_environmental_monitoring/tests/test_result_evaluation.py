# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for result evaluation, limit snapshotting and amendment."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestResultEvaluation(EnvMonitoringCommon):
    """Evaluation applies approved limits and retains what it applied."""

    def _run_to_results(self, sample, values):
        """Advance a sample to results entered with the supplied values."""
        sample.action_schedule()
        sample.with_user(self.technician).action_collect()
        sample.with_user(self.technician).action_start_analysis()
        for result, value in zip(sample.result_ids, values):
            if result.result_type == "quantitative":
                result.write({"value_numeric": value, "value_set": True})
            else:
                result.write({"value_qualitative": value})
        sample.with_user(self.technician).action_enter_results()
        return sample

    def test_result_within_limits(self):
        self._approve_limit(
            self._create_limit(self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [3.0])
        self.assertEqual(sample.result_ids.evaluation, "within_limits")
        self.assertFalse(sample.result_ids.is_breach)

    def test_result_exceeding_the_action_limit(self):
        self._approve_limit(
            self._create_limit(self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [25.0])
        self.assertEqual(sample.result_ids.evaluation, "action_exceeded")
        self.assertTrue(sample.result_ids.is_breach)

    def test_result_with_no_approved_limit(self):
        sample = self._run_to_results(self._create_sample(), [5.0])
        self.assertEqual(sample.result_ids.evaluation, "no_limit")

    def test_limit_values_are_snapshotted_onto_the_result(self):
        limit = self._create_limit(
            self.point, self.parameter_count,
            alert_set=True, alert_value=5.0,
            action_set=True, action_value=10.0)
        self._approve_limit(limit)
        sample = self._run_to_results(self._create_sample(), [7.0])
        result = sample.result_ids
        self.assertEqual(result.evaluation, "alert_exceeded")
        self.assertEqual(result.applied_alert_value, 5.0)
        self.assertEqual(result.applied_action_value, 10.0)
        self.assertTrue(result.applied_alert_set)
        self.assertEqual(result.limit_id, limit)

    def test_snapshot_survives_a_later_limit_revision(self):
        limit = self._create_limit(
            self.point, self.parameter_count, action_value=10.0)
        self._approve_limit(limit)
        sample = self._run_to_results(self._create_sample(), [12.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        original_snapshot = sample.result_ids.applied_action_value

        limit.with_user(self.author).action_create_revision()
        revision = self.env["ls.env.limit"].search(
            [("sampling_point_id", "=", self.point.id), ("state", "=", "draft")],
            limit=1)
        revision.action_value = 100.0
        revision.with_user(self.manager).action_approve()

        self.assertEqual(sample.result_ids.applied_action_value, original_snapshot)
        self.assertEqual(sample.result_ids.evaluation, "action_exceeded")

    def test_qualitative_failure_is_an_action_exceedance(self):
        sample = self._create_sample(parameters=[self.parameter_qualitative])
        self._run_to_results(sample, ["fail"])
        self.assertEqual(sample.result_ids.evaluation, "action_exceeded")

    def test_lower_bound_limit_is_applied(self):
        limit = self._create_limit(
            self.point, self.parameter_temperature,
            direction="lower", action_value=18.0)
        self._approve_limit(limit)
        sample = self._create_sample(parameters=[self.parameter_temperature])
        self._run_to_results(sample, [15.0])
        self.assertEqual(sample.result_ids.evaluation, "action_exceeded")

    def test_both_bounds_use_the_more_severe_outcome(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_temperature,
            direction="upper", action_value=25.0))
        self._approve_limit(self._create_limit(
            self.point, self.parameter_temperature,
            direction="lower", action_value=18.0))
        sample = self._create_sample(parameters=[self.parameter_temperature])
        self._run_to_results(sample, [30.0])
        self.assertEqual(sample.result_ids.evaluation, "action_exceeded")

        compliant = self._create_sample(parameters=[self.parameter_temperature])
        self._run_to_results(compliant, [21.0])
        self.assertEqual(compliant.result_ids.evaluation, "within_limits")

    def test_sample_outcome_is_the_worst_result_outcome(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._create_sample(
            parameters=[self.parameter_count, self.parameter_qualitative])
        self._run_to_results(sample, [50.0, "pass"])
        self.assertEqual(sample.overall_evaluation, "action_exceeded")

    def test_negative_count_is_rejected(self):
        sample = self._create_sample()
        with self.assertRaises(ValidationError):
            sample.result_ids.write({"value_numeric": -1.0, "value_set": True})

    def test_zero_is_accepted_as_a_recorded_value(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [0.0])
        self.assertEqual(sample.result_ids.evaluation, "within_limits")
        self.assertTrue(sample.result_ids.value_set)

    def test_result_is_frozen_once_the_sample_is_approved(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [2.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            sample.result_ids.write({"value_numeric": 3.0})

    def test_amendment_retains_the_original_value(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [2.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        result = sample.result_ids
        result.with_user(self.manager).amend_value(
            "Transcription error identified during review.", value_numeric=4.0)
        self.assertTrue(result.is_amended)
        self.assertEqual(result.original_value_numeric, 2.0)
        self.assertEqual(result.value_numeric, 4.0)
        self.assertEqual(result.amended_by_id, self.manager)

    def test_amendment_requires_a_reason(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [2.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            sample.result_ids.amend_value("", value_numeric=4.0)

    def test_a_result_can_be_amended_only_once(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [2.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        result = sample.result_ids
        result.amend_value("First correction.", value_numeric=4.0)
        with self.assertRaises(UserError):
            result.amend_value("Second correction.", value_numeric=5.0)

    def test_approved_result_cannot_be_re_evaluated(self):
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))
        sample = self._run_to_results(self._create_sample(), [2.0])
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            sample.result_ids.action_evaluate()

    def test_one_result_per_parameter_per_sample(self):
        sample = self._create_sample()
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.env.result"].create(
                {
                    "sample_id": sample.id,
                    "parameter_id": self.parameter_count.id,
                }
            )
