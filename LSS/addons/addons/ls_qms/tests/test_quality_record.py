# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality records, protection of evidence and retention."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestQualityRecord(LsQmsCommon):
    """Lifecycle, locking, retention and disposal."""

    def test_01_reference_prefix(self):
        """A quality record is numbered with the QR prefix."""
        self.assertTrue(
            self._create_quality_record().reference.startswith("QR-")
        )

    def test_02_retention_date_is_computed(self):
        """Retain until equals the record date plus the retention period."""
        record = self._create_quality_record(retention_period_months=60)
        self.assertEqual(
            record.date_retention_until,
            record.date_record + relativedelta(months=60),
        )

    def test_03_zero_retention_gives_no_limit(self):
        """A retention period of zero produces no retention date."""
        record = self._create_quality_record(retention_period_months=0)
        self.assertFalse(record.date_retention_until)

    def test_04_lifecycle(self):
        """Draft, confirmed and archived follow each other."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        self.assertEqual(record.state, "confirmed")
        record.with_user(self.user_author).action_archive_record()
        self.assertEqual(record.state, "archived")

    def test_05_confirm_twice_is_refused(self):
        """A confirmed record cannot be confirmed again."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        with self.assertRaises(UserError):
            record.with_user(self.user_author).action_confirm()

    def test_06_archive_requires_confirmation(self):
        """A draft record cannot be archived."""
        record = self._create_quality_record()
        with self.assertRaises(UserError):
            record.with_user(self.user_author).action_archive_record()

    def test_07_confirmed_record_is_locked_for_users(self):
        """A QMS user cannot modify confirmed evidence."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        with self.assertRaises(UserError):
            record.with_user(self.user_author).write(
                {"conclusion": "Rewritten conclusion."}
            )

    def test_08_manager_can_correct_a_confirmed_record(self):
        """A QMS manager corrects evidence and the change is tracked."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.with_user(self.user_manager).write(
            {"conclusion": "Corrected conclusion."}
        )
        self.assertEqual(record.conclusion, "Corrected conclusion.")

    def test_09_confirmed_record_cannot_be_deleted(self):
        """Evidence is retained, not deleted."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        with self.assertRaises(UserError):
            record.unlink()

    def test_10_draft_record_can_be_deleted(self):
        """A draft record is deletable."""
        self.assertTrue(self._create_quality_record().unlink())

    def test_11_disposal_requires_the_manager_role(self):
        """Only a QMS manager disposes of a record."""
        record = self._create_quality_record(retention_period_months=1)
        record.with_user(self.user_author).action_confirm()
        record.with_user(self.user_author).action_archive_record()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        with self.assertRaises(UserError):
            record.with_user(self.user_author).action_dispose()

    def test_12_disposal_requires_the_retention_to_be_elapsed(self):
        """A record still under retention cannot be disposed of."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.with_user(self.user_author).action_archive_record()
        with self.assertRaises(UserError):
            record.with_user(self.user_manager).action_dispose()

    def test_13_disposal_after_retention(self):
        """An archived record past its retention can be disposed of."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.with_user(self.user_author).action_archive_record()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        record.with_user(self.user_manager).action_dispose()
        self.assertEqual(record.state, "disposed")
        self.assertFalse(record.active)

    def test_14_disposal_requires_archiving(self):
        """A confirmed record must be archived before disposal."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        with self.assertRaises(UserError):
            record.with_user(self.user_manager).action_dispose()

    def test_15_retention_expired_flag(self):
        """The flag is raised only for retained records past the date."""
        record = self._create_quality_record()
        self.assertFalse(record.retention_expired)
        record.with_user(self.user_author).action_confirm()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        self.assertTrue(record.retention_expired)

    def test_16_display_name(self):
        """The display name carries the reference."""
        record = self._create_quality_record(name="Management Review")
        self.assertEqual(
            record.display_name,
            "[%s] Management Review" % record.reference,
        )
