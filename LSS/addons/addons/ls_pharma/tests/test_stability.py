# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of stability studies, of their schedule and of their results."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestStability(LsPharmaCommon):
    """Exercise the schedule of ICH Q1A(R2) and the time point life cycle."""

    def setUp(self):
        """Create a draft study with a long term and an accelerated condition."""
        super().setUp()
        self.long_term = self.env.ref(
            "ls_pharma.stability_condition_long_term_25_60"
        )
        self.accelerated = self.env.ref(
            "ls_pharma.stability_condition_accelerated_40_75"
        )
        self.intermediate = self.env.ref(
            "ls_pharma.stability_condition_intermediate_30_65"
        )
        self.study = self.env["ls.pharma.stability_study"].create(
            {
                "title": "Registration stability, tablet 500 mg",
                "study_type": "registration",
                "product_id": self.product.id,
                "protocol_reference": "STB-PROT-001",
                "packaging_description": "Alu/PVC blister, 30 tablets",
                "date_start": "2026-01-15",
                "duration_months": 24,
                "condition_ids": [
                    (6, 0, [self.long_term.id, self.accelerated.id])
                ],
            }
        )

    def test_shipped_conditions_match_the_guideline(self):
        """The installed conditions carry the values published by ICH.

        ICH Q1A(R2) gives, for the general case, a long term condition of
        25 degrees Celsius with 60 per cent relative humidity and an
        accelerated condition of 40 degrees Celsius with 75 per cent relative
        humidity, each with a tolerance of 2 degrees and 5 per cent.
        """
        self.assertAlmostEqual(
            self.long_term.temperature_celsius, 25.0, places=1
        )
        self.assertAlmostEqual(self.long_term.relative_humidity, 60.0, places=1)
        self.assertAlmostEqual(
            self.long_term.temperature_tolerance, 2.0, places=1
        )
        self.assertAlmostEqual(self.long_term.humidity_tolerance, 5.0, places=1)
        self.assertAlmostEqual(
            self.accelerated.temperature_celsius, 40.0, places=1
        )
        self.assertAlmostEqual(
            self.accelerated.relative_humidity, 75.0, places=1
        )
        self.assertEqual(self.intermediate.condition_type, "intermediate")

    def test_long_term_months(self):
        """The long term frequency follows ICH Q1A(R2).

        Every three months over the first year, every six months over the
        second year and annually thereafter gives, for a twenty-four month
        study, the months 0, 3, 6, 9, 12, 18 and 24.
        """
        months = self.study._ich_timepoint_months("long_term", 24)
        self.assertEqual(months, [0, 3, 6, 9, 12, 18, 24])

    def test_long_term_months_over_thirty_six(self):
        """A thirty-six month study adds the month 36 to the same series."""
        months = self.study._ich_timepoint_months("long_term", 36)
        self.assertEqual(months, [0, 3, 6, 9, 12, 18, 24, 36])

    def test_accelerated_months(self):
        """The accelerated condition uses at least three time points."""
        months = self.study._ich_timepoint_months("accelerated", 24)
        self.assertEqual(months, [0, 3, 6])

    def test_intermediate_months(self):
        """The intermediate condition uses at least four time points."""
        months = self.study._ich_timepoint_months("intermediate", 12)
        self.assertEqual(months, [0, 6, 9, 12])

    def test_schedule_generation(self):
        """The schedule creates one time point per condition and month.

        Seven long term points plus three accelerated points give ten.
        """
        created = self.study.action_generate_schedule()
        self.assertEqual(len(created), 10)
        self.assertEqual(self.study.timepoint_count, 10)
        self.assertEqual(self.study.state, "scheduled")
        long_term_points = self.study.timepoint_ids.filtered(
            lambda point: point.condition_id == self.long_term
        )
        self.assertEqual(
            sorted(long_term_points.mapped("month")),
            [0, 3, 6, 9, 12, 18, 24],
        )

    def test_schedule_generation_is_idempotent(self):
        """Running the generation twice creates no duplicate time point."""
        self.study.action_generate_schedule()
        second = self.study.action_generate_schedule()
        self.assertEqual(len(second), 0)
        self.assertEqual(self.study.timepoint_count, 10)

    def test_scheduled_dates_follow_the_start_date(self):
        """The scheduled date of a time point is the start date plus months."""
        self.study.action_generate_schedule()
        point = self.study.timepoint_ids.filtered(
            lambda item: item.condition_id == self.long_term
            and item.month == 6
        )
        self.assertEqual(str(point.date_scheduled), "2026-07-15")

    def test_timepoint_life_cycle(self):
        """A time point walks from scheduled to completed."""
        self.study.action_generate_schedule()
        self.study.action_start()
        self.assertEqual(self.study.state, "ongoing")
        point = self.study.timepoint_ids[0]
        point.action_pull()
        self.assertEqual(point.state, "pulled")
        self.assertTrue(point.date_pulled)
        self.env["ls.pharma.stability.result"].create(
            {
                "timepoint_id": point.id,
                "name": "Assay",
                "result_type": "numeric",
                "has_minimum": True,
                "specification_min": 95.0,
                "has_maximum": True,
                "specification_max": 105.0,
                "result_value": 99.2,
                "result_uom": "%",
            }
        )
        point.action_record_tested()
        self.assertEqual(point.state, "tested")
        point.action_complete()
        self.assertEqual(point.state, "completed")

    def test_out_of_specification_result(self):
        """A result outside its limits is not conform and is counted."""
        self.study.action_generate_schedule()
        point = self.study.timepoint_ids[0]
        result = self.env["ls.pharma.stability.result"].create(
            {
                "timepoint_id": point.id,
                "name": "Assay",
                "result_type": "numeric",
                "has_minimum": True,
                "specification_min": 95.0,
                "has_maximum": True,
                "specification_max": 105.0,
                "result_value": 92.0,
                "result_uom": "%",
            }
        )
        self.assertFalse(result.is_conform)
        self.assertEqual(point.nonconforming_count, 1)

    def test_significant_change_is_carried_to_the_study(self):
        """A significant change on one result marks the whole study."""
        self.study.action_generate_schedule()
        point = self.study.timepoint_ids[0]
        self.env["ls.pharma.stability.result"].create(
            {
                "timepoint_id": point.id,
                "name": "Dissolution",
                "result_type": "numeric",
                "has_minimum": True,
                "specification_min": 80.0,
                "result_value": 70.0,
                "result_uom": "%",
                "is_significant_change": True,
            }
        )
        self.assertTrue(self.study.has_significant_change)

    def test_samples_belong_to_a_condition(self):
        """A stability sample records the condition under which it is held."""
        sample = self.env["ls.pharma.stability.sample"].create(
            {
                "name": "SS-0001",
                "study_id": self.study.id,
                "condition_id": self.long_term.id,
                "quantity": 30.0,
                "uom_id": self.uom.id,
                "chamber_reference": "CH-01",
                "date_placed": "2026-01-15",
            }
        )
        self.assertEqual(sample.state, "stored")
        sample.action_pull()
        self.assertEqual(sample.state, "pulled")
        self.assertTrue(sample.date_removed)
        self.assertEqual(self.study.sample_count, 1)

    def test_schedule_wizard_previews_before_writing(self):
        """The wizard shows a preview and creates the points on confirmation."""
        wizard = self.env["ls.pharma.stability.schedule.wizard"].create(
            {
                "study_id": self.study.id,
                "duration_months": 24,
                "condition_ids": [(6, 0, [self.accelerated.id])],
            }
        )
        self.assertTrue(wizard.preview)
        self.assertEqual(self.study.timepoint_count, 0)
        wizard.action_generate()
        self.assertEqual(self.study.timepoint_count, 3)

    def test_completion_requires_settled_time_points_and_a_conclusion(self):
        """A study is completed only once every point is settled.

        21 CFR 211.166 requires the results of the stability testing
        programme to be used in determining appropriate storage conditions and
        expiration dates, so the study carries a written conclusion.
        """
        self.study.action_generate_schedule()
        self.study.action_start()
        with self.assertRaises(UserError):
            self.study.action_complete()
        for point in self.study.timepoint_ids:
            point.remark = "Chamber excursion; time point not pulled."
            point.action_mark_missed()
        with self.assertRaises(UserError):
            self.study.action_complete()
        self.study.write(
            {
                "conclusion": "No significant change over twenty-four months.",
                "proposed_shelf_life_months": 24,
            }
        )
        self.study.action_complete()
        self.assertEqual(self.study.state, "completed")
        with self.assertRaises(UserError):
            self.study.action_start()

    def test_study_without_time_points_cannot_start(self):
        """A study with no time point cannot be started."""
        with self.assertRaises(UserError):
            self.study.action_start()
