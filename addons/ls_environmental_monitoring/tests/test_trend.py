# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for trend analysis over released results."""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestTrend(EnvMonitoringCommon):
    """Analyses cover approved samples only and report undefined figures honestly."""

    def _approved_sample(self, value):
        sample = self._create_sample()
        sample.action_schedule()
        sample.with_user(self.technician).action_collect()
        sample.with_user(self.technician).action_start_analysis()
        sample.result_ids.write({"value_numeric": value, "value_set": True})
        sample.with_user(self.technician).action_enter_results()
        sample.with_user(self.manager).action_review()
        sample.with_user(self.manager).action_approve()
        return sample

    def setUp(self):
        super().setUp()
        self._approve_limit(self._create_limit(
            self.point, self.parameter_count, action_value=10.0))

    def test_period_end_must_not_precede_the_start(self):
        with self.assertRaises(ValidationError):
            self.env["ls.env.trend"].create(
                {
                    "name": "Bad period",
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 1, 1),
                }
            )

    def test_analysis_counts_released_results(self):
        for value in (1.0, 2.0, 3.0):
            self._approved_sample(value)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Quarterly review",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        self.assertEqual(analysis.state, "computed")
        line = analysis.line_ids.filtered(
            lambda line: line.parameter_id == self.parameter_count)
        self.assertEqual(line.result_count, 3)
        self.assertEqual(line.value_min, 1.0)
        self.assertEqual(line.value_max, 3.0)
        self.assertAlmostEqual(line.value_mean, 2.0)

    def test_unapproved_samples_are_excluded(self):
        draft = self._create_sample()
        draft.action_schedule()
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Excludes unreleased",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        self.assertEqual(len(analysis.line_ids), 0)

    def test_exceedance_rate_is_a_ratio(self):
        self._approved_sample(1.0)
        self._approved_sample(1.0)
        self._approved_sample(1.0)
        self._approved_sample(50.0)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Exceedance",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        line = analysis.line_ids[0]
        self.assertEqual(line.action_count, 1)
        self.assertAlmostEqual(line.exceedance_ratio, 0.25)
        self.assertLessEqual(line.exceedance_ratio, 1.0)

    def test_standard_deviation_is_flagged_unavailable_for_one_value(self):
        self._approved_sample(5.0)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Single value",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        line = analysis.line_ids[0]
        self.assertFalse(line.value_stdev_available)
        self.assertTrue(line.value_mean_available)

    def test_direction_is_insufficient_below_the_minimum_count(self):
        for value in (1.0, 2.0, 3.0):
            self._approved_sample(value)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Thin series",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        self.assertEqual(analysis.line_ids[0].direction, "insufficient_data")

    def test_review_requires_a_conclusion(self):
        self._approved_sample(1.0)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Needs conclusion",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        with self.assertRaises(UserError):
            analysis.action_review()

    def test_reviewed_analysis_cannot_be_recomputed(self):
        self._approved_sample(1.0)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Locked",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        analysis.conclusion = "No adverse trend identified."
        analysis.action_review()
        with self.assertRaises(UserError):
            analysis.action_compute()

    def test_recomputation_replaces_previous_lines(self):
        self._approved_sample(1.0)
        analysis = self.env["ls.env.trend"].create(
            {
                "name": "Recompute",
                "date_from": date(2020, 1, 1),
                "date_to": date(2030, 1, 1),
            }
        )
        analysis.action_compute()
        first_count = len(analysis.line_ids)
        analysis.action_compute()
        self.assertEqual(len(analysis.line_ids), first_count)
