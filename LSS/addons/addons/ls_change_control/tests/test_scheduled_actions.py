# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the three scheduled actions."""

from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestScheduledActions(ChangeControlCommon):
    """Verify that the reminders target exactly the expected records."""

    def test_pending_approval_reminder_is_sent_after_the_delay(self):
        """An approval older than the reminder delay is reminded once."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        self.company.ls_cc_approval_reminder_days = 3
        old_date = fields.Date.context_today(request) - timedelta(days=5)
        request.approval_ids.sudo().write({"date_requested": old_date})

        self.request_model._cron_remind_pending_approvals()
        self.assertTrue(
            all(request.approval_ids.mapped("date_reminder")),
            "Every pending approval must carry a reminder date.",
        )

    def test_pending_approval_reminder_respects_the_delay(self):
        """A recent approval is not reminded."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        self.company.ls_cc_approval_reminder_days = 30

        self.request_model._cron_remind_pending_approvals()
        self.assertFalse(any(request.approval_ids.mapped("date_reminder")))

    def test_pending_approval_reminder_can_be_disabled(self):
        """A reminder delay of zero disables the reminder."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        self.company.ls_cc_approval_reminder_days = 0
        old_date = fields.Date.context_today(request) - timedelta(days=90)
        request.approval_ids.sudo().write({"date_requested": old_date})

        self.request_model._cron_remind_pending_approvals()
        self.assertFalse(any(request.approval_ids.mapped("date_reminder")))

    def test_overdue_implementation_schedules_an_activity(self):
        """A late implementation produces an activity for the manager."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        # The planned date cannot precede the request date: plan it for
        # tomorrow and run the reminder a week later.
        tomorrow = fields.Date.context_today(request) + timedelta(days=1)
        request.with_user(self.user_manager).write(
            {"date_planned_implementation": tomorrow}
        )

        with freeze_time(tomorrow + timedelta(days=7)):
            self.request_model._cron_remind_overdue_implementations()
        self.assertTrue(
            request.activity_ids.filtered(
                lambda a: a.user_id == self.user_manager
            ),
            "An activity must be scheduled for the change control manager.",
        )

    def test_overdue_implementation_reminder_is_not_duplicated(self):
        """Running the reminder twice does not duplicate the activity."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        tomorrow = fields.Date.context_today(request) + timedelta(days=1)
        request.with_user(self.user_manager).write(
            {"date_planned_implementation": tomorrow}
        )

        with freeze_time(tomorrow + timedelta(days=7)):
            self.request_model._cron_remind_overdue_implementations()
            count_after_first = len(request.activity_ids)
            self.request_model._cron_remind_overdue_implementations()
        self.assertEqual(len(request.activity_ids), count_after_first)

    def test_due_verification_schedules_an_activity(self):
        """A due effectiveness verification produces an activity."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        action.with_user(self.user_manager).write({"evidence_reference": "EV-1"})
        action.with_user(self.user_requester).action_done()
        self.category.verification_delay = 1

        past = fields.Date.context_today(request) - timedelta(days=10)
        action.sudo().write({"date_done": past})
        self.assertEqual(request.date_actual_implementation, past)
        self.request_model._cron_remind_due_verifications()
        self.assertTrue(
            request.activity_ids,
            "An activity must be scheduled when the verification is due.",
        )

    def test_due_verification_is_skipped_when_already_completed(self):
        """No reminder is produced when a verification is completed."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        action.with_user(self.user_manager).write({"evidence_reference": "EV-1"})
        action.with_user(self.user_requester).action_done()
        verification = self._add_verification(request)
        verification.with_user(self.user_manager).write({"conclusion": "Applied."})
        verification.with_user(self.user_requester).action_complete_effective()

        request.activity_ids.unlink()
        self.request_model._cron_remind_due_verifications()
        self.assertFalse(request.activity_ids)
