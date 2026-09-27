# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Append-only transition log tests."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationStageLog(DeviationCommon):
    """Verify that the transition log cannot be altered."""

    def setUp(self):
        super().setUp()
        self.deviation = self._create_deviation()
        self.log = self.deviation.stage_log_ids[0]

    def test_log_write_is_blocked(self):
        """The log rejects modification."""
        with self.assertRaises(UserError):
            self.log.write({"reason": "tampered"})

    def test_log_write_is_blocked_even_for_superuser(self):
        """The block is enforced at model level, not by access rights."""
        with self.assertRaises(UserError):
            self.log.sudo().write({"reason": "tampered"})

    def test_log_unlink_is_blocked(self):
        """The log rejects deletion."""
        with self.assertRaises(UserError):
            self.log.unlink()

    def test_log_unlink_is_blocked_even_for_superuser(self):
        """Deletion is blocked at model level for every user."""
        with self.assertRaises(UserError):
            self.log.sudo().unlink()

    def test_log_records_actor(self):
        """The log records the acting user."""
        self.assertEqual(self.log.user_id, self.env.user)

    def test_log_removed_with_parent_deviation(self):
        """Cascade deletion of a Reported deviation removes its log."""
        deviation = self._create_deviation()
        log = deviation.stage_log_ids[0]
        deviation.unlink()
        self.assertFalse(log.exists())

    def test_log_ordering_is_reverse_chronological(self):
        """The most recent transition is listed first."""
        self._advance_to_assessed(self.deviation)
        # Read the relation back from the database: the cache of a one2many
        # keeps the creation order of records created in this transaction.
        self.env.flush_all()
        self.deviation.invalidate_recordset(["stage_log_ids"])
        self.assertEqual(self.deviation.stage_log_ids[0].to_state, "assessed")
