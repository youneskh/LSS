# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the root cause analysis model."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaRootCause(CapaCommon):
    """Analysis methods, computed RPN and confirmation lifecycle."""

    def test_sequence_allocated(self):
        """A root cause analysis receives a reference from the sequence."""
        root_cause = self._make_root_cause(self._make_issue())
        self.assertTrue(root_cause.name.startswith("RCA/"))

    def test_default_state_is_draft(self):
        """A new analysis starts in Draft."""
        self.assertEqual(
            self._make_root_cause(self._make_issue()).state, "draft"
        )

    def test_confirm_sets_state(self):
        """Confirming moves the analysis to Confirmed."""
        root_cause = self._make_root_cause(self._make_issue())
        root_cause.action_confirm()
        self.assertEqual(root_cause.state, "confirmed")

    def test_confirm_twice_is_blocked(self):
        """A confirmed analysis cannot be confirmed again."""
        root_cause = self._make_root_cause(self._make_issue())
        root_cause.action_confirm()
        with self.assertRaises(UserError):
            root_cause.action_confirm()

    def test_reset_to_draft(self):
        """A confirmed analysis can return to Draft before execution."""
        root_cause = self._make_root_cause(self._make_issue())
        root_cause.action_confirm()
        root_cause.action_reset_to_draft()
        self.assertEqual(root_cause.state, "draft")

    def test_reset_blocked_after_execution_started(self):
        """Reset is refused once the CAPA started execution."""
        issue = self._make_issue()
        self._advance_to_in_progress(issue)
        with self.assertRaises(UserError):
            issue.root_cause_ids.action_reset_to_draft()

    def test_five_whys_requires_first_why(self):
        """A Five Whys analysis must document the first Why."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            self._make_root_cause(issue, why_1=False)

    def test_ishikawa_requires_category(self):
        """An Ishikawa analysis must name a diagram category."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            self.env["ls.capa.root_cause"].create(
                {
                    "issue_id": issue.id,
                    "method": "ishikawa",
                    "description": "Operator training gap.",
                }
            )

    def test_ishikawa_accepts_category(self):
        """An Ishikawa analysis with a category is accepted."""
        issue = self._make_issue()
        root_cause = self.env["ls.capa.root_cause"].create(
            {
                "issue_id": issue.id,
                "method": "ishikawa",
                "description": "Operator training gap.",
                "ishikawa_category": "man",
            }
        )
        self.assertEqual(root_cause.ishikawa_category, "man")

    def test_fmea_rpn_computed(self):
        """The RPN is the product of severity, occurrence and detection."""
        issue = self._make_issue()
        root_cause = self.env["ls.capa.root_cause"].create(
            {
                "issue_id": issue.id,
                "method": "fmea",
                "description": "Seal integrity failure mode.",
                "fmea_severity": 7,
                "fmea_occurrence": 3,
                "fmea_detection": 2,
            }
        )
        self.assertEqual(root_cause.fmea_rpn, 42)

    def test_fmea_rpn_zero_for_other_methods(self):
        """Non-FMEA analyses report a zero RPN."""
        self.assertEqual(
            self._make_root_cause(self._make_issue()).fmea_rpn, 0
        )

    def test_fmea_rating_out_of_range_rejected(self):
        """FMEA ratings outside the 1 to 10 scale are rejected."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            self.env["ls.capa.root_cause"].create(
                {
                    "issue_id": issue.id,
                    "method": "fmea",
                    "description": "Invalid rating.",
                    "fmea_severity": 11,
                    "fmea_occurrence": 3,
                    "fmea_detection": 2,
                }
            )

    def test_fmea_rating_zero_rejected(self):
        """A zero FMEA rating is rejected."""
        issue = self._make_issue()
        with self.assertRaises(ValidationError):
            self.env["ls.capa.root_cause"].create(
                {
                    "issue_id": issue.id,
                    "method": "fmea",
                    "description": "Invalid rating.",
                    "fmea_severity": 5,
                    "fmea_occurrence": 0,
                    "fmea_detection": 2,
                }
            )

    def test_company_propagated_from_issue(self):
        """The company is inherited from the parent CAPA."""
        issue = self._make_issue()
        root_cause = self._make_root_cause(issue)
        self.assertEqual(root_cause.company_id, issue.company_id)

    def test_cascade_delete_with_issue(self):
        """Deleting a CAPA removes its root cause analyses."""
        issue = self._make_issue()
        root_cause = self._make_root_cause(issue)
        issue.unlink()
        self.assertFalse(root_cause.exists())
