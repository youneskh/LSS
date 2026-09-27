# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Tests of the FMEA models."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged

from ..models import constants
from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskFmea(RiskCommon):
    """Verify RPN arithmetic, action thresholds and the approval workflow."""

    def setUp(self):
        """Create a worksheet with one failure mode for each test."""
        super().setUp()
        self.fmea = self._make_fmea()
        self.line = self._make_fmea_line(self.fmea, severity=5, occurrence=4, detection=3)

    def test_sequence_assigned(self):
        """A worksheet receives a reference from the sequence."""
        self.assertTrue(self.fmea.name.startswith("FMEA/"))

    def test_rpn_is_product(self):
        """The RPN is severity times occurrence times detection."""
        self.assertEqual(self.line.rpn, 60)

    def test_rpn_bounds_match_constants(self):
        """The lowest and highest achievable RPN match the constants."""
        low = self._make_fmea_line(self.fmea, severity=1, occurrence=1, detection=1)
        high = self._make_fmea_line(self.fmea, severity=10, occurrence=10, detection=10)
        self.assertEqual(low.rpn, constants.FMEA_RPN_MIN)
        self.assertEqual(high.rpn, constants.FMEA_RPN_MAX)

    def test_action_not_required_below_thresholds(self):
        """A line below both thresholds needs no action."""
        self.assertFalse(self.line.action_required)

    def test_action_required_above_rpn_threshold(self):
        """A line at or above the RPN threshold requires action."""
        line = self._make_fmea_line(self.fmea, severity=5, occurrence=5, detection=4)
        self.assertEqual(line.rpn, 100)
        self.assertTrue(line.action_required)

    def test_action_required_by_severity_alone(self):
        """A high severity requires action regardless of the RPN."""
        line = self._make_fmea_line(self.fmea, severity=9, occurrence=1, detection=1)
        self.assertEqual(line.rpn, 9)
        self.assertTrue(line.action_required)

    def test_threshold_change_recomputes_lines(self):
        """Lowering the worksheet threshold re-flags existing lines."""
        self.assertFalse(self.line.action_required)
        self.fmea.rpn_threshold = 50
        self.assertTrue(self.line.action_required)

    def test_revised_rpn_and_reduction(self):
        """The revised RPN and the reduction are computed together."""
        self.line.write(
            {
                "revised_severity": 5,
                "revised_occurrence": 2,
                "revised_detection": 2,
            }
        )
        self.assertEqual(self.line.revised_rpn, 20)
        self.assertEqual(self.line.rpn_reduction, 40)

    def test_revised_rpn_zero_when_incomplete(self):
        """No revised RPN is produced while ratings are absent."""
        self.assertEqual(self.line.revised_rpn, 0)
        self.assertEqual(self.line.rpn_reduction, 0)

    def test_revised_ratings_must_be_complete(self):
        """Partial revised ratings are rejected."""
        with self.assertRaises(ValidationError):
            self.line.revised_severity = 3

    def test_rating_upper_bound_enforced(self):
        """A rating above the scale maximum is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self._make_fmea_line(self.fmea, severity=11)
            self.env.flush_all()

    def test_rating_lower_bound_enforced(self):
        """A rating below the scale minimum is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self._make_fmea_line(self.fmea, occurrence=0)
            self.env.flush_all()

    def test_statistics_aggregate_lines(self):
        """Worksheet statistics aggregate the failure mode rows."""
        self._make_fmea_line(self.fmea, severity=10, occurrence=5, detection=4)
        self.assertEqual(self.fmea.line_count, 2)
        self.assertEqual(self.fmea.max_rpn, 200)
        self.assertEqual(self.fmea.action_required_count, 1)

    def test_submit_requires_lines(self):
        """An empty worksheet cannot be submitted for review."""
        empty = self._make_fmea(title="Empty FMEA")
        empty.action_start()
        with self.assertRaises(UserError):
            empty.action_submit_review()

    def test_review_blocks_facilitator(self):
        """The facilitator cannot review their own worksheet."""
        fmea = self._make_fmea(user=self.user_manager)
        self._make_fmea_line(fmea)
        fmea.action_start()
        fmea.action_submit_review()
        with self.assertRaises(UserError):
            fmea.with_user(self.user_manager).action_review()

    def test_review_requires_manager_role(self):
        """An analyst cannot record a review through the ORM."""
        self.fmea.action_start()
        self.fmea.action_submit_review()
        with self.assertRaises(AccessError):
            self.fmea.with_user(self.user_analyst).action_review()

    def test_approve_requires_review(self):
        """A worksheet must be reviewed before it is approved."""
        self.fmea.action_start()
        self.fmea.action_submit_review()
        with self.assertRaises(UserError):
            self.fmea.with_user(self.user_manager).action_approve()

    def test_approve_requires_recommended_actions(self):
        """Lines requiring action must carry a recommended action."""
        self._make_fmea_line(self.fmea, severity=10, occurrence=5, detection=4)
        self.fmea.action_start()
        self.fmea.action_submit_review()
        self.fmea.with_user(self.user_manager).action_review()
        with self.assertRaises(UserError):
            self.fmea.with_user(self.user_manager).action_approve()

    def test_full_approval_path(self):
        """A compliant worksheet reaches the approved state."""
        self.fmea.action_start()
        self.fmea.action_submit_review()
        self.fmea.with_user(self.user_manager).action_review()
        self.fmea.with_user(self.user_manager_two).action_approve()
        self.assertEqual(self.fmea.state, "approved")
        self.assertEqual(self.fmea.approved_by_id, self.user_manager_two)

    def test_close_requires_no_open_actions(self):
        """A worksheet with open required actions cannot be closed."""
        line = self._make_fmea_line(self.fmea, severity=10, occurrence=5, detection=4)
        line.write({"recommended_action": "Add detection.", "action_state": "open"})
        self.fmea.action_start()
        self.fmea.action_submit_review()
        self.fmea.with_user(self.user_manager).action_review()
        self.fmea.with_user(self.user_manager_two).action_approve()
        with self.assertRaises(UserError):
            self.fmea.with_user(self.user_manager).action_close()

    def test_close_succeeds_when_actions_complete(self):
        """A worksheet whose actions are complete can be closed."""
        line = self._make_fmea_line(self.fmea, severity=10, occurrence=5, detection=4)
        line.write(
            {
                "recommended_action": "Add detection.",
                "action_state": "completed",
                "actions_taken": "In-line check installed.",
            }
        )
        self.fmea.action_start()
        self.fmea.action_submit_review()
        self.fmea.with_user(self.user_manager).action_review()
        self.fmea.with_user(self.user_manager_two).action_approve()
        self.fmea.with_user(self.user_manager).action_close()
        self.assertEqual(self.fmea.state, "closed")

    def test_revision_creates_copy(self):
        """Creating a revision copies the worksheet and increments it."""
        self.fmea.action_start()
        self.fmea.action_submit_review()
        self.fmea.with_user(self.user_manager).action_review()
        self.fmea.with_user(self.user_manager_two).action_approve()
        self.fmea.action_create_revision()
        new = self.env["ls.risk.fmea"].search(
            [("title", "=", self.fmea.title), ("revision", "=", 2)], limit=1
        )
        self.assertTrue(new)
        self.assertEqual(new.state, "draft")
        self.assertFalse(new.approved_by_id)
        self.assertEqual(len(new.line_ids), len(self.fmea.line_ids))

    def test_revision_requires_approved(self):
        """A draft worksheet cannot be revised."""
        with self.assertRaises(UserError):
            self.fmea.action_create_revision()

    def test_create_risk_from_line(self):
        """A failure mode can raise a risk register entry."""
        self.line.action_create_risk()
        self.assertTrue(self.line.risk_id)
        self.assertEqual(self.line.risk_id.matrix_id, self.matrix)
        self.assertEqual(self.line.risk_id.risk_type, "process")
        self.assertEqual(self.line.risk_id.hazard, self.line.failure_mode)

    def test_create_risk_is_not_repeatable(self):
        """A second risk cannot be raised from the same failure mode."""
        self.line.action_create_risk()
        with self.assertRaises(UserError):
            self.line.action_create_risk()

    def test_create_risk_requires_default_matrix(self):
        """Raising a risk requires an approved default matrix."""
        self.matrix.with_user(self.user_manager).action_set_obsolete()
        with self.assertRaises(UserError):
            self.line.action_create_risk()

    def test_risk_records_originating_lines(self):
        """The risk exposes the failure modes that produced it."""
        self.line.action_create_risk()
        self.assertEqual(self.line.risk_id.fmea_line_count, 1)

    def test_unlink_blocked_after_start(self):
        """A worksheet in progress cannot be deleted."""
        self.fmea.action_start()
        with self.assertRaises(UserError):
            self.fmea.unlink()

    def test_display_name_includes_revision(self):
        """The display name shows the reference, title and revision."""
        self.assertIn("rev. 1", self.fmea.display_name)
