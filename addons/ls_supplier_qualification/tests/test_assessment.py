# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the assessment scoring engine and workflow."""
from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestAssessment(SupplierQualificationCommon):
    """Cover scoring, thresholds, freezing of rules and the workflow."""

    def setUp(self):
        """Create a draft assessment for each test."""
        super().setUp()
        self.assessment = self.env["ls.supplier.assessment"].create({
            "qualification_id": self.qualification.id,
            "template_id": self.template.id,
            "assessor_id": self.user_assessor.id,
        })

    def test_rules_frozen_from_template(self):
        """The scoring rules are copied from the template at creation."""
        self.assertEqual(self.assessment.max_score_per_criterion, 5)
        self.assertEqual(self.assessment.mandatory_min_score, 3)
        self.assertEqual(self.assessment.pass_threshold, 80.0)
        self.template.pass_threshold = 95.0
        self.assessment.invalidate_recordset()
        self.assertEqual(self.assessment.pass_threshold, 80.0)

    def test_load_template_creates_lines(self):
        """Loading the template copies its criteria onto the assessment."""
        self.assessment.action_load_template()
        self.assertEqual(len(self.assessment.line_ids), 2)
        mandatory = self.assessment.line_ids.filtered("is_mandatory")
        self.assertEqual(mandatory.criterion_id, self.criterion_mandatory)
        self.assertEqual(mandatory.weight, 2.0)

    def test_cannot_start_without_lines(self):
        """An assessment without criteria cannot be started."""
        with self.assertRaises(UserError):
            self.assessment.action_start()

    def test_weighted_score_and_pass_result(self):
        """Full scores produce 100 % and a Pass result."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        self.assessment.line_ids.write({"score": 5})
        self.assertEqual(self.assessment.total_weighted_score, 15.0)
        self.assertEqual(self.assessment.total_max_weighted_score, 15.0)
        self.assertEqual(self.assessment.score_percent, 100.0)
        self.assertEqual(self.assessment.result, "pass")

    def test_conditional_result_between_thresholds(self):
        """A score between the two thresholds produces a Conditional result."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        for line in self.assessment.line_ids:
            line.score = 4 if line.is_mandatory else 2
        # (4*2 + 2*1) / (5*2 + 5*1) = 10 / 15 = 66.67 %
        self.assertEqual(self.assessment.score_percent, 66.67)
        self.assertEqual(self.assessment.result, "conditional")

    def test_failed_mandatory_criterion_forces_fail(self):
        """A mandatory criterion below the minimum forces a Fail result."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        for line in self.assessment.line_ids:
            line.score = 2 if line.is_mandatory else 5
        self.assertEqual(self.assessment.mandatory_failed_count, 1)
        self.assertEqual(self.assessment.result, "fail")

    def test_score_cannot_exceed_scale(self):
        """A score above the frozen scale is rejected."""
        self.assessment.action_load_template()
        with self.assertRaises(ValidationError):
            self.assessment.line_ids[0].score = 9

    def test_low_score_requires_comment(self):
        """Completing requires a comment on every low-scored criterion."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        self.assessment.line_ids.write({"score": 1})
        self.assessment.conclusion = "Conclusion."
        with self.assertRaises(UserError):
            self.assessment.action_done()

    def test_conclusion_required_before_completion(self):
        """Completing requires a written conclusion."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        self.assessment.line_ids.write({"score": 5})
        with self.assertRaises(UserError):
            self.assessment.action_done()

    def test_completion_creates_signature_entry(self):
        """Completing an assessment appends an authored signature entry."""
        before = self.env["ls.supplier.signature"].search_count([])
        self._create_assessment(self.qualification)
        after = self.env["ls.supplier.signature"].search_count([])
        self.assertEqual(after, before + 1)

    def test_review_requires_second_person(self):
        """With segregation of duties, the assessor cannot review."""
        assessment = self._create_assessment(
            self.qualification, assessor=self.user_assessor
        )
        with self.assertRaises(UserError):
            assessment.with_user(self.user_assessor).action_review()
        assessment.with_user(self.user_assessor_two).action_review()
        self.assertEqual(assessment.state, "reviewed")
        self.assertEqual(assessment.reviewer_id, self.user_assessor_two)

    def test_review_allowed_when_sod_disabled(self):
        """Disabling the company flag allows a self-review."""
        self.company.ls_enforce_sod = False
        assessment = self._create_assessment(
            self.qualification, assessor=self.user_assessor
        )
        assessment.with_user(self.user_assessor).action_review()
        self.assertEqual(assessment.state, "reviewed")

    def test_reviewed_assessment_cannot_be_cancelled(self):
        """A reviewed assessment is final."""
        assessment = self._create_assessment(self.qualification)
        assessment.with_user(self.user_assessor_two).action_review()
        with self.assertRaises(UserError):
            assessment.action_cancel()

    def test_started_assessment_cannot_be_deleted(self):
        """Deleting a started assessment is refused."""
        self.assessment.action_load_template()
        self.assessment.action_start()
        with self.assertRaises(UserError):
            self.assessment.unlink()

    def test_criterion_unique_per_assessment(self):
        """The same criterion cannot be scored twice in one assessment."""
        self.assessment.action_load_template()
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.supplier.assessment.line"].create({
                "assessment_id": self.assessment.id,
                "criterion_id": self.criterion_mandatory.id,
                "weight": 1.0,
            })
            self.env.flush_all()

    def test_latest_assessment_exposed_on_dossier(self):
        """The dossier exposes the latest concluded assessment."""
        assessment = self._create_assessment(self.qualification)
        self.qualification.invalidate_recordset()
        self.assertEqual(
            self.qualification.latest_assessment_id, assessment
        )
        self.assertEqual(self.qualification.latest_assessment_result, "pass")
