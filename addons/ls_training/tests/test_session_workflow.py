# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the session state machine and attendance evidence."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingSessionWorkflow(LsTrainingCommon):
    """Session lifecycle, attendance rules and certification issuance."""

    def test_reference_generated_from_sequence(self):
        """A session receives its reference from the sequence."""
        self.assertTrue(self.session.name.startswith("TRN/SES/"))

    def test_end_must_follow_start(self):
        """A session ending before it starts is rejected."""
        with self.assertRaises(ValidationError):
            self.session.write({"date_end": "2026-05-01 08:00:00"})

    def test_single_trainer_only(self):
        """Naming both an internal and an external trainer is rejected."""
        with self.assertRaises(ValidationError):
            self.session.write({"trainer_external": "External Provider"})

    def test_capacity_enforced(self):
        """Registrations beyond the capacity are rejected."""
        self.session.write({"capacity": 1})
        self._create_attendance(self.session, self.employee)
        with self.assertRaises(ValidationError):
            self._create_attendance(self.session, self.employee_two)

    def test_duplicate_registration_rejected(self):
        """One employee cannot be registered twice on a session."""
        self._create_attendance(self.session, self.employee)
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self._create_attendance(self.session, self.employee)

    def test_confirm_requires_attendees(self):
        """A session without attendees cannot be confirmed."""
        with self.assertRaises(UserError):
            self.session.action_confirm()

    def test_full_workflow_issues_certification(self):
        """Closing a session issues certifications to passing attendees."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        self.assertEqual(self.session.state, "done")
        certification = self.env["ls.training.certification"].search(
            [("session_id", "=", self.session.id)]
        )
        self.assertEqual(len(certification), 1)
        self.assertEqual(certification.employee_id, self.employee)
        self.assertEqual(certification.course_version, self.course.version)

    def test_failing_attendee_gets_no_certification(self):
        """An attendee below the pass score receives no certification."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._create_attendance(
            self.session, self.employee_two, attended=True, score=40.0
        )
        self._run_session_to_done(self.session)
        certifications = self.env["ls.training.certification"].search(
            [("session_id", "=", self.session.id)]
        )
        self.assertEqual(len(certifications), 1)
        self.assertEqual(certifications.employee_id, self.employee)

    def test_close_blocked_by_pending_attendance(self):
        """A pending outcome prevents closing the session."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._create_attendance(
            self.session, self.employee_two, attended=False
        )
        self.session.action_confirm()
        self.session.action_start()
        with self.assertRaises(UserError):
            self.session.action_close()

    def test_result_pending_when_absent(self):
        """An absent attendee stays pending rather than failing."""
        attendance = self._create_attendance(
            self.session, self.employee, attended=False, score=95.0
        )
        self.assertEqual(attendance.result, "pending")

    def test_result_passed_without_assessment(self):
        """Attendance alone passes a course without assessment."""
        session = self.env["ls.training.session"].create(
            {
                "course_id": self.course_no_expiry.id,
                "date_start": "2026-06-02 08:00:00",
                "date_end": "2026-06-02 09:00:00",
            }
        )
        attendance = self._create_attendance(
            session, self.employee, attended=True
        )
        self.assertEqual(attendance.result, "passed")

    def test_result_recomputed_on_score_change(self):
        """Changing the score re-derives the outcome."""
        attendance = self._create_attendance(
            self.session, self.employee, attended=True, score=50.0
        )
        self.assertEqual(attendance.result, "failed")
        attendance.write({"score": 85.0})
        self.assertEqual(attendance.result, "passed")

    def test_score_bounds(self):
        """A score outside 0 to 100 is rejected."""
        attendance = self._create_attendance(self.session, self.employee)
        with self.assertRaises(ValidationError):
            attendance.write({"score": 101.0})

    def test_attendee_company_must_match(self):
        """An employee of another company cannot attend the session."""
        foreign_employee = self.env["hr.employee"].create(
            {
                "name": "Foreign Employee",
                "company_id": self.other_company.id,
            }
        )
        with self.assertRaises(ValidationError):
            self._create_attendance(self.session, foreign_employee)

    def test_cannot_register_on_closed_session(self):
        """Adding an attendee to a closed session is rejected."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        with self.assertRaises(UserError):
            self._create_attendance(self.session, self.employee_two)

    def test_attendance_frozen_after_close(self):
        """Attendance evidence is read-only once the session is closed."""
        attendance = self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        with self.assertRaises(UserError):
            attendance.write({"score": 10.0})

    def test_attendance_of_closed_session_not_deletable(self):
        """Attendance of a closed session cannot be deleted."""
        attendance = self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        with self.assertRaises(UserError):
            attendance.unlink()

    def test_closed_session_header_is_immutable(self):
        """Course, dates and trainer are frozen after closing."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        with self.assertRaises(UserError):
            self.session.write({"date_start": "2026-01-01 08:00:00"})

    def test_closed_session_cannot_be_cancelled(self):
        """A closed session is terminal."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        with self.assertRaises(UserError):
            self.session.action_cancel()

    def test_start_requires_confirmed(self):
        """Starting a draft session is rejected."""
        with self.assertRaises(UserError):
            self.session.action_start()

    def test_close_requires_in_progress(self):
        """Closing a draft session is rejected."""
        with self.assertRaises(UserError):
            self.session.action_close()

    def test_cancel_and_reset_to_draft(self):
        """A cancelled session can be returned to draft."""
        self.session.action_cancel()
        self.assertEqual(self.session.state, "cancelled")
        self.session.action_reset_to_draft()
        self.assertEqual(self.session.state, "draft")

    def test_reset_to_draft_requires_cancelled(self):
        """Only a cancelled session can be reset."""
        with self.assertRaises(UserError):
            self.session.action_reset_to_draft()

    def test_confirmed_session_cannot_be_deleted(self):
        """Deleting a confirmed session is rejected."""
        self._create_attendance(self.session, self.employee)
        self.session.action_confirm()
        with self.assertRaises(UserError):
            self.session.unlink()

    def test_draft_session_can_be_deleted(self):
        """A draft session may be removed."""
        session = self.env["ls.training.session"].create(
            {
                "course_id": self.course.id,
                "date_start": "2026-07-01 08:00:00",
                "date_end": "2026-07-01 12:00:00",
            }
        )
        session.unlink()
        self.assertFalse(session.exists())

    def test_attendance_statistics(self):
        """Registered, passed and failed counters are consistent."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._create_attendance(
            self.session, self.employee_two, attended=True, score=10.0
        )
        self.assertEqual(self.session.attendee_count, 2)
        self.assertEqual(self.session.passed_count, 1)
        self.assertEqual(self.session.failed_count, 1)

    def test_onchange_course_sets_end_date(self):
        """Selecting a course proposes an end date from its duration."""
        session = self.env["ls.training.session"].new(
            {
                "course_id": self.course.id,
                "date_start": "2026-06-01 08:00:00",
            }
        )
        session._onchange_course_id()
        self.assertTrue(session.date_end)

    def test_mark_attended_helpers(self):
        """The bulk attendance helpers update the records."""
        attendance = self._create_attendance(
            self.session, self.employee, attended=False
        )
        attendance.action_mark_attended()
        self.assertTrue(attendance.attended)
        attendance.action_mark_absent()
        self.assertFalse(attendance.attended)
        self.assertEqual(attendance.score, 0.0)
