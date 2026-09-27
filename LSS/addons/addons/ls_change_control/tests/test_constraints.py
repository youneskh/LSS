# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the data integrity constraints of the change request."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestConstraints(ChangeControlCommon):
    """Verify the Python constraints and the write protections."""

    def test_temporary_change_requires_an_end_date(self):
        """A temporary change must declare when it ends."""
        with self.assertRaises(ValidationError):
            self._create_request(
                user=self.user_requester, change_type="temporary"
            )

    def test_permanent_change_refuses_an_end_date(self):
        """A permanent change must not declare an end date."""
        with self.assertRaises(ValidationError):
            self._create_request(
                user=self.user_requester,
                change_type="permanent",
                temporary_end_date="2027-01-01",
            )

    def test_temporary_change_with_end_date_is_accepted(self):
        """A well formed temporary change is accepted."""
        request = self._create_request(
            user=self.user_requester,
            change_type="temporary",
            temporary_end_date="2027-01-01",
        )
        self.assertEqual(request.change_type, "temporary")

    def test_planning_dates_cannot_precede_the_request(self):
        """A target date in the past is refused."""
        with self.assertRaises(ValidationError):
            self._create_request(
                user=self.user_requester, date_required="2000-01-01"
            )

    def test_requester_must_be_internal(self):
        """A portal user cannot be the requester."""
        from odoo.tests.common import new_test_user

        portal_user = new_test_user(
            self.env, login="ls_cc_portal_req", groups="base.group_portal"
        )
        with self.assertRaises(ValidationError):
            self._create_request(
                user=self.user_manager, requester_id=portal_user.id
            )

    def test_only_draft_requests_may_be_archived(self):
        """Archiving a submitted request is refused."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_manager).write({"active": False})
        self.assertFalse(request.active)

        other = self._create_request(user=self.user_requester)
        other.with_user(self.user_requester).action_submit_review()
        with self.assertRaises(ValidationError):
            other.with_user(self.user_manager).write({"active": False})

    def test_system_fields_cannot_be_written_directly(self):
        """A direct write on a workflow field is refused."""
        request = self._create_request(user=self.user_requester)
        for values in (
            {"state": "approved"},
            {"date_approved": "2026-01-01 00:00:00"},
            {"closure_statement": "Forged closure."},
            {"rejection_reason": "Forged rejection."},
        ):
            with self.assertRaises(AccessError):
                request.with_user(self.user_manager).write(values)

    def test_content_fields_are_frozen_after_submission(self):
        """The description of the change is frozen once submitted."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        for values in (
            {"title": "Rewritten title"},
            {"justification": "Rewritten justification."},
            {"current_situation": "Rewritten situation."},
            {"proposed_change": "Rewritten change."},
            {"category_id": self.category.id},
            {"change_type": "temporary"},
        ):
            with self.assertRaises(UserError):
                request.with_user(self.user_manager).write(values)

    def test_content_fields_are_editable_in_draft(self):
        """A draft request remains fully editable by its requester."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).write({"title": "New title"})
        self.assertEqual(request.title, "New title")

    def test_only_managers_may_modify_a_submitted_request(self):
        """A requester cannot modify a request after submission."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        with self.assertRaises(AccessError):
            request.with_user(self.user_requester).write(
                {"classification": "critical"}
            )
        request.with_user(self.user_manager).write({"classification": "critical"})
        self.assertEqual(request.classification, "critical")

    def test_submitted_requests_cannot_be_deleted(self):
        """A submitted request is retained and never deleted."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).unlink()

    def test_draft_requests_may_be_deleted_by_a_manager(self):
        """A draft request carries no decision and may be deleted."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_manager).unlink()
        self.assertFalse(request.exists())

    def test_verification_planned_date_uses_the_category_delay(self):
        """The planned verification date applies the category delay."""
        from datetime import timedelta

        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        action.with_user(self.user_manager).write({"evidence_reference": "EV-1"})
        action.with_user(self.user_requester).action_done()
        self.assertEqual(
            request.date_verification_planned,
            request.date_actual_implementation + timedelta(days=15),
        )
