# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the audit lifecycle from planning to closure."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestAuditWorkflow(AuditCommon):
    """State machine, statistics, locking and deletion rules."""

    def setUp(self):
        """Approve the programme: audits are only scheduled inside one."""
        super().setUp()
        self.program.action_approve()

    def test_schedule_requires_approved_programme(self):
        """An audit of a programme that is not approved cannot be scheduled."""
        audit = self._create_audit(
            program_id=self.env["ls.audit.program"].create(
                {
                    "name": "Draft Programme",
                    "date_start": self.program.date_start,
                    "date_end": self.program.date_end,
                    "responsible_id": self.user_manager.id,
                    "company_id": self.company.id,
                }
            ).id
        )
        self._load_checklist(audit)
        with self.assertRaises(UserError):
            audit.action_schedule()

    def test_reference_is_allocated(self):
        """An audit receives a reference from its sequence."""
        self.assertTrue(self.audit.reference.startswith("AUD/"))

    def test_initial_state_is_planned(self):
        """A new audit starts in the planned status."""
        self.assertEqual(self.audit.state, "planned")

    def test_schedule_requires_qualified_lead_auditor(self):
        """An audit led by an unqualified user cannot be scheduled."""
        self.qualification_lead.is_lead_auditor = False
        self._load_checklist()
        with self.assertRaises(UserError):
            self.audit.action_schedule()

    def test_schedule_refuses_expired_qualification(self):
        """An audit with a lapsed team member cannot be scheduled."""
        self.qualification_auditor.expiry_date = self.today - relativedelta(
            days=1
        )
        self._load_checklist()
        with self.assertRaises(UserError):
            self.audit.action_schedule()

    def test_schedule_refuses_out_of_scope_auditor(self):
        """An auditor not qualified for the audited area is refused."""
        self.qualification_auditor.scope_ids = [(6, 0, self.area_other.ids)]
        self._load_checklist()
        with self.assertRaises(UserError):
            self.audit.action_schedule()

    def test_schedule_succeeds_with_qualified_team(self):
        """A qualified team allows the audit to be scheduled."""
        self._load_checklist()
        self.audit.action_schedule()
        self.assertEqual(self.audit.state, "scheduled")

    def test_cannot_start_without_checklist(self):
        """An audit without loaded questions cannot be started."""
        self.audit.action_schedule()
        with self.assertRaises(UserError):
            self.audit.action_start()

    def test_start_records_actual_start(self):
        """Starting the fieldwork records the actual start timestamp."""
        self._bring_audit_to_in_progress()
        self.assertEqual(self.audit.state, "in_progress")
        self.assertTrue(self.audit.date_start)

    def test_cannot_complete_with_pending_mandatory_question(self):
        """A pending mandatory question blocks completion."""
        self._bring_audit_to_in_progress()
        with self.assertRaises(UserError):
            self.audit.action_complete()

    def test_optional_question_does_not_block_completion(self):
        """A pending optional question does not block completion."""
        self._bring_audit_to_in_progress()
        mandatory = self.audit.response_ids.filtered("is_mandatory")
        mandatory.write({"result": "conform"})
        self.audit.action_complete()
        self.assertEqual(self.audit.state, "completed")
        self.assertTrue(self.audit.date_end)

    def test_conformity_rate_ignores_not_applicable(self):
        """Questions marked not applicable are excluded from the rate."""
        self._bring_audit_to_in_progress()
        responses = self.audit.response_ids
        responses[0].write({"result": "conform"})
        responses[1].write(
            {"result": "nonconform", "evidence": "Evidence recorded."}
        )
        responses[2].write({"result": "not_applicable"})
        self.assertEqual(self.audit.assessed_count, 3)
        self.assertAlmostEqual(self.audit.conformity_rate, 50.0, places=2)

    def test_duration_is_computed(self):
        """The fieldwork duration is derived from start and end."""
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()
        self.assertGreaterEqual(self.audit.duration_hours, 0.0)

    def test_follow_up_requires_issued_report(self):
        """An audit without issued report cannot move to follow-up."""
        self._complete_audit()
        with self.assertRaises(UserError):
            self.audit.action_follow_up()

    def test_close_requires_no_open_finding(self):
        """An audit with an open finding cannot be closed."""
        self._complete_audit()
        finding = self._create_finding()
        finding.action_issue()
        self._issue_report()
        self.audit.action_follow_up()
        self.assertEqual(self.audit.open_finding_count, 1)
        with self.assertRaises(UserError):
            self.audit.action_close()

    def test_full_lifecycle_to_closed(self):
        """An audit closes once report and findings are resolved."""
        self._complete_audit()
        self._issue_report()
        self.audit.action_follow_up()
        self.audit.action_close()
        self.assertEqual(self.audit.state, "closed")
        self.assertTrue(self.audit.closure_date)
        self.assertTrue(self.audit.closed_by_id)

    def test_closed_audit_is_read_only(self):
        """A closed audit refuses further modification."""
        self._complete_audit()
        self._issue_report()
        self.audit.action_follow_up()
        self.audit.action_close()
        with self.assertRaises(UserError):
            self.audit.name = "Renamed after closure"

    def test_closed_audit_can_still_be_archived(self):
        """Archiving remains possible on a closed audit."""
        self._complete_audit()
        self._issue_report()
        self.audit.action_follow_up()
        self.audit.action_close()
        self.audit.active = False
        self.assertFalse(self.audit.active)

    def test_started_audit_cannot_be_deleted(self):
        """An audit that left the planned status cannot be deleted."""
        self._bring_audit_to_in_progress()
        with self.assertRaises(UserError):
            self.audit.unlink()

    def test_planned_audit_can_be_deleted(self):
        """A planned audit can still be deleted."""
        audit = self._create_audit(name="Disposable Audit")
        audit.unlink()
        self.assertFalse(audit.exists())

    def test_transition_out_of_order_is_refused(self):
        """A transition from an unexpected status is refused."""
        with self.assertRaises(UserError):
            self.audit.action_complete()

    def test_is_overdue_flag_and_search(self):
        """The overdue flag is computed and searchable."""
        self.program.date_start = self.today - relativedelta(months=6)
        self.audit.date_planned = self.today - relativedelta(days=3)
        self.assertTrue(self.audit.is_overdue)
        overdue = self.env["ls.audit.schedule"].search(
            [("is_overdue", "=", True)]
        )
        self.assertIn(self.audit, overdue)
        not_overdue = self.env["ls.audit.schedule"].search(
            [("is_overdue", "=", False)]
        )
        self.assertNotIn(self.audit, not_overdue)

    def test_cancelled_audit_records_reason(self):
        """Cancelling an audit stores the justification."""
        wizard = self.env["ls.audit.cancel"].create(
            {
                "res_model": "ls.audit.schedule",
                "res_id": self.audit.id,
                "reason": "Auditee site closed for maintenance.",
            }
        )
        wizard.action_cancel()
        self.assertEqual(self.audit.state, "cancelled")
        self.assertEqual(
            self.audit.cancellation_reason,
            "Auditee site closed for maintenance.",
        )

    def test_cancel_wizard_refuses_final_record(self):
        """A closed audit can no longer be cancelled."""
        self._complete_audit()
        self._issue_report()
        self.audit.action_follow_up()
        self.audit.action_close()
        wizard = self.env["ls.audit.cancel"].create(
            {
                "res_model": "ls.audit.schedule",
                "res_id": self.audit.id,
                "reason": "Too late.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_cancel()

    def _complete_audit(self):
        """Advance the fixture audit to the completed status."""
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()

    def _issue_report(self):
        """Prepare, review, approve and issue a report on the audit."""
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        report.with_user(self.user_manager).action_approve()
        report.with_user(self.user_manager).action_issue()
        return report
