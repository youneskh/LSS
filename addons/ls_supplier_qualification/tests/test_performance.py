# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the performance scorecard."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestPerformance(SupplierQualificationCommon):
    """Cover indicator derivation, weighting, rating and constraints."""

    def setUp(self):
        """Create a draft evaluation covering the last quarter."""
        super().setUp()
        self.evaluation = self.env["ls.supplier.performance"].create({
            "qualification_id": self.qualification.id,
            "period_start": self.today - relativedelta(months=3),
            "period_end": self.today,
        })

    def test_weights_frozen_from_company(self):
        """Weights and thresholds are seeded from the company settings."""
        self.assertEqual(self.evaluation.weight_otd, 30.0)
        self.assertEqual(self.evaluation.weight_quality, 40.0)
        self.assertEqual(self.evaluation.threshold_a, 90.0)
        self.company.ls_perf_weight_otd = 50.0
        self.evaluation.invalidate_recordset()
        self.assertEqual(self.evaluation.weight_otd, 30.0)

    def test_otd_derived_from_counters(self):
        """On-time delivery is derived from the delivery counters."""
        self.evaluation.write({
            "delivery_total_count": 40,
            "delivery_late_count": 4,
        })
        self.assertEqual(self.evaluation.otd_percent, 90.0)

    def test_quality_derived_from_counters(self):
        """Quality acceptance is derived from the lot counters."""
        self.evaluation.write({
            "lot_total_count": 25,
            "lot_rejected_count": 1,
        })
        self.assertEqual(self.evaluation.quality_percent, 96.0)

    def test_overall_score_and_rating(self):
        """The overall score is the weighted mean of the four indicators."""
        self.evaluation.write({
            "otd_percent": 90.0,
            "quality_percent": 100.0,
            "documentation_percent": 80.0,
            "responsiveness_percent": 80.0,
        })
        # (90*30 + 100*40 + 80*15 + 80*15) / 100 = 91.0
        self.assertEqual(self.evaluation.overall_score, 91.0)
        self.assertEqual(self.evaluation.rating, "a")
        self.assertFalse(self.evaluation.action_required)

    def test_low_score_flags_action_required(self):
        """A rating of C or D flags that an action is required."""
        self.evaluation.write({
            "otd_percent": 50.0,
            "quality_percent": 60.0,
            "documentation_percent": 60.0,
            "responsiveness_percent": 60.0,
        })
        self.assertEqual(self.evaluation.rating, "d")
        self.assertTrue(self.evaluation.action_required)

    def test_percentage_bounds(self):
        """Indicators outside 0-100 are rejected."""
        with self.assertRaises(ValidationError):
            self.evaluation.documentation_percent = 120.0

    def test_counter_consistency(self):
        """Late deliveries cannot exceed total deliveries."""
        with self.assertRaises(ValidationError):
            self.evaluation.write({
                "delivery_total_count": 5,
                "delivery_late_count": 9,
            })

    def test_period_must_be_positive(self):
        """The period end must follow the period start."""
        with self.assertRaises(ValidationError):
            self.evaluation.period_end = self.evaluation.period_start

    def test_confirmed_periods_cannot_overlap(self):
        """Two confirmed evaluations of a dossier cannot overlap."""
        self.evaluation.action_confirm()
        overlapping = self.env["ls.supplier.performance"].create({
            "qualification_id": self.qualification.id,
            "period_start": self.today - relativedelta(months=1),
            "period_end": self.today + relativedelta(months=1),
        })
        with self.assertRaises(ValidationError):
            overlapping.action_confirm()

    def test_confirmed_evaluation_cannot_be_deleted(self):
        """A confirmed evaluation is retained."""
        self.evaluation.action_confirm()
        with self.assertRaises(UserError):
            self.evaluation.unlink()

    def test_latest_rating_exposed_on_dossier(self):
        """The dossier exposes the latest confirmed rating."""
        self.evaluation.write({
            "otd_percent": 95.0,
            "quality_percent": 95.0,
            "documentation_percent": 95.0,
            "responsiveness_percent": 95.0,
        })
        self.evaluation.action_confirm()
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.latest_performance_rating, "a")
        self.assertEqual(self.qualification.latest_performance_score, 95.0)

    def test_automatic_counters_require_purchase_stock(self):
        """Automatic counters are refused when the bridge fields are absent."""
        has_link = (
            "stock.move" in self.env
            and "purchase_line_id" in self.env["stock.move"]._fields
        )
        if has_link:
            self.evaluation.action_compute_delivery_counters()
            self.assertGreaterEqual(self.evaluation.delivery_total_count, 0)
        else:
            with self.assertRaises(UserError):
                self.evaluation.action_compute_delivery_counters()

    def test_automatic_counters_refused_when_confirmed(self):
        """Counters cannot be recomputed on a confirmed evaluation."""
        self.evaluation.action_confirm()
        with self.assertRaises(UserError):
            self.evaluation.action_compute_delivery_counters()
