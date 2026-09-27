# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of calibration plans, record generation and OOT events."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CalibrationCommon


@tagged("post_install", "-at_install")
class TestCalibrationPlan(CalibrationCommon):
    """Plan approval, overlap control and scheduled record generation."""

    def test_plan_approval(self):
        """Approving a plan stamps the approver and the timestamp."""
        self.plan.with_user(self.user_approver).action_approve()
        self.assertEqual(self.plan.state, "approved")
        self.assertEqual(self.plan.approved_by_user_id, self.user_approver)
        self.assertTrue(self.plan.approved_date)

    def test_plan_without_points_cannot_be_approved(self):
        """A plan on a point-less instrument cannot be approved."""
        instrument = self.env["ls.calibration.instrument"].create(
            {"name": "No points", "category_id": self.category.id}
        )
        plan = self.env["ls.calibration.plan"].create(
            {
                "name": "Point-less plan",
                "instrument_id": instrument.id,
                "start_date": self.today,
            }
        )
        with self.assertRaises(UserError):
            plan.action_approve()

    def test_external_plan_requires_provider(self):
        """An external plan must name its service provider."""
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.plan"].create(
                {
                    "name": "External plan",
                    "instrument_id": self.instrument.id,
                    "start_date": self.today,
                    "provider_type": "external",
                }
            )

    def test_overlapping_approved_plans_rejected(self):
        """Two approved plans cannot overlap on one instrument."""
        self.plan.action_approve()
        second = self.env["ls.calibration.plan"].create(
            {
                "name": "Competing plan",
                "instrument_id": self.instrument.id,
                "start_date": self.today + relativedelta(days=10),
            }
        )
        with self.assertRaises(ValidationError):
            second.action_approve()

    def test_non_overlapping_plans_allowed(self):
        """Sequential plans with disjoint windows may both be approved."""
        self.plan.end_date = self.today + relativedelta(days=30)
        self.plan.action_approve()
        second = self.env["ls.calibration.plan"].create(
            {
                "name": "Successor plan",
                "instrument_id": self.instrument.id,
                "start_date": self.today + relativedelta(days=31),
            }
        )
        second.action_approve()
        self.assertEqual(second.state, "approved")

    def test_suspend_requires_reason(self):
        """Suspending a plan without a reason is refused."""
        self.plan.action_approve()
        with self.assertRaises(UserError):
            self.plan.action_suspend()
        self.plan.suspension_reason = "Instrument withdrawn for repair"
        self.plan.action_suspend()
        self.assertEqual(self.plan.state, "suspended")
        self.plan.action_resume()
        self.assertEqual(self.plan.state, "approved")
        self.assertFalse(self.plan.suspension_reason)

    def test_close_requires_reason(self):
        """Closing a plan without a reason is refused."""
        with self.assertRaises(UserError):
            self.plan.action_close()
        self.plan.closure_reason = "Superseded by SOP-CAL-030"
        self.plan.action_close()
        self.assertEqual(self.plan.state, "closed")
        self.assertFalse(self.plan.active)

    def test_generation_creates_scheduled_records(self):
        """Generation creates one draft record per due occurrence."""
        self.plan.action_approve()
        horizon = self.today + relativedelta(years=3)
        created = self.plan._generate_records_until(horizon)
        self.assertEqual(len(created), 4)
        self.assertTrue(all(rec.state == "draft" for rec in created))
        self.assertEqual(created[0].scheduled_date, self.today)
        self.assertEqual(
            created[1].scheduled_date, self.today + relativedelta(years=1)
        )

    def test_generation_respects_end_date(self):
        """Generation stops at the plan effective-to date."""
        self.plan.end_date = self.today + relativedelta(years=1, days=1)
        self.plan.action_approve()
        created = self.plan._generate_records_until(
            self.today + relativedelta(years=5)
        )
        self.assertEqual(len(created), 2)

    def test_generation_skips_unapproved_plans(self):
        """A draft plan generates nothing."""
        created = self.plan._generate_records_until(
            self.today + relativedelta(years=2)
        )
        self.assertFalse(created)

    def test_generation_is_idempotent(self):
        """Running generation twice over the same horizon adds nothing."""
        self.plan.action_approve()
        horizon = self.today + relativedelta(years=2)
        first = self.plan._generate_records_until(horizon)
        self.assertTrue(first)
        second = self.plan._generate_records_until(horizon)
        self.assertFalse(second)

    def test_plan_with_records_cannot_be_deleted(self):
        """A plan that produced records cannot be deleted."""
        self.plan.action_approve()
        self.plan._generate_records_until(self.today)
        with self.assertRaises(UserError):
            self.plan.unlink()


@tagged("post_install", "-at_install")
class TestCalibrationOot(CalibrationCommon):
    """Out-of-tolerance event creation, assessment and closure."""

    def _approve_failing_record(self):
        """Take a record with a failing as-found series through to approval."""
        record = self._create_record()
        record.with_user(self.user_technician).action_start()
        self._enter_reading(record, self.point_zero, as_found=0.0)
        self._enter_reading(record, self.point_mid, as_found=105.0)
        record.with_user(self.user_technician).action_mark_performed()
        record.with_user(self.user_technician).action_submit_for_review()
        record.with_user(self.user_approver).action_review()
        record.with_user(self.user_approver_two).action_approve()
        return record

    def test_oot_raised_on_as_found_failure(self):
        """Approving a failing calibration raises an OOT event."""
        record = self._approve_failing_record()
        self.assertEqual(len(record.oot_ids), 1)
        event = record.oot_ids
        self.assertEqual(event.state, "open")
        self.assertEqual(event.instrument_id, self.instrument)
        self.assertTrue(event.name.startswith("OOT/"))

    def test_oot_quarantines_the_instrument(self):
        """Raising an OOT places the in-service instrument in quarantine."""
        self._approve_failing_record()
        self.assertEqual(self.instrument.state, "quarantined")
        self.assertTrue(self.instrument.quarantine_reason)

    def test_no_oot_when_assessment_not_required(self):
        """An instrument opted out of OOT assessment raises no event."""
        self.instrument.requires_oot_assessment = False
        record = self._approve_failing_record()
        self.assertFalse(record.oot_ids)

    def test_no_oot_on_passing_calibration(self):
        """A passing calibration raises no event."""
        record = self._create_record()
        self._perform_and_submit(record)
        record.with_user(self.user_approver).action_review()
        record.with_user(self.user_approver_two).action_approve()
        self.assertFalse(record.oot_ids)

    def test_assessment_requires_all_fields(self):
        """Completing an assessment requires every mandatory element."""
        event = self._approve_failing_record().oot_ids
        event.action_start_assessment()
        with self.assertRaises(UserError):
            event.action_complete_assessment()
        event.impact_assessment = "Weighings above 100 g may be inaccurate."
        with self.assertRaises(UserError):
            event.action_complete_assessment()
        event.product_impact = "potential"
        with self.assertRaises(UserError):
            event.action_complete_assessment()
        event.disposition = "further_investigation"
        with self.assertRaises(UserError):
            event.action_complete_assessment()
        event.disposition_justification = "Batch records to be reviewed."
        event.with_user(self.user_approver).action_complete_assessment()
        self.assertEqual(event.state, "assessed")

    def test_closure_requires_capa_when_impact_reported(self):
        """A reported product impact requires a corrective action reference."""
        event = self._approve_failing_record().oot_ids
        event.action_start_assessment()
        event.write(
            {
                "impact_assessment": "Potential impact on three batches.",
                "product_impact": "confirmed",
                "disposition": "product_quarantine",
                "disposition_justification": "Batches quarantined pending review.",
            }
        )
        event.with_user(self.user_approver).action_complete_assessment()
        with self.assertRaises(UserError):
            event.with_user(self.user_manager).action_close()
        event.capa_reference = "CAPA-2026-0117"
        event.with_user(self.user_manager).action_close()
        self.assertEqual(event.state, "closed")
        self.assertEqual(event.closed_by_user_id, self.user_manager)

    def test_assessor_cannot_close(self):
        """The user who assessed an event cannot also close it."""
        event = self._approve_failing_record().oot_ids
        event.action_start_assessment()
        event.write(
            {
                "impact_assessment": "No impact identified.",
                "product_impact": "none",
                "disposition": "no_action",
                "disposition_justification": "Deviation below reporting limit.",
            }
        )
        event.with_user(self.user_approver).action_complete_assessment()
        with self.assertRaises(UserError):
            event.with_user(self.user_approver).action_close()

    def test_affected_period_bounds(self):
        """The affected period cannot end before it starts."""
        event = self._approve_failing_record().oot_ids
        with self.assertRaises(ValidationError):
            event.write(
                {
                    "affected_period_start": self.today,
                    "affected_period_end": self.today - relativedelta(days=5),
                }
            )

    def test_forbidden_oot_transition(self):
        """An OOT transition outside the map is refused."""
        event = self._approve_failing_record().oot_ids
        with self.assertRaises(UserError):
            event.action_close()

    def test_assessed_event_cannot_be_deleted(self):
        """Only an open event may be deleted."""
        event = self._approve_failing_record().oot_ids
        event.action_start_assessment()
        with self.assertRaises(UserError):
            event.unlink()
