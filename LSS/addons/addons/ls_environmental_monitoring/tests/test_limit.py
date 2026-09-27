# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for limit versioning, approval and immutability."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestLimit(EnvMonitoringCommon):
    """Limits are approved, versioned and never edited in place."""

    def test_limit_requires_at_least_one_threshold(self):
        with self.assertRaises(ValidationError):
            self.env["ls.env.limit"].create(
                {
                    "sampling_point_id": self.point.id,
                    "parameter_id": self.parameter_count.id,
                    "occupancy_state": "any",
                    "direction": "upper",
                }
            )

    def test_upper_bound_threshold_ordering_is_enforced(self):
        with self.assertRaises(ValidationError):
            self._create_limit(
                self.point, self.parameter_count,
                alert_set=True, alert_value=50.0,
                action_set=True, action_value=10.0,
            )

    def test_lower_bound_threshold_ordering_is_enforced(self):
        with self.assertRaises(ValidationError):
            self._create_limit(
                self.point, self.parameter_temperature,
                direction="lower",
                alert_set=True, alert_value=10.0,
                action_set=True, action_value=50.0,
            )

    def test_approval_requires_a_justification(self):
        limit = self._create_limit(self.point, self.parameter_count)
        limit.justification = False
        with self.assertRaises(UserError):
            limit.with_user(self.manager).action_approve()

    def test_author_cannot_approve_own_limit(self):
        limit = self._create_limit(self.point, self.parameter_count)
        with self.assertRaises(UserError):
            limit.with_user(self.author).action_approve()

    def test_approval_sets_the_effective_date_and_approver(self):
        limit = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(limit)
        self.assertEqual(limit.state, "approved")
        self.assertTrue(limit.effective_date)
        self.assertEqual(limit.approved_by_id, self.manager)

    def test_approved_thresholds_cannot_be_edited(self):
        limit = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(limit)
        with self.assertRaises(UserError):
            limit.action_value = 99.0

    def test_approved_limit_cannot_be_deleted(self):
        limit = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(limit)
        with self.assertRaises(UserError):
            limit.unlink()

    def test_draft_limit_can_be_deleted(self):
        limit = self._create_limit(self.point, self.parameter_count)
        limit.unlink()
        self.assertFalse(limit.exists())

    def test_revision_supersedes_the_predecessor(self):
        original = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(original)
        original.with_user(self.author).action_create_revision()
        revision = self.env["ls.env.limit"].search(
            [
                ("sampling_point_id", "=", self.point.id),
                ("parameter_id", "=", self.parameter_count.id),
                ("state", "=", "draft"),
            ],
            limit=1,
        )
        self.assertTrue(revision)
        revision.action_value = 20.0
        revision.with_user(self.author).write(
            {"justification": "Revised after annual review."})
        revision.with_user(self.manager).action_approve()
        self.assertEqual(original.state, "superseded")
        self.assertEqual(original.superseded_by_id, revision)
        self.assertTrue(original.superseded_date)
        self.assertEqual(revision.state, "approved")
        self.assertGreater(revision.version, original.version)

    def test_two_approved_limits_for_the_same_scope_are_rejected(self):
        first = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(first)
        second = self._create_limit(self.point, self.parameter_count)
        # Approving through the supported route supersedes the first, so the
        # constraint is exercised by forcing the state directly.
        with self.assertRaises(ValidationError):
            second.write({"state": "approved"})

    def test_specific_occupancy_limit_takes_precedence(self):
        general = self._create_limit(
            self.point, self.parameter_count,
            occupancy_state="any", action_value=100.0)
        self._approve_limit(general)
        specific = self._create_limit(
            self.point, self.parameter_count,
            occupancy_state="in_operation", action_value=5.0)
        self._approve_limit(specific)
        found = self.point.find_approved_limit(
            self.parameter_count, "in_operation", "upper")
        self.assertEqual(found, specific)

    def test_general_limit_is_used_when_no_specific_limit_exists(self):
        general = self._create_limit(
            self.point, self.parameter_count, occupancy_state="any")
        self._approve_limit(general)
        found = self.point.find_approved_limit(
            self.parameter_count, "at_rest", "upper")
        self.assertEqual(found, general)

    def test_get_thresholds_reports_unset_thresholds_as_none(self):
        limit = self._create_limit(
            self.point, self.parameter_count,
            alert_set=False, alert_value=0.0,
            action_set=True, action_value=10.0)
        thresholds = limit.get_thresholds()
        self.assertIsNone(thresholds["alert"])
        self.assertEqual(thresholds["action"], 10.0)
        self.assertIsNone(thresholds["spec"])
