# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for competencies and competency assessments."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingCompetency(LsTrainingCommon):
    """Competency master data and assessment evidence."""

    def _create_assessment(self, level="proficient", evidence="Observed."):
        """Create a draft assessment for the fixture employee."""
        return self.env["ls.training.competency.assessment"].create(
            {
                "employee_id": self.employee.id,
                "competency_id": self.competency.id,
                "assessor_id": self.trainer.id,
                "level": level,
                "evidence": evidence,
                "company_id": self.company.id,
            }
        )

    def test_display_name_contains_code(self):
        """The competency display name is prefixed with its code."""
        self.assertTrue(
            self.competency.display_name.startswith("[CMP-DOC]")
        )

    def test_code_unique_per_company(self):
        """Competency codes are unique within a company."""
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.env["ls.training.competency"].create(
                    {
                        "name": "Duplicate",
                        "code": "CMP-DOC",
                        "company_id": self.company.id,
                    }
                )

    def test_negative_reassessment_interval_rejected(self):
        """A negative reassessment interval raises a validation error."""
        with self.assertRaises(ValidationError):
            self.competency.write({"reassessment_months": -1})

    def test_assessment_count(self):
        """The assessment counter reflects the recorded assessments."""
        self._create_assessment()
        self.competency.invalidate_recordset()
        self.assertEqual(self.competency.assessment_count, 1)

    def test_action_view_assessments(self):
        """The assessments button filters on the current competency."""
        action = self.competency.action_view_assessments()
        self.assertIn(
            ("competency_id", "=", self.competency.id), action["domain"]
        )

    def test_next_assessment_date_computed(self):
        """The next assessment date follows the competency interval."""
        assessment = self._create_assessment()
        self.assertTrue(assessment.date_next)
        self.assertGreater(
            assessment.date_next, assessment.date_assessment
        )

    def test_no_next_date_without_interval(self):
        """Without a reassessment interval no next date is proposed."""
        self.competency.write({"reassessment_months": 0})
        assessment = self._create_assessment()
        self.assertFalse(assessment.date_next)

    def test_is_acquired_true_when_level_sufficient(self):
        """Reaching the minimum level marks the competency acquired."""
        assessment = self._create_assessment(level="expert")
        self.assertTrue(assessment.is_acquired)

    def test_is_acquired_false_when_level_insufficient(self):
        """A level below the minimum does not grant the competency."""
        assessment = self._create_assessment(level="developing")
        self.assertFalse(assessment.is_acquired)

    def test_self_assessment_forbidden(self):
        """An employee cannot assess their own competency."""
        with self.assertRaises(ValidationError):
            self.env["ls.training.competency.assessment"].create(
                {
                    "employee_id": self.employee.id,
                    "competency_id": self.competency.id,
                    "assessor_id": self.employee.id,
                    "level": "proficient",
                }
            )

    def test_next_date_cannot_precede_assessment(self):
        """A next assessment date in the past is rejected."""
        assessment = self._create_assessment()
        with self.assertRaises(ValidationError):
            assessment.write({"date_next": "2000-01-01"})

    def test_duplicate_assessment_same_day_rejected(self):
        """One employee cannot be assessed twice per competency and day."""
        first = self._create_assessment()
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.env["ls.training.competency.assessment"].create(
                    {
                        "employee_id": self.employee.id,
                        "competency_id": self.competency.id,
                        "assessor_id": self.trainer.id,
                        "date_assessment": first.date_assessment,
                        "level": "expert",
                    }
                )

    def test_confirm_requires_evidence(self):
        """An assessment without evidence cannot be confirmed."""
        assessment = self._create_assessment(evidence=False)
        with self.assertRaises(UserError):
            assessment.action_confirm()

    def test_confirm_locks_the_record(self):
        """A confirmed assessment can no longer be edited."""
        assessment = self._create_assessment()
        assessment.action_confirm()
        self.assertEqual(assessment.state, "confirmed")
        with self.assertRaises(UserError):
            assessment.write({"level": "expert"})

    def test_confirmed_assessment_cannot_be_deleted(self):
        """Confirmed assessments are retained as evidence."""
        assessment = self._create_assessment()
        assessment.action_confirm()
        with self.assertRaises(UserError):
            assessment.unlink()

    def test_draft_assessment_can_be_deleted(self):
        """A draft assessment may still be removed."""
        assessment = self._create_assessment()
        assessment.unlink()
        self.assertFalse(assessment.exists())

    def test_double_confirm_rejected(self):
        """Confirming twice raises a user error."""
        assessment = self._create_assessment()
        assessment.action_confirm()
        with self.assertRaises(UserError):
            assessment.action_confirm()
