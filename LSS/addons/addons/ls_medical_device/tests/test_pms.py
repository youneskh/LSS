# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the post-market surveillance plan and its periodic reports."""

from datetime import date

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon

#: Values that satisfy every element ``ls.md.pms.action_approve`` requires.
COMPLETE_PLAN_VALUES = {
    "information_sources": "Sources recorded for the test.",
    "collection_process": "Proactive collection process recorded for the test.",
    "referenced_procedures": "Referenced procedures recorded for the test.",
    "corrective_action_process": "Corrective action process for the test.",
    "traceability_tools": "Traceability tools recorded for the test.",
}


@tagged("post_install", "-at_install")
class TestPmsPlan(MedicalDeviceCommon):
    """Behaviour of ``ls.md.pms``."""

    def setUp(self):
        """Create a surveillance plan holding every mandatory element."""
        super().setUp()
        values = {
            "title": "Surveillance Plan Under Test",
            "device_id": self.device_iia.id,
            "responsible_id": self.user_second.id,
            "pmcf_plan_included": True,
            "pmcf_plan_reference": "TEST-PMCF-001",
            "review_frequency_months": 12,
        }
        values.update(COMPLETE_PLAN_VALUES)
        self.plan = self.env["ls.md.pms"].create(values)

    def test_report_type_derived_from_device(self):
        """The plan inherits the report obligation of the device class."""
        self.assertEqual(self.plan.periodic_report_type, "psur")
        self.assertEqual(self.plan.periodic_report_interval_months, 24)

    def test_pmcf_included_requires_reference(self):
        """Declaring a PMCF plan requires its reference to be recorded."""
        with self.assertRaises(ValidationError):
            self.plan.write({"pmcf_plan_reference": False})

    def test_pmcf_absence_requires_justification(self):
        """Omitting a PMCF plan requires a justification."""
        with self.assertRaises(ValidationError):
            self.plan.write(
                {"pmcf_plan_included": False, "pmcf_plan_reference": False}
            )

    def test_pmcf_absence_accepted_with_justification(self):
        """A justified omission of the PMCF plan is accepted."""
        self.plan.write(
            {
                "pmcf_plan_included": False,
                "pmcf_plan_reference": False,
                "pmcf_not_applicable_justification": "Justified for the test.",
            }
        )
        self.assertFalse(self.plan.pmcf_plan_included)

    def test_next_review_date_is_user_maintained(self):
        """The next review date is recorded by the user, not computed.

        The field carries no compute method, so this test pins the current
        behaviour: a written value is stored and read back unchanged.
        """
        self.plan.write({"next_review_date": date(2027, 1, 1)})
        self.assertEqual(self.plan.next_review_date, date(2027, 1, 1))

    def test_incomplete_plan_can_be_submitted(self):
        """Submission only checks the status, not the mandated content."""
        incomplete = self.env["ls.md.pms"].create(
            {
                "title": "Incomplete Plan",
                "device_id": self.device_iii.id,
                "pmcf_plan_reference": "TEST-PMCF-002",
            }
        )
        incomplete.action_submit_for_review()
        self.assertEqual(incomplete.state, "under_review")

    def test_incomplete_plan_cannot_be_approved(self):
        """Approval is refused while a mandated element is missing."""
        incomplete = self.env["ls.md.pms"].create(
            {
                "title": "Incomplete Plan For Approval",
                "device_id": self.device_iii.id,
                "pmcf_plan_reference": "TEST-PMCF-003",
            }
        )
        incomplete.action_submit_for_review()
        with self.assertRaises(UserError):
            incomplete.with_user(self.user_regulatory).action_approve()

    def test_approval_workflow(self):
        """A complete plan is submitted and approved."""
        self.plan.action_submit_for_review()
        self.plan.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.plan.state, "approved")
        self.assertTrue(self.plan.approval_date)
        self.assertEqual(self.plan.approver_id, self.user_regulatory)

    def test_plain_user_cannot_approve(self):
        """A plain user cannot approve a surveillance plan."""
        self.plan.action_submit_for_review()
        with self.assertRaises(UserError):
            self.plan.with_user(self.user_user).action_approve()

    def test_approve_requires_under_review(self):
        """A draft plan cannot be approved directly."""
        with self.assertRaises(UserError):
            self.plan.with_user(self.user_regulatory).action_approve()

    def test_version_unique_per_device(self):
        """Two plans of one device cannot share a version."""
        values = {
            "title": "Duplicate Version",
            "device_id": self.device_iia.id,
            "version": self.plan.version,
            "pmcf_plan_reference": "TEST-PMCF-004",
        }
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.md.pms"].create(values)
            self.env["ls.md.pms"].flush_model()

    def test_report_count(self):
        """The plan counts the periodic reports issued under it."""
        self.assertEqual(self.plan.report_count, 0)
        self.env["ls.md.pms_report"].create(
            {
                "device_id": self.device_iia.id,
                "pms_id": self.plan.id,
                "report_type": "psur",
                "period_start": date(2025, 1, 1),
                "period_end": date(2025, 12, 31),
            }
        )
        self.plan.invalidate_recordset()
        self.assertEqual(self.plan.report_count, 1)


@tagged("post_install", "-at_install")
class TestPmsReport(MedicalDeviceCommon):
    """Behaviour of ``ls.md.pms_report``."""

    def setUp(self):
        """Create a draft periodic post-market report."""
        super().setUp()
        self.report = self.env["ls.md.pms_report"].create(
            {
                "device_id": self.device_iia.id,
                "report_type": "psur",
                "period_start": date(2025, 1, 1),
                "period_end": date(2025, 12, 31),
                "author_id": self.user_second.id,
                "data_analysis_summary": "Analysis recorded for the test.",
                "benefit_risk_conclusion": "Benefit-risk remains favourable.",
                "conclusion": "favourable",
            }
        )

    def test_reference_allocated_from_sequence(self):
        """A new report receives a reference from the dedicated sequence."""
        self.assertNotEqual(self.report.name, "New")
        self.assertTrue(self.report.name)

    def test_period_order_enforced(self):
        """A period ending before it starts is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.report.write({"period_end": date(2024, 1, 1)})
            self.report.flush_recordset()

    def test_next_report_due_computed(self):
        """The next report due date follows from the class interval."""
        self.assertEqual(self.report.next_report_due, date(2027, 12, 31))

    def test_trend_signal_requires_description(self):
        """Declaring a trend signal requires a description of it."""
        with self.assertRaises(ValidationError):
            self.report.write({"trend_signal_identified": True})

    def test_notified_body_submission_for_implantable(self):
        """An implantable device requires submission to the notified body."""
        implant_report = self.env["ls.md.pms_report"].create(
            {
                "device_id": self.device_iii.id,
                "report_type": "psur",
                "period_start": date(2025, 1, 1),
                "period_end": date(2025, 12, 31),
            }
        )
        self.assertTrue(implant_report.notified_body_submission_required)
        self.assertFalse(self.report.notified_body_submission_required)

    def test_approval_workflow(self):
        """A complete report is submitted and approved."""
        self.report.action_submit_for_review()
        self.report.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.report.state, "approved")
        self.assertTrue(self.report.approval_date)

    def test_self_approval_rejected(self):
        """The author cannot approve their own report."""
        self.report.write({"author_id": self.user_regulatory.id})
        self.report.action_submit_for_review()
        with self.assertRaises(UserError):
            self.report.with_user(self.user_regulatory).action_approve()

    def test_approved_report_updates_device_status(self):
        """An approved report becomes the last periodic report of the device."""
        self.report.action_submit_for_review()
        self.report.with_user(self.user_regulatory).action_approve()
        self.device_iia.invalidate_recordset()
        self.assertEqual(
            self.device_iia.last_periodic_report_date, date(2025, 12, 31)
        )

    def test_content_locked_after_submission(self):
        """The content can no longer be edited after submission."""
        self.report.action_submit_for_review()
        with self.assertRaises(UserError):
            self.report.write({"data_analysis_summary": "Changed"})

    def test_approved_report_cannot_be_deleted(self):
        """An approved report is preserved rather than deleted."""
        self.report.action_submit_for_review()
        self.report.with_user(self.user_regulatory).action_approve()
        with self.assertRaises(UserError):
            self.report.unlink()

    def test_draft_report_can_be_deleted(self):
        """A draft report may still be deleted."""
        report = self.env["ls.md.pms_report"].create(
            {
                "device_id": self.device_iia.id,
                "report_type": "psur",
                "period_start": date(2024, 1, 1),
                "period_end": date(2024, 12, 31),
            }
        )
        report.unlink()
        self.assertFalse(report.exists())
