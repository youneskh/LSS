# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for certification issuance, expiry and revocation."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingCertification(LsTrainingCommon):
    """Certification lifecycle and expiry semantics."""

    def _create_certification(self, course=None, date_granted=None):
        """Create a manual certification for the fixture employee."""
        values = {
            "employee_id": self.employee.id,
            "course_id": (course or self.course).id,
            "company_id": self.company.id,
        }
        if date_granted:
            values["date_granted"] = date_granted
        return self.env["ls.training.certification"].create(values)

    def test_reference_generated(self):
        """A certification receives its reference from the sequence."""
        certification = self._create_certification()
        self.assertTrue(certification.name.startswith("TRN/CER/"))

    def test_course_version_frozen_on_creation(self):
        """The course version is copied at issuance time."""
        certification = self._create_certification()
        self.assertEqual(certification.course_version, "1.0")
        self.course.write({"version": "2.0"})
        certification.invalidate_recordset()
        self.assertEqual(certification.course_version, "1.0")

    def test_expiry_derived_from_course_validity(self):
        """The expiry date follows the course validity period."""
        certification = self._create_certification()
        expected = certification.date_granted + relativedelta(months=12)
        self.assertEqual(certification.date_expiry, expected)

    def test_no_expiry_when_validity_is_zero(self):
        """A course without validity yields a non-expiring certification."""
        certification = self._create_certification(
            course=self.course_no_expiry
        )
        self.assertFalse(certification.date_expiry)
        self.assertEqual(certification.state, "valid")

    def test_expiry_can_be_overridden(self):
        """The computed expiry date remains manually editable."""
        certification = self._create_certification()
        override = fields.Date.today() + relativedelta(months=1)
        certification.write({"date_expiry": override})
        self.assertEqual(certification.date_expiry, override)

    def test_state_valid(self):
        """A certification far from expiry is valid."""
        certification = self._create_certification()
        self.assertEqual(certification.state, "valid")

    def test_state_expiring(self):
        """A certification inside the warning window is expiring."""
        certification = self._create_certification()
        certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=10)}
        )
        self.assertEqual(certification.state, "expiring")

    def test_state_expired(self):
        """A certification past its expiry date is expired."""
        certification = self._create_certification()
        certification.write(
            {
                "date_granted": fields.Date.today() - relativedelta(days=400),
                "date_expiry": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertEqual(certification.state, "expired")

    def test_days_to_expiry(self):
        """The remaining validity is reported in days."""
        certification = self._create_certification()
        certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=15)}
        )
        self.assertEqual(certification.days_to_expiry, 15)

    def test_warning_window_from_parameter(self):
        """The warning window is read from the system parameter."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_training.expiry_warning_days", "90"
        )
        certification = self._create_certification()
        certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=60)}
        )
        self.assertEqual(certification.state, "expiring")

    def test_invalid_parameter_falls_back_to_default(self):
        """A non-numeric parameter falls back to the module default."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_training.expiry_warning_days", "not-a-number"
        )
        model = self.env["ls.training.certification"]
        self.assertEqual(model._get_expiry_warning_days(), 30)

    def test_negative_parameter_falls_back_to_default(self):
        """A negative parameter falls back to the module default."""
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_training.expiry_warning_days", "-5"
        )
        model = self.env["ls.training.certification"]
        self.assertEqual(model._get_expiry_warning_days(), 30)

    def test_expiry_before_grant_rejected(self):
        """A certification cannot expire before it was granted."""
        certification = self._create_certification()
        with self.assertRaises(ValidationError):
            certification.write({"date_expiry": "2000-01-01"})

    def test_score_bounds(self):
        """The score must remain a valid percentage."""
        certification = self._create_certification()
        with self.assertRaises(ValidationError):
            certification.write({"score": 150.0})

    def test_revocation_requires_reason(self):
        """Revoking without a documented reason is rejected."""
        certification = self._create_certification()
        with self.assertRaises(ValidationError):
            certification.write({"revoked": True})

    def test_revocation_with_reason(self):
        """A justified revocation sets the terminal status."""
        certification = self._create_certification()
        certification.write(
            {
                "revocation_reason": "Training material found deficient.",
                "revoked": True,
            }
        )
        self.assertEqual(certification.state, "revoked")

    def test_action_confirm_revoke(self):
        """The revocation dialog applies the revocation."""
        certification = self._create_certification()
        certification.write({"revocation_reason": "Retraining required."})
        certification.action_confirm_revoke()
        self.assertTrue(certification.revoked)
        self.assertEqual(certification.state, "revoked")

    def test_action_confirm_revoke_without_reason(self):
        """The revocation dialog refuses an empty reason."""
        certification = self._create_certification()
        with self.assertRaises(UserError):
            certification.action_confirm_revoke()

    def test_action_revoke_on_revoked_record(self):
        """Revoking twice raises a user error."""
        certification = self._create_certification()
        certification.write({"revocation_reason": "Reason."})
        certification.action_confirm_revoke()
        with self.assertRaises(UserError):
            certification.action_revoke()

    def test_certifications_cannot_be_deleted(self):
        """Certifications are permanent quality evidence."""
        certification = self._create_certification()
        with self.assertRaises(UserError):
            certification.unlink()

    def test_renewal_keeps_history(self):
        """Renewal adds a record instead of overwriting the previous one."""
        first = self._create_certification(
            date_granted=fields.Date.today() - relativedelta(months=13)
        )
        second = self._create_certification()
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.state, "expired")
        self.assertEqual(second.state, "valid")

    def test_display_name(self):
        """The display name carries reference, employee and course."""
        certification = self._create_certification()
        self.assertIn(certification.name, certification.display_name)
        self.assertIn(self.employee.name, certification.display_name)
