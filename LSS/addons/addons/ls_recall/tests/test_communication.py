# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for recall communications and their content confirmations."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestCommunication(RecallCommon):
    """A notice cannot be issued until its content has been confirmed."""

    def test_reference_allocated(self):
        """A communication receives a reference on creation."""
        execution = self._create_execution()
        communication = self._create_communication(execution)
        self.assertTrue(communication.name.startswith("RCC/"))

    def test_recipient_required(self):
        """A directed communication must have a recipient."""
        execution = self._create_execution()
        with self.assertRaises(ValidationError):
            self._create_communication(execution, partner_ids=[(5, 0, 0)])

    def test_public_warning_needs_no_recipient(self):
        """A public warning is addressed through the media."""
        execution = self._create_execution()
        communication = self._create_communication(
            execution,
            communication_type="public_warning",
            partner_ids=[(5, 0, 0)],
        )
        self.assertEqual(communication.recipient_count, 0)

    def test_approval_requires_content_confirmations(self):
        """An unconfirmed notice cannot be approved."""
        execution = self._create_execution()
        communication = self._create_communication(
            execution, content_gives_instructions=False
        )
        self.assertFalse(communication.content_complete)
        with self.assertRaises(UserError):
            communication.action_approve()

    def test_approval_requires_a_body(self):
        """An empty notice cannot be approved."""
        execution = self._create_execution()
        communication = self._create_communication(execution, body=False)
        with self.assertRaises(UserError):
            communication.action_approve()

    def test_cannot_send_before_approval(self):
        """Sending is only possible after approval."""
        execution = self._create_execution()
        communication = self._create_communication(execution)
        with self.assertRaises(UserError):
            communication.action_mark_sent()

    def test_send_marks_consignees_notified(self):
        """Recipients' consignee lines are flagged as notified."""
        execution = self._create_execution()
        line = self._add_line(execution, self.partner_a, self.lot_1, 10.0)
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        self.assertTrue(line.notified)
        self.assertTrue(line.notification_date)
        self.assertEqual(communication.sent_by_user_id, self.env.user)

    def test_authority_notification_updates_the_recall(self):
        """Notifying an authority is reflected on the recall header."""
        execution = self._create_execution()
        communication = self._create_communication(
            execution,
            communication_type="authority_notification",
            partner_ids=[(6, 0, [self.partner_authority.id])],
        )
        communication.action_approve()
        communication.action_mark_sent()
        self.assertTrue(execution.authority_notified)
        self.assertTrue(execution.authority_notification_date)

    def test_sent_communication_is_frozen(self):
        """A sent notice cannot be reworded."""
        execution = self._create_execution()
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        with self.assertRaises(UserError):
            communication.subject = "Reworded after sending"

    def test_sent_communication_cannot_be_cancelled_or_deleted(self):
        """A sent notice stays on the record."""
        execution = self._create_execution()
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        with self.assertRaises(UserError):
            communication.action_cancel()
        with self.assertRaises(UserError):
            communication.unlink()

    def test_first_communication_metrics(self):
        """The delay between decision and first notice is computed."""
        execution = self._create_execution(
            decision_date="2026-06-01 08:00:00"
        )
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        self.assertTrue(execution.first_communication_date)
        self.assertGreater(execution.initiation_delay_hours, 0.0)

    def test_status_update_needs_no_content_confirmation(self):
        """Only notices carry the mandatory content confirmations."""
        execution = self._create_execution()
        communication = self._create_communication(
            execution,
            communication_type="status_update",
            content_identifies_product=False,
            content_states_reason=False,
            content_gives_instructions=False,
            content_requests_response=False,
            content_gives_contact=False,
        )
        communication.action_approve()
        self.assertEqual(communication.state, "approved")
