# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for monitoring plans and sample generation."""

from datetime import date

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestScheduling(EnvMonitoringCommon):
    """Only approved plans generate samples, and never duplicates."""

    def setUp(self):
        super().setUp()
        self.plan = self.env["ls.env.plan"].with_user(self.author).create(
            {
                "name": "Routine Filling Room Monitoring",
                "code": "PLAN-FR01",
                "area_id": self.area.id,
                "rationale": "Derived from the area risk assessment.",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "sampling_point_id": self.point.id,
                            "parameter_id": self.parameter_count.id,
                            "method_id": self.method.id,
                            "occupancy_state": "in_operation",
                            "frequency_interval": 1,
                            "frequency_unit": "week",
                            "start_date": date(2026, 1, 5),
                        },
                    )
                ],
            }
        )

    def test_empty_plan_cannot_be_approved(self):
        empty = self.env["ls.env.plan"].with_user(self.author).create(
            {"name": "Empty", "code": "PLAN-EMPTY"})
        with self.assertRaises(UserError):
            empty.with_user(self.manager).action_approve()

    def test_author_cannot_approve_own_plan(self):
        with self.assertRaises(UserError):
            self.plan.with_user(self.author).action_approve()

    def test_approval_initialises_the_next_due_date(self):
        self.plan.with_user(self.manager).action_approve()
        self.assertEqual(self.plan.state, "approved")
        self.assertEqual(self.plan.line_ids.next_due_date, date(2026, 1, 5))

    def test_draft_plan_generates_nothing(self):
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 3, 1), 100)
        self.assertEqual(len(samples), 0)

    def test_weekly_generation_produces_the_expected_dates(self):
        self.plan.with_user(self.manager).action_approve()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 26), 100)
        self.assertEqual(len(samples), 4)
        self.assertEqual(
            sorted(samples.mapped("scheduled_date")),
            [date(2026, 1, 5), date(2026, 1, 12),
             date(2026, 1, 19), date(2026, 1, 26)],
        )

    def test_generation_is_idempotent(self):
        self.plan.with_user(self.manager).action_approve()
        first = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 26), 100)
        second = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 26), 100)
        self.assertEqual(len(first), 4)
        self.assertEqual(len(second), 0)

    def test_generated_samples_carry_a_result_line(self):
        self.plan.with_user(self.manager).action_approve()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 5), 100)
        self.assertEqual(len(samples.result_ids), 1)
        self.assertEqual(samples.result_ids.parameter_id, self.parameter_count)
        self.assertEqual(samples.result_ids.method_id, self.method)

    def test_generated_samples_are_scheduled_and_linked_to_the_plan(self):
        self.plan.with_user(self.manager).action_approve()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 5), 100)
        self.assertEqual(samples.state, "scheduled")
        self.assertEqual(samples.plan_id, self.plan)
        self.assertFalse(samples.is_unscheduled)

    def test_the_generation_limit_is_respected(self):
        self.plan.with_user(self.manager).action_approve()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 12, 31), 3)
        self.assertEqual(len(samples), 3)

    def test_monthly_frequency_uses_calendar_arithmetic(self):
        self.plan.line_ids.write(
            {"frequency_unit": "month", "start_date": date(2026, 1, 31)})
        self.plan.with_user(self.manager).action_approve()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 4, 30), 100)
        dates = sorted(samples.mapped("scheduled_date"))
        self.assertIn(date(2026, 1, 31), dates)
        self.assertIn(date(2026, 2, 28), dates)
        self.assertIn(date(2026, 3, 31), dates)

    def test_second_parameter_joins_the_existing_sample_for_the_same_occasion(self):
        self.plan.with_user(self.manager).action_approve()
        self.env["ls.env.sample"].generate_from_plans(
            self.plan, date(2026, 1, 5), 100)
        self.plan.with_user(self.author).action_create_revision()
        revision = self.env["ls.env.plan"].search(
            [("code", "=", "PLAN-FR01"), ("state", "=", "draft")], limit=1)
        revision.line_ids.write({"start_date": date(2026, 1, 5)})
        self.env["ls.env.plan.line"].create(
            {
                "plan_id": revision.id,
                "sampling_point_id": self.point.id,
                "parameter_id": self.parameter_qualitative.id,
                "occupancy_state": "in_operation",
                "frequency_interval": 1,
                "frequency_unit": "week",
                "start_date": date(2026, 1, 5),
            }
        )
        revision.with_user(self.manager).action_approve()
        self.env["ls.env.sample"].generate_from_plans(
            revision, date(2026, 1, 5), 100)
        sample = self.env["ls.env.sample"].search(
            [
                ("sampling_point_id", "=", self.point.id),
                ("scheduled_date", "=", date(2026, 1, 5)),
            ]
        )
        self.assertEqual(len(sample), 1)
        self.assertEqual(len(sample.result_ids), 2)

    def test_duplicate_plan_line_is_rejected(self):
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.env.plan.line"].create(
                {
                    "plan_id": self.plan.id,
                    "sampling_point_id": self.point.id,
                    "parameter_id": self.parameter_count.id,
                    "occupancy_state": "in_operation",
                    "frequency_interval": 1,
                    "frequency_unit": "week",
                }
            )

    def test_method_must_match_the_parameter(self):
        with self.assertRaises(ValidationError):
            self.env["ls.env.plan.line"].create(
                {
                    "plan_id": self.plan.id,
                    "sampling_point_id": self.point_two.id,
                    "parameter_id": self.parameter_qualitative.id,
                    "method_id": self.method.id,
                    "occupancy_state": "at_rest",
                    "frequency_interval": 1,
                    "frequency_unit": "week",
                }
            )

    def test_zero_frequency_is_rejected(self):
        with self.assertRaises(pg_errors.CheckViolation):
            self.env["ls.env.plan.line"].create(
                {
                    "plan_id": self.plan.id,
                    "sampling_point_id": self.point_two.id,
                    "parameter_id": self.parameter_count.id,
                    "occupancy_state": "at_rest",
                    "frequency_interval": 0,
                    "frequency_unit": "week",
                }
            )

    def test_plan_revision_supersedes_the_predecessor(self):
        self.plan.with_user(self.manager).action_approve()
        self.plan.with_user(self.author).action_create_revision()
        revision = self.env["ls.env.plan"].search(
            [("code", "=", "PLAN-FR01"), ("state", "=", "draft")], limit=1)
        revision.with_user(self.manager).action_approve()
        self.assertEqual(self.plan.state, "superseded")
        self.assertEqual(self.plan.superseded_by_id, revision)

    def test_approved_plan_cannot_be_cancelled_or_deleted(self):
        self.plan.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            self.plan.action_cancel()
        with self.assertRaises(UserError):
            self.plan.unlink()

    def test_wizard_reports_when_nothing_is_due(self):
        wizard = self.env["ls.env.schedule.wizard"].create(
            {"date_to": date(2020, 1, 1)})
        with self.assertRaises(UserError):
            wizard.action_generate()
