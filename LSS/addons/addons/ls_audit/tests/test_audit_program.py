# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the audit programme lifecycle."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestAuditProgram(AuditCommon):
    """Programme references, dates, statistics and lifecycle."""

    def test_reference_is_allocated(self):
        """A programme receives a reference from its sequence."""
        self.assertTrue(self.program.reference.startswith("APG/"))

    def test_end_date_before_start_date_refused(self):
        """A programme ending before it starts is refused."""
        with self.assertRaises(ValidationError):
            self.program.date_end = self.program.date_start - relativedelta(
                days=1
            )

    def test_statistics_count_audits(self):
        """The programme counts its audits and its closed audits."""
        self.assertEqual(self.program.audit_count, 1)
        self.assertEqual(self.program.closed_audit_count, 0)
        self.assertEqual(self.program.completion_rate, 0.0)

    def test_empty_programme_cannot_be_approved(self):
        """A programme without audit cannot be approved."""
        empty = self.env["ls.audit.program"].create(
            {
                "name": "Empty Programme",
                "date_start": self.today,
                "date_end": self.today + relativedelta(months=1),
                "responsible_id": self.user_manager.id,
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(UserError):
            empty.action_approve()

    def test_approval_records_user_and_date(self):
        """Approving a programme records who approved it and when."""
        self.program.with_user(self.user_manager).action_approve()
        self.assertEqual(self.program.state, "approved")
        self.assertEqual(self.program.approved_by_id, self.user_manager)
        self.assertTrue(self.program.approval_date)

    def test_cannot_approve_twice(self):
        """A programme cannot be approved from a non-draft status."""
        self.program.action_approve()
        with self.assertRaises(UserError):
            self.program.action_approve()

    def test_cannot_start_before_approval(self):
        """A draft programme cannot be started."""
        with self.assertRaises(UserError):
            self.program.action_start()

    def test_cannot_close_with_pending_audits(self):
        """A programme with an unfinished audit cannot be closed."""
        self.program.action_approve()
        self.program.action_start()
        with self.assertRaises(UserError):
            self.program.action_close()

    def test_close_when_every_audit_is_cancelled(self):
        """A programme closes once every audit reached a final status."""
        self.program.action_approve()
        self.program.action_start()
        wizard = self.env["ls.audit.cancel"].create(
            {
                "res_model": "ls.audit.schedule",
                "res_id": self.audit.id,
                "reason": "Audit superseded by a supplier audit.",
            }
        )
        wizard.action_cancel()
        self.program.action_close()
        self.assertEqual(self.program.state, "closed")

    def test_cancellation_records_reason(self):
        """Cancelling a programme stores the justification."""
        wizard = self.env["ls.audit.cancel"].create(
            {
                "res_model": "ls.audit.program",
                "res_id": self.program.id,
                "reason": "Programme replaced after reorganisation.",
            }
        )
        wizard.action_cancel()
        self.assertEqual(self.program.state, "cancelled")
        self.assertEqual(
            self.program.cancellation_reason,
            "Programme replaced after reorganisation.",
        )

    def test_audit_planned_date_must_be_inside_programme(self):
        """An audit planned outside the programme period is refused."""
        with self.assertRaises(ValidationError):
            self.audit.date_planned = self.program.date_end + relativedelta(
                days=1
            )
