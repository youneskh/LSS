# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the effectiveness verification model."""

from datetime import timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaEffectiveness(CapaCommon):
    """Verification lifecycle, conclusions and follow-up escalation."""

    def test_sequence_allocated(self):
        """An effectiveness check receives a reference from the sequence."""
        check = self._make_effectiveness(self._make_issue())
        self.assertTrue(check.name.startswith("CAPA-EFF/"))

    def test_default_result_pending(self):
        """A new check starts with a Pending result."""
        check = self._make_effectiveness(self._make_issue())
        self.assertEqual(check.result, "pending")
        self.assertEqual(check.state, "draft")

    def test_plan_moves_to_planned(self):
        """Planning a draft check moves it to Planned."""
        check = self._make_effectiveness(self._make_issue())
        check.action_plan()
        self.assertEqual(check.state, "planned")

    def test_plan_blocked_when_not_draft(self):
        """Only draft checks can be planned."""
        check = self._make_effectiveness(self._make_issue())
        check.action_plan()
        with self.assertRaises(UserError):
            check.action_plan()

    def test_conclude_requires_conclusion(self):
        """A conclusion is mandatory before completing a check."""
        check = self._make_effectiveness(self._make_issue())
        with self.assertRaises(UserError):
            check.action_mark_effective()

    def test_mark_effective(self):
        """Concluding Effective stamps the verification date."""
        check = self._make_effectiveness(self._make_issue())
        check.conclusion = "No recurrence across twenty batches."
        check.action_mark_effective()
        self.assertEqual(check.result, "effective")
        self.assertEqual(check.state, "done")
        self.assertEqual(check.date_check, self.today)

    def test_mark_not_effective(self):
        """Concluding Not Effective is recorded."""
        check = self._make_effectiveness(self._make_issue())
        check.conclusion = "Recurrence observed on batch B-2500."
        check.action_mark_not_effective()
        self.assertEqual(check.result, "not_effective")

    def test_conclude_twice_blocked(self):
        """A completed check cannot be concluded again."""
        check = self._make_effectiveness(self._make_issue())
        check.conclusion = "No recurrence."
        check.action_mark_effective()
        with self.assertRaises(UserError):
            check.action_mark_not_effective()

    def test_done_state_requires_decided_result(self):
        """A completed check cannot keep a Pending result."""
        check = self._make_effectiveness(self._make_issue())
        with self.assertRaises(ValidationError):
            check.write({"state": "done", "conclusion": "Reviewed."})

    def test_planned_before_identification_rejected(self):
        """A check cannot be planned before the CAPA was identified."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            self._make_effectiveness(
                issue, date_planned=issue.date_identified - timedelta(days=1)
            )

    def test_followup_requires_not_effective(self):
        """A follow-up CAPA needs a Not Effective conclusion."""
        check = self._make_effectiveness(self._make_issue())
        check.conclusion = "No recurrence."
        check.action_mark_effective()
        with self.assertRaises(UserError):
            check.action_create_followup_capa()

    def test_followup_creates_new_capa(self):
        """A Not Effective conclusion can raise a follow-up CAPA."""
        issue = self._make_issue()
        check = self._make_effectiveness(issue)
        check.conclusion = "Recurrence observed."
        check.action_mark_not_effective()
        result = check.action_create_followup_capa()
        self.assertTrue(check.new_capa_id)
        self.assertEqual(result["res_model"], "ls.capa.issue")
        self.assertEqual(check.new_capa_id.source_reference, issue.name)
        self.assertEqual(check.new_capa_id.severity, issue.severity)
        self.assertEqual(check.new_capa_id.state, "identified")

    def test_followup_twice_blocked(self):
        """Only one follow-up CAPA can be raised per check."""
        check = self._make_effectiveness(self._make_issue())
        check.conclusion = "Recurrence observed."
        check.action_mark_not_effective()
        check.action_create_followup_capa()
        with self.assertRaises(UserError):
            check.action_create_followup_capa()

    def test_cascade_delete_with_issue(self):
        """Deleting a CAPA removes its effectiveness checks."""
        issue = self._make_issue()
        check = self._make_effectiveness(issue)
        issue.unlink()
        self.assertFalse(check.exists())
